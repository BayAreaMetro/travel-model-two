package com.pb.mtctm2.abm.transitcapacityrestraint;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.MissingResourceException;
import java.util.ResourceBundle;
import java.util.Set;

import org.apache.log4j.Logger;
import org.jppf.client.JPPFClient;

import com.pb.common.calculator.MatrixDataServerIf;
import com.pb.common.math.MersenneTwister;
import com.pb.common.util.ResourceUtil;
import com.pb.mtctm2.abm.application.MTCTM2TourBasedModel;
import com.pb.mtctm2.abm.application.SandagCtrampApplication;
import com.pb.mtctm2.abm.application.SandagCtrampDmuFactory;
import com.pb.mtctm2.abm.application.SandagHouseholdDataManager;
import com.pb.mtctm2.abm.application.SandagModelStructure;
import com.pb.mtctm2.abm.ctramp.CtrampDmuFactoryIf;
import com.pb.mtctm2.abm.ctramp.Household;
import com.pb.mtctm2.abm.ctramp.HouseholdDataManager;
import com.pb.mtctm2.abm.ctramp.HouseholdDataManagerIf;
import com.pb.mtctm2.abm.ctramp.HouseholdDataManagerRmi;
import com.pb.mtctm2.abm.ctramp.HouseholdDataWriter;
import com.pb.mtctm2.abm.ctramp.MgraDataManager;
import com.pb.mtctm2.abm.ctramp.ModelStructure;
import com.pb.mtctm2.abm.ctramp.Person;
import com.pb.mtctm2.abm.ctramp.Stop;
import com.pb.mtctm2.abm.ctramp.TapDataManager;
import com.pb.mtctm2.abm.ctramp.TazDataManager;
import com.pb.mtctm2.abm.ctramp.Tour;
import com.pb.mtctm2.abm.ctramp.Util;

public class ParkingCapacityRestraintModel {
	
	protected static final Logger logger = Logger.getLogger(ParkingCapacityRestraintModel.class);
	protected HashMap<String, String> propertyMap = null;
	protected MersenneTwister       random;
	protected double[] endTimeMinutes; // the period end time in number of minutes past 3 AM , starting in period 1 (index 1)
	protected int iteration;
	protected MgraDataManager mgraManager;
	protected TazDataManager tazManager;
	protected TapDataManager tapManager;
	protected static final String ModelSeedProperty = "Model.Random.Seed";
    private transient ModelStructure          modelStructure;
	protected int numberOfTimeBins;
	private int numberOfSimulationPeriods;
	private ArrayList<Household> householdsToResimulate;
	private float sampleRate;
	private int seed;
	private static float UNSPECIFIED_SPACES = 50;
	private static int MINUTES_PER_SIMULATION_PERIOD = 15;

    private static int              PACKET_SIZE                           = 0;

    private static String           PROPERTIES_NUM_INITIALIZATION_PACKETS = "number.initialization.packets";
    private static String           PROPERTIES_INITIALIZATION_PACKET_SIZE = "initialization.packet.size";
    private static final String     HOUSEHOLD_CHOICE_PACKET_SIZE          = "distributed.task.packet.size";
    private static int              NUM_INITIALIZATION_PACKETS            = 0;
    private static int              INITIALIZATION_PACKET_SIZE            = 0;
    private static final String PROPERTIES_UNCONSTRAINED_PNR_DEMAND_FILE = "Results.UnconstrainedPNRDemandFile";
    private static final String PROPERTIES_CONSTRAINED_PNR_DEMAND_FILE = "Results.ConstrainedPNRDemandFile";

    public static final String PROPERTIES_PROJECT_DIRECTORY = "Project.Directory";

    private static final int   DEFAULT_ITERATION_NUMBER     = 1;
    private static final float DEFAULT_SAMPLE_RATE          = 1.0f;
    private static final int   DEFAULT_SAMPLE_SEED          = 0;

    public static final int    DEBUG_CHOICE_MODEL_HHID      = 740151;

    private ResourceBundle     rb;

