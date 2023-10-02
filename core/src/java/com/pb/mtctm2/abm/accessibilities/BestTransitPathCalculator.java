/*
 * Copyright 2005 PB Consult Inc. Licensed under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance with the License. You
 * may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software distributed
 * under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
 * CONDITIONS OF ANY KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations under the License.
 */
package com.pb.mtctm2.abm.accessibilities;

import java.io.File;
import java.io.PrintWriter;
import java.io.Serializable;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.concurrent.ConcurrentHashMap;

import org.apache.log4j.Logger;

import com.pb.mtctm2.abm.ctramp.CtrampApplication;
import com.pb.mtctm2.abm.ctramp.MgraDataManager;
import com.pb.mtctm2.abm.ctramp.ModelStructure;
import com.pb.mtctm2.abm.ctramp.Modes;
import com.pb.mtctm2.abm.ctramp.Modes.AccessMode;
import com.pb.mtctm2.abm.ctramp.TazDataManager;
import com.pb.mtctm2.abm.ctramp.TransitDriveAccessDMU;
import com.pb.mtctm2.abm.ctramp.TransitWalkAccessDMU;
import com.pb.mtctm2.abm.ctramp.Util;
import com.pb.common.calculator.IndexValues;
import com.pb.common.calculator.VariableTable;
import com.pb.common.datafile.OLD_CSVFileReader;
import com.pb.common.datafile.TableDataSet;
import com.pb.common.util.Tracer;
import com.pb.common.newmodel.UtilityExpressionCalculator;
import com.pb.common.newmodel.Alternative;
import com.pb.common.newmodel.ConcreteAlternative;
import com.pb.common.newmodel.LogitModel;
/**
 * WalkPathUEC calculates the best walk-transit utilities for a given MGRA pair.
 * 
 * @author Joel Freedman
 * @version 1.0, May 2009
 */
public class BestTransitPathCalculator implements Serializable
{

    private transient Logger                 logger        = Logger.getLogger(BestTransitPathCalculator.class);

    protected static final String transitFareDiscountFileName = "transit.fareDiscount.file";
    
    //TODO: combine APP_TYPE_xxx constants into a enum structure
    public static final int              APP_TYPE_GENERIC = 0;
    public static final int              APP_TYPE_TOURMC  = 1;
    public static final int              APP_TYPE_TRIPMC  = 2;

    private static final int              EA                            = ModelStructure.EA_SKIM_PERIOD_INDEX;
    private static final int              AM                            = ModelStructure.AM_SKIM_PERIOD_INDEX;
    private static final int              MD                            = ModelStructure.MD_SKIM_PERIOD_INDEX;
    private static final int              PM                            = ModelStructure.PM_SKIM_PERIOD_INDEX;
    private static final int              EV                            = ModelStructure.EV_SKIM_PERIOD_INDEX;
    public static final int              NUM_PERIODS                   = ModelStructure.SKIM_PERIOD_STRINGS.length;

    public static final float               NA            = -999;
    public static final int               WTW           = 0;
    public static final int               PTW           = 1;
    public static final int               WTP           = 2;
    public static final int               KTW           = 3;
    public static final int               WTK           = 4;
    public static final int[]             ACC_EGR       = {WTW,PTW,WTP,KTW,WTK};
    public static final int               NUM_ACC_EGR   = ACC_EGR.length;

    // seek and trace
    private boolean                       trace;
    private int[]                         traceOtaz;
    private int[]                         traceDtaz;
    protected Tracer                      tracer;

    private TazDataManager                tazManager;
    private MgraDataManager               mgraManager;

    private int                           maxMgra;
    private int                           maxTaz;

    // piece-wise utilities are being computed
    private UtilityExpressionCalculator   walkAccessUEC;
    private UtilityExpressionCalculator   walkEgressUEC;
    private UtilityExpressionCalculator   driveAccessUEC;
    private UtilityExpressionCalculator   driveEgressUEC;
    private UtilityExpressionCalculator   tazToTazUEC;
    private UtilityExpressionCalculator   driveAccDisutilityUEC;
    private UtilityExpressionCalculator   driveEgrDisutilityUEC;
 
