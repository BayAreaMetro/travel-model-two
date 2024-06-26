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
    public static final int        			   ET_MODEL_NO_ALT = 1;
    public static final int        			   ET_MODEL_YES_ALT = 2;

    private ChoiceModelApplication etModel;
    private ExplicitTelecommuteDMU etDmuObject;

    private AccessibilitiesTable accTable;
    
    private double[] pctHighIncome;
    private double[] pctMedHighPlusIncome;
    private double[] pctMultipleAutos;
    private double[] avgtts;
    private double[] transpDist;
    private double[] pctDetour;
    
    public ExplicitTelecommuteModel( HashMap<String, String> propertyMap, CtrampDmuFactoryIf dmuFactory, AccessibilitiesTable accTable,
            double[] pctHighIncome, double[] pctMedHighPlusIncome, double[] pctMultipleAutos, double[] avgtts, double[] transpDist, double[] pctDetour )
    {
        this.accTable = accTable;
        this.pctHighIncome = pctHighIncome;
        this.pctMedHighPlusIncome = pctMedHighPlusIncome;
        this.pctMultipleAutos = pctMultipleAutos;
        this.avgtts = avgtts;
        this.transpDist = transpDist;
        this.pctDetour = pctDetour;
        
        setupExplictiTelecommuteModelApplication(propertyMap, dmuFactory);
    }

    private void setupExplictiTelecommuteModelApplication(HashMap<String, String> propertyMap, CtrampDmuFactoryIf dmuFactory)
    {
        logger.info("setting up explicit telecommute choice model.");

        // locate the explicit telecommute choice UEC
        String uecFileDirectory = propertyMap.get( CtrampApplication.PROPERTIES_UEC_PATH );
        String etUecFile = uecFileDirectory + propertyMap.get(ET_CONTROL_FILE_TARGET);

        int dataSheet = Util.getIntegerValueFromPropertyMap( propertyMap, ET_DATA_SHEET_TARGET );
        int modelSheet = Util.getIntegerValueFromPropertyMap( propertyMap, ET_MODEL_SHEET_TARGET );
        
        // create the explicit telecommute choice model DMU object.
        etDmuObject = dmuFactory.getExplicitTelecoummteDMU();

        // create the explicit telecommute choice model object
        etModel = new ChoiceModelApplication(etUecFile, modelSheet, dataSheet, propertyMap, (VariableTable) etDmuObject);

    }

    
    public void applyModel(Household hhObject){

        int homeTaz = hhObject.getHhTaz();

        etDmuObject.setHouseholdObject( hhObject );
        
        // set the zone, orig and dest attributes
        etDmuObject.setDmuIndexValues( hhObject.getHhId(), hhObject.getHhTaz(), hhObject.getHhTaz(), 0 );
        
        etDmuObject.setPctIncome100Kplus( pctHighIncome[homeTaz] ); 
        etDmuObject.setPctIncome75Kplus( pctMedHighPlusIncome[homeTaz] );
        etDmuObject.setPctTazMultpleAutos( pctMultipleAutos[homeTaz] ); 
        etDmuObject.setExpectedTravelTimeSavings( avgtts[homeTaz] ); 
        etDmuObject.setTransponderDistance( transpDist[homeTaz] ); 
        etDmuObject.setPctDetour( pctDetour[homeTaz] );

        float accessibility = accTable.getAggregateAccessibility("transit", hhObject.getHhMgra());
        etDmuObject.setAccessibility( accessibility );


        Random hhRandom = hhObject.getHhRandom();
        double randomNumber = hhRandom.nextDouble();
        
        // compute utilities and choose transponder choice alternative.
        etModel.computeUtilities ( etDmuObject, etDmuObject.getDmuIndexValues() );

        // if the choice model has at least one available alternative, make choice.
        int chosenAlt;
        if ( etModel.getAvailabilityCount() > 0) {
            chosenAlt = etModel.getChoiceResult(randomNumber);
        }
        else {
            String decisionMaker = String.format("HHID=%d",  hhObject.getHhId() );
            String errorMessage = String.format("Exception caught for %s, no available explicit telecommute alternatives to choose from in choiceModelApplication.", decisionMaker );
            logger.error (errorMessage);
            
            etModel.logUECResults( logger, decisionMaker );            
            throw new RuntimeException();
        }

        // write choice model alternative info to log file
        if ( hhObject.getDebugChoiceModels() ) {
            String decisionMaker = String.format("HHID=%d",  hhObject.getHhId() );
            etModel.logAlternativesInfo("Explicit Telecommute Choice", decisionMaker, logger);
            logger.info( String.format("%s result chosen for %s is %d with rn %.8f",
                    "Explicit Telecommute Choice", decisionMaker, chosenAlt, randomNumber));
            etModel.logUECResults( logger, decisionMaker );            
        }
        
        hhObject.setEtChoice( chosenAlt-1 );

        hhObject.setTpRandomCount( hhObject.getHhRandomCount() );
    }
    
}
