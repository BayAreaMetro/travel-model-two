package com.pb.mtctm2.abm.application;

import java.util.HashMap;

import com.pb.mtctm2.abm.ctramp.TransitSubsidyAndPassDMU;

public class SandagTransitSubsidyAndPassDMU
        extends TransitSubsidyAndPassDMU
{

    public SandagTransitSubsidyAndPassDMU()
    {
        super();
        setupMethodIndexMap();
    }

    private void setupMethodIndexMap()
    {
        methodIndexMap = new HashMap<String, Integer>();

        methodIndexMap.put("getPersonType",1);
        methodIndexMap.put("getTransitAccessToHHs",2);
        methodIndexMap.put("getNaicsCode",3);
        methodIndexMap.put("getMonthlyParkingCost",4);
        methodIndexMap.put("getDailyParkingCost",5);
        methodIndexMap.put("getHourlyParkingCost",6);
        methodIndexMap.put("getValueOfTime",7);
        methodIndexMap.put("getHhIncomeInDollars",8);
        methodIndexMap.put("getHasSubsidy",9);
        methodIndexMap.put("getAutoGenTime",10);
        methodIndexMap.put("getTranGenTime",11);
        methodIndexMap.put("getPTazTerminalTime",12);
        methodIndexMap.put("getATazTerminalTime",13);
 
    }

    public double getValueForIndex(int variableIndex, int arrayIndex)
    {

        switch (variableIndex)
        {
            case 1:
            	return getPersonType();
            case 2:
            	return getTransitAccessToHHs();
            case 3:
            	return getNaicsCode();
            case 4:
            	return getLsWgtAvgCostM();
            case 5:
            	return getLsWgtAvgCostD();
            case 6:
            	return getLsWgtAvgCostH();
            case 7:
            	return getValueOfTime();
            case 8:
            	return getHhIncomeInDollars();
            case 9:
            	return getHasSubsidy();
            case 10:
            	return getAutoGenTime();
            case 11:
            	return getTranGenTime();
            case 12:
            	return getPTazTerminalTime();
            case 13:
            	return getATazTerminalTime();

            default:
                logger.error("method number = " + variableIndex + " not found");
                throw new RuntimeException("method number = " + variableIndex + " not found");

        }
    }

}