    // utility data cache for each transit path segment 
    private StoredUtilityData storedDataObject; //Encapsulates data shared by the BestTransitPathCalculator objects created for each hh choice model object
    // note that access/egress utilities are independent of transit skim set 
    private float[][]                  storedWalkAccessUtils;	// references StoredUtilityData.storedWalkAccessUtils
    private float[][]                  storedDriveAccessUtils;// references StoredUtilityData.storedDriveAccessUtils
    private float[][]                  storedWalkEgressUtils;	// references StoredUtilityData.storedWalkEgressUtils
    private float[][]                  storedDriveEgressUtils;// references StoredUtilityData.storedDriveEgressUtils    
    private HashMap<Integer,HashMap<Integer,ConcurrentHashMap<Long,float[]>>> storedDepartPeriodTazTazUtils; //references StoredUtilityData.storedDepartPeriodTazTazUtils

    private IndexValues                   index         = new IndexValues();
       
    private float nestingCoefficient;
    
    HashMap<String, String> rbMap;
    
    private float[][] fareDiscounts;
    /**
     * Constructor.
     * 
     * @param rbMap HashMap<String, String>
     * @param UECFileName The path/name of the UEC containing the walk-transit model.
     * @param modelSheet The sheet (0-indexed) containing the model specification.
     * @param dataSheet The sheet (0-indexed) containing the data specification.
     */
    public BestTransitPathCalculator(HashMap<String, String> rbMap)
    {
    	
    	this.rbMap = rbMap;

        // read in resource bundle properties
        trace = Util.getBooleanValueFromPropertyMap(rbMap, "Trace");
        traceOtaz = Util.getIntegerArrayFromPropertyMap(rbMap, "Trace.otaz");
        traceDtaz = Util.getIntegerArrayFromPropertyMap(rbMap, "Trace.dtaz");

        // set up the tracer object
        tracer = Tracer.getTracer();
        tracer.setTrace(trace);
        if ( trace )
        {
            for (int i = 0; i < traceOtaz.length; i++)
            {
                for (int j = 0; j < traceDtaz.length; j++)
                {
                    tracer.traceZonePair(traceOtaz[i], traceDtaz[j]);
                 }
            }
        }
        

        String uecPath = Util.getStringValueFromPropertyMap(rbMap,CtrampApplication.PROPERTIES_UEC_PATH);
        String uecFileName = Paths.get(uecPath,rbMap.get("utility.bestTransitPath.uec.file")).toString();

        int dataPage = Util.getIntegerValueFromPropertyMap(rbMap,
                "utility.bestTransitPath.data.page");

        int walkAccessPage = Util.getIntegerValueFromPropertyMap(rbMap,
                "utility.bestTransitPath.walkAccess.page");
        int driveAccessPage = Util.getIntegerValueFromPropertyMap(rbMap,
                "utility.bestTransitPath.driveAccess.page");
        int walkEgressPage = Util.getIntegerValueFromPropertyMap(rbMap,
                "utility.bestTransitPath.walkEgress.page");
        int driveEgressPage = Util.getIntegerValueFromPropertyMap(rbMap,
                "utility.bestTransitPath.driveEgress.page");
        int tazToTazPage = Util.getIntegerValueFromPropertyMap( rbMap, 
        		"utility.bestTransitPath.tazToTaz.page" );
        int driveAccDisutilityPage = Util.getIntegerValueFromPropertyMap( rbMap, 
        		"utility.bestTransitPath.driveAccDisutility.page" );
        int driveEgrDisutilityPage = Util.getIntegerValueFromPropertyMap( rbMap, 
        		"utility.bestTransitPath.driveEgrDisutility.page" );
        
        File uecFile = new File(uecFileName);
        walkAccessUEC = createUEC(uecFile, walkAccessPage, dataPage, rbMap, new TransitWalkAccessDMU());
        driveAccessUEC = createUEC(uecFile, driveAccessPage, dataPage, rbMap, new TransitDriveAccessDMU());
        walkEgressUEC = createUEC(uecFile, walkEgressPage, dataPage, rbMap, new TransitWalkAccessDMU());
        driveEgressUEC = createUEC(uecFile, driveEgressPage, dataPage, rbMap, new TransitDriveAccessDMU());
        TransitWalkAccessDMU tazToTazDmu = new TransitWalkAccessDMU();
        tazToTazUEC = createUEC(uecFile, tazToTazPage, dataPage, rbMap, tazToTazDmu);
        driveAccDisutilityUEC = createUEC(uecFile, driveAccDisutilityPage, dataPage, rbMap, new TransitDriveAccessDMU());
        driveEgrDisutilityUEC = createUEC(uecFile, driveEgrDisutilityPage, dataPage, rbMap, new TransitDriveAccessDMU());
        
        mgraManager = MgraDataManager.getInstance(rbMap);
        tazManager = TazDataManager.getInstance(rbMap);

        maxMgra = mgraManager.getMaxMgra();
        maxTaz = tazManager.getMaxTaz();

        // these arrays are shared by the BestTransitPathCalculator objects created for each hh choice model object
        storedDataObject = StoredUtilityData.getInstance( maxMgra, maxTaz, ACC_EGR, ModelStructure.PERIODCODES);
        storedWalkAccessUtils = storedDataObject.getStoredWalkAccessUtils();
        storedDriveAccessUtils = storedDataObject.getStoredDriveAccessUtils();
        storedWalkEgressUtils = storedDataObject.getStoredWalkEgressUtils();
        storedDriveEgressUtils = storedDataObject.getStoredDriveEgressUtils();
        storedDepartPeriodTazTazUtils = storedDataObject.getStoredDepartPeriodTazTazUtils();
        
        nestingCoefficient =  new Float(Util.getStringValueFromPropertyMap(rbMap, "utility.bestTransitPath.nesting.coeff")).floatValue();
        
        String directoryPath = Util.getStringValueFromPropertyMap(rbMap,CtrampApplication.PROPERTIES_PROJECT_DIRECTORY);
        String fareDiscountFileName = Paths.get(directoryPath,rbMap.get(transitFareDiscountFileName)).toString();
        fareDiscounts = readTransitFareDiscounts(fareDiscountFileName);
        tazToTazDmu.setTransitFareDiscounts(fareDiscounts);
        
     }
    

