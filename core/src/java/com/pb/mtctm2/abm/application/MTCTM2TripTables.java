package com.pb.mtctm2.abm.application;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.Serializable;
import java.util.HashMap;
import java.util.Properties;
import java.util.ResourceBundle;

import org.apache.log4j.Logger;

import com.pb.mtctm2.abm.ctramp.TapDataManager;
import com.pb.mtctm2.abm.ctramp.TazDataManager;
import com.pb.common.calculator.MatrixDataServerIf;
import com.pb.common.datafile.OLD_CSVFileReader;
import com.pb.common.datafile.CSVFileWriter;
import com.pb.common.datafile.TableDataSet;
import com.pb.common.matrix.Matrix;
import com.pb.common.util.ResourceUtil;
import com.pb.mtctm2.abm.ctramp.CtrampApplication;
import com.pb.mtctm2.abm.ctramp.MatrixDataServer;
import com.pb.mtctm2.abm.ctramp.MatrixDataServerRmi;
import com.pb.mtctm2.abm.ctramp.MgraDataManager;
import com.pb.mtctm2.abm.ctramp.Util;
import com.pb.mtctm2.abm.reports.SkimBuilder;

public class MTCTM2TripTables {

	private static Logger logger = Logger.getLogger(MTCTM2TripTables.class);

    private  TableDataSet indivTripData;
    private  TableDataSet jointTripData;
    
    //Some parameters
    private int[] modeIndex;  // an index array, dimensioned by number of total modes, returns 0=auto modes, 1=non-motor, 2=transit, 3= other
    private int[] matrixIndex; // an index array, dimensioned by number of modes, returns the element of the matrix array to store value
    
    //array modes: AUTO, NON-MOTORIZED, TRANSIT,  OTHER
	private int autoModes=0;
	private int tranModes=0;
	private int nmotModes=0;
	private int othrModes=0;
    
    //one file per time period
    private int numberOfPeriods;
   
    private String purposeName[] = {"Work","University","School","Escort","Shop","Maintenance","EatingOut","Visiting","Discretionary","WorkBased"};
    
    // matrices are indexed by modes
    private Matrix[][] matrix;
     
    private Properties properties;
    private HashMap<String, String> rbMap;
    private MgraDataManager mgraManager;
    private TazDataManager tazManager;
    private TapDataManager tapManager;
    private SandagModelStructure modelStructure;
    
    private float[][] CBDVehicles; // an array of parked vehicles in MGRAS by period
    private float[][] PNRVehicles; // an array of parked vehicles at TAPs by period
    
    private float sampleRate;
    private int iteration;
	private String directory;
	private String matrixFileExtension = "mat";
 	
	private MatrixDataServerIf ms;
        
    private HashMap<String, Float> averageOcc3Plus;  //a HashMap of average occupancies for 3+ vehicles by tour purpose
    
    public MazSets mazSets;
    
    public int numSkimSets;
    
