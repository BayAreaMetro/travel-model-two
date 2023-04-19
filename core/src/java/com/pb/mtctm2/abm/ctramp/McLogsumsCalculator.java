package com.pb.mtctm2.abm.ctramp;

import java.io.Serializable;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Random;

import org.apache.log4j.Logger;

import com.pb.mtctm2.abm.accessibilities.AutoAndNonMotorizedSkimsCalculator;
import com.pb.mtctm2.abm.accessibilities.BestTransitPathCalculator;
import com.pb.common.newmodel.Alternative;
import com.pb.common.newmodel.ConcreteAlternative;
import com.pb.common.newmodel.LogitModel;
import com.pb.mtctm2.abm.accessibilities.TransitPath;
import com.pb.mtctm2.abm.ctramp.MgraDataManager;
import com.pb.mtctm2.abm.ctramp.Modes;
import com.pb.mtctm2.abm.ctramp.Modes.AccessMode;
import com.pb.mtctm2.abm.ctramp.TazDataManager;
import com.pb.common.calculator.IndexValues;


public class McLogsumsCalculator implements Serializable
{

    private transient Logger                autoSkimLogger                   = Logger.getLogger("autoSkim");

    public static final String              PROPERTIES_UEC_TOUR_MODE_CHOICE  = "tourModeChoice.uec.file";
    public static final String              PROPERTIES_UEC_TRIP_MODE_CHOICE  = "tripModeChoice.uec.file";


    public static final int                   WTW = 0;
    public static final int                   WTD = 1;
    public static final int                   DTW = 2;
    public static final int                   NUM_ACC_EGR = 3;
    
    public static final int                   OUT = 0;
    public static final int                   IN = 1;
    public static final int                   NUM_DIR = 2;

    private BestTransitPathCalculator          bestPathUEC;
    private double[]                           tripModeChoiceSegmentStoredProbabilities;

    
    private TazDataManager                     tazManager;
    private MgraDataManager                    mgraManager;

    private double[]                           lsWgtAvgCostM;
    private double[]                           lsWgtAvgCostD;
    private double[]                           lsWgtAvgCostH;
    private int[]                              parkingArea;
    
    private AutoAndNonMotorizedSkimsCalculator anm;

    private int                                setTourMcLogsumDmuAttributesTotalTime = 0;
    private int                                setTripMcLogsumDmuAttributesTotalTime = 0;

    //added for TNC and Taxi modes
    TNCAndTaxiWaitTimeCalculator tncTaxiWaitTimeCalculator = null;
       
    public McLogsumsCalculator()
    {
        if (mgraManager == null)
            mgraManager = MgraDataManager.getInstance();    
            
        if (tazManager == null)
            tazManager = TazDataManager.getInstance();

        this.lsWgtAvgCostM = mgraManager.getLsWgtAvgCostM();
        this.lsWgtAvgCostD = mgraManager.getLsWgtAvgCostD();
        this.lsWgtAvgCostH = mgraManager.getLsWgtAvgCostH();
        this.parkingArea = mgraManager.getMgraParkAreas();
        
      }
    
    
    public BestTransitPathCalculator getBestTransitPathCalculator()
    {
        return bestPathUEC;
    }
    
    
    public void setupSkimCalculators(HashMap<String, String> rbMap)
    {
        bestPathUEC = new BestTransitPathCalculator(rbMap);
        anm = new AutoAndNonMotorizedSkimsCalculator(rbMap);
        
        tncTaxiWaitTimeCalculator = new TNCAndTaxiWaitTimeCalculator();
        tncTaxiWaitTimeCalculator.createWaitTimeDistributions(rbMap);

    }

    public void setTazDistanceSkimArrays( double[][][] storedFromTazDistanceSkims, double[][][] storedToTazDistanceSkims ) {     
        anm.setTazDistanceSkimArrays( storedFromTazDistanceSkims, storedToTazDistanceSkims );                                                                
    }                                                                                                                            
                                                                                                                                 
                                                                                                                                 
    public AutoAndNonMotorizedSkimsCalculator getAnmSkimCalculator()
    {
        return anm;
    }

