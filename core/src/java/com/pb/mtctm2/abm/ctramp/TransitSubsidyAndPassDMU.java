package com.pb.mtctm2.abm.ctramp;

import java.io.Serializable;
import java.util.HashMap;
import org.apache.log4j.Logger;
import com.pb.common.calculator.IndexValues;
import com.pb.common.calculator.VariableTable;

public class TransitSubsidyAndPassDMU
        implements Serializable, VariableTable
{

    protected transient Logger         logger                           = Logger.getLogger(TransitSubsidyAndPassDMU.class);

    protected HashMap<String, Integer> methodIndexMap;

    private IndexValues                dmuIndex;
	private int personType;
    private float transitAccessToHHs;
    private int naicsCode;
    protected float valueOfTime;
    protected float hhIncomeInDollars;
    protected float hasSubsidy;
    protected float autoGenTime;
    protected float tranGenTime;
    protected float PTazTerminalTime;
    protected float ATazTerminalTime;

    protected float                   lsWgtAvgCostM;
    protected float                   lsWgtAvgCostD;
    protected float                   lsWgtAvgCostH;

    public TransitSubsidyAndPassDMU()
    {
        dmuIndex = new IndexValues();
    }

    // DMU methods - define one of these for every @var in the mode choice control
    // file.

    public void setDmuIndexValues(int hhId, int zoneId, int origTaz, int destTaz)
    {
        dmuIndex.setHHIndex(hhId);
        dmuIndex.setZoneIndex(zoneId);
        dmuIndex.setOriginZone(origTaz);
        dmuIndex.setDestZone(destTaz);

        dmuIndex.setDebug(false);
        dmuIndex.setDebugLabel("");
  
    }

    public IndexValues getDmuIndexValues()
    {
        return dmuIndex;
    }

    public int getPersonType() {
		return personType;
	}

	public void setPersonType(int personType) {
		this.personType = personType;
	}

	public float getTransitAccessToHHs() {
		return transitAccessToHHs;
	}

	public void setTransitAccessToHHs(float transitAccessToHHs) {
		this.transitAccessToHHs = transitAccessToHHs;
	}

	public int getNaicsCode() {
		return naicsCode;
	}

	public void setNaicsCode(int naicsCode) {
		this.naicsCode = naicsCode;
	}


    public float getLsWgtAvgCostM() {
		return lsWgtAvgCostM;
	}

	public void setLsWgtAvgCostM(float lsWgtAvgCostM) {
		this.lsWgtAvgCostM = lsWgtAvgCostM;
	}

	public float getLsWgtAvgCostD() {
		return lsWgtAvgCostD;
	}

	public void setLsWgtAvgCostD(float lsWgtAvgCostD) {
		this.lsWgtAvgCostD = lsWgtAvgCostD;
	}

	public float getLsWgtAvgCostH() {
		return lsWgtAvgCostH;
	}

	public void setLsWgtAvgCostH(float lsWgtAvgCostH) {
		this.lsWgtAvgCostH = lsWgtAvgCostH;
	}

	public float getValueOfTime() {
		return valueOfTime;
	}

	public void setValueOfTime(float valueOfTime) {
		this.valueOfTime = valueOfTime;
	}

	public float getHhIncomeInDollars() {
		return hhIncomeInDollars;
	}

	public void setHhIncomeInDollars(float hhIncomeInDollars) {
		this.hhIncomeInDollars = hhIncomeInDollars;
	}

	public float getHasSubsidy() {
		return hasSubsidy;
	}

	public void setHasSubsidy(float hasSubsidy) {
		this.hasSubsidy = hasSubsidy;
	}

	public float getAutoGenTime() {
		return autoGenTime;
	}

	public void setAutoGenTime(float autoGenTime) {
		this.autoGenTime = autoGenTime;
	}

	public float getTranGenTime() {
		return tranGenTime;
	}

	public void setTranGenTime(float tranGenTime) {
		this.tranGenTime = tranGenTime;
	}

	public float getPTazTerminalTime() {
		return PTazTerminalTime;
	}

	public void setPTazTerminalTime(float pTazTerminalTime) {
		PTazTerminalTime = pTazTerminalTime;
	}

	public float getATazTerminalTime() {
		return ATazTerminalTime;
	}

	public void setATazTerminalTime(float aTazTerminalTime) {
		ATazTerminalTime = aTazTerminalTime;
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
