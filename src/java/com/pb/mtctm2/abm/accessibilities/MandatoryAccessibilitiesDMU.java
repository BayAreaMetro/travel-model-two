package com.pb.mtctm2.abm.accessibilities;

import java.io.Serializable;
import java.util.HashMap;
import org.apache.log4j.Logger;
import com.pb.common.calculator.VariableTable;

public class MandatoryAccessibilitiesDMU
        implements Serializable, VariableTable
{

    protected transient Logger         logger = Logger.getLogger(MandatoryAccessibilitiesDMU.class);

    protected HashMap<String, Integer> methodIndexMap;

    protected double                   sovNestLogsum;
    protected double                   hovNestLogsum;
    protected double                   wlkNestLogsum;
    protected double                   drvNestLogsum;
    protected double                   mgraStopsWalkTime;
    protected double                   stopsMgraWalkTime;
    protected int                      autoSufficiency;

    public MandatoryAccessibilitiesDMU()
    {
        setupMethodIndexMap();
    }

    public int getAutoSufficiency()
    {
        return autoSufficiency;
    }

    public void setAutoSufficiency(int autoSufficiency)
    {
        this.autoSufficiency = autoSufficiency;
    }

    public double getSovNestLogsum()
    {
        return sovNestLogsum;
    }

    public void setSovNestLogsum(double sovNestLogsum)
    {
        this.sovNestLogsum = sovNestLogsum;
    }

    public double getHovNestLogsum()
    {
        return hovNestLogsum;
    }

    public void setHovNestLogsum(double hovNestLogsum)
    {
        this.hovNestLogsum = hovNestLogsum;
    }

    public double getWlkNestLogsum()
    {
        return wlkNestLogsum;
    }

    public void setWlkNestLogsum(double wlkNestLogsum)
    {
        this.wlkNestLogsum = wlkNestLogsum;
    }

    public double getDrvNestLogsum()
    {
        return drvNestLogsum;
    }

    public void setDrvNestLogsum(double drvNestLogsum)
    {
        this.drvNestLogsum = drvNestLogsum;
    }

    public double getMgraStopsWalkTime()
    {
        return mgraStopsWalkTime;
    }

    public void setMgraStopsWalkTime(double mgraStopsWalkTime)
    {
        this.mgraStopsWalkTime = mgraStopsWalkTime;
    }

    public double getStopsMgraWalkTime()
    {
        return stopsMgraWalkTime;
    }

    public void setStopsMgraWalkTime(double stopsMgraWalkTime)
    {
        this.stopsMgraWalkTime = stopsMgraWalkTime;
    }

    public int getIndexValue(String variableName)
    {
        return methodIndexMap.get(variableName);
    }

    private void setupMethodIndexMap()
    {
        methodIndexMap = new HashMap<String, Integer>();

        methodIndexMap.put("getWlkNestLogsum", 0);
        methodIndexMap.put("getDrvNestLogsum", 1);
        methodIndexMap.put("getSovNestLogsum", 2);
        methodIndexMap.put("getHovNestLogsum", 3);
        methodIndexMap.put("getMgraStopsWalkTime", 4);
        methodIndexMap.put("getStopsMgraWalkTime", 5);
        methodIndexMap.put("getAutoSufficiency", 6);
    }

    public double getValueForIndex(int variableIndex, int arrayIndex)
    {

        switch (variableIndex)
        {
            case 0:
                return getWlkNestLogsum();
            case 1:
                return getDrvNestLogsum();
            case 2:
                return getSovNestLogsum();
            case 3:
                return getHovNestLogsum();
            case 4:
                return getMgraStopsWalkTime();
            case 5:
                return getStopsMgraWalkTime();
            case 6:
                return getAutoSufficiency();

            default:
                logger.error("method number = " + variableIndex + " not found");
                throw new RuntimeException("method number = " + variableIndex + " not found");

        }
    }

    public int getAssignmentIndexValue(String variableName)
    {
        throw new UnsupportedOperationException();
    }

    public double getValueForIndex(int variableIndex)
    {
        throw new UnsupportedOperationException();
    }

    public void setValue(String variableName, double variableValue)
    {
        throw new UnsupportedOperationException();
    }

    public void setValue(int variableIndex, double variableValue)
    {
        throw new UnsupportedOperationException();
    }

}