    public void setTourMcDmuAttributes( TourModeChoiceDMU mcDmuObject, int origMgra, int destMgra, int departPeriod, int arrivePeriod, boolean debug )
    {
    
        setNmTourMcDmuAttributes(  mcDmuObject, origMgra, destMgra, departPeriod, arrivePeriod, debug );
        setWtwTourMcDmuAttributes( mcDmuObject, origMgra, destMgra, departPeriod, arrivePeriod, debug );        
        setWtdTourMcDmuAttributes( mcDmuObject, origMgra, destMgra, departPeriod, arrivePeriod, debug );        
        setDtwTourMcDmuAttributes( mcDmuObject, origMgra, destMgra, departPeriod, arrivePeriod, debug );        

        // set the land use data items in the DMU for the origin
        mcDmuObject.setOrigDuDen( mgraManager.getDuDenValue( origMgra ) );
        mcDmuObject.setOrigEmpDen( mgraManager.getEmpDenValue( origMgra ) );
        mcDmuObject.setOrigTotInt( mgraManager.getTotIntValue( origMgra ) );

        // set the land use data items in the DMU for the destination
        mcDmuObject.setDestDuDen( mgraManager.getDuDenValue( destMgra ) );
        mcDmuObject.setDestEmpDen( mgraManager.getEmpDenValue( destMgra ) );
        mcDmuObject.setDestTotInt( mgraManager.getTotIntValue( destMgra ) );
        
        mcDmuObject.setLsWgtAvgCostM( lsWgtAvgCostM[destMgra] );
        mcDmuObject.setLsWgtAvgCostD( lsWgtAvgCostD[destMgra] );
        mcDmuObject.setLsWgtAvgCostH( lsWgtAvgCostH[destMgra] );
        
        int tourOrigTaz = mgraManager.getTaz(origMgra);
        int tourDestTaz = mgraManager.getTaz(destMgra);
        
        mcDmuObject.setPTazTerminalTime( tazManager.getOriginTazTerminalTime(tourOrigTaz) );
        mcDmuObject.setATazTerminalTime( tazManager.getDestinationTazTerminalTime(tourDestTaz) );
        
        Person person = mcDmuObject.getPersonObject();
        
        double reimbursePct=0;
        if(person!=null) { 
        	reimbursePct = person.getParkingReimbursement();
        }
        
        mcDmuObject.setReimburseProportion( reimbursePct );
        mcDmuObject.setParkingArea(parkingArea[destMgra]);
 
        float TNCWaitTimeOrig = 0;
        float TaxiWaitTimeOrig = 0;
        float TNCWaitTimeDest = 0;
        float TaxiWaitTimeDest = 0;
        float popEmpDenOrig = (float) mgraManager.getPopEmpPerSqMi(origMgra);
        float popEmpDenDest = (float) mgraManager.getPopEmpPerSqMi(destMgra);
        
        Household household = mcDmuObject.getHouseholdObject();
        if(household!=null){
            Random hhRandom = household.getHhRandom();
            double rnum = hhRandom.nextDouble();
            TNCWaitTimeOrig = (float) tncTaxiWaitTimeCalculator.sampleFromTNCWaitTimeDistribution(rnum, popEmpDenOrig);
            TaxiWaitTimeOrig = (float) tncTaxiWaitTimeCalculator.sampleFromTaxiWaitTimeDistribution(rnum, popEmpDenOrig);
            TNCWaitTimeDest = (float) tncTaxiWaitTimeCalculator.sampleFromTNCWaitTimeDistribution(rnum, popEmpDenDest);
            TaxiWaitTimeDest = (float) tncTaxiWaitTimeCalculator.sampleFromTaxiWaitTimeDistribution(rnum, popEmpDenDest);
        }else{
            TNCWaitTimeOrig = (float) tncTaxiWaitTimeCalculator.getMeanTNCWaitTime( popEmpDenOrig);
            TaxiWaitTimeOrig = (float) tncTaxiWaitTimeCalculator.getMeanTaxiWaitTime( popEmpDenOrig);
            TNCWaitTimeDest = (float) tncTaxiWaitTimeCalculator.getMeanTNCWaitTime( popEmpDenDest);
            TaxiWaitTimeDest = (float) tncTaxiWaitTimeCalculator.getMeanTaxiWaitTime(popEmpDenDest);
        }
        
        mcDmuObject.setOrigTaxiWaitTime(TaxiWaitTimeOrig);
        mcDmuObject.setDestTaxiWaitTime(TaxiWaitTimeDest);
        mcDmuObject.setOrigTNCWaitTime(TNCWaitTimeOrig);
        mcDmuObject.setDestTNCWaitTime(TNCWaitTimeDest);

    }
    
    
    public double calculateTourMcLogsum(int origMgra, int destMgra, int departPeriod, int arrivePeriod,
        ChoiceModelApplication mcModel, TourModeChoiceDMU mcDmuObject)
    {
        
        long currentTime = System.currentTimeMillis();        
        setTourMcDmuAttributes( mcDmuObject, origMgra, destMgra, departPeriod, arrivePeriod, mcDmuObject.getDmuIndexValues().getDebug() );
        setTourMcLogsumDmuAttributesTotalTime += ( System.currentTimeMillis() - currentTime );
    
        // mode choice UEC references highway skim matrices directly, so set index orig/dest to O/D TAZs.
        IndexValues mcDmuIndex = mcDmuObject.getDmuIndexValues();
        int tourOrigTaz = mgraManager.getTaz(origMgra);
        int tourDestTaz = mgraManager.getTaz(destMgra);
        mcDmuIndex.setOriginZone(tourOrigTaz);
        mcDmuIndex.setDestZone(tourDestTaz);
        mcDmuObject.setOMaz(origMgra);
        mcDmuObject.setDMaz(destMgra);
    
        mcModel.computeUtilities(mcDmuObject, mcDmuIndex);
        double logsum = mcModel.getLogsum();
    
        return logsum;
        
    }

