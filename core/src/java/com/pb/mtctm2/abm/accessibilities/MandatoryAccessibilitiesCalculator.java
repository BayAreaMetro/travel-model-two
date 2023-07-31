package com.pb.mtctm2.abm.accessibilities;

import com.pb.common.util.Tracer;
import com.pb.common.calculator.IndexValues;
import com.pb.mtctm2.abm.ctramp.CtrampApplication;
import com.pb.mtctm2.abm.ctramp.MgraDataManager;
import com.pb.mtctm2.abm.ctramp.ModelStructure;
import com.pb.mtctm2.abm.ctramp.TransitDriveAccessDMU;
import com.pb.mtctm2.abm.ctramp.TransitWalkAccessDMU;
import com.pb.mtctm2.abm.ctramp.Util;
import com.pb.common.newmodel.UtilityExpressionCalculator;

import java.io.File;
import java.io.Serializable;
import java.nio.file.Paths;
import java.util.HashMap;

import org.apache.log4j.Logger;

import com.pb.mtctm2.abm.accessibilities.NonTransitUtilities;
import com.pb.mtctm2.abm.ctramp.Modes;
import com.pb.mtctm2.abm.ctramp.TazDataManager;

/**
 * This class builds accessibility components for all modes.
 * 
 * @author Joel Freedman
 * @version May, 2009
 */
