package com.pb.mtctm2.abm.ctramp;

import java.io.Serializable;
import java.util.HashMap;
import org.apache.log4j.Logger;
import com.pb.common.calculator.IndexValues;
import com.pb.common.calculator.VariableTable;

public class ExplicitTelecommuteDMU
        implements Serializable, VariableTable
{

    protected transient Logger         logger = Logger.getLogger(ExplicitTelecommuteDMU.class);

    protected HashMap<String, Integer> methodIndexMap;

    private Household                  hh;
    private Person                     person;
    private IndexValues                dmuIndex;

    
    
    public ExplicitTelecommuteDMU()
    {
        dmuIndex = new IndexValues();
    }

    /** need to set hh and home taz before using **/
    public void setPersonObject(Person person)
    {
        hh = person.getHouseholdObject();
        this.person = person;
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
   
    public IndexValues getDmuIndexValues()
    {
        return dmuIndex;
    }

    /* dmu @ functions */

    public int getIncomeInDollars()
    {
        return hh.getIncomeInDollars();
    }
    
    public double getLnhhinc()
    {
    	if (hh.getIncomeInDollars()>0)
    	{
    		return Math.log(hh.getIncomeInDollars());
    	}
    	else 
    	{
    		return 0.0;
    	}
    }
    
    public double getPersonIsFullTimeWorker()
    {
    	return person.getPersonIsFullTimeWorker();
    }
    
    public double getPersonIsPartTimeWorker()
    {
    	return person.getPersonIsPartTimeWorker();
    }
    
    
    public int getWorkLocMgra() {
        return person.getPersonWorkLocationZone();
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
