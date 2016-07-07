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

    private static final int WALK_TIME_INDEX = 0;
    private static final int BIKE_TIME_INDEX = 0;

    private static final int DA_TIME_INDEX = 0;
    private static final int DA_FF_TIME_INDEX = 1;
    private static final int DA_DIST_INDEX = 2;
    private static final int DA_TOLL_TIME_INDEX = 3;
    private static final int DA_TOLL_FF_TIME_INDEX = 4;
    private static final int DA_TOLL_DIST_INDEX = 5;
    private static final int DA_TOLL_COST_INDEX = 6;
    private static final int DA_TOLL_TOLLDIST_INDEX = 7;
    private static final int HOV_TIME_INDEX = 8;
    private static final int HOV_FF_TIME_INDEX = 9;
    private static final int HOV_DIST_INDEX = 10;
    private static final int HOV_HOVDIST_INDEX = 11;
    
    private static final int HOV3_TIME_INDEX = 12;
    private static final int HOV3_FF_TIME_INDEX = 13;
    private static final int HOV3_DIST_INDEX = 14;
    private static final int HOV3_HOVDIST_INDEX = 15;
    
    private static final int HOV_TOLL_TIME_INDEX = 16;
    private static final int HOV_TOLL_FF_TIME_INDEX = 17;
    private static final int HOV_TOLL_DIST_INDEX = 18;
    private static final int HOV_TOLL_COST_INDEX = 19;
    private static final int HOV_TOLL_HOV_DIST_INDEX = 20;
    private static final int HOV_TOLL_TOLL_DIST_INDEX = 21;
    
    private static final int HOV3_TOLL_TIME_INDEX = 22;
    private static final int HOV3_TOLL_FF_TIME_INDEX = 23;
    private static final int HOV3_TOLL_DIST_INDEX = 24;
    private static final int HOV3_TOLL_COST_INDEX = 25;
    private static final int HOV3_TOLL_HOV_DIST_INDEX = 26;
    private static final int HOV3_TOLL_TOLL_DIST_INDEX = 27;

    private static final int TRANSIT_SET_ACCESS_TIME_INDEX = 0;
    private static final int TRANSIT_SET_EGRESS_TIME_INDEX = 1;
    private static final int TRANSIT_SET_AUX_WALK_TIME_INDEX = 2;
    private static final int TRANSIT_SET_LOCAL_BUS_TIME_INDEX = 3;
    private static final int TRANSIT_SET_EXPRESS_BUS_TIME_INDEX = 4;
    private static final int TRANSIT_SET_HR_TIME_INDEX = 5;
    private static final int TRANSIT_SET_FR_TIME_INDEX = 6;
    private static final int TRANSIT_SET_LRT_TIME_INDEX = 7;
    private static final int TRANSIT_SET_CR_TIME_INDEX = 8;
    private static final int TRANSIT_SET_FIRST_WAIT_TIME_INDEX = 9;
    private static final int TRANSIT_SET_TRANSFER_WAIT_TIME_INDEX = 10;
    private static final int TRANSIT_SET_FARE_INDEX = 11;
    private static final int TRANSIT_SET_MAIN_MODE_INDEX = 12;
    private static final int TRANSIT_SET_XFERS_INDEX = 13;

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
            TripModeChoice.KNR_SET,				//KNR_TRANSIT
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
        return new TripAttributes(-1,-1,-1,-1,-1,-1);
    }

    private double getCost(double baseCost, double driveDist) {
        return baseCost;
    }

    private TripAttributes getTripAttributes(TripModeChoice modeChoice, int origin, int destination, int boardTap, int alightTap, int tod, boolean inbound, int set) {
        int timeIndex = -1;
        int distIndex = -1;
        int costIndex = -1;
        int fullMode = -1;

        switch (modeChoice) {
            case UNKNOWN : return getTripAttributesUnknown();
            case DRIVE_ALONE_NO_TOLL : {
                timeIndex = DA_TIME_INDEX;
                distIndex = DA_DIST_INDEX;
                costIndex = -1;
                fullMode = TripModeChoice.DRIVE_ALONE_NO_TOLL.ordinal();
            }
            case DRIVE_ALONE_TOLL : {
                if (timeIndex < 0) {
                    timeIndex = DA_TOLL_TIME_INDEX;
                    distIndex = DA_TOLL_DIST_INDEX;
                    costIndex = DA_TOLL_COST_INDEX;
                    fullMode = TripModeChoice.DRIVE_ALONE_TOLL.ordinal();
                }
            }
            case S2_GP : {
                if (timeIndex < 0) {
                    timeIndex = DA_TIME_INDEX;
                    distIndex = DA_DIST_INDEX;
                    costIndex = -1;
                    fullMode = TripModeChoice.S2_GP.ordinal();
                }                                 
                double[] autoSkims = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger);
                return new TripAttributes(autoSkims[timeIndex],autoSkims[distIndex],getCost(costIndex < 0 ? 0.0 : autoSkims[costIndex],autoSkims[distIndex]),fullMode);
            }
            case S2_TOLL : {
                if (timeIndex < 0) {
                    timeIndex = HOV_TOLL_TIME_INDEX;
                    distIndex = HOV_TOLL_DIST_INDEX;
                    costIndex = HOV_TOLL_COST_INDEX;
                    fullMode = TripModeChoice.S2_TOLL.ordinal();
                }                                 
                double[] autoSkims = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger);
                return new TripAttributes(autoSkims[timeIndex],autoSkims[distIndex],getCost(costIndex < 0 ? 0.0 : autoSkims[costIndex],autoSkims[distIndex]),fullMode);
            }
            case S2_NO_TOLL : {
                if (timeIndex < 0) {
                    timeIndex = HOV_TIME_INDEX;
                    distIndex = HOV_DIST_INDEX;
                    costIndex = -1;
                    fullMode = TripModeChoice.S2_NO_TOLL.ordinal();
                }                                 
                double[] autoSkims = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger);
                return new TripAttributes(autoSkims[timeIndex],autoSkims[distIndex],getCost(costIndex < 0 ? 0.0 : autoSkims[costIndex],autoSkims[distIndex]),fullMode);
            }
            case S3_GP : {
                if (timeIndex < 0) {
                    timeIndex = DA_TIME_INDEX;
                    distIndex = DA_DIST_INDEX;
                    costIndex = -1;
                    fullMode = TripModeChoice.S3_GP.ordinal();
                }                                 
                double[] autoSkims = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger);
                return new TripAttributes(autoSkims[timeIndex],autoSkims[distIndex],getCost(costIndex < 0 ? 0.0 : autoSkims[costIndex],autoSkims[distIndex]),fullMode);
            }
            case S3_TOLL : {
                if (timeIndex < 0) {
                    timeIndex = HOV3_TOLL_TIME_INDEX;
                    distIndex = HOV3_TOLL_DIST_INDEX;
                    costIndex = HOV3_TOLL_COST_INDEX;
                    fullMode = TripModeChoice.S3_TOLL.ordinal();
                }                                 
                double[] autoSkims = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger);
                return new TripAttributes(autoSkims[timeIndex],autoSkims[distIndex],getCost(costIndex < 0 ? 0.0 : autoSkims[costIndex],autoSkims[distIndex]),fullMode);
            }
            case S3_NO_TOLL : {
                if (timeIndex < 0) {
                    timeIndex = HOV3_TIME_INDEX;
                    distIndex = HOV3_DIST_INDEX;
                    costIndex = -1;
                    fullMode = TripModeChoice.S3_NO_TOLL.ordinal();
                }                                 
                double[] autoSkims = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger);
                return new TripAttributes(autoSkims[timeIndex],autoSkims[distIndex],getCost(costIndex < 0 ? 0.0 : autoSkims[costIndex],autoSkims[distIndex]),fullMode);
            }

            case WALK :
            case BIKE : {
            	
            	double distance = 0.0;
            	double speed = modeChoice == TripModeChoice.BIKE ? DEFAULT_BIKE_SPEED : DEFAULT_WALK_SPEED;
            	fullMode = modeChoice == TripModeChoice.BIKE ? TripModeChoice.BIKE.ordinal() : TripModeChoice.WALK.ordinal();
            	//If mgras are within walking distance, use the mgraToMgra file, else use auto skims distance.
            	if(mgraManager.getMgrasAreWithinWalkDistance(origin, destination)){
            		distance = mgraManager.getMgraToMgraWalkDistFrom(origin, destination);
            		return new TripAttributes((distance/5280)*60/speed,distance/5280,0,fullMode);
            	} else {
            		distance = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger)[DA_DIST_INDEX];
            		return new TripAttributes(distance*60/speed,distance,0,fullMode);
            	}
                

            }
            case WALK_SET : 
            case PNR_SET : 
            case KNR_SET : {
                boolean isDrive = modeChoice.isDrive;

                double[] skims;
                int boardTaz = -1;
                int alightTaz = -1;
                double boardAccessTime = 0.0;
                double alightAccessTime = 0.0;
                boardTaz = mgraManager.getTaz(origin);
                alightTaz = mgraManager.getTaz(destination);
                if (isDrive) {
                    if (!inbound) { //outbound: drive to transit stop at origin, then transit to destination
                        int taz = tapManager.getTazForTap(boardTap);
                        boardTaz = taz;
                        int btapPosition = tazManager.getTapPosition(taz,boardTap,Modes.AccessMode.PARK_N_RIDE);
                        int atapPosition = mgraManager.getTapPosition(destination,alightTap);
                        if (atapPosition < 0 || btapPosition < 0) {
                            logger.info("bad tap position for drive access board tap");
                            logger.info("mc: " + modeChoice);
                            logger.info("origin: " + origin);
                            logger.info("dest: " + destination);
                            logger.info("board tap: " + boardTap);
                            logger.info("alight tap: " + alightTap);
                            logger.info("tod: " + tod);
                            logger.info("inbound: " + inbound);
                            logger.info("set: " + set);
                            logger.info("board tap position: " + btapPosition);
                            logger.info("alight tap position: " + atapPosition);
                        } else {
                            boardAccessTime = tazManager.getTapTime(taz,btapPosition,Modes.AccessMode.PARK_N_RIDE);
                            alightAccessTime = mgraManager.getMgraToTapWalkTime(destination,atapPosition);
                        }
                        skims = dtw.getDriveTransitWalkSkims(set,boardAccessTime,alightAccessTime,boardTap,alightTap,tod,false);
                    } else { //inbound: transit from origin to destination, then drive
                        int taz = -1;
                        try {
                            taz = tapManager.getTazForTap(alightTap);
                            alightTaz = taz;
                        } catch (NullPointerException e) {
                            logger.info("tap manager can't find taz for alight tap");
                            logger.info("mc: " + modeChoice);
                            logger.info("origin: " + origin);
                            logger.info("dest: " + destination);
                            logger.info("board tap: " + boardTap);
                            logger.info("alight tap: " + alightTap);
                            logger.info("tod: " + tod);
                            logger.info("inbound: " + inbound);
                            logger.info("set: " + set);
                            logger.info("a: " + tapManager.getTapParkingInfo());
                            logger.info("b: " + tapManager.getTapParkingInfo()[alightTap]);
                            logger.info("b: " + tapManager.getTapParkingInfo()[alightTap][1]);
                            logger.info("b: " + tapManager.getTapParkingInfo()[alightTap][1][0]);
                            throw e;
                        }
                        int atapPosition = tazManager.getTapPosition(taz,alightTap,Modes.AccessMode.PARK_N_RIDE);
                        int btapPosition = mgraManager.getTapPosition(origin,boardTap);
                        if (atapPosition < 0 || btapPosition < 0) {

                            logger.info("mc: " + modeChoice);
                            logger.info("origin: " + origin);
                            logger.info("dest: " + destination);
                            logger.info("board tap: " + boardTap);
                            logger.info("alight tap: " + alightTap);
                            logger.info("tod: " + tod);
                            logger.info("set: " + set);
                            logger.info("inbound: " + inbound);
                            logger.info("board tap position: " + btapPosition);
                            logger.info("alight tap position: " + atapPosition);
                        } else {
                            boardAccessTime = mgraManager.getMgraToTapWalkTime(origin,btapPosition);
                            alightAccessTime = tazManager.getTapTime(taz,atapPosition,Modes.AccessMode.PARK_N_RIDE);
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
                
                int modeIndex = 0;
                for(modeIndex = TRANSIT_SET_LOCAL_BUS_TIME_INDEX; modeIndex <= TRANSIT_SET_CR_TIME_INDEX; modeIndex++){
                	if(skims[modeIndex] > 0)
                		break;
                }
                
                if(modeChoice == TripModeChoice.WALK_SET)
                	fullMode = TripModeChoice.WALK_SET.ordinal() + (modeIndex - 3);//11-16
                
                if(modeChoice == TripModeChoice.PNR_SET)
                	fullMode = TripModeChoice.PNR_SET.ordinal() + (modeIndex + 2);//17-22
                
                if(modeChoice == TripModeChoice.KNR_SET)
                	fullMode = TripModeChoice.KNR_SET.ordinal() + (modeIndex + 7);//23-28
                
                double dist = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger)[DA_DIST_INDEX];  //todo: is this correct enough?
                return new TripAttributes(time,dist,skims[TRANSIT_SET_FARE_INDEX],fullMode,boardTaz,alightTaz);
            }
            case SCHOOLBUS : {
                if (timeIndex < 0) {
                    timeIndex = HOV_TIME_INDEX;
                    distIndex = HOV_DIST_INDEX;
                    costIndex = -1;
                    fullMode = TripModeChoice.SCHOOLBUS.ordinal() + 15;//29
                }                                 
                double[] autoSkims = autoNonMotSkims.getAutoSkims(origin,destination,tod,false,logger);
                return new TripAttributes(autoSkims[timeIndex],autoSkims[distIndex],getCost(costIndex < 0 ? 0.0 : autoSkims[costIndex],autoSkims[distIndex]),fullMode);
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
        KNR_SET(true,false),
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
        private int fullMode;

        public int getTripStartTime() {
            return tripStartTime;
        }

        public void setTripStartTime(int tripStartTime) {
            this.tripStartTime = tripStartTime;
        }

        private int tripStartTime;


        public TripAttributes(double tripTime, double tripDistance, double tripCost, int fullMode, int tripBoardTaz, int tripAlightTaz) {
            this.tripTime = (float) tripTime;
            this.tripDistance = (float) tripDistance;
            this.tripCost = (float) tripCost;
            this.tripBoardTaz = tripBoardTaz;
            this.tripAlightTaz = tripAlightTaz;
            this.fullMode = fullMode;
        }

        public TripAttributes(double tripTime, double tripDistance, double tripCost, int fullMode) {
            this(tripTime,tripDistance,tripCost,fullMode,-1,-1);
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
        
        
        public int getFullMode() {
        	return fullMode;
        }
    }

}