    public void setWalkTransitLogSumUnavailable( TripModeChoiceDMU tripMcDmuObject ) {
    	tripMcDmuObject.setTransitLogSum( WTW, bestPathUEC.NA );
    }
    
    public void setDriveTransitLogSumUnavailable( TripModeChoiceDMU tripMcDmuObject, boolean isInbound ) {
    	
    	// set drive transit skim attributes to unavailable
        if ( ! isInbound ) {
        	tripMcDmuObject.setTransitLogSum( DTW, bestPathUEC.NA);
        }
        else {
        	tripMcDmuObject.setTransitLogSum( WTD, bestPathUEC.NA);
        }

    }
    
    
    public double calculateTripMcLogsum(int origMgra, int destMgra, int departPeriod, ChoiceModelApplication mcModel, TripModeChoiceDMU mcDmuObject, Logger myLogger)
    {
        long currentTime = System.currentTimeMillis();
        setNmTripMcDmuAttributes(  mcDmuObject, origMgra, destMgra, departPeriod, mcDmuObject.getHouseholdObject().getDebugChoiceModels() );

        // set the land use data items in the DMU for the origin
        mcDmuObject.setOrigDuDen( mgraManager.getDuDenValue( origMgra ) );
        mcDmuObject.setOrigEmpDen( mgraManager.getEmpDenValue( origMgra ) );
        mcDmuObject.setOrigTotInt( mgraManager.getTotIntValue( origMgra ) );

        // set the land use data items in the DMU for the destination
        mcDmuObject.setDestDuDen( mgraManager.getDuDenValue( destMgra ) );
        mcDmuObject.setDestEmpDen( mgraManager.getEmpDenValue( destMgra ) );
        mcDmuObject.setDestTotInt( mgraManager.getTotIntValue( destMgra ) );
        
        // mode choice UEC references highway skim matrices directly, so set index orig/dest to O/D TAZs.
        IndexValues mcDmuIndex = mcDmuObject.getDmuIndexValues();
        mcDmuIndex.setOriginZone(mgraManager.getTaz(origMgra));
        mcDmuIndex.setDestZone(mgraManager.getTaz(destMgra));
        mcDmuObject.setOMaz(origMgra);
        mcDmuObject.setDMaz(destMgra);
        
        setTripMcLogsumDmuAttributesTotalTime += ( System.currentTimeMillis() - currentTime );
        mcDmuObject.setPTazTerminalTime( tazManager.getOriginTazTerminalTime(mgraManager.getTaz(origMgra)) );
        mcDmuObject.setATazTerminalTime( tazManager.getDestinationTazTerminalTime(mgraManager.getTaz(destMgra)) );

        float TNCWaitTime = 0;
        float TaxiWaitTime = 0;
        float popEmpDen = (float) mgraManager.getPopEmpPerSqMi(origMgra);
        
        Household household = mcDmuObject.getHouseholdObject();
        if(household!=null){
            Random hhRandom = household.getHhRandom();
            double rnum = hhRandom.nextDouble();
            TNCWaitTime = (float) tncTaxiWaitTimeCalculator.sampleFromTNCWaitTimeDistribution(rnum, popEmpDen);
            TaxiWaitTime = (float) tncTaxiWaitTimeCalculator.sampleFromTaxiWaitTimeDistribution(rnum, popEmpDen);
       }else{
            TNCWaitTime = (float) tncTaxiWaitTimeCalculator.getMeanTNCWaitTime( popEmpDen);
            TaxiWaitTime = (float) tncTaxiWaitTimeCalculator.getMeanTaxiWaitTime( popEmpDen);
        }
        
        mcDmuObject.setWaitTimeTaxi(TaxiWaitTime);
        mcDmuObject.setWaitTimeTNC(TNCWaitTime);

        mcModel.computeUtilities(mcDmuObject, mcDmuIndex);
        double logsum = mcModel.getLogsum();
        tripModeChoiceSegmentStoredProbabilities = Arrays.copyOf( mcModel.getCumulativeProbabilities(), mcModel.getNumberOfAlternatives() );
        
        if ( mcDmuObject.getHouseholdObject().getDebugChoiceModels() )
            mcModel.logUECResults(myLogger, "Trip Mode Choice Utility Expressions for mgras: " + origMgra + " to " + destMgra + " for HHID: " + mcDmuIndex.getHHIndex() );
        
        return logsum;
        
    }

    
    /**
     * return the array of mode choice model cumulative probabilities determined while
     * computing the mode choice logsum for the trip segmen during stop location choice.
     * These probabilities arrays are stored for each sampled stop location so that when
     * the selected sample stop location is known, the mode choice can be drawn from the
     * already computed probabilities.
     *  
     * @return mode choice cumulative probabilities array
     */
    public double[] getStoredSegmentCumulativeProbabilities() {
        return tripModeChoiceSegmentStoredProbabilities;
    }
    
