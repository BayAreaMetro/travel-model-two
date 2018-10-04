package com.pb.mtctm2.abm.reports;

import java.nio.file.Paths;
import java.util.HashMap;
import java.util.MissingResourceException;
import java.util.ResourceBundle;

import org.apache.log4j.Logger;
import org.jppf.client.JPPFClient;

import com.pb.common.calculator.MatrixDataManager;
import com.pb.common.calculator.MatrixDataServerIf;
import com.pb.common.util.ResourceUtil;
import com.pb.mtctm2.abm.accessibilities.BuildAccessibilities;
import com.pb.mtctm2.abm.application.MTCTM2TourBasedModel;
import com.pb.mtctm2.abm.application.SandagCtrampDmuFactory;
import com.pb.mtctm2.abm.application.SandagHouseholdDataManager;
import com.pb.mtctm2.abm.application.SandagModelStructure;
import com.pb.mtctm2.abm.ctramp.Household;
import com.pb.mtctm2.abm.ctramp.HouseholdDataManager;
import com.pb.mtctm2.abm.ctramp.HouseholdDataManagerIf;
import com.pb.mtctm2.abm.ctramp.HouseholdDataManagerRmi;
import com.pb.mtctm2.abm.ctramp.MatrixDataServer;
import com.pb.mtctm2.abm.ctramp.MatrixDataServerRmi;
import com.pb.mtctm2.abm.ctramp.UsualWorkSchoolLocationChoiceModel;
import com.pb.mtctm2.abm.ctramp.Util;

public class CreateLogsums {


	private BuildAccessibilities                       aggAcc;
	private JPPFClient 								   jppfClient;
	private static Logger      logger                  = Logger.getLogger(CreateLogsums.class);
	private HouseholdDataManagerIf householdDataManager;
	private HashMap<String,String> propertyMap;
	private ResourceBundle resourceBundle;
    // are used if no command line arguments are specified.
    private int                globalIterationNumber        = 0;
    private float              iterationSampleRate          = 0f;
    private int                sampleSeed                   = 0;
    private SandagModelStructure modelStructure;
    private SandagCtrampDmuFactory dmuFactory;
    private MatrixDataServerIf ms;
    private ModelOutputReader modelOutputReader;
    
    /**
     * Constructor.
     * 
     * @param propertiesFile
     * @param globalIterationNumber
     * @param globalSampleRate
     * @param sampleSeed
     */
	public void CreateLogsums(String propertiesFile, int globalIterationNumber, float globalSampleRate, int sampleSeed){
		
		this.resourceBundle = ResourceBundle.getBundle(propertiesFile);
		propertyMap = ResourceUtil.getResourceBundleAsHashMap ( propertiesFile);
	    this.globalIterationNumber = globalIterationNumber;
	    this.iterationSampleRate = iterationSampleRate;
	    this.sampleSeed = sampleSeed;
	 
	}
	
	/**
	 * Initialize data members
	 */
	public void initialize(){
		
    	startMatrixServer(propertyMap);

        // create modelStructure object
        modelStructure = new SandagModelStructure();

		householdDataManager = getHouseholdDataManager();
	
		// create a factory object to pass to various model components from which
        // they can create DMU objects
        dmuFactory = new SandagCtrampDmuFactory(modelStructure);

        modelOutputReader = new ModelOutputReader(propertyMap,modelStructure, globalIterationNumber);
	}
	
	
	/**
	 * Run all components.
	 * 
	 */
	public void run(){
		
		initialize();
		readModelOutputsAndCreateTours();
		createWorkLogsums();
		createNonWorkLogsums();
	}
	
	/**
	 * Read the model outputs and create tours.
	 */
	public void readModelOutputsAndCreateTours(){
		
		modelOutputReader.readHouseholdDataOutput();
		modelOutputReader.readPersonDataOutput();
		modelOutputReader.readTourDataOutput();
		
		Household[] households = householdDataManager.getHhArray();
		for(Household household : households){
			modelOutputReader.createJointTours(household);
			modelOutputReader.createIndividualTours(household);
		}
		householdDataManager.setHhArray(households);
	}
	
	
	