public class MandatoryAccessibilitiesCalculator
        implements Serializable
{

    protected transient Logger             logger   = Logger.getLogger(MandatoryAccessibilitiesCalculator.class);

    private static final int MIN_EXP_FUNCTION_ARGUMENT = -500;

    private static final int PEAK_NONTOLL_SOV_TIME_INDEX = 0;
    private static final int PEAK_NONTOLL_SOV_DIST_INDEX = 1;
    private static final int OFFPEAK_NONTOLL_SOV_TIME_INDEX = 2;
    private static final int OFFPEAK_NONTOLL_SOV_DIST_INDEX = 3;
    
    public static final int                   WTW = 0;
    public static final int                   WTD = 1;
    public static final int                   DTW = 2;
    
    private UtilityExpressionCalculator autoSkimUEC;
    private UtilityExpressionCalculator bestWalkTransitUEC;
    private UtilityExpressionCalculator bestDriveTransitUEC;
    private UtilityExpressionCalculator autoLogsumUEC;
    private UtilityExpressionCalculator transitLogsumUEC;

    private MandatoryAccessibilitiesDMU dmu;
    private IndexValues                 iv;

    private NonTransitUtilities         ntUtilities;

    private MgraDataManager             mgraManager;
    private TazDataManager              tazManager;
    
    private AutoAndNonMotorizedSkimsCalculator anm;

    // auto sufficiency (0 autos, autos<adults, autos>=adults),
    // and mode (SOV,HOV,Walk-Transit,Non-Motorized)
    private double[][]                  expConstants;
    
    HashMap<String, String> rbMap;

    private String[] accNames = {
            "SovTime", // 0
            "SovDist", // 1
            "WTTime", // 2
            "DTTime", // 3
            "SovUtility", // 4
            "WTUtility", // 5
            "AutoLogsum", // 6
            "WTLogsum", // 7
            "TransitLogsum", // 8
            "WTRailShare", // 9
            "DTRailShare", // 10
            "DTLogsum", // 11
            "HovUtility" // 12
    };

    private BestTransitPathCalculator bestPathCalculator;
   
    public MandatoryAccessibilitiesCalculator(HashMap<String, String> rbMap,
            NonTransitUtilities aNtUtilities, double[][] aExpConstants, BestTransitPathCalculator myBestPathCalculator)
    {

    	this.rbMap = rbMap;
    	
        ntUtilities = aNtUtilities;
        expConstants = aExpConstants;

        // Create the UECs
        String uecFileName = Util.getStringValueFromPropertyMap(rbMap, "acc.mandatory.uec.file");
        int dataPage = Util.getIntegerValueFromPropertyMap(rbMap, "acc.mandatory.data.page");
        int autoSkimPage = Util.getIntegerValueFromPropertyMap(rbMap, "acc.mandatory.auto.page");
        int bestWalkTransitPage = Util.getIntegerValueFromPropertyMap(rbMap, "acc.mandatory.bestWalkTransit.page");
        int bestDriveTransitPage = Util.getIntegerValueFromPropertyMap(rbMap, "acc.mandatory.bestDriveTransit.page");
        int autoLogsumPage = Util.getIntegerValueFromPropertyMap(rbMap, "acc.mandatory.autoLogsum.page");
        int transitLogsumPage = Util.getIntegerValueFromPropertyMap(rbMap, "acc.mandatory.transitLogsum.page");


        dmu = new MandatoryAccessibilitiesDMU();

        File uecFile = new File(uecFileName);
        autoSkimUEC = new UtilityExpressionCalculator(uecFile, autoSkimPage, dataPage, rbMap, dmu);
        bestWalkTransitUEC = new UtilityExpressionCalculator(uecFile, bestWalkTransitPage, dataPage, rbMap, dmu);
        bestDriveTransitUEC = new UtilityExpressionCalculator(uecFile, bestDriveTransitPage, dataPage, rbMap, dmu);
        autoLogsumUEC = new UtilityExpressionCalculator(uecFile, autoLogsumPage, dataPage, rbMap, dmu);
        transitLogsumUEC = new UtilityExpressionCalculator(uecFile, transitLogsumPage, dataPage, rbMap, dmu);
        
        iv = new IndexValues();

        tazManager = TazDataManager.getInstance();
        mgraManager = MgraDataManager.getInstance();

        bestPathCalculator = myBestPathCalculator;
      
    }
    

    public double[] calculateWorkerMandatoryAccessibilities(int hhMgra, int workMgra)
    {
        return calculateAccessibilitiesForMgraPair(hhMgra, workMgra, false, null);
    }

    public double[] calculateStudentMandatoryAccessibilities(int hhMgra, int schoolMgra)
    {
        return calculateAccessibilitiesForMgraPair(hhMgra, schoolMgra, false, null);
    }

    /**
     * Calculate the work logsum for the household MGRA and sampled work location
     * MGRA.
     * 
     * @param hhMgra Household MGRA
     * @param workMgra Sampled work MGRA
     * @param autoSufficiency Auto sufficiency category
     * @return Work mode choice logsum
     */
    public double calculateWorkLogsum(int hhMgra, int workMgra, int autoSufficiency, boolean debug, Logger aLogger)
    {

        String separator = "";
        String header = "";
        if (debug)
        {
            aLogger.info("");
            aLogger.info("");
            header = "calculateWorkLogsum() debug info for homeMgra=" + hhMgra + ", workMgra=" + workMgra;
            for (int i = 0; i < header.length(); i++)
                separator += "^";
        }

        double[] accessibilities = calculateAccessibilitiesForMgraPair(hhMgra, workMgra, debug, aLogger);

        double sovUtility = accessibilities[4];
        double hovUtility = accessibilities[12];
        double transitLogsum = accessibilities[8]; // includes both walk and drive access        
        double nmExpUtility = ntUtilities.getNMotorExpUtility(hhMgra, workMgra, NonTransitUtilities.OFFPEAK_PERIOD_INDEX);

        // constrain auto sufficiency to 0,1,2
        autoSufficiency = Math.min(autoSufficiency, 2);

        double utilSum = Math.exp(sovUtility) * expConstants[autoSufficiency][0]
                       + Math.exp(hovUtility) * expConstants[autoSufficiency][1]
                       + Math.exp(transitLogsum) * expConstants[autoSufficiency][2]
                       + nmExpUtility * expConstants[autoSufficiency][3];

        double logsum = Math.log(utilSum);

        if (debug)
        {

            aLogger.info(separator);
            aLogger.info(header);
            aLogger.info(separator);

            aLogger.info("accessibilities array values");
            aLogger.info(String.format("%5s %15s %15s", "i", "accName", "value"));
            aLogger.info(String.format("%5s %15s %15s", "-----", "----------", "----------"));
            for (int i = 0; i < accessibilities.length; i++)
            {
                aLogger.info(String.format("%5d %15s %15.5e", i, accNames[i], accessibilities[i]));
            }

            aLogger.info("");
            aLogger.info("");
            aLogger.info("logsum component values");
            aLogger.info(String.format("autoSufficiency = %d", autoSufficiency));
            aLogger.info(String.format("%-15s = %15.5e, %-18s = %15.5e, %-18s = %15.5e",
                    "sovUtility", sovUtility, "exp(sovUtility)", Math.exp(sovUtility), String
                            .format("expConst suff=%d 0", autoSufficiency),
                    expConstants[autoSufficiency][0]));
            aLogger.info(String.format("%-15s = %15.5e, %-18s = %15.5e, %-18s = %15.5e",
                    "hovUtility", hovUtility, "exp(hovUtility)", Math.exp(hovUtility), String
                            .format("expConst suff=%d 1", autoSufficiency),
                    expConstants[autoSufficiency][1]));
            aLogger.info(String.format("%-15s = %15.5e, %-18s = %15.5e, %-18s = %15.5e",
                    "transitLogsum", transitLogsum, "exp(transitLogsum)", Math.exp(transitLogsum),
                    String.format("expConst suff=%d 2", autoSufficiency),
                    expConstants[autoSufficiency][2]));
            aLogger.info(String.format("%-15s = %15.5e, %-18s = %15.5e", "nmExpUtility",
                    nmExpUtility, String.format("expConst suff=%d 3", autoSufficiency),
                    expConstants[autoSufficiency][3]));
            aLogger.info(String.format("%-15s = %15.5e", "utilSum", utilSum));
            aLogger.info(String.format("%-15s = %15.5e", "logsum", logsum));
            aLogger.info(separator);
        }

        return logsum;
    }

    /**
     * Calculate the school logsum for the household MGRA and sampled school location
     * MGRA.
     * 
     * @param hhMgra Household MGRA
     * @param schoolMgra Sampled work MGRA
     * @param autoSufficiency Auto sufficiency category
     * @param studentType Student type 0=Pre-school (SOV not available) 1=K-8 (SOV
     *            not available) 2=9-12 (Normal car-sufficiency-based logsum)
     *            3=College/university(typical) (Normal car-sufficiency-based logsum)
     *            4=College/university(non-typical) (Normal car-sufficiency-based
     *            logsum)
     * @return School mode choice logsum
     */
    public double calculateSchoolLogsum(int hhMgra, int schoolMgra, int autoSufficiency, int studentType, boolean debug, Logger aLogger)
    {

        String separator = "";
        String header = "";
        if (debug)
        {
            aLogger.info("");
            aLogger.info("");
            header = "calculateSchoolLogsum() debug info for homeMgra=" + hhMgra + ", schoolMgra="
                    + schoolMgra;
            for (int i = 0; i < header.length(); i++)
                separator += "^";
        }

        double[] accessibilities = calculateAccessibilitiesForMgraPair(hhMgra, schoolMgra, debug, aLogger);

        double sovUtility = accessibilities[4];
        double hovUtility = accessibilities[12];
        double transitLogsum = accessibilities[8]; // includes both walk and drive access
        double nmExpUtility = ntUtilities.getNMotorExpUtility(hhMgra, schoolMgra, NonTransitUtilities.OFFPEAK_PERIOD_INDEX);

        // constrain auto sufficiency to 0,1,2
        autoSufficiency = Math.min(autoSufficiency, 2);

        double logsum = Math.exp(hovUtility) * expConstants[autoSufficiency][1]
                      + Math.exp(transitLogsum) * expConstants[autoSufficiency][2]
                      + nmExpUtility * expConstants[autoSufficiency][3];

        // used for debugging
        double logsum1 = logsum;

        if (studentType >= 2)
        {
            logsum = logsum + Math.exp(sovUtility) * expConstants[autoSufficiency][0];
        }

        // used for debugging
        double logsum2 = logsum;

        logsum = Math.log(logsum);

        if (debug)
        {

            aLogger.info(separator);
            aLogger.info(header);
            aLogger.info(separator);

            aLogger.info("accessibilities array values");
            aLogger.info(String.format("%5s %15s %15s", "i", "accName", "value"));
            aLogger.info(String.format("%5s %15s %15s", "-----", "----------", "----------"));
            for (int i = 0; i < accessibilities.length; i++)
            {
                aLogger.info(String.format("%5d %15s %15.5e", i, accNames[i], accessibilities[i]));
            }

            aLogger.info("");
            aLogger.info("");
            aLogger.info("logsum component values");
            aLogger.info(String.format("autoSufficiency = %d", autoSufficiency));
            aLogger.info(String.format("%-15s = %15.5e, %-18s = %15.5e, %-18s = %15.5e",
                    "hovUtility", hovUtility, "exp(hovUtility)", Math.exp(hovUtility),
                    String.format("expConst suff=%d 1", autoSufficiency),
                    expConstants[autoSufficiency][1]));
            aLogger.info(String.format("%-15s = %15.5e, %-18s = %15.5e, %-18s = %15.5e",
                    "transitLogsum", transitLogsum, "exp(transitLogsum)", Math.exp(transitLogsum),
                    String.format("expConst suff=%d 2", autoSufficiency),
                    expConstants[autoSufficiency][2]));
            aLogger.info(String.format("%-15s = %15.5e, %-18s = %15.5e", "nmExpUtility",
                    nmExpUtility, String.format("expConst suff=%d 3", autoSufficiency),
                    expConstants[autoSufficiency][3]));
            aLogger.info(String.format("%s = %15.5e", "utility sum (before adding sovUtility)",
                    logsum1));
            if (studentType >= 2)
            {
                aLogger.info(String.format("studentType = %d", studentType));
                aLogger.info(String.format("%-15s = %15.5e, %-18s = %15.5e, %-18s = %15.5e",
                        "sovUtility", sovUtility, "exp(sovUtility)", Math.exp(sovUtility), String.format("expConst suff=%d 0", autoSufficiency),
                        expConstants[autoSufficiency][0]));
                aLogger.info(String.format("%s = %15.5e", "utility sum (after adding sovUtility)", logsum2));
            } else
            {
                aLogger.info(String.format(
                    "studentType = %d, no additional contribution to utility sum",
                    studentType));
            }
            aLogger.info(String.format("%s = %15.5e, %s = %15.5e", "final utility sum", logsum2,
                "final logsum", logsum));
            aLogger.info(separator);
        }

        return logsum;
    }

    /**
     * Calculate the accessibilities for a given origin and destination mgra
     * 
     * @param oMgra The origin mgra
     * @param dMgra The destination mgra
     * @return An array of accessibilities
     */
    public double[] calculateAccessibilitiesForMgraPair(int oMgra, int dMgra, boolean debug, Logger aLogger)
    {

        double[] accessibilities = new double[accNames.length];
        
        // DMUs for this UEC
        TransitWalkAccessDMU walkDmu = new TransitWalkAccessDMU();
        walkDmu.setTransitFareDiscounts(bestPathCalculator.getTransitFareDiscounts());
        TransitDriveAccessDMU driveDmu = new TransitDriveAccessDMU();

        if (oMgra > 0 && dMgra > 0)
        {

            int oTaz = mgraManager.getTaz(oMgra);
            int dTaz = mgraManager.getTaz(dMgra);
                     
            iv.setOriginZone(oTaz);
            iv.setDestZone(dTaz);

            // sov time and distance
            double[] autoResults = autoSkimUEC.solve(iv, dmu, null);
            if (debug)
                autoSkimUEC.logAnswersArray( aLogger, String.format( "autoSkimUEC:  oMgra=%d, dMgra=%d", oMgra, dMgra ) );

            // autoResults[0] is peak non-toll sov time, autoResults[1] is peak non-toll sov dist 
            // autoResults[2] is off-peak non-toll sov time, autoResults[3] is off-peak non-toll sov dist 
            accessibilities[0] = autoResults[PEAK_NONTOLL_SOV_TIME_INDEX];
            accessibilities[1] = autoResults[PEAK_NONTOLL_SOV_DIST_INDEX];

            float odDistance = (float) autoResults[PEAK_NONTOLL_SOV_DIST_INDEX];
            		
            // pre-calculate the hov, sov, and non-motorized exponentiated utilities for the origin MGRA.
            // the method called returns cached values if they were already calculated.
            ntUtilities.buildUtilitiesForOrigMgraAndPeriod( oMgra, NonTransitUtilities.PEAK_PERIOD_INDEX );
            
            // auto logsum
            double pkSovExpUtility = ntUtilities.getSovExpUtility(oTaz, dTaz, NonTransitUtilities.PEAK_PERIOD_INDEX);
            double pkHovExpUtility = ntUtilities.getHovExpUtility(oTaz, dTaz, NonTransitUtilities.PEAK_PERIOD_INDEX);

            dmu.setSovNestLogsum(-999);
            if (pkSovExpUtility > 0)
            {
                dmu.setSovNestLogsum(Math.log(pkSovExpUtility));
                accessibilities[4] = dmu.getSovNestLogsum();
            }
            dmu.setHovNestLogsum(-999);
            if (pkHovExpUtility > 0)
            {
                dmu.setHovNestLogsum(Math.log(pkHovExpUtility));
                accessibilities[12] = dmu.getHovNestLogsum();
            }

            double[] autoLogsum = autoLogsumUEC.solve(iv, dmu, null);
            if (debug)
                autoLogsumUEC.logAnswersArray(aLogger, String.format(
                        "autoLogsumUEC:  oMgra=%d, dMgra=%d", oMgra, dMgra));
            accessibilities[6] = autoLogsum[0];

            
            //////////////////////////////////////////////////////////////////////////            
            // walk transit
            //////////////////////////////////////////////////////////////////////////
            
            // get the walkTransitWalk utility
            double walkTransitWalkUtility = bestPathCalculator.calcPersonSpecificUtilities(oTaz, dTaz, walkDmu, driveDmu, WTW, oMgra, dMgra, ModelStructure.AM_SKIM_PERIOD_INDEX, debug, logger, odDistance);
            
            // 7 used to be the logsum of N best transit paths
            // now it is just the transit utility between the mgra pair
            if (walkTransitWalkUtility > MIN_EXP_FUNCTION_ARGUMENT)
                accessibilities[7] = walkTransitWalkUtility;
            else
                accessibilities[7] = -999;

            dmu.setWlkNestLogsum(accessibilities[7]);
            
            if (walkTransitWalkUtility > MIN_EXP_FUNCTION_ARGUMENT)
            {
            	// 5 used to be the transit utility between the best tap pair
            	// now it is the same as 7
                accessibilities[5] = walkTransitWalkUtility;

                //set access and egress times
                double mgraStopsWalkTime = mgraManager.getPMgraToStopsWalkTime(oMgra,ModelStructure.AM_SKIM_PERIOD_INDEX);
                dmu.setMgraStopsWalkTime(mgraStopsWalkTime);
                
                double stopsMgraWalkTime = mgraManager.getAMgraFromStopsWalkTime(dMgra, ModelStructure.AM_SKIM_PERIOD_INDEX);
                dmu.setStopsMgraWalkTime(stopsMgraWalkTime);
                
                iv.setOriginZone(oTaz);
                iv.setDestZone(dTaz);
                double[] wlkTransitTimes = bestWalkTransitUEC.solve(iv, dmu, null);
                
                if (debug){
                    bestWalkTransitUEC.logAnswersArray(aLogger, String.format("bestWalkTransitUEC:  oMgra=%d, dMgra=%d", oMgra, dMgra));
                }
                
                accessibilities[2] = wlkTransitTimes[0];
                accessibilities[9] = wlkTransitTimes[1];

            }
            
            //////////////////////////////////////////////////////////////////////////
            // drive transit
            //////////////////////////////////////////////////////////////////////////
            
            // get the drive transit walk utility
            double driveTransitWalkUtility = bestPathCalculator.calcPersonSpecificUtilities(oTaz, dTaz, walkDmu, driveDmu, DTW, oMgra, dMgra, ModelStructure.AM_SKIM_PERIOD_INDEX, debug, logger, odDistance);
            
            // 11 used to be the logsum of N best transit paths
            // now it is just the transit utility between the mgra pair
            if (driveTransitWalkUtility > MIN_EXP_FUNCTION_ARGUMENT)
                accessibilities[11] = driveTransitWalkUtility;
            else
                accessibilities[11] = -999;

            dmu.setDrvNestLogsum(accessibilities[11]);

            if (driveTransitWalkUtility > MIN_EXP_FUNCTION_ARGUMENT)
            {
                //set access and egress times
            	// drive access time is read in from skims
                
                double stopsMgraWalkTime = mgraManager.getAMgraFromStopsWalkTime(dMgra, ModelStructure.AM_SKIM_PERIOD_INDEX);
                dmu.setStopsMgraWalkTime(stopsMgraWalkTime);

                iv.setOriginZone(oTaz);
                iv.setDestZone(dTaz);
                double[] drvTransitTimes = bestDriveTransitUEC.solve(iv, dmu, null);
                
                if (debug){
                    bestDriveTransitUEC.logAnswersArray(aLogger, String.format("bestDriveTransitUEC:  oMgra=%d, dMgra=%d", oMgra, dMgra));
                }
                
                accessibilities[3] = drvTransitTimes[0];
                accessibilities[10] = drvTransitTimes[1];

            }
            
            
            double[] transitLogsumResults = transitLogsumUEC.solve(iv, dmu, null);
            if (debug){
                transitLogsumUEC.logAnswersArray(aLogger, String.format("transitLogsumUEC:  oMgra=%d, dMgra=%d", oMgra, dMgra));
            }
            
            // transit logsum  results array has only 1 alternative, so result is in 0 element.
            accessibilities[8] = transitLogsumResults[0];
            
        } // end if oMgra and dMgra > 0

        return accessibilities;
    }

    /**
     * Calculate auto skims for a given origin to all destination mgras, and return
     * auto distance.
     * 
     * @param oMgra The origin mgra
     * @return An array of distances
     */
    public double[] calculateDistancesForAllMgras(int oMgra)
    {

        double[] distances = new double[mgraManager.getMaxMgra() + 1];

        int oTaz = mgraManager.getTaz(oMgra);
        iv.setOriginZone(oTaz);

        for (int i = 0; i < mgraManager.getMgras().size(); i++)
        {

        	int dTaz = mgraManager.getTaz(mgraManager.getMgras().get(i));
            iv.setDestZone(dTaz);

            // sov distance
            double[] autoResults = autoSkimUEC.solve(iv, dmu, null);
            distances[dTaz] = autoResults[PEAK_NONTOLL_SOV_DIST_INDEX];

        }

        return distances;
    }

    /**
     * Calculate auto skims for a given origin to all destination mgras, and return
     * auto distance.
     * 
     * @param oMgra The origin mgra
     * @return An array of distances
     */
    public double[] calculateOffPeakDistancesForAllMgras(int oMgra)
    {

        double[] distances = new double[mgraManager.getMaxMgra() + 1];

        int oTaz = mgraManager.getTaz(oMgra);
        iv.setOriginZone(oTaz);

        for (int i = 0; i < mgraManager.getMgras().size(); i++)
        {

            int dTaz = mgraManager.getTaz(mgraManager.getMgras().get(i));
            iv.setDestZone(dTaz);

            // sov distance
            double[] autoResults = autoSkimUEC.solve(iv, dmu, null);
            distances[dTaz] = autoResults[OFFPEAK_NONTOLL_SOV_DIST_INDEX];

        }

        return distances;
    }

}
