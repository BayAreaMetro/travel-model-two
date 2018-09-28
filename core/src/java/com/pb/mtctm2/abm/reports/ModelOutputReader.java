package com.pb.mtctm2.abm.reports;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.HashMap;

import org.apache.log4j.Logger;

import com.pb.common.datafile.OLD_CSVFileReader;
import com.pb.common.datafile.TableDataSet;
import com.pb.mtctm2.abm.ctramp.CtrampApplication;
import com.pb.mtctm2.abm.ctramp.Household;
import com.pb.mtctm2.abm.ctramp.HouseholdDataWriter;
import com.pb.mtctm2.abm.ctramp.HouseholdIndividualMandatoryTourFrequencyModel;
import com.pb.mtctm2.abm.ctramp.ModelStructure;
import com.pb.mtctm2.abm.ctramp.Person;

public class ModelOutputReader {

    private transient Logger    logger                          = Logger.getLogger(ModelOutputReader.class);

    private static final String PROPERTIES_HOUSEHOLD_DATA_FILE  = "Results.HouseholdDataFile";
    private static final String PROPERTIES_PERSON_DATA_FILE     = "Results.PersonDataFile";
    private static final String PROPERTIES_INDIV_TOUR_DATA_FILE = "Results.IndivTourDataFile";
    private static final String PROPERTIES_JOINT_TOUR_DATA_FILE = "Results.JointTourDataFile";
    private static final String PROPERTIES_INDIV_TRIP_DATA_FILE = "Results.IndivTripDataFile";
    private static final String PROPERTIES_JOINT_TRIP_DATA_FILE = "Results.JointTripDataFile";
    private ModelStructure      modelStructure;
    private int                 iteration;
    private HashMap<String,String> rbMap;
    private HashMap<Long, PersonFileAttributes> personFileAttributesMap;
    private HashMap<Long, TourFileAttributes> individualTourAttributesMap; //by person_id
    private HashMap<Long, TourFileAttributes> jointTourAttributesMap; //by hh_id
   
    /**
     * Default constructor.
     * @param rbMap          Hashmap of properties
     * @param modelStructure Model structure object
     * @param iteration      Iteration number used for file names
     */
	public ModelOutputReader(HashMap<String,String> rbMap, ModelStructure modelStructure,
        int iteration)
	{
		logger.info("Writing data structures to files.");
		this.modelStructure = modelStructure;
		this.iteration = iteration;
		this.rbMap = rbMap;
	}
	/**
	 * Create a file name with the iteration number appended.
	 * 
	 * @param originalFileName The original file name	
	 * @param iteration The iteration number
	 * @return The reformed file name with the iteration number appended.
	 */
    private String formFileName(String originalFileName, int iteration)
    {
        int lastDot = originalFileName.lastIndexOf('.');

        String returnString = "";
        if (lastDot > 0)
        {
            String base = originalFileName.substring(0, lastDot);
            String ext = originalFileName.substring(lastDot);
            returnString = String.format("%s_%d%s", base, iteration, ext);
        } else
        {
            returnString = String.format("%s_%d.csv", originalFileName, iteration);
        }

        logger.info("writing " + originalFileName + " file to " + returnString);

        return returnString;
    }

