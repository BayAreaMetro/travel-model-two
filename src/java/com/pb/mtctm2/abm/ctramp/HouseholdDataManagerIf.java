package com.pb.mtctm2.abm.ctramp;

import java.util.HashMap;

/**
 * @author Jim Hicks
 * 
 *         Class for managing household and person object data read from synthetic
 *         population files.
 */
public interface HouseholdDataManagerIf
{

    public String testRemote();

    public void setPropertyFileValues(HashMap<String, String> propertyMap);

    public void setDebugHhIdsFromHashmap();

    public void computeTransponderChoiceTazPercentArrays();
    
    public double[] getPercentHhsIncome100Kplus();
    
    public double[] getPercentHhsIncome75Kplus();

    public double[] getPercentHhsMultipleAutos();
    
    public int[] getRandomOrderHhIndexArray(int numHhs);

    public int getArrayIndex(int hhId);

    public void setHhArray(Household[] hhs);

    public void setHhArray(Household[] tempHhs, int startIndex);

    public void setSchoolDistrictMappings( HashMap<String, Integer> segmentNameIndexMap, int[] mgraGsDist, int[] mgraHsDist,
            HashMap<Integer,Integer> gsDistSegMap, HashMap<Integer,Integer> hsDistSegMap );
    
    public void setupHouseholdDataManager(ModelStructure modelStructure, String inputHouseholdFileName, String inputPersonFileName);

    public double[][] getTourPurposePersonsByHomeMgra(String[] purposeList);

    public double[][] getWorkersByHomeMgra(HashMap<Integer, Integer> segmentValueIndexMap);

    public double[][] getStudentsByHomeMgra();

    public double[][] getWorkToursByDestMgra(HashMap<Integer, Integer> segmentValueIndexMap);

    public double[] getWorksAtHomeBySegment(HashMap<Integer, Integer> segmentValueIndexMap);
    
    public double[][] getSchoolToursByDestMgra();

    public double[] getIndividualNonMandatoryToursByHomeMgra(String purposeString);

    public double[] getJointToursByHomeMgra(String purposeString);

    public double[] getAtWorkSubtoursByWorkMgra(String purposeString);

    public void logPersonSummary();

    public void setUwslRandomCount(int iter);

    public void resetUwslRandom(int iter);

    public void resetPreAoRandom();

    public void resetAoRandom(int iter);

    public void resetFpRandom();

    public void resetCdapRandom();

    public void resetImtfRandom();

    public void resetImtodRandom();

    public void resetAwfRandom();

    public void resetAwlRandom();

    public void resetAwtodRandom();

    public void resetJtfRandom();

    public void resetJtlRandom();

    public void resetJtodRandom();

    public void resetInmtfRandom();

    public void resetInmtlRandom();

    public void resetInmtodRandom();

    public void resetStfRandom();

    public void resetStlRandom();

    /**
     * Sets the HashSet used to trace households for debug purposes and sets the
     * debug switch for each of the listed households. Also sets
     */
    public void setTraceHouseholdSet();

    /**
     * Sets the HashSet used to trace households for debug purposes and sets the
     * debug switch for each of the listed households. Also sets
     */
    public void setHouseholdSampleRate(float sampleRate, int sampleSeed);

    /**
     * return the array of Household objects holding the synthetic population and
     * choice model outcomes.
     * 
     * @return hhs
     */
    public Household[] getHhArray();

    public Household[] getHhArray(int firstHhIndex, int lastHhIndex);

    /**
     * return the number of household objects read from the synthetic population.
     * 
     * @return
     */
    public int getNumHouseholds();

    /**
     * set walk segment (0-none, 1-short, 2-long walk to transit access) for the
     * origin for this tour
     */
    public int getInitialOriginWalkSegment(int taz, double randomNumber);

    public long getBytesUsedByHouseholdArray();

}