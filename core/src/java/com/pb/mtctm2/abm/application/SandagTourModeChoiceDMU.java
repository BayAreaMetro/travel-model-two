package com.pb.mtctm2.abm.application;

import java.util.HashMap;

import com.pb.mtctm2.abm.ctramp.ModelStructure;
import com.pb.mtctm2.abm.ctramp.TourModeChoiceDMU;

public class SandagTourModeChoiceDMU
        extends TourModeChoiceDMU
{

    public SandagTourModeChoiceDMU(ModelStructure modelStructure)
    {
        super(modelStructure);
        setupMethodIndexMap();
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

    public float getTimeOutbound()
    {
        return tour.getTourDepartPeriod();
    }

    public float getTimeInbound()
    {
        return tour.getTourArrivePeriod();
    }

    public int getIncome()
    {
        return hh.getIncomeInDollars();
    }

    public int getTpChoice() {
    	return hh.getTpChoice();
    }
        
    public int getAdults()
    {
        return hh.getNumPersons18plus();
    }

    public int getFemale()
    {
        return person.getPersonIsFemale();
    }

    public void setOrigDuDen(double arg)
    {
        origDuDen = arg;
    }

    public void setOrigEmpDen(double arg)
    {
        origEmpDen = arg;
    }

    public void setOrigTotInt(double arg)
    {
        origTotInt = arg;
    }

    public void setDestDuDen(double arg)
    {
        destDuDen = arg;
    }

    public void setDestEmpDen(double arg)
    {
        destEmpDen = arg;
    }

    public void setDestTotInt(double arg)
    {
        destTotInt = arg;
    }

    public double getODUDen()
    {
        return origDuDen;
    }

    public double getOEmpDen()
    {
        return origEmpDen;
    }

    public double getOTotInt()
    {
        return origTotInt;
    }

    public double getDDUDen()
    {
        return destDuDen;
    }

    public double getDEmpDen()
    {
        return destEmpDen;
    }

    public double getDTotInt()
    {
        return destTotInt;
    }

    public double getNm_walkTime_out()
    {
        return getNmWalkTimeOut();
    }

    public double getNm_walkTime_in()
    {
        return getNmWalkTimeIn();
    }

    public double getNm_bikeTime_out()
    {
        return getNmBikeTimeOut();
    }

    public double getNm_bikeTime_in()
    {
        return getNmBikeTimeIn();
    }

    private void setupMethodIndexMap()
    {
        methodIndexMap = new HashMap<String, Integer>();

        methodIndexMap.put("getTimeOutbound", 0);
        methodIndexMap.put("getTimeInbound", 1);
        methodIndexMap.put("getIncome", 2);
        methodIndexMap.put("getAdults", 3);
        methodIndexMap.put("getFemale", 4);
        methodIndexMap.put("getHhSize", 5);
        methodIndexMap.put("getAutos", 6);
        methodIndexMap.put("getAge", 7);
        methodIndexMap.put("getTourCategoryJoint", 8);
        methodIndexMap.put("getNumberOfParticipantsInJointTour", 9);
        methodIndexMap.put("getWorkTourModeIsSov", 10);
        methodIndexMap.put("getWorkTourModeIsBike", 11);
        methodIndexMap.put("getWorkTourModeIsHov", 12);
        methodIndexMap.put("getPTazTerminalTime", 14);
        methodIndexMap.put("getATazTerminalTime", 15);
        methodIndexMap.put("getODUDen", 16);
        methodIndexMap.put("getOEmpDen", 17);
        methodIndexMap.put("getOTotInt", 18);
        methodIndexMap.put("getDDUDen", 19);
        methodIndexMap.put("getDEmpDen", 20);
        methodIndexMap.put("getDTotInt", 21);
        methodIndexMap.put("getTourCategoryEscort", 22);
        methodIndexMap.put("getMonthlyParkingCost", 23);
        methodIndexMap.put("getDailyParkingCost", 24);
        methodIndexMap.put("getHourlyParkingCost", 25);
        methodIndexMap.put("getReimburseProportion", 26);
        methodIndexMap.put("getPersonType", 27);
        methodIndexMap.put("getFreeParkingEligibility", 28);
        methodIndexMap.put("getValueOfTime", 29);
        
        methodIndexMap.put("getNm_walkTime_out", 90);
        methodIndexMap.put("getNm_walkTime_in", 91);
        methodIndexMap.put("getNm_bikeTime_out", 92);
        methodIndexMap.put("getNm_bikeTime_in", 93);

        methodIndexMap.put("getWalkSetLogSum", 100);
        methodIndexMap.put("getPnrSetLogSum", 101);
        methodIndexMap.put("getKnrSetLogSum", 102);
                
        methodIndexMap.put("getWorkers", 200);
        
        methodIndexMap.put("getTpChoice", 400);
        
        methodIndexMap.put("getOMaz", 401);
        methodIndexMap.put("getDMaz", 402);

    }

    public double getValueForIndex(int variableIndex, int arrayIndex)
    {

        double returnValue = -1;

        switch (variableIndex)
        {

            case 0:
                returnValue = getTimeOutbound();
                break;
            case 1:
                returnValue = getTimeInbound();
                break;
            case 2:
                returnValue = getIncome();
                break;
            case 3:
                returnValue = getAdults();
                break;
            case 4:
                returnValue = getFemale();
                break;
            case 5:
                returnValue = getHhSize();
                break;
            case 6:
                returnValue = getAutos();
                break;
            case 7:
                returnValue = getAge();
                break;
            case 8:
                returnValue = getTourCategoryJoint();
                break;
            case 9:
                returnValue = getNumberOfParticipantsInJointTour();
                break;
            case 10:
                returnValue = getWorkTourModeIsSov();
                break;
            case 11:
                returnValue = getWorkTourModeIsBike();
                break;
            case 12:
                returnValue = getWorkTourModeIsHov();
                break;
            case 14:
                returnValue = getPTazTerminalTime();
                break;
            case 15:
                returnValue = getATazTerminalTime();
                break;
            case 16:
                returnValue = getODUDen();
                break;
            case 17:
                returnValue = getOEmpDen();
                break;
            case 18:
                returnValue = getOTotInt();
                break;
            case 19:
                returnValue = getDDUDen();
                break;
            case 20:
                returnValue = getDEmpDen();
                break;
            case 21:
                returnValue = getDTotInt();
                break;
            case 22:
                returnValue = getTourCategoryEscort();
                break;
            case 23:
                returnValue = getLsWgtAvgCostM();
                break;
            case 24:
                returnValue = getLsWgtAvgCostD();
                break;
            case 25:
                returnValue = getLsWgtAvgCostH();
                break;
            case 26:
                returnValue = getReimburseProportion();
                break;
            case 27:
                returnValue = getPersonType();
                break;
            case 28:
                returnValue = getFreeParkingEligibility();
                break;
            case 29:
                returnValue = getValueOfTime();
                break;
            case 90:
                returnValue = getNmWalkTimeOut();
                break;
            case 91:
                returnValue = getNmWalkTimeIn();
                break;
            case 92:
                returnValue = getNmBikeTimeOut();
                break;
            case 93:
                returnValue = getNmBikeTimeIn();
                break;

            case 100:
                returnValue = getTransitLogSum(WTW, true) + getTransitLogSum(WTW, false);
                break;
            case 101:
                returnValue = getTransitLogSum(WTD, true) + getTransitLogSum(DTW, false);
                break;
            case 102:
                returnValue = getTransitLogSum(WTD, true) + getTransitLogSum(DTW, false);
                break;
            case 200:
                returnValue = getWorkers();
                break;
            case 400:
                returnValue = getTpChoice();
                break;
            case 401:
                returnValue = getOMaz();
                break;
            case 402:
                returnValue = getDMaz();
                break;
                
            default:
                logger.error("method number = " + variableIndex + " not found");
                throw new RuntimeException("method number = " + variableIndex + " not found");

        }

        return returnValue;

    }

}