    public MTCTM2TripTables(String resourceBundleName, int iteration, float sampleRate){

        HashMap<String,String> rbMap = ResourceUtil.getResourceBundleAsHashMap(resourceBundleName);
        properties = new Properties();
        for (String key : rbMap.keySet()) 
        	properties.put(key,rbMap.get(key));
        directory = properties.getProperty("Project.Directory");
        
        numSkimSets = Integer.valueOf(properties.getProperty("utility.bestTransitPath.skim.sets"));
        
		tazManager = TazDataManager.getInstance(rbMap);
		tapManager = TapDataManager.getInstance(rbMap);
		mgraManager = MgraDataManager.getInstance(rbMap);
        
		modelStructure = new SandagModelStructure();
		
		//Time period limits
		numberOfPeriods = modelStructure.getNumberModelPeriods();
	
		//number of modes
		modeIndex = new int[modelStructure.MAXIMUM_TOUR_MODE_ALT_INDEX+1];
		matrixIndex = new int[modeIndex.length];
		
		//set the mode arrays
		for(int i=1;i<modeIndex.length;++i){
			if(modelStructure.getTourModeIsSovOrHov(i)){
				modeIndex[i] = 0;
				matrixIndex[i]= autoModes;
				++autoModes;
			}else if(modelStructure.getTourModeIsNonMotorized(i)){
				modeIndex[i] = 1;
				matrixIndex[i]= nmotModes;
				++nmotModes;
			}else if(modelStructure.getTourModeIsWalkTransit(i)|| modelStructure.getTourModeIsDriveTransit(i)){
				modeIndex[i] = 2;
				matrixIndex[i]= tranModes;
				++tranModes;
			}else{
				modeIndex[i] = 3;
				matrixIndex[i]= othrModes;
				++othrModes;
			}
		}
		readOccupancies();
		//Initialize arrays (need for all periods, so initialize here)
		CBDVehicles = new float[mgraManager.getMaxMgra()+1][numberOfPeriods];
		PNRVehicles = new float[tapManager.getMaxTap()+1][numberOfPeriods];
		
		setSampleRate(sampleRate);
		this.iteration = iteration; 
		
		//create mazSets
		mazSets = new MazSets();
	}
	
	/**
	 * Read occupancies from the properties file and store in the averageOcc3Plus HashMap
	 */
	public void readOccupancies(){
	
		averageOcc3Plus = new HashMap<String,Float>();
		
		for(int i=0;i<purposeName.length;++i){
			String searchString = "occ3plus.purpose." + purposeName[i];
			float occupancy = new Float(properties.getProperty(searchString));
			averageOcc3Plus.put(purposeName[i], occupancy);
		}
	}

	/**
	 * Initialize all the matrices for the given time period.
	 *
	 * @param periodName  The name of the time period.
	 */
	public void initializeMatrices(String periodName){
		
		//get the taz and tap matrix sizes
        int tazs = tazManager.getMaxTaz();
		int taps = tapManager.getMaxTap();
		
		//Initialize matrices; one for each mode group (auto, non-mot, tran, other)
		int numberOfModes = 4;
		matrix = new Matrix[numberOfModes][];
		for(int i = 0; i < numberOfModes; ++ i){
			
			String modeName;
			
			if(i==0){
				//dim TAZ to TAZ auto matrices + MAZ to MAZ matrices
				matrix[i] = new Matrix[autoModes + mazSets.numSets];
				for(int j=0;j<autoModes;++j){
					modeName = modelStructure.getModeName(j+1);
					matrix[i][j] = new Matrix(modeName+"_"+periodName,"",tazs,tazs);
					
					mazSets.autoMatOffset = j;
				}
				
				//dim MAZ to MAZ auto matrices
				for(int k=0;k<mazSets.numSets;k++){
			      matrix[i][mazSets.autoMatOffset + k+1] = new Matrix("MAZ_AUTO"+"_"+(k+1)+"_"+periodName,"",mazSets.numZones[k],mazSets.numZones[k]);	
				}
				
			}else if(i==1){
				matrix[i] = new Matrix[nmotModes];
				for(int j=0;j<nmotModes;++j){
					modeName = modelStructure.getModeName(j+1+autoModes);
					matrix[i][j] = new Matrix(modeName+"_"+periodName,"",tazs,tazs);
				}
			}else if(i==2){
				matrix[i] = new Matrix[tranModes*numSkimSets];
				for(int j=0;j<tranModes;++j){
					for(int k=0;k<numSkimSets;++k){
						modeName = modelStructure.getModeName(j+1+autoModes+nmotModes);
						String setName = String.valueOf(k+1);
						matrix[i][(j*numSkimSets)+k] = new Matrix(modeName+"_set"+setName+"_"+periodName,"",taps,taps);
					}
				}
			}else{
				matrix[i] = new Matrix[othrModes];
				for(int j=0;j<othrModes;++j){
					modeName = modelStructure.getModeName(j+1+autoModes+nmotModes+tranModes);
					matrix[i][j] = new Matrix(modeName+"_"+periodName,"",tazs,tazs);
				}
			}
		}
	}
	
	
	/**
	 * Create trip tables for all time periods and modes.
	 * This is the main entry point into the class; it should be called
	 * after instantiating the SandagTripTables object.
	 * 
	 */
	public void createTripTables(){
		

		//Open the individual trip file 
		String indivTripFile = properties.getProperty("Results.IndivTripDataFile");
		indivTripFile = formFileName(directory + indivTripFile, iteration);		
		indivTripData = openTripFile(indivTripFile);
		
		//Open the joint trip file 
		String jointTripFile = properties.getProperty("Results.JointTripDataFile");
		jointTripFile = formFileName(directory + jointTripFile, iteration);
		jointTripData = openTripFile(jointTripFile);

	    // connect to matrix server
        connectToMatrixServer();
        
        // add time, distance, and cost to trip files
        addTripFields(indivTripData);
        addTripFields(jointTripData);
        
        // write out updated trip tables 
        writeTripFile(indivTripData, indivTripFile);
        writeTripFile(jointTripData, jointTripFile);
        
        //Iterate through periods so that we don't have to keep
		//trip tables for all periods in memory.
		for(int i=0;i<numberOfPeriods;++i){
			
			//Initialize the matrices
			initializeMatrices(modelStructure.getModelPeriodLabel(i));
	
			//process trips
			processTrips(i, indivTripData);
			processTrips(i, jointTripData);

			//write matrices
			writeTrips(i);
	        
		}
        
		//write the vehicles by parking-constrained MGRA
		String CBDFile = properties.getProperty("Results.CBDFile");
		writeCBDFile(directory+CBDFile);

		//write the vehicles by PNR lot TAP
		String PNRFile = properties.getProperty("Results.PNRFile");
		writePNRFile(directory+PNRFile);
	}
	