    private void setNmTourMcDmuAttributes( TourModeChoiceDMU mcDmuObject, int origMgra, int destMgra, int departPeriod, int arrivePeriod, boolean loggingEnabled )
    {
        // non-motorized, outbound then inbound
        int skimPeriodIndex = ModelStructure.getSkimPeriodIndex(departPeriod);
        departPeriod = skimPeriodIndex;
        double[] nmSkimsOut = anm.getNonMotorizedSkims(origMgra, destMgra, departPeriod, loggingEnabled, autoSkimLogger);
        if (loggingEnabled)
            anm.logReturnedSkims(origMgra, destMgra, departPeriod, nmSkimsOut, "non-motorized outbound", autoSkimLogger);

        skimPeriodIndex = ModelStructure.getSkimPeriodIndex(arrivePeriod);
        arrivePeriod = skimPeriodIndex;
        double[] nmSkimsIn = anm.getNonMotorizedSkims(destMgra, origMgra, arrivePeriod, loggingEnabled, autoSkimLogger);
        if (loggingEnabled) anm.logReturnedSkims(destMgra, origMgra, arrivePeriod, nmSkimsIn, "non-motorized inbound", autoSkimLogger);
        
        int walkIndex = anm.getNmWalkTimeSkimIndex();
        mcDmuObject.setNmWalkTimeOut( nmSkimsOut[walkIndex] );
        mcDmuObject.setNmWalkTimeIn( nmSkimsIn[walkIndex] );

        int bikeIndex = anm.getNmBikeTimeSkimIndex();
        mcDmuObject.setNmBikeTimeOut( nmSkimsOut[bikeIndex] );
        mcDmuObject.setNmBikeTimeIn( nmSkimsIn[bikeIndex] );
        
    }