    protected ArrayList<Stop> unconstrainedPNRTrips;
    protected float totalUnconstrainedPNRTours;
    protected float totalUnconstrainedPNRArrivals;
    protected HashMap<Integer, float[]> unconstrainedPNRLotMap; //a hashmap of lots and the lot arrivals by time period.
    protected float[] unconstrainedPNRArrivalsByPeriod; //an array of arrivals by period
    protected ArrayList<Stop> constrainedPNRTrips;
    protected float totalConstrainedPNRTours;
    protected float totalConstrainedPNRArrivals;
    protected HashMap<Integer, float[]> constrainedPNRLotMap; //a hashmap of lots and the lot arrivals by time period.
    protected float[] constrainedPNRArrivalsByPeriod; //an array of arrivals by period
	protected ArrayList<Integer> tapsToRemove;
	protected float[] unconstrainedArrivalsToTAP; //to track arrivals over time.
	protected float[] constrainedArrivalsToTAP; //to track arrivals over time.
	    
	/**
	 * Constructor
	 * @param rb ResourceBundle version of property map
	 * @param pMap Property map version of resource bundle (dumb? yes)
	 * @param globalIterationNumber The global iteration number
	 * @param iterationSampleRate The sample rate
	 * @param sampleSeed The sample seed for monte carlo.
	 */
	public ParkingCapacityRestraintModel(ResourceBundle rb, HashMap<String, String> pMap, int globalIterationNumber,
            float iterationSampleRate, int sampleSeed) {
		
		this.rb = rb;
		propertyMap = pMap;
		sampleRate = iterationSampleRate;
		iteration = globalIterationNumber;
		seed=sampleSeed;
		
	}
	
	
	/**
	 * Reads properties, initializes data structures, instantiates member classes, etc.
	 */
	public void initialize() {

		
		//initialize the end time in minutes (stored in double so no overlap between periods)
        endTimeMinutes = new double[40+1];
        endTimeMinutes[1]=119.999999; //first period is 3-3:59:99:99
        for(int period=2;period<endTimeMinutes.length;++period)
        	endTimeMinutes[period] = endTimeMinutes[period-1] + 30; //all other periods are 30 minutes long
        endTimeMinutes[40] = endTimeMinutes[39] + 3*60; //last period is 12 - 2:59:99:99 AM

        random = new MersenneTwister(seed);
        
        String propertyValue = propertyMap.get(HOUSEHOLD_CHOICE_PACKET_SIZE);
        if (propertyValue == null) PACKET_SIZE = 0;
        else PACKET_SIZE = Integer.parseInt(propertyValue);

        propertyValue = propertyMap.get(PROPERTIES_NUM_INITIALIZATION_PACKETS);
        if (propertyValue == null) NUM_INITIALIZATION_PACKETS = 0;
        else NUM_INITIALIZATION_PACKETS = Integer.parseInt(propertyValue);

        propertyValue = propertyMap.get(PROPERTIES_INITIALIZATION_PACKET_SIZE);
        if (propertyValue == null) INITIALIZATION_PACKET_SIZE = 0;
        else INITIALIZATION_PACKET_SIZE = Integer.parseInt(propertyValue);

        unconstrainedPNRTrips = new ArrayList<Stop>();

		modelStructure = new SandagModelStructure();
		
		totalUnconstrainedPNRTours = 0;
		totalUnconstrainedPNRArrivals = 0;
		
		tapManager = TapDataManager.getInstance(propertyMap);
		mgraManager = MgraDataManager.getInstance(propertyMap);
		tazManager = TazDataManager.getInstance(propertyMap);
		
		//set the length of a simulation period
		numberOfTimeBins = ((24*60)/MINUTES_PER_SIMULATION_PERIOD);
		logger.info("Running "+numberOfSimulationPeriods+" simulation periods using a period length of "+MINUTES_PER_SIMULATION_PERIOD+" minutes");


	}
	
