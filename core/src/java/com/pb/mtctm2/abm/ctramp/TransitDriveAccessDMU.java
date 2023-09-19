package com.pb.mtctm2.abm.ctramp;

import java.io.Serializable;
import java.util.HashMap;
import org.apache.log4j.Logger;

import com.pb.common.calculator.VariableTable;
import com.pb.mtctm2.abm.ctramp.Modes.AccessMode;
/**
 * This class is used for ...
 * 
 * @author Joel Freedman
 * @version Mar 20, 2009
 *          <p/>
 *          Created by IntelliJ IDEA.
 */
public class TransitDriveAccessDMU
        implements Serializable, VariableTable
{

    protected transient Logger         logger = Logger.getLogger(TransitDriveAccessDMU.class);

    protected HashMap<String, Integer> methodIndexMap;

    double                              OrigDestDistance;
    double                              stopsToMgraWalkTime;
    double                              mgraToStopsWalkTime;
    int                                 accessMode;
    int 								period;
    int                                 accessEgress;
    
    //default values for generic application
    int                                 applicationType = 0;
    int                                 tourCateogryIsJoint = 0;
    int                                 personType = 1;
    float                               valueOfTime = (float) 10.0;
    
    float               parkingCost;
    


    public TransitDriveAccessDMU()
    {
        setupMethodIndexMap();
    }

    /**
     * Get the walk time from the alighting stop to the destination MGRA.
     * 
     * @return The walk time from the alighting stop to the destination MGRA.
     */
    public double getStopsMgraWalkTime()
    {
        return stopsToMgraWalkTime;
    }

    /**
     * Set the walk time from the alighting stop to the destination MGRA.
     * 
     * @param walkTime The walk time from the alighting stop to the destination MGRA.
     */
    public void setStopsMgraWalkTime(double walkTime)
    {
        stopsToMgraWalkTime = walkTime;
    }

    /**
     * Get the walk time to the boarding stop from the origin MGRA.
     * 
     * @return The walk time from the origin MGRA to the boarding stop.
     */
    public double getMgraStopsWalkTime()
    {
        return mgraToStopsWalkTime;
    }

    /**
     * Set the walk time to the boarding stops from the origin MGRA
     * 
     * @param walkTime The walk time to the boarding stop from the origin MGRA.
     */
    public void setMgraStopsWalkTime(double walkTime)
    {
        mgraToStopsWalkTime = walkTime;
    }

    /**
     * Get the access mode for this DMU.
     * 
     * @return The access mode.
     */
    public int getAccessMode()
    {
        return accessMode;
    }

    /**
     * Set the access mode for this DMU.
     * 
     * @param accessMode The access mode.
     */
    public void setAccessMode(int accessMode)
    {
        this.accessMode = accessMode;
    }
    
    public double getOrigDestDistance() {
		return OrigDestDistance;
	}
	public void setOrigDestDistance(double origDestDistance) {
		OrigDestDistance = origDestDistance;
	}
    public void setTOD(int period) {
    	this.period = period;
    }
    
    public int getTOD() {
    	return period;
    }
    
    public void setApplicationType(int applicationType) {
    	this.applicationType = applicationType;
    }
    
    public int getApplicationType() {
    	return applicationType;
    }
    
    public void setTourCategoryIsJoint(int tourCateogryIsJoint) {
    	this.tourCateogryIsJoint = tourCateogryIsJoint;
    }
    
    public int getTourCategoryIsJoint() {
    	return tourCateogryIsJoint;
    }
    
    public void setPersonType(int personType) {
    	this.personType = personType;
    }
    
    public int getPersonType() {
    	return personType;
    }
    
    public void setValueOfTime(float valueOfTime) {
    	this.valueOfTime = valueOfTime;
    }
    
    public float getValueOfTime() {
    	return valueOfTime;
    }

    public float getParkingCost() {
		return parkingCost;
	}

	public void setParkingCost(float parkingCost) {
		this.parkingCost = parkingCost;
	}

	/**
     * Log the DMU values.
     * 
     * @param localLogger The logger to use.
     */
    public void logValues(Logger localLogger)
    {

        localLogger.info("");
        localLogger.info("Drive-Transit Auto Access DMU Values:");
        localLogger.info("");
        localLogger.info(String.format("Stops to MGRA walk time:    %9.4f", stopsToMgraWalkTime));
        localLogger.info(String.format("MGRA to stops walk time:    %9.4f", mgraToStopsWalkTime));
        localLogger.info(String.format("Period:                   %9s", period));
        localLogger.info(String.format("applicationType:          %9s", applicationType));
        localLogger.info(String.format("tourCateogryIsJoint:      %9s", tourCateogryIsJoint));
        localLogger.info(String.format("personType:               %9s", personType));
        localLogger.info(String.format("valueOfTime:              %9.4f", valueOfTime));
        localLogger.info(String.format("origDestDistance          %9.4f, origDestDistance"));
        localLogger.info(String.format("Parking Cost:             %9.2f", parkingCost));
        


        AccessMode[] accessModes = AccessMode.values();
        localLogger.info(String.format("Access Mode:              %5s", accessModes[accessMode]
                .toString()));
    }

    private void setupMethodIndexMap()
    {
        methodIndexMap = new HashMap<String, Integer>();

        methodIndexMap.put("getAccessMode", 0);
        methodIndexMap.put("getStopsMgraWalkTime", 7);
        methodIndexMap.put("getMgraStopsWalkTime", 8);
        methodIndexMap.put("getTOD", 9);
        methodIndexMap.put("getSet", 10);
        
        methodIndexMap.put("getApplicationType", 12);
        methodIndexMap.put("getTourCategoryIsJoint", 13);
        methodIndexMap.put("getPersonType", 14);
        methodIndexMap.put("getValueOfTime", 15);
        methodIndexMap.put("getOrigDestDistance",17);
        methodIndexMap.put("getAccessEgress",18);
        
        methodIndexMap.put("getParkingCost", 20);

    }

    public double getValueForIndex(int variableIndex, int arrayIndex)
    {

        switch (variableIndex)
        {
            case 0:
                return getAccessMode();
            case 7:
                return getStopsMgraWalkTime();
            case 8:
                return getMgraStopsWalkTime();
            case 9:
                return getTOD();
                
            case 12:
                return getApplicationType();
            case 13:
                return getTourCategoryIsJoint();
            case 14:
                return getPersonType();
            case 15:
                return getValueOfTime();
            case 17:
            	return getOrigDestDistance();
            case 18:
            	return getAccessEgress();

            case 20:
            	return getParkingCost();


            default:
                logger.error("method number = " + variableIndex + " not found");
                throw new RuntimeException("method number = " + variableIndex + " not found");

        }
    }

    /**
     * Get the combinatorial access egress mode for this DMU.
     * 
     * @return The access mode.
     */
    public int getAccessEgress()
    {
        return accessEgress;
    }

    /**
     * Set the combinatorial access egress mode for this DMU.
     * 
     * @param accessMode The access mode.
     */
    public void setAccessEgress(int accessEgress)
    {
        this.accessEgress = accessEgress;
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
