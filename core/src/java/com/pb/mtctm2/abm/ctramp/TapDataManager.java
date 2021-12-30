package com.pb.mtctm2.abm.ctramp;

import com.pb.common.datafile.TableDataFileReader;
import com.pb.common.datafile.TableDataSet;
import com.pb.common.util.ResourceUtil;
import com.pb.mtctm2.abm.application.NodeZoneMapping;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.io.Serializable;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.ResourceBundle;
import java.util.Set;
import java.util.StringTokenizer;
import java.util.TreeMap;
import java.util.TreeSet;

import org.apache.log4j.Logger;

public final class TapDataManager
        implements Serializable
{
    
    public static final String TAP_DATA_FILE_PROPERTY = "tap.data.file";
    public static final String TAP_DATA_TAP_COLUMN_PROPERTY = "tap.data.tap.column";
    public static final String TAP_DATA_LOTID_COLUMN_PROPERTY = "tap.data.lotid.column";
    public static final String TAP_DATA_TAZ_COLUMN_PROPERTY = "tap.data.taz.column";
    public static final String TAP_DATA_CAPACITY_COLUMN_PROPERTY = "tap.data.capacity.column";

    public static final String STATION_DATA_FILE_PROPERTY = "tap.station.attribute.file";
    
    public static final String DEFAULT_PNR_SHARE_PROPERTY = "tap.pnr.default.share";

    protected transient Logger       logger = Logger.getLogger(TapDataManager.class);
    private static TapDataManager instance;

    // tapID, [tapNum, lotId, ??, taz][list of values]
    private float[][][]           tapParkingInfo;

    // an array that stores parking lot use by lot ID.
    private int[]                 lotUse;

    // an array of taps
    private int[]                  taps;
    private int                   maxTap;
    
    private float[]               parkingCost;
    private float[]               driveAccessWalkTime;
    private float[]               driveAccessDriveTime;
    private boolean[]             driveAccessAllowed;

    public int getMaxTap() {
		return maxTap;
	}

	private TapDataManager(HashMap<String, String> rbMap)
    {

        System.out.println("TapDataManager Started");
        readTap(rbMap);
        getTapList(rbMap);
        intializeLotUse();
        readStationAttributes(rbMap);
        
    }

    /**
     * This method should only be used after the getInstance(HashMap<String, String>
     * rbMap) method has been called since the rbMap is needed to read in all the
     * data and populate the object. This method will return the instance that has
     * already been populated.
     * 
     * @return instance
     * @throws RuntimeException
     */
    public static TapDataManager getInstance()
    {
        if (instance == null)
        {
            throw new RuntimeException(
                    "Must instantiate TapDataManager with the getInstance(rbMap) method first");
        } else
        {
            return instance;
        }
    }

    /**
     * This method will read in the tapParkingInfo.ptype file and store the info in a
     * TreeMap where key equals the iTap and value equals an array of [][3] elements.
     * The TreeMap will be passed to the populateTap function which will transpose
     * the array of [][3] elements to an array of [4][] elements and attaches it to
     * the this.tapParkingInfo[key]
     * 
     * //TODO: Test this and see if there is only a single lot associated // TODO
     * with each tap.
     * 
     * The file has 4 columns - tap, lotid, taz, and capacity
     * 
     * @param rb - the resource bundle that lists the tap.ptype file and
     *            scenario.path.
     */
    private void readTap(HashMap<String, String> rbMap) {

        File tapDataFile = Paths.get(Util.getStringValueFromPropertyMap(rbMap, "scenario.path"),
        		                     Util.getStringValueFromPropertyMap(rbMap, TAP_DATA_FILE_PROPERTY)).toFile();    	
        TableDataFileReader reader = TableDataFileReader.createReader(tapDataFile);
        TableDataSet data;
        try {
        	data = reader.readFile(tapDataFile);
        } catch (IOException e) {
        	throw new RuntimeException(e);
        } finally {
        	reader.close();
        }

        TreeMap<Integer,List<float[]>> map = new TreeMap<Integer, List<float[]>>();
        String tapColumn = Util.getStringValueFromPropertyMap(rbMap,TAP_DATA_TAP_COLUMN_PROPERTY);
        String lotidColumn = Util.getStringValueFromPropertyMap(rbMap,TAP_DATA_LOTID_COLUMN_PROPERTY);
        String tazColumn = Util.getStringValueFromPropertyMap(rbMap,TAP_DATA_TAZ_COLUMN_PROPERTY);
        String capacityColumn = Util.getStringValueFromPropertyMap(rbMap,TAP_DATA_CAPACITY_COLUMN_PROPERTY);
        for (int row = 1; row <= data.getRowCount(); row++) {

        	int tap = (int) data.getValueAt(row,tapColumn);
        	float lotId = data.getValueAt(row,lotidColumn);
        	float taz = data.getValueAt(row,tazColumn);
        	float capacity = data.getValueAt(row,capacityColumn);
        	capacity = Math.max(capacity,15.0f)*2.5f; //todo: inherited formula, may need to be revised
        	if (!map.containsKey(tap))
        		map.put(tap,new LinkedList<float[]>());
        	map.get(tap).add(new float[] {lotId,taz,capacity});
        }
        populateTap(map);
    }
    
    
    
    public void readStationAttributes(HashMap<String, String> rbMap) {
    	
        
    	float defaultPnrShare = Util.getFloatValueFromPropertyMap(rbMap, DEFAULT_PNR_SHARE_PROPERTY);
    	
    	File tapDataFile = Paths.get(Util.getStringValueFromPropertyMap(rbMap, "scenario.path"),
                Util.getStringValueFromPropertyMap(rbMap, STATION_DATA_FILE_PROPERTY)).toFile();    	
        TableDataFileReader reader = TableDataFileReader.createReader(tapDataFile);
        TableDataSet data;
        try {
        	data = reader.readFile(tapDataFile);
        } catch (IOException e) {
        	throw new RuntimeException(e);
        } finally {
        	reader.close();
        }
        
        for(int row=1;row<=data.getRowCount();++row) {
        
        	int tap = (int) data.getValueAt(row, "tap");
        	float pnrWalkTime = data.getValueAt(row, "stPNRWalkTime");	
        	float knrWalkTime = data.getValueAt(row, "stKNRWalkTime");
        	float pnrDriveTime = data.getValueAt(row, "stPNRDriveTime");
        	float knrDriveTime = data.getValueAt(row, "stKNRDriveTime");
        	String parkingType = data.getStringValueAt(row, "stParkType");
        	float freeSpaces = data.getValueAt(row, "stFreeSpaces");
        	float paidSpaces = data.getValueAt(row, "stPaidSpaces");
        	float permitSpaces = data.getValueAt(row, "stPermitSpaces");
        	float privateSpaces = data.getValueAt(row, "stPrivateSpaces");
        	float dailyCost = data.getValueAt(row, "stDailyCost");
        	float monthlyCost = data.getValueAt(row, "stMonthlyCost");
        	float privateCost = data.getValueAt(row, "stPrivateCost");
        	float pnrSplit = data.getValueAt(row, "stPNRSplit");
        
        	if(pnrSplit==0)
        		pnrSplit = defaultPnrShare;
        	
        	//calculate weighted average times and divide by 60 to convert to minutes
        	float walkTime = (pnrWalkTime * pnrSplit + knrWalkTime * (1-pnrSplit))/60.0f;
        	float driveTime = (pnrDriveTime * pnrSplit + knrDriveTime * (1-pnrSplit))/60.0f;
        	
        	//calculated weighted average parking cost (convert from dollars to cents)
        	float avgParkingCost=0.0f;
        	if((freeSpaces + paidSpaces + permitSpaces + privateSpaces)>0)
        	     avgParkingCost = 
        			(paidSpaces * dailyCost +
        			permitSpaces * monthlyCost/22.0f +
        			privateSpaces * privateCost)
        			/ (freeSpaces + paidSpaces + permitSpaces + privateSpaces) * pnrSplit * 0.5f * 100f;

        	boolean driveAvailable=true;
        	if(parkingType.equalsIgnoreCase("W"))
        		driveAvailable=false;
        	
        	parkingCost[tap] = avgParkingCost;
        	driveAccessWalkTime[tap] = walkTime;
            driveAccessDriveTime[tap] = driveTime;
            driveAccessAllowed[tap] = driveAvailable;
        
        }
        
        
        
    }

   

    /**
     * The function will get a TreeMap having with iTaps as keys and [][4] arrays.
     * For each iTap in the TreeMap it will transpose the [][4] array associated with
     * it and attach it to the this.tapParkingInfo[key] element.
     * 
     * @param map - a TreeMap containing all the records of the tapParkingInfo.ptype
     *            file
     */
    private void populateTap(TreeMap<Integer, List<float[]>> map)
    {

        this.tapParkingInfo = new float[map.lastKey() + 1][3][];
        Iterator<Integer> iterKeys = map.keySet().iterator();
        while (iterKeys.hasNext())
        {
            int key = iterKeys.next();
            int numElem = map.get(key).size();
            for (int i = 0; i < 3; i++)
                this.tapParkingInfo[key][i] = new float[numElem];
            for (int i = 0; i < numElem; i++)
            {
                for (int j = 0; j < 3; j++)
                {
                    this.tapParkingInfo[key][j][i] = map.get(key).get(i)[j];
                }
            }
        }
    }

    // TODO: test this.
    public void intializeLotUse()
    {

        float maxLotId = 0;
        for (int i = 0; i < tapParkingInfo.length; i++)
        {
            float[] lotIds = tapParkingInfo[i][0];
            if (lotIds != null)
            {
                for (int j = 0; j < tapParkingInfo[i][0].length; j++)
                {
                    if (maxLotId < tapParkingInfo[i][0][j]) maxLotId = tapParkingInfo[i][0][j];

                }
            }
        }

        lotUse = new int[(int) maxLotId + 1];
        parkingCost = new float[(int) maxLotId + 1];
        driveAccessWalkTime= new float[(int) maxLotId + 1];
        driveAccessDriveTime= new float[(int) maxLotId + 1];
        driveAccessAllowed= new boolean[(int) maxLotId + 1];

    }

    /**
     * Set the array of tap numbers (taps[]), indexed at 1.
     * 
     * @param rb A Resourcebundle with skims.path and tap.skim.file properties.
     */
    public void getTapList(HashMap<String, String> rbMap)
    {
    	maxTap = 0;
    	Set<Integer> tapSequence = new NodeZoneMapping(rbMap).getSequenceTaps();
    	taps = new int[tapSequence.size()+1];
    	int counter = 1;
    	for (int tap : tapSequence) {
    		taps[counter++] = tap;
    		if (tap > maxTap)
    			maxTap = tap;
    	}
    }

    public int getLotUse(int lotId)
    {
        return lotUse[lotId];
    }
    
    public int getTazForTap(int tap){
    	return (int) tapParkingInfo[tap][1][0];
    }

    public static TapDataManager getInstance(HashMap<String, String> rbMap)
    {
        if (instance == null)
        {
            instance = new TapDataManager(rbMap);
            return instance;
        } else return instance;
    }

    public float[][][] getTapParkingInfo()
    {
        if (instance != null)
        {
            return this.tapParkingInfo;
        } else
        {
            throw new RuntimeException();
        }
    }


    public int[] getTaps()
    {
        return taps;
    }
    
    public float getParkingCost(int tap) {
    	
    	return parkingCost[tap];
    }
    
    public float getDriveAccessWalkTime(int tap) {
    	
    	return driveAccessWalkTime[tap];

    }
   
    public float getDriveAccessDriveTime(int tap) {
    	
    	return driveAccessDriveTime[tap];

    }

    public boolean getDriveAccessAllowed(int tap) {
    	
    	return driveAccessAllowed[tap];

    }
    
    public static void main(String[] args)
    {
        ResourceBundle rb = ResourceUtil.getPropertyBundle(new File(args[0]));

        TapDataManager tdm = TapDataManager.getInstance(ResourceUtil
                .changeResourceBundleIntoHashMap(rb));
    }

}