	/**
	 * Open a trip file and return the Tabledataset.
	 * 
	 * @fileName  The name of the trip file
	 * @return The tabledataset
	 */
	public TableDataSet openTripFile(String fileName){
		
	    logger.info("Begin reading the data in file " + fileName);
	    TableDataSet tripData;
	    
        try {
        	OLD_CSVFileReader csvFile = new OLD_CSVFileReader();
            tripData = csvFile.readFile(new File(fileName));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        
        logger.info("End reading the data in file " + fileName);
        return tripData;
	}
	
	/**
	 * This is the main workhorse method in this class.  It iterates over records in the trip file.  
	 * Attributes for the trip record are read, and the trip record is accumulated in the relevant
	 * matrix.
	 * 
	 * @param timePeriod  The time period to process
	 * @param tripData  The trip data file to process
	 */
	public void processTrips(int timePeriod, TableDataSet tripData){
		
        logger.info("Begin processing trips for period "+ timePeriod);

        boolean jointTour = tripData.containsColumn("num_participants");
        int participantsCol = 0;
        if(jointTour){
        	participantsCol = tripData.getColumnPosition("num_participants");
        }
        
        //iterate through the trip data and save trips in arrays
        for(int i = 1; i <= tripData.getRowCount(); ++i){
        
        	int departTime = (int) tripData.getValueAt(i,"stop_period");
        	int period = SandagModelStructure.getModelPeriodIndex(departTime);
            if(period!=timePeriod)
            	continue;
            
        	int originMGRA = (int) tripData.getValueAt(i, "orig_mgra");
        	int destinationMGRA = (int) tripData.getValueAt(i, "dest_mgra");
        	int tripMode = (int) tripData.getValueAt(i,"trip_mode");
        	
        	int originTAZ = mgraManager.getTaz(originMGRA);
        	int destinationTAZ = mgraManager.getTaz(destinationMGRA);
			int inbound = (int) tripData.getValueAt(i,"inbound");
			
			//get trip distance for taz/maz level matrix decision
			float tripdist = (int) tripData.getValueAt(i,"TRIP_DISTANCE");

        	//transit trip - get boarding and alighting tap
        	int boardTap=0;
        	int alightTap=0;
        	int parkingTaz=0;
        	int parkingMGRA=0;
        	int set=0;
        	
        	if(modelStructure.getTourModeIsWalkTransit(tripMode)||modelStructure.getTourModeIsDriveTransit(tripMode)){
        		boardTap=(int) tripData.getValueAt(i,"trip_board_tap");
        		alightTap = (int) tripData.getValueAt(i,"trip_alight_tap");
        		set = (int) tripData.getValueAt(i,"set");
        	}else{
        		parkingMGRA = (int) tripData.getValueAt(i,"parking_mgra");
            }
        	
        	//scale individual person trips by occupancy for vehicle trips (auto modes only)
        	float vehicleTrips=1;
        	
        	if(modelStructure.getTourModeIsS2(tripMode) && !jointTour){
        		vehicleTrips = 0.5f;
        	}else if(modelStructure.getTourModeIsS3(tripMode)  && !jointTour){
            	String tourPurpose = tripData.getStringValueAt(i, "tour_purpose");
            	tourPurpose = tourPurpose.replace(" ","");
            	tourPurpose = tourPurpose.replace("-", "");
        		float occ = averageOcc3Plus.get(tourPurpose);
        		vehicleTrips = 1/occ;
        	}
        	
        	//calculate person trips for all other modes
        	float personTrips=1;
        	if(jointTour){
        		personTrips = (int) tripData.getValueAt(i, participantsCol);
        	}
        	
        	//apply sample rate
        	vehicleTrips = vehicleTrips * 1/sampleRate;
        	personTrips = personTrips * 1/sampleRate;
       	
        	//Store in matrix
        	int mode = modeIndex[tripMode];
    		int mat = matrixIndex[tripMode];
        	if(mode==0){
        		
         		//look up what taz the parking mgra is in, and re-assign the trip destination to the parking taz
        		if(parkingMGRA>0 ){
        			parkingTaz = mgraManager.getTaz(parkingMGRA);
        			destinationTAZ = parkingTaz;
        			destinationMGRA = parkingMGRA; //update dest maz as well for maz to maz assignment if needed
        			CBDVehicles[parkingMGRA][period] = CBDVehicles[parkingMGRA][period] + vehicleTrips;
        		}
        		
        		//is auto trip maz level or taz level
        		if(mazSets.isMazSetTrip(tripdist, originMGRA, destinationMGRA)) {
        			//maz level
        			int mazSet = mazSets.getZoneSet(originMGRA, destinationMGRA);
        			int omaz = mazSets.getNewZoneSetNum(originMGRA);
        			int dmaz = mazSets.getNewZoneSetNum(destinationMGRA);
        			float value = matrix[mode][mazSets.autoMatOffset + mazSet].getValueAt(omaz, dmaz);
            		matrix[mode][mazSets.autoMatOffset + mazSet].setValueAt(omaz, dmaz, (value + vehicleTrips));
        		
        		} else {        
        			//taz level
        			float value = matrix[mode][mat].getValueAt(originTAZ, destinationTAZ);
            		matrix[mode][mat].setValueAt(originTAZ, destinationTAZ, (value + vehicleTrips));
        		}
        		
        	} else if (mode==1){
        		float value = matrix[mode][mat].getValueAt(originTAZ, destinationTAZ);
        		matrix[mode][mat].setValueAt(originTAZ, destinationTAZ, (value + personTrips));
        	
        	} else if (mode==2){
        		
        		if(boardTap==0||alightTap==0)
        			continue;
        		
        		//store transit trips in matrices
        		mat = (matrixIndex[tripMode]*numSkimSets)+set;
        		float value = matrix[mode][mat].getValueAt(boardTap, alightTap);
        		matrix[mode][mat].setValueAt(boardTap, alightTap, (value + personTrips));

        		//Store PNR transit trips in SOV free mode skim (mode 0 mat 0)
        		if(modelStructure.getTourModeIsDriveTransit(tripMode)){
        			
        			// add the vehicle trip portion to the trip table
    				if(inbound==0){ //from origin to lot (boarding tap)
        				int PNRTAZ = tapManager.getTazForTap(boardTap);
    					value = matrix[0][0].getValueAt(originTAZ, PNRTAZ);
    					matrix[0][0].setValueAt(originTAZ,PNRTAZ,(value+vehicleTrips));
    					
    					//and increment up the array of parked vehicles at the lot
    					++PNRVehicles[boardTap][period];
        					
    				}else{  // from lot (alighting tap) to destination 
        				int PNRTAZ = tapManager.getTazForTap(alightTap);
    					value = matrix[0][0].getValueAt(PNRTAZ, destinationTAZ);
    					matrix[0][0].setValueAt(PNRTAZ, destinationTAZ,(value+vehicleTrips));
    				}
       			
        		}
        	
        	} else {
        		float value = matrix[mode][mat].getValueAt(originTAZ, destinationTAZ);
        		matrix[mode][mat].setValueAt(originTAZ, destinationTAZ, (value + personTrips));
    		}
        }
        logger.info("End creating trip tables for period "+ timePeriod);
	}
	
	/**
	 * Get the output trip table file names from the properties file,
	 * and write trip tables for all modes for the given time period.
	 * 
	 * @param period  Time period, which will be used to find the
	 * period time string to append to each trip table matrix file
	 */
	public void writeTrips(int period){
		
		String per = modelStructure.getModelPeriodLabel(period);
		String end = "_" + per;
		String[] fileName = new String[4];
		
		fileName[0] = directory + properties.getProperty("Results.AutoTripMatrix") + end;
		fileName[1] = directory + properties.getProperty("Results.NMotTripMatrix") + end;
		fileName[2] = directory + properties.getProperty("Results.TranTripMatrix") + end; 
		fileName[3] = directory + properties.getProperty("Results.OthrTripMatrix") + end; 
		
		for(int i=0;i<fileName.length;++i) {
			writeMatricesToFile(fileName[i], matrix[i]);
		}
 	}
	
	/**
	 * Utility method to write a set of matrices to disk.
	 * 
	 * @param fileName The file name to write to.
	 * @param m  An array of matrices
	 */
	public void writeMatricesToFile(String fileName, Matrix[] m){
		
		//todo - currently write one matrix to each file since  there is a problem 
		//calling RemoteMatrixDataServer.writeMatrices from RMI if the matrix array has more than 1 matrix
		for (int i=0; i<m.length; i++) {
			
			String matFileName = fileName + "_" + m[i].getName() + "." + matrixFileExtension;
			Matrix[] temp = new Matrix[1];
			temp[0] = m[i];
			ms.writeMatrixFile(matFileName, temp);
			
			logger.info( m[i].getName() + " has " + m[i].getRowCount() + " rows, " + m[i].getColumnCount() + " cols, and a total of " + m[i].getSum() );
			logger.info("Writing " + matFileName);
		}
				
	}
	
	/**
	 * Connect to matrix server
	 */
    private void connectToMatrixServer()
    {
    	
		// get matrix server address and port
		String matrixServerAddress = properties.getProperty("RunModel.MatrixServerAddress");
		int serverPort = Integer.parseInt(properties.getProperty("RunModel.MatrixServerPort"));
		
		ms = new MatrixDataServerRmi(matrixServerAddress, serverPort, MatrixDataServer.MATRIX_DATA_SERVER_NAME);
		ms.testRemote(Thread.currentThread().getName());
        logger.info("connected to matrix data server");
    }

    
    /**
     * Write a file of vehicles parking in parking-constrained areas by MGRA.
     * 
     * @param fileName  The name of the csv file to write to.
     */
    public void writeCBDFile(String fileName){
    	
    	try
    	{
    	    FileWriter writer = new FileWriter(fileName);
    	    
    	    //write header
    	    writer.append("MGRA,");

	    	for(int j=0;j<numberOfPeriods;++j)
	    		writer.append(modelStructure.getModelPeriodLabel(j)+",");

	    	writer.append("Total\n");
	    	   
	    	//iterate through mgras
    	    for(int i =0; i< CBDVehicles.length;++i){
    	    	
    	    	float totalVehicles=0;
    	    	for(int j=0;j<numberOfPeriods;++j){
    	    		totalVehicles += CBDVehicles[i][j];
    	    	}
    	    
    	    	//only write the mgra if there are vehicles parked there
    	    	if(totalVehicles>0){
    	    		
    	    		writer.append(Integer.toString(i));
    	    	
    	    		//iterate through periods
    	    		for(int j=0;j<numberOfPeriods;++j)
    	    			writer.append(","+Float.toString(CBDVehicles[i][j]));
    	
    	    		writer.append(","+Float.toString(totalVehicles)+"\n");
    	    	    writer.flush();
    	    	}
    	    }
    	    writer.flush();
    	    writer.close();
    	}
    	catch(IOException e)
    	{
    	     e.printStackTrace();
    	} 

    }
    
    /**
     * Write a file of vehicles parking in PNR lots by TAP.
     * 
     * @param fileName  The name of the csv file to write to.
     */
    public void writePNRFile(String fileName){
    	
    	try
    	{
    	    FileWriter writer = new FileWriter(fileName);
    	    
    	    //write header
    	    writer.append("TAP,");
    	    
	    	for(int j=0;j<numberOfPeriods;++j)
	    		writer.append(modelStructure.getModelPeriodLabel(j)+",");
	    		
	    	writer.append("Total\n");
    	   
    	    //iterate through taps
    	    for(int i =0; i< PNRVehicles.length;++i){
    	    	
    	    	float totalVehicles=0;
    	    	for(int j=0;j<numberOfPeriods;++j){
    	    		totalVehicles += PNRVehicles[i][j];
    	    	}
    	    	
    	    	//only write the tap if there are vehicles parked there
    	    	if(totalVehicles>0){
    	    		
    	    		writer.append(Integer.toString(i));
    	    	
    	    		//iterate through periods
    	    		for(int j=0;j<numberOfPeriods;++j)
    	    			writer.append(","+Float.toString(PNRVehicles[i][j]));
    	
    	    		writer.append(","+Float.toString(totalVehicles)+"\n");
    	    	    writer.flush();
    	    	}
    	    }
    	    writer.flush();
    	    writer.close();
    	}catch(IOException e)
    	{
    	     e.printStackTrace();
    	} 

    }
    
    /**
     * Set the sample rate
     * @param sampleRate  The sample rate, used for expanding trips
     */
    public void setSampleRate(float sampleRate) {
		this.sampleRate = sampleRate;
	}
    
    
    private String formFileName( String originalFileName, int iteration ) {
        int lastDot = originalFileName.lastIndexOf('.');
        
        String returnString = "";
        if ( lastDot > 0 ) {
            String base = originalFileName.substring( 0, lastDot );
            String ext = originalFileName.substring( lastDot );
            returnString = String.format( "%s_%d%s", base, iteration, ext );
        }
        else {
            returnString = String.format( "%s_%d.csv", originalFileName, iteration );
        }
        return returnString;
    }

	/**
	 * @param args
	 */
	public static void main(String[] args) {

		//command line arguments
		String propertiesName = args[0];
		//args[1] is "-iteration"
		int iteration = new Integer(args[2]).intValue();
		//args[3] is "-sampleRate"
		float sampleRate = new Float(args[4]).floatValue();
		
		//run trip table generator
		MTCTM2TripTables tripTables = new MTCTM2TripTables(propertiesName, iteration, sampleRate);		
		tripTables.createTripTables();

	}
	
	public void writeTripFile(TableDataSet table, String fileName){
		
	    logger.info("Write the trip file " + fileName);	    
        try {
        	CSVFileWriter csvWriter = new CSVFileWriter();
            csvWriter.writeFile(table, new File(fileName));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        
	}
	
	private void addTripFields(TableDataSet table) {
		
		//columns to add: trip_time, trip_distance, trip_cost
		int rowCount = table.getRowCount();
        float[] tripTime = new float[rowCount];
        float[] tripDistance = new float[rowCount];
        float[] tripCost = new float[rowCount];
        int[] fullMode = new int[rowCount];
        
        //setup skim builder class
        SkimBuilder skimBuilder = new SkimBuilder(properties);
        
        //loop through trips and get trip attributes
        for (int i = 0; i < rowCount; i++) {
            int row = i+1;
            
            SkimBuilder.TripAttributes attributes = skimBuilder.getTripAttributes(
                    (int) table.getValueAt(row,"orig_mgra"),
                    (int) table.getValueAt(row,"dest_mgra"),
                    (int) table.getValueAt(row,"trip_mode"),
                    (int) table.getValueAt(row,"trip_board_tap"),
                    (int) table.getValueAt(row,"trip_alight_tap"),
                    (int) table.getValueAt(row,"stop_period"),
                    ((int) table.getValueAt(row,"inbound"))==1,
                    (int) table.getValueAt(row,"set"));            
            
            tripTime[i] = attributes.getTripTime();
            tripDistance[i] = attributes.getTripDistance();
            tripCost[i] = attributes.getTripCost();
            fullMode[i] = attributes.getFullMode();
        }
        
        //append data
        table.appendColumn(tripTime,"TRIP_TIME");
        table.appendColumn(tripDistance,"TRIP_DISTANCE");
        table.appendColumn(tripCost,"TRIP_COST");
        table.appendColumn(fullMode,"FULL_MODE");
	}
	
	public class MazSets implements Serializable
    {
		
		private float maxMazAutoTripDistance;
	    private int[] maxMaz = new int[3];
		public int[] numZones = new int[maxMaz.length];
		public int numSets = maxMaz.length;
		public int autoMatOffset;
		
		public MazSets() {
			
			//get max distance for maz to maz trips
			maxMazAutoTripDistance = Float.parseFloat(properties.getProperty("Results.MAZAutoTripMatrix.TripMaxDistance"));
			
			//get the near maz to maz assignment sets
			maxMaz[0] = Integer.parseInt(properties.getProperty("Results.MAZAutoTripMatrix.MaxSeqMazSet1"));
			maxMaz[1] = Integer.parseInt(properties.getProperty("Results.MAZAutoTripMatrix.MaxSeqMazSet2"));
			maxMaz[2] = Integer.parseInt(properties.getProperty("Results.MAZAutoTripMatrix.MaxSeqMazSet3"));
			
			numZones[0] = maxMaz[0];
			numZones[1] = maxMaz[1] - maxMaz[0];
			numZones[2] = maxMaz[2] - maxMaz[1];
		}
		
		
		public int getZoneSet(int omaz, int dmaz) {

			//determine if trip is in a near maz set
			int oZoneSet = 0;
			for(int j=0;j<maxMaz.length;++j){
				if(omaz <= maxMaz[j]) {
					oZoneSet = j + 1;
					break;
				}
			}
			int dZoneSet = 0;
			for(int j=0;j<maxMaz.length;++j){
				if(dmaz <= maxMaz[j]) {
					dZoneSet = j + 1;
					break;
				}
			}
			
			if(oZoneSet == dZoneSet) {
				return(oZoneSet);
			} else {
				return(0); //not an intrazonal maz set trip
			}
			
		}
		
		//get new maz offset from the start of the zone set
		public int getNewZoneSetNum(int maz) {
			int zoneSet = 0;
			for(int j=0;j<maxMaz.length;++j){
				if(maz <= maxMaz[j]) {
					zoneSet = j + 1;
					break;
				}
			}
			if (zoneSet > 1) {
				return(maz - maxMaz[zoneSet-2]);
			} else {
				return(maz);
			}
		}
		
		public boolean isMazSetTrip(float tripdist, int originMGRA, int destinationMGRA) {
			
			if((tripdist < maxMazAutoTripDistance) & (getZoneSet(originMGRA, destinationMGRA) > 0)) {
				return(true);
			} else {
				return(false);
			}
			
		}
		
    }

}