    private void setWtwTourMcDmuAttributes( TourModeChoiceDMU mcDmuObject, int origMgra, int destMgra, int departPeriod, int arrivePeriod, boolean loggingEnabled )
    {
        
    	//setup best path dmu variables
    	TransitWalkAccessDMU walkDmu =  new TransitWalkAccessDMU();
    	walkDmu.setTransitFareDiscounts(bestPathUEC.getTransitFareDiscounts());
    	TransitDriveAccessDMU driveDmu  = new TransitDriveAccessDMU();
    	    	
    	// walk access, walk egress transit, outbound
        int skimPeriodIndexOut = ModelStructure.getSkimPeriodIndex(departPeriod);
        int pTaz = mgraManager.getTaz(origMgra);
        int aTaz = mgraManager.getTaz(destMgra);
        float odDistance = (float) anm.getTazDistanceFromTaz(pTaz, ModelStructure.AM_SKIM_PERIOD_INDEX)[aTaz];
        	
    	//set person specific variables
    	walkDmu.setApplicationType(bestPathUEC.APP_TYPE_TOURMC);
    	walkDmu.setTourCategoryIsJoint(mcDmuObject.getTourCategoryJoint());
    	walkDmu.setPersonType(mcDmuObject.getTourCategoryJoint()==1 ? walkDmu.personType : mcDmuObject.getPersonType());
    	walkDmu.setValueOfTime((float)mcDmuObject.getValueOfTime());
    	walkDmu.setFareSubsidy(mcDmuObject.getFareSubsidy());
    	
    	driveDmu.setApplicationType(bestPathUEC.APP_TYPE_TOURMC);
    	driveDmu.setTourCategoryIsJoint(mcDmuObject.getTourCategoryJoint());
    	driveDmu.setPersonType(mcDmuObject.getTourCategoryJoint()==1 ? driveDmu.personType : mcDmuObject.getPersonType());
    	driveDmu.setValueOfTime((float)mcDmuObject.getValueOfTime());

    	// In the Tap version, logsumXX is the logsum of N best transit paths (N Tap pairs)
    	// In the non-Tap version, we keep the logsumXX name unchanged even though it is really just the transit utility between one TAZ pair
    	double logsumOut = bestPathUEC.calcPersonSpecificUtilities(pTaz, aTaz, walkDmu, driveDmu, WTW, origMgra, destMgra, skimPeriodIndexOut, loggingEnabled, autoSkimLogger, odDistance);
    	
    	mcDmuObject.setTransitLogSum( WTW, false, logsumOut);
        
        //setup best path dmu variables
    	walkDmu =  new TransitWalkAccessDMU();
    	walkDmu.setTransitFareDiscounts(bestPathUEC.getTransitFareDiscounts());
    	driveDmu  = new TransitDriveAccessDMU();
        
        // walk access, walk egress transit, inbound
        int skimPeriodIndexIn = ModelStructure.getSkimPeriodIndex(arrivePeriod);
        	
    	//set person specific variables
    	walkDmu.setApplicationType(bestPathUEC.APP_TYPE_TOURMC);
    	walkDmu.setTourCategoryIsJoint(mcDmuObject.getTourCategoryJoint());
    	walkDmu.setPersonType(mcDmuObject.getTourCategoryJoint()==1 ? walkDmu.personType : mcDmuObject.getPersonType());
    	walkDmu.setValueOfTime((float)mcDmuObject.getValueOfTime());
    	
    	driveDmu.setApplicationType(bestPathUEC.APP_TYPE_TOURMC);
    	driveDmu.setTourCategoryIsJoint(mcDmuObject.getTourCategoryJoint());
    	driveDmu.setPersonType(mcDmuObject.getTourCategoryJoint()==1 ? driveDmu.personType : mcDmuObject.getPersonType());
    	driveDmu.setValueOfTime((float)mcDmuObject.getValueOfTime());
    	
    	// In the Tap version, logsumXX is the logsum of N best transit paths (N Tap pairs)
    	// In the non-Tap version, we keep the logsumXX name unchanged even though it is really just the transit utility between one TAZ pair
    	double logsumIn = bestPathUEC.calcPersonSpecificUtilities(aTaz, pTaz, walkDmu, driveDmu, WTW, destMgra, origMgra, skimPeriodIndexIn, loggingEnabled, autoSkimLogger, odDistance);
    	           
    	mcDmuObject.setTransitLogSum( WTW, true, logsumIn);
        
    }

