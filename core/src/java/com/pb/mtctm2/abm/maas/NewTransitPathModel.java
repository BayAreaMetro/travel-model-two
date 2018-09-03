package com.pb.mtctm2.abm.maas;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;

import org.apache.log4j.Logger;

import com.pb.common.calculator.IndexValues;
import com.pb.common.calculator.MatrixDataManager;
import com.pb.common.calculator.MatrixDataServerIf;
import com.pb.common.datafile.OLD_CSVFileReader;
import com.pb.common.datafile.TableDataSet;
import com.pb.common.math.MersenneTwister;
import com.pb.common.newmodel.UtilityExpressionCalculator;
import com.pb.common.util.ResourceUtil;
import com.pb.mtctm2.abm.accessibilities.AutoTazSkimsCalculator;
import com.pb.mtctm2.abm.accessibilities.BestTransitPathCalculator;
import com.pb.mtctm2.abm.accessibilities.DriveTransitWalkSkimsCalculator;
import com.pb.mtctm2.abm.accessibilities.WalkTransitDriveSkimsCalculator;
import com.pb.mtctm2.abm.accessibilities.WalkTransitWalkSkimsCalculator;
import com.pb.mtctm2.abm.application.SandagModelStructure;
import com.pb.mtctm2.abm.ctramp.CtrampApplication;
import com.pb.mtctm2.abm.ctramp.MatrixDataServer;
import com.pb.mtctm2.abm.ctramp.MatrixDataServerRmi;
import com.pb.mtctm2.abm.ctramp.McLogsumsCalculator;
import com.pb.mtctm2.abm.ctramp.MgraDataManager;
import com.pb.mtctm2.abm.ctramp.ModelStructure;
import com.pb.mtctm2.abm.ctramp.Person;
import com.pb.mtctm2.abm.ctramp.TazDataManager;
import com.pb.mtctm2.abm.ctramp.TransitDriveAccessDMU;
import com.pb.mtctm2.abm.ctramp.TransitWalkAccessDMU;
import com.pb.mtctm2.abm.ctramp.Util;
import com.pb.mtctm2.abm.survey.OutputTapPairs;

/**
 * This class chooses a new transit path for transit trips whose chosen TAP pair
 * is transit capacity-constrained.
 *  
 * @author joel.freedman
 *
 */
public class NewTransitPathModel{

	private static final Logger logger = Logger.getLogger(NewTransitPathModel.class);
    private BestTransitPathCalculator         bestPathCalculator;
    public static final int         MATRIX_DATA_SERVER_PORT        = 1171;
    public static final int         MATRIX_DATA_SERVER_PORT_OFFSET = 0;
    private MatrixDataServerRmi     ms;
    private MgraDataManager mgraManager;
    private TazDataManager tazManager;
    AutoTazSkimsCalculator tazDistanceCalculator;
    private int iteration;
    private HashMap<String, String> propertyMap = null;
    private MersenneTwister       random;
    private ModelStructure modelStructure;
    private ArrayList<Trip> transitTrips;
    private double[] endTimeMinutes; // the period end time in number of minutes past 3 AM , starting in period 1 (index 1)
    private HashMap<Long,Float> valueOfTimeByPersonNumber;
    private HashMap<Long,Float> valueOfTimeByHhId; // the maximum VOT for all persons in the household
    private HashMap<Long,Integer> personTypeByPersonNumber;
    private int tripsWithNoTransitPath;
    private int resimulatedTransitTrips;
    private UtilityExpressionCalculator identifyTripToResimulateUEC;
    private IndexValues                   index;
	ResimulateTransitPathDMU resimulateDMU;
    private PrintWriter outputIndivTripWriter;
    private PrintWriter outputJointTripWriter;
    
    //for tracing
    private boolean seek;
    private ArrayList<Long> traceHHIds;
    
