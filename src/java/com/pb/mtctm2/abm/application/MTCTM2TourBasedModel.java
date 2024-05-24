package com.pb.mtctm2.abm.application;

import java.util.HashMap;
import java.util.ResourceBundle;
import java.util.MissingResourceException;
import org.apache.log4j.Logger;
import com.pb.common.util.ResourceUtil;
import com.pb.mtctm2.abm.ctramp.CtrampApplication;
import com.pb.mtctm2.abm.ctramp.HouseholdDataManager;
import com.pb.mtctm2.abm.ctramp.HouseholdDataManagerIf;
import com.pb.mtctm2.abm.ctramp.HouseholdDataManagerRmi;

public final class MTCTM2TourBasedModel
{

    private static Logger      logger                       = Logger.getLogger(MTCTM2TourBasedModel.class);

    public static final String PROPERTIES_PROJECT_DIRECTORY = "Project.Directory";

    private static final int   DEFAULT_ITERATION_NUMBER     = 1;
    private static final float DEFAULT_SAMPLE_RATE          = 1.0f;
    private static final int   DEFAULT_SAMPLE_SEED          = 0;

    public static final int    DEBUG_CHOICE_MODEL_HHID      = 740151;

    private ResourceBundle     rb;

    // values for these variables are set as command line arguments, or default vaues
    // are used if no command line arguments are specified.
    private int                globalIterationNumber        = 0;
    private float              iterationSampleRate          = 0f;
    private int                sampleSeed                   = 0;

    /**
     * 
     * @param rb , java.util.ResourceBundle containing environment settings from a
     *            properties file specified on the command line
     * @param globalIterationNumber , int iteration number for which the model is
     *            run, set by another process controlling a model stream with
     *            feedback.
     * @param iterationSampleRate , float percentage [0.0, 1.0] inicating the portion
     *            of all households to be modeled.
     * 
     *            This object defines the implementation of the ARC tour based,
     *            activity based travel demand model.
     */
    private MTCTM2TourBasedModel(ResourceBundle aRb, HashMap<String,String> aPropertyMap, int aGlobalIterationNumber,
            float aIterationSampleRate, int aSampleSeed)
    {
        rb = aRb;
        globalIterationNumber = aGlobalIterationNumber;
        iterationSampleRate = aIterationSampleRate;
        sampleSeed = aSampleSeed;
    }