	/**
	 * Main method. First initializes data, then processes all tours. Finds PNR tours, and arrival stops to PNR lots.
	 * Stores arrivals in unconstrainedPNRTrips ArrayList. Calculates unconstrained demand by arrival period and lot, stores in unconstrainedPNRLotMap.
	 * Finds all tours with PNR trips that arrive in lot after lot is filled. Removes drive-transit option at the lot and 
	 * resimulates the tours that arrive after the lot is filled.
	 *  
	 * @param propertyMap
	 */
	public void runModel(HashMap<String, String> propertyMap) {
		
		initialize();
		
		HouseholdDataManagerIf householdDataManager = connectToHouseholdDataManager(propertyMap);
		
		processHouseholds(householdDataManager);
		
		logger.info("Total unconstrained PNR tours:    "+ totalUnconstrainedPNRTours); 
		logger.info("Total unconstrained PNR arrivals: "+ totalUnconstrainedPNRArrivals); 
		
		Collections.sort(unconstrainedPNRTrips, new StopComparator());
		
		calculateUnconstrainedArrivalsByPeriod();
		
        String filename = propertyMap.get(PROPERTIES_PROJECT_DIRECTORY)
        		+ formFileName(propertyMap.get(PROPERTIES_UNCONSTRAINED_PNR_DEMAND_FILE), iteration);
	
		writeDemandToFile(filename,unconstrainedArrivalsToTAP,unconstrainedPNRLotMap);
		
 		constrainDemand(householdDataManager);
 		
 		calculateConstrainedArrivalsByPeriod(householdDataManager);
 		
        filename = propertyMap.get(PROPERTIES_PROJECT_DIRECTORY)
        		+ formFileName(propertyMap.get(PROPERTIES_CONSTRAINED_PNR_DEMAND_FILE), iteration);
	
		writeDemandToFile(filename,constrainedArrivalsToTAP,constrainedPNRLotMap);
		
	}
	
	
	/**
	 * Simulate the exact time for the period.
	 * 
	 * @param period The time period (1->40)
	 * @return The exact time in float precision (number of minutes past 3 AM)
	 */
	public float simulateExactTime(int period){
		
		double lowerEnd = endTimeMinutes[period-1];
		double upperEnd = endTimeMinutes[period];
        double randomNumber = random.nextDouble();
        
        float time = (float) ((upperEnd - lowerEnd) * randomNumber + lowerEnd);

		return time;
	}
	
	
	/**
	 * This method assigns exact departure times in minutes to all stops on the tour.
	 * 
	 * @param tour A PNR tour
	 */
	public void simulateExactTimesForTour(Tour tour) {
		
		Stop[] outboundStops = tour.getOutboundStops();
		Stop[] inboundStops = tour.getInboundStops();
		
		int lastTime = -99;
		for(Stop thisStop : outboundStops) {
			
			if(thisStop.getMinute()>0)
				continue;
			
			int period = thisStop.getStopPeriod();
			
			//iterate until simulated time is greater or equal to the time for the last trip on the tour
			int exactTime=0;
			int draws=0;
			do {
				exactTime = (int) simulateExactTime(period);
				++draws;
				
				if(draws==200) {
					exactTime=lastTime;
				}
			}while(exactTime<lastTime);
			
			thisStop.setMinute((short) exactTime);
		}

		for(Stop thisStop : inboundStops) {
			
			if(thisStop.getMinute()>0)
				continue;

			int period = thisStop.getStopPeriod();
			
			//iterate until simulated time is greater or equal to the time for the last trip on the tour
			int exactTime=0;
			int draws=0;
			do {
				exactTime = (int) simulateExactTime(period);
				++draws;
				
				if(draws==200) {
					exactTime=lastTime;
				}
			}while(exactTime<lastTime);
			
			thisStop.setMinute((short) exactTime);
		
		}
		
	}
	
	/**
	 * Process all the households in the household data manager, finding PNR tours for each person in each household, process the tour.
	 * 
	 * @param householdDataManager
	 */
	public void processHouseholds(HouseholdDataManagerIf householdDataManager) {
		
		
		logger.info("There are "+householdDataManager.getNumHouseholds()+" households in household data manager");
		int totalHouseholds=0;
		int totalPersons=0;
		
        try
        {

            ArrayList<int[]> startEndTaskIndicesList = getTaskHouseholdRanges(householdDataManager
                    .getNumHouseholds());

            for (int[] startEndIndices : startEndTaskIndicesList)
            {

                int startIndex = startEndIndices[0];
                int endIndex = startEndIndices[1];

                // get the array of households
                Household[] householdArray = householdDataManager.getHhArray(startIndex, endIndex);

                for (Household thisHousehold : householdArray)
                {
                	if (thisHousehold == null) continue;
                    
                	++totalHouseholds;
                    Tour[] jointTours = thisHousehold.getJointTourArray();
                    codePNRTours(jointTours);
                    
                    Person[] persons = thisHousehold.getPersons();
                    if(persons==null) continue;
                    
                    for(Person thisPerson : persons) {
                    	
                    	if(thisPerson==null)
                    		continue;
                    	
                    	++totalPersons;
                    	
                    	ArrayList<Tour> workTours = thisPerson.getListOfWorkTours();
                    	ArrayList<Tour> schoolTours = thisPerson.getListOfSchoolTours();
                    	ArrayList<Tour> nonMandatoryTours = thisPerson.getListOfIndividualNonMandatoryTours();
                    	ArrayList<Tour> atWorkTours = thisPerson.getListOfAtWorkSubtours();
                    	
                    	codePNRTours(workTours);
                    	codePNRTours(schoolTours);
                    	codePNRTours(nonMandatoryTours);
                    	codePNRTours(atWorkTours);
                    }

                }
            }
        }catch(Exception e) {
        	throw(e);
        }
        
        logger.info("Coded "+totalHouseholds+" households and "+totalPersons+" persons");
	}
	