    private static final String DirectoryProperty = "Project.Directory";
    private static final String IndivTripDataFileProperty = "Results.IndivTripDataFile";
    private static final String JointTripDataFileProperty = "Results.JointTripDataFile";
    private static final String PersonDataFileProperty = "Results.PersonDataFile";
    private static final String ModelSeedProperty = "Model.Random.Seed";
    private static final String SeekProperty = "Seek";
    private static final String TraceHouseholdList = "Debug.Trace.HouseholdIdList";
    private static final String ResimulateTransitPathUECProperty = "ResimulateTransitPath.uec.file";
    private static final String ResimulateTransitPathDataPageProperty = "ResimulateTransitPath.data.page";
    private static final String ResimulateTransitPathIdentifyPageProperty = "ResimulateTransitPath.identifyTripToResimulate.page";
    private static final String ResimulateTransitPathIndividualOutputFileProperty = "ResimulateTransitPath.results.IndivTripDataFile";
    private static final String ResimulateTransitPathJointOutputFileProperty = "ResimulateTransitPath.results.JointTripDataFile";
    

    /**
     * Create a New Transit Path Model.
     * @param propertyMap
     * @param iteration
     */
    public NewTransitPathModel(HashMap<String, String> propertyMap, int iteration){
     	
    	this.iteration = iteration;
    	this.propertyMap = propertyMap;
    	startMatrixServer(propertyMap);
    	initialize(propertyMap);
    	
    	modelStructure = new SandagModelStructure();
    }
	
    /**
     * Initialize the arrays and other data members.
     * @param propertyMap
     */
	public void initialize(HashMap<String, String> propertyMap){
		
		logger.info("Initializing NewTransitPathModel");
	    mgraManager = MgraDataManager.getInstance(propertyMap);
	    tazManager = TazDataManager.getInstance(propertyMap);

        bestPathCalculator = new BestTransitPathCalculator(propertyMap);
        tazDistanceCalculator = new AutoTazSkimsCalculator(propertyMap);
        tazDistanceCalculator.computeTazDistanceArrays();
        
        //initialize the end time in minutes (stored in double so no overlap between periods)
        endTimeMinutes = new double[40+1];
        endTimeMinutes[1]=119.999999; //first period is 3-3:59:99:99
        for(int period=2;period<endTimeMinutes.length;++period)
        	endTimeMinutes[period] = endTimeMinutes[period-1] + 30; //all other periods are 30 minutes long
        endTimeMinutes[40] = endTimeMinutes[39] + 3*60; //last period is 12 - 2:59:99:99 AM
        
        int seed = Util.getIntegerValueFromPropertyMap(propertyMap, ModelSeedProperty);
        random = new MersenneTwister(seed);

        //initialize containers
        transitTrips = new ArrayList<Trip>();
        valueOfTimeByPersonNumber = new HashMap<Long,Float>();
        valueOfTimeByHhId =  new HashMap<Long,Float>();
        personTypeByPersonNumber =  new HashMap<Long,Integer>();
        
        //set up the trace
        seek = new Boolean(Util.getStringValueFromPropertyMap(propertyMap, SeekProperty));
        String[] hhids = Util.getStringArrayFromPropertyMap(propertyMap, TraceHouseholdList);
        traceHHIds = new ArrayList<Long>();
        if(hhids.length>0){
        	for(String hhid:hhids){
        		traceHHIds.add(new Long(hhid.replace(" ","")));
        	}
		}
        
        //set up the UEC for determining whether to re-simulate the transit path choice
        String uecPath = Util.getStringValueFromPropertyMap(propertyMap,CtrampApplication.PROPERTIES_UEC_PATH);
        String uecFileName = Paths.get(uecPath,propertyMap.get(ResimulateTransitPathUECProperty)).toString();
        int dataPage = Util.getIntegerValueFromPropertyMap(propertyMap,
        		ResimulateTransitPathDataPageProperty);
        int identifyPage = Util.getIntegerValueFromPropertyMap(propertyMap,
        		ResimulateTransitPathIdentifyPageProperty);
        File uecFile = new File(uecFileName);
        resimulateDMU = new ResimulateTransitPathDMU();
        identifyTripToResimulateUEC = new UtilityExpressionCalculator(uecFile, identifyPage, dataPage, propertyMap, resimulateDMU);
        index         = new IndexValues();

	}
	