    private void runTourBasedModel( HashMap<String,String> propertyMap )
    {

        // new a ctramp application object
        SandagCtrampApplication ctrampApplication = new SandagCtrampApplication(rb, propertyMap);

        // create modelStructure object
        SandagModelStructure modelStructure = new SandagModelStructure();

        boolean localHandlers = false;

        String hhHandlerAddress = "";
        int hhServerPort = 0;
        try
        {
            // get household server address. if none is specified a local server in
            // the current process will be started.
            hhHandlerAddress = rb.getString("RunModel.HouseholdServerAddress");
            try
            {
                // get household server port.
                hhServerPort = Integer.parseInt(rb.getString("RunModel.HouseholdServerPort"));
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

        String testString;
        // if ( localHandlers ) {
        // tazDataHandler = new SandagTazDataHandler(rb, projectDirectory);
        // }
        // else {
        // tazDataHandler = new TazDataHandlerRmi(
        // ArcTazDataHandler.ZONAL_DATA_SERVER_ADDRESS,
        // ArcTazDataHandler.ZONAL_DATA_SERVER_PORT,
        // ArcTazDataHandler.ZONAL_DATA_SERVER_NAME );
        // testString = tazDataHandler.testRemote();
        // logger.info ( "TazDataHandler test: " + testString );
        // }

        // setup the ctramp application
        ctrampApplication.setupModels(modelStructure);

        // generate the synthetic population
        // ARCPopulationSynthesizer populationSynthesizer = new
        // ARCPopulationSynthesizer( propertiesFileBaseName );
        // ctrampApplication.runPopulationSynthesizer( populationSynthesizer );

        HouseholdDataManagerIf householdDataManager;


        try
        {

            if (localHandlers)
            {

                // create a new local instance of the household array manager
                householdDataManager = new SandagHouseholdDataManager();
                householdDataManager.setPropertyFileValues(propertyMap);

                // have the household data manager read the synthetic population
                // files and apply its tables to objects mapping method.
                String inputHouseholdFileName = rb.getString(HouseholdDataManager.PROPERTIES_SYNPOP_INPUT_HH);
                String inputPersonFileName = rb.getString(HouseholdDataManager.PROPERTIES_SYNPOP_INPUT_PERS);
                householdDataManager.setHouseholdSampleRate(iterationSampleRate, sampleSeed);
                householdDataManager.setupHouseholdDataManager(modelStructure, inputHouseholdFileName, inputPersonFileName);

            } else
            {

                householdDataManager = new HouseholdDataManagerRmi(hhHandlerAddress, hhServerPort,
                        SandagHouseholdDataManager.HH_DATA_SERVER_NAME);
                testString = householdDataManager.testRemote();
                logger.info("HouseholdDataManager test: " + testString);

                householdDataManager.setPropertyFileValues(propertyMap);

                // have the household data manager read the synthetic population
                // files and apply its tables to objects mapping method.
                boolean restartHhServer = false;
                try
                {
                    // possible values for the following can be none, ao, cdap, imtf,
                    // imtod, awf, awl, awtod, jtf, jtl, jtod, inmtf, inmtl, inmtod,
                    // stf, stl
                    String restartModel = rb.getString("RunModel.RestartWithHhServer");
                    if (restartModel.equalsIgnoreCase("none")) restartHhServer = true;
                    else if (restartModel.equalsIgnoreCase("uwsl")
                            || restartModel.equalsIgnoreCase("ao")
                            || restartModel.equalsIgnoreCase("fp")
                            || restartModel.equalsIgnoreCase("cdap")
                            || restartModel.equalsIgnoreCase("imtf")
                            || restartModel.equalsIgnoreCase("imtod")
                            || restartModel.equalsIgnoreCase("awf")
                            || restartModel.equalsIgnoreCase("awl")
                            || restartModel.equalsIgnoreCase("awtod")
                            || restartModel.equalsIgnoreCase("jtf")
                            || restartModel.equalsIgnoreCase("jtl")
                            || restartModel.equalsIgnoreCase("jtod")
                            || restartModel.equalsIgnoreCase("inmtf")
                            || restartModel.equalsIgnoreCase("inmtl")
                            || restartModel.equalsIgnoreCase("inmtod")
                            || restartModel.equalsIgnoreCase("stf")
                            || restartModel.equalsIgnoreCase("stl")) restartHhServer = false;
                } catch (MissingResourceException e)
                {
                    restartHhServer = true;
                }

                if (restartHhServer)
                {

                    householdDataManager.setDebugHhIdsFromHashmap();

                    String inputHouseholdFileName = rb
                            .getString(HouseholdDataManager.PROPERTIES_SYNPOP_INPUT_HH);
                    String inputPersonFileName = rb
                            .getString(HouseholdDataManager.PROPERTIES_SYNPOP_INPUT_PERS);
                    householdDataManager.setHouseholdSampleRate(iterationSampleRate, sampleSeed);
                    householdDataManager.setupHouseholdDataManager(modelStructure, inputHouseholdFileName, inputPersonFileName);

                } else
                {

                    householdDataManager.setHouseholdSampleRate(iterationSampleRate, sampleSeed);
                    householdDataManager.setDebugHhIdsFromHashmap();
                    householdDataManager.setTraceHouseholdSet();

                    // set the random number sequence for household objects
                    // accordingly based on which model components are
                    // assumed to have already run and are stored in the remote
                    // HouseholdDataManager object.
                    ctrampApplication.restartModels(householdDataManager);

                }

            }

            // create a factory object to pass to various model components from which
            // they can create DMU objects
            SandagCtrampDmuFactory dmuFactory = new SandagCtrampDmuFactory(modelStructure);

            // run the models
            ctrampApplication.runModels(householdDataManager, dmuFactory, globalIterationNumber, iterationSampleRate);

        } catch (Exception e)
        {

            logger.error(String
                    .format("exception caught running ctramp model components -- exiting."), e);
            throw new RuntimeException();

        }

    }

    public static void main(String[] args)
    {

        long startTime = System.currentTimeMillis();
        int globalIterationNumber = -1;
        float iterationSampleRate = -1.0f;
        int sampleSeed = -1;

        ResourceBundle rb = null;
        HashMap<String,String> pMap;

        logger.info(String.format("MTC TM2 Activity Based Model"));

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
        MTCTM2TourBasedModel mainObject = new MTCTM2TourBasedModel(rb, pMap, globalIterationNumber,
                iterationSampleRate, sampleSeed);

        // run tour based models
        try
        {

            logger.info("");
            logger.info("starting tour based model.");
            mainObject.runTourBasedModel( pMap );

        } catch (RuntimeException e)
        {
            logger.error( "RuntimeException caught in com.pb.mtctm2.abm.application.MTCTM2TourBasedModel.main() -- exiting.", e );
        }

        logger.info("");
        logger.info("");
        logger.info("MTC TM2 Activity Based Model finished in "
                + ((System.currentTimeMillis() - startTime) / 60000.0) + " minutes.");

        System.exit(0);
    }

}
