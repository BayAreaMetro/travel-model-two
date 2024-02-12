package com.pb.mtctm2.abm.accessibilities;

import org.apache.log4j.Logger;


public class StoredTransitSkimData
{

    private transient Logger                        logger       = Logger.getLogger(StoredTransitSkimData.class);;

    private static StoredTransitSkimData objInstance = null;

    // these arrays are shared by McLogsumsAppender objects and are used by wtw, wtd, and dtw calculators.
    private double[][][][] storedWtwDepartPeriodTazTazSkims;
    private double[][][][] storedWtdDepartPeriodTazTazSkims;
    private double[][][][] storedDtwDepartPeriodTazTazSkims;
    
    public static synchronized StoredTransitSkimData getInstance( int numPeriods, int maxTaz )
    {
        if (objInstance == null) {
            objInstance = new StoredTransitSkimData();
            objInstance.setupStoredDataArrays(numPeriods, maxTaz );
            return objInstance;
        }
        else {
            return objInstance;
        }
    }    
    
    private void setupStoredDataArrays(int numPeriods, int maxTaz ){        
        
    	storedWtwDepartPeriodTazTazSkims = new double[numPeriods + 1][maxTaz + 1][][];
        storedWtdDepartPeriodTazTazSkims = new double[numPeriods + 1][maxTaz + 1][][];
        storedDtwDepartPeriodTazTazSkims = new double[numPeriods + 1][maxTaz + 1][][];
    }
    
    public double[][][][] getStoredWtwDepartPeriodTazTazSkims() {
        return storedWtwDepartPeriodTazTazSkims;
    }
    
    public double[][][][] getStoredWtdDepartPeriodTazTazSkims() {
        return storedWtdDepartPeriodTazTazSkims;
    }
    
    public double[][][][] getStoredDtwDepartPeriodTazTazSkims() {
        return storedDtwDepartPeriodTazTazSkims;
    }
    
    
}