	/**
	 * Read the input individual and joint trip files. This function calls the method
	 * @readTripList for each table.
	 */
	public void readInputFiles(){
		
        String directory = Util.getStringValueFromPropertyMap(propertyMap, DirectoryProperty);
        String indivTripFile = directory
                + Util.getStringValueFromPropertyMap(propertyMap, IndivTripDataFileProperty);
        indivTripFile = insertIterationNumber(indivTripFile,iteration);
        String jointTripFile = directory
                + Util.getStringValueFromPropertyMap(propertyMap, JointTripDataFileProperty);
        jointTripFile = insertIterationNumber(jointTripFile,iteration);

        String personFile = directory
                + Util.getStringValueFromPropertyMap(propertyMap, PersonDataFileProperty); 
        personFile = insertIterationNumber(personFile,iteration);
       
        //start with individual trips
        TableDataSet indivTripDataSet = readTableData(indivTripFile);
        readTripList(indivTripDataSet, false);
        
        //now read joint trip data
        TableDataSet jointTripDataSet = readTableData(jointTripFile);
        readTripList(jointTripDataSet, true);
        
        //read person data
        TableDataSet personData = readTableData(personFile);
        readPersonData(personData);
        
        // create output files
        String outIndivTripFileName = directory
                + Util.getStringValueFromPropertyMap(propertyMap, ResimulateTransitPathIndividualOutputFileProperty);
        outIndivTripFileName = insertIterationNumber(outIndivTripFileName,iteration);
        String outJointTripFileName = directory
                + Util.getStringValueFromPropertyMap(propertyMap, ResimulateTransitPathJointOutputFileProperty);
        outJointTripFileName = insertIterationNumber(outJointTripFileName,iteration);

        outputIndivTripWriter = createOutputFile(outIndivTripFileName);
        outputJointTripWriter = createOutputFile(outJointTripFileName);
        
        writeIndividualTripFileHeader(outputIndivTripWriter);
        writeJointTripFileHeader(outputJointTripWriter);
      
	}

