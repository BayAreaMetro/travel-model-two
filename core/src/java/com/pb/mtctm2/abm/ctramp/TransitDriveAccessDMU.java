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

    double                              driveTimeToTap;
    double                              driveDistToTap;
    double                              driveDistFromTap;
    double                              driveTimeFromTap;
    double                              OrigDestDistance;
    double                              tapToMgraWalkTime;
    double                              mgraToTapWalkTime;
    int                                 accessMode;
    int 								period;
    int 								set;
    
    //default values for generic application
    int                                 applicationType = 0;
    int                                 tourCateogryIsJoint = 0;
    int                                 personType = 1;
    float                               valueOfTime = (float) 10.0;
    
    float               parkingCost;
    float               driveAccessWalkTime;
    float               driveAccessDriveTime;
    


    public TransitDriveAccessDMU()
    {
        setupMethodIndexMap();
    }

    /**
     * Get the walk time from the alighting TAP to the destination MGRA.
     * 
     * @return The walk time from the alighting TAP to the destination MGRA.
     */
    public double getTapMgraWalkTime()
    {
        return tapToMgraWalkTime;
    }

    /**
     * Set the walk time from the alighting TAP to the destination MGRA.
     * 
     * @param walkTime The walk time from the alighting TAP to the destination MGRA.
     */
    public void setTapMgraWalkTime(double walkTime)
    {
        tapToMgraWalkTime = walkTime;
    }

    /**
     * Get the walk time to the boarding TAP from the origin MGRA.
     * 
     * @return The walk time from the origin MGRA to the boarding TAP.
     */
    public double getMgraTapWalkTime()
    {
        return mgraToTapWalkTime;
    }

    /**
     * Set the walk time to the boarding TAP from the origin MGRA
     * 
     * @param walkTime The walk time to the boarding TAP from the origin MGRA.
     */
    public void setMgraTapWalkTime(double walkTime)
    {
        mgraToTapWalkTime = walkTime;
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

    /**
     * Get the drive time from the origin/production TDZ/TAZ to the TAP.
     * 
     * @return The drive time in minutes.
     */
    public double getDriveTimeToTap()
    {
        return driveTimeToTap;
    }

    /**
     * Set the drive time from the origin/production TDZ/TAZ to the TAP.
     * 
     * @param driveTimeToTap The drive time in minutes.
     */
    public void setDriveTimeToTap(double driveTimeToTap)
    {
        this.driveTimeToTap = driveTimeToTap;
    }

    /**
     * Get the drive distance from the origin/production TDZ/TAZ to the TAP.
     * 
     * @return The drive distance in miles.
     */
    public double getDriveDistToTap()
    {
        return driveDistToTap;
    }

    /**
     * Set the drive distance from the origin/production TDZ/TAZ to the TAP.
     * 
     * @param driveDistToTap The drive distance in miles.
     */
    public void setDriveDistToTap(double driveDistToTap)
    {
        this.driveDistToTap = driveDistToTap;
    }

    /**
     * Get the drive time from the TAP to the destination/attraction TDZ/TAZ.
     * 
     * @return The drive time in minutes.
     */
    public double getDriveTimeFromTap()
    {
        return driveTimeFromTap;
    }

    /**
     * Set the drive time from the TAP to the destination/attraction TDZ/TAZ.
     * 
     * @param driveTime The drive time in minutes.
     */
    public void setDriveTimeFromTap(double driveTime)
    {
        driveTimeFromTap = driveTime;
    }

    /**
     * Get the drive distance from the TAP to the destination/attraction TDZ/TAZ.
     * 
     * @return The drive distance in miles.
     */
    public double getDriveDistFromTap()
    {
        return driveDistFromTap;
    }

    /**
     * Set the drive distance from the TAP to the destination/attraction TDZ/TAZ.
     * 
     * @param driveDist The drive distance in miles.
     */
    public void setDriveDistFromTap(double driveDist)
    {
        driveDistFromTap = driveDist;
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

	public float getDriveAccessWalkTime() {
		return driveAccessWalkTime;
	}

	public void setDriveAccessWalkTime(float driveAccessWalkTime) {
		this.driveAccessWalkTime = driveAccessWalkTime;
	}

	public float getDriveAccessDriveTime() {
		return driveAccessDriveTime;
	}

	public void setDriveAccessDriveTime(float driveAccessDriveTime) {
		this.driveAccessDriveTime = driveAccessDriveTime;
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
        localLogger.info(String.format("Drive Time To Tap:     %9.4f", driveTimeToTap));
        localLogger.info(String.format("Drive Dist To Tap:     %9.4f", driveDistToTap));
        localLogger.info(String.format("Drive Time From Tap:     %9.4f", driveTimeFromTap));
        localLogger.info(String.format("Drive Dist From Tap:     %9.4f", driveDistFromTap));
        localLogger.info(String.format("TAP to MGRA walk time:    %9.4f", tapToMgraWalkTime));
        localLogger.info(String.format("MGRA to TAP walk time:    %9.4f", mgraToTapWalkTime));
        localLogger.info(String.format("Period:                   %9s", period));
        localLogger.info(String.format("Set:                      %9s", set));
        localLogger.info(String.format("applicationType:          %9s", applicationType));
        localLogger.info(String.format("tourCateogryIsJoint:      %9s", tourCateogryIsJoint));
        localLogger.info(String.format("personType:               %9s", personType));
        localLogger.info(String.format("valueOfTime:              %9.4f", valueOfTime));
        localLogger.info(String.format("origDestDistance          %9.4f, origDestDistance"));
        localLogger.info(String.format("Parking Cost:             %9.2f", parkingCost));
        localLogger.info(String.format("Drive access walk time:   %9.2f", driveAccessWalkTime));
        localLogger.info(String.format("Drive access drive time:  %9.2f, driveAccessDriveTime"));
        


        AccessMode[] accessModes = AccessMode.values();
        localLogger.info(String.format("Access Mode:              %5s", accessModes[accessMode]
                .toString()));
    }

    private void setupMethodIndexMap()
    {
        methodIndexMap = new HashMap<String, Integer>();

        methodIndexMap.put("getAccessMode", 0);
        methodIndexMap.put("getDriveDistToTap", 2);
        methodIndexMap.put("getDriveTimeToTap", 3);
        methodIndexMap.put("getDriveDistFromTap", 4);
        methodIndexMap.put("getDriveTimeFromTap", 5);
        methodIndexMap.put("getTapMgraWalkTime", 7);
        methodIndexMap.put("getMgraTapWalkTime", 8);
        methodIndexMap.put("getTOD", 9);
        methodIndexMap.put("getSet", 10);
        
        methodIndexMap.put("getApplicationType", 12);
        methodIndexMap.put("getTourCategoryIsJoint", 13);
        methodIndexMap.put("getPersonType", 14);
        methodIndexMap.put("getValueOfTime", 15);
        methodIndexMap.put("getOrigDestDistance",17);
        
        
        methodIndexMap.put("getParkingCost", 20);
        methodIndexMap.put("getDriveAccessWalkTime", 21);
        methodIndexMap.put("getDriveAccessDriveTime", 22);

    }

    public double getValueForIndex(int variableIndex, int arrayIndex)
    {

        switch (variableIndex)
        {
            case 0:
                return getAccessMode();
            case 2:
                return getDriveDistToTap();
            case 3:
                return getDriveTimeToTap();
            case 4:
                return getDriveDistFromTap();
            case 5:
                return getDriveTimeFromTap();
            case 7:
                return getTapMgraWalkTime();
            case 8:
                return getMgraTapWalkTime();
            case 9:
                return getTOD();
            case 10:
                return getSet();
                
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

            case 20:
            	return getParkingCost();
            case 21:
            	return getDriveAccessWalkTime();
            case 22:
            	return getDriveAccessDriveTime();


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
