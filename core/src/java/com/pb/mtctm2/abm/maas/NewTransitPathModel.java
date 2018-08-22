package com.pb.mtctm2.abm.maas;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;

import org.apache.log4j.Logger;

import com.pb.common.calculator.MatrixDataManager;
import com.pb.common.calculator.MatrixDataServerIf;
import com.pb.common.datafile.OLD_CSVFileReader;
import com.pb.common.datafile.TableDataSet;
import com.pb.common.math.MersenneTwister;
import com.pb.mtctm2.abm.accessibilities.AutoTazSkimsCalculator;
import com.pb.mtctm2.abm.accessibilities.BestTransitPathCalculator;
import com.pb.mtctm2.abm.accessibilities.DriveTransitWalkSkimsCalculator;
import com.pb.mtctm2.abm.accessibilities.WalkTransitDriveSkimsCalculator;
import com.pb.mtctm2.abm.accessibilities.WalkTransitWalkSkimsCalculator;
import com.pb.mtctm2.abm.application.SandagModelStructure;
import com.pb.mtctm2.abm.ctramp.MatrixDataServer;
import com.pb.mtctm2.abm.ctramp.MatrixDataServerRmi;
import com.pb.mtctm2.abm.ctramp.MgraDataManager;
import com.pb.mtctm2.abm.ctramp.ModelStructure;
import com.pb.mtctm2.abm.ctramp.TazDataManager;
import com.pb.mtctm2.abm.ctramp.TransitDriveAccessDMU;
import com.pb.mtctm2.abm.ctramp.TransitWalkAccessDMU;
import com.pb.mtctm2.abm.ctramp.Util;

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

    //for tracing
    private boolean seek;
    private ArrayList<Long> traceHHIds;
    
    private static final String DirectoryProperty = "Project.Directory";
    private static final String IndivTripDataFileProperty = "Results.IndivTripDataFile";
    private static final String JointTripDataFileProperty = "Results.JointTripDataFile";
    private static final String ModelSeedProperty = "Model.Random.Seed";
    private static final String SeekProperty = "Seek";
    private static final String TraceHouseholdList = "Debug.Trace.HouseholdIdList";

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

        transitTrips = new ArrayList<Trip>();
        
        //set up the trace
        seek = new Boolean(Util.getStringValueFromPropertyMap(propertyMap, SeekProperty));
        String[] hhids = Util.getStringArrayFromPropertyMap(propertyMap, TraceHouseholdList);
        traceHHIds = new ArrayList<Long>();
        if(hhids.length>0){
        	for(String hhid:hhids){
        		traceHHIds.add(new Long(hhid));
        	}
		}
	}
	
	/**
	 * Read the input individual and joint trip files. This function calls the method
	 * @readTripList for each table.
	 */
	public void readInputTrips(){
		
        String directory = Util.getStringValueFromPropertyMap(propertyMap, DirectoryProperty);
        String indivTripFile = directory
                + Util.getStringValueFromPropertyMap(propertyMap, IndivTripDataFileProperty);
        indivTripFile = insertIterationNumber(indivTripFile,iteration);
        String jointTripFile = directory
                + Util.getStringValueFromPropertyMap(propertyMap, JointTripDataFileProperty);
        jointTripFile = insertIterationNumber(jointTripFile,iteration);

         
        //start with individual trips
        TableDataSet indivTripDataSet = readTableData(indivTripFile);
        readTripList(indivTripDataSet, false);
        
        //now read joint trip data
        TableDataSet jointTripDataSet = readTableData(jointTripFile);
        readTripList(jointTripDataSet, true);
        
	}

	/**
	 * Iterate through trips and process
	 */
	private void run(){
		
		TableDataSet mgraData = mgraManager.getMgraTableDataSet();
		TransitWalkAccessDMU walkDmu =  new TransitWalkAccessDMU();
    	TransitDriveAccessDMU driveDmu  = new TransitDriveAccessDMU();
    	double[][] bestTaps = null;
		boolean debug = false;
		
		//iterate through data and calculate
		for(Trip trip : transitTrips ){
		
			long hhid = trip.getHhid();
			int originMaz = trip.getOriginMaz();
			int destinationMaz = trip.getDestinationMaz();
			int originTaz = mgraManager.getTaz(originMaz);
			int destinationTaz = mgraManager.getTaz(destinationMaz);
			int mode = trip.getMode();
			int inbound = trip.getInbound();
			int period = trip.getDepartPeriod();
			int joint = trip.getJoint();
			
			if(traceHHIds.contains(hhid))
				debug = true;
			
			float odDistance  = (float) tazDistanceCalculator.getTazToTazDistance(ModelStructure.AM_SKIM_PERIOD_INDEX, originTaz, destinationTaz);
		
			int accessEgressMode = -1;
			if(modelStructure.getTripModeIsWalkTransit(mode))
				accessEgressMode=bestPathCalculator.WTW;
			else if (inbound==0)
				accessEgressMode = bestPathCalculator.DTW;
			else 
				accessEgressMode = bestPathCalculator.WTD;

			bestTaps = bestPathCalculator.getBestTapPairs(walkDmu, driveDmu, accessEgressMode, originMaz, destinationMaz, period, debug, logger, odDistance);
			

	        //set person specific variables and re-calculate best tap pair utilities
	    	walkDmu.setApplicationType(bestPathCalculator.APP_TYPE_TRIPMC);
	    	walkDmu.setTourCategoryIsJoint(joint);
	 //   	walkDmu.setPersonType(joint==1 ? walkDmu.personType : tripMcDmuObject.getPersonType());
	 //   	walkDmu.setValueOfTime((float)tripMcDmuObject.getValueOfTime());
	    	driveDmu.setApplicationType(bestPathCalculator.APP_TYPE_TRIPMC);
	    	driveDmu.setTourCategoryIsJoint(joint);
	  //  	driveDmu.setPersonType(joint==1 ? driveDmu.personType : tripMcDmuObject.getPersonType());
	   // 	driveDmu.setValueOfTime((float)tripMcDmuObject.getValueOfTime());

			
			
			
			
			
			double[] bestUtilities = bestPathCalculator.getBestUtilities();
			
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
           	int personNumber=-1;
           	if(jointTripData==false)
           		personNumber = (int) inputTripTableData.getValueAt(row,"person_num");
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
        	int set = (int)inputTripTableData.getValueAt(row,"set"); 
        	
           if(modelStructure.getTripModeIsTransit(mode)){
        		Trip trip = new Trip(hhid,personNumber,tourid,stopid,inbound,(jointTripData?1:0),oMaz,dMaz,depPeriod,depTime,sRate,mode,boardingTap,alightingTap,set);
        		transitTrips.add(trip);
        	} 
        }
 	}

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

}