	/**
	 * Iterate through trips and process
	 */
	private void run(){
		
			
		//iterate through data and calculate transit path, write results
		for(Trip trip : transitTrips ){
			
			//skip trip if doesn't need to be resimulated
			if(resimulateTransitTrip(trip)== false){
				if(trip.getJoint()==0)
					writeTrip(trip,outputIndivTripWriter);
				else
					writeTrip(trip,outputJointTripWriter);
				
				continue;
			}
				
			++resimulatedTransitTrips;
			
			TransitWalkAccessDMU walkDmu =  new TransitWalkAccessDMU();
	    	TransitDriveAccessDMU driveDmu  = new TransitDriveAccessDMU();
	    	double[][] bestTaps = null;

			long hhid = trip.getHhid();
			int originMaz = trip.getOriginMaz();
			int destinationMaz = trip.getDestinationMaz();
			int originTaz = mgraManager.getTaz(originMaz);
			int destinationTaz = mgraManager.getTaz(destinationMaz);
			int mode = trip.getMode();
			int inbound = trip.getInbound();
			int period = trip.getDepartPeriod();
			int joint = trip.getJoint();
			
			int todPeriod = ModelStructure.getSkimPeriodIndex(period);
			
			//get the value of time for this person (or hh if joint tour)
			long personNumber = trip.getPersonNumber();
			float valueOfTime = (joint == 1) ? valueOfTimeByHhId.get(hhid) : valueOfTimeByPersonNumber.get(personNumber);
			
			int personType = personTypeByPersonNumber.get(personNumber);
			
	    	boolean debug = false;
			if(traceHHIds.contains(hhid))
				debug = true;
			
			float odDistance  = (float) tazDistanceCalculator.getTazToTazDistance(ModelStructure.AM_SKIM_PERIOD_INDEX, originTaz, destinationTaz);
		

			if(modelStructure.getTripModeIsWalkTransit(mode))
				bestTaps = bestPathCalculator.getBestTapPairs(walkDmu, driveDmu, bestPathCalculator.WTW, originMaz, destinationMaz, todPeriod, debug, logger, odDistance);
			else
				if(inbound==0)
					bestTaps =  bestPathCalculator.getBestTapPairs(walkDmu, driveDmu, bestPathCalculator.DTW, originMaz, destinationMaz, todPeriod, debug, logger, odDistance);
				else
					bestTaps =  bestPathCalculator.getBestTapPairs(walkDmu, driveDmu, bestPathCalculator.WTD, originMaz, destinationMaz, todPeriod, debug, logger, odDistance);
			
			//if no best taps for the trip, log the error and move on to the next record
			if(bestTaps==null){
				++tripsWithNoTransitPath;
				long hh_id = trip.getHhid();
				long per_num = trip.getPersonNumber();
				int tour = trip.getTourid();
				int stop = trip.getStopid();
				logger.error("Transit trip with no transit path. HHID: "+hh_id+" PERID "+per_num+" TOUR "+tour+" INBOUND "+inbound+" STOP "+stop);
				continue;
			}
	        //set person specific variables and re-calculate best tap pair utilities
	    	walkDmu.setApplicationType(bestPathCalculator.APP_TYPE_TRIPMC);
	    	walkDmu.setTourCategoryIsJoint(joint);
	    	walkDmu.setPersonType(joint==1 ? walkDmu.getPersonType() : personType);
	    	walkDmu.setValueOfTime(valueOfTime);
	    	driveDmu.setApplicationType(bestPathCalculator.APP_TYPE_TRIPMC);
	    	driveDmu.setTourCategoryIsJoint(joint);
	     	driveDmu.setPersonType(joint==1 ? driveDmu.getPersonType() : personType);
	     	driveDmu.setValueOfTime(valueOfTime);
			
	     	//recalculate utilities for best walk and drive paths for person attributes
			if(modelStructure.getTripModeIsWalkTransit(mode))
				bestTaps = bestPathCalculator.calcPersonSpecificUtilities(bestTaps, walkDmu, driveDmu, bestPathCalculator.WTW, originMaz, destinationMaz, todPeriod, debug, logger, odDistance);
			else{
				if(inbound==0)
					bestTaps = bestPathCalculator.calcPersonSpecificUtilities(bestTaps, walkDmu, driveDmu, bestPathCalculator.DTW, originMaz, destinationMaz, todPeriod, debug, logger, odDistance);
				else
					bestTaps = bestPathCalculator.calcPersonSpecificUtilities(bestTaps, walkDmu, driveDmu, bestPathCalculator.WTD, originMaz, destinationMaz, todPeriod, debug, logger, odDistance);
			}
			
			float rnum = (float) random.nextDouble();
			int pathIndex = bestPathCalculator.chooseTripPath(rnum, bestTaps, debug, logger);
			int boardTap = (int) bestTaps[pathIndex][0];
			int alightTap = (int)  bestTaps[pathIndex][1];
			int set = (int)  bestTaps[pathIndex][2];
       	
			trip.setBoardingTap(boardTap);
			trip.setAlightingTap(alightTap);
			trip.setSet(set);
			
			//write results
			if(trip.getJoint()==0)
				writeTrip(trip,outputIndivTripWriter);
			else
				writeTrip(trip,outputJointTripWriter);

		}
		if(tripsWithNoTransitPath>0)
			logger.info("There are "+tripsWithNoTransitPath+" transit trips with no valid transit path");
		
		logger.info("Resimulated "+resimulatedTransitTrips+" transit trips");
		outputIndivTripWriter.close();
		outputJointTripWriter.close();
	}
	
	

