package com.pb.mtctm2.abm.ctramp;

import java.io.File;
import java.io.IOException;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Random;

import com.pb.common.calculator.VariableTable;
import com.pb.common.datafile.OLD_CSVFileReader;
import com.pb.common.datafile.TableDataSet;
import com.pb.common.model.ModelException;
import com.pb.mtctm2.abm.accessibilities.AccessibilitiesTable;
import com.pb.mtctm2.abm.accessibilities.AutoAndNonMotorizedSkimsCalculator;
import com.pb.mtctm2.abm.accessibilities.AutoTazSkimsCalculator;
import com.pb.mtctm2.abm.accessibilities.BestTransitPathCalculator;
import com.pb.mtctm2.abm.accessibilities.WalkTransitWalkSkimsCalculator;
import com.pb.mtctm2.abm.reports.SkimBuilder;

import org.apache.log4j.Logger;

public class TransitSubsidyAndPassModel
        implements Serializable
{

    private transient Logger                   logger                 = Logger.getLogger(TransitSubsidyAndPassModel.class);
    private transient Logger                   aoLogger               = Logger.getLogger("ao");

    private static final String                TT_CONTROL_FILE_TARGET = "tt.uec.file";
    private static final String                TT_DATA_SHEET_TARGET   = "tt.data.page";
    private static final String                TT_SUBSIDYMODEL_SHEET_TARGET  = "tt.subsidyModel.page";
    private static final String                TT_PASSMODEL_SHEET_TARGET  = "tt.passModel.page";
    private static final String                TT_AUTOGENTIME_TARGET  = "tt.autoGenTime.page";
    private static final String                TT_SUBSIDY_PCT_FILE  = "tt.subsidyPercent.file";
    
    private AccessibilitiesTable               accTable;
    private ChoiceModelApplication             subsidyModel;
    private ChoiceModelApplication             passModel;
    private ChoiceModelApplication             autoGenTimeModel;
    
    private TransitSubsidyAndPassDMU           ttDmuObject;
    
    private MgraDataManager                    mgraManager;
    private TazDataManager					tazManager;

    private double[]                           lsWgtAvgCostM;
    private double[]                           lsWgtAvgCostD;
    private double[]                           lsWgtAvgCostH;
    private double[]                           subsidyDistribution;
    private double[]                           subsidyPercent;
    
    public static final int                   WTW = 0;
    public static final int                   WTD = 1;
    public static final int                   DTW = 2;
    
    
    
   public static short HAS_TRANSIT_SUBSIDY  =1;
   public static short HAS_TRANSIT_PASS  =1;
   
   private BestTransitPathCalculator         bestPathCalculator;
   protected WalkTransitWalkSkimsCalculator  wtw;
   AutoAndNonMotorizedSkimsCalculator anmCalculator;
	TransitWalkAccessDMU walkDmu;
	TransitDriveAccessDMU driveDmu;

    HashMap<String, String> rbMap;

    public TransitSubsidyAndPassModel(HashMap<String, String> rbMap,
            CtrampDmuFactoryIf dmuFactory, AccessibilitiesTable myAccTable, McLogsumsCalculator logsumHelper)
    {

        logger.info("setting up transit subsidy and transit pass ownership models.");

        accTable = myAccTable;
        this.rbMap = rbMap;
        
        // locate the transit subsidy and pass ownership UEC
        String uecPath = rbMap.get(CtrampApplication.PROPERTIES_UEC_PATH);
        String uecFileName = rbMap.get(TT_CONTROL_FILE_TARGET);
        uecFileName = uecPath + uecFileName;

        int dataPage = Util.getIntegerValueFromPropertyMap(rbMap, TT_DATA_SHEET_TARGET);
        int subsidyModelPage = Util.getIntegerValueFromPropertyMap(rbMap, TT_SUBSIDYMODEL_SHEET_TARGET);
        int passModelPage = Util.getIntegerValueFromPropertyMap(rbMap, TT_PASSMODEL_SHEET_TARGET);
        int autoGenTimePage = Util.getIntegerValueFromPropertyMap(rbMap, TT_AUTOGENTIME_TARGET);

        // create the transit subsidy and pass ownership model DMU object.
        ttDmuObject = dmuFactory.getTransitSubsidyAndPassDMU();

        // create the subsidy model object
        subsidyModel = new ChoiceModelApplication(uecFileName, subsidyModelPage, dataPage, rbMap,
                (VariableTable) ttDmuObject);
        
        // create the transit pass model object
        passModel = new ChoiceModelApplication(uecFileName, passModelPage, dataPage, rbMap,
                (VariableTable) ttDmuObject);
        
        // create the generalized auto time object
        autoGenTimeModel = new ChoiceModelApplication(uecFileName, autoGenTimePage, dataPage, rbMap,
                (VariableTable) ttDmuObject);
       

        if (mgraManager == null)
            mgraManager = MgraDataManager.getInstance();    
            
        if(tazManager == null)
        	tazManager = TazDataManager.getInstance();

        this.lsWgtAvgCostM = mgraManager.getLsWgtAvgCostM();
        this.lsWgtAvgCostD = mgraManager.getLsWgtAvgCostD();
        this.lsWgtAvgCostH = mgraManager.getLsWgtAvgCostH();
        
        String subsidyPercentFileName = uecPath + rbMap.get(TT_SUBSIDY_PCT_FILE);
       
        setSubsidyDistribution(subsidyPercentFileName);

        bestPathCalculator = logsumHelper.getBestTransitPathCalculator();
        anmCalculator = logsumHelper.getAnmSkimCalculator();

        wtw = new WalkTransitWalkSkimsCalculator(rbMap);
        wtw.setup(rbMap, logger, bestPathCalculator);
	    walkDmu =  new TransitWalkAccessDMU();
    	walkDmu.setTransitFareDiscounts(bestPathCalculator.getTransitFareDiscounts());
	    driveDmu =  new TransitDriveAccessDMU();
	    

     }

    /**
     * Set the dmu attributes, compute the pre-AO or AO utilities, and select an
     * alternative
     * 
     * @param hhObj for which to apply thye model
     * @param preAutoOwnership is true if running pre-auto ownership, or false to run
     *            primary auto ownership model.
     */

    public void applyModels(Household hhObj)
    {

     	ttDmuObject.setHhIncomeInDollars(hhObj.getIncomeInDollars());
    	
    	Person[] personArray = hhObj.getPersons();
    	for(int i = 1; i<personArray.length;++i) {
    		
    		Person thisPerson = personArray[i];
    	
    		int personType = thisPerson.getPersonTypeNumber();
            ttDmuObject.setPersonType(personType);
            ttDmuObject.setValueOfTime(thisPerson.getValueOfTime());
    		
    		if(thisPerson.getPersonIsWorker()==1) {
    			int workMgra = thisPerson.getUsualWorkLocation();
    			if (workMgra != ModelStructure.WORKS_AT_HOME_LOCATION_INDICATOR)
    			{	
    				int originTaz = mgraManager.getTaz(hhObj.getHhMgra());
    				int destinationTaz = mgraManager.getTaz(workMgra);
    				ttDmuObject.setDmuIndexValues(hhObj.getHhId(), originTaz, originTaz, destinationTaz);
    				
    				ttDmuObject.setPTazTerminalTime(tazManager.getOriginTazTerminalTime(originTaz));
    				ttDmuObject.setATazTerminalTime(tazManager.getDestinationTazTerminalTime(destinationTaz));
    				
    				double genAutoTime = calculateGeneralizedAutoTime(ttDmuObject);
    				ttDmuObject.setAutoGenTime((float)genAutoTime);
    				
    				double[] transitSkims = getBestPeakWalkTransitSkims(hhObj.getHhMgra(), workMgra, hhObj.getDebugChoiceModels());
    				
    				double genTranTime=0;
    				if(transitSkims != null) 
    					genTranTime = calculateGeneralizedTransitTime(transitSkims, thisPerson.getValueOfTime(),hhObj.getDebugChoiceModels());
    				
    				ttDmuObject.setTranGenTime((float) genTranTime);
    				
    				ttDmuObject.setTransitAccessToHHs( accTable.getAggregateAccessibility("hhWlkTrn", workMgra ) );
    		        
    				ttDmuObject.setLsWgtAvgCostM( (float) lsWgtAvgCostM[workMgra] );
    		        ttDmuObject.setLsWgtAvgCostD( (float) lsWgtAvgCostD[workMgra] );
    		        ttDmuObject.setLsWgtAvgCostH( (float) lsWgtAvgCostH[workMgra] );
    		        
    		        double randomNumber = hhObj.getHhRandom().nextDouble();
    		        int naicsCode = sampleNaicsCodeForMAZ(workMgra, randomNumber);
    		        thisPerson.setNaicsCode((short)naicsCode);
    		        ttDmuObject.setNaicsCode(naicsCode);
    		       	
    		        
    		        
    			}
    		}else if(thisPerson.getPersonIsUniversityStudent()==1) {
    			int schoolMgra = thisPerson.getUsualSchoolLocation();
    			if (schoolMgra != ModelStructure.NOT_ENROLLED_SEGMENT_INDEX)
    			{	
    				int originTaz = mgraManager.getTaz(hhObj.getHhMgra());
    				int destinationTaz = mgraManager.getTaz(schoolMgra);
    				ttDmuObject.setDmuIndexValues(hhObj.getHhId(), originTaz, originTaz, destinationTaz);
    				
    				ttDmuObject.setPTazTerminalTime(tazManager.getOriginTazTerminalTime(originTaz));
    				ttDmuObject.setATazTerminalTime(tazManager.getDestinationTazTerminalTime(destinationTaz));
    				
    				double genAutoTime = calculateGeneralizedAutoTime(ttDmuObject);
    				ttDmuObject.setAutoGenTime((float)genAutoTime);
    				
    				double[] transitSkims = getBestPeakWalkTransitSkims(hhObj.getHhMgra(), schoolMgra, hhObj.getDebugChoiceModels());
       				double genTranTime=0;
    				if(transitSkims != null) 
    					genTranTime = calculateGeneralizedTransitTime(transitSkims, thisPerson.getValueOfTime(),hhObj.getDebugChoiceModels());
    				ttDmuObject.setTranGenTime((float) genTranTime);
    				
    				ttDmuObject.setTransitAccessToHHs( accTable.getAggregateAccessibility("hhWlkTrn", schoolMgra ) );
    		        
    				ttDmuObject.setLsWgtAvgCostM( (float) lsWgtAvgCostM[schoolMgra] );
    		        ttDmuObject.setLsWgtAvgCostD( (float) lsWgtAvgCostD[schoolMgra] );
    		        ttDmuObject.setLsWgtAvgCostH( (float) lsWgtAvgCostH[schoolMgra] );
    		        
    			}
		        ttDmuObject.setNaicsCode(0);
		   }else {
   				
				int originTaz = mgraManager.getTaz(hhObj.getHhMgra());
				ttDmuObject.setDmuIndexValues(hhObj.getHhId(), originTaz, originTaz, originTaz);
				
				ttDmuObject.setPTazTerminalTime(0);
				ttDmuObject.setATazTerminalTime(0);
				
				ttDmuObject.setAutoGenTime(0);
				ttDmuObject.setTranGenTime(0);
				
				ttDmuObject.setTransitAccessToHHs( 0);
		        
				ttDmuObject.setLsWgtAvgCostM( 0 );
		        ttDmuObject.setLsWgtAvgCostD( 0);
		        ttDmuObject.setLsWgtAvgCostH( 0 );
		        
		        ttDmuObject.setNaicsCode(0);
			
   				
   			}
    		
    		// compute utilities and choose transit subsidy alternative.
    		subsidyModel.computeUtilities(ttDmuObject, ttDmuObject.getDmuIndexValues());

    		Random hhRandom = hhObj.getHhRandom();
    		double rn = hhRandom.nextDouble();

    		// if the choice model has at least one available alternative, make choice.
    		int chosenAlt = -1;
    		if (subsidyModel.getAvailabilityCount() > 0)
    		{
    			try{
    				chosenAlt = subsidyModel.getChoiceResult(rn)-1;
    			} catch (ModelException e){
    				logger.error(String.format(
                              "exception caught for HHID=%d PERSID=%d in choiceModelApplication for subsidy model.", hhObj
                                    .getHhId(), thisPerson.getPersonId()));
    			}
    		} else {
    			logger.error(String.format(
                                   "error: HHID=%d PERSID=%d has no available transit subsidy alternatives to choose from in choiceModelApplication.",
                                   hhObj.getHhId(), thisPerson.getPersonId()));
    			logCalculations(aoLogger, hhObj, thisPerson, subsidyModel, "Subsidy Model");
    			throw new RuntimeException();
    		}
    		if(hhObj.getDebugChoiceModels()) {
       			logCalculations(aoLogger, hhObj, thisPerson, subsidyModel, "Subsidy Model");
   			}

   			//set choice and subsidy percent in person object and DMU
   			thisPerson.setTransitSubsidyChoice((short) (chosenAlt));
   			if(chosenAlt==HAS_TRANSIT_SUBSIDY) {
       			rn = hhRandom.nextDouble();
       			float subsidyPercent = sampleSubsidy(rn);
       			thisPerson.setTransitSubsidyPercent(subsidyPercent);
       			ttDmuObject.setHasSubsidy(1);
   			}else {
   				ttDmuObject.setHasSubsidy(0);
   			}
    				
   			// compute utilities and choose transit pass ownership alternative.
   			passModel.computeUtilities(ttDmuObject, ttDmuObject.getDmuIndexValues());
   			rn = hhRandom.nextDouble();

   			// if the choice model has at least one available alternative, make choice.
    		chosenAlt = -1;
    		if (passModel.getAvailabilityCount() > 0)
    		{
    			try
    			{
    			chosenAlt = passModel.getChoiceResult(rn)-1;
    			} catch (ModelException e)
    			{
    				logger.error(String.format(
                               "exception caught for HHID=%d PERSID=%d in choiceModelApplication for transit pass model.", hhObj
                                      .getHhId(), thisPerson.getPersonId()));
    			}
    		} else
    		{
    			logger.error(String.format(
                                   "error: HHID=%d PERSID=%d has no available transit pass alternatives to choose from in choiceModelApplication.",
                                   hhObj.getHhId(), thisPerson.getPersonId()));
    			logCalculations(aoLogger, hhObj, thisPerson, passModel, "Transit Pass Model");
    			throw new RuntimeException();
    		}
    			
    		if(hhObj.getDebugChoiceModels()) {
       			logCalculations(aoLogger, hhObj, thisPerson, passModel, "Transit Pass Model");
   			}

   			//set choice in person object
   			thisPerson.setTransitPassChoice((short) (chosenAlt));
   			 			
   			
   		} //end persons
   
    }
    
    	
    	
    /**
     * Sample from the probabilities calculated in the setupNaicsArrays method and
     * return the NAICS code corresponding to the work MAZ and random number. If the MAZ
     * is not found or 
     * @param workMaz
     * @param randomNumber
     * @return the NAICS code 10,20,30...90
     */
	public int sampleNaicsCodeForMAZ(int workMaz, double randomNumber) {
			
		HashMap<Integer, double[]> naicsProbabilitiesByMAZ = mgraManager.getNaicsProbabilitiesByMAZ();
		
		if (naicsProbabilitiesByMAZ.containsKey(workMaz)){
	   		
	   		double[] probabilities = naicsProbabilitiesByMAZ.get(workMaz);
	    		
	   		double cumProb=0;
	   		for(int i=0;i<10;++i) {
	   			
	   			cumProb += probabilities[i];
	   			if(cumProb> randomNumber) {
	   				return i*10+10;
	   			}
	   		}
	    }
		return 0;
	}

	private void logCalculations(Logger logger, Household thisHousehold, Person thisPerson, ChoiceModelApplication thisModel, String thisModelName) {

		thisHousehold.logHouseholdObject(thisModelName, aoLogger);
		thisPerson.logPersonObject(logger, 100);

        double[] utilities = thisModel.getUtilities();
        double[] probabilities = thisModel.getProbabilities();

        logger
                    .info("Alternative                    Utility       Probability           CumProb");
        logger
                    .info("--------------------   ---------------      ------------      ------------");

        double cumProb = 0.0;
        for (int k = 0; k < thisModel.getNumberOfAlternatives(); k++)
        {
            cumProb += probabilities[k];
            logger.info(String.format("%-20s%18.6e%18.6e%18.6e", k + " autos", utilities[k],
                        probabilities[k], cumProb));
        }

        logger
                    .info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++");
        logger.info("");
        logger.info("");

        // write choice model alternative info to debug log file
        thisModel.logAlternativesInfo(thisModelName, String.format("HH_%d, Person %d",
            		thisHousehold.getHhId(),thisPerson.getPersonId()));
        
        // write UEC calculation results to separate model specific log file
        thisModel.logUECResults(logger, String.format(thisModelName+"HH_%d, Person %d",
            		thisHousehold.getHhId(),thisPerson.getPersonId()));
           
	}
	
	  /**
     * Read file containing probabilities by subsidy percentage (10,20,30,...100. Store cumulative
     * distribution in subsidyDistribution.
     * 
     * @param fileName
     *            Name of file containing two columns, one row for each subsidy amount.
     *            First column has subsidy percentage, second column has
     *            probability.
     */
    protected void setSubsidyDistribution(String fileName)
    {
        logger.info("Begin reading the data in file " + fileName);
        TableDataSet probabilityTable;

        try
        {
            OLD_CSVFileReader csvFile = new OLD_CSVFileReader();
            probabilityTable = csvFile.readFile(new File(fileName));
        } catch (IOException e)
        {
            throw new RuntimeException(e);
        }

        logger.info("End reading the data in file " + fileName);

        subsidyDistribution = new double[probabilityTable.getRowCount()];
        subsidyPercent = new double[probabilityTable.getRowCount()];

        double total_prob = 0.0;
        // calculate and store cumulative probability distribution
        for (int i = 0; i < subsidyDistribution.length; ++i)
        {

            double percent = probabilityTable.getValueAt(i + 1, "SubsidizedPercentage");
            double probability = probabilityTable.getValueAt(i + 1, "Percent");

            total_prob += probability;
            subsidyDistribution[i] = total_prob;
            subsidyPercent[i]=percent;

        }
        logger.info("End storing cumulative probabilities from file " + fileName);
    }

    /**
     * Choose a subsidy amount.
     * 
     * @param random
     *            A uniform random number.
     * @return the subsidy amount.
     */
    protected float sampleSubsidy(double random)
    {
        // iterate through the probability array and choose
        for (int alt = 0; alt < subsidyDistribution.length; ++alt)
        {
            if (subsidyDistribution[alt] > random) return (float) subsidyPercent[alt];
        }
        throw new RuntimeException();
    }

    
    public double[] getBestPeakWalkTransitSkims(int originMaz, int destinationMaz, boolean debug) {
    	
    	double[] skims = null;
		double boardAccessTime;
		double alightAccessTime;
				
		int period = 1; //1=AM

		int originTaz = mgraManager.getTaz(originMaz);
		int destinationTaz = mgraManager.getTaz(destinationMaz);
		double[] dist = anmCalculator.getTazDistanceFromTaz(originTaz, ModelStructure.AM_SKIM_PERIOD_INDEX);
		
		float odDistance  = (float) dist[destinationTaz];
		
		double transitUtility = bestPathCalculator.calcPersonSpecificUtilities(originTaz, destinationTaz, walkDmu, driveDmu, WTW, originMaz, destinationMaz, period, debug, logger, odDistance);
			
		if(transitUtility <-500)
			return skims;
		
        boardAccessTime = mgraManager.getPMgraToStopsWalkTime(originMaz,period);
    	alightAccessTime = mgraManager.getAMgraFromStopsWalkTime(destinationMaz,period);
	    skims = wtw.getWalkTransitWalkSkims(boardAccessTime, alightAccessTime, originTaz, destinationTaz, period, debug); 

	    return skims;
    }
	
    public double calculateGeneralizedTransitTime(double[] skims, double vot, boolean debug) {
    	
        double accTime = skims[SkimBuilder.TRANSIT_SET_ACCESS_TIME_INDEX];
        double egrTime = skims[SkimBuilder.TRANSIT_SET_EGRESS_TIME_INDEX];
        double auxTime = skims[SkimBuilder.TRANSIT_SET_AUX_WALK_TIME_INDEX];
        double locTime = skims[SkimBuilder.TRANSIT_SET_LOCAL_BUS_TIME_INDEX];
        double expTime = skims[SkimBuilder.TRANSIT_SET_EXPRESS_BUS_TIME_INDEX];
        double hvyTime = skims[SkimBuilder.TRANSIT_SET_HR_TIME_INDEX];
        double fryTime = skims[SkimBuilder.TRANSIT_SET_FR_TIME_INDEX];
        double lrtTime = skims[SkimBuilder.TRANSIT_SET_LRT_TIME_INDEX];
        double comTime = skims[SkimBuilder.TRANSIT_SET_CR_TIME_INDEX];
        double fwtTime = skims[SkimBuilder.TRANSIT_SET_FIRST_WAIT_TIME_INDEX ];
        double xwtTime = skims[SkimBuilder.TRANSIT_SET_TRANSFER_WAIT_TIME_INDEX];
        double fare = skims[SkimBuilder.TRANSIT_SET_FARE_INDEX];
        double xfers = skims[SkimBuilder.TRANSIT_SET_XFERS_INDEX];

    	double totalIVT = locTime+expTime+hvyTime+fryTime+lrtTime+comTime;
    	
    	if(debug) {
    		
    		aoLogger.info("");
    		aoLogger.info("Generalized transit skim calculations");
    		aoLogger.info("");
    		aoLogger.info("VOT = "+vot);
    		aoLogger.info("accTime = "+skims[SkimBuilder.TRANSIT_SET_ACCESS_TIME_INDEX]);
    		aoLogger.info("egrTime = "+skims[SkimBuilder.TRANSIT_SET_EGRESS_TIME_INDEX]);
    		aoLogger.info("auxTime = "+skims[SkimBuilder.TRANSIT_SET_AUX_WALK_TIME_INDEX]);
    		aoLogger.info("locTime = "+skims[SkimBuilder.TRANSIT_SET_LOCAL_BUS_TIME_INDEX]);
    		aoLogger.info("expTime = "+skims[SkimBuilder.TRANSIT_SET_EXPRESS_BUS_TIME_INDEX]);
    		aoLogger.info("hvyTime = "+skims[SkimBuilder.TRANSIT_SET_HR_TIME_INDEX]);
    		aoLogger.info("fryTime = "+skims[SkimBuilder.TRANSIT_SET_FR_TIME_INDEX]);   										
    		aoLogger.info("lrtTime = "+skims[SkimBuilder.TRANSIT_SET_LRT_TIME_INDEX]);
    		aoLogger.info("comTime = "+skims[SkimBuilder.TRANSIT_SET_CR_TIME_INDEX]);
    		aoLogger.info("fwtTime = "+skims[SkimBuilder.TRANSIT_SET_FIRST_WAIT_TIME_INDEX]);
    		aoLogger.info("xwtTime = "+skims[SkimBuilder.TRANSIT_SET_TRANSFER_WAIT_TIME_INDEX]);
    		aoLogger.info("fare = "+skims[SkimBuilder.TRANSIT_SET_FARE_INDEX]);
    		aoLogger.info("xfers = "+skims[SkimBuilder.TRANSIT_SET_XFERS_INDEX]);
    		aoLogger.info("totalIVT = "+(locTime+expTime+hvyTime+fryTime+lrtTime+comTime));

        	if(totalIVT>0)
        		aoLogger.info("Total Gen Cost = "+(totalIVT + 1.5*(accTime+egrTime+auxTime+fwtTime)+2.0*xwtTime+10*xfers + (fare*100)/(vot*60.0)));
        	else
        		aoLogger.info("Total Gen Cost = 0");
    		
    	}
    	
    	
    	
    	
    	
    	if(totalIVT>0)
    		return totalIVT + 1.5*(accTime+egrTime+auxTime+fwtTime)+2.0*xwtTime+10*xfers + (fare*100)/(vot*60.0);
    	
    	return 0;
    }
    
    
    public double calculateGeneralizedAutoTime(TransitSubsidyAndPassDMU ttDmuObject) {
    	
   		
		// compute utilities 
		autoGenTimeModel.computeUtilities(ttDmuObject, ttDmuObject.getDmuIndexValues());
		double[] utilities = autoGenTimeModel.getUtilities();
    	
		return utilities[0];
    	
    	
    	
    }
    
    
   
}
