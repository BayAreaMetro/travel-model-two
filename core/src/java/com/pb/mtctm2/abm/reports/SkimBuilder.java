package com.pb.mtctm2.abm.reports;

import com.pb.common.calculator.MatrixDataManager;
import com.pb.common.calculator.MatrixDataServerIf;

import org.apache.log4j.Logger;

import com.pb.mtctm2.abm.accessibilities.*;
import com.pb.mtctm2.abm.application.SandagModelStructure;
import com.pb.mtctm2.abm.ctramp.MatrixDataServer;
import com.pb.mtctm2.abm.ctramp.MatrixDataServerRmi;
import com.pb.mtctm2.abm.ctramp.ModelStructure;
import com.pb.mtctm2.abm.ctramp.TapDataManager;
import com.pb.mtctm2.abm.ctramp.MgraDataManager;
import com.pb.mtctm2.abm.ctramp.Modes;
import com.pb.mtctm2.abm.ctramp.TazDataManager;
import com.pb.mtctm2.abm.ctramp.Util;

import java.io.File;
import java.util.*;

/**
 * The {@code SkimBuilder} ...
 *
 * @author crf
 *         Started 10/17/12 9:12 AM
 * @revised 5/6/2013 for SERPM (ymm)
 * @revised 5/6/2015 for MTC (ymm)
 * 
 *	1	Auto SOV (Free)
	2	Auto SOV (Pay)
	3	Auto 2 Person (GP)
	4	Auto 2 Person (Free)
	5	Auto 2 Person (Pay)
	6	Auto 3+ Person (GP)
	7	Auto 3+ Person (Free)
	8	Auto 3+ Person (Pay)
	9	Walk
	10	Bike/Moped
	11	Walk-LB
	12	Walk-EB
	13	Walk-FR
	14	Walk-HR
	15	Walk-LRT
	16	Walk-CR
	17	PNR-LB
	18	PNR-EB
	19	PNR-FR
	20	PNR-HR
	21	PNR-LRT
	22	PNR-CR
	23	KNR-LB
	24	KNR-EB
	25	KNR-FR
	26	KNR-HR
	27	KNR-LRT
	28	KNR-CR
	29	SCHLBS
 */
public class SkimBuilder {
    private final static Logger logger = Logger.getLogger(SkimBuilder.class);

    public static final int WALK_TIME_INDEX = 0;
    public static final int BIKE_TIME_INDEX = 0;

    public static final int DA_TIME_INDEX = 0;
    public static final int DA_FF_TIME_INDEX = 1;
    public static final int DA_DIST_INDEX = 2;
    public static final int DA_BTOLL_INDEX = 3;
    
    public static final int DA_TOLL_TIME_INDEX = 4;
    public static final int DA_TOLL_FF_TIME_INDEX = 5;
    public static final int DA_TOLL_DIST_INDEX = 6;
    public static final int DA_TOLL_TOLL_INDEX = 7;
    public static final int DA_TOLL_TOLLDIST_INDEX = 8;
    public static final int DA_TOLL_BTOLL_INDEX = 9;
    
    public static final int HOV_TIME_INDEX = 10;
    public static final int HOV_FF_TIME_INDEX = 11;
    public static final int HOV_DIST_INDEX = 12;
    public static final int HOV_HOVDIST_INDEX = 13;
    public static final int HOV_BTOLL_INDEX = 14;
    
    public static final int HOV3_TIME_INDEX = 15;
    public static final int HOV3_FF_TIME_INDEX = 16;
    public static final int HOV3_DIST_INDEX = 17;
    public static final int HOV3_HOVDIST_INDEX = 18;
    public static final int HOV3_BTOLL_INDEX = 19;
    
    public static final int HOV_TOLL_TIME_INDEX = 20;
    public static final int HOV_TOLL_FF_TIME_INDEX = 21;
    public static final int HOV_TOLL_DIST_INDEX = 22;
    public static final int HOV_TOLL_TOLL_INDEX = 23;
    public static final int HOV_TOLL_HOV_DIST_INDEX = 24;
    public static final int HOV_TOLL_BTOLL_INDEX = 25;
    
    public static final int HOV3_TOLL_TIME_INDEX = 26;
    public static final int HOV3_TOLL_FF_TIME_INDEX = 27;
    public static final int HOV3_TOLL_DIST_INDEX = 28;
    public static final int HOV3_TOLL_TOLL_INDEX = 29;
    public static final int HOV3_TOLL_HOV_DIST_INDEX = 30;
    public static final int HOV3_TOLL_BTOLL_INDEX = 31;