	/**
	 * Read the person data file and store required data in hashmaps
	 * @param personData
	 */
	public void readPersonData(TableDataSet personData){
		
        for(int row = 1; row<=personData.getRowCount();++row){
        	long hhid = (long) personData.getValueAt(row, "hh_id");
        	long personNumber = (long) personData.getValueAt(row,"person_num");
        	float valueOfTime = personData.getValueAt(row,"value_of_time");
        	String personTypeString = personData.getStringValueAt(row,"type");
        	int personType = getPersonType(personTypeString);
           	personTypeByPersonNumber.put(personNumber, personType);
                  	
        	valueOfTimeByPersonNumber.put(personNumber, valueOfTime);
        	if(valueOfTimeByHhId.containsKey(hhid)){
        		float existingVOTForHH = valueOfTimeByHhId.get(hhid);
        		if(valueOfTime>existingVOTForHH)
        			valueOfTimeByHhId.put(hhid,valueOfTime);
        	}else{
    			valueOfTimeByHhId.put(hhid,valueOfTime);
        	}
        }

	}

	/**
	 * Read the trip list in the TableDataSet. 
	 * 
	 * @param inputTripTableData The TableDataSet containing the CT-RAMP output trip file.
	 * @param jointTripData A boolean indicating whether the data is for individual or joint trips.
	 */
	public void readTripList(TableDataSet inputTripTableData, boolean jointTripData){
		
         for(int row = 1; row <= inputTripTableData.getRowCount();++row){
        	
           	long hhid = (long) inputTripTableData.getValueAt(row,"hh_id");	
           	long personId=-1;
           	int personNumber=-1;
           	if(jointTripData==false){
           		personId = (long) inputTripTableData.getValueAt(row,"person_id");
           		personNumber = (int) inputTripTableData.getValueAt(row,"person_num");
           		
           	}
        	int tourid = (int) inputTripTableData.getValueAt(row,"tour_id");
        	int stopid = (int) inputTripTableData.getValueAt(row,"stop_id");
        	int inbound = (int)inputTripTableData.getValueAt(row,"inbound");
         	int oMaz = (int) inputTripTableData.getValueAt(row,"orig_mgra");
        	int dMaz = (int) inputTripTableData.getValueAt(row,"dest_mgra");
        	int depPeriod = (int) inputTripTableData.getValueAt(row,"stop_period");
        	float depTime = simulateExactTime(depPeriod);
        	float sRate = inputTripTableData.getValueAt(row,"sampleRate");
          	int mode = (int) inputTripTableData.getValueAt(row,"trip_mode");
            int avAvailable = (int) inputTripTableData.getValueAt(row,"avAvailable");  	
        	int boardingTap = (int) inputTripTableData.getValueAt(row,"trip_board_tap");  
        	int alightingTap = (int) inputTripTableData.getValueAt(row,"trip_alight_tap");  
        	String tour_purpose	= inputTripTableData.getStringValueAt(row, "tour_purpose");
        	String orig_purpose	= inputTripTableData.getStringValueAt(row, "orig_purpose");
        	String dest_purpose = inputTripTableData.getStringValueAt(row, "dest_purpose");
        	float distance = inputTripTableData.getValueAt(row,"trip_dist");
        	
        	int num_participants=-1;
        	if(jointTripData){
        		num_participants = (int) inputTripTableData.getValueAt(row,"num_participants");
        	}
        	int tour_mode = (int)inputTripTableData.getValueAt(row,"tour_mode");
        	
        	int set = (int)inputTripTableData.getValueAt(row,"set"); 
        	
            if(modelStructure.getTripModeIsTransit(mode)){
        		Trip trip = new Trip(hhid,personId,personNumber,tourid,stopid,inbound,(jointTripData?1:0),oMaz,dMaz,depPeriod,depTime,sRate,mode,boardingTap,alightingTap,set);
        		trip.setAvAvailable(avAvailable);
        		trip.setTourPurpose(tour_purpose);
        		trip.setOriginPurpose(orig_purpose);
        		trip.setDestinationPurpose(dest_purpose);
        		trip.setDistance(distance);
        		trip.setNumberParticipants(num_participants);
        		trip.setTourMode(tour_mode);
        		if(num_participants>-1)
        			trip.setJoint(1);
        		transitTrips.add(trip);
        	} 
        }
 	}
	
