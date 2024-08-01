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

    private transient Logger                   logger   = Logger.getLogger(ExplicitTelecommuteModel.class);
    private transient Logger                   etLogger = Logger.getLogger("et");

    private static final String                ET_CONTROL_FILE_TARGET = "et.uec.file";
    private static final String                ET_MODEL_SHEET_TARGET  = "et.model.page";
    private static final String                ET_DATA_SHEET_TARGET   = "et.data.page";
    private static final String 			   ET_UPDATE_CDAP_MODEL_SHEET_TARGET = "et.updatecdap.model.page";
    public static final int        			   ET_MODEL_NO_ALT = 1;
    public static final int        			   ET_MODEL_YES_ALT = 2;



    private AccessibilitiesTable accTable;
    private MgraDataManager mgraManager;
    
    private double meanReimb;
    private double stdDevReimb;
    
    private int[]                               mgraParkArea;
    private int[]                               numfreehrs;
    private int[]                               hstallsoth;
    private int[]                               hstallssam;
    private float[]                             hparkcost;
    private int[]                               dstallsoth;
    private int[]                               dstallssam;
    private float[]                             dparkcost;
    private int[]                               mstallsoth;
    private int[]                               mstallssam;
    private float[]                             mparkcost;
    
    private double[]                            lsWgtAvgCostM;
    private double[]                            lsWgtAvgCostD;
    private double[]                            lsWgtAvgCostH;
    
    private ChoiceModelApplication etModel;
    private ChoiceModelApplication updateCdapModel;
    private ExplicitTelecommuteDMU etDmuObject;
    

    
    public ExplicitTelecommuteModel( HashMap<String, String> propertyMap, CtrampDmuFactoryIf dmuFactory )
    {        
        mgraManager = MgraDataManager.getInstance(propertyMap);        
        setupExplicitTelecommuteChoiceModel(propertyMap, dmuFactory);
    }

    private void setupExplicitTelecommuteChoiceModel(HashMap<String, String> propertyMap, CtrampDmuFactoryIf dmuFactory)
    {
        logger.info("setting up explicit telecommute model.");

        // locate the explicit telecommute  UEC
        String uecFileDirectory = propertyMap.get( CtrampApplication.PROPERTIES_UEC_PATH );
        String etUecFile = uecFileDirectory + propertyMap.get(ET_CONTROL_FILE_TARGET);

        int dataSheet = Util.getIntegerValueFromPropertyMap( propertyMap, ET_DATA_SHEET_TARGET );
        int modelSheet = Util.getIntegerValueFromPropertyMap( propertyMap, ET_MODEL_SHEET_TARGET );
        int updateCdapModelSheet = Util.getIntegerValueFromPropertyMap(propertyMap, ET_UPDATE_CDAP_MODEL_SHEET_TARGET);
        // create the explicit telecommute choice model DMU object.
        etDmuObject = dmuFactory.getExplicitTelecoummteDMU();

        // create the explicit telecommute choice model object
        etModel = new ChoiceModelApplication(etUecFile, modelSheet, dataSheet, propertyMap, (VariableTable) etDmuObject);
        updateCdapModel = new ChoiceModelApplication(etUecFile, updateCdapModelSheet, dataSheet, propertyMap, (VariableTable) etDmuObject);
        
        //meanReimb = Float.parseFloat( propertyMap.get(REIMBURSEMENT_MEAN) );
        //stdDevReimb = Float.parseFloat( propertyMap.get(REIMBURSEMENT_STD_DEV) );

        mgraParkArea = mgraManager.getMgraParkAreas();
        numfreehrs = mgraManager.getNumFreeHours();
        lsWgtAvgCostM = mgraManager.getLsWgtAvgCostM();
        lsWgtAvgCostD = mgraManager.getLsWgtAvgCostD();
        lsWgtAvgCostH = mgraManager.getLsWgtAvgCostH();
        mstallsoth = mgraManager.getMStallsOth();
        mstallssam = mgraManager.getMStallsSam();
        mparkcost = mgraManager.getMParkCost();
        dstallsoth = mgraManager.getDStallsOth();
        dstallssam = mgraManager.getDStallsSam();
        dparkcost = mgraManager.getDParkCost();
        hstallsoth = mgraManager.getHStallsOth();
        hstallssam = mgraManager.getHStallsSam();
        hparkcost = mgraManager.getHParkCost();
        
    }

    
    public void applyModel(Household hhObject){

        Random hhRandom = hhObject.getHhRandom();
        //Get pre-telecommute hh cdap
        hhObject.setPreEtCdapPattern(hhObject.getCoordinatedDailyActivityPattern());
        // person array is 1-based
        Person[] person = hhObject.getPersons();         
        for (int i=1; i<person.length; i++) 
        {
            int workLoc = person[i].getUsualWorkLocation();
            String cdap = person[i].getCdapActivity();
            person[i].setPreExplicitTelecommuteCdap(cdap);
            int cdapIndex = person[i].getCdapIndex();
            if ( workLoc != ModelStructure.WORKS_AT_HOME_LOCATION_INDICATOR && workLoc >0 && cdapIndex == 1 ) 
            {
                double randomNumber = hhRandom.nextDouble();
                int chosen = getEtChoice(person[i], randomNumber);
                person[i].setEtChoice(chosen);
                if (chosen == 2) 
                {
                	String hhCdap = hhObject.getCoordinatedDailyActivityPattern();
                	int person_index = person[i].getPersonNum();
                	String newChosenCdapActivity = "N"; //if the HH pattern is joint, update cdap to N
                	if (hhCdap.charAt(hhCdap.length()-1)=='0')
                	{
                		//Update cdap to Non-Mandatory or Home according to a fixed probability distribution if pattern is not j
                    	updateCdapModel.computeUtilities(etDmuObject,etDmuObject.getDmuIndexValues());
                    	int chosenCdap = updateCdapModel.getChoiceResult(randomNumber);
                    	newChosenCdapActivity = (chosenCdap==1)?"N":"H";
                    }
                	
                	person[i].setDailyActivityResult(newChosenCdapActivity);
                	String newHhCdap = hhCdap.substring(0,person_index-1)+ newChosenCdapActivity + hhCdap.substring(person_index);
                	hhObject.setCoordinatedDailyActivityPatternResult(newHhCdap);
                	

                }
                
        }
            else {
            	person[i].setEtChoice(-1); //Not applicable to workers who don't have a work location.
            }
        }

        hhObject.setEtRandomCount( hhObject.getHhRandomCount() );
    }

    
    private int getEtChoice (Person personObj, double randomNumber) {
        
        // get the corresponding household object
        Household hhObj = personObj.getHouseholdObject();
        etDmuObject.setPersonObject( personObj );
        
        etDmuObject.setMgraParkArea( mgraParkArea[personObj.getUsualWorkLocation()] );
        etDmuObject.setNumFreeHours( numfreehrs[personObj.getUsualWorkLocation()] );
        etDmuObject.setLsWgtAvgCostM( lsWgtAvgCostM[personObj.getUsualWorkLocation()] );
        etDmuObject.setLsWgtAvgCostD( lsWgtAvgCostD[personObj.getUsualWorkLocation()] );
        etDmuObject.setLsWgtAvgCostH( lsWgtAvgCostH[personObj.getUsualWorkLocation()] );
        etDmuObject.setMStallsOth( mstallsoth[personObj.getUsualWorkLocation()] );
        etDmuObject.setMStallsSam( mstallssam[personObj.getUsualWorkLocation()] );
        etDmuObject.setMParkCost( mparkcost[personObj.getUsualWorkLocation()] );
        etDmuObject.setDStallsSam( dstallssam[personObj.getUsualWorkLocation()] );
        etDmuObject.setDStallsOth( dstallsoth[personObj.getUsualWorkLocation()] );
        etDmuObject.setDParkCost( dparkcost[personObj.getUsualWorkLocation()] );
        etDmuObject.setHStallsOth( hstallsoth[personObj.getUsualWorkLocation()] );
        etDmuObject.setHStallsSam( hstallssam[personObj.getUsualWorkLocation()] );
        etDmuObject.setHParkCost( hparkcost[personObj.getUsualWorkLocation()] );
        
        
        // set the zone and dest attributes to the person's work location
        etDmuObject.setDmuIndexValues(hhObj.getHhId(),personObj.getUsualWorkLocation(),hhObj.getHhTaz(),personObj.getUsualWorkLocation());

        // compute utilities and choose auto ownership alternative.
        etModel.computeUtilities (etDmuObject,etDmuObject.getDmuIndexValues() );

        // if the choice model has at least one available alternative, make choice.
        int chosenAlt;
        if (etModel.getAvailabilityCount() > 0) {
            chosenAlt = etModel.getChoiceResult(randomNumber);
        }
        else {
            String decisionMaker = String.format("HHID=%d, PERSID=%d",  hhObj.getHhId(), personObj.getPersonId() );
            String errorMessage = String.format("Exception caught for %s, no available explicit telecommute options to choose from in choiceModelApplication.", decisionMaker );
            logger.error (errorMessage);
            
            etModel.logUECResults( logger, decisionMaker );            
            throw new RuntimeException();
        }

        // write choice model alternative info to log file
        if ( hhObj.getDebugChoiceModels() ) {
            String decisionMaker = String.format("HHID=%d, PERSID=%d",  hhObj.getHhId(), personObj.getPersonId() );
            etModel.logAlternativesInfo("Explicit Telecommute Choice", decisionMaker, logger);
            logger.info(String.format("%s result chosen for %s is %d with rn %.8f",
                    "Explicit Telecommute Choice", decisionMaker, chosenAlt, randomNumber));
            etModel.logUECResults( logger, decisionMaker );            
        }

        return chosenAlt;
    }
}