    public static final int TRANSIT_SET_ACCESS_TIME_INDEX = 0;
    public static final int TRANSIT_SET_EGRESS_TIME_INDEX = 1;
    public static final int TRANSIT_SET_AUX_WALK_TIME_INDEX = 2;
    public static final int TRANSIT_SET_LOCAL_BUS_TIME_INDEX = 3;
    public static final int TRANSIT_SET_EXPRESS_BUS_TIME_INDEX = 4;
    public static final int TRANSIT_SET_HR_TIME_INDEX = 5;
    public static final int TRANSIT_SET_FR_TIME_INDEX = 6;
    public static final int TRANSIT_SET_LRT_TIME_INDEX = 7;
    public static final int TRANSIT_SET_CR_TIME_INDEX = 8;
    public static final int TRANSIT_SET_FIRST_WAIT_TIME_INDEX = 9;
    public static final int TRANSIT_SET_TRANSFER_WAIT_TIME_INDEX = 10;
    public static final int TRANSIT_SET_FARE_INDEX = 11;
    public static final int TRANSIT_SET_MAIN_MODE_INDEX = 12;
    public static final int TRANSIT_SET_XFERS_INDEX = 13;

    private final TapDataManager tapManager;
    private final TazDataManager tazManager;
    private final MgraDataManager mgraManager;
    private final AutoTazSkimsCalculator tazDistanceCalculator;
    private final AutoAndNonMotorizedSkimsCalculator autoNonMotSkims;
    private final WalkTransitWalkSkimsCalculator wtw;
    private final WalkTransitDriveSkimsCalculator wtd;
    private final DriveTransitWalkSkimsCalculator dtw;
    
    private float DEFAULT_BIKE_SPEED;//get values from autoNonMotSkims
    private float DEFAULT_WALK_SPEED;//get values from autoNonMotSkims

    private final String 			FUEL_COST_PROPERTY          = "aoc.fuel";
    private final String 			MAINTENANCE_COST_PROPERTY = "aoc.maintenance";
    private float autoOperatingCost;

    public SkimBuilder(Properties properties) {

        HashMap<String,String> rbMap = new HashMap<String,String>((Map<String,String>) (Map) properties);
        startMatrixServer(properties);

        tapManager = TapDataManager.getInstance(rbMap);
        tazManager = TazDataManager.getInstance(rbMap);
        mgraManager = MgraDataManager.getInstance(rbMap);
        tazDistanceCalculator = new AutoTazSkimsCalculator(rbMap);
        tazDistanceCalculator.computeTazDistanceArrays();
        autoNonMotSkims = new AutoAndNonMotorizedSkimsCalculator(rbMap);
        autoNonMotSkims.setTazDistanceSkimArrays(tazDistanceCalculator.getStoredFromTazToAllTazsDistanceSkims(),tazDistanceCalculator.getStoredToTazFromAllTazsDistanceSkims());

        DEFAULT_BIKE_SPEED = (float) autoNonMotSkims.getBikeSpeed();
        DEFAULT_WALK_SPEED = (float) autoNonMotSkims.getWalkSpeed();
        
        BestTransitPathCalculator bestPathUEC = new BestTransitPathCalculator(rbMap);
        wtw = new WalkTransitWalkSkimsCalculator(rbMap);
        wtw.setup(rbMap,logger, bestPathUEC);
        wtd = new WalkTransitDriveSkimsCalculator(rbMap);
        wtd.setup(rbMap,logger, bestPathUEC);
        dtw = new DriveTransitWalkSkimsCalculator(rbMap);
        dtw.setup(rbMap,logger, bestPathUEC);

        float fuelCost = new Float(properties.getProperty(FUEL_COST_PROPERTY));
        float mainCost = new Float(properties.getProperty(MAINTENANCE_COST_PROPERTY));
        autoOperatingCost = (fuelCost + mainCost)  * 0.01f;

    }