    /**
     * Read the data from the Results.PersonDataFile.
     * Data is stored in HashMap personFileAttributesMap<person_id,PersonFileAttributes>
     * so that it can be retrieved quickly for a household object.
     * 
     */
	public void readPersonDataOutput(){
		
        //read person data
        String baseDir = rbMap.get(CtrampApplication.PROPERTIES_PROJECT_DIRECTORY);
        String personFile = baseDir + formFileName(rbMap.get(PROPERTIES_PERSON_DATA_FILE), iteration);
        TableDataSet personData = readTableData(personFile);

        personFileAttributesMap = new HashMap<Long, PersonFileAttributes>();
        
        for(int row = 1; row<=personData.getRowCount();++row){
        	
        	//get the values for this person
        	long hhid = (long) personData.getValueAt(row, "hh_id");
        	long person_id = (long) personData.getValueAt(row,"person_id");
        	long personNumber = (long) personData.getValueAt(row,"person_num");
        	int age = (int) personData.getValueAt(row,"age");
        	
        	String genderString = personData.getStringValueAt(row,"gender");
        	int gender = (genderString.compareTo("m")==0 ? 1 : 2);
        	
        	float valueOfTime = personData.getValueAt(row,"value_of_time");
        	String activityPattern = personData.getStringValueAt(row,"activity_pattern");
        	
        	String personTypeString = personData.getStringValueAt(row,"type");
        	int personType = getPersonType(personTypeString);
        	
        	int imfChoice = (int) personData.getValueAt(row, "imf_choice");
        	int inmfChoice = (int) personData.getValueAt(row, "inmf_choice");
        	int fp_choice = (int) personData.getValueAt(row,"fp_choice");
        	float reimb_pct = personData.getValueAt(row,"reimb_pct");
        	float sampleRate = personData.getValueAt(row,"sampleRate");
           
        	PersonFileAttributes personFileAttributes = new PersonFileAttributes(hhid,person_id,personNumber,age,gender,valueOfTime,
        			activityPattern,personType,imfChoice,inmfChoice,fp_choice,reimb_pct,sampleRate);
        	
        	personFileAttributesMap.put(person_id,personFileAttributes);
        	
        }

	}

	
    /**
     * Read the data from the Results.IndivTourDataFile or Results.JointTourDataFile.
     * Data is stored in HashMap passed into method as an argument. Method handles
     * both individual and joint data. Joint tour data is indexed by hh_id
     * so that it can be retrieved quickly for a household object. Individual tour data is
     * indexed by person_id.
     * 
     */
	public void readTourDataOutput(String filename, boolean isJoint, HashMap<Long, TourFileAttributes> tourFileAttributesMap ){
		
        TableDataSet tourData = readTableData(filename);

        tourFileAttributesMap = new HashMap<Long, TourFileAttributes>();
        
        for(int row = 1; row<=tourData.getRowCount();++row){
        	
    		long hh_id = (long) tourData.getValueAt(row,"hh_id");
    		long person_id = 0;
    		int person_num=0;
    		int person_type=0;
    		if(!isJoint){
    			person_id = (long) tourData.getValueAt(row,"person_id");;
    		    person_num            = (int) tourData.getValueAt(row,"person_num");            
        		person_type           = (int) tourData.getValueAt(row,"person_type");           
    		}
    		int tour_id               = (int) tourData.getValueAt(row,"tour_id");               
    		String tour_category      = tourData.getStringValueAt(row,"tour_category");         
    		String tour_purpose       = tourData.getStringValueAt(row,"tour_purpose");          
    		
    		int tour_composition = 0;
    		String tour_participants = null;
    		if(isJoint){
    			tour_composition = (int) tourData.getValueAt(row,"tour_composition");
    			tour_participants = tourData.getStringValueAt(row,"tour_participants");
    		}
    		
    		int orig_mgra             = (int) tourData.getValueAt(row,"orig_mgra");             
    		int dest_mgra             = (int) tourData.getValueAt(row,"dest_mgra");             
    		int start_period          = (int) tourData.getValueAt(row,"start_period");          
    		int end_period            = (int) tourData.getValueAt(row,"end_period");            
    		int tour_mode             = (int) tourData.getValueAt(row,"tour_mode");             
    		float tour_distance       = tourData.getValueAt(row,"tour_distance");               
    		float tour_time           = tourData.getValueAt(row,"tour_time");                   
    		int atWork_freq           = (int) tourData.getValueAt(row,"atWork_freq");           
    		int num_ob_stops          = (int) tourData.getValueAt(row,"num_ob_stops");          
    		int num_ib_stops          = (int) tourData.getValueAt(row,"num_ib_stops");          
    		int out_btap              = (int) tourData.getValueAt(row,"out_btap");              
    		int out_atap              = (int) tourData.getValueAt(row,"out_atap");              
    		int in_btap               = (int) tourData.getValueAt(row,"in_btap");               
    		int in_atap               = (int) tourData.getValueAt(row,"in_atap");               
    		int out_set               = (int) tourData.getValueAt(row,"out_set");               
    		int in_set                = (int) tourData.getValueAt(row,"in_set");                
    		float sampleRate          = tourData.getValueAt(row,"sampleRate");                  
    		int avAvailable           = (int) tourData.getValueAt(row,"avAvailable");           
    		float[] util = new float[modelStructure.getMaxTourModeIndex()];
    		float[] prob = new float[modelStructure.getMaxTourModeIndex()];
    		
    		for(int i = 0; i<util.length;++i){
    			String colName = "util_"+(i+1);
    			util[i]= tourData.getValueAt(row,colName);
    		}
    		
    		for(int i = 0; i<prob.length;++i){
    			String colName = "prob"+(i+1);
    			prob[i]= tourData.getValueAt(row,colName);
    		}
          
        	TourFileAttributes tourFileAttributes = new TourFileAttributes(hh_id, person_id, person_num, person_type,
    				 tour_id,  tour_category, tour_purpose, orig_mgra,dest_mgra,
    				 start_period, end_period, tour_mode, tour_distance, tour_time,
    				 atWork_freq,  num_ob_stops, num_ib_stops, out_btap, out_atap,
    				 in_btap, in_atap, out_set, in_set, sampleRate, avAvailable,
    				util, prob, tour_composition, tour_participants);
        	
        	tourFileAttributesMap.put(person_id,tourFileAttributes);
        	
        }

	}

	
	