	/**
	 * Process the tours in each arraylist. Used for individual tours.
	 * 
	 * @param tours
	 */
	public void codePNRTours(ArrayList<Tour> tours) {
		
		if(tours==null) return;
		
		for(Tour thisTour : tours) {
			codePNRTour(thisTour);
		}
	}
	
	/**
	 * Process the tours in each array. Used for joint tours.
	 * @param tours
	 */
	public void codePNRTours(Tour[] tours) {
		
		if(tours==null) return;
		
		for(Tour thisTour : tours) {
			codePNRTour(thisTour);
		}
	}

	/**
	 * Process the tour. If the tour is PNR, find the outbound PNR trip and add it to the unconstrained PNR trip arraylist, and count the number of arrivals for reporting.
	 * 
	 * @param thisTour
	 */
	public void codePNRTour(Tour thisTour) {
		if(modelStructure.getTourModeIsPnr(thisTour.getTourModeChoice())){
			totalUnconstrainedPNRTours += (1.0/sampleRate);;
				
			simulateExactTimesForTour(thisTour);
				
			Stop[] stops = thisTour.getOutboundStops();
			if(stops==null) return;
			for(Stop thisStop : stops) {
					
				if(modelStructure.getTripModeIsPnrTransit(thisStop.getMode())) {
						
					unconstrainedPNRTrips.add(thisStop);
					totalUnconstrainedPNRArrivals += (1.0/sampleRate);
				}
			}
		}
	}
	
	
	/**
	 * Iterate through PNR arrivals (sorted by minute), calculate the arrivals by TAP and by TAP-simulation period. For any arrival to lot 
	 * after lot is full, add the household to a container of households to resimulate (householdsToResimulate). Add full lots to container
	 * of lots to remove from the next iteration (tapsToRemove)
	 * 
	 */
	public void calculateUnconstrainedArrivalsByPeriod() {
		
		logger.info("Calculated "+numberOfTimeBins+" simulation periods using a period length of "+MINUTES_PER_SIMULATION_PERIOD+" minutes");
		
		unconstrainedPNRArrivalsByPeriod=new float[numberOfTimeBins];
		
		//to hold households to resimulate (will reset household data manager with these)
		householdsToResimulate = new ArrayList<Household>();
		
		//taps to remove from resimulation
		tapsToRemove = new ArrayList<Integer>();
		
		//to hold taps and an array of arrivals by arrival bin
		unconstrainedPNRLotMap = new HashMap<Integer, float[]>();
		
		//to hold arrivals over time
		unconstrainedArrivalsToTAP = new float[tapManager.getMaxTap()+1];
		 
		for(Stop thisStop : unconstrainedPNRTrips) {
			
			float departTime = thisStop.getMinute();
			int bin = (int) Math.floor(departTime/((float) MINUTES_PER_SIMULATION_PERIOD));
			
			int tap = thisStop.getBoardTap();

			//assume some small number of spaces if lot is not in station attribute file?
			float totalSpaces = tapManager.getTotalSpaces(tap);
			if(totalSpaces==0) {
				totalSpaces=UNSPECIFIED_SPACES;
				tapManager.setTotalSpaces(tap, totalSpaces);
			}
			
			unconstrainedPNRArrivalsByPeriod[bin] += (1.0/sampleRate);
			
			if(unconstrainedPNRLotMap.containsKey(tap)) {
				float[] tapArrivalArray = unconstrainedPNRLotMap.get(tap);
				tapArrivalArray[bin] += (1.0f/sampleRate);
				unconstrainedArrivalsToTAP[tap] += (1.0f/sampleRate);
			}else {
				float[] tapArrivalArray = new float[numberOfTimeBins];
				tapArrivalArray[bin] +=  (1.0f/sampleRate);
				unconstrainedArrivalsToTAP[tap] += (1.0f/sampleRate);
				unconstrainedPNRLotMap.put(tap, tapArrivalArray);
			}
			
			//No more room!
			if(unconstrainedArrivalsToTAP[tap] >=totalSpaces) {
				
				Household thisHousehold = thisStop.getTour().getHousehold();
				
				if(!householdsToResimulate.contains(thisHousehold))
					householdsToResimulate.add(thisHousehold);
				
				if(!tapsToRemove.contains(tap)) {
					tapsToRemove.add(tap);
					String timeWhenLotFilled = getTimeString(thisStop.getMinute());
					logger.info("TAP "+tap+" filled up at "+timeWhenLotFilled);
				}
				
			}
		}
		
	}
	