    private void startMatrixServer(Properties properties) {
        String serverAddress = (String) properties.get("RunModel.MatrixServerAddress");
        int serverPort = new Integer((String) properties.get("RunModel.MatrixServerPort"));
        logger.info("connecting to matrix server " + serverAddress + ":" + serverPort);

        try{

            MatrixDataManager mdm = MatrixDataManager.getInstance();
            MatrixDataServerIf ms = new MatrixDataServerRmi(serverAddress, serverPort, MatrixDataServer.MATRIX_DATA_SERVER_NAME);
            ms.testRemote(Thread.currentThread().getName());
            mdm.setMatrixDataServerObject(ms);

        } catch (Exception e) {
            logger.error("could not connect to matrix server", e);
            throw new RuntimeException(e);

        }

    }

    private final TripModeChoice[] modeChoiceLookup = {
            TripModeChoice.UNKNOWN, 			//NA
            TripModeChoice.DRIVE_ALONE_NO_TOLL,	//Drive alone free
            TripModeChoice.DRIVE_ALONE_TOLL,	//Drive alone pay
            TripModeChoice.S2_GP,				//Shared 2GP
            TripModeChoice.S2_NO_TOLL,			//Shared 2HOV
            TripModeChoice.S2_TOLL,				//Shared 2PAY
            TripModeChoice.S3_GP,				//Shared 3GP
            TripModeChoice.S3_NO_TOLL,			//Shared 3HOV
            TripModeChoice.S3_TOLL,				//Shared 3PAY
            TripModeChoice.WALK,				//WALK
            TripModeChoice.BIKE,				//BIKE
            TripModeChoice.WALK_SET,			//WALK_TRANSIT           
            TripModeChoice.PNR_SET,				//PNR_TRANSIT
            TripModeChoice.KNR_PVT,				//KNR_TRANSIT_PVT
            TripModeChoice.KNR_TNC,				//KNR_TRANSIT_TNC
            TripModeChoice.TAXI,				//TAXI
            TripModeChoice.TNC,                 //TNC
            TripModeChoice.SCHOOLBUS			//SHOOLBUS
    };

    private int getTod(int tripTimePeriod) {
        int tod = ModelStructure.getSkimPeriodIndex(tripTimePeriod);
        return tod;
    }

    private int getStartTime(int tripTimePeriod) {
        return (tripTimePeriod-1)*30 + 270; //starts at 4:30 and goes half hour intervals after that
    }

    public TripAttributes getTripAttributes(int origin, int destination, int tripModeIndex, int boardTap, int alightTap, int tripTimePeriod, boolean inbound, int set) {
        int tod = getTod(tripTimePeriod);
        TripModeChoice tripMode = modeChoiceLookup[tripModeIndex < 0 ? 0 : tripModeIndex];
        TripAttributes attributes = getTripAttributes(tripMode,origin,destination,boardTap,alightTap,tod,inbound,set);
        attributes.setTripStartTime(getStartTime(tripTimePeriod));
        int oTaz = -1;
        int dTaz = -1;
        oTaz = mgraManager.getTaz(origin);
        dTaz = mgraManager.getTaz(destination);
        attributes.setOriginTAZ(oTaz);
        attributes.setDestinationTAZ(dTaz);
        return attributes;
    }

    private TripAttributes getTripAttributesUnknown() {
        return new TripAttributes(-1,-1,-1,-1,-1);
    }

