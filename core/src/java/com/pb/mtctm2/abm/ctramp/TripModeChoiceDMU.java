package com.pb.mtctm2.abm.ctramp;

import java.io.Serializable;
import java.util.HashMap;
import org.apache.log4j.Logger;
import com.pb.common.calculator.IndexValues;
import com.pb.common.calculator.VariableTable;

public class TripModeChoiceDMU
        implements Serializable, VariableTable
{

    protected transient Logger logger = Logger.getLogger(TourModeChoiceDMU.class);
    
    protected static final int                WTW = McLogsumsCalculator.WTW;
    protected static final int                WTD = McLogsumsCalculator.WTD;
    protected static final int                DTW = McLogsumsCalculator.DTW;
    protected static final int                NUM_ACC_EGR = McLogsumsCalculator.NUM_ACC_EGR;
    
    protected static final int                OUT = McLogsumsCalculator.OUT;
    protected static final int                IN = McLogsumsCalculator.IN;
    protected static final int                NUM_DIR = McLogsumsCalculator.NUM_DIR;
    
    protected HashMap<String, Integer> methodIndexMap;
    
    
    protected Tour                     tour;
    protected Person                   person;
    protected Household                hh;
    protected IndexValues              dmuIndex;
    
    protected double                   nmWalkTime;
    protected double                   nmBikeTime;
    
    protected ModelStructure           modelStructure;
    
    protected double origDuDen;
    protected double origEmpDen;
    protected double origTotInt;
    protected double destDuDen;
    protected double destEmpDen;
    protected double destTotInt;

    protected int tripOrigIsTourDest;
    protected int tripDestIsTourDest;
    
    protected int tripTime;
    protected int firstTrip;
    protected int lastTrip;
    protected int outboundStops;
    protected int inboundStops;

    protected int incomeInDollars;
    protected int age;
    protected int adults;
    protected int autos;
    protected int hhSize;
    protected int workers;
    protected int personIsFemale;

    protected int departPeriod;
    protected int arrivePeriod;
    protected int tripPeriod;

    protected int escortTour;
    protected int jointTour;
    protected int partySize;
    
    protected int outboundHalfTourDirection;
    
    protected double reimburseAmount;
    
    protected float pTazTerminalTime;
    protected float aTazTerminalTime;
    
    protected int[] mgraParkArea;
    
    protected boolean inbound;
    
    protected double[]                           lsWgtAvgCostM;
    protected double[]                           lsWgtAvgCostD;
    protected double[]                           lsWgtAvgCostH;

    protected boolean segmentIsIk; 
    protected boolean autoModeRequiredForDriveTransit; 
    protected boolean walkModeAllowedForDriveTransit; 

    protected double[] transitLogSum;
    
    protected int oMaz;
    protected int dMaz;
    
    protected float waitTimeTNC;
    protected float waitTimeTaxi;
    
    
    public TripModeChoiceDMU(ModelStructure modelStructure)
    {
        this.modelStructure = modelStructure;
        dmuIndex = new IndexValues();
        
        transitLogSum = new double[McLogsumsCalculator.NUM_ACC_EGR];
    }
    
    
    public void setParkingCostInfo( int[] mgraParkArea, double[] lsWgtAvgCostM, double[] lsWgtAvgCostD, double[] lsWgtAvgCostH )
    {
        this.mgraParkArea = mgraParkArea;
        this.lsWgtAvgCostM = lsWgtAvgCostM;
        this.lsWgtAvgCostD = lsWgtAvgCostD;
        this.lsWgtAvgCostH = lsWgtAvgCostH;
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
    
    public Tour getTourObject()
    {
        return tour;
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

    
    
    public float getTimeOutbound()
    {
        return tour.getTourDepartPeriod();
    }

    public float getTimeInbound()
    {
        return tour.getTourArrivePeriod();
    }

    
    public void setSegmentIsIk( boolean flag )
    {
        segmentIsIk = flag;
    }
    
    public int getSegmentIsIk()
    {
        return segmentIsIk ? 1 : 0;
    }
    
    public void setIncomeInDollars(int arg)
    {
        incomeInDollars = arg;
    }
    
    public void setAutos(int arg)
    {
        autos = arg;
    }

    public void setAdults(int arg)
    {
        adults = arg;
    }

    public void setHhSize(int arg)
    {
        hhSize = arg;
    }

    public void setHhWorkers(int arg)
    {
        workers = arg;
    }
    
    public void setAge(int arg)
    {
        age = arg;
    }

    public void setPersonIsFemale(int arg)
    {
        personIsFemale = arg;
    }

    public void setEscortTour(int arg)
    {
        escortTour = arg;
    }

    public void setJointTour(int arg)
    {
        jointTour = arg;
    }

    public void setPartySize(int arg)
    {
        partySize = arg;
    }

    public void setOutboundHalfTourDirection(int arg)
    {
        outboundHalfTourDirection = arg;
    }

    public void setDepartPeriod(int period)
    {
        departPeriod = period;
    }

    public void setArrivePeriod(int period)
    {
        arrivePeriod = period;
    }

    public void setTripPeriod(int period)
    {
        tripPeriod = period;
    }

    public void setOutboundStops(int stops)
    {
        outboundStops = stops;
    }

    public void setInboundStops(int stops)
    {
        inboundStops = stops;
    }

    public void setFirstTrip(int trip)
    {
        firstTrip = trip;
    }

    public void setLastTrip(int trip)
    {
        lastTrip = trip;
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
    
    public void setReimburseProportion( double prop) {
        reimburseAmount = prop;
    }
    
    public void setPTazTerminalTime(float time)
    {
        pTazTerminalTime = time;
    }
    
    public void setATazTerminalTime(float time)
    {
        aTazTerminalTime = time;
    }

    public void setTripOrigIsTourDest( int value ) {
        tripOrigIsTourDest = value; 
    }
    
    public void setTripDestIsTourDest( int value ) {
        tripDestIsTourDest = value; 
    }
    
    public void setOMaz( int value ) {
        oMaz = value; 
    }
    
    public void setDMaz( int value ) {
        dMaz = value; 
    }
    
    public IndexValues getDmuIndexValues()
    {
        return dmuIndex;
    }
    
    public void setAutoModeRequiredForTripSegment( boolean flag ) {
        autoModeRequiredForDriveTransit = flag; 
    }
    
    public void setWalkModeAllowedForTripSegment( boolean flag ) {
        walkModeAllowedForDriveTransit = flag; 
    }
    
    
    public void setIndexDest(int d)
    {
        dmuIndex.setDestZone(d);
    }
    
    public void setNonMotorizedWalkTime(double walkTime)
    {
        nmWalkTime = walkTime;
    }
        
    public void setNonMotorizedBikeTime(double bikeTime)
    {
        nmBikeTime = bikeTime;
    }
    
    public void setTransitLogSum(int accEgr, double value){
    	transitLogSum[accEgr] = value;
    }

    protected double getTransitLogSum(int accEgr){
        return transitLogSum[accEgr];
    }
    
    
    public int getAutoModeAllowedForTripSegment() {
        return autoModeRequiredForDriveTransit ? 1 : 0;        
    }
    
    public int getWalkModeAllowedForTripSegment() {
        return walkModeAllowedForDriveTransit ? 1 : 0;        
    }
    

    public int getTourModeIsDA()
    {
        boolean tourModeIsDa = modelStructure.getTourModeIsSov(tour.getTourModeChoice());
        return tourModeIsDa ? 1 : 0;
    }
    
    public int getTourModeIsS2()
    {
        boolean tourModeIsS2 = modelStructure.getTourModeIsS2(tour.getTourModeChoice());
        return tourModeIsS2 ? 1 : 0;
    }
    
    public int getTourModeIsS3()
    {
        boolean tourModeIsS3 = modelStructure.getTourModeIsS3(tour.getTourModeChoice());
        return tourModeIsS3 ? 1 : 0;
    }
    
    public int getTourModeIsSchBus()
    {
        boolean tourModeIsSchBus = modelStructure.getTourModeIsSchoolBus(tour.getTourModeChoice());
        return tourModeIsSchBus ? 1 : 0;
    }
    
    public int getTourModeIsWalk()
    {
        boolean tourModeIsWalk = modelStructure.getTourModeIsWalk(tour.getTourModeChoice());
        return tourModeIsWalk ? 1 : 0;
    }
    
    public int getTourModeIsBike()
    {
        boolean tourModeIsBike = modelStructure.getTourModeIsBike(tour.getTourModeChoice());
        return tourModeIsBike ? 1 : 0;
    }
    
    public int getTourModeIsWTran()
    {
        boolean tourModeIsWTran = modelStructure.getTourModeIsWalkTransit(tour.getTourModeChoice());
        return tourModeIsWTran ? 1 : 0;
    }
    
    public int getTourModeIsPnr()
    {
        boolean tourModeIsPnr = modelStructure.getTourModeIsPnr(tour.getTourModeChoice());
        return tourModeIsPnr ? 1 : 0;
    }
    
    public int getTourModeIsKnr()
    {
        boolean tourModeIsKnr = modelStructure.getTourModeIsKnrTransit(tour.getTourModeChoice());
        return tourModeIsKnr ? 1 : 0;
    }
    
    public int getTourModeIsTNCTransit()
    {
        boolean tourModeIsKnr = modelStructure.getTourModeIsTNCTransit(tour.getTourModeChoice());
        return tourModeIsKnr ? 1 : 0;
    }

    public int getTourModeIsTNC()
    {
    	boolean tourModeIsTNC = modelStructure.getTourModeIsTNC(tour.getTourModeChoice());
    	return tourModeIsTNC ? 1 : 0;
    }
    
    public int getTourModeIsTaxi()
    {
    	boolean tourModeIsTaxi = modelStructure.getTourModeIsTaxi(tour.getTourModeChoice());
    	return tourModeIsTaxi ? 1 : 0;
    }
    
   public double getODUDen()
    {
        return origDuDen;
    }

    public double getOEmpDen()
    {
        return origEmpDen;
    }

    public double getOTotInt()
    {
        return origTotInt;
    }

    public double getDDUDen()
    {
        return destDuDen;
    }

    public double getDEmpDen()
    {
        return destEmpDen;
    }

    public double getDTotInt()
    {
        return destTotInt;
    }

    public int getFirstTrip()
    {
        return firstTrip;
    }

    public int getLastTrip()
    {
        return lastTrip;
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
        return hh.getAutosOwned();
    }
    
    public int getAge()
    {
        return person.getAge();
    }
    
    public int getFemale()
    {
        return person.getPersonIsFemale();
    }
    
    public int getIncome()
    {
        return hh.getIncome();
    }
    
    public double getNmWalkTime()
    {
        return nmWalkTime;
    }
    
    public double getNmBikeTime()
    {
        return nmBikeTime;
    }
    
    public double getReimburseAmount() {
        return reimburseAmount;
    }
    
    public double getMonthlyParkingCostTourDest() {
        return lsWgtAvgCostM[tour.getTourDestMgra()];
    }
    
    public double getDailyParkingCostTourDest() {
        return lsWgtAvgCostD[tour.getTourDestMgra()];
    }
    
    public double getHourlyParkingCostTourDest() {
        return lsWgtAvgCostH[tour.getTourDestMgra()];
    }
    
    public double getHourlyParkingCostTripOrig() {
        return lsWgtAvgCostH[oMaz];
    }
    
    public double getHourlyParkingCostTripDest() {
        return lsWgtAvgCostH[dMaz];
    }
    
    public int getTripOrigIsTourDest() {
        return tripOrigIsTourDest; 
    }
    
    public int getTripDestIsTourDest() {
        return tripDestIsTourDest; 
    }
    
    public int getFreeOnsite() {
        return person.getFreeParkingAvailableResult() == ParkingProvisionModel.FP_MODEL_FREE_ALT ? 1 : 0;
    }
    
    public int getPersonType() {
        return person.getPersonTypeNumber();
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
    

    public int getInbound() {
 		return inbound ? 1 : 0 ;
 	}


	public void setInbound(boolean inbound) {
		this.inbound = inbound;
	}
    /** 
     * Return a 1 if this tour has an AV available else 0
     * @return
     */
    public int getUseOwnedAV() {
		return tour.getUseOwnedAV() ? 1 : 0;
	}

    public float getWaitTimeTNC() {
		return waitTimeTNC;
	}


	public void setWaitTimeTNC(float waitTimeTNC) {
		this.waitTimeTNC = waitTimeTNC;
	}


	public float getWaitTimeTaxi() {
		return waitTimeTaxi;
	}


	public void setWaitTimeTaxi(float waitTimeTaxi) {
		this.waitTimeTaxi = waitTimeTaxi;
	}
	
	public float getFareSubsidy() {
        return ((tour.getTourPrimaryPurposeIndex() == ModelStructure.WORK_PRIMARY_PURPOSE_INDEX)||
        		(tour.getTourPrimaryPurposeIndex() == ModelStructure.SCHOOL_PRIMARY_PURPOSE_INDEX)||
        		(tour.getTourPrimaryPurposeIndex() == ModelStructure.UNIVERSITY_PRIMARY_PURPOSE_INDEX))
        		? person.getTransitSubsidyPercent() : 0f;	
    }

	public int outboundPNRTripOnTour() {
		
		if(tour==null) return 0;
		
		Stop[] outboundStops = tour.getOutboundStops();
		
		if(outboundStops==null) return 0;
		
		for(Stop stop: outboundStops) {
			if(stop==null)
				continue;
			if(modelStructure.getTripModeIsPnrTransit(stop.getMode()))
				return 1;
		}
		return 0;
	}

	public int inboundPNRTripOnTour() {
		
		if(tour==null) return 0;
		
		Stop[] inboundStops = tour.getOutboundStops();
		
		if(inboundStops==null) return 0;
		
		for(Stop stop: inboundStops) {
			if(stop==null)
				continue;
			if(modelStructure.getTripModeIsPnrTransit(stop.getMode()))
				return 1;
		}
		return 0;
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
