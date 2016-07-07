package com.pb.mtctm2.abm.ctramp;

import java.io.Serializable;
import java.util.Arrays;
import java.util.HashMap;

public class Util implements Serializable {
	private static final long serialVersionUID = -1819542390832827779L;

	public static boolean getBooleanValueFromPropertyMap(HashMap<String, String> rbMap, String key) {
        String value = getStringValueFromPropertyMap(rbMap,key);
        if (value.equalsIgnoreCase("true") || value.equalsIgnoreCase("false")) 
            return Boolean.parseBoolean(value);
    	String errorMessage = "property file key: " + key + " = " + value + " should be either 'true' or 'false'.";
        System.out.println(errorMessage);
        throw new RuntimeException(errorMessage);
    }

    public static String getStringValueFromPropertyMap(HashMap<String, String> rbMap, String key) {
        String returnValue = rbMap.get(key);
        if (returnValue == null) {
        	String errorMessage = "key not found in properties: " + key;
            System.out.println(errorMessage);
            throw new RuntimeException(errorMessage);
        }
        return returnValue;
    }

    public static float getFloatValueFromPropertyMap(HashMap<String, String> rbMap, String key) {
        return  Float.parseFloat(getStringValueFromPropertyMap(rbMap,key));
    }

    public static int getIntegerValueFromPropertyMap(HashMap<String, String> rbMap, String key) {
        return  Integer.parseInt(getStringValueFromPropertyMap(rbMap,key));
    }

    public static int[] getIntegerArrayFromPropertyMap(HashMap<String, String> rbMap, String key) {
        String[] values = getStringValueFromPropertyMap(rbMap,key).split(",");
        int[] array = new int[values.length];
        for (int i = 0; i < array.length; i++)
        	array[i] = Integer.parseInt(values[i]);
        return array;
    }

    /**
     * 
     * @param cumProbabilities cumulative probabilities array
     * @param entry target to search for in array
     * @return the array index i where cumProbabilities[i] > entry and
     *         cumProbabilities[i-1] <= entry.
     */
    public static int binarySearchDouble(double[] cumProbabilities, double entry) {
        // lookup index for 0 <= entry < 1.0 in cumProbabilities
        // cumProbabilities values are assumed to be in range: [0,1], and
        // cumProbabilities[cumProbabilities.length-1] must equal 1.0

        // if entry is outside the allowed range, return -1
        if (entry < 0 || entry >= 1.0) {
            System.out.println( "entry = " + entry + " is outside of allowable range for cumulative distribution [0,...,1.0)");
            return -1;
        }

        // if cumProbabilities[cumProbabilities.length-1] is not equal to 1.0, return -1
        if (cumProbabilities[cumProbabilities.length - 1] != 1.0) {
            System.out.println( "cumProbabilities[cumProbabilities.length-1] = "
                    + cumProbabilities[cumProbabilities.length - 1] + " must equal 1.0");
            return -1;
        }
        
        int location = Arrays.binarySearch(cumProbabilities,entry);
        return location < 0 ? -1*location -1 : location;
    }

    /**
     * 
     * @param cumProbabilities cumulative probabilities array
     * @param numIndices are the number of probability values to consider in the cumulative probabilities array
     * @param entry target to search for in array between indices 1 and numValues.
     * @return the array index i where cumProbabilities[i] > entry and
     *         cumProbabilities[i-1] <= entry.
     */
    public static int binarySearchDouble(double cumProbabilityLowerBound, double[] cumProbabilities, int numIndices, double entry) {

        // search for 0-based index i for cumProbabilities such that
        //      cumProbabilityLowerBound <= entry < cumProbabilities[0], i = 0;
        // or
        //      cumProbabilities[i-1] <= entry < cumProbabilities[i], for i = 1,...numIndices-1;

        
        // if entry is outside the allowed range, return -1
        if ( entry < cumProbabilityLowerBound || entry >= cumProbabilities[numIndices-1] ) {
            System.out.println( "entry = " + entry + " is outside of allowable range of cumulative probabilities.");
            System.out.println( "cumProbabilityLowerBound = " + cumProbabilityLowerBound + ", cumProbabilities[numIndices-1] = " + cumProbabilities[numIndices-1] + ", numIndices = " + numIndices );
            return -1;
        }
        
        int location = Arrays.binarySearch(cumProbabilities,entry);
        return location < 0 ? -1*location -1 : location;

    }

}