    private TripAttributes getTripAttributes(TripModeChoice modeChoice, int origin, int destination, int boardTap, int alightTap, int tod, boolean inbound, int set) {
        int timeIndex = -1;
        int distIndex = -1;
        int tollIndex = -1;
        int btollIndex = -1;
   
        switch (modeChoice) {
            case UNKNOWN : return getTripAttributesUnknown();
            case DRIVE_ALONE_NO_TOLL : {
                timeIndex = DA_TIME_INDEX;
                distIndex = DA_DIST_INDEX;
                btollIndex = DA_BTOLL_INDEX;
                double[] autoSkims = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger);
                double cost = autoSkims[distIndex] * autoOperatingCost + autoSkims[btollIndex];
                return new TripAttributes(autoSkims[timeIndex],autoSkims[distIndex],cost);
          }
            case DRIVE_ALONE_TOLL : {
                timeIndex = DA_TOLL_TIME_INDEX;
                distIndex = DA_TOLL_DIST_INDEX;
                tollIndex = DA_TOLL_TOLL_INDEX;
                btollIndex = DA_TOLL_BTOLL_INDEX;
                double[] autoSkims = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger);
                double cost = autoSkims[distIndex] * autoOperatingCost + autoSkims[btollIndex] + autoSkims[tollIndex];
                return new TripAttributes(autoSkims[timeIndex],autoSkims[distIndex],cost);
            }
            case S2_GP : {
                timeIndex = DA_TIME_INDEX;
                distIndex = DA_DIST_INDEX;
                btollIndex = DA_BTOLL_INDEX;
                double[] autoSkims = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger);
                double cost = autoSkims[distIndex] * autoOperatingCost + autoSkims[btollIndex];
                return new TripAttributes(autoSkims[timeIndex],autoSkims[distIndex],cost);
            }
            case S2_TOLL : 
            case TAXI: 
            case TNC: {
                timeIndex = HOV_TOLL_TIME_INDEX;
                distIndex = HOV_TOLL_DIST_INDEX;
                tollIndex = HOV_TOLL_TOLL_INDEX;
                btollIndex = HOV_TOLL_BTOLL_INDEX;
                double[] autoSkims = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger);
                double cost = autoSkims[distIndex] * autoOperatingCost + autoSkims[btollIndex] + autoSkims[tollIndex];
                return new TripAttributes(autoSkims[timeIndex],autoSkims[distIndex],cost);
            }
            case S2_NO_TOLL : {
                timeIndex = HOV_TIME_INDEX;
                distIndex = HOV_DIST_INDEX;
                btollIndex = HOV_BTOLL_INDEX;
                double[] autoSkims = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger);
                double cost = autoSkims[distIndex] * autoOperatingCost + autoSkims[btollIndex];
                return new TripAttributes(autoSkims[timeIndex],autoSkims[distIndex],cost);
            }
            case S3_GP : {
                timeIndex = DA_TIME_INDEX;
                distIndex = DA_DIST_INDEX;
                btollIndex = DA_BTOLL_INDEX;
                double[] autoSkims = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger);
                double cost = autoSkims[distIndex] * autoOperatingCost + autoSkims[btollIndex];
                return new TripAttributes(autoSkims[timeIndex],autoSkims[distIndex],cost);
            }
            case S3_TOLL : {
                timeIndex = HOV3_TOLL_TIME_INDEX;
                distIndex = HOV3_TOLL_DIST_INDEX;
                tollIndex = HOV3_TOLL_TOLL_INDEX;
                btollIndex = HOV3_TOLL_BTOLL_INDEX;
                double[] autoSkims = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger);
                double cost = autoSkims[distIndex] * autoOperatingCost + autoSkims[btollIndex] + autoSkims[tollIndex];
                return new TripAttributes(autoSkims[timeIndex],autoSkims[distIndex],cost);
            }
            case S3_NO_TOLL : {
                timeIndex = HOV3_TIME_INDEX;
                distIndex = HOV3_DIST_INDEX;
                btollIndex = HOV3_BTOLL_INDEX;
                double[] autoSkims = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger);
                double cost = autoSkims[distIndex] * autoOperatingCost + autoSkims[btollIndex];
                return new TripAttributes(autoSkims[timeIndex],autoSkims[distIndex],cost);
            }

            case WALK :
            case BIKE : {
            	
            	double distance = 0.0;
            	double speed = modeChoice == TripModeChoice.BIKE ? DEFAULT_BIKE_SPEED : DEFAULT_WALK_SPEED;
            	//If mgras are within walking distance, use the mgraToMgra file, else use auto skims distance.
            	if(mgraManager.getMgrasAreWithinWalkDistance(origin, destination)){
            		distance = mgraManager.getMgraToMgraWalkDistFrom(origin, destination);
            		return new TripAttributes((distance/5280)*60/speed,distance/5280,0);
            	} else {
            		distance = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger)[DA_DIST_INDEX];
            		return new TripAttributes(distance*60/speed,distance,0);
            	}
                

            }
            case WALK_SET : 
            case PNR_SET : 
            case KNR_PVT :
            case KNR_TNC :{
                boolean isDrive = modeChoice.isDrive;

                double[] skims;
                int boardTaz = -1;
                int alightTaz = -1;
                double boardAccessTime = 0.0;
                double alightAccessTime = 0.0;
                int originTaz = mgraManager.getTaz(origin);
                int destTaz = mgraManager.getTaz(destination);
                if (isDrive) { 
                    if (!inbound) { //outbound: drive to transit stop at origin, then transit to destination
                        boardAccessTime = tazManager.getTimeToTapFromTaz(originTaz,boardTap,( modeChoice==TripModeChoice.PNR_SET ? Modes.AccessMode.PARK_N_RIDE : Modes.AccessMode.KISS_N_RIDE));
                        alightAccessTime = mgraManager.getWalkTimeFromMgraToTap(destination,alightTap);
                        
                        if (boardAccessTime ==-1) {
                            logger.info("Error: TAP not accessible from origin TAZ by "+ (modeChoice==TripModeChoice.PNR_SET ? "PNR" : "KNR" )+" access");
                            logger.info("mc: " + modeChoice);
                            logger.info("origin MAZ: " + origin);
                            logger.info("origin TAZ" + originTaz);
                            logger.info("dest MAZ: " + destination);
                            logger.info("board tap: " + boardTap);
                            logger.info("alight tap: " + alightTap);
                            logger.info("tod: " + tod);
                            logger.info("inbound: " + inbound);
                            logger.info("set: " + set);
                        } 
                        
                        if (alightAccessTime == -1){
                            logger.info("Error: TAP not accessible from destination MAZ by walk access");
                            logger.info("mc: " + modeChoice);
                            logger.info("origin MAZ: " + origin);
                            logger.info("origin TAZ" + originTaz);
                            logger.info("dest MAZ: " + destination);
                            logger.info("board tap: " + boardTap);
                            logger.info("alight tap: " + alightTap);
                            logger.info("tod: " + tod);
                            logger.info("inbound: " + inbound);
                            logger.info("set: " + set);
                       	
                        }
                        skims = dtw.getDriveTransitWalkSkims(set,boardAccessTime,alightAccessTime,boardTap,alightTap,tod,false);
                    } else { //inbound: transit from origin to destination, then drive
                        boardAccessTime = mgraManager.getWalkTimeFromMgraToTap(origin,boardTap);
                        alightAccessTime = tazManager.getTimeToTapFromTaz(destTaz,alightTap,( modeChoice==TripModeChoice.PNR_SET ? Modes.AccessMode.PARK_N_RIDE : Modes.AccessMode.KISS_N_RIDE));
                        
                        if (boardAccessTime ==-1) {
                            logger.info("Error: TAP not accessible from origin MAZ by walk access");
                            logger.info("mc: " + modeChoice);
                            logger.info("origin MAZ: " + origin);
                            logger.info("origin TAZ" + originTaz);
                            logger.info("dest MAZ: " + destination);
                            logger.info("board tap: " + boardTap);
                            logger.info("alight tap: " + alightTap);
                            logger.info("tod: " + tod);
                            logger.info("inbound: " + inbound);
                            logger.info("set: " + set);
                        } 
                        
                        if (alightAccessTime == -1){
                            logger.info("Error: TAP not accessible from destination TAZ by "+ (modeChoice==TripModeChoice.PNR_SET ? "PNR" : "KNR" )+" access");
                            logger.info("mc: " + modeChoice);
                            logger.info("origin MAZ: " + origin);
                            logger.info("origin TAZ" + originTaz);
                            logger.info("dest MAZ: " + destination);
                            logger.info("board tap: " + boardTap);
                            logger.info("alight tap: " + alightTap);
                            logger.info("tod: " + tod);
                            logger.info("inbound: " + inbound);
                            logger.info("set: " + set);
                       	
                        }
                   skims = wtd.getWalkTransitDriveSkims(set,boardAccessTime,alightAccessTime,boardTap,alightTap,tod,false);
                    }
                } else {
                    int bt = mgraManager.getTapPosition(origin,boardTap);
                    int at = mgraManager.getTapPosition(destination,alightTap);
                    if (bt < 0 || at < 0) {
                        logger.info("bad tap position: " + bt + "  " + at);
                        logger.info("mc: " + modeChoice);
                        logger.info("origin: " + origin);
                        logger.info("dest: " + destination);
                        logger.info("board tap: " + boardTap);
                        logger.info("alight tap: " + alightTap);
                        logger.info("tod: " + tod);
                        logger.info("inbound: " + inbound);
                        logger.info("set: " + set);
                        logger.info("board tap position: " + bt);
                        logger.info("alight tap position: " + at);
                    } else {
                        boardAccessTime = mgraManager.getMgraToTapWalkTime(origin,bt);
                        alightAccessTime = mgraManager.getMgraToTapWalkTime(destination,at);
                    }
                    skims = wtw.getWalkTransitWalkSkims(set,boardAccessTime,alightAccessTime,boardTap,alightTap,tod,false);
                }

                double time = 0.0;
                
                time += skims[TRANSIT_SET_CR_TIME_INDEX];
                time += skims[TRANSIT_SET_LRT_TIME_INDEX];
                time += skims[TRANSIT_SET_HR_TIME_INDEX];
                time += skims[TRANSIT_SET_FR_TIME_INDEX];
                time += skims[TRANSIT_SET_EXPRESS_BUS_TIME_INDEX];
                time += skims[TRANSIT_SET_LOCAL_BUS_TIME_INDEX];
                
                time += skims[TRANSIT_SET_ACCESS_TIME_INDEX];
                time += skims[TRANSIT_SET_EGRESS_TIME_INDEX ];
                time += skims[TRANSIT_SET_AUX_WALK_TIME_INDEX];
                time += skims[TRANSIT_SET_FIRST_WAIT_TIME_INDEX];
                time += skims[TRANSIT_SET_TRANSFER_WAIT_TIME_INDEX];
                
                double dist = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger)[DA_DIST_INDEX];  //todo: is this correct enough?
                return new TripAttributes(time,dist,skims[TRANSIT_SET_FARE_INDEX],boardTaz,alightTaz);
            }
            case SCHOOLBUS : {
                timeIndex = HOV_TIME_INDEX;
                distIndex = HOV_DIST_INDEX;
                double cost = 0.0;
                double[] autoSkims = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger);
                return new TripAttributes(autoSkims[timeIndex],autoSkims[distIndex],cost);
            }
            default : throw new IllegalStateException("Should not be here: " + modeChoice);
        }
    }

    public static enum TripModeChoice {
        UNKNOWN(false,false),
        DRIVE_ALONE_NO_TOLL(true,false),
        DRIVE_ALONE_TOLL(true,true),
        S2_GP(true,false),
        S2_NO_TOLL(true,false),
        S2_TOLL(true,true),
        S3_GP(true,false),
        S3_NO_TOLL(true,false),
        S3_TOLL(true,true),
        WALK(false,false),
        BIKE(false,false),
        WALK_SET(false,false),
        PNR_SET(true,false),
        KNR_PVT(true,false),
        KNR_TNC(true,false),
        TAXI(true,true),
        TNC(true,true),
        SCHOOLBUS(true,false);
        
        private final boolean isDrive;
        private final boolean isToll;

        private TripModeChoice(boolean drive, boolean toll) {
            isDrive = drive;
            isToll = toll;
        }
    }

    public static class TripAttributes {
        private final float tripTime;
        private final float tripDistance;
        private final float tripCost;
        private final int tripBoardTaz;
        private final int tripAlightTaz;
        private int originTAZ;
        private int destinationTAZ;
 
        public int getTripStartTime() {
            return tripStartTime;
        }

        public void setTripStartTime(int tripStartTime) {
            this.tripStartTime = tripStartTime;
        }

        private int tripStartTime;


        public TripAttributes(double tripTime, double tripDistance, double tripCost, int tripBoardTaz, int tripAlightTaz) {
            this.tripTime = (float) tripTime;
            this.tripDistance = (float) tripDistance;
            this.tripCost = (float) tripCost;
            this.tripBoardTaz = tripBoardTaz;
            this.tripAlightTaz = tripAlightTaz;
       }

        public TripAttributes(double tripTime, double tripDistance, double tripCost) {
            this(tripTime,tripDistance,tripCost,-1,-1);
        }
        
        public void setOriginTAZ(int oTaz) {
            this.originTAZ = oTaz;
        }
        
        public void setDestinationTAZ(int dTaz) {
            this.destinationTAZ = dTaz;
        }

        public float getTripTime() {
            return tripTime;
        }

        public float getTripDistance() {
            return tripDistance;
        }

        public float getTripCost() {
            return tripCost;
        }

        public int getTripBoardTaz() {
            return tripBoardTaz;
        }

        public int getTripAlightTaz() {
            return tripAlightTaz;
        }
        
        public int getTripOriginTaz() {
        	return originTAZ;
        }
        
        public int getTripDestinationTaz() {
        	return destinationTAZ;
        }
        
       
     }

}