    private void setWtdTourMcDmuAttributes( TourModeChoiceDMU mcDmuObject, int origMgra, int destMgra, int departPeriod, int arrivePeriod, boolean loggingEnabled )
    {
        
    	//setup best path dmu variables
    	TransitWalkAccessDMU walkDmu =  new TransitWalkAccessDMU();
    	walkDmu.setTransitFareDiscounts(bestPathUEC.getTransitFareDiscounts());
    	TransitDriveAccessDMU driveDmu  = new TransitDriveAccessDMU();
    	
    	// logsum for WTD outbound is never used -> set to NA
    	mcDmuObject.setTransitLogSum( WTD, false, bestPathUEC.NA );
    	
        //setup best path dmu variables
    	walkDmu =  new TransitWalkAccessDMU();
    	walkDmu.setTransitFareDiscounts(bestPathUEC.getTransitFareDiscounts());
    	driveDmu  = new TransitDriveAccessDMU();
    	
        // walk access, drive egress transit, inbound
        int skimPeriodIndexIn = ModelStructure.getSkimPeriodIndex(arrivePeriod);
        int pTaz = mgraManager.getTaz(origMgra);
        int aTaz = mgraManager.getTaz(destMgra);
        float odDistance = (float) anm.getTazDistanceFromTaz(pTaz, ModelStructure.AM_SKIM_PERIOD_INDEX)[aTaz];
        	
    	//set person specific variables
    	walkDmu.setApplicationType(bestPathUEC.APP_TYPE_TOURMC);
    	walkDmu.setTourCategoryIsJoint(mcDmuObject.getTourCategoryJoint());
    	walkDmu.setPersonType(mcDmuObject.getTourCategoryJoint()==1 ? walkDmu.personType : mcDmuObject.getPersonType());
    	walkDmu.setValueOfTime((float)mcDmuObject.getValueOfTime());
    	walkDmu.setFareSubsidy(mcDmuObject.getFareSubsidy());
    	
    	driveDmu.setApplicationType(bestPathUEC.APP_TYPE_TOURMC);
    	driveDmu.setTourCategoryIsJoint(mcDmuObject.getTourCategoryJoint());
    	driveDmu.setPersonType(mcDmuObject.getTourCategoryJoint()==1 ? driveDmu.personType : mcDmuObject.getPersonType());
    	driveDmu.setValueOfTime((float)mcDmuObject.getValueOfTime());
    	
    	// In the Tap version, logsumXX is the logsum of N best transit paths (N Tap pairs)
    	// In the non-Tap version, we keep the logsumXX name unchanged even though it is really just the transit utility between one TAZ pair
    	double logsumIn = bestPathUEC.calcPersonSpecificUtilities(aTaz, pTaz, walkDmu, driveDmu, WTD, destMgra, origMgra, skimPeriodIndexIn, loggingEnabled, autoSkimLogger, odDistance);
    	
    	mcDmuObject.setTransitLogSum( WTD, true, logsumIn);
    	
    }

    private void setDtwTourMcDmuAttributes( TourModeChoiceDMU mcDmuObject, int origMgra, int destMgra, int departPeriod, int arrivePeriod, boolean loggingEnabled )
    {
    	//setup best path dmu variables
    	TransitWalkAccessDMU walkDmu =  new TransitWalkAccessDMU();
    	walkDmu.setTransitFareDiscounts(bestPathUEC.getTransitFareDiscounts());
    	TransitDriveAccessDMU driveDmu  = new TransitDriveAccessDMU();
    	
    	// drive access, walk egress transit, outbound
        int skimPeriodIndexOut = ModelStructure.getSkimPeriodIndex(departPeriod);
        int pTaz = mgraManager.getTaz(origMgra);
        int aTaz = mgraManager.getTaz(destMgra);
        float odDistance = (float) anm.getTazDistanceFromTaz(pTaz, ModelStructure.AM_SKIM_PERIOD_INDEX)[aTaz];
        	
    	//set person specific variables
    	walkDmu.setApplicationType(bestPathUEC.APP_TYPE_TOURMC);
    	walkDmu.setTourCategoryIsJoint(mcDmuObject.getTourCategoryJoint());
    	walkDmu.setPersonType(mcDmuObject.getTourCategoryJoint()==1 ? walkDmu.personType : mcDmuObject.getPersonType());
    	walkDmu.setValueOfTime((float) mcDmuObject.getValueOfTime());
    	walkDmu.setFareSubsidy(mcDmuObject.getFareSubsidy());
    	
      	driveDmu.setApplicationType(bestPathUEC.APP_TYPE_TOURMC);
        driveDmu.setTourCategoryIsJoint(mcDmuObject.getTourCategoryJoint());
    	driveDmu.setPersonType(mcDmuObject.getTourCategoryJoint()==1 ? driveDmu.personType : mcDmuObject.getPersonType());
    	driveDmu.setValueOfTime((float)mcDmuObject.getValueOfTime());
    	
    	// In the Tap version, logsumXX is the logsum of N best transit paths (N Tap pairs)
    	// In the non-Tap version, we keep the logsumXX name unchanged even though it is really just the transit utility between one TAZ pair
    	double logsumOut = bestPathUEC.calcPersonSpecificUtilities(pTaz, aTaz, walkDmu, driveDmu, DTW, origMgra, destMgra, skimPeriodIndexOut, loggingEnabled, autoSkimLogger, odDistance);
    	
    	mcDmuObject.setTransitLogSum( DTW, false, logsumOut);
        
    	// logsum for DTW inbound is never used -> set to NA
    	mcDmuObject.setTransitLogSum( DTW, true, bestPathUEC.NA );
        
    }

