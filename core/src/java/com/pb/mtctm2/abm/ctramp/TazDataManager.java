package com.pb.mtctm2.abm.ctramp;

import com.pb.common.datafile.OLD_CSVFileReader;
import com.pb.common.datafile.TableDataFileReader;
import com.pb.common.datafile.TableDataSet;
import com.pb.common.util.ResourceUtil;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.io.Serializable;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.ResourceBundle;
import java.util.StringTokenizer;
import java.util.TreeMap;
import java.util.TreeSet;

import org.apache.log4j.Logger;

import com.pb.mtctm2.abm.ctramp.Modes.AccessMode;

/**
 * This class is used for storing the TAZ data for the mode choice model.
 * 
 * @author Christi Willison
 * @version Sep 2, 2008
 *          <p/>
 *          Created by IntelliJ IDEA.
 */
public class TazDataManager
        implements Serializable
{
	
	public static final String TAZ_DATA_FILE_PROPERTY = "taz.data.file";
	public static final String TAZ_DATA_FILE_TAZ_COLUMN_PROPERTY = "taz.data.taz.column";
	public static final String TAZ_DATA_FILE_AVGTT_COLUMN_PROPERTY = "taz.data.avgttd.column";
	public static final String TAZ_DATA_FILE_DIST_COLUMN_PROPERTY = "taz.data.dist.column";
	public static final String TAZ_DATA_FILE_PCTDETOUR_COLUMN_PROPERTY = "taz.data.pctdetour.column";
	public static final String TAZ_DATA_FILE_TERMINAL_COLUMN_PROPERTY = "taz.data.terminal.column";

    protected transient Logger       logger = Logger.getLogger(TazDataManager.class);
    private static TazDataManager instance;
    public int[]                  tazs;
    protected int[]               tazsOneBased;
 
    // arrays for the MGRA and TAZ fields from the MGRA table data file.
    private int[] mgraTableMgras;
    private int[] mgraTableTazs;
    
    // list of TAZs in numerical order
	public TreeSet<Integer>       tazSet = new TreeSet<Integer>();
    public int                    maxTaz;

    private int                   nTazsWithMgras;
    private int[][]               tazMgraArray;
    //private int[][]               tazXYCoordArray;
    private float[]               tazDestinationTerminalTime;
    private float[]               tazOriginTerminalTime;
//    private int[]                 tazSuperDistrict;
//    private int[]                 pmsa;
//    private int[]                 cmsa;
    // This might be a poor name for this array.
    // Please change if you know better.
    private int[]                 tazAreaType;
    
    private double[] avgtts;
    private double[] transpDist;
    private double[] pctDetour;
    
    /**
     * Get an array of tazs, indexed sequentially from 0
     * @return Taz array indexed from 0
     */
    public int[] getTazs() {
		return tazs;
	}
    
    /**
     * Get an array of tazs, indexed sequentially from 1
     * @return  taz array indexed from 1
     */
	public int[] getTazsOneBased() {
		return tazsOneBased;
	}


    private TazDataManager(HashMap<String, String> rbMap)
    {
        System.out.println("TazDataManager Started");

        // read the MGRA data file into a TableDataSet and get the MGRA and TAZ fields from it for setting TAZ correspondence.
        readMgraTableData(rbMap); 
        setTazMgraCorrespondence();
        readTazData(rbMap);

        //printTazStats();
    }
    
    private void readTazData(HashMap<String,String> rbMap) {
        File dataFile = Paths.get(Util.getStringValueFromPropertyMap(rbMap, "scenario.path"),
                        Util.getStringValueFromPropertyMap(rbMap,TAZ_DATA_FILE_PROPERTY)).toFile();
        TableDataSet tazData;
    	try {
			tazData = TableDataFileReader.createReader(dataFile).readFile(dataFile);
		} catch (IOException e) {
			throw new RuntimeException(e);
		}

        tazOriginTerminalTime = new float[maxTaz+1];
    	tazDestinationTerminalTime = new float[maxTaz+1];
        avgtts = new double[maxTaz+1];
        transpDist = new double[maxTaz+1];
        pctDetour = new double[maxTaz+1];
        String tazColumn = Util.getStringValueFromPropertyMap(rbMap,TAZ_DATA_FILE_TAZ_COLUMN_PROPERTY);
        String avgttColumn = Util.getStringValueFromPropertyMap(rbMap,TAZ_DATA_FILE_AVGTT_COLUMN_PROPERTY);
        String pctdetourColumn = Util.getStringValueFromPropertyMap(rbMap,TAZ_DATA_FILE_PCTDETOUR_COLUMN_PROPERTY);
        String distColumn = Util.getStringValueFromPropertyMap(rbMap,TAZ_DATA_FILE_DIST_COLUMN_PROPERTY);
        String terminalColumn = Util.getStringValueFromPropertyMap(rbMap,TAZ_DATA_FILE_TERMINAL_COLUMN_PROPERTY);
        
    	for (int row = 1; row <= tazData.getRowCount(); row++) {
    		int taz = (int) tazData.getValueAt(row,tazColumn);
    		float avgtt = tazData.getValueAt(row,avgttColumn);
    		float pctdetour = tazData.getValueAt(row,pctdetourColumn);
    		float dist = tazData.getValueAt(row,distColumn);
    		float terminalTime = tazData.getValueAt(row,terminalColumn);
    		
    		tazOriginTerminalTime[taz] = terminalTime;
    		tazDestinationTerminalTime[taz] = terminalTime;
    		avgtts[taz] = avgtt;
    		pctDetour[taz] = pctdetour;
    		transpDist[taz] = dist;
    	}
    }

    /**
     * This method will set the TAZ/MGRA correspondence. Two columns from the MGRA data table are used.
     * The first column is the MGRA and the second column is the TAZ. The goal of
     * this method is to populate the tazMgraArray array and the tazs treeset, plus
     * set maxTaz.
     * 
     */
    private void setTazMgraCorrespondence()
    {

        HashMap<Integer, ArrayList<Integer>> tazMgraMap = new HashMap<Integer, ArrayList<Integer>>();

        int mgra;
        int taz;

        for ( int i=0; i < mgraTableMgras.length; i++ ) {

            mgra = mgraTableMgras[i];
            taz = mgraTableTazs[i];
            if ( ! tazSet.contains(taz) )
                tazSet.add(taz);
            
            maxTaz = Math.max( taz, maxTaz );
            
            if ( ! tazMgraMap.containsKey(taz) ) {
                ArrayList<Integer> tazMgraList = new ArrayList<Integer>();
                tazMgraList.add(mgra);
                tazMgraMap.put(taz, tazMgraList);
            } else {
                ArrayList<Integer> tazMgraList = tazMgraMap.get(taz);
                tazMgraList.add(mgra);
            }

        }

        // now go thru the array of ArrayLists and convert the lists to arrays and
        // store in the class variable tazMgraArrays.
        tazMgraArray = new int[maxTaz + 1][];
        for (Iterator it = tazMgraMap.entrySet().iterator(); it.hasNext();)
        { // elements in the array of arraylists
            Map.Entry entry = (Map.Entry) it.next();
            taz = (Integer) entry.getKey();
            ArrayList tazMgraList = (ArrayList) entry.getValue();
            if (tazMgraList != null)
            { // if the list isn't null
                tazMgraArray[taz] = new int[tazMgraList.size()]; // initialize the class variable
                for (int j = 0; j < tazMgraList.size(); j++)
                    tazMgraArray[taz][j] = (Integer) tazMgraList.get(j);
                nTazsWithMgras++;
            }
        }
        tazs = new int[tazSet.size()];
        
        tazsOneBased =  new int[tazSet.size()+1];
        int i = 0;
        for (Integer tazNumber : tazSet) {
            tazs[i++] = tazNumber;
            tazsOneBased[i] = tazNumber;
        }
    }

    /**
     * This method will return the Area Type (Location?) for the TAZ.
     * 
     * 
     * @param taz - TAZ that AreaType is wanted for.
     * @return area type that the taz corresponds to
     */
    public int getTAZAreaType(int taz)
    {
        return tazAreaType[taz];
    }

    /**
     * Write taz data manager data to logger for debugging.
     * 
     */
    public void printTazStats()
    {
        logger.info("Number of TAZs: " + tazSet.size());
        logger.info("Max TAZ: " + maxTaz);
        logger.info("Number of TAZs with MGRAs: " + nTazsWithMgras);
       
    }

    /**
     * Get a static instance of the Taz Data Manager. One is created if it doesn't
     * exist already.
     * 
     * @param rb A resourcebundle with properties for the TazDataManager.
     * @return A static instance of this class.
     */
    public static TazDataManager getInstance(HashMap<String, String> rbMap)
    {
        if (instance == null)
        {
            instance = new TazDataManager(rbMap);
            return instance;
        } else return instance;
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
    public static TazDataManager getInstance() throws RuntimeException
    {
        if (instance == null)
        {
            throw new RuntimeException(
                    "Must instantiate TazDataManager with the getInstance(rbMap) method first");
        } else
        {
            return instance;
        }
    }

    /**
     * Get the number of TAZs with MGRAs.
     * 
     * @return The number of TAZs with MGRAs.
     */
    public int getNTazsWithMgras()
    {
        if (instance != null)
        {
            return nTazsWithMgras;
        } else
        {
            throw new RuntimeException();
        }
    }

    public int[][] getTazMgraArray()
    {
        if (instance != null)
        {
            return tazMgraArray;
        } else
        {
            throw new RuntimeException();
        }
    }

    /**
     * Return the list of MGRAs within this TAZ.
     * 
     * @param taz The TAZ number
     * @return An array of MGRAs within the TAZ.
     */
    public int[] getMgraArray(int taz)
    {
        if (instance != null)
        {
            return tazMgraArray[taz];
        } else
        {
            throw new RuntimeException();
        }
    }

/*    
    public int[][] getTazXYCoordArray()
    {
        if (instance != null)
        {
            return tazXYCoordArray;
        } else
        {
            throw new RuntimeException();
        }
    }

    public int[] getTazSuperDistrict()
    {
        if (instance != null)
        {
            return tazSuperDistrict;
        } else
        {
            throw new RuntimeException();
        }

    }

    public int[] getPmsa()
    {
        if (instance != null)
        {
            return this.pmsa;
        } else
        {
            throw new RuntimeException();
        }
    }

    public int[] getCmsa()
    {
        if (instance != null)
        {
            return this.cmsa;
        } else
        {
            throw new RuntimeException();
        }
    }
*/
    
    /**
     * Returns the max TAZ value
     * @return the max TAZ value
     */
    public int getMaxTaz() {
        return maxTaz;
    }
    
    
    private void readMgraTableData( HashMap<String,String> rbMap ) {
        
        // get the mgra data table from one of these UECs.
        String projectPath = rbMap.get(CtrampApplication.PROPERTIES_PROJECT_DIRECTORY);
        String mgraFile = rbMap.get(MgraDataManager.PROPERTIES_MGRA_DATA_FILE);
        mgraFile = projectPath + mgraFile;

        TableDataSet mgraTableDataSet = null;
        try {
            OLD_CSVFileReader reader = new OLD_CSVFileReader();
            mgraTableDataSet = reader.readFile(new File(mgraFile));
        }
        catch (IOException e) {
            logger.error ("problem reading mgra data table for TazDataManager.", e);
            System.exit(1);
        }
      

        // get 0-based arrays from the specified fields in the MGRA table
        mgraTableMgras = mgraTableDataSet.getColumnAsInt( MgraDataManager.MGRA_FIELD_NAME );
        mgraTableTazs = mgraTableDataSet.getColumnAsInt( MgraDataManager.MGRA_TAZ_FIELD_NAME );

    }

    /**
     * Test an instance of the class by instantiating and reporting.
     * 
     * @param args [0] The properties file name/path.
     */
    public static void main(String[] args)
    {
        ResourceBundle rb = ResourceUtil.getPropertyBundle(new File(args[0]));

        TazDataManager tdm = TazDataManager.getInstance(ResourceUtil
                .changeResourceBundleIntoHashMap(rb));

    }

    /**
     * This method will return the Origin Terminal Time for the TDZ.
     * 
     * @param taz - TAZ that Terminal Time is wanted for.
     *@return Origin Terminal Time
     */
    public float getOriginTazTerminalTime(int taz)
    {
        return tazOriginTerminalTime[taz];
    }

    /**
     * This method will return the Destination Terminal Time for the TDZ.
     * 
     * @param taz - TAZ that Terminal Time is wanted for.
     *@return Destination Terminal Time
     */
    public float getDestinationTazTerminalTime(int taz)
    {
        return tazDestinationTerminalTime[taz];
    }
    
    /**
     * Get the average travel time to a taz from the network (that is the average from the "real" streets to the taz via a connector).
     * 
     * @param taz
     *        The TAZ.
     *        
     * @return the average connector travel time to TAZ.
     */
    public double getAvgTravelTime(int taz) {
    	return avgtts[taz];
    }
    
    /**
     * Get array holding the average travel distance to a taz from the network (that is the average from the "real" streets to the taz via a connector).
     * 
     * @return the average connector travel distance to TAZ data array.
     */
    public double[] getAvgTravelDistanceData() {
    	return transpDist;
    }
    
    /**
     * Get array holding the average travel time to a taz from the network (that is the average from the "real" streets to the taz via a connector).
     * 
     * @return the average connector travel time to TAZ data array.
     */
    public double[] getAvgTravelTimeData() {
    	return avgtts;
    }
    
    /**
     * Get array holding the percent detour for a taz.
     * 
     * @return the percent detour TAZ data array.
     */
    public double[] getPctDetourData() {
    	return pctDetour;
    }

}