	/**
	 * Set person attributes for this household object. This method uses
	 * the data in the personFileAttributesMap to set the data members of the
	 * Person objects for all persons in the household.
	 * 
	 * @param hhObject
	 */
	public void setPersonAttributes(Household hhObject){
		
		int hhid = hhObject.getHhId();
		for(Person p : hhObject.getPersons()){
			
			long person_id = p.getPersonId();
			PersonFileAttributes personFileAttributes = personFileAttributesMap.get(person_id);
			personFileAttributes.setPersonAttributes(p);
		}
	}
	
	
	
	/**
	 * A class to hold person file attributes (read in from Results.PersonDataFile)
	 * @author joel.freedman
	 *
	 */
	private class PersonFileAttributes{
       
		long hhid;
    	long person_id;
    	long personNumber;
    	int age;
    	int gender;
    	float valueOfTime;
    	String activityPattern;
    	int personType;
    	int imfChoice;
    	int inmfChoice;
    	int fp_choice;
    	float reimb_pct;
    	float sampleRate;

		public PersonFileAttributes(long hhid, long person_id, long personNumber, int age, int gender,float valueOfTime, 
				String activityPattern,int personType,
				int imfChoice,int inmfChoice,int fp_choice, float reimb_pct,float sampleRate){
			
			this.hhid=hhid;
			this.person_id = person_id;
			this.personNumber=personNumber;
			this.age=age;
			this.gender=gender;
			this.valueOfTime=valueOfTime;
			this.activityPattern=activityPattern;
			this.personType=personType;
			this.imfChoice=imfChoice;
			this.inmfChoice=inmfChoice;
			this.fp_choice=fp_choice;
			this.reimb_pct=reimb_pct;
			this.sampleRate=sampleRate;
		}
		
		
		public void setPersonAttributes(Person p){
			
			p.setPersAge(age);
			p.setPersGender(gender);
			p.setValueOfTime(valueOfTime);
			p.setDailyActivityResult(activityPattern);
			p.setPersonTypeCategory(personType);
			p.setImtfChoice(imfChoice);
			p.setInmtfChoice(inmfChoice);
			p.setFreeParkingAvailableResult(fp_choice);
			p.setParkingReimbursement(reimb_pct);
			p.setSampleRate(sampleRate);
			
		}
	}
	
	private class TourFileAttributes{
		
		long hh_id;
		long person_id;
		int person_num;
		int person_type;
		int tour_id;
		String tour_category;
		String tour_purpose;
		int orig_mgra;
		int dest_mgra;
		int start_period;
		int end_period;
		int tour_mode;
		float tour_distance;
		float tour_time;
		int atWork_freq;
		int num_ob_stops;
		int num_ib_stops;
		int out_btap;
		int out_atap;
		int in_btap;
		int in_atap;
		int out_set;
		int in_set;
		float sampleRate;
		int avAvailable;
		float[] util;
		float[] prob;
		
		//for joint tours
		int tour_composition;
		String tour_participants;

		public TourFileAttributes(long hh_id, long person_id, int person_num, int person_type,
				int tour_id, String tour_category,String tour_purpose, int orig_mgra,int dest_mgra,
				int start_period,int end_period,int tour_mode, float tour_distance,float tour_time,
				int atWork_freq, int num_ob_stops,int num_ib_stops,int out_btap,int out_atap,
				int in_btap,int in_atap,int out_set,int in_set,float sampleRate,int avAvailable,
				float[] util, float[] prob, int tour_composition,String tour_participants){
			
			
			this.hh_id = hh_id;
			this.person_id = person_id;
			this.person_num = person_num;
			this.person_type = person_type;
			this.tour_id = tour_id;
			this.tour_category = tour_category;
			this.tour_purpose = tour_purpose;
			this.orig_mgra = orig_mgra;
			this.dest_mgra = dest_mgra;
			this.start_period = start_period;
			this.end_period = end_period;
			this.tour_mode = tour_mode;
			this.tour_distance = tour_distance;
			this.tour_time = tour_time;
			this.atWork_freq = atWork_freq;
			this.num_ob_stops = num_ob_stops;
			this.num_ib_stops = num_ib_stops;
			this.out_btap = out_btap;
			this.out_atap = out_atap;
			this.in_btap = in_btap;
			this.in_atap = in_atap;
			this.out_set = out_set;
			this.in_set = in_set;
			this.sampleRate = sampleRate;
			this.avAvailable = avAvailable;
			this.util = util;
			this.prob = prob;
			this.tour_composition = tour_composition;
			this.tour_participants = tour_participants;
						
		}
		
		
		
	}
	