	/**
	 * Calculate person type value based on string.
	 * @param personTypeString
	 * @return
	 */
	private int getPersonType(String personTypeString){
		
		for(int i =0;i<Person.personTypeNameArray.length;++i){
			
			if(personTypeString.compareTo(Person.personTypeNameArray[i])==0)
				return i;
			
		}
	   
		//should never be here
		return -1;
		
	}
	
	/** 
	 * Start a new matrix server connection.
	 * 
	 * @param properties
	 */
	private void startMatrixServer(HashMap<String, String> properties) {
	        String serverAddress = (String) properties.get("RunModel.MatrixServerAddress");
	        int serverPort = new Integer((String) properties.get("RunModel.MatrixServerPort"));
	        logger.info("connecting to matrix server " + serverAddress + ":" + serverPort);

	        try{

	            MatrixDataManager mdm = MatrixDataManager.getInstance();
	            MatrixDataServerIf ms = new MatrixDataServerRmi(serverAddress, serverPort, MatrixDataServer.MATRIX_DATA_SERVER_NAME);
	            ms.testRemote(Thread.currentThread().getName());
	            mdm.setMatrixDataServerObject(ms);

	        } catch (Exception e) {
	            logger.error("could not connect to matrix server", e);
	            throw new RuntimeException(e);

	        }

	    }
		/**
		 * Simulate the exact time for the period.
		 * 
		 * @param period The time period (1->40)
		 * @return The exact time in double precision (number of minutes past 3 AM)
		 */
		public float simulateExactTime(int period){
			
			double lowerEnd = endTimeMinutes[period-1];
			double upperEnd = endTimeMinutes[period];
	        double randomNumber = random.nextDouble();
	        
	        float time = (float) ((upperEnd - lowerEnd) * randomNumber + lowerEnd);

			return time;
		}

	    /**
	     * Determine whether to resimulate transit trip.
	     * 
	     */
		public boolean resimulateTransitTrip(Trip trip){
			
			int todPeriod = ModelStructure.getSkimPeriodIndex(trip.getDepartPeriod());

			resimulateDMU.setOriginMaz(trip.getOriginMaz());
			resimulateDMU.setDestinationMaz(trip.getDestinationMaz());
			resimulateDMU.setBoardingTap(trip.getBoardingTap());
			resimulateDMU.setAlightingTap(trip.getAlightingTap());
			resimulateDMU.setSet(trip.getSet());
			resimulateDMU.setTOD(todPeriod);
		        
			// set up the index and dmu objects
		    index.setOriginZone(trip.getBoardingTap());
		    index.setDestZone(trip.getAlightingTap());
		       
		    // solve
		    float util = (float)identifyTripToResimulateUEC.solve(index, resimulateDMU, null)[0];  
		    if(util>0)
		    	return true;
			return false;
		}
		
		
		/** 
		 * A simple helper function to insert the iteration number into the file name.
		 * 
		 * @param filename The input file name (ex: inputFile.csv)
		 * @param iteration The iteration number (ex: 3)
		 * @return The new string (ex: inputFile_3.csv)
		 */
		private String insertIterationNumber(String filename, int iteration){
			
			String newFileName = filename.replace(".csv", "_"+new Integer(iteration).toString()+".csv");
			return newFileName;
		}

		/**
		 * Read data into inputDataTable tabledataset.
		 * 
		 */
		private TableDataSet readTableData(String inputFile){
			
			TableDataSet tableDataSet = null;
			
			logger.info("Begin reading the data in file " + inputFile);
		    
		    try
		    {
		    	OLD_CSVFileReader csvFile = new OLD_CSVFileReader();
		    	tableDataSet = csvFile.readFile(new File(inputFile));
		    } catch (IOException e)
		    {
		    	throw new RuntimeException(e);
	        }
	        logger.info("End reading the data in file " + inputFile);
	        
	        return tableDataSet;
		}
		
