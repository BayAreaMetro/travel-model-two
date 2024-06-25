package com.pb.mtctm2.abm.accessibilities;

import java.util.concurrent.ConcurrentHashMap;
import java.util.HashMap;


public class StoredUtilityData
{

    private static StoredUtilityData objInstance = null;
    public static final float		 default_utility = -999;

    // these arrays are shared by multiple BestTransitPathCalculator objects in a distributed computing environment
    private float[][] storedWalkAccessUtils;	// dim#1: MGRA id, dim#2: TAZ id
    private float[][] storedDriveAccessUtils; // dim#1: TAZ id, dim#2: TAZ id
    private float[][] storedWalkEgressUtils; 	// dim#1: TAZ id, dim#2: MGRA id
    private float[][] storedDriveEgressUtils; // dim#1: TAZ id, dim#2: TAZ id
    
    // {0:WTW, 1:WTD, 2:DTW} -> TOD period number -> pTAZ*100000+aTAZ -> utility
    private HashMap<Integer,HashMap<Integer,ConcurrentHashMap<Long,float[]>>> storedDepartPeriodTazTazUtils;
       
    
    private StoredUtilityData(){
    }
    
    public static synchronized StoredUtilityData getInstance( int maxMgra, int maxTaz, int[] accEgrSegments, int[] periods)
    {
        if (objInstance == null) {
            objInstance = new StoredUtilityData();
            objInstance.setupStoredDataArrays( maxMgra, maxTaz, accEgrSegments, periods);
            return objInstance;
        }
        else {
            return objInstance;
        }
    }    
    
    private void setupStoredDataArrays( int maxMgra, int maxTaz, int[] accEgrSegments, int[] periods){        
    	// dimension the arrays
    	storedWalkAccessUtils = new float[maxMgra + 1][maxTaz + 1];
        storedDriveAccessUtils = new float[maxTaz + 1][maxTaz + 1];
        storedWalkEgressUtils = new float[maxTaz + 1][maxMgra + 1];
        storedDriveEgressUtils = new float[maxTaz + 1][maxTaz + 1];
        // assign default values to array elements
        for (int i=0; i<=maxMgra; i++)
        	for (int j=0; j<=maxTaz; j++) {
        		storedWalkAccessUtils[i][j] = default_utility;
        		storedWalkEgressUtils[j][i] = default_utility;
        	}
        // assign default values to array elements
        for (int i=0; i<=maxTaz; i++)
        	for (int j=0; j<=maxTaz; j++) {
        		storedDriveAccessUtils[i][j] = default_utility;
        		storedDriveEgressUtils[j][i] = default_utility;
        	}
        
        //put into concurrent hashmap
        storedDepartPeriodTazTazUtils = new HashMap<Integer,HashMap<Integer,ConcurrentHashMap<Long,float[]>>>();
        for(int i=0; i<accEgrSegments.length; i++) {
        	storedDepartPeriodTazTazUtils.put(accEgrSegments[i], new HashMap<Integer,ConcurrentHashMap<Long,float[]>>());
        	for(int j=0; j<periods.length; j++) {
        		HashMap<Integer,ConcurrentHashMap<Long,float[]>> hm = storedDepartPeriodTazTazUtils.get(accEgrSegments[i]);
        		hm.put(periods[j], new ConcurrentHashMap<Long,float[]>()); //key method paTazKey below
        	}
    	}        
    }
    
    public float[][] getStoredWalkAccessUtils() {
        return storedWalkAccessUtils;
    }
    
    public float[][] getStoredDriveAccessUtils() {
        return storedDriveAccessUtils;
    }
    
    public float[][] getStoredWalkEgressUtils() {
        return storedWalkEgressUtils;
    }
    
    public float[][]getStoredDriveEgressUtils() {
        return storedDriveEgressUtils;
    }
    
    public HashMap<Integer,HashMap<Integer,ConcurrentHashMap<Long,float[]>>> getStoredDepartPeriodTazTazUtils() {
        return storedDepartPeriodTazTazUtils;
    }
    
    //create p to a hash key - up to 99,999 
    public long paTazKey(int p, int a) {
    	return(p * 100000 + a);
    }
    
    //convert double array to float array
    public float[] d2f(double[] d) {
    	float[] f = new float[d.length];
    	for(int i=0; i<d.length; i++) {
    		f[i] = (float)d[i];
    	}
    	return(f);
    }
    
}
