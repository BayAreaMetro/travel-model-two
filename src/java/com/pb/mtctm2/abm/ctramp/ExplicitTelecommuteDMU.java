package com.pb.mtctm2.abm.ctramp;

import java.io.Serializable;
import java.util.HashMap;
import org.apache.log4j.Logger;
import com.pb.common.calculator.IndexValues;
import com.pb.common.calculator.VariableTable;

/**
 * @author crf <br/>
 *         Started: Apr 14, 2009 11:09:58 AM
 */
public class ExplicitTelecommuteDMU
        implements Serializable, VariableTable
{

    protected transient Logger         logger = Logger.getLogger(ExplicitTelecommuteDMU.class);

    protected HashMap<String, Integer> methodIndexMap;

    private IndexValues dmuIndex;

    private Household hh;

    private double percentTazIncome100Kplus;
    private double percentTazIncome75Kplus;
    private double percentTazMultpleAutos;
    private double expectedTravelTimeSavings;
    private double transpDist;
    private double pctDetour;
    private double accessibility;
    
    
    public ExplicitTelecommuteDMU()
    {
        dmuIndex = new IndexValues();
    }
    
    private void setupMethodIndexMap()
    {
        methodIndexMap = new HashMap<String, Integer>();

        methodIndexMap.put("getAutoOwnership", 0);
        methodIndexMap.put("getPctHighIncome", 1);
        methodIndexMap.put("getPctMultipleAutos", 2);
        methodIndexMap.put("getAvgtts", 3);
        methodIndexMap.put("getDistanceFromFacility", 4);
        methodIndexMap.put("getPctAltTimeCBD", 5);
        methodIndexMap.put("getAvgTransitAccess", 6);
        methodIndexMap.put("getPctIncome75Kplus", 7);
    }



    public void setDmuIndexValues(int hhId, int zoneId, int origTaz, int destTaz)
    {
        dmuIndex.setHHIndex(hhId);
        dmuIndex.setZoneIndex(zoneId);
        dmuIndex.setOriginZone(origTaz);
        dmuIndex.setDestZone(destTaz);

        dmuIndex.setDebug(false);
        dmuIndex.setDebugLabel("");
        if (hh.getDebugChoiceModels())
        {
            dmuIndex.setDebug(true);
            dmuIndex.setDebugLabel("Debug Explicit Telecommute UEC");
        }
    }

    public void setHouseholdObject(Household hhObj) {
        hh = hhObj;
    }


    public void setPctIncome100Kplus( double value) {
        percentTazIncome100Kplus = value;
    }
    
    public void setPctIncome75Kplus( double value) {
        percentTazIncome75Kplus = value;
    }

    public void setPctTazMultpleAutos( double value) {
        percentTazMultpleAutos = value;
    }

    public void setExpectedTravelTimeSavings( double value) {
        expectedTravelTimeSavings = value;
    }

    public void setTransponderDistance( double value) {
        transpDist = value;
    }
    
    public void setPctDetour( double value) {
        pctDetour = value;
    }
    
    public void setAccessibility( double value) {
        accessibility = value;
    }
    
    
    public double getPctIncome100Kplus() {
        return percentTazIncome100Kplus;
    }
    
    public double getPctIncome75Kplus() {
        return percentTazIncome75Kplus;
    }
    
    public double getPctTazMultpleAutos() {
        return percentTazMultpleAutos;
    }
    
    public double getExpectedTravelTimeSavings() {
        return expectedTravelTimeSavings;
    }
    
    public double getTransponderDistance() {
        return transpDist;
    }
    
    public double getPctDetour() {
        return pctDetour;
    }
    
    public double getAccessibility() {
        return accessibility;
    }
    
    public int getAutoOwnership() {
        return hh.getAutosOwned();
    }

    public IndexValues getDmuIndexValues() {
        return dmuIndex; 
    }
    
    
    
    public int getIndexValue(String variableName)
    {
        return methodIndexMap.get(variableName);
    }

    public int getAssignmentIndexValue(String variableName)
    {
        throw new UnsupportedOperationException();
    }

    public double getValueForIndex(int variableIndex)
    {
        throw new UnsupportedOperationException();
    }

    public double getValueForIndex(int variableIndex, int arrayIndex)
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