    public float calcWalkAccessUtility(TransitWalkAccessDMU walkDmu, int pMgra, int timePeriod, boolean myTrace, Logger myLogger)
    {
    	double pWalkTime = mgraManager.getPMgraToStopsWalkTime(pMgra, timePeriod);
    	
    	if(pWalkTime==0){
    		//myLogger.info("Walk time from mgra "+pMgra+" to stops is 0; setting walk access utility to "+NA);
    		return NA;
    	}
    	
        walkDmu.setMgraStopsWalkTime(pWalkTime);
        float util = (float)walkAccessUEC.solve(index, walkDmu, null)[0];
        
        // logging
        if (myTrace) {
            walkAccessUEC.logAnswersArray(myLogger, "Walk Orig Mgra=" + pMgra + ", to stops Utility Piece");
        }
        
        return(util);
        
    }
    
    public float calcDriveAccessUtility(TransitDriveAccessDMU driveDmu, int pMgra, int pTaz, boolean myTrace, Logger myLogger)
    {
    	float util = (float)driveAccessUEC.solve(index, driveDmu, null)[0];

        // logging
        if (myTrace) {
        	driveAccessUEC.logAnswersArray(myLogger, "Drive from Orig Taz=" + pTaz + " to stops Utility Piece");
        }
        return(util);
    }
    
    public float calcDriveAccessRatioDisutility(TransitDriveAccessDMU driveDmu, int pMgra, int pTaz, float origDestDistance, boolean myTrace, Logger myLogger){
    	driveDmu.setOrigDestDistance(origDestDistance);
    	float util = (float)driveAccDisutilityUEC.solve(index, driveDmu, null)[0];
        // logging
        if (myTrace) {
        	driveAccDisutilityUEC.logAnswersArray(myLogger, "Drive from Orig Taz=" + pTaz + ", to stops Drive Ratio Disutility Piece");
    }
        return(util);
    }
    
    public float calcWalkEgressUtility(TransitWalkAccessDMU walkDmu, int aMgra, int timePeriod, boolean myTrace, Logger myLogger)
    {
    	double aWalkTime = mgraManager.getAMgraFromStopsWalkTime(aMgra, timePeriod);        
 
    	if(aWalkTime==0){
    		//myLogger.info("Walk time from stops to mgra "+aMgra+" is 0; setting walk egress utility to "+NA);
    		return NA;
    	}

    	walkDmu.setStopsMgraWalkTime(aWalkTime);
        float util = (float)walkEgressUEC.solve(index, walkDmu, null)[0];

        // logging
        if (myTrace) {
        	walkEgressUEC.logAnswersArray(myLogger, "Walk from stops to Dest Mgra=" + aMgra + " Utility Piece");
        }    
        return(util);
    }
    
    public float calcDriveEgressUtility(TransitDriveAccessDMU driveDmu, int aTaz, int aMgra, boolean myTrace, Logger myLogger)
    {
    	float util = (float)driveEgressUEC.solve(index, driveDmu, null)[0];

        // logging
        if (myTrace) {
        	driveEgressUEC.logAnswersArray(myLogger, "Drive from stops to Dest Taz=" + aTaz + " Utility Piece");
        }
        return(util);
    }
    
