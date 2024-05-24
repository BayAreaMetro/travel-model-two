package com.pb.mtctm2.abm.accessibilities;

import com.pb.common.calculator.IndexValues;
import com.pb.common.calculator.MatrixDataServerIf;
import com.pb.common.util.ResourceUtil;
import com.pb.mtctm2.abm.ctramp.CtrampApplication;
import com.pb.common.calculator.MatrixDataManager;
import com.pb.mtctm2.abm.ctramp.MatrixDataServer;
import com.pb.mtctm2.abm.ctramp.MatrixDataServerRmi;
import com.pb.mtctm2.abm.ctramp.McLogsumsCalculator;
import com.pb.mtctm2.abm.ctramp.MgraDataManager;
import com.pb.mtctm2.abm.ctramp.TazDataManager;
import com.pb.mtctm2.abm.ctramp.ModelStructure;
import com.pb.mtctm2.abm.ctramp.TransitDriveAccessDMU;
import com.pb.mtctm2.abm.ctramp.Util;
import com.pb.common.newmodel.UtilityExpressionCalculator;

import java.io.File;
import java.io.Serializable;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.ResourceBundle;

import org.apache.log4j.Logger;

import com.pb.mtctm2.abm.accessibilities.DriveTransitWalkSkimsCalculator;
import com.pb.mtctm2.abm.ctramp.Modes;

/**
 * This class is used to return drive-transit-walk skim values for MGRA pairs
 * associated with estimation data file records.
 * 
 * @author Jim Hicks
 * @version March, 2010
 */
