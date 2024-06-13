package com.pb.mtctm2.abm.transitcapacityrestraint;

import java.io.Serializable;
import java.util.HashMap;
import org.apache.log4j.Logger;
import com.pb.common.calculator.VariableTable;

/**
 * This class is for resimulating transit path choice. it is used 
 * as the DMU in the selection UEC.
 * 
 * @author Joel Freedman
 * @version August 27, 2018
 */
public class ResimulateTransitPathDMU
        implements Serializable, VariableTable
{

    protected transient Logger         logger = Logger.getLogger(ResimulateTransitPathDMU.class);

    protected HashMap<String, Integer> methodIndexMap;
    int                                 applicationType = 0;
    int                                 personType = 1;     //defaults to full-time worker
    private int originMaz;
    private int destinationMaz;
    //private int boardingTap;
    //private int alightingTap;
    //private int set;
    private int tod;
    float								fareSubsidy = 0f;
    protected float[][] transitFareDiscounts;
    int									accessEgressMode=0; //this is called a walk-access DMU but it is used in the TAP-to-TAP UEC, so it is
    //possible that it is being called for a drive-access path!

    public ResimulateTransitPathDMU()
    {
        setupMethodIndexMap();
    }

    private void setupMethodIndexMap()
    {
        methodIndexMap = new HashMap<String, Integer>();

        methodIndexMap.put("getOriginMaz", 0);
        methodIndexMap.put("getDestinationMaz", 1);
        //methodIndexMap.put("getBoardingTap", 2);
        //methodIndexMap.put("getAlightingTap", 3);
        //methodIndexMap.put("getSet", 4);
        methodIndexMap.put("getTOD", 5);
        methodIndexMap.put("getApplicationType", 6);
        methodIndexMap.put("getPersonType", 8);
        methodIndexMap.put("getAccessEgressMode", 11);
        methodIndexMap.put("getLocalDiscount",20);
        methodIndexMap.put("getExpressDiscount",21);
        methodIndexMap.put("getLRTDiscount",22);
        methodIndexMap.put("getHeavyDiscount",23);
        methodIndexMap.put("getCRDiscount",24);
        methodIndexMap.put("getFerryDiscount",25);
        
        methodIndexMap.put("getFareSubsidy", 26);

    }

    public double getValueForIndex(int variableIndex, int arrayIndex)
    {

        switch (variableIndex)
        {
            case 0:
                return getOriginMaz();
            case 1:
                return getDestinationMaz();
            //case 2:
            //    return getBoardingTap();
            //case 3:
            //    return getAlightingTap();
            //case 4:
            //    return getSet();
            case 5:
                return getTOD();
            case 6:
                return getApplicationType();
            case 8:
                return getPersonType();
            case 11:
            	return getAccessEgressMode();
            case 20:
            	return getLocalDiscount();
            case 21:
            	return getExpressDiscount();
            case 22:
            	return getLRTDiscount();
            case 23:
            	return getHeavyDiscount();
            case 24:
            	return getCRDiscount();
            case 25:
            	return getFerryDiscount();
            case 26:
            	return getFareSubsidy();

            default:
                logger.error("method number = " + variableIndex + " not found");
                throw new RuntimeException("method number = " + variableIndex + " not found");

        }
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

    public void setValue(String variableName, double variableValue)
    {
        throw new UnsupportedOperationException();
    }

    public void setValue(int variableIndex, double variableValue)
    {
        throw new UnsupportedOperationException();
    }

	public int getOriginMaz() {
		return originMaz;
	}

	public void setOriginMaz(int originMaz) {
		this.originMaz = originMaz;
	}

	public int getDestinationMaz() {
		return destinationMaz;
	}

	public void setDestinationMaz(int destinationMaz) {
		this.destinationMaz = destinationMaz;
	}
	/*
	public int getBoardingTap() {
		return boardingTap;
	}

	public void setBoardingTap(int boardingTap) {
		this.boardingTap = boardingTap;
	}

	public int getAlightingTap() {
		return alightingTap;
	}

	public void setAlightingTap(int alightingTap) {
		this.alightingTap = alightingTap;
	}

	public int getSet() {
		return set;
	}

	public void setSet(int set) {
		this.set = set;
	}
	*/
	public int getTOD() {
		return tod;
	}

	public void setTOD(int tod) {
		this.tod = tod;
	}
	   
	public float getLocalDiscount() {
	    	
	   	if(applicationType!=0)
	   		return transitFareDiscounts[0][personType-1];
	   	return 1.0f;
	}
	    
	public float getExpressDiscount() {
	    	
	   	if(applicationType!=0)
	   		return transitFareDiscounts[1][personType-1];
	   	return 1.0f;
	}
	    
	public float getLRTDiscount() {
	    	
	   	if(applicationType!=0)
	   		return transitFareDiscounts[2][personType-1];
	  	return 1.0f;
	}

	public float getHeavyDiscount() {
	    	
	  	if(applicationType!=0)
	   		return transitFareDiscounts[3][personType-1];
	   	return 1.0f;
	}
	public float getCRDiscount() {
	    	
	   	if(applicationType!=0)
	   		return transitFareDiscounts[4][personType-1];
	   	return 1.0f;
	}

	public float getFerryDiscount() {
	   	if(applicationType!=0)
	   		return transitFareDiscounts[5][personType-1];
	  	return 1.0f;
	}

	    
    public float getFareSubsidy() {
		return fareSubsidy;
	}

	public void setFareSubsidy(float fareSubsidy) {
		this.fareSubsidy = fareSubsidy;
	}

	public void setApplicationType(int applicationType) {
    	this.applicationType = applicationType;
	}
		    
	public int getApplicationType() {
	   	return applicationType;
	}
	public void setPersonType(int personType) {
	  	this.personType = personType;
	}
	public int getPersonType() {
	   	return personType;
	}
    public void setAccessEgressMode(int accessEgressMode){
    	this.accessEgressMode = accessEgressMode;
    }
    
    public void setTransitFareDiscounts(float[][] transitFareDiscounts) {
    	
    	this.transitFareDiscounts = transitFareDiscounts;
    }
    
    /**
     * Get the access/egress mode
     * 
     * @return accessEgressMode
     */
    public int getAccessEgressMode(){
    	return accessEgressMode;
    }

}
