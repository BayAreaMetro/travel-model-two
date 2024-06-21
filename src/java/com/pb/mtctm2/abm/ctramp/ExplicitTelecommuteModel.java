package com.pb.mtctm2.abm.ctramp;

import java.io.Serializable;
import java.util.HashMap;
import java.util.Random;
import com.pb.common.calculator.VariableTable;
import com.pb.common.model.ModelException;
import com.pb.mtctm2.abm.accessibilities.AccessibilitiesTable;
import com.pb.mtctm2.abm.accessibilities.MandatoryAccessibilitiesCalculator;

import org.apache.log4j.Logger;

public class ExplicitTelecommuteModel
        implements Serializable
{

    private transient Logger                   logger                 = Logger.getLogger(ExplicitTelecommuteModel.class);
    private transient Logger                   etLogger               = Logger.getLogger("et");

    private static final String                ET_CONTROL_FILE_TARGET = "et.uec.file";
    private static final String                ET_MODEL_SHEET_TARGET  = "et.model.page";
    private static final String                ET_DATA_SHEET_TARGET   = "et.data.page";

    private static final int                   AUTO_SOV_TIME_INDEX    = 10;
    private static final int                   AUTO_LOGSUM_INDEX      = 6;
    private static final int                   TRANSIT_LOGSUM_INDEX   = 8;
    private static final int                   DT_RAIL_PROP_INDEX     = 10;

    private AccessibilitiesTable               accTable;
    private MandatoryAccessibilitiesCalculator mandAcc;
    private ChoiceModelApplication             etModel;
    private ExplicitTelecommuteDMU             etDmuObject;
    
    private int[]                              totalAutosByAlt;
    private int[]                              automatedVehiclesByAlt;
    private int[]                              conventionalVehiclesByAlt;

    public ExplicitTelecommuteModel(HashMap<String, String> rbMap,
            CtrampDmuFactoryIf dmuFactory, AccessibilitiesTable myAccTable, MandatoryAccessibilitiesCalculator myMandAcc)
    {

        logger.info("setting up ET choice model.");

        // set the aggAcc class variable, which will serve as a flag: null -> no
        // accessibilities, !null -> set accessibilities.
        // if the BuildAccessibilities object is null, the AO utility does not need
        // to use the accessibilities components.
        accTable = myAccTable;
        mandAcc = myMandAcc;
        
        // locate the auto ownership UEC
        String uecPath = rbMap.get(CtrampApplication.PROPERTIES_UEC_PATH);
        String explicitiTelecommuteUecFile = rbMap.get(ET_CONTROL_FILE_TARGET);
        explicitiTelecommuteUecFile = uecPath + explicitiTelecommuteUecFile;

        int dataPage = Util.getIntegerValueFromPropertyMap(rbMap, ET_DATA_SHEET_TARGET);
        int modelPage = Util.getIntegerValueFromPropertyMap(rbMap, ET_MODEL_SHEET_TARGET);

        // create the explicit telecommute choice model DMU object.
        etDmuObject = dmuFactory.getExplicitTelecoummteDMU();

        // create the auto ownership choice model object
        etModel = new ChoiceModelApplication(explicitiTelecommuteUecFile, modelPage, dataPage, rbMap,
                (VariableTable) etDmuObject);
        
        String[] alternativeNames = etModel.getAlternativeNames();
        calculateAlternativeArrays(alternativeNames);

    }

    /**
     * Set the dmu attributes, compute the pre-AO or AO utilities, and select an
     * alternative
     * 
     * @param hhObj for which to apply thye model
     * @param preAutoOwnership is true if running pre-auto ownership, or false to run
     *            primary auto ownership model.
     */

    public void applyModel(Household hhObj, boolean preAutoOwnership)
    {

        // update the AO dmuObject for this hh
    	etDmuObject.setHouseholdObject(hhObj);
    	etDmuObject.setDmuIndexValues(hhObj.getHhId(), hhObj.getHhMgra(), hhObj.getHhMgra(), 0);

        // set the non-mandatory accessibility values for the home MGRA.
        // values used by both pre-ao and ao models.
    	etDmuObject.setHomeTazAutoAccessibility( accTable.getAggregateAccessibility("auto", hhObj.getHhMgra() ) );
    	etDmuObject.setHomeTazTransitAccessibility( accTable.getAggregateAccessibility("transit", hhObj.getHhMgra() ) );
    	etDmuObject.setHomeTazNonMotorizedAccessibility( accTable.getAggregateAccessibility( "nonmotor", hhObj.getHhMgra() ) );

        if (preAutoOwnership)
        {

            etDmuObject.setUseAccessibilities(false);

        } else
        {

            etDmuObject.setUseAccessibilities(true);

            // compute the disaggregate accessibilities for the home MGRA to work and
            // school MGRAs summed accross workers and students
            double workAutoDependency = 0.0;
            double schoolAutoDependency = 0.0;
            double workRailProp = 0.0;
            double schoolRailProp = 0.0;
            double workAutoTime = 0.0;
           
            Person[] persons = hhObj.getPersons();
            for (int i = 1; i < persons.length; i++)
            {

                // sum over all workers (full time or part time)
                if (persons[i].getPersonIsWorker() == 1)
                {

                    int workMgra = persons[i].getUsualWorkLocation();
                    if (workMgra != ModelStructure.WORKS_AT_HOME_LOCATION_INDICATOR)
                    {

                        // Non-Motorized Factor = 0.5*MIN(MAX(DIST,1),3)-0.5
                        // if 0 <= dist < 1, nmFactor = 0
                        // if 1 <= dist <= 3, nmFactor = [0.0, 1.0]
                        // if 3 <= dist, nmFactor = 1.0
                        double nmFactor = 0.5 * (Math.min(Math.max(persons[i].getWorkLocationDistance(), 1.0), 3.0)) - 0.5;

                        // if auto logsum < transit logsum, do not accumulate auto
                        // dependency
                        double[] workerAccessibilities = mandAcc.calculateWorkerMandatoryAccessibilities(hhObj.getHhMgra(), workMgra);
           
                        workAutoTime += workerAccessibilities[AUTO_SOV_TIME_INDEX];
                        if (workerAccessibilities[AUTO_LOGSUM_INDEX] >= workerAccessibilities[TRANSIT_LOGSUM_INDEX])
                        {
                            double logsumDiff = workerAccessibilities[AUTO_LOGSUM_INDEX]
                                    - workerAccessibilities[TRANSIT_LOGSUM_INDEX];

                            // need to scale and cap logsum difference
                            logsumDiff = Math.min(logsumDiff / 3.0, 1.0);
                            workAutoDependency += (logsumDiff * nmFactor);
                        }

                        workRailProp += workerAccessibilities[DT_RAIL_PROP_INDEX];

                    }

                }

                // sum over all students of driving age
                if (persons[i].getPersonIsUniversityStudent() == 1
                        || persons[i].getPersonIsStudentDriving() == 1)
                {

                    int schoolMgra = persons[i].getUsualSchoolLocation();
                    if (schoolMgra != ModelStructure.NOT_ENROLLED_SEGMENT_INDEX)
                    {

                        // Non-Motorized Factor = 0.5*MIN(MAX(DIST,1),3)-0.5
                        // if 0 <= dist < 1, nmFactor = 0
                        // if 1 <= dist <= 3, nmFactor = [0.0, 1.0]
                        // if 3 <= dist, nmFactor = 1.0
                        double nmFactor = 0.5 * (Math.min(Math.max(persons[i]
                                .getWorkLocationDistance(), 1.0), 3.0)) - 0.5;

                        // if auto logsum < transit logsum, do not accumulate auto
                        // dependency
                        double[] studentAccessibilities = mandAcc.calculateStudentMandatoryAccessibilities(hhObj.getHhMgra(), schoolMgra);
                        if (studentAccessibilities[AUTO_LOGSUM_INDEX] >= studentAccessibilities[TRANSIT_LOGSUM_INDEX])
                        {
                            double logsumDiff = studentAccessibilities[AUTO_LOGSUM_INDEX]
                                    - studentAccessibilities[TRANSIT_LOGSUM_INDEX];

                            // need to scale and cap logsum difference
                            logsumDiff = Math.min(logsumDiff / 3.0, 1.0);
                            schoolAutoDependency += (logsumDiff * nmFactor);
                        }

                        schoolRailProp += studentAccessibilities[DT_RAIL_PROP_INDEX];

                    }
                }

            }

            etDmuObject.setWorkAutoDependency(workAutoDependency);
            etDmuObject.setSchoolAutoDependency(schoolAutoDependency);

            etDmuObject.setWorkersRailProportion(workRailProp);
            etDmuObject.setStudentsRailProportion(schoolRailProp);
            
            etDmuObject.setWorkAutoTime(workAutoTime);

        }

        // compute utilities and choose auto ownership alternative.
        etModel.computeUtilities(etDmuObject, etDmuObject.getDmuIndexValues());

        Random hhRandom = hhObj.getHhRandom();
        int randomCount = hhObj.getHhRandomCount();
        double rn = hhRandom.nextDouble();

        // if the choice model has at least one available alternative, make choice.
        int chosenAlt = -1;
        if (etModel.getAvailabilityCount() > 0)
        {
            try
            {
                chosenAlt = etModel.getChoiceResult(rn);
            } catch (ModelException e)
            {
                logger
                        .error(String.format(
                                "exception caught for HHID=%d in choiceModelApplication.", hhObj
                                        .getHhId()));
            }
        } else
        {
            logger
                    .error(String
                            .format(
                                    "error: HHID=%d has no available auto ownership alternatives to choose from in choiceModelApplication.",
                                    hhObj.getHhId()));
            throw new RuntimeException();
        }

        // write choice model alternative info to log file
        if (hhObj.getDebugChoiceModels() || chosenAlt < 0)
        {

            String loggerString = (preAutoOwnership ? "Pre-AO without" : "AO with")
                    + " accessibilities, Household " + hhObj.getHhId() + " Object";
            hhObj.logHouseholdObject(loggerString, etLogger);

            double[] utilities = etModel.getUtilities();
            double[] probabilities = etModel.getProbabilities();

            etLogger
                    .info("Alternative                    Utility       Probability           CumProb");
            etLogger
                    .info("--------------------   ---------------      ------------      ------------");

            double cumProb = 0.0;
            for (int k = 0; k < etModel.getNumberOfAlternatives(); k++)
            {
                cumProb += probabilities[k];
                etLogger.info(String.format("%-20s%18.6e%18.6e%18.6e", k + " autos", utilities[k],
                        probabilities[k], cumProb));
            }

            etLogger.info(" ");
            etLogger.info(String.format("Choice: %s, with rn=%.8f, randomCount=%d", chosenAlt, rn,
                    randomCount));

            etLogger
                    .info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++");
            etLogger.info("");
            etLogger.info("");

            // write choice model alternative info to debug log file
            etModel.logAlternativesInfo("Household Auto Ownership Choice", String.format("HH_%d",
                    hhObj.getHhId()));
            etModel.logSelectionInfo("Household Auto Ownership Choice", String.format("HH_%d",
                    hhObj.getHhId()), rn, chosenAlt);

            // write UEC calculation results to separate model specific log file
            etModel.logUECResults(etLogger, String.format("Household Auto Ownership Choice, HH_%d",
                    hhObj.getHhId()));
        }

        if (preAutoOwnership) hhObj.setPreAoRandomCount(hhObj.getHhRandomCount());
        else hhObj.setAoRandomCount(hhObj.getHhRandomCount());

        int autos = totalAutosByAlt[chosenAlt-1];
        int AVs = automatedVehiclesByAlt[chosenAlt-1];
        int CVs = conventionalVehiclesByAlt[chosenAlt-1];
        hhObj.setHhAutos(autos);
        hhObj.setAutomatedVehicles(AVs);
        hhObj.setConventionalVehicles(CVs);

    }
    
    
    /**
     * This is a helper method that iterates through the alternative names
     * in the auto ownership UEC and searches through each name to collect 
     * the total number of autos (in the first position of the name character
     * array), the number of AVs for the alternative (preceded by the "AV" substring) 
     * and the number of CVs for the alternative (preceded by the "CV" substring). The
     * results are stored in the arrays:
     * 
     *  totalAutosByAlt
     *  automatedVehiclesByAlt
     *  conventionalVehiclesByAlt
     *  
     * @param alternativeNames The array of alternative names.
     */
    private void calculateAlternativeArrays(String[] alternativeNames){
    	
    	totalAutosByAlt = new int[alternativeNames.length];
	    automatedVehiclesByAlt = new int[alternativeNames.length];
	    conventionalVehiclesByAlt = new int[alternativeNames.length];
   	
    	
    	//iterate thru names
    	for(int i = 0; i < alternativeNames.length;++i){
    		
    		String altName = alternativeNames[i];
    		
    		//find the number of cars; first element of name (e.g. 0_CARS)
    		int autos = new Integer(altName.substring(0,1)).intValue();
    		int AVs=0;
    		int HVs=0;
    		int AVPosition = altName.indexOf("AV");
    		if(AVPosition>=0)
    			AVs = new Integer(altName.substring(AVPosition-1, AVPosition)).intValue();
    		int HVPosition = altName.indexOf("HV");
    		if(HVPosition>=0)
    			HVs = new Integer(altName.substring(HVPosition-1, HVPosition)).intValue();
    		
    		totalAutosByAlt[i] = autos;
    	    automatedVehiclesByAlt[i] = AVs;
    	    conventionalVehiclesByAlt[i] = HVs;
   		
    	}
    	
    }
    

}