	/**
	 * Rerun choice models for only households with tours to re-simulate
	 * @param householdManager
	 */
	public void constrainDemand(HouseholdDataManagerIf householdManager) {
		
		if(householdsToResimulate.size()==0) {
			logger.info("No households to resimulate");
			return;
		}else {
			logger.info("Resimulating "+householdsToResimulate.size()+" households");
		}
		
		//get unconstrained households
		Household[] unconstrainedHouseholds = householdManager.getHhArray();
		
		//convert arraylist to array
		Household[] hhs =householdsToResimulate.toArray(new Household[householdsToResimulate.size()]);
		
		
		logger.info("Check length of converted household arraylist: "+hhs.length+" households");
		
		//set the household array in the household manager to the households that are to be resimulated
		householdManager.setHhArray(hhs);
		
		//remove the taps that have reached capacity from the tap data manager
		logger.info("Removing drive access to the following TAPs");
		for(Integer tap : tapsToRemove) {
			tapManager.setDriveAccessAllowed(tap, false);
			logger.info("TAP "+tap);
		}
		
        // new a ctramp application object
        SandagCtrampApplication ctrampApplication = new SandagCtrampApplication(rb, propertyMap);

        // create modelStructure object
        SandagModelStructure modelStructure = new SandagModelStructure();

        // setup the ctramp application
        ctrampApplication.setupModels(modelStructure);


        // create a factory object to pass to various model components from which
        // they can create DMU objects
        SandagCtrampDmuFactory dmuFactory = new SandagCtrampDmuFactory(modelStructure);

        // run the models
        ctrampApplication.runModels(householdManager, dmuFactory, iteration, sampleRate);
        
        Household[] resimulatedHouseholds = householdManager.getHhArray();
        
        //Replace the initial households with resimulated households        
        Household[] finalHouseholds = replaceHouseholdsWithResimulatedHouseholds(unconstrainedHouseholds, resimulatedHouseholds);
        
        //Replace the household array in the manager
        householdManager.setHhArray(finalHouseholds);
        
        //And write the constrained household, person, tour, and trip files.
        HouseholdDataWriter dataWriter = new HouseholdDataWriter(propertyMap, modelStructure, iteration);
        dataWriter.writeDataToFiles(householdManager);
		
	}
	
	/**
	 * Replace households in the unconstrainedHouseholds array with the resimulated households in resimulatedHouseholds array
	 * 
	 * @param unconstrainedHouseholds
	 * @param resimulatedHouseholds
	 * 
	 * @return An array with all households (where initial hhs are replaced with resimulated hhs)
	 */
	public Household[] replaceHouseholdsWithResimulatedHouseholds(Household[] unconstrainedHouseholds, Household[] resimulatedHouseholds) {
		
	    //create a hashmap of the resimulated households
		HashMap<Integer, Household> resimulatedHouseholdsMap = new HashMap<Integer, Household>();
		for(Household hh: resimulatedHouseholds) {
			resimulatedHouseholdsMap.put(hh.getHhId(), hh);
		}
	
        for(int i =0; i < unconstrainedHouseholds.length;++i) {
        	if(unconstrainedHouseholds[i]==null)
        		continue;
        	Household unconstrainedHousehold = unconstrainedHouseholds[i];
        	Integer id = unconstrainedHousehold.getHhId();
        	if(resimulatedHouseholdsMap.containsKey(id)) {
        		unconstrainedHouseholds[i] = resimulatedHouseholdsMap.get(id);
        		
        	}
        	
        }
        
        return unconstrainedHouseholds;

	}
	