    /**
     * Calculate the drive transit disutility on the egress end for inbound trips.
     * 
     * @param driveDmu
     * @param aMgra  destination MGRA
     * @param aTaz   destination TAZ of trip
     * @param accMode
     * @param myTrace
     * @param myLogger
     * @return
     */
    public float calcDriveEgressRatioDisutility(TransitDriveAccessDMU driveDmu, int aMgra, int aTaz, float origDestDistance, boolean myTrace, Logger myLogger)
    {
    	driveDmu.setOrigDestDistance(origDestDistance);
    	float util = (float)driveEgrDisutilityUEC.solve(index, driveDmu, null)[0];
        // logging
        if (myTrace) {
        	driveEgrDisutilityUEC.logAnswersArray(myLogger, "Drive from stops to Dest Taz=" + aTaz + " Drive Ratio Disutility Piece");
        }
        return(util);
    }
    
    public float calcUtilitiesForTazPair(TransitWalkAccessDMU walkDmu, int period, int accessEgressMode, int pTaz, int aTaz, int origMgra, int destMgra, boolean myTrace, Logger myLogger) {
   	
        // set up the index and dmu objects
        index.setOriginZone(pTaz);
        index.setDestZone(aTaz);
        walkDmu.setTOD(period);
        walkDmu.setAccessEgress(accessEgressMode);

        // solve
        float util = (float)tazToTazUEC.solve(index, walkDmu, null)[0];  
        
        // logging
        if (myTrace) {
        	tazToTazUEC.logAnswersArray(myLogger, " TAZ-TAZ Utilities From Orig pTaz=" + pTaz + " (Origin MAZ:" + origMgra +") " +  " to Dest aTaz=" + aTaz + " (Dest MAZ:" + destMgra +") " + " Utility Piece");
            tazToTazUEC.logResultsArray(myLogger, pTaz, aTaz);
        }
        return(util);
    }

    
    public float calcPathUtility(TransitWalkAccessDMU walkDmu, TransitDriveAccessDMU driveDmu, int accEgr, int period, int origMgra, int pTaz, int aTaz, int destMgra, boolean myTrace, Logger myLogger, float odDistance) {
    	
    	float accUtil    =NA;
        float egrUtil    =NA;
        float tazTazUtil =NA;
        float accDisutil =0f;
        float egrDisutil =0f;
        
    	if(accEgr==WTW) {
    		accUtil = calcWalkAccessUtility(walkDmu, origMgra, period, myTrace, myLogger);
            egrUtil = calcWalkEgressUtility(walkDmu, destMgra, period, myTrace, myLogger);
            tazTazUtil = calcUtilitiesForTazPair(walkDmu, period, WTW, pTaz, aTaz, origMgra, destMgra, myTrace, myLogger);
    	} else if(accEgr==WTP || accEgr==WTK) {
    		driveDmu.setAccessEgress(accEgr);
    		accUtil = calcWalkAccessUtility(walkDmu, origMgra, pTaz, myTrace, myLogger);
    		egrUtil = calcDriveEgressUtility(driveDmu, aTaz, destMgra, myTrace, myLogger);
    		egrDisutil = calcDriveEgressRatioDisutility(driveDmu, destMgra,aTaz, odDistance, myTrace, myLogger);
    		tazTazUtil = calcUtilitiesForTazPair(walkDmu, period, accEgr, pTaz, aTaz, origMgra, destMgra, myTrace, myLogger);
    	} else if(accEgr==PTW || accEgr==KTW) {
    		driveDmu.setAccessEgress(accEgr);
    		accUtil = calcDriveAccessUtility(driveDmu, origMgra, pTaz, myTrace, myLogger);
       		accDisutil = calcDriveAccessRatioDisutility(driveDmu, origMgra, pTaz, odDistance, myTrace, myLogger);
    		egrUtil = calcWalkEgressUtility(walkDmu, aTaz, destMgra, myTrace, myLogger);
    		tazTazUtil = calcUtilitiesForTazPair(walkDmu, period, accEgr, pTaz, aTaz, origMgra, destMgra, myTrace, myLogger);
    	}
        return(accUtil + tazTazUtil + egrUtil + accDisutil + egrDisutil);
    }
    