	/**
	 * Calculate and write work destination choice logsums for the synthetic population.
	 * 
	 * @param propertyMap
	 */
	public void createWorkLogsums(){
        
        jppfClient = new JPPFClient();

        if (aggAcc == null)
        {
            logger.info("creating Accessibilities Object for UWSL.");
            aggAcc = BuildAccessibilities.getInstance();
            aggAcc.setupBuildAccessibilities(propertyMap);
            aggAcc.setJPPFClient(jppfClient);
            
            aggAcc.calculateSizeTerms();
            aggAcc.calculateConstants();
          
            boolean readAccessibilities = ResourceUtil.getBooleanProperty(resourceBundle, "acc.read.input.file");
            if (readAccessibilities)
            {
            	String projectDirectory = Util.getStringValueFromPropertyMap(propertyMap,"Project.Directory");
                String accFileName = Paths.get(projectDirectory,Util.getStringValueFromPropertyMap(propertyMap, "acc.output.file")).toString();

                aggAcc.readAccessibilityTableFromFile(accFileName);

            } else
            {

                aggAcc.calculateDCUtilitiesDistributed(propertyMap);

            }
        }

        // new the usual school and location choice model object
        UsualWorkSchoolLocationChoiceModel usualWorkSchoolLocationChoiceModel = new UsualWorkSchoolLocationChoiceModel(
                resourceBundle, "none", jppfClient, modelStructure, ms, dmuFactory, aggAcc);

        // calculate and get the array of worker size terms table - MGRAs by
        // occupations
        aggAcc.createWorkSegmentNameIndices();
        aggAcc.calculateWorkerSizeTerms();
        double[][] workerSizeTerms = aggAcc.getWorkerSizeTerms();

        // run the model
        logger.info("Starting usual work location choice for logsum calculations.");
        usualWorkSchoolLocationChoiceModel.runWorkLocationChoiceModel(householdDataManager, workerSizeTerms);
        logger.info("Finished with usual work location choice for logsum calculations.");


	}
	
	public void createNonWorkLogsums(){
		
	}
	

	
	/**
	 * Create the household data manager. Based on the code in MTCTM2TourBasedModel.runTourBasedModel() 
	 * @return The household data manager interface.
	 */
	public HouseholdDataManagerIf getHouseholdDataManager( ){

		
        boolean localHandlers = false;

       String testString;
 
        HouseholdDataManagerIf householdDataManager;
        String hhHandlerAddress = "";
        int hhServerPort = 0;
        try
        {
            // get household server address. if none is specified a local server in
            // the current process will be started.
            hhHandlerAddress = resourceBundle.getString("RunModel.HouseholdServerAddress");
            try
            {
                // get household server port.
                hhServerPort = Integer.parseInt(resourceBundle.getString("RunModel.HouseholdServerPort"));
                localHandlers = false;
            } catch (MissingResourceException e)
            {
                // if no household data server address entry is found, the object
                // will be created in the local process
                localHandlers = true;
            }
        } catch (MissingResourceException e)
        {
            localHandlers = true;
        }


        try
        {

            if (localHandlers)
            {

                // create a new local instance of the household array manager
                householdDataManager = new SandagHouseholdDataManager();
                householdDataManager.setPropertyFileValues(propertyMap);

                // have the household data manager read the synthetic population
                // files and apply its tables to objects mapping method.
                String inputHouseholdFileName = resourceBundle.getString(HouseholdDataManager.PROPERTIES_SYNPOP_INPUT_HH);
                String inputPersonFileName = resourceBundle.getString(HouseholdDataManager.PROPERTIES_SYNPOP_INPUT_PERS);
                householdDataManager.setHouseholdSampleRate(iterationSampleRate, sampleSeed);
                householdDataManager.setupHouseholdDataManager(modelStructure, inputHouseholdFileName, inputPersonFileName);

            } else
            {

                householdDataManager = new HouseholdDataManagerRmi(hhHandlerAddress, hhServerPort,
                        SandagHouseholdDataManager.HH_DATA_SERVER_NAME);
                testString = householdDataManager.testRemote();
                logger.info("HouseholdDataManager test: " + testString);

                householdDataManager.setPropertyFileValues(propertyMap);
            }
		
            //always starting from scratch (RunModel.RestartWithHhServer=none)
            householdDataManager.setDebugHhIdsFromHashmap();

            String inputHouseholdFileName = resourceBundle
                    .getString(HouseholdDataManager.PROPERTIES_SYNPOP_INPUT_HH);
            String inputPersonFileName = resourceBundle
                    .getString(HouseholdDataManager.PROPERTIES_SYNPOP_INPUT_PERS);
            householdDataManager.setHouseholdSampleRate(iterationSampleRate, sampleSeed);
            householdDataManager.setupHouseholdDataManager(modelStructure, inputHouseholdFileName, inputPersonFileName);

        }catch (Exception e)
        {

            logger.error(String
                    .format("Exception caught setting up household data manager."), e);
            throw new RuntimeException();

        }

        return householdDataManager;
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
	            ms = new MatrixDataServerRmi(serverAddress, serverPort, MatrixDataServer.MATRIX_DATA_SERVER_NAME);
	            ms.testRemote(Thread.currentThread().getName());
	            mdm.setMatrixDataServerObject(ms);

	        } catch (Exception e) {
	            logger.error("could not connect to matrix server", e);
	            throw new RuntimeException(e);

	        }

	    }
	
	
	public static void main(String[] args) {
		// TODO Auto-generated method stub

	}

}