	public void createIndividualMandatoryTours(int indMandTourFreqChoice, Person person){
		
        // set the person choices
        if (indMandTourFreqChoice == HouseholdIndividualMandatoryTourFrequencyModel.CHOICE_ONE_WORK)
        {
            person.createWorkTours(1, 0, ModelStructure.WORK_PRIMARY_PURPOSE_NAME,
                    ModelStructure.WORK_PRIMARY_PURPOSE_INDEX);
        } else if (indMandTourFreqChoice == HouseholdIndividualMandatoryTourFrequencyModel.CHOICE_TWO_WORK)
        {
            person.createWorkTours(2, 0, ModelStructure.WORK_PRIMARY_PURPOSE_NAME,
                    ModelStructure.WORK_PRIMARY_PURPOSE_INDEX);
        } else if (indMandTourFreqChoice == HouseholdIndividualMandatoryTourFrequencyModel.CHOICE_ONE_SCHOOL)
        {
            if (person.getPersonIsUniversityStudent() == 1) person.createSchoolTours(1,
                    0, ModelStructure.UNIVERSITY_PRIMARY_PURPOSE_NAME,
                    ModelStructure.UNIVERSITY_PRIMARY_PURPOSE_INDEX);
            else person.createSchoolTours(1, 0,
                    ModelStructure.SCHOOL_PRIMARY_PURPOSE_NAME,
                    ModelStructure.SCHOOL_PRIMARY_PURPOSE_INDEX);
        } else if (indMandTourFreqChoice == HouseholdIndividualMandatoryTourFrequencyModel.CHOICE_TWO_SCHOOL)
        {
            if (person.getPersonIsUniversityStudent() == 1) person.createSchoolTours(2,
                    0, ModelStructure.UNIVERSITY_PRIMARY_PURPOSE_NAME,
                    ModelStructure.UNIVERSITY_PRIMARY_PURPOSE_INDEX);
            else person.createSchoolTours(2, 0,
                    ModelStructure.SCHOOL_PRIMARY_PURPOSE_NAME,
                    ModelStructure.SCHOOL_PRIMARY_PURPOSE_INDEX);
        } else if (indMandTourFreqChoice == HouseholdIndividualMandatoryTourFrequencyModel.CHOICE_WORK_AND_SCHOOL)
        {
            person.createWorkTours(1, 0, ModelStructure.WORK_PRIMARY_PURPOSE_NAME,
                    ModelStructure.WORK_PRIMARY_PURPOSE_INDEX);
            if (person.getPersonIsUniversityStudent() == 1) person.createSchoolTours(1,
                    0, ModelStructure.UNIVERSITY_PRIMARY_PURPOSE_NAME,
                    ModelStructure.UNIVERSITY_PRIMARY_PURPOSE_INDEX);
            else person.createSchoolTours(1, 0,
                    ModelStructure.SCHOOL_PRIMARY_PURPOSE_NAME,
                    ModelStructure.SCHOOL_PRIMARY_PURPOSE_INDEX);
        }
    }

	
	/**
	 * Calculate person type value based on string.
	 * @param personTypeString
	 * @return
	 */
	private int getPersonType(String personTypeString){
		
		for(int i =0;i<Person.personTypeNameArray.length;++i){
			
			if(personTypeString.compareTo(Person.personTypeNameArray[i])==0)
				return i;
			
		}
	   
		//should never be here
		return -1;
		
	}

	
	public void readHouseholdDataOutput(){
	
		String baseDir = rbMap.get(CtrampApplication.PROPERTIES_PROJECT_DIRECTORY);
		String hhFile = formFileName(rbMap.get(PROPERTIES_HOUSEHOLD_DATA_FILE), iteration);
	    
	}
	
	public void readTourDataOutput(){
		
		String baseDir = rbMap.get(CtrampApplication.PROPERTIES_PROJECT_DIRECTORY);
	    String indivTourFile = formFileName(rbMap.get(PROPERTIES_INDIV_TOUR_DATA_FILE), iteration);
        String jointTourFile = formFileName(rbMap.get(PROPERTIES_JOINT_TOUR_DATA_FILE), iteration);

	}
	
	/**
	 * Read data into inputDataTable tabledataset.
	 * 
	 */
	private TableDataSet readTableData(String inputFile){
		
		TableDataSet tableDataSet = null;
		
		logger.info("Begin reading the data in file " + inputFile);
	    
	    try
	    {
	    	OLD_CSVFileReader csvFile = new OLD_CSVFileReader();
	    	tableDataSet = csvFile.readFile(new File(inputFile));
	    } catch (IOException e)
	    {
	    	throw new RuntimeException(e);
        }
        logger.info("End reading the data in file " + inputFile);
        
        return tableDataSet;
	}
	


}
