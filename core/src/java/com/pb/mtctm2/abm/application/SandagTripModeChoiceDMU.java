package com.pb.mtctm2.abm.application;

import java.util.HashMap;
import com.pb.common.calculator.IndexValues;
import com.pb.mtctm2.abm.ctramp.ModelStructure;
import com.pb.mtctm2.abm.ctramp.TourModeChoiceDMU;
import com.pb.mtctm2.abm.ctramp.TripModeChoiceDMU;

public class SandagTripModeChoiceDMU
        extends TripModeChoiceDMU
{
    
    public SandagTripModeChoiceDMU(ModelStructure modelStructure)
    {
        super(modelStructure);
        setupMethodIndexMap();
    }

    /**
     * Set this index values for this tour mode choice DMU object.
     * 
     * @param hhIndex is the DMU household index
     * @param zoneIndex is the DMU zone index
     * @param origIndex is the DMU origin index
     * @param destIndex is the DMU desatination index
     */
    public void setDmuIndexValues(int hhIndex, int zoneIndex, int origIndex, int destIndex,
            boolean debug)
    {
        dmuIndex.setHHIndex(hhIndex);
        dmuIndex.setZoneIndex(zoneIndex);
        dmuIndex.setOriginZone(origIndex);
        dmuIndex.setDestZone(destIndex);

        dmuIndex.setDebug(false);
        dmuIndex.setDebugLabel("");
        if (debug)
        {
            dmuIndex.setDebug(true);
            dmuIndex.setDebugLabel("Debug MC UEC");
        }

    }

    public IndexValues getDmuIndexValues()
    {
        return dmuIndex;
    }

    public double getValueOfTime()
    {
        return (getTourCategoryJoint() == 1) ? getHouseholdMaxValueOfTime() : person.getValueOfTime();
    }
    
    public float getHouseholdMaxValueOfTime() {
    	
    	float max_hh_vot = 0;
        for (int i=1; i < hh.getPersons().length; i++){
        	float per_vot = hh.getPersons()[i].getValueOfTime();
        	if(per_vot > max_hh_vot) { max_hh_vot = per_vot; }
        }
        
        return max_hh_vot;
    }
    
    public int getEscortTour()
    {
        return escortTour;
    }

    public int getJointTour()
    {
        return jointTour;
    }

    public int getPartySize()
    {
        return partySize;
    }

    public int getAutos()
    {
        return autos;
    }

    public int getAge()
    {
        return age;
    }

    public int getAdults()
    {
        return adults;
    }

    public int getHhSize()
    {
        return hhSize;
    }

    public int getWorkers()
    {
        return workers;
    }
    
    public int getFemale()
    {
        return personIsFemale;
    }

    public int getIncome()
    {
        return incomeInDollars;
    }

    
    public int getTpChoice() {
    	return hh.getTpChoice();
    }

    public int getDepartPeriod()
    {
        return departPeriod;
    }

    public int getArrivePeriod()
    {
        return arrivePeriod;
    }

    public int getTripPeriod()
    {
        return tripPeriod;
    }

    public int getOutboundStops()
    {
        return outboundStops;
    }
    
    public int getInboundStops()
    {
        return inboundStops;
    }
    
    public int getTourModeIsDA()
    {
        return tourModeIsDA;
    }
    
    public int getTourModeIsS2()
    {
        return tourModeIsS2;
    }
    
    public int getTourModeIsS3()
    {
        return tourModeIsS3;
    }
    
    public int getTourModeIsWalk()
    {
        return tourModeIsWalk;
    }
    
    public int getTourModeIsBike()
    {
        return tourModeIsBike;
    }
    
    public int getTourModeIsWTran()
    {
        return tourModeIsWTran;
    }
    
    public int getTourModeIsPnr()
    {
        return tourModeIsPnr;
    }
    
    public int getTourModeIsKnr()
    {
        return tourModeIsKnr;
    }
    
    public int getTourModeIsSchBus()
    {
        return tourModeIsSchBus;
    }
    
    
    private void setupMethodIndexMap()
    {
        methodIndexMap = new HashMap<String, Integer>();

        methodIndexMap.put("getAutos", 1);
        methodIndexMap.put("getAdults", 2);
        methodIndexMap.put("getHhSize", 3);
        methodIndexMap.put("getFemale", 4);
        methodIndexMap.put("getIncome", 5);
        methodIndexMap.put("getTimeOutbound", 6);
        methodIndexMap.put("getTimeInbound", 7);
        methodIndexMap.put("getTimeTrip", 8);
        methodIndexMap.put("getTourCategoryJoint", 9);
        methodIndexMap.put("getNumberOfParticipantsInJointTour", 10);
        methodIndexMap.put("getOutboundStops", 11);
        methodIndexMap.put("getReturnStops", 12);
        methodIndexMap.put("getFirstTrip", 13);
        methodIndexMap.put("getLastTrip", 14);
        methodIndexMap.put("getTourModeIsDA", 15);
        methodIndexMap.put("getTourModeIsS2", 16);
        methodIndexMap.put("getTourModeIsS3", 17);
        methodIndexMap.put("getTourModeIsWalk", 18);
        methodIndexMap.put("getTourModeIsBike", 19);
        methodIndexMap.put("getTourModeIsWTran", 20);
        methodIndexMap.put("getTourModeIsPNR", 21);
        methodIndexMap.put("getTourModeIsKNR", 22);
        methodIndexMap.put("getODUDen", 23);
        methodIndexMap.put("getOEmpDen", 24);
        methodIndexMap.put("getOTotInt", 25);
        methodIndexMap.put("getDDUDen", 26);
        methodIndexMap.put("getDEmpDen", 27);
        methodIndexMap.put("getDTotInt", 28);
        methodIndexMap.put("getPTazTerminalTime", 30);
        methodIndexMap.put("getATazTerminalTime", 31);
        methodIndexMap.put("getAge", 32);
        methodIndexMap.put("getTourModeIsSchBus", 33);
        methodIndexMap.put("getEscortTour", 34);
        methodIndexMap.put("getAutoModeAllowedForTripSegment", 35);
        methodIndexMap.put("getWalkModeAllowedForTripSegment", 36);
        methodIndexMap.put("getSegmentIsIk", 37);
        methodIndexMap.put("getReimburseAmount", 38);
        methodIndexMap.put("getMonthlyParkingCostTourDest", 39);
        methodIndexMap.put("getDailyParkingCostTourDest", 40);
        methodIndexMap.put("getHourlyParkingCostTourDest", 41);
        methodIndexMap.put("getHourlyParkingCostTripOrig", 42);
        methodIndexMap.put("getHourlyParkingCostTripDest", 43);
        methodIndexMap.put("getTripOrigIsTourDest", 44);
        methodIndexMap.put("getTripDestIsTourDest", 45);
        methodIndexMap.put("getFreeOnsite", 46);
        methodIndexMap.put("getPersonType", 47);
        methodIndexMap.put("getValueOfTime", 48);
        methodIndexMap.put("getNm_walkTime", 90);
        methodIndexMap.put("getNm_bikeTime", 91);

        methodIndexMap.put("getWalkSetLogSum", 100);
        methodIndexMap.put("getPnrSetLogSum", 101);
        methodIndexMap.put("getKnrSetLogSum", 102);
        
        methodIndexMap.put("getWorkers", 200);
        
        methodIndexMap.put("getTpChoice", 400);
        

    }

    public double getValueForIndex(int variableIndex, int arrayIndex)
    {

        double returnValue = -1;

        switch (variableIndex)
        {

            case 1:
                returnValue = getAutos();
                break;
            case 2:
                returnValue = getAdults();
                break;
            case 3:
                returnValue = getHhSize();
                break;
            case 4:
                returnValue = getFemale();
                break;
            case 5:
                returnValue = getIncome();
                break;
            case 6:
                returnValue = getDepartPeriod();
                break;
            case 7:
                returnValue = getArrivePeriod();
                break;
            case 8:
                returnValue = getTripPeriod();
                break;
            case 9:
                returnValue = getJointTour();
                break;
            case 10:
                returnValue = getPartySize();
                break;
            case 11:
                returnValue = getOutboundStops();
                break;
            case 12:
                returnValue = getInboundStops();
                break;
            case 13:
                returnValue = getFirstTrip();
                break;
            case 14:
                returnValue = getLastTrip();
                break;
            case 15:
                returnValue = getTourModeIsDA();
                break;
            case 16:
                returnValue = getTourModeIsS2();
                break;
            case 17:
                returnValue = getTourModeIsS3();
                break;
            case 18:
                returnValue = getTourModeIsWalk();
                break;
            case 19:
                returnValue = getTourModeIsBike();
                break;
            case 20:
                returnValue = getTourModeIsWTran();
                break;
            case 21:
                returnValue = getTourModeIsPnr();
                break;
            case 22:
                returnValue = getTourModeIsKnr();
                break;
            case 23:
                returnValue = getODUDen();
                break;
            case 24:
                returnValue = getOEmpDen();
                break;
            case 25:
                returnValue = getOTotInt();
                break;
            case 26:
                returnValue = getDDUDen();
                break;
            case 27:
                returnValue = getDEmpDen();
                break;
            case 28:
                returnValue = getDTotInt();
                break;
            case 30:
                returnValue = getPTazTerminalTime();
                break;
            case 31:
                returnValue = getATazTerminalTime();
                break;
            case 32:
                returnValue = getAge();
                break;
            case 33:
                returnValue = getTourModeIsSchBus();
                break;
            case 34:
                returnValue = getEscortTour();
                break;
            case 35:
                returnValue = getAutoModeAllowedForTripSegment();
                break;
            case 36:
                returnValue = getWalkModeAllowedForTripSegment();
                break;
            case 37:
                returnValue = getSegmentIsIk();
                break;
            case 38:
                returnValue = getReimburseAmount();
                break;
            case 39:
                returnValue = getMonthlyParkingCostTourDest();
                break;
            case 40:
                returnValue = getDailyParkingCostTourDest();
                break;
            case 41:
                returnValue = getHourlyParkingCostTourDest();
                break;
            case 42:
                returnValue = getHourlyParkingCostTripOrig();
                break;
            case 43:
                returnValue = getHourlyParkingCostTripDest();
                break;
            case 44:
                returnValue = getTripOrigIsTourDest();
                break;
            case 45:
                returnValue = getTripDestIsTourDest();
                break;
            case 46:
                returnValue = getFreeOnsite();
                break;                
            case 47:
                returnValue = getPersonType();
                break;                
            case 48:
                returnValue = getValueOfTime();
                break;
            case 90:
                returnValue = getNmWalkTime();
                break;
            case 91:
                returnValue = getNmBikeTime();
                break;
                
            case 100:
                returnValue = getTransitLogSum(WTW);
                break;
            case 101:
            	if ( outboundHalfTourDirection == 1 )
                    returnValue = getTransitLogSum(DTW);
                else
                    returnValue = getTransitLogSum(WTD);
                break;
            case 102:
            	if ( outboundHalfTourDirection == 1 )
                    returnValue = getTransitLogSum(DTW);
                else
                    returnValue = getTransitLogSum(WTD);
                break;
            case 200:
                returnValue = getWorkers();
                break;    
            case 400:
                returnValue = getTpChoice();
                break;

            default:
                logger.error( "method number = " + variableIndex + " not found" );
                throw new RuntimeException( "method number = " + variableIndex + " not found" );

        }

        return returnValue;

    }

}