		/**
		 * Create the output file and write a header record.
		 */
		private PrintWriter createOutputFile(String outputFile){
	        
			logger.info("Creating file " + outputFile);
			PrintWriter outWriter = null;
			
			try
	        {
	            outWriter = new PrintWriter(new BufferedWriter(new FileWriter(outputFile)));
	        } catch (IOException e)
	        {
	            logger.fatal("Could not open file " + outputFile + " for writing\n");
	            throw new RuntimeException();
	        }
	        
	        return outWriter;

		}
		
		/**
		 * Write a header record for individual trip records.
		 * 
		 * @param printWriter
		 */
		private void writeIndividualTripFileHeader(PrintWriter printWriter){
			
			
	        String headerString = new String(
			"hh_id,person_id,person_num,tour_id,stop_id,inbound,tour_purpose,orig_purpose,dest_purpose,orig_mgra,dest_mgra,trip_dist,"+
	        "parking_mgra,stop_period,trip_mode,trip_board_tap,trip_alight_tap,tour_mode,set,sampleRate,avAvailable");

	        printWriter.println(headerString);

		}
		/**
		 * Write a header record for joint trip records.
		 * 
		 * @param printWriter
		 */
		private void writeJointTripFileHeader(PrintWriter printWriter){
			
			
	        String headerString = new String(
			"hh_id,tour_id,stop_id,inbound,tour_purpose,orig_purpose,dest_purpose,orig_mgra,dest_mgra,trip_dist,parking_mgra,stop_period,"
			+"trip_mode,num_participants,trip_board_tap,trip_alight_tap,tour_mode,set,sampleRate,avAvailable");

	        printWriter.println(headerString);

		}
		
		/**
		 * Write the trip to the PrintWriter and flush the file.
		 * @param trip
		 * @param writer
		 */
		private void writeTrip(Trip trip, PrintWriter writer){
			
			String outputRecord= new String(trip.getHhid() + ",");
			
			if(trip.getJoint()==0){
				outputRecord = outputRecord + new String(trip.getPersonId() + "," + trip.getPersonNumber() + ",");
			}
		
			outputRecord = outputRecord + new String(
					trip.getTourid() + ","
					+ trip.getStopid() + ","
					+ trip.getInbound() + ","
					+ trip.getTourPurpose() + ","
					+ trip.getOriginPurpose() + ","
					+ trip.getDestinationPurpose() + ","
					+ trip.getOriginMaz() + ","
					+ trip.getDestinationMaz() + ","
					+ trip.getDistance() + ","
					+ trip.getParkingMaz() + ","
					+ trip.getDepartPeriod() + ","
					+ trip.getMode() + ",");
			
			if(trip.getJoint()==1){
				outputRecord = outputRecord + new String(trip.getNumberParticipants()+",");
			}
			
			outputRecord = outputRecord + new String(
					trip.getBoardingTap() + ","
					+ trip.getAlightingTap() + ","
					+ trip.getTourMode() + ","
					+ trip.getSet() + ","
					+ trip.getSampleRate() + ","
					+ trip.getAvAvailable() 
					);
			writer.println(outputRecord);
			writer.flush();
		}
		
		/**
		 * Main run method
		 * @param args
		 */
		public static void main(String[] args) {

	        String propertiesFile = null;
	        HashMap<String, String> pMap;

	        logger.info(String.format("Resimulate Transit Path Program using CT-RAMP version ",
	                CtrampApplication.VERSION));

	        logger.info(String.format("Resimulating transit paths for transit trips in congested Tap-pairs"));

	        int iteration=0;
	        
	        if (args.length == 0)
	        {
	            logger.error(String
	                    .format("no properties file base name (without .properties extension) was specified as an argument."));
	            return;
	        } else {
	        	propertiesFile = args[0];

		        for (int i = 1; i < args.length; ++i)
		        {
		            if (args[i].equalsIgnoreCase("-iteration"))
		            {
		                iteration = Integer.valueOf(args[i + 1]);
		            }
		           
		        }
	        }
	        
	        pMap = ResourceUtil.getResourceBundleAsHashMap(propertiesFile);
	        NewTransitPathModel transitPathModel = new NewTransitPathModel(pMap, iteration);
	        transitPathModel.readInputFiles();
	        transitPathModel.run();

	    
		}

}
