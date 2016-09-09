package com.pb.mtctm2.abm.ctramp;

import java.io.Serializable;
import java.util.HashMap;
import org.apache.log4j.Logger;
import com.pb.common.calculator.IndexValues;
import com.pb.common.calculator.VariableTable;

public class TourModeChoiceDMU
        implements Serializable, VariableTable
{

    protected transient Logger             logger = Logger.getLogger(TourModeChoiceDMU.class);

    public static final int                WTW = McLogsumsCalculator.WTW;
    public static final int                WTD = McLogsumsCalculator.WTD;
    public static final int                DTW = McLogsumsCalculator.DTW;
    protected static final int             NUM_ACC_EGR = McLogsumsCalculator.NUM_ACC_EGR;
        
    protected static final int             OUT = McLogsumsCalculator.OUT;
    protected static final int             IN = McLogsumsCalculator.IN;
    protected static final int             NUM_DIR = McLogsumsCalculator.NUM_DIR;
    
    protected HashMap<String, Integer> methodIndexMap;
    protected IndexValues              dmuIndex;

    protected Household                hh;
    protected Tour                     tour;
    protected Tour                     workTour;
    protected Person                   person;

    protected ModelStructure           modelStructure;

    protected double                   origDuDen;
    protected double                   origEmpDen;
    protected double                   origTotInt;
    protected double                   destDuDen;
    protected double                   destEmpDen;
    protected double                   destTotInt;    
    
    protected double                   lsWgtAvgCostM;
    protected double                   lsWgtAvgCostD;
    protected double                   lsWgtAvgCostH;
    protected double                   reimburseProportion;
    
    protected float                    pTazTerminalTime;
    protected float                    aTazTerminalTime;

    
    protected double                   nmWalkTimeOut;
    protected double                   nmWalkTimeIn;
    protected double                   nmBikeTimeOut;
    protected double                   nmBikeTimeIn;
    
    protected int                      parkingArea;

    protected double[][]                 transitLogSum;
    
    protected int oMaz;
    protected int dMaz;
    

    public TourModeChoiceDMU(ModelStructure modelStructure)
    {
        this.modelStructure = modelStructure;
        dmuIndex = new IndexValues();
        
        //accEgr by in/outbound
        transitLogSum = new double[NUM_ACC_EGR][NUM_DIR];
        
    }

    
    public void setHouseholdObject(Household hhObject)
    {
        hh = hhObject;
    }

    public Household getHouseholdObject()
    {
        return hh;
    }

    public void setPersonObject(Person personObject)
    {
        person = personObject;
    }

    public Person getPersonObject()
    {
        return person;
    }

    public void setTourObject(Tour tourObject)
    {
        tour = tourObject;
    }

    public void setWorkTourObject(Tour tourObject)
    {
        workTour = tourObject;
    }

    public Tour getTourObject()
    {
        return tour;
    }
    
    
    public void setParkingArea(int parkingArea) {
  		this.parkingArea = parkingArea;
  	}

    /**
     * Set this index values for this tour mode choice DMU object.
     * 
     * @param hhIndex is the DMU household index
     * @param zoneIndex is the DMU zone index
     * @param origIndex is the DMU origin index
     * @param destIndex is the DMU desatination index
     */
    public void setDmuIndexValues(int hhIndex, int zoneIndex, int origIndex, int destIndex, boolean debug)
    {
        dmuIndex.setHHIndex(hhIndex);
        dmuIndex.setZoneIndex(zoneIndex);
        dmuIndex.setOriginZone(origIndex);
        dmuIndex.setDestZone(destIndex);

        dmuIndex.setDebug(false);
        dmuIndex.setDebugLabel("");
        if (debug)
        {
            dmuIndex.setDebug(true);
            dmuIndex.setDebugLabel("Debug MC UEC");
        }

    }

    public int getPersonType()
    {
        return person.getPersonTypeNumber();
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
    
    public void setReimburseProportion( double proportion ) {
        reimburseProportion = proportion;
    }
    
    public void setLsWgtAvgCostM( double cost ) {
        lsWgtAvgCostM = cost;
    }
    
    public void setLsWgtAvgCostD( double cost ) {
        lsWgtAvgCostD = cost;
    }
    
    public void setLsWgtAvgCostH( double cost ) {
        lsWgtAvgCostH = cost;
    }
    
    public void setPTazTerminalTime(float time)
    {
        pTazTerminalTime = time;
    }
    
    public void setATazTerminalTime(float time)
    {
        aTazTerminalTime = time;
    }
    
    public IndexValues getDmuIndexValues()
    {
        return dmuIndex;
    }

    public void setIndexDest(int d)
    {
        dmuIndex.setDestZone(d);
    }

    public void setOMaz( int value ) {
        oMaz = value; 
    }
    
    public void setDMaz( int value ) {
        dMaz = value; 
    } 
    
    public int getOMaz() {
        return oMaz; 
    }
    
    public int getDMaz() {
        return dMaz; 
    }
    
    public void setTransitLogSum(int accEgr, boolean inbound, double value){
    	transitLogSum[accEgr][inbound == true ? 1 : 0] = value;
    }

    protected double getTransitLogSum(int accEgr,boolean inbound){
        return transitLogSum[accEgr][inbound == true ? 1 : 0];
    }
    
    
    public int getWorkTourModeIsSov()
    {
        boolean tourModeIsSov = modelStructure.getTourModeIsSov(workTour.getTourModeChoice());
        return tourModeIsSov ? 1 : 0;
    }

    public int getWorkTourModeIsHov()
    {
        boolean tourModeIsHov = modelStructure.getTourModeIsHov(workTour.getTourModeChoice());
        return tourModeIsHov ? 1 : 0;
    }

    public int getWorkTourModeIsBike()
    {
        boolean tourModeIsBike = modelStructure.getTourModeIsBike(workTour.getTourModeChoice());
        return tourModeIsBike ? 1 : 0;
    }

    public int getTourCategoryJoint()
    {
        if (tour.getTourCategory().equalsIgnoreCase(ModelStructure.JOINT_NON_MANDATORY_CATEGORY)) return 1;
        else return 0;
    }

    public int getTourCategoryEscort()
    {
        if (tour.getTourPrimaryPurpose().equalsIgnoreCase(ModelStructure.ESCORT_PRIMARY_PURPOSE_NAME)) return 1;
        else return 0;
    }

    public int getTourCategorySubtour()
    {
        if (tour.getTourCategory().equalsIgnoreCase(ModelStructure.AT_WORK_CATEGORY)) return 1;
        else return 0;
    }

    public int getNumberOfParticipantsInJointTour()
    {
        int[] participants = tour.getPersonNumArray();
        int returnValue = 0;
        if (participants != null) returnValue = participants.length;
        return returnValue;
    }

    public int getHhSize()
    {
        return hh.getHhSize();
    }

    public int getAutos()
    {
        return hh.getAutoOwnershipModelResult();
    }

    public int getWorkers()
    {
        return hh.getWorkers();
    }
    
    public int getAge()
    {
        return person.getAge();
    }

    public int getIncome()
    {
        return hh.getIncome();
    }

    public void setNmWalkTimeOut( double nmWalkTime )
    {
        nmWalkTimeOut = nmWalkTime;
    }
    
    public double getNmWalkTimeOut()
    {
        return nmWalkTimeOut;
    }
    
    public void setNmWalkTimeIn( double nmWalkTime )
    {
        nmWalkTimeIn = nmWalkTime;
    }
    
    public double getNmWalkTimeIn()
    {
        return nmWalkTimeIn;
    }
    
    public void setNmBikeTimeOut( double nmBikeTime )
    {
        nmBikeTimeOut = nmBikeTime;
    }
    
    public double getNmBikeTimeOut()
    {
        return nmBikeTimeOut;
    }
    
    public void setNmBikeTimeIn( double nmBikeTime )
    {
        nmBikeTimeIn = nmBikeTime;
    }
    
    public double getNmBikeTimeIn()
    {
        return nmBikeTimeIn;
    }
    
    public int getFreeParkingEligibility()
    {
        return person.getFreeParkingAvailableResult();
    }
           
    public double getReimburseProportion() {
        return reimburseProportion;
    }
    
    public double getLsWgtAvgCostM() {
        return lsWgtAvgCostM;
    }
    
    public double getLsWgtAvgCostD() {
        return lsWgtAvgCostD;
    }

    public double getLsWgtAvgCostH() {
        return lsWgtAvgCostH;
    }
    
    public double getPTazTerminalTime()
    {
        return pTazTerminalTime;
    }
    
    public double getATazTerminalTime()
    {
        return aTazTerminalTime;
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