	/**
	 * Iterate through households in the household data manager, and calculated the constrained arrivals
	 * by time of day, by TAP and by TAP and time of day period.
	 * 
	 * @param householdDataManager
	 */
	public void calculateConstrainedArrivalsByPeriod(HouseholdDataManagerIf householdDataManager) {
		
		constrainedPNRArrivalsByPeriod=new float[numberOfTimeBins];
		
		constrainedPNRLotMap = new HashMap<Integer, float[]>();
		
		constrainedArrivalsToTAP = new float[tapManager.getMaxTap()+1];

		
        try{

	       ArrayList<int[]> startEndTaskIndicesList = getTaskHouseholdRanges(householdDataManager
	            .getNumHouseholds());

	       for (int[] startEndIndices : startEndTaskIndicesList)
	       {

	    	   int startIndex = startEndIndices[0];
	           int endIndex = startEndIndices[1];

	           // get the array of households
	           Household[] householdArray = householdDataManager.getHhArray(startIndex, endIndex);

	           for (Household thisHousehold : householdArray)
	           {
	        	   if (thisHousehold == null) continue;
	                    
	               Tour[] jointTours = thisHousehold.getJointTourArray();

	               if(jointTours!=null) {
	            	   for(Tour thisTour: jointTours) {
	            		   if(modelStructure.getTourModeIsPnr(thisTour.getTourModeChoice()))
	            			   calculateConstrainedArrivals(thisTour);
	                    }
	               }
	                    
	               Person[] persons = thisHousehold.getPersons();
	               if(persons==null) continue;
	                    
	               for(Person thisPerson : persons) {
	            	   
	            	   if(thisPerson==null)
	            		   continue;
	            	   
		               ArrayList<Tour> workTours = thisPerson.getListOfWorkTours();
		               if(workTours!=null) {
		            	   for(Tour thisTour: workTours) {
		            		   if(modelStructure.getTourModeIsPnr(thisTour.getTourModeChoice()))
		                    		calculateConstrainedArrivals(thisTour);
		                    }
		               }

	                   ArrayList<Tour> schoolTours = thisPerson.getListOfSchoolTours();
		               if(schoolTours!=null) {
		               		for(Tour thisTour: schoolTours) {
		               			if(modelStructure.getTourModeIsPnr(thisTour.getTourModeChoice()))
		                    		calculateConstrainedArrivals(thisTour);
		                    }
		               }
	                   ArrayList<Tour> nonMandatoryTours = thisPerson.getListOfIndividualNonMandatoryTours();
		               if(nonMandatoryTours!=null) {
		            	   for(Tour thisTour: nonMandatoryTours) {
		            		   if(modelStructure.getTourModeIsPnr(thisTour.getTourModeChoice()))
		                    		calculateConstrainedArrivals(thisTour);
		                    }
		               }
	                   ArrayList<Tour> atWorkTours = thisPerson.getListOfAtWorkSubtours();
		               if(atWorkTours!=null) {
		            	   for(Tour thisTour: atWorkTours) {
		            		   if(modelStructure.getTourModeIsPnr(thisTour.getTourModeChoice()))
		            			   calculateConstrainedArrivals(thisTour);
		                   }
		               }
	               
	             }
	         }
	       }
        }catch(Exception e) {
	    	throw(e);
	    }
	}
	

	/**
	 * Iterate through trips in tour. Simulate the times for the tour. Track arrivals to lots.
	 * This method _may_ be unnecessary once iteration is built into the algorithm.
	 * 
	 * @param thisTour
	 */
	private void calculateConstrainedArrivals(Tour thisTour) {
		
		totalConstrainedPNRTours += (1.0/sampleRate);
		
		
		//times need to be resimulated
		simulateExactTimesForTour(thisTour);

		Stop[] stops = thisTour.getOutboundStops();
		if(stops==null) return;
		for(Stop thisStop : stops) {
				
			if(modelStructure.getTripModeIsPnrTransit(thisStop.getMode())) {
					
				totalUnconstrainedPNRArrivals += (1.0/sampleRate);
				
				float departTime = thisStop.getMinute();
				int bin = (int) Math.floor(departTime/((float) MINUTES_PER_SIMULATION_PERIOD));
				
				int tap = thisStop.getBoardTap();
		
				constrainedPNRArrivalsByPeriod[bin] += (1.0/sampleRate);
				
				if(constrainedPNRLotMap.containsKey(tap)) {
					float[] tapArrivalArray = constrainedPNRLotMap.get(tap);
					tapArrivalArray[bin] += (1.0f/sampleRate);
					constrainedArrivalsToTAP[tap] += (1.0f/sampleRate);
				}else {
					float[] tapArrivalArray = new float[numberOfTimeBins];
					tapArrivalArray[bin] +=  (1.0f/sampleRate);
					constrainedPNRLotMap.put(tap, tapArrivalArray);
					constrainedArrivalsToTAP[tap] += (1.0f/sampleRate);

				}
			}
		}
		
	}
	