    /**
     * Calculate utilities for the taz pairs using person specific attributes.
     * 
     * @param int pTaz Origin TAZ
     * @param int aTaz Destination TAZ
     * @param TransitWalkAccessDMU walkDmu
     * @param TransitDriveAccessDMU driveDmu
     * @param Modes.AccessMode accMode
     * @param origMgra Origin MGRA
     * @param workMgra Destination MGRA
     * @param departPeriod Departure time period - 1 = AM period, 2 = PM period, 3 =OffPeak period
     * @param debug boolean flag to indicate if debugging reports should be logged
     * @param logger Logger to which debugging reports should be logged if debug is true
     * @return double transit utility
     */
    public double calcPersonSpecificUtilities(int pTaz, int aTaz, TransitWalkAccessDMU walkDmu, TransitDriveAccessDMU driveDmu, int accMode, int origMgra, int destMgra, int departPeriod, boolean debug, Logger myLogger, float odDistance)
    {

        String separator = "";
        String header = "";
        if (debug)
        {
        	myLogger.info("");
        	myLogger.info("");
            header = accMode + " person specific utility info for origMgra=" + origMgra
                    + ", destMgra=" + destMgra + ", period index=" + departPeriod
                    + ", period label=" + ModelStructure.SKIM_PERIOD_STRINGS[departPeriod];
            for (int i = 0; i < header.length(); i++)
                separator += "^";

            myLogger.info("");
            myLogger.info(separator);
            myLogger.info("Calculating " + header);
        }

        //re-calculate utilities
        double utility =  calcPathUtility(walkDmu, driveDmu, accMode, departPeriod, origMgra, pTaz, aTaz, destMgra, debug, myLogger, odDistance);
        
        // log the utilities and taz pairs
        if (debug)
        {
        	myLogger.info("");
        	myLogger.info(separator);
        	myLogger.info(header);
        	myLogger.info("Final Person Specific Best Utilities:");
        	myLogger.info("Utility, ITaz, JTaz");
            myLogger.info(utility + "," + pTaz + "," + aTaz);
            myLogger.info(separator);
        }
        return utility;
    }
    

    public void setTrace(boolean myTrace)
    {
        tracer.setTrace(myTrace);
    }

    /**
     * Trace calculations for a zone pair.
     * 
     * @param itaz
     * @param jtaz
     * @return true if zone pair should be traced, otherwise false
     */
    public boolean isTraceZonePair(int itaz, int jtaz)
    {
        if (tracer.isTraceOn()) {
            return tracer.isTraceZonePair(itaz, jtaz);
        } else {
            return false;
        }
    }
    

    /**
     * Create the UEC for the main transit portion of the utility.
     * 
     * @param uecSpreadsheet The .xls workbook with the model specification.
     * @param modelSheet The sheet with model specifications.
     * @param dataSheet The sheet with the data specifications.
     * @param rb A resource bundle with the path to the skims "skims.path"
     * @param dmu The DMU class for this UEC.
     */
    public UtilityExpressionCalculator createUEC(File uecSpreadsheet, int modelSheet,
            int dataSheet, HashMap<String, String> rbMap, VariableTable dmu)
    {
        return new UtilityExpressionCalculator(uecSpreadsheet, modelSheet, dataSheet, rbMap, dmu);
    }


	public float getNestingCoefficient() {
		return nestingCoefficient;
	}



	public void setNestingCoefficient(float nestingCoefficient) {
		this.nestingCoefficient = nestingCoefficient;
	}



	public UtilityExpressionCalculator getTazToTazUEC() {
		return tazToTazUEC;
	}
	
    public static float[][] readTransitFareDiscounts(String fileName)
    {

        File discountFile = new File(fileName);

        // read in the csv table
        TableDataSet discountTable;
        try
        {
            OLD_CSVFileReader reader = new OLD_CSVFileReader();
            reader.setDelimSet("," + reader.getDelimSet());
            discountTable = reader.readFile(discountFile);

        } catch (Exception e)
        {
           throw new RuntimeException();
        }
        
        int ptypes=8;
        int modes=6;
        
        //initialize array to 1 in case the fare is missing from file for a given mode and ptype combo
        float fareDiscounts[][] = new float[modes][];
        for(int i = 0; i< modes;++i) {
        	fareDiscounts[i]=new float[ptypes];
        	for(int j=0;j<ptypes;++j)
        		fareDiscounts[i][j]=1;
        }
        
        for(int row=1;row<=discountTable.getRowCount();++row) {
 
        	int mode = (int) discountTable.getValueAt(row,"mode");
        	int ptype = (int) discountTable.getValueAt(row, "ptype");
        	float discount = discountTable.getValueAt(row, "mean_discount");
        	
        	fareDiscounts[mode-1][ptype-1]=discount;
        }
 
        return fareDiscounts;
 
    }
    
    public float[][] getTransitFareDiscounts(){
    	
    	return fareDiscounts;
    }
   
}