    private void setNmTripMcDmuAttributes( TripModeChoiceDMU tripMcDmuObject, int origMgra, int destMgra, int departPeriod, boolean loggingEnabled )
    {

        double[] nmSkims = null;
        
        // non-motorized, outbound then inbound
        int skimPeriodIndex = ModelStructure.getSkimPeriodIndex(departPeriod);
        departPeriod = skimPeriodIndex;
        nmSkims = anm.getNonMotorizedSkims(origMgra, destMgra, departPeriod, loggingEnabled, autoSkimLogger);
        if (loggingEnabled)
            anm.logReturnedSkims(origMgra, destMgra, departPeriod, nmSkims, "non-motorized trip mode choice skims", autoSkimLogger);
    
        int walkIndex = anm.getNmWalkTimeSkimIndex();
        tripMcDmuObject.setNonMotorizedWalkTime(nmSkims[walkIndex] );
    
        int bikeIndex = anm.getNmBikeTimeSkimIndex();
        tripMcDmuObject.setNonMotorizedBikeTime(nmSkims[bikeIndex] );
        
    }
    
    public void setWtwTripMcDmuAttributes( TripModeChoiceDMU tripMcDmuObject, int origMgra, int destMgra, int departPeriod, boolean loggingEnabled )
    {
    	//setup best path dmu variables
    	TransitWalkAccessDMU walkDmu =  new TransitWalkAccessDMU();
    	walkDmu.setTransitFareDiscounts(bestPathUEC.getTransitFareDiscounts());
    	TransitDriveAccessDMU driveDmu  = new TransitDriveAccessDMU();
    	
        // walk access and walk egress for transit segment
        int skimPeriodIndex = ModelStructure.getSkimPeriodIndex(departPeriod);
        int pTaz = mgraManager.getTaz(origMgra);
        int aTaz = mgraManager.getTaz(destMgra);
        float odDistance = (float) anm.getTazDistanceFromTaz(pTaz, ModelStructure.AM_SKIM_PERIOD_INDEX)[aTaz];
        
        //set person specific variables
    	walkDmu.setApplicationType(bestPathUEC.APP_TYPE_TRIPMC);
    	walkDmu.setTourCategoryIsJoint(tripMcDmuObject.getTourCategoryJoint());
    	walkDmu.setPersonType(tripMcDmuObject.getTourCategoryJoint()==1 ? walkDmu.personType : tripMcDmuObject.getPersonType());
    	walkDmu.setValueOfTime((float)tripMcDmuObject.getValueOfTime());
    	walkDmu.setFareSubsidy(tripMcDmuObject.getFareSubsidy());
    	
    	driveDmu.setApplicationType(bestPathUEC.APP_TYPE_TRIPMC);
    	driveDmu.setTourCategoryIsJoint(tripMcDmuObject.getTourCategoryJoint());
    	driveDmu.setPersonType(tripMcDmuObject.getTourCategoryJoint()==1 ? driveDmu.personType : tripMcDmuObject.getPersonType());
    	driveDmu.setValueOfTime((float)tripMcDmuObject.getValueOfTime());
    	
    	// In the Tap version, logsumXX is the logsum of N best transit paths (N Tap pairs)
    	// In the non-Tap version, we keep the logsumXX name unchanged even though it is really just the transit utility between one TAZ pair
    	double logsum = bestPathUEC.calcPersonSpecificUtilities(pTaz, aTaz, walkDmu, driveDmu, WTW, origMgra, destMgra, skimPeriodIndex, loggingEnabled, autoSkimLogger, odDistance);
        
        tripMcDmuObject.setTransitLogSum( WTW, logsum);
        
    }
    
