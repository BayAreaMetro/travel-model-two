package com.pb.mtctm2.abm.ctramp;

import java.io.File;
import java.io.Serializable;
import java.nio.file.Paths;
import java.util.Date;
import java.util.HashMap;
import java.util.LinkedList;

import org.apache.log4j.Logger;

import com.pb.mtctm2.abm.ctramp.TazDataManager;
import com.pb.common.calculator.MatrixDataServerIf;
import com.pb.common.datafile.OLD_CSVFileReader;
import com.pb.common.datafile.TableDataSet;
import com.pb.mtctm2.abm.accessibilities.AutoTazSkimsCalculator;
import com.pb.mtctm2.abm.accessibilities.BuildAccessibilities;
import com.pb.mtctm2.abm.accessibilities.MandatoryAccessibilitiesCalculator;
import com.pb.mtctm2.abm.accessibilities.NonTransitUtilities;
import com.pb.common.calculator.MatrixDataManager;

public class HouseholdChoiceModelsManager
        implements Serializable
{

    private transient Logger                              logger              = Logger.getLogger(HouseholdChoiceModelsManager.class);

    private static final String USE_NEW_SOA_METHOD_PROPERTY_KEY = "nmdc.use.new.soa";
    
    private static final String TAZ_FIELD_NAME = "TAZ";
    private static final String TP_CHOICE_AVG_TTS_FILE = "tc.choice.avgtts.file";
    private static final String AVGTTS_COLUMN_NAME = "AVGTTS";
    private static final String TRANSP_DIST_COLUMN_NAME = "DIST";
    private static final String PCT_DETOUR_COLUMN_NAME = "PCTDETOUR";

    private static String PROPERTIES_NON_MANDATORY_DC_SOA_UEC_FILE        = "nonSchool.soa.uec.file";
    private static String PROPERTIES_ESCORT_DC_SOA_UEC_MODEL_PAGE         = "escort.soa.uec.model";
    private static String PROPERTIES_ESCORT_DC_SOA_UEC_DATA_PAGE          = "escort.soa.uec.data";
    private static String PROPERTIES_NON_MANDATORY_DC_SOA_UEC_MODEL_PAGE  = "other.nonman.soa.uec.model";
    private static String PROPERTIES_NON_MANDATORY_DC_SOA_UEC_DATA_PAGE   = "other.nonman.soa.uec.data";
    private static String PROPERTIES_ATWORK_DC_SOA_UEC_MODEL_PAGE         = "atwork.soa.uec.model";
    private static String PROPERTIES_ATWORK_DC_SOA_UEC_DATA_PAGE          = "atwork.soa.uec.data";
    
     
    private static HouseholdChoiceModelsManager objInstance         = null;

    private LinkedList<HouseholdChoiceModels>   modelQueue          = null;

    private HashMap<String, String>             propertyMap;
    private String                              restartModelString;
    private ModelStructure                      modelStructure;
    private CtrampDmuFactoryIf                  dmuFactory;

    private MgraDataManager                     mgraManager;
    private TazDataManager                      tdm;

    private int                                 maxMgra;
    private int                                 maxTaz;
    

    private BuildAccessibilities                aggAcc;

    private int                                 completedHouseholds;
    private int                                 modelIndex;

    // store taz-taz exponentiated utilities (period, from taz, to taz)
    private double[][][]                        sovExpUtilities;
    private double[][][]                        hovExpUtilities;
    private double[][][]                        nMotorExpUtilities;

    private double[]                            pctHighIncome;
    private double[]                            pctMedHighPlusIncome;
    private double[]                            pctMultipleAutos;   

    private double[][][]                        nonMandatorySizeProbs;
    private double[][][]                        nonMandatoryTazDistProbs;
    private double[][][]                        subTourSizeProbs;
    private double[][][]                        subTourTazDistProbs;

    private AutoTazSkimsCalculator tazDistanceCalculator;
    
    private boolean                             useNewSoaMethod;


    

    
    
    private HouseholdChoiceModelsManager()
    {
    }

    public static synchronized HouseholdChoiceModelsManager getInstance()
    {
        if (objInstance == null)
        {
            objInstance = new HouseholdChoiceModelsManager();
            return objInstance;
        } else
        {
            return objInstance;
        }
    }

    
    // the task instances should call needToInitialize() first, then this method if necessary.
    public synchronized void managerSetup(MatrixDataServerIf ms, HouseholdDataManagerIf hhDataManager,
            HashMap<String, String> propertyMap, String restartModelString,
            ModelStructure modelStructure, CtrampDmuFactoryIf dmuFactory )
    {

        if (modelQueue != null)
            return;

        modelIndex = 0;
        completedHouseholds = 0;

        this.propertyMap = propertyMap;
        this.restartModelString = restartModelString;
        this.modelStructure = modelStructure;
        this.dmuFactory = dmuFactory;

        mgraManager = MgraDataManager.getInstance(propertyMap);
        maxMgra = mgraManager.getMaxMgra();
        
        tdm = TazDataManager.getInstance( propertyMap );
        maxTaz = tdm.getMaxTaz();
        
        pctHighIncome = hhDataManager.getPercentHhsIncome100Kplus();
        pctMedHighPlusIncome = hhDataManager.getPercentHhsIncome75Kplus();
        pctMultipleAutos = hhDataManager.getPercentHhsMultipleAutos();
        
        MatrixDataManager mdm = MatrixDataManager.getInstance();
        mdm.setMatrixDataServerObject(ms);

        aggAcc = BuildAccessibilities.getInstance();
        if ( ! aggAcc.getAccessibilitiesAreBuilt() )
        {
            logger.info("creating Accessibilities Object for Household Choice Models.");

            aggAcc.setupBuildAccessibilities(propertyMap);
    
            aggAcc.calculateSizeTerms();
            aggAcc.calculateConstants();
            //aggAcc.buildAccessibilityComponents(propertyMap);
    
            boolean readAccessibilities = Util.getBooleanValueFromPropertyMap(propertyMap, CtrampApplication.READ_ACCESSIBILITIES);
            if (readAccessibilities)
            {
    
                // output data
                String projectDirectory = Util.getStringValueFromPropertyMap(propertyMap,CtrampApplication.PROPERTIES_PROJECT_DIRECTORY);
                String accFileName = Paths.get(projectDirectory,Util.getStringValueFromPropertyMap(propertyMap,"acc.output.file")).toString();
    
                logger.info("filling Accessibilities Object by reading file: " + accFileName + ".");
                aggAcc.readAccessibilityTableFromFile(accFileName);
    
            } else
            {
    
                logger.info("filling Accessibilities Object by calculating them.");
                aggAcc.calculateDCUtilitiesDistributed(propertyMap);
    
            }
        
        }
    
                
        useNewSoaMethod = Util.getBooleanValueFromPropertyMap( propertyMap, USE_NEW_SOA_METHOD_PROPERTY_KEY);
        
        
        if ( useNewSoaMethod ) {
            // compute the arrays of cumulative probabilities based on mgra size for mgras within each origin taz.
            logger.info( "pre-computing non-mandatory purpose SOA Distance and Size probabilities." );
            computeNonMandatorySegmentSizeArrays( dmuFactory );

            logger.info( "pre-computing at-work sub-tour purpose SOA Distance and Size probabilities." );
            computeSubtourSegmentSizeArrays( modelStructure, dmuFactory );
        }
        
            
        tazDistanceCalculator = new AutoTazSkimsCalculator( propertyMap );
        tazDistanceCalculator.computeTazDistanceArrays();
        
        
        // the first thread to reach this method initializes the modelQueue used to
        // recycle hhChoiceModels objects.
        modelQueue = new LinkedList<HouseholdChoiceModels>();

        mgraManager = MgraDataManager.getInstance(propertyMap);

    }

    /**
     * @return DestChoiceModel object created if none is available from the queue.
     * 
     */
    public synchronized HouseholdChoiceModels getHouseholdChoiceModelsObject(int taskIndex)
    {

        String message = "";
        HouseholdChoiceModels hhChoiceModels = null;

        if (modelQueue.isEmpty()) {

            NonTransitUtilities ntUtilities = new NonTransitUtilities(propertyMap, sovExpUtilities, hovExpUtilities, nMotorExpUtilities);
 
            McLogsumsCalculator logsumHelper = new McLogsumsCalculator();
            logsumHelper.setupSkimCalculators(propertyMap);
            logsumHelper.setTazDistanceSkimArrays( tazDistanceCalculator.getStoredFromTazToAllTazsDistanceSkims(), tazDistanceCalculator.getStoredToTazFromAllTazsDistanceSkims() );
            
            MandatoryAccessibilitiesCalculator mandAcc = new MandatoryAccessibilitiesCalculator(propertyMap, ntUtilities, aggAcc.getExpConstants(), logsumHelper.getBestTransitPathCalculator());
            

            // create choice model object
            hhChoiceModels = new HouseholdChoiceModels(++modelIndex, restartModelString, propertyMap, modelStructure, dmuFactory, aggAcc, logsumHelper, mandAcc,
                    pctHighIncome, pctMedHighPlusIncome, pctMultipleAutos,tdm.getAvgTravelTimeData(),tdm.getAvgTravelDistanceData(),tdm.getPctDetourData(),
                    nonMandatoryTazDistProbs, nonMandatorySizeProbs,
                    subTourTazDistProbs, subTourSizeProbs );
            
            
            message = String.format("created hhChoiceModels=%d, task=%d, thread=%s.", modelIndex, taskIndex, Thread.currentThread().getName());
        
        }
        else {
            hhChoiceModels = modelQueue.remove();
            message = String.format("removed hhChoiceModels=%d from queue, task=%d, thread=%s.", hhChoiceModels.getModelIndex(), taskIndex, Thread.currentThread().getName());
        }
        logger.info(message);
        logger.info("");

        return hhChoiceModels;

    }

    /**
     * return the HouseholdChoiceModels object to the manager's queue so that it may
     * be used by another thread without it having to create one.
     * 
     * @param hhModels
     */
    public void returnHouseholdChoiceModelsObject(HouseholdChoiceModels hhModels, int startIndex,
            int endIndex)
    {
        modelQueue.add(hhModels);
        completedHouseholds += (endIndex - startIndex + 1);
        logger.info("returned hhChoiceModels=" + hhModels.getModelIndex() + " to queue: thread="
            + Thread.currentThread().getName() + ", completedHouseholds=" + completedHouseholds + ".");
    }

    public synchronized void clearHhModels()
    {

        if (modelQueue == null)
            return;

        System.out.println(String.format( "%s:  clearing household choice models modelQueue, thread=%s.", new Date(), Thread.currentThread().getName()));

        while( ! modelQueue.isEmpty() )
            modelQueue.remove();

        modelIndex = 0;
        completedHouseholds = 0;

        modelQueue = null;

    }


    private void computeNonMandatorySegmentSizeArrays( CtrampDmuFactoryIf dmuFactory ) {
        
        // compute the array of cumulative taz distance based SOA probabilities for each origin taz.
        DestChoiceTwoStageSoaTazDistanceUtilityDMU dcDistSoaDmu = dmuFactory.getDestChoiceSoaTwoStageTazDistUtilityDMU();        

        
        // the size term array in aggAcc gives mgra*purpose - need an array of all mgras for one purpose
        double[][] aggAccDcSizeArray = aggAcc.getSizeTerms();
        
        String[] tourPurposeNames = {
            ModelStructure.ESCORT_PRIMARY_PURPOSE_NAME,
            ModelStructure.SHOPPING_PRIMARY_PURPOSE_NAME,
            ModelStructure.OTH_MAINT_PRIMARY_PURPOSE_NAME,
            ModelStructure.EAT_OUT_PRIMARY_PURPOSE_NAME,
            ModelStructure.VISITING_PRIMARY_PURPOSE_NAME,
            ModelStructure.OTH_DISCR_PRIMARY_PURPOSE_NAME
        };
      
        int[] sizeSheetIndices = {
            BuildAccessibilities.ESCORT_INDEX,
            BuildAccessibilities.SHOP_INDEX,
            BuildAccessibilities.OTH_MAINT_INDEX,
            BuildAccessibilities.EATOUT_INDEX,
            BuildAccessibilities.VISIT_INDEX,
            BuildAccessibilities.OTH_DISCR_INDEX
        };
        
        HashMap<String,Integer> nonMandatorySegmentNameIndexMap = new HashMap<String,Integer>();
        HashMap<String,Integer> nonMandatorySizeSegmentNameIndexMap = new HashMap<String,Integer>();
        for ( int k=0; k < tourPurposeNames.length; k++ ){
            nonMandatorySegmentNameIndexMap.put( tourPurposeNames[k], k );
            nonMandatorySizeSegmentNameIndexMap.put( tourPurposeNames[k], sizeSheetIndices[k] );
        }
      
        double[][] dcSizeArray = new double[tourPurposeNames.length][aggAccDcSizeArray.length];        
        for ( int i=0; i < aggAccDcSizeArray.length; i++ ){
            for ( int m : nonMandatorySegmentNameIndexMap.values() ){
                int s = sizeSheetIndices[m];
                dcSizeArray[m][i] = aggAccDcSizeArray[i][s];
            }
        }
                        
        
        // compute the arrays of cumulative probabilities based on mgra size for mgras within each origin taz.        
        nonMandatorySizeProbs = new double[tourPurposeNames.length][][];
        nonMandatoryTazDistProbs = new double[tourPurposeNames.length][][];

        DestChoiceTwoStageSoaProbabilitiesCalculator nonManSoaDistProbsObject =
            new DestChoiceTwoStageSoaProbabilitiesCalculator( propertyMap, dmuFactory,
                    PROPERTIES_NON_MANDATORY_DC_SOA_UEC_FILE, PROPERTIES_NON_MANDATORY_DC_SOA_UEC_MODEL_PAGE,
                    PROPERTIES_NON_MANDATORY_DC_SOA_UEC_DATA_PAGE );
              
        for ( String tourPurpose : tourPurposeNames ) {

            int purposeSizeIndex = nonMandatorySizeSegmentNameIndexMap.get( tourPurpose );
    
            // compute the TAZ size values from the mgra values and the correspondence between mgras and tazs.
            if ( tourPurpose.equalsIgnoreCase( ModelStructure.ESCORT_PRIMARY_PURPOSE_NAME ) ) {
                
                double[] mgraData = new double[maxMgra+1];
                double[] tazData = null;

                // aggregate TAZ grade school enrollment and set array in DMU
                for ( int i=0; i < mgraManager.getMgras().size(); i++ )
                    mgraData[i] = aggAcc.getMgraGradeSchoolEnrollment( mgraManager.getMgras().get(i) );
                tazData = computeTazSize( mgraData );
                dcDistSoaDmu.setTazGsEnrollment( tazData );
                
                // aggregate TAZ high school enrollment and set array in DMU
                for ( int i=0; i < mgraManager.getMgras().size(); i++ )
                    mgraData[i] = aggAcc.getMgraHighSchoolEnrollment( mgraManager.getMgras().get(i) );
                tazData = computeTazSize( mgraData );
                dcDistSoaDmu.setTazHsEnrollment( tazData );
                
                // aggregate TAZ households and set array in DMU
                for ( int i=0; i < mgraManager.getMgras().size(); i++ )
                    mgraData[i] = aggAcc.getMgraHouseholds( mgraManager.getMgras().get(i) );
                tazData = computeTazSize( mgraData );
                dcDistSoaDmu.setNumHhs( tazData );
                
                DestChoiceTwoStageSoaProbabilitiesCalculator escortSoaDistProbsObject =
                    new DestChoiceTwoStageSoaProbabilitiesCalculator( propertyMap, dmuFactory,
                            PROPERTIES_NON_MANDATORY_DC_SOA_UEC_FILE, PROPERTIES_ESCORT_DC_SOA_UEC_MODEL_PAGE,
                            PROPERTIES_ESCORT_DC_SOA_UEC_DATA_PAGE );
                      
                logger.info( "     " + tourPurpose + " probabilities" );
                nonMandatoryTazDistProbs[purposeSizeIndex] = escortSoaDistProbsObject.computeDistanceProbabilities( dcDistSoaDmu );

            }
            else {
                
                // aggregate TAZ size for the non-mandatoy purpose and set array in DMU
                double[] tazSize = computeTazSize( dcSizeArray[purposeSizeIndex] );
                dcDistSoaDmu.setDestChoiceTazSize( tazSize );
                
                logger.info( "     " + tourPurpose + " probabilities" );
                nonMandatoryTazDistProbs[purposeSizeIndex] = nonManSoaDistProbsObject.computeDistanceProbabilities( dcDistSoaDmu );

            }

            
            nonMandatorySizeProbs[purposeSizeIndex] = computeSizeSegmentProbabilities( dcSizeArray[purposeSizeIndex] );  
            
        }

        
    }
    

    private void computeSubtourSegmentSizeArrays( ModelStructure modelStructure, CtrampDmuFactoryIf dmuFactory ) {
        
        // compute the array of cumulative taz distance based SOA probabilities for each origin taz.
        DestChoiceTwoStageSoaTazDistanceUtilityDMU dcDistSoaDmu = dmuFactory.getDestChoiceSoaTwoStageTazDistUtilityDMU();        

        
        // the size term array in aggAcc gives mgra*purpose - need an array of all mgras for one purpose
        double[][] aggAccDcSizeArray = aggAcc.getSizeTerms();
        
        String[] tourPurposeNames = {
            modelStructure.AT_WORK_BUSINESS_PURPOSE_NAME,
            modelStructure.AT_WORK_EAT_PURPOSE_NAME,
            modelStructure.AT_WORK_MAINT_PURPOSE_NAME
        };
      
        int[] sizeSheetIndices = {
                SubtourDestChoiceModel.PROPERTIES_AT_WORK_BUSINESS_SIZE_SHEET,
                SubtourDestChoiceModel.PROPERTIES_AT_WORK_EAT_OUT_SIZE_SHEET,
                SubtourDestChoiceModel.PROPERTIES_AT_WORK_OTHER_SIZE_SHEET
        };
        
        HashMap<String,Integer> segmentNameIndexMap = new HashMap<String,Integer>();
        HashMap<String,Integer> sizeSegmentNameIndexMap = new HashMap<String,Integer>();
        for ( int k=0; k < tourPurposeNames.length; k++ ){
            segmentNameIndexMap.put( tourPurposeNames[k], k );
            sizeSegmentNameIndexMap.put( tourPurposeNames[k], sizeSheetIndices[k] );
        }
      
        double[][] dcSizeArray = new double[tourPurposeNames.length][aggAccDcSizeArray.length];        
        for ( int i=0; i < aggAccDcSizeArray.length; i++ ){
            for ( int m : segmentNameIndexMap.values() ){
                int s = sizeSheetIndices[m];
                dcSizeArray[m][i] = aggAccDcSizeArray[i][s];
            }
        }
                        
        
        // compute the arrays of cumulative probabilities based on mgra size for mgras within each origin taz.        
        subTourSizeProbs = new double[tourPurposeNames.length][][];
        subTourTazDistProbs = new double[tourPurposeNames.length][][];

        DestChoiceTwoStageSoaProbabilitiesCalculator subTourSoaDistProbsObject =
            new DestChoiceTwoStageSoaProbabilitiesCalculator( propertyMap, dmuFactory,
                    PROPERTIES_NON_MANDATORY_DC_SOA_UEC_FILE, PROPERTIES_ATWORK_DC_SOA_UEC_MODEL_PAGE,
                    PROPERTIES_ATWORK_DC_SOA_UEC_DATA_PAGE );
              
        for ( String tourPurpose : tourPurposeNames ) {

            int purposeSizeIndex = segmentNameIndexMap.get( tourPurpose );
    
            // aggregate TAZ size for the non-mandatoy purpose and set array in DMU
            double[] tazSize = computeTazSize( dcSizeArray[purposeSizeIndex] );
            dcDistSoaDmu.setDestChoiceTazSize( tazSize );
            
            logger.info( "     " + tourPurpose + " probabilities" );
            subTourTazDistProbs[purposeSizeIndex] = subTourSoaDistProbsObject.computeDistanceProbabilities( dcDistSoaDmu );
            
            subTourSizeProbs[purposeSizeIndex] = computeSizeSegmentProbabilities( dcSizeArray[purposeSizeIndex] );  
            
        }

        
    }
    

    private double[] computeTazSize( double[] size ) {

        // this is a 0-based array of cumulative probabilities
        double[] tazSize = new double[maxTaz+1];
        
        for ( int i=0; i< tdm.getTazs().length; i++ ) {

            int taz = tdm.getTazs()[i];
        	int[] mgraArray = tdm.getMgraArray(taz);            
            if ( mgraArray != null ) {
                for ( int mgra : mgraArray ) {
                    tazSize[taz] += size[mgra] + (size[mgra] > 0 ? 1 : 0);
                }
            }
            
        }
        
        return tazSize;
        
    }
            
    private double[][] computeSizeSegmentProbabilities( double[] size ) {

        // this is a 0-based array of cumulative probabilities
        double[][] sizeProbs = new double[maxTaz][];
        
        for ( int k=0; k< tdm.getTazs().length; k++ ) {

            int taz = tdm.getTazs()[k];
            int[] mgraArray = tdm.getMgraArray(taz);
            
            if ( mgraArray == null ) {
                sizeProbs[taz-1] = new double[0];                
            }
            else {
                double totalSize = 0;
                for ( int mgra : mgraArray )
                    totalSize += size[mgra] + (size[mgra] > 0 ? 1 : 0); 

                if ( totalSize > 0 ) {
                    sizeProbs[taz-1] = new double[mgraArray.length];                
                    for ( int i=0; i < mgraArray.length; i++ ) {
                        double mgraSize = size[mgraArray[i]];
                        if ( mgraSize > 0 )
                            mgraSize += 1;
                        sizeProbs[taz-1][i] = mgraSize / totalSize;
                    }
                }
                else {
                    sizeProbs[taz-1] = new double[0];                
                }
            }            
            
        }
        
        return sizeProbs;
        
    }
    
}
