/*
 * Copyright 2005 PB Consult Inc. Licensed under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance with the License. You
 * may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software distributed
 * under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
 * CONDITIONS OF ANY KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations under the License.
 */
package com.pb.mtctm2.abm.ctramp;

import java.io.Serializable;
import java.util.HashMap;
import org.apache.log4j.Logger;
import com.pb.common.calculator.VariableTable;
import com.pb.common.datafile.TableDataSet;

/**
 * WalkDMU is the Decision-Making Unit class for the Walk-transit choice. The class
 * contains getter and setter methods for the variables used in the WalkPathUEC.
 * 
 * @author Joel Freedman
 * @version 1.0, March, 2009
 * 
 */
public class TransitWalkAccessDMU
        implements Serializable, VariableTable
{

    protected transient Logger         logger = Logger.getLogger(TransitWalkAccessDMU.class);

    protected HashMap<String, Integer> methodIndexMap;

    double                              stopsToMgraWalkTime;
    double                              mgraToStopsWalkTime;
    double                              escalatorTime;
    int 								period;
    int 								set;
    
    //default values for generic application
    int                                 applicationType = 0;
    int                                 personType = 1;     //defaults to full-time worker
    float                               ivtCoeff;
    float                               costCoeff;
    int									accessEgressMode=0; //this is called a walk-access DMU but it is used in the TAP-to-TAP UEC, so it is
                                                            //possible that it is being called for a drive-access path!
    int                                 tourCategoryIsJoint = 0;
    float                               valueOfTime = (float) 10.0;
    float								fareSubsidy = 0f;
    
    protected float[][] transitFareDiscounts;

    public TransitWalkAccessDMU()
    {
        setupMethodIndexMap();
    }

    /**
     * Set the access/egress mode
     * 
     * @param accessEgressMode
     */
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
    
  
    /**
     * Get the time from the production/origin MGRA to stops.
     * 
     * @return The time from the production/origin MGRA to stops.
     */
    public double getMgraStopsWalkTime()
    {
        return mgraToStopsWalkTime;
    }

    /**
     * Set the time from the production/origin MGRA to stops.
     * 
     * @param walkTime The time from the production/origin MGRA to stops.
     */
    public void setMgraStopsWalkTime(double walkTime)
    {
        this.mgraToStopsWalkTime = walkTime;
    }

    /**
     * Get the time from stops to the attraction/destination MGRA.
     * 
     * @return The time from stops to the attraction/destination MGRA.
     */
    public double getStopsMgraWalkTime()
    {
        return stopsToMgraWalkTime;
    }

    /**
     * Set the time from the alighting stops to the attraction/destination MGRA.
     * 
     * @param walkTime The time from the alighting stops to the attraction/destination
     *            MGRA.
     */
    public void setStopsMgraWalkTime(double walkTime)
    {
        this.stopsToMgraWalkTime = walkTime;
    }

    /**
     * Get the time to get to the platform.
     * 
     * @return The time in minutes.
     */
    public double getEscalatorTime()
    {
        return escalatorTime;
    }

    /**
     * Set the time to get to the platform.
     * 
     * @param escalatorTime The time in minutes.
     */
    public void setEscalatorTime(double escalatorTime)
    {
        this.escalatorTime = escalatorTime;
    }
    
    public void setTOD(int period) {
    	this.period = period;
    }
    
    public int getTOD() {
    	return period;
    }
    
    public void setSet(int set) {
    	this.set = set;
    }
    
    public int getSet() {
    	return set;
    }
    
    
    public void setApplicationType(int applicationType) {
    	this.applicationType = applicationType;
    }
    
    public int getApplicationType() {
    	return applicationType;
    }
    
    public void setTourCategoryIsJoint(int tourCategoryIsJoint) {
    	this.tourCategoryIsJoint = tourCategoryIsJoint;
    }
    
    public int getTourCategoryIsJoint() {
    	return tourCategoryIsJoint;
    }
    
    public void setPersonType(int personType) {
    	this.personType = personType;
    }
    
    public int getPersonType() {
    	return personType;
    }
    
    public void setIvtCoeff(float ivtCoeff) {
    	this.ivtCoeff = ivtCoeff;
    }
    
    public void setCostCoeff(float costCoeff) {
    	this.costCoeff = costCoeff;
    }
    
    public float getIvtCoeff() {
    	return ivtCoeff;
    }

    public float getCostCoeff() {
    	return costCoeff;
    }
    public void setValueOfTime(float valueOfTime) {
    	this.valueOfTime = valueOfTime;
    }
    
    public float getValueOfTime() {
    	return valueOfTime;
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

	/**
     * Log the DMU values.
     * 
     * @param localLogger The logger to use.
     */
    public void logValues(Logger localLogger)
    {

        localLogger.info("");
        localLogger.info("Walk DMU Values:");
        localLogger.info("");
        localLogger.info(String.format("MGRA to Stops walk time:    %9.4f", mgraToStopsWalkTime));
        localLogger.info(String.format("Stops to MGRA walk time:    %9.4f", stopsToMgraWalkTime));
        localLogger.info(String.format("Escalator time:           %9.4f", escalatorTime));
        localLogger.info(String.format("Period:                   %9s", period));
        localLogger.info(String.format("Set:                      %9s", set));
        localLogger.info(String.format("applicationType:          %9s", applicationType));
        localLogger.info(String.format("personType:               %9s", personType));
        localLogger.info(String.format("ivtCoeff  :               %9.4f", ivtCoeff));
        localLogger.info(String.format("costCoeff  :              %9.4f", costCoeff));
        localLogger.info(String.format("accessEgressMode  :       %9s", accessEgressMode));
        localLogger.info(String.format("tourCategoryIsJoint:      %9s", tourCategoryIsJoint));
        localLogger.info(String.format("valueOfTime:              %9.4f", valueOfTime));
 
        if(applicationType!=0) {
        	localLogger.info(String.format("Local fare discount:      %9.4f", getLocalDiscount()));
        	localLogger.info(String.format("Express fare discount:    %9.4f", getExpressDiscount()));
        	localLogger.info(String.format("LRT fare discount:        %9.4f", getLRTDiscount()));
        	localLogger.info(String.format("Heavy fare discount:      %9.4f", getHeavyDiscount()));
        	localLogger.info(String.format("CR fare discount:         %9.4f", getCRDiscount()));
        	localLogger.info(String.format("Ferry fare discount:      %9.4f", getFerryDiscount()));
        	localLogger.info(String.format("Transit fare subsidy:     %9.4f", getFareSubsidy()));
        }
        

    }

    private void setupMethodIndexMap()
    {
        methodIndexMap = new HashMap<String, Integer>();

        methodIndexMap.put("getEscalatorTime", 0);
        methodIndexMap.put("getMgraStopsWalkTime", 1);
        methodIndexMap.put("getStopsMgraWalkTime", 2);
        methodIndexMap.put("getTOD", 3);
        methodIndexMap.put("getSet", 4);
        
        methodIndexMap.put("getApplicationType", 6);
        methodIndexMap.put("getPersonType", 8);
        methodIndexMap.put("getIvtCoeff", 9);
        methodIndexMap.put("getCostCoeff", 10);
        methodIndexMap.put("getAccessEgressMode", 11);
        methodIndexMap.put("getTourCategoryIsJoint", 12);
        methodIndexMap.put("getValueOfTime", 13);
        
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
                return getEscalatorTime();
            case 1:
                return getMgraStopsWalkTime();
            case 2:
                return getStopsMgraWalkTime();
            case 3:
                return getTOD();
            case 4:
                return getSet();
            case 6:
                return getApplicationType();
            case 8:
                return getPersonType();
            case 9:
                return getIvtCoeff();
            case 10:
            	return getCostCoeff();
            case 11:
            	return getAccessEgressMode();
            case 12:
            	return getTourCategoryIsJoint();
            case 13:
            	return getValueOfTime();
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

}