	/** Write the PNR lot demand by time period to an output file
	 * 
	 * @param filename
	 * @param arrivalsToTAP
	 * @param PNRLotMap
	 */
	private void writeDemandToFile(String filename, float[] arrivalsToTAP, HashMap<Integer, float[]> PNRLotMap) {

		PrintWriter pnrWriter = null;
        try
        {
        	pnrWriter = new PrintWriter(new File(filename));
        } catch (IOException e)
        {
            throw new RuntimeException(e);
        }

        String header = "TAP,CAPACITY,TOT_ARRIVALS";
        for(int i=0; i<numberOfTimeBins;++i) {
        	String timeString = getTimeString(MINUTES_PER_SIMULATION_PERIOD+(i*MINUTES_PER_SIMULATION_PERIOD));
        	header += ","+timeString;
        }
        pnrWriter.println(header);
        pnrWriter.flush();
        
        Set<Integer> tapSet = PNRLotMap.keySet();
        for(Integer tap:tapSet) {
        	float totalSpaces = tapManager.getTotalSpaces(tap);
            float[] arrivals = PNRLotMap.get(tap);
        	String printString = tap + "," + totalSpaces +","+arrivalsToTAP[tap];
        	for(int i=0;i<arrivals.length;++i) {
        		printString += "," + arrivals[i];
        	}
        	pnrWriter.println(printString);
            pnrWriter.flush();
        }

        pnrWriter.close();
	}
				

    private HouseholdDataManagerIf connectToHouseholdDataManager( HashMap<String,String> propertyMap )
    {

        String hhHandlerAddress = "";
        int hhServerPort = 0;
        hhHandlerAddress = propertyMap.get("RunModel.HouseholdServerAddress");
        hhServerPort = Integer.parseInt(propertyMap.get("RunModel.HouseholdServerPort"));
        String testString;

        HouseholdDataManagerIf householdDataManager;

        try
        {
        	householdDataManager = new HouseholdDataManagerRmi(hhHandlerAddress, hhServerPort,
                        SandagHouseholdDataManager.HH_DATA_SERVER_NAME);
            testString = householdDataManager.testRemote();
            logger.info("HouseholdDataManager test: " + testString);

            householdDataManager.setPropertyFileValues(propertyMap);

            householdDataManager.setHouseholdSampleRate(1.0f, 1000102);
            householdDataManager.setDebugHhIdsFromHashmap();
//            householdDataManager.setTraceHouseholdSet();
        } catch (Exception e)
        {

            logger.error(String
                    .format("exception caught running ctramp model components -- exiting."), e);
            throw new RuntimeException();

        }
        
        return householdDataManager;

    }
    
    /**
     * Convert the departure time (minutes past 3 AM) into a string hour:minute. Useful for logging.
     * 
     * @param departTimeInMinutes
     * @return The time string.
     */
    public String getTimeString(int departTimeInMinutes) {
    	
    	int hour = (int) (departTimeInMinutes/60);
    	int minute = ((int) departTimeInMinutes) - hour*60;
    	hour+=3;
    	
    	return new String(String.format("%02d:%02d", hour,minute));
    }


    /**
     * For distributed computing.
     * 
     * @param numberOfHouseholds
     * @return
     */
    private ArrayList<int[]> getTaskHouseholdRanges(int numberOfHouseholds)
    {

        ArrayList<int[]> startEndIndexList = new ArrayList<int[]>();

            int numInitializationHouseholds = NUM_INITIALIZATION_PACKETS
                    * INITIALIZATION_PACKET_SIZE;

            int startIndex = 0;
            int endIndex = 0;
            if (numInitializationHouseholds < numberOfHouseholds)
            {

                while(endIndex < numInitializationHouseholds)
                {
                    endIndex = startIndex + INITIALIZATION_PACKET_SIZE - 1;

                    int[] startEndIndices = new int[2];
                    startEndIndices[0] = startIndex;
                    startEndIndices[1] = endIndex;
                    startEndIndexList.add(startEndIndices);

                    startIndex += INITIALIZATION_PACKET_SIZE;
                }

            }

            while(endIndex < numberOfHouseholds - 1)
            {
                endIndex = startIndex + PACKET_SIZE - 1;
                if (endIndex + PACKET_SIZE > numberOfHouseholds) endIndex = numberOfHouseholds - 1;

                int[] startEndIndices = new int[2];
                startEndIndices[0] = startIndex;
                startEndIndices[1] = endIndex;
                startEndIndexList.add(startEndIndices);

                startIndex += PACKET_SIZE;
            }

            return startEndIndexList;


    }

	
    // creates the comparator for sorting stops
    class StopComparator implements Comparator<Stop> {
      
