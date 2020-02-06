package com.pb.mtctm2.abm.ctramp;

import com.pb.common.datafile.OLD_CSVFileReader;
import com.pb.common.datafile.TableDataSet;
import com.pb.common.util.ResourceUtil;
import com.pb.common.datafile.CSVFileReader;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.io.Serializable;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.ResourceBundle;
import java.util.Set;
import java.util.StringTokenizer;
import java.util.TreeMap;
import java.util.TreeSet;

import org.apache.log4j.Logger;

import com.pb.mtctm2.abm.ctramp.CtrampApplication;
import com.pb.mtctm2.abm.ctramp.Constants;
import com.pb.mtctm2.abm.ctramp.TazDataManager;
import com.pb.mtctm2.abm.ctramp.Modes.AccessMode;

/**
 * This class is used for ...
 * 
 * @author Christi Willison
 * @version Sep 4, 2008
 *          <p/>
 *          Created by IntelliJ IDEA.
 * 
 *          Edited JEF May 2009
 */
public final class MgraDataManager
        implements Serializable
{

    private static MgraDataManager      instance;
    protected transient Logger          logger = Logger.getLogger(MgraDataManager.class);

    public static double                MAX_PARKING_WALK_DISTANCE;  
    private int                         LOG_MGRA;

    // create Strubg variables for the 4D land use data file field names
    public static final String          MGRA_4DDENSITY_DU_DEN_FIELD      = "DUDen";
    public static final String          MGRA_4DDENSITY_EMP_DEN_FIELD     = "EmpDen";
    public static final String          MGRA_4DDENSITY_TOT_INT_FIELD     = "TotInt";

    public static final String          MGRA_FIELD_NAME                                  = "MAZ";
    public static final String          MGRA_TAZ_FIELD_NAME                              = "TAZ";
    private static final String         MGRA_POPULATION_FIELD_NAME                       = "pop";
    private static final String         MGRA_HOUSEHOLDS_FIELD_NAME                       = "hh";
    private static final String         MGRA_GRADE_SCHOOL_ENROLLMENT_FIELD_NAME          = "EnrollGradeKto8";
    private static final String         MGRA_HIGH_SCHOOL_ENROLLMENT_FIELD_NAME           = "EnrollGrade9to12";
    private static final String         MGRA_UNIVERSITY_ENROLLMENT_FIELD_NAME            = "collegeEnroll";
    private static final String         MGRA_OTHER_COLLEGE_ENROLLMENT_FIELD_NAME         = "otherCollegeEnroll";
    private static final String         MGRA_ADULT_SCHOOL_ENROLLMENT_FIELD_NAME          = "AdultSchEnrl";
    private static final String         MGRA_GRADE_SCHOOL_DISTRICT_FIELD_NAME            = "ech_dist";
    private static final String         MGRA_HIGH_SCHOOL_DISTRICT_FIELD_NAME             = "hch_dist";
    public static final String         MGRA_COUNTY_FIELD_NAME                           = "CountyID";

    private static final String PROPERTIES_PARKING_COST_OUTPUT_FILE = "mgra.avg.cost.output.file";
    
    public static final String PROPERTIES_MGRA_DATA_FILE = "mgra.socec.file";
    private static final String MGRA_DISTANCE_COEFF_WORK = "mgra.avg.cost.dist.coeff.work";
    private static final String MGRA_DISTANCE_COEFF_OTHER = "mgra.avg.cost.dist.coeff.other";
    private static final String LOG_MGRA_PARKCOST = "mgra.avg.cost.trace.zone";
    public static final String PROPERTIES_MAX_WALK_DIST = "mgra.max.parking.distance";

    public static final int PARK_AREA_ONE = 1;
    private static final String MGRA_PARKAREA_FIELD   = "parkarea";
    private static final String MGRA_HSTALLSOTH_FIELD = "hstallsoth";
    private static final String MGRA_HSTALLSSAM_FIELD = "hstallssam";
    private static final String MGRA_HPARKCOST_FIELD  = "hparkcost";
    private static final String MGRA_NUMFREEHRS_FIELD = "numfreehrs";
    private static final String MGRA_DSTALLSOTH_FIELD = "dstallsoth";
    private static final String MGRA_DSTALLSSAM_FIELD = "dstallssam";
    private static final String MGRA_DPARKCOST_FIELD  = "dparkcost";
    private static final String MGRA_MSTALLSOTH_FIELD = "mstallsoth";
    private static final String MGRA_MSTALLSSAM_FIELD = "mstallssam";
    private static final String MGRA_MPARKCOST_FIELD  = "mparkcost";
    
    //for TNC and Taxi wait time calculations
    private static final String MGRA_POPEMPPERSQMI_FIELD = "PopEmpDenPerMi";
    
    
    private ArrayList<Integer>          mgras  = new ArrayList<Integer>();
    private int                         maxMgra;

    private int                         maxTap;
    private int                         nMgrasWithWlkTaps;
    // [mgra], [0=tapID, 1=Distance], [tap number (0-number of taps)]
    private int[][][]                   mgraWlkTapsDistArray;
    private int[]                       mgraTaz;
    private float                       maxWalkTapDistMi = 1.25f;  

    // An array of Hashmaps dimensioned by origin mgra, with distance in feet, in a ragged
    // array (no key for mgra means no other mgras in walk distance)
    private HashMap<Integer, Integer>[] oMgraWalkDistance;

    // An array of Hashmaps dimensioned by destination mgra, with distance in feet, in a ragged
    // array (no key for mgra means no other mgras in walk distance)
    private HashMap<Integer, Integer>[] dMgraWalkDistance;
    

    private HashMap<Integer, Integer>[] oMgraBikeDistance;
    private HashMap<Integer, Integer>[] dMgraBikeDistance;

    // An array dimensioned to maxMgra of ragged arrays of lists of TAPs accessible by driving
    private Set<Integer>[]              driveAccessibleTaps;
    private Set<Integer>[]              walkAccessibleTaps;

    private TableDataSet                mgraTableDataSet;
    
    private HashMap<Integer,Integer>    mgraDataTableMgraRowMap; 

    private double[]                    duDen;
    private double[]                    empDen;
    private double[]                    totInt;
    private double[]                    popEmpDenPerSqMi;

    private double[]                    lsWgtAvgCostM;
    private double[]                    lsWgtAvgCostD;
    private double[]                    lsWgtAvgCostH;

    private int[]                       mgraParkArea;
    private int[]                       numfreehrs;
    private int[]                       hstallsoth;
    private int[]                       hstallssam;
    private float[]                     hparkcost;
    private int[]                       dstallsoth;
    private int[]                       dstallssam;
    private float[]                     dparkcost;
    private int[]                       mstallsoth;
    private int[]                       mstallssam;
    private float[]                     mparkcost;
    
    private TableDataSet tapLinesTable;
    private HashMap<Integer,String> taplines;
    
    /**
     * Constructor.
     * 
     * @param rbMap A HashMap created from a resourcebundle with model properties.
     * 
     */
    private MgraDataManager(HashMap<String, String> rbMap)
    {
        logger.info("MgraDataManager Started");
        
        if(rbMap.containsKey("maz.tap.maxWalkTapDistInMiles")){
        
        	maxWalkTapDistMi = Util.getFloatValueFromPropertyMap(rbMap, "maz.tap.maxWalkTapDistInMiles");
        }
        
        readMgraTableData(rbMap);
        
        //read maz to tap and trim set 
        readMgraWlkTaps(rbMap);
        
        
        //trim tap lines
        boolean trimTapSet = Util.getBooleanValueFromPropertyMap(rbMap, "maz.tap.trimTapSet");
        if(trimTapSet){
        	readTapLines(rbMap);
        	trimTapSet();
        }
        
        readMazMazWalkDistance(rbMap);
        readMazMazBikeDistance(rbMap);

        // pre-process the list of TAPS reachable by drive access for each MGRA 
        mapDriveAccessTapsToMgras( TazDataManager.getInstance(rbMap) );
        
        // create arrays from 4ddensity fields added to MGRA table used by TourModeChoice DMU methods
        process4ddensityData(rbMap);
        
        calculateMgraAvgParkingCosts( rbMap );
        
        printMgraStats();
    }

    /**
     * Get a static instance of the Mgra data manager. Creates one if it is not
     * initialized.
     * 
     * @param rb A resourcebundle with appropriate property settings.
     * 
     * @return A static instance of the MGRA data manager.
     */
    public static MgraDataManager getInstance(HashMap<String, String> rbMap)
    {
        if (instance == null)
        {
            instance = new MgraDataManager(rbMap);
            return instance;
        } else return instance;
    }

    /**
     * This method should only be used after the getInstance(ResourceBundle rb)
     * method has been called since the rb is needed to read in all the data and
     * populate the object. This method will return the instance that has already
     * been populated.
     * 
     * @return instance
     * @throws RuntimeException
     */
    public static MgraDataManager getInstance()
    {
        if (instance == null)
        {
            throw new RuntimeException( "Must instantiate MgraDataManager with the getInstance(rb) method first" );
        } else
        {
            return instance;
        }
    }

    /**
     * read tap lines table (tap, line names served)
     * @param rbMap
     */
    public void readTapLines(HashMap<String, String> rbMap) {
    	
    	File tapLinesTableFile = Paths.get(Util.getStringValueFromPropertyMap(rbMap, "scenario.path"),
                Util.getStringValueFromPropertyMap(rbMap, "maz.tap.tapLines")).toFile();
        try {
        	CSVFileReader csvReader = new CSVFileReader();
        	tapLinesTable = csvReader.readFile( tapLinesTableFile);
        } catch (IOException e) {
        	throw new RuntimeException();
        }
        
    	//get tap lines table field names
        int[] tapLinesTapIds = tapLinesTable.getColumnAsInt("TAP");
        String[] linesForTap = tapLinesTable.getColumnAsString("LINES");
        
        //create lookups
        taplines = new HashMap<Integer,String>();
        for(int i=0; i<tapLinesTapIds.length; i++) {
        	taplines.put(tapLinesTapIds[i], linesForTap[i]);
        }
    }
    
    /**
     * trim the near tap set by origin/destination by only including the nearest tap when more than one tap serves the same line.
     */
    public void trimTapSet() {
    	
    	//mgraWlkTapsDistArray[maz], [2] ([0] = taps, [1]=distances), []
    	
	    int mazToTaps = 0;
	    int trimmedTaps = 0; 
	    
        //loop thru mazs	    
	    for (int i=0; i < mgraWlkTapsDistArray.length; i++) {
	    	
	    	//skip mazs with no taps
	    	if(mgraWlkTapsDistArray[i][0] != null) {
	    		
	    		//get taps and distances
		    	int[] taps = mgraWlkTapsDistArray[i][0];
		    	int[] distances = mgraWlkTapsDistArray[i][1];
		    	
		    	ArrayList<Maz2Tap> maz2TapData = new ArrayList<Maz2Tap>();
		    	for (int j=0; j <taps.length; j++) {
		    	
		    	  //setup data
	    		  Maz2Tap m2t = new Maz2Tap();
	    		  m2t.tap = taps[j];
	    		  m2t.dist = distances[j];
	    		  if(taplines.containsKey(m2t.tap)) { //else drop tap from list
	    			  m2t.lines = taplines.get(m2t.tap).split(" ");
	    		  }  
	    		  maz2TapData.add(m2t);
	    		  
		    	}
		    	
		    	//sort by distance and check for new lines
				Collections.sort(maz2TapData);
				HashMap<String,String> linesServed = new HashMap<String,String>();
				for (Maz2Tap m2t : maz2TapData) {
					
					//skip if no lines served
					if(m2t.lines != null) {
					
						for (int k=0; k<m2t.lines.length; k++) {
							if(linesServed.containsKey(m2t.lines[k]) == false) {
								m2t.servesNewLines = true;
								linesServed.put(m2t.lines[k], m2t.lines[k]);
							}
						}
					}
		    	}
		    	
				//remove unused taps
				ArrayList<Integer> tapsToRemove = new ArrayList<Integer>();
				for (Maz2Tap m2t : maz2TapData) {
					mazToTaps = mazToTaps + 1;
					if( m2t.servesNewLines == false) {
						tapsToRemove.add(m2t.tap);
						trimmedTaps = trimmedTaps + 1;
					}
				}
				
				int[] finalTaps = new int[taps.length-tapsToRemove.size()];
				int[] finalDistances = new int[taps.length-tapsToRemove.size()];
				
				int tapCounter = 0;
				for (int m=0; m<taps.length; m++) {
					if(!tapsToRemove.contains(taps[m])) {
						finalTaps[tapCounter] = taps[m];
						finalDistances[tapCounter] = distances[m];
						tapCounter = tapCounter + 1;
					}
				}
				
				//update data structures
		    	mgraWlkTapsDistArray[i][0] = finalTaps;
		    	mgraWlkTapsDistArray[i][1] = finalDistances;
	    		
	    	}
	    	
	    }

	    logger.info("Removed " + trimmedTaps + " of " + mazToTaps + " Maz tap pairs since servesNewLines=false");

    }
  
    
    /**
     * Read the walk-transit taps for mgras.
     * 
     * @param rb The resourcebundle with the scenario.path and
     *            mgra.wlkacc.taps.and.distance.file properties.
     */
    public void readMgraWlkTaps(HashMap<String, String> rbMap) {
        File mgraWlkTapCorresFile = Paths.get(Util.getStringValueFromPropertyMap(rbMap, "scenario.path"),
                		                      Util.getStringValueFromPropertyMap(rbMap, "maz.tap.distance.file")).toFile();

        Map<Integer,Map<Integer,Integer>> mgraToTapToDistance = new TreeMap<>();
        try (BufferedReader reader = new BufferedReader(new FileReader(mgraWlkTapCorresFile))) {
        	String line;
        	while ((line = reader.readLine()) != null) {
				line = line.trim();
				if (line.length() == 0)
					continue;
				String[] data = line.split(",");
        		//10001,90002,90002,43053.39,11689.23
        		//maz,tap,tap,generalized cost,distance in feet
        		int maz = Integer.parseInt(data[0]);
        		int tap = Integer.parseInt(data[1]);
        		int distance = new Double(data[4]).intValue();
        		
        		if(((float)distance) > (maxWalkTapDistMi * 5280.0))
        			continue;
        		
        		if (!mgraToTapToDistance.containsKey(maz)) 
        			mgraToTapToDistance.put(maz,new TreeMap<Integer,Integer>());
        		mgraToTapToDistance.get(maz).put(tap,distance);
        		if (tap > maxTap) 
        			maxTap = tap;
        	}
        } catch (IOException e) {
			throw new RuntimeException(e);
		}

        nMgrasWithWlkTaps = mgraToTapToDistance.size();
        mgraWlkTapsDistArray = new int[maxMgra + 1][2][];
        for (int maz : mgraToTapToDistance.keySet()) {
        	Map<Integer,Integer> tapToDistance = mgraToTapToDistance.get(maz);
        	int[] taps = new int[tapToDistance.size()];
        	int[] distances = new int[taps.length];
        	mgraWlkTapsDistArray[maz][0] = taps;
        	mgraWlkTapsDistArray[maz][1] = distances;
        	int counter = 0;
        	for (int tap : tapToDistance.keySet()) {
        		taps[counter] = tap;
        		distances[counter++] = tapToDistance.get(tap);
        	}
        }
    }

    private void readMazMazWalkDistance(HashMap<String, String> rbMap) {
        File mazMazDistanceFile = Paths.get(Util.getStringValueFromPropertyMap(rbMap, "scenario.path"),
                		                      Util.getStringValueFromPropertyMap(rbMap, "maz.maz.distance.file")).toFile();
        oMgraWalkDistance = new HashMap[maxMgra + 1];
        dMgraWalkDistance = new HashMap[maxMgra + 1];
        readMazMazDistance(mazMazDistanceFile,oMgraWalkDistance,dMgraWalkDistance);
    }

    private void readMazMazBikeDistance(HashMap<String, String> rbMap) {
        File mazMazDistanceFile = Paths.get(Util.getStringValueFromPropertyMap(rbMap, "scenario.path"),
                		                      Util.getStringValueFromPropertyMap(rbMap, "maz.maz.bike.distance.file")).toFile();
        oMgraBikeDistance = new HashMap[maxMgra + 1];
        dMgraBikeDistance = new HashMap[maxMgra + 1];
        readMazMazDistance(mazMazDistanceFile,oMgraBikeDistance,dMgraBikeDistance);
    }
    
    /** 
     * THis method reads the MAZ to MAZ distance file. The format of the file is:
     * 
     *   from_maz, to_maz, to_maz, generalized cost, distance in feet.
     * 
     * There is no header record. Note that there are no intrazonal MAZ distances in the file so this method calculates 
     * the intraMAZ distance as half the distance to the nearest neighbor.
     * 
     * @param mazMazDistanceFile
     * @param oDistance
     * @param dDistance
     */
    private void readMazMazDistance(File mazMazDistanceFile, HashMap[] oDistance, HashMap[] dDistance) {
        
    	HashMap<Integer, Integer> minDistanceMap = new HashMap<Integer, Integer>(); 
    	try (BufferedReader reader = new BufferedReader(new FileReader(mazMazDistanceFile))) {
        	String line;
        	
        	while ((line = reader.readLine()) != null) {
				line = line.trim();
				if (line.length() == 0)
					continue;
				String[] data = line.split(",");
        		//10001,90002,90002,43053.39,11689.23
        		//maz,maz,maz,generalized cost,distance in feet
        		int fmaz = Integer.parseInt(data[0]);
        		int tmaz = Integer.parseInt(data[1]);
        		int distance = new Double(data[4]).intValue();
        		if (oDistance[fmaz] == null)
        			oDistance[fmaz] = new HashMap();
        		oDistance[fmaz].put(tmaz,distance);
        		if (dDistance[tmaz] == null)
        			dDistance[tmaz] = new HashMap();
        		dDistance[tmaz].put(fmaz,distance);
        		
        		//store minimum distance from (strange but the walk file is asymmetrical)
        		if(minDistanceMap.containsKey(fmaz)){
        			int minDist = minDistanceMap.get(fmaz);
        			if(distance < minDist )
        				minDistanceMap.put(fmaz,distance);
        		}else{
        			minDistanceMap.put(fmaz,distance);
        		}
        		
           		//store minimum distance to (strange but the walk file is asymmetrical)
        		if(minDistanceMap.containsKey(tmaz)){
        			int minDist = minDistanceMap.get(tmaz);
        			if(distance < minDist )
        				minDistanceMap.put(tmaz,distance);
        		}else{
        			minDistanceMap.put(tmaz,distance);
        		}

        	}
        } catch (IOException e) {
			throw new RuntimeException(e);
		}
    	
    	//now add intrazonal distance to arrays
    	for(int maz : minDistanceMap.keySet()){
    		
    		float minDist = (float) minDistanceMap.get(maz);
    		double intraDist = Math.max(minDist/2.0,100.0); // at least 100 feet
    		
    		if (oDistance[maz] == null)
    			oDistance[maz] = new HashMap();
    		oDistance[maz].put(maz, (int)(intraDist+0.5));
    		if (dDistance[maz] == null)
    			dDistance[maz] = new HashMap();
    		dDistance[maz].put(maz, (int)(intraDist+0.5));
   		
    	}
    }

    /**
     * Return an int array of mgras within walking distance of this mgra.
     * 
     * @param mgra The mgra to look up
     * @return The mgras within walking distance. Null is returned if no mgras are
     *         within walk distance.
     */
    public int[] getMgrasWithinWalkDistanceFrom(int mgra)
    {

        if (oMgraWalkDistance[mgra] == null) return null;

        Set<Integer> keySet = oMgraWalkDistance[mgra].keySet();
        int[] walkMgras = new int[keySet.size()];
        Iterator<Integer> it = keySet.iterator();
        int i = 0;
        while (it.hasNext())
        {
            walkMgras[i] = it.next();
            ++i;
        }
        return walkMgras;

    }

    /**
     * Return an int array of mgras within walking distance of this mgra.
     * 
     * @param mgra The mgra to look up
     * @return The mgras within walking distance. Null is returned if no mgras are
     *         within walk distance.
     */
    public int[] getMgrasWithinWalkDistanceTo(int mgra)
    {

        if (dMgraWalkDistance[mgra] == null) return null;

        Set<Integer> keySet = dMgraWalkDistance[mgra].keySet();
        int[] walkMgras = new int[keySet.size()];
        Iterator<Integer> it = keySet.iterator();
        int i = 0;
        while (it.hasNext())
        {
            walkMgras[i] = it.next();
            ++i;
        }
        return walkMgras;

    }

    /**
     * Return true if mgras are within walking distance of each other.
     * 
     * @param oMgra The from mgra
     * @param dMgra The to mgra
     * @return The mgras are within walking distance - true or false.
     */
    public boolean getMgrasAreWithinWalkDistance(int oMgra, int dMgra)
    {

        if (dMgraWalkDistance[dMgra] == null)
            return false;

        return dMgraWalkDistance[dMgra].containsKey( oMgra );

    }

    /**
     * Get the walk distance from an MGRA to a TAP.
     * 
     * @param mgra The number of the destination MGRA.
     * @param pos The position of the TAP in the MGRA array (0+)
     * @return The walk distance in feet.
     */
    public float getMgraToTapWalkDist(int mgra, int pos)
    {
        return mgraWlkTapsDistArray[mgra][1][pos]; // [1] = distance
    }

    /**
     * Get the position of the tap in the mgra walk tap array.
     * 
     * @param mgra The mgra to lookup
     * @param tap The tap to lookup
     * @return The position of the tap in the mgra array. -1 is returned if it is an
     *         invalid tap for the mgra, or if the tap is not within walking
     *         distance.
     */
    public int getTapPosition(int mgra, int tap)
    {

        if (mgraWlkTapsDistArray[mgra] != null)
        {
            if (mgraWlkTapsDistArray[mgra][0] != null)
            {
                for (int i = 0; i < mgraWlkTapsDistArray[mgra][0].length; ++i)
                    if (mgraWlkTapsDistArray[mgra][0][i] == tap) return i;
            }
        }

        return -1;

    }

    /**
     * Get the walk time from an MGRA to a TAP.
     * 
     * @param mgra The number of the destination MGRA.
     * @param pos The position of the TAP in the MGRA array (0+)
     * @return The walk time in minutes.
     */
    public float getMgraToTapWalkTime(int mgra, int pos)
    {
        return (float) (mgraWlkTapsDistArray[mgra][1][pos] * Constants.walkMinutesPerFoot);
    }

    
    /**
     * Get the walk time from an MGRA to a TAP.
     * 
     * @param mgra The MGRA
     * @param tap The TAP
     * @return The walk time in minutes, else -1 if there is no walk link between the MGRA and the TAP.
     */
    public float getWalkTimeFromMgraToTap(int mgra, int tap){
    	
    	int tapPosition = getTapPosition(mgra, tap);
    	float time = 0;
    	
    	if(tapPosition==-1){
    		logger.info("Bad Tap Position for Walk Access From MAZ: "+mgra+" to TAP: "+tap);
    		return -1;
    	}
    	else{
    		time = (float) (mgraWlkTapsDistArray[mgra][1][tapPosition] * Constants.walkMinutesPerFoot);
    	}
    	return time;
    }
    
    /**
     * Get the walk distance from an MGRA to an MGRA. Return 0 if not within walking
     * distance.
     * 
     * @param oMgra The number of the production/origin MGRA.
     * @param dMgra The number of the attraction/destination MGRA.
     * @return The walk distance in feet.
     */
    public int getMgraToMgraWalkDistFrom(int oMgra, int dMgra)
    {

        if (oMgraWalkDistance[oMgra] == null)
            return 0;
        else if (oMgraWalkDistance[oMgra].containsKey(dMgra))
            return oMgraWalkDistance[oMgra].get(dMgra);

        return 0;
    }

    /**
     * Get the walk distance from an MGRA to an MGRA. Return 0 if not within walking
     * distance.
     * 
     * @param oMgra The number of the production/origin MGRA.
     * @param dMgra The number of the attraction/destination MGRA.
     * @return The walk distance in feet.
     */
    public int getMgraToMgraWalkDistTo(int oMgra, int dMgra)
    {

        if (dMgraWalkDistance[dMgra] == null)
            return 0;
        else if (dMgraWalkDistance[dMgra].containsKey(oMgra))
            return dMgraWalkDistance[dMgra].get(oMgra);

        return 0;
    }

    /**
     * Get the walk time from an MGRA to an MGRA. Return 0 if not within walking
     * distance.
     * 
     * @param oMgra The number of the production/origin MGRA.
     * @param dMgra The number of the attraction/destination MGRA.
     * @return The walk time in minutes.
     */
    public float getMgraToMgraWalkTime(int oMgra, int dMgra)
    {
    	return (float) (getMgraToMgraWalkDistTo(oMgra,dMgra)*Constants.walkMinutesPerFoot);
    }

    /**
     * Get the bike distance from an MGRA to an MGRA. Return 0 if not within short bike
     * distance.
     * 
     * @param oMgra The number of the production/origin MGRA.
     * @param dMgra The number of the attraction/destination MGRA.
     * @return The bike distance in feet.
     */
    public int getMgraToMgraBikeDistFrom(int oMgra, int dMgra)
    {

        if (oMgraBikeDistance[oMgra] == null)
            return 0;
        else if (oMgraBikeDistance[oMgra].containsKey(dMgra))
            return oMgraBikeDistance[oMgra].get(dMgra);

        return 0;
    }

    /**
     * Get the bike distance from an MGRA to an MGRA. Return 0 if not within bikeing
     * distance.
     * 
     * @param oMgra The number of the production/origin MGRA.
     * @param dMgra The number of the attraction/destination MGRA.
     * @return The bike distance in feet.
     */
    public int getMgraToMgraBikeDistTo(int oMgra, int dMgra)
    {

        if (dMgraBikeDistance[dMgra] == null)
            return 0;
        else if (dMgraBikeDistance[dMgra].containsKey(oMgra))
            return dMgraBikeDistance[dMgra].get(oMgra);

        return 0;
    }

    /**
     * Get the bike time from an MGRA to an MGRA. Return 0 if not within walking
     * distance.
     * 
     * @param oMgra The number of the production/origin MGRA.
     * @param dMgra The number of the attraction/destination MGRA.
     * @return The bike time in minutes.
     */
    public float getMgraToMgraBikeTime(int oMgra, int dMgra)
    {
    	return (float) (getMgraToMgraBikeDistTo(oMgra,dMgra)*Constants.bikeMinutesPerFoot);
    }

    /**
     * Print mgra data to the log file for debugging purposes.
     * 
     */
    public void printMgraStats()
    {
        logger.info("Number of MGRAs: " + mgras.size());
        logger.info("Max MGRA: " + maxMgra);
        logger.info("Max TAP: "+maxTap);

        //logger.info("Number of MGRAs with WalkAccessTaps: " + nMgrasWithWlkTaps);
        //logger.info("Number of TAPs in MGRA 18 (should be 3): "
        //        + mgraWlkTapsDistArray[18][0].length);
        //logger.info("Distance between MGRA 18 and TAP 1648 (should be 2728): "
        //        + mgraWlkTapsDistArray[18][1][1]);
        //logger.info("MGRA 28435 is in what TAZ? (Should be 995)" + mgraTaz[28435]);
        //logger.info("Number of mgras within walk distance of mgra 22573 (Should be 67)"
        //        + getMgrasWithinWalkDistanceFrom(22573).length);

    }

    /**
     * 
     * @param mgra - the zone
     * @return the taz that the tmgra is contained in
     */
    public int getTaz(int mgra)
    {
        return mgraTaz[mgra];
    }

    /**
     * Get the maximum MGRA.
     * 
     * @return The highest MGRA number
     */
    public int getMaxMgra()
    {
        return maxMgra;
    }

    /**
     * Get the maximum TAP.
     * 
     * @return The highest TAP number
     */
    public int getMaxTap()
    {
        return maxTap;
    }

    /**
     * Get the ArrayList of MGRAs
     * 
     * @return ArrayList<Integer> mgras.
     */
    public ArrayList<Integer> getMgras()
    {
        return mgras;
    }

    /**
     * Get the MgraTaz correspondence array. Given an MGRA, returns its TAZ.
     * 
     * @return int[] mgraTaz correspondence array.
     */
    public int[] getMgraTaz()
    {
        return mgraTaz;
    }

    /**
     * Get the array of Taps within walk distance
     * 
     * @return The int[][][] array of Taps within walk distance of MGRAs
     */
    public int[][][] getMgraWlkTapsDistArray()
    {
        return mgraWlkTapsDistArray;
    }

    
    /**
     * get arrays of drive accessible TAPS for each MGRA and populate an array of sets so that later one can
     * determine, for a given mgra, if a tap is contained in the set.
     * 
     * @param args TazDataManager to get TAPs with drive access from TAZs
     */
    public void mapDriveAccessTapsToMgras( TazDataManager tazDataManager )
    {

        walkAccessibleTaps = new TreeSet[maxMgra+1];
        driveAccessibleTaps = new TreeSet[maxMgra+1];
        
        for ( int mgra=1; mgra <= maxMgra; mgra++ ) {
            
            // get the TAZ associated with this MGRA
            int taz = getTaz( mgra );

            // store the array of walk accessible TAPS for this MGRA as a set so that contains can be called on it later
            // to determine, for a given mgra, if a tap is contained in the set.
            int[] mgraSet = getMgraWlkTapsDistArray()[mgra][0];
            if ( mgraSet != null ) {
                walkAccessibleTaps[mgra] = new TreeSet<Integer>();
                for ( int i=0; i < mgraSet.length; i++ )    
                    walkAccessibleTaps[mgra].add( mgraSet[i] );
            }
            
            // store the array of drive accessible TAPS for this MGRA as a set so that contains can be called on it later
            // to determine, for a given mgra, if a tap is contained in the set.
            int[] tapItems = tazDataManager.getParkRideOrKissRideTapsForZone( taz, AccessMode.PARK_N_RIDE );
            if ( tapItems != null ) {
            	driveAccessibleTaps[mgra] = new TreeSet<Integer>();
            	for ( int item : tapItems )    
            		driveAccessibleTaps[mgra].add( item );
            }
            
        }
        
    }
    
    /**
     * @param mgra for which we want to know if TAP can be reached by drive access
     * @param tap for which we want to know if the mgra can reach it by drive access
     * @return true if reachable; false otherwise
     */
    public boolean getTapIsDriveAccessibleFromMgra( int mgra, int tap )
    {
        if ( driveAccessibleTaps[mgra] == null )
            return false;
        else
            return driveAccessibleTaps[mgra].contains( tap );
    }
    
    
    /**
     * @param mgra for which we want to know if TAP can be reached by walk access
     * @param tap for which we want to know if the mgra can reach it by walk access
     * @return true if reachable; false otherwise
     */
    public boolean getTapIsWalkAccessibleFromMgra( int mgra, int tap )
    {
        if ( walkAccessibleTaps[mgra] == null )
            return false;
        else
            return walkAccessibleTaps[mgra].contains( tap );
    }
    

    /**
     * return the duDen value for the mgra
     * @param mgra is the MGRA value for which the duDen value is needed
     * @return duDen[mgra]
     */
    public double getDuDenValue( int mgra ) {
        return duDen[mgra];
    }
    
    /**
     * return the empDen value for the mgra
     * @param mgra is the MGRA value for which the empDen value is needed
     * @return empDen[mgra]
     */
    public double getEmpDenValue( int mgra ) {
        return empDen[mgra];
    }
    
    /**
     * return the totInt value for the mgra
     * @param mgra is the MGRA value for which the totInt value is needed
     * @return totInt[mgra]
     */
    public double getTotIntValue( int mgra ) {
        return totInt[mgra];
    }
    
    public double getPopEmpPerSqMi( int mgra ) {
        return popEmpDenPerSqMi[mgra];
    }
  
    
    /**
     * Process the 4D density land use data file and store the selected fields as arrays indexed by the mgra value.
     * The data fields are in the mgra TableDataSet read from the MGRA csv file.
     * 
     * @param rbMap is a HashMap for the resource bundle generated from the properties file.
     */
    public void process4ddensityData( HashMap<String,String> rbMap )
    {

        try
        {

            // allocate arrays for the land use data fields
            duDen = new double[maxMgra+1];
            empDen = new double[maxMgra+1];
            totInt = new double[maxMgra+1];
            
            //added for Taxi/TNC
            popEmpDenPerSqMi = new double[maxMgra+1];
            
            // get the data fields needed for the mode choice utilities as 0-based double[]
            double[] duDenField = mgraTableDataSet.getColumnAsDouble( MGRA_4DDENSITY_DU_DEN_FIELD );
            double[] empDenField = mgraTableDataSet.getColumnAsDouble( MGRA_4DDENSITY_EMP_DEN_FIELD );
            double[] totIntField = mgraTableDataSet.getColumnAsDouble( MGRA_4DDENSITY_TOT_INT_FIELD );

            double[] popEmpField = mgraTableDataSet.getColumnAsDouble( MGRA_POPEMPPERSQMI_FIELD );
            
            // create a HashMap to convert MGRA values to array indices for the data
            // arrays above
            int mgraCol = mgraTableDataSet.getColumnPosition( MGRA_FIELD_NAME );

            for (int row = 1; row <= mgraTableDataSet.getRowCount(); row++) {
                
                int mgra = (int) mgraTableDataSet.getValueAt(row, mgraCol);
                duDen[mgra] = duDenField[row-1];
                empDen[mgra] = empDenField[row-1];
                totInt[mgra] = totIntField[row-1];
                popEmpDenPerSqMi [mgra] = popEmpField[row-1];
                
            }

        } catch (Exception e)
        {
            logger.error(String.format( "Exception occurred processing 4ddensity data file from mgraData TableDataSet object." ), e );
            throw new RuntimeException();
        }

    }

    
    private void readMgraTableData( HashMap<String,String> rbMap ) {
        
        // get the mgra data table from one of these UECs.
        String projectPath = rbMap.get(CtrampApplication.PROPERTIES_PROJECT_DIRECTORY);
        String mgraFile = rbMap.get(PROPERTIES_MGRA_DATA_FILE);
        mgraFile = projectPath + mgraFile;

        try {
            OLD_CSVFileReader reader = new OLD_CSVFileReader();
            mgraTableDataSet = reader.readFile(new File(mgraFile));
        }
        catch (IOException e) {
            logger.error ("problem reading mgra data table for MgraDataManager.", e);
            System.exit(1);
        }
      
        
        HashMap<Integer, Integer> tazs = new HashMap<Integer, Integer>();

        // create a HashMap between mgra values and the corresponding row number in the mgra TableDataSet.
        mgraDataTableMgraRowMap = new HashMap<Integer,Integer>(); 
        maxMgra = 0;
        for (int i=1; i <= mgraTableDataSet.getRowCount(); i++) {
            int mgra = (int)mgraTableDataSet.getValueAt(i, MGRA_FIELD_NAME);
            int taz = (int)mgraTableDataSet.getValueAt(i, MGRA_TAZ_FIELD_NAME);
            mgraDataTableMgraRowMap.put(mgra, i);

            if (mgra > maxMgra)
                maxMgra = mgra;
            mgras.add(mgra);
            tazs.put(mgra, taz);

        }
         
        mgraTaz = new int[maxMgra + 1];
        for ( int mgra : mgras )
            mgraTaz[mgra] = tazs.get(mgra);

    }

    /**
     * @param mgra for which table data is desired
     * @return population for the specified mgra.
     */
    public double getMgraPopulation(int mgra)
    {
        int row = mgraDataTableMgraRowMap.get(mgra);
        return mgraTableDataSet.getValueAt(row, MGRA_POPULATION_FIELD_NAME);
    }

    /**
     * @param mgra for which table data is desired
     * @return households for the specified mgra.
     */
    public double getMgraHouseholds(int mgra)
    {
        int row = mgraDataTableMgraRowMap.get(mgra);
        return mgraTableDataSet.getValueAt(row, MGRA_HOUSEHOLDS_FIELD_NAME);
    }

    /**
     * @param mgra for which table data is desired
     * @return grade school enrollment for the specified mgra.
     */
    public double getMgraGradeSchoolEnrollment(int mgra)
    {
        int row = mgraDataTableMgraRowMap.get(mgra);
        return mgraTableDataSet.getValueAt(row, MGRA_GRADE_SCHOOL_ENROLLMENT_FIELD_NAME);
    }

    /**
     * @param mgra for which table data is desired
     * @return high school enrollment for the specified mgra.
     */
    public double getMgraHighSchoolEnrollment(int mgra)
    {
        int row = mgraDataTableMgraRowMap.get(mgra);
        return mgraTableDataSet.getValueAt(row, MGRA_HIGH_SCHOOL_ENROLLMENT_FIELD_NAME);
    }

    /**
     * @param mgra for which table data is desired
     * @return university enrollment for the specified mgra.
     */
    public double getMgraUniversityEnrollment(int mgra)
    {
        int row = mgraDataTableMgraRowMap.get(mgra);
        return mgraTableDataSet.getValueAt(row, MGRA_UNIVERSITY_ENROLLMENT_FIELD_NAME);
    }

    /**
     * @param mgra for which table data is desired
     * @return other college enrollment for the specified mgra.
     */
    public double getMgraOtherCollegeEnrollment(int mgra)
    {
        int row = mgraDataTableMgraRowMap.get(mgra);
        return mgraTableDataSet.getValueAt(row, MGRA_OTHER_COLLEGE_ENROLLMENT_FIELD_NAME);
    }

    /**
     * @param mgra for which table data is desired
     * @return adult school enrollment for the specified mgra.
     */
    public double getMgraAdultSchoolEnrollment(int mgra)
    {
        int row = mgraDataTableMgraRowMap.get(mgra);
        return mgraTableDataSet.getValueAt(row, MGRA_ADULT_SCHOOL_ENROLLMENT_FIELD_NAME);
    }

    /**
     * @param mgra for which table data is desired
     * @return grade school district for the specified mgra.
     */
    public int getMgraGradeSchoolDistrict(int mgra)
    {
        int row = mgraDataTableMgraRowMap.get(mgra);
        return (int)mgraTableDataSet.getValueAt(row, MGRA_GRADE_SCHOOL_DISTRICT_FIELD_NAME);
    }

    /**
     * @param mgra for which table data is desired
     * @return high school district for the specified mgra.
     */
    public int getMgraHighSchoolDistrict(int mgra)
    {
        int row = mgraDataTableMgraRowMap.get(mgra);
        return (int)mgraTableDataSet.getValueAt(row, MGRA_HIGH_SCHOOL_DISTRICT_FIELD_NAME);
    }


    public HashMap<Integer,Integer> getMgraDataTableMgraRowMap() {
        return mgraDataTableMgraRowMap;
    }
    
    
    public TableDataSet getMgraTableDataSet() {
		return mgraTableDataSet;
	}

  	public int getCountyId(int mgra){
		
        int row = mgraDataTableMgraRowMap.get(mgra);
        return (int)mgraTableDataSet.getValueAt(row, MGRA_COUNTY_FIELD_NAME);

	}

	
	private void calculateMgraAvgParkingCosts( HashMap<String,String> propertyMap ) {
        
        // open output file to write average parking costs for each mgra
        PrintWriter out = null;

        String projectPath = propertyMap.get(CtrampApplication.PROPERTIES_PROJECT_DIRECTORY);
        String outFile = propertyMap.get(PROPERTIES_PARKING_COST_OUTPUT_FILE);
        outFile = projectPath + outFile;

        try {
            out = new PrintWriter( new BufferedWriter( new FileWriter( new File( outFile ) ) ) );
        }
        catch (IOException e) {
            e.printStackTrace();
        }

        // write the header record
        out.println( "mgra,mgraParkArea,lsWgtAvgCostM,lsWgtAvgCostD,lsWgtAvgCostH" );
        
        //get max parking cost
        MAX_PARKING_WALK_DISTANCE = Float.parseFloat(propertyMap.get(PROPERTIES_MAX_WALK_DIST) );
        
        // open output files for writing debug info for a specific mgra
        
        // get trace settings from properties file
        LOG_MGRA = Integer.parseInt( propertyMap.get(LOG_MGRA_PARKCOST) );
        
        PrintWriter outM = null;
        PrintWriter outD = null;
        PrintWriter outH = null;

        if ( LOG_MGRA > 0 ) {
            try {
                outM = new PrintWriter( new BufferedWriter( new FileWriter( new File( projectPath + "/mgraAvgParkingCost_" + LOG_MGRA + "_Debug_M.csv" ) ) ) );
                outD = new PrintWriter( new BufferedWriter( new FileWriter( new File( projectPath + "/mgraAvgParkingCost_" + LOG_MGRA + "_Debug_D.csv" ) ) ) );
                outH = new PrintWriter( new BufferedWriter( new FileWriter( new File( projectPath + "/mgraAvgParkingCost_" + LOG_MGRA + "_Debug_H.csv" ) ) ) );
            }
            catch (IOException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }
        }
        
        
        float workDistCoeff = Float.parseFloat( propertyMap.get(MGRA_DISTANCE_COEFF_WORK) );
        float otherDistCoeff = Float.parseFloat( propertyMap.get(MGRA_DISTANCE_COEFF_OTHER) );
        
        int[] mgraField = mgraTableDataSet.getColumnAsInt( MGRA_FIELD_NAME );
        int[] mgraParkAreaField = mgraTableDataSet.getColumnAsInt( MGRA_PARKAREA_FIELD );
        int[] hstallsothField = mgraTableDataSet.getColumnAsInt( MGRA_HSTALLSOTH_FIELD );
        int[] hstallssamField = mgraTableDataSet.getColumnAsInt( MGRA_HSTALLSSAM_FIELD );
        float[] hparkcostField = mgraTableDataSet.getColumnAsFloat( MGRA_HPARKCOST_FIELD );
        int[] numfreehrsField = mgraTableDataSet.getColumnAsInt( MGRA_NUMFREEHRS_FIELD );
        int[] dstallsothField = mgraTableDataSet.getColumnAsInt( MGRA_DSTALLSOTH_FIELD );
        int[] dstallssamField = mgraTableDataSet.getColumnAsInt( MGRA_DSTALLSSAM_FIELD );
        float[] dparkcostField = mgraTableDataSet.getColumnAsFloat( MGRA_DPARKCOST_FIELD );
        int[] mstallsothField = mgraTableDataSet.getColumnAsInt( MGRA_MSTALLSOTH_FIELD );
        int[] mstallssamField = mgraTableDataSet.getColumnAsInt( MGRA_MSTALLSSAM_FIELD );
        float[] mparkcostField = mgraTableDataSet.getColumnAsFloat( MGRA_MPARKCOST_FIELD );

        mgraParkArea = new int[maxMgra+1];
        numfreehrs = new int[maxMgra+1];
        hstallsoth = new int[maxMgra+1];
        hstallssam = new int[maxMgra+1];
        hparkcost = new float[maxMgra+1];
        dstallsoth = new int[maxMgra+1];
        dstallssam = new int[maxMgra+1];
        dparkcost = new float[maxMgra+1];
        mstallsoth = new int[maxMgra+1];
        mstallssam = new int[maxMgra+1];
        mparkcost = new float[maxMgra+1];
        
        lsWgtAvgCostM = new double[maxMgra+1];
        lsWgtAvgCostD = new double[maxMgra+1];
        lsWgtAvgCostH = new double[maxMgra+1];
        
        //loop over mgras in input file - allows for skipped mgras
        for (int k=0; k < mgraField.length; k++ ) { 
            
            // get the mgra value for TableDataSet row k from the mgra field.
            int mgra = mgraField[k];
            
         
            mgraParkArea[mgra] = mgraParkAreaField[k];
            numfreehrs[mgra] = numfreehrsField[k];
            hstallsoth[mgra] = hstallsothField[k];
            hstallssam[mgra] = hstallssamField[k];
            hparkcost[mgra] = hparkcostField[k];
            dstallsoth[mgra] = dstallsothField[k];
            dstallssam[mgra] = dstallssamField[k];
            dparkcost[mgra] = dparkcostField[k];
            mstallsoth[mgra] = mstallsothField[k];
            mstallssam[mgra] = mstallssamField[k];
            mparkcost[mgra] = mparkcostField[k];
        
          // get the array of mgras within walking distance of m
            int[] walkMgras = getMgrasWithinWalkDistanceFrom( mgra );
            
            // park area 1.
            if ( mgraParkAreaField[k] == PARK_AREA_ONE ) {
                      
                // calculate weighted average cost from monthly costs 
                double dist = getMgraToMgraWalkDistFrom( mgra, mgra )/5280.0;
                
                double numeratorM = mstallssamField[k] * Math.exp( workDistCoeff * dist ) * mparkcostField[k];
                double denominatorM = mstallssamField[k] * Math.exp( workDistCoeff * dist );
                
                double numeratorD = dstallssamField[k] * Math.exp( workDistCoeff * dist ) * dparkcostField[k];
                double denominatorD = dstallssamField[k] * Math.exp( workDistCoeff * dist );
                
                double discountFactor = Math.max( 1 - (numfreehrsField[k]/4), 0 );
                double numeratorH = hstallssamField[k] * Math.exp( workDistCoeff * dist ) * discountFactor * hparkcostField[k];
                double denominatorH = hstallssamField[k] * Math.exp( workDistCoeff * dist );

                
                if ( mgra == LOG_MGRA ) {
                    // log the file header
                    outM.println( "wMgra" + "," + "mgraParkArea" + "," + "workDistCoeff*dist" + "," + "exp(workDistCoeff*dist)" + "," + "mstallsoth" + "," + "mparkcost" + "," + "numeratorM" + "," + "denominatorM" );
                    outD.println( "wMgra" + "," + "mgraParkArea" + "," + "otherDistCoeff*dist" + "," + "exp(otherDistCoeff*dist)" + "," + "dstallsoth" + "," + "dparkcost" + "," + "numeratorD" + "," + "denominatorD" );
                    outH.println( "wMgra" + "," + "mgraParkArea" + "," + "otherDistCoeff*dist" + "," + "exp(otherDistCoeff*dist)" + "," + "discountFactor" + "," + "hstallsoth" + "," + "hparkcost" + "," + "numeratorH" + "," + "denominatorH" );

                    outM.println( mgra + "," + mgraParkAreaField[k] + "," + workDistCoeff*dist + "," + Math.exp( workDistCoeff*dist ) + "," + mstallsothField[k] + "," + mparkcostField[k] + "," + numeratorM + "," + denominatorM );
                    outD.println( mgra + "," + mgraParkAreaField[k] + "," + workDistCoeff*dist + "," + Math.exp( workDistCoeff*dist ) + "," + dstallsothField[k] + "," + dparkcostField[k] + "," + numeratorD + "," + denominatorD );
                    outH.println( mgra + "," + mgraParkAreaField[k] + "," + workDistCoeff*dist + "," + Math.exp( workDistCoeff*dist ) + "," + discountFactor + "," + hstallsothField[k] + "," + hparkcostField[k] + "," + numeratorH + "," + denominatorH );
                }
                
                if ( walkMgras != null ) {
                    
                    for ( int wMgra : walkMgras ) {

                        int row = mgraDataTableMgraRowMap.get(wMgra) - 1;

                        // skip mgra if not in park area 1 or 2.
                        if ( mgraParkAreaField[row] > 2 ) {
                            if ( mgra == LOG_MGRA ) {
                                outM.println( wMgra + "," + mgraParkAreaField[row] );
                                outD.println( wMgra + "," + mgraParkAreaField[row] );
                                outH.println( wMgra + "," + mgraParkAreaField[row] );
                            }
                            continue;
                        }
                        
                        
                        if ( wMgra != mgra ) {
                          dist = getMgraToMgraWalkDistFrom( mgra, wMgra )/5280.0;
                          
                          if ( dist > MAX_PARKING_WALK_DISTANCE ) {
                              if ( mgra == LOG_MGRA ) {
                                  outM.println( wMgra + "," + mgraParkAreaField[row] );
                                  outD.println( wMgra + "," + mgraParkAreaField[row] );
                                  outH.println( wMgra + "," + mgraParkAreaField[row] );
                              }
                              continue;
                          }
                          
                          numeratorM += mstallsothField[row] * Math.exp( workDistCoeff * dist ) * mparkcostField[row];
                          denominatorM += mstallsothField[row] * Math.exp( workDistCoeff * dist );
                          
                          numeratorD += dstallsothField[row] * Math.exp( otherDistCoeff * dist ) * dparkcostField[row];
                          denominatorD += dstallsothField[row] * Math.exp( otherDistCoeff * dist );
                          
                          discountFactor = Math.max( 1 - (numfreehrsField[row]/4), 0 );
                          numeratorH += hstallsothField[row] * Math.exp( otherDistCoeff * dist ) * discountFactor * hparkcostField[row];
                          denominatorH += hstallsothField[row] * Math.exp( otherDistCoeff * dist );

                          if ( mgra == LOG_MGRA ) {
                              outM.println( wMgra + "," + mgraParkAreaField[row] + "," + workDistCoeff*dist + "," + Math.exp( workDistCoeff*dist ) + "," + mstallsothField[row] + "," + mparkcostField[row] + "," + numeratorM + "," + denominatorM );
                              outD.println( wMgra + "," + mgraParkAreaField[row] + "," + otherDistCoeff*dist + "," + Math.exp( otherDistCoeff*dist ) + "," + dstallsothField[row] + "," + dparkcostField[row] + "," + numeratorD + "," + denominatorD );
                              outH.println( wMgra + "," + mgraParkAreaField[row] + "," + otherDistCoeff*dist + "," + Math.exp( otherDistCoeff*dist ) + "," + discountFactor + "," + hstallsothField[row] + "," + hparkcostField[row] + "," + numeratorH + "," + denominatorH );
                          }
                          
                       }
                    
                    }
                    
                }
                //jef: storing by mgra since they are indexed into by mgra
                if (denominatorM != 0) {
                	lsWgtAvgCostM[mgra] = numeratorM / denominatorM;
                } else {
                    if ( LOG_MGRA == mgra ) {
                        outM.close();
                        outD.close();
                        outH.close();
                    }
                    lsWgtAvgCostM[mgra] = 0;
                	logger.warn("Monthly weighted average parking cost for mgra " + mgra + " cannot be calculated since denominator is " + denominatorM);
                }
                
                if (denominatorD != 0) {
                	lsWgtAvgCostD[mgra] = numeratorD / denominatorD;
                } else {
                    if ( LOG_MGRA == mgra ) {
                        outM.close();
                        outD.close();
                        outH.close();
                    }
                   	lsWgtAvgCostD[mgra] = 0;
                   	logger.warn("Daily weighted average parking cost for mgra " + mgra + " cannot be calculated since denominator is " + denominatorD);
                }
                
                if (denominatorH != 0) {
                	lsWgtAvgCostH[mgra] = numeratorH / denominatorH;
                } else {
                    if ( LOG_MGRA > 0 ) {
                        outM.close();
                        outD.close();
                        outH.close();
                    }
                    lsWgtAvgCostH[mgra] = 0;
                    logger.warn("Hourly weighted average parking cost for mgra " + mgra + " cannot be calculated since denominator is " + denominatorH);
                }

            }
            else {
                
                lsWgtAvgCostM[mgra] = mparkcostField[k];
                lsWgtAvgCostD[mgra] = dparkcostField[k];
                lsWgtAvgCostH[mgra] = hparkcostField[k];
                
            }

            // write the data record
            out.println( mgra + "," + mgraParkAreaField[k] + "," + lsWgtAvgCostM[mgra] + "," + lsWgtAvgCostD[mgra] + "," + lsWgtAvgCostH[mgra] );
                    }
        
        if ( LOG_MGRA > 0 ) {
            outM.close();
            outD.close();
            outH.close();
        }

        out.close();

    }      
        
    public double[] getLsWgtAvgCostM() { 
        return lsWgtAvgCostM;
    }
    
    public double[] getLsWgtAvgCostD() { 
        return lsWgtAvgCostD;
    }
    
    public double[] getLsWgtAvgCostH() { 
        return lsWgtAvgCostH;
    }

    public int[] getMgraParkAreas() {
        return mgraParkArea;
    }

    public int[] getNumFreeHours() {
        return numfreehrs;
    }
    
    public int[] getMStallsOth() {
        return mstallsoth;
    }

    public int[] getMStallsSam() {
        return mstallssam;
    }

    public float[] getMParkCost() {
        return mparkcost;
    }

    public int[] getDStallsOth() {
        return dstallsoth;
    }

    public int[] getDStallsSam() {
        return dstallssam;
    }

    public float[] getDParkCost() {
        return dparkcost;
    }

    public int[] getHStallsOth() {
        return hstallsoth;
    }

    public int[] getHStallsSam() {
        return hstallssam;
    }

    public float[] getHParkCost() {
        return hparkcost;
    }

    /**
     * @param mgra for which table data is desired
     * @return high school district for the specified mgra.
     */
    public int getMgraHourlyParkingCost(int mgra)
    {
        int row = mgraDataTableMgraRowMap.get(mgra);
        return (int)mgraTableDataSet.getValueAt(row, MGRA_HPARKCOST_FIELD);
    }


    
    
    public static void main(String[] args)
    {
        ResourceBundle rb = ResourceUtil.getPropertyBundle(new File(args[0]));
        MgraDataManager mdm = MgraDataManager.getInstance(ResourceUtil.changeResourceBundleIntoHashMap(rb));
        mdm.printMgraStats();
    }
    
    
    private class Maz2Tap implements Comparable<Maz2Tap>, Serializable
    {
        public int maz;
        public int tap;
        public double dist;
        public String[] lines;
        public boolean servesNewLines = false;
        
    	@Override
    	public int compareTo(Maz2Tap o) {
		    if ( this.dist < o.dist ) {
		    	return -1;
		    } else if (this.dist==o.dist) {
		    	return 0;
		    } else {
		    	return 1;
		    }
    	}
    }
    
}