public class DriveTransitWalkSkimsCalculator
        implements Serializable
{

    private transient Logger                        primaryLogger       = Logger.getLogger(DriveTransitWalkSkimsCalculator.class);;

    private static final int              EA                            = ModelStructure.EA_SKIM_PERIOD_INDEX;
    private static final int              AM                            = ModelStructure.AM_SKIM_PERIOD_INDEX;
    private static final int              MD                            = ModelStructure.MD_SKIM_PERIOD_INDEX;
    private static final int              PM                            = ModelStructure.PM_SKIM_PERIOD_INDEX;
    private static final int              EV                            = ModelStructure.EV_SKIM_PERIOD_INDEX;
    private static final int              NUM_PERIODS                   = ModelStructure.SKIM_PERIOD_STRINGS.length;
    private static final String[]         PERIODS                       = ModelStructure.SKIM_PERIOD_STRINGS;

    private static final int              ACCESS_TIME_INDEX             = 0;
    private static final int              EGRESS_TIME_INDEX             = 1;
    private static final int              NA                            = -999;

    private int[]                         NUM_SKIMS;
    private double[]                      defaultSkims;
    
    // declare UEC object
    private UtilityExpressionCalculator   driveWalkSkimUEC;
    private IndexValues                   iv;

    // The simple auto skims UEC does not use any DMU variables
    private TransitDriveAccessDMU         dmu                           = new TransitDriveAccessDMU();                             // DMU
    // for
    // this
    // UEC

    private TazDataManager                tazManager;
    private int                           maxTaz;

    // skim values array for
    // depart skim period(am, pm, op),
    // and Taz-Taz pair.
    private double[][][][] storedDepartPeriodTazTazSkims;

    private BestTransitPathCalculator     bestPathUEC;

    private MatrixDataServerIf            ms;

    public DriveTransitWalkSkimsCalculator(HashMap<String, String> rbMap)
    {
    	tazManager = TazDataManager.getInstance();
        maxTaz = tazManager.getMaxTaz();
    }

    public void setup(HashMap<String, String> rbMap, Logger logger,
            BestTransitPathCalculator myBestPathUEC)
    {

        primaryLogger = logger;

        // set the best transit path utility UECs
        bestPathUEC = myBestPathUEC;

        // Create the skim UECs
        int dataPage = Util.getIntegerValueFromPropertyMap(rbMap,"skim.drive.transit.walk.data.page");
        int skimPage = Util.getIntegerValueFromPropertyMap(rbMap,"skim.drive.transit.walk.skim.page");
        int dtwNumSkims = Util.getIntegerValueFromPropertyMap(rbMap, "skim.drive.transit.walk.skims");
        String uecPath = Util.getStringValueFromPropertyMap(rbMap, CtrampApplication.PROPERTIES_UEC_PATH);
        String uecFileName = Paths.get(uecPath,Util.getStringValueFromPropertyMap(rbMap, "skim.drive.transit.walk.uec.file")).toString();
        File uecFile = new File(uecFileName);
        driveWalkSkimUEC = new UtilityExpressionCalculator(uecFile, skimPage, dataPage, rbMap, dmu);

        //setup index values
        iv = new IndexValues();
        
        //setup default skim values
        defaultSkims = new double[dtwNumSkims];
        for (int j = 0; j < dtwNumSkims; j++) {
          defaultSkims[j] = NA;
        }
        
        // point the stored Array of skims: by Prem or Local, DepartPeriod, O taz, D taz, skim values[] to a shared data store
        StoredTransitSkimData storedDataObject = StoredTransitSkimData.getInstance(NUM_PERIODS, maxTaz );
        storedDepartPeriodTazTazSkims = storedDataObject.getStoredDtwDepartPeriodTazTazSkims();
        
    }

 

    /**
     * Return the array of drive-transit-walk skims for the ride mode, origin TAz,
     * destination TAZ, and departure time period.
     * 
     * @param set for set source skims
     * @param origTaz Origin TAZ for the MGRA pair
     * @param workTaz Destination TAZ for the MGRA pair
     * @param departPeriod Departure time period - 1 = AM period, 2 = PM period, 3 =
     *            OffPeak period
     * @return Array of 55 skim values for the MGRA pair and departure period
     */
    public double[] getDriveTransitWalkSkims(double aWalkTime, int origTaz, int destTaz,
            int departPeriod, boolean debug)
    {

        dmu.setMgraStopsWalkTime(aWalkTime);

        iv.setOriginZone(origTaz);
        iv.setDestZone(destTaz);

        // allocate space for the origin tap if it hasn't been allocated already
        if (storedDepartPeriodTazTazSkims[departPeriod][origTaz] == null)
        {
            storedDepartPeriodTazTazSkims[departPeriod][origTaz] = new double[maxTaz + 1][];
        }

        // if the destTaz skims are not already stored, calculate them and store
        // them
        if (storedDepartPeriodTazTazSkims[departPeriod][origTaz][destTaz] == null)
        {
        	dmu.setTOD(departPeriod);
            double[] results = driveWalkSkimUEC.solve(iv, dmu, null);
            if (debug)
            	driveWalkSkimUEC.logAnswersArray(primaryLogger, "Drive-Walk Skims");
            storedDepartPeriodTazTazSkims[departPeriod][origTaz][destTaz] = results;
        }

        try {
            storedDepartPeriodTazTazSkims[departPeriod][origTaz][destTaz][EGRESS_TIME_INDEX] = aWalkTime;
        }
        catch ( Exception e ) {
            primaryLogger.error ("departPeriod=" + departPeriod + ", origTaz=" + origTaz + ", destTaz=" + destTaz + ", aWalkTime=" + aWalkTime);
            primaryLogger.error ("exception setting drive-transit-walk walk egress time in stored array.", e);
        }
        return storedDepartPeriodTazTazSkims[departPeriod][origTaz][destTaz];
        

    }


    public double[] getNullTransitSkims()
    {
    	return defaultSkims;
    }

    /**
     * Start the matrix server
     * 
     * @param rb is a ResourceBundle for the properties file for this application
     */
    private void startMatrixServer(ResourceBundle rb)
    {

        primaryLogger.info("");
        primaryLogger.info("");
        String serverAddress = rb.getString("RunModel.MatrixServerAddress");
        int serverPort = new Integer(rb.getString("RunModel.MatrixServerPort"));
        primaryLogger.info("connecting to matrix server " + serverAddress + ":" + serverPort);

        try
        {

            MatrixDataManager mdm = MatrixDataManager.getInstance();
            ms = new MatrixDataServerRmi(serverAddress, serverPort, MatrixDataServer.MATRIX_DATA_SERVER_NAME);
            ms.testRemote(Thread.currentThread().getName());
            mdm.setMatrixDataServerObject(ms);

        } catch (Exception e)
        {

            primaryLogger.error(String
                    .format("exception caught running ctramp model components -- exiting."), e);
            throw new RuntimeException();

        }

    }

    /**
     * log a report of the final skim values for the MGRA odt
     * 
     * @param odt is an int[] with the first element the origin mgra and the second
     *            element the dest mgra and third element the departure period index
     * @param bestTapPairs is an int[][] of TAP values with the first dimesion the
     *            ride mode and second dimension a 2 element array with best orig and
     *            dest TAP
     * @param returnedSkims is a double[][] of skim values with the first dimesion
     *            the ride mode indices and second dimention the skim categories
     */
    public void logReturnedSkims(int[] odt, int[][] bestTapPairs, double[][] skims)
    {

        Modes.TransitMode[] mode = Modes.TransitMode.values();

        int nrows = skims.length;
        int ncols = 0;
        for (int i = 0; i < nrows; i++)
            if (skims[i].length > ncols) ncols = skims[i].length;

        String separator = "";
        String header = "";

        primaryLogger.info("");
        primaryLogger.info("");
        header = "Returned drive-transit-walk skim value tables for origMgra=" + odt[0]
                + ", destMgra=" + odt[1] + ", period index=" + odt[2] + ", period label="
                + PERIODS[odt[2]];
        for (int i = 0; i < header.length(); i++)
            separator += "^";

        primaryLogger.info(separator);
        primaryLogger.info(header);
        primaryLogger.info("");

        String modeHeading = String.format("%-12s      %3s      ", "RideMode:", mode[0]);
        for (int i = 1; i < bestTapPairs.length; i++)
            modeHeading += String.format("      %3s      ", mode[i]);
        primaryLogger.info(modeHeading);

        String[] logValues = {"NA", "NA"};
        if (bestTapPairs[0] != null)
        {
            logValues[0] = String.valueOf(bestTapPairs[0][0]);
            logValues[1] = String.valueOf(bestTapPairs[0][1]);
        }
        String tapHeading = String.format("%-12s   %4s-%4s   ", "TAP Pair:", logValues[0],
                logValues[1]);

        for (int i = 1; i < bestTapPairs.length; i++)
        {
            if (bestTapPairs[i] != null)
            {
                logValues[0] = String.valueOf(bestTapPairs[i][0]);
                logValues[1] = String.valueOf(bestTapPairs[i][1]);
            } else
            {
                logValues[0] = "NA";
                logValues[1] = "NA";
            }
            tapHeading += String.format("   %4s-%4s   ", logValues[0], logValues[1]);
        }
        primaryLogger.info(tapHeading);

        String underLine = String.format("%-12s   %9s   ", "---------", "---------");
        for (int i = 1; i < bestTapPairs.length; i++)
            underLine += String.format("   %9s   ", "---------");
        primaryLogger.info(underLine);

        for (int j = 0; j < ncols; j++)
        {
            String tableRecord = "";
            if (j < skims[0].length) tableRecord = String.format("%-12d %12.5f  ", j + 1,
                    skims[0][j]);
            else tableRecord = String.format("%-12d %12s  ", j + 1, "");
            for (int i = 1; i < bestTapPairs.length; i++)
            {
                if (j < skims[i].length) tableRecord += String.format(" %12.5f  ", skims[i][j]);
                else tableRecord += String.format(" %12s  ", "");
            }
            primaryLogger.info(tableRecord);
        }

        primaryLogger.info("");
        primaryLogger.info(separator);
    }

 


}