    public void setWtdTripMcDmuAttributes( TripModeChoiceDMU tripMcDmuObject, int origMgra, int destMgra, int departPeriod, boolean loggingEnabled )
    {
    	//setup best path dmu variables
    	TransitWalkAccessDMU walkDmu =  new TransitWalkAccessDMU();
    	walkDmu.setTransitFareDiscounts(bestPathUEC.getTransitFareDiscounts());
    	TransitDriveAccessDMU driveDmu  = new TransitDriveAccessDMU();
    	
        // walk access, drive egress transit, outbound
        int skimPeriodIndex = ModelStructure.getSkimPeriodIndex(departPeriod);
        int pTaz = mgraManager.getTaz(origMgra);
        int aTaz = mgraManager.getTaz(destMgra);
        float odDistance = (float) anm.getTazDistanceFromTaz(pTaz, ModelStructure.AM_SKIM_PERIOD_INDEX)[aTaz];
        
        walkDmu.setApplicationType(bestPathUEC.APP_TYPE_TRIPMC);
    	walkDmu.setTourCategoryIsJoint(tripMcDmuObject.getTourCategoryJoint());
    	walkDmu.setPersonType(tripMcDmuObject.getTourCategoryJoint()==1 ? walkDmu.personType : tripMcDmuObject.getPersonType());
    	walkDmu.setValueOfTime((float)tripMcDmuObject.getValueOfTime());
    	walkDmu.setFareSubsidy(tripMcDmuObject.getFareSubsidy());
    	
    	driveDmu.setApplicationType(bestPathUEC.APP_TYPE_TRIPMC);
    	driveDmu.setTourCategoryIsJoint(tripMcDmuObject.getTourCategoryJoint());
    	driveDmu.setPersonType(tripMcDmuObject.getTourCategoryJoint()==1 ? driveDmu.personType : tripMcDmuObject.getPersonType());
    	driveDmu.setValueOfTime((float)tripMcDmuObject.getValueOfTime());
    	
    	// In the Tap version, logsumXX is the logsum of N best transit paths (N Tap pairs)
    	// In the non-Tap version, we keep the logsumXX name unchanged even though it is really just the transit utility between one TAZ pair
    	double logsum = bestPathUEC.calcPersonSpecificUtilities(pTaz, aTaz, walkDmu, driveDmu, WTD, origMgra, destMgra, skimPeriodIndex, loggingEnabled, autoSkimLogger, odDistance);
        
        tripMcDmuObject.setTransitLogSum( WTD, logsum);
        
    }
    
    public void setDtwTripMcDmuAttributes( TripModeChoiceDMU tripMcDmuObject, int origMgra, int destMgra, int departPeriod, boolean loggingEnabled )
    {
    	//setup best path dmu variables
    	TransitWalkAccessDMU walkDmu =  new TransitWalkAccessDMU();
    	walkDmu.setTransitFareDiscounts(bestPathUEC.getTransitFareDiscounts());
    	TransitDriveAccessDMU driveDmu  = new TransitDriveAccessDMU();
    	
        // drive access, walk egress transit, outbound
        int skimPeriodIndex = ModelStructure.getSkimPeriodIndex(departPeriod);
        int pTaz = mgraManager.getTaz(origMgra);
        int aTaz = mgraManager.getTaz(destMgra);
        float odDistance = (float) anm.getTazDistanceFromTaz(pTaz, ModelStructure.AM_SKIM_PERIOD_INDEX)[aTaz];
        
        //set person specific variables
        walkDmu.setApplicationType(bestPathUEC.APP_TYPE_TRIPMC);
    	walkDmu.setTourCategoryIsJoint(tripMcDmuObject.getTourCategoryJoint());
    	walkDmu.setPersonType(tripMcDmuObject.getTourCategoryJoint()==1 ? walkDmu.personType : tripMcDmuObject.getPersonType());
    	walkDmu.setValueOfTime((float)tripMcDmuObject.getValueOfTime());
    	walkDmu.setFareSubsidy(tripMcDmuObject.getFareSubsidy());
    	
    	driveDmu.setApplicationType(bestPathUEC.APP_TYPE_TRIPMC);
    	driveDmu.setTourCategoryIsJoint(tripMcDmuObject.getTourCategoryJoint());
    	driveDmu.setPersonType(tripMcDmuObject.getTourCategoryJoint()==1 ? driveDmu.personType : tripMcDmuObject.getPersonType());
    	driveDmu.setValueOfTime((float)tripMcDmuObject.getValueOfTime());
    	
    	// In the Tap version, logsumXX is the logsum of N best transit paths (N Tap pairs)
    	// In the non-Tap version, we keep the logsumXX name unchanged even though it is really just the transit utility between one TAZ pair
    	double logsum = bestPathUEC.calcPersonSpecificUtilities(pTaz, aTaz, walkDmu, driveDmu, DTW, origMgra, destMgra, skimPeriodIndex, loggingEnabled, autoSkimLogger, odDistance);
        
        tripMcDmuObject.setTransitLogSum( DTW, logsum);
        
    }
    
}