        // override the compare() method
        public int compare(Stop s1, Stop s2)
        {
            if (s1.getMinute() == s2.getMinute())
                return 0;
            else if (s1.getMinute() > s2.getMinute())
                return 1;
            else
                return -1;
        }
    }
    
    /**
     * Helper method for forming file names from a file name and iteration number.
     * 
     * @param originalFileName
     * @param iteration
     * @return
     */
    private String formFileName(String originalFileName, int iteration)
    {
        int lastDot = originalFileName.lastIndexOf('.');

        String returnString = "";
        if (lastDot > 0)
        {
            String base = originalFileName.substring(0, lastDot);
            String ext = originalFileName.substring(lastDot);
            returnString = String.format("%s_%d%s", base, iteration, ext);
        } else
        {
            returnString = String.format("%s_%d.csv", originalFileName, iteration);
        }

        logger.info("writing " + originalFileName + " file to " + returnString);

        return returnString;
    }

    /**
     * Main method
     * @param args
     */
    public static void main(String[] args)
    {

        long startTime = System.currentTimeMillis();
        int globalIterationNumber = -1;
        float iterationSampleRate = -1.0f;
        int sampleSeed = -1;

        ResourceBundle rb = null;
        HashMap<String,String> pMap;

        logger.info(String.format("MTC TM2 Activity Based Model - Parking Capacity Restraint Model"));

        if (args.length == 0)
        {
            logger.error( String.format("no properties file base name (without .properties extension) was specified as an argument.") );
            return;
        } else
        {
            rb = ResourceBundle.getBundle(args[0]);
            pMap = ResourceUtil.getResourceBundleAsHashMap ( args[0] );

            // optional arguments
            for (int i = 1; i < args.length; i++)
            {

                if (args[i].equalsIgnoreCase("-iteration"))
                {
                    globalIterationNumber = Integer.parseInt(args[i + 1]);
                    logger.info(String.format("-iteration %d.", globalIterationNumber));
                }

                if (args[i].equalsIgnoreCase("-sampleRate"))
                {
                    iterationSampleRate = Float.parseFloat(args[i + 1]);
                    logger.info(String.format("-sampleRate %.4f.", iterationSampleRate));
                }

                if (args[i].equalsIgnoreCase("-sampleSeed"))
                {
                    sampleSeed = Integer.parseInt(args[i + 1]);
                    logger.info(String.format("-sampleSeed %d.", sampleSeed));
                }

            }

            if (globalIterationNumber < 0)
            {
                globalIterationNumber = DEFAULT_ITERATION_NUMBER;
                logger.info(String.format("no -iteration flag, default value %d used.",
                        globalIterationNumber));
            }

            if (iterationSampleRate < 0)
            {
                iterationSampleRate = DEFAULT_SAMPLE_RATE;
                logger.info(String.format("no -sampleRate flag, default value %.4f used.",
                        iterationSampleRate));
            }

            if (sampleSeed < 0)
            {
                sampleSeed = DEFAULT_SAMPLE_SEED;
                logger.info(String
                        .format("no -sampleSeed flag, default value %d used.", sampleSeed));
            }

        }

        // create an instance of this class for main() to use.
        ParkingCapacityRestraintModel mainObject = new ParkingCapacityRestraintModel(rb, pMap, globalIterationNumber,
                iterationSampleRate, sampleSeed);

        // run tour based models
        try
        {

            logger.info("");
            logger.info("Starting PNR capacity restraint.");
            mainObject.runModel( pMap );

        } catch (RuntimeException e)
        {
            logger.error( "RuntimeException caught in PNR capacity restraint model -- exiting.", e );
            throw e;
        }

        logger.info("");
        logger.info("");
        logger.info("MTC TM2 Activity Based Model PNR capacity restraint finished in "
                + ((System.currentTimeMillis() - startTime) / 60000.0) + " minutes.");

        System.exit(0);
    }

}
