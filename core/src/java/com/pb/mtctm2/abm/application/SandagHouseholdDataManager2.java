package com.pb.mtctm2.abm.application;

import com.pb.common.datafile.OLD_CSVFileReader;
import com.pb.common.datafile.TableDataSet;
import com.pb.common.util.IndexSort;
import com.pb.mtctm2.abm.ctramp.Household;
import com.pb.mtctm2.abm.ctramp.HouseholdDataManager;
import com.pb.mtctm2.abm.ctramp.Person;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.HashSet;
import java.util.Set;

import gnu.cajo.invoke.Remote;
import gnu.cajo.utils.ItemServer;

/**
 * @author Jim Hicks
 * 
 *         Class for managing household and person object data read from synthetic
 *         population files.
 */
public class SandagHouseholdDataManager2
        extends HouseholdDataManager
{


    public static final String HH_DATA_SERVER_NAME       = SandagHouseholdDataManager.class.getCanonicalName();
    public static final String HH_DATA_SERVER_ADDRESS    = "127.0.0.1";
    public static final int    HH_DATA_SERVER_PORT       = 1139;

    //public static final String PROPERTIES_OCCUP_CODES    = "PopulationSynthesizer.OccupCodes";
    //public static final String PROPERTIES_INDUSTRY_CODES = "PopulationSynthesizer.IndustryCodes";
    
    public static final int MIN_EMPLOYMENT_AGE = 16;
    public static final int MIN_SCHOOL_AGE = 6;
    public static final int MIN_DRIVING_AGE = 16;
    public static final int MAX_SCHOOL_AGE = 19;
    public static final int RETIREMENT_AGE = 65;

    public SandagHouseholdDataManager2()
    {
        super();
    }

    /**
     * Associate data in hh and person TableDataSets read from synthetic population
     * files with Household objects and Person objects with Households.
     * 
     */
    public void mapTablesToHouseholdObjects()
    {

        logger.info("mapping popsyn household and person data records to objects.");

        int id = -1;

        int invalidPersonTypeCount1 = 0;
        int invalidPersonTypeCount2 = 0;
        int invalidPersonTypeCount3 = 0;

        // read the corrrespondence files for mapping persons to occupation and
        //int[] occCodes = readOccupCorrespondenceData();
        //int[] indCodes = readIndustryCorrespondenceData();

        // get the maximum HH id value to use to dimension the hhIndex correspondence
        // array.  The hhIndex array will store the hhArray index number for the given
        // hh index.
        int maxHhId = 0;
        for (int r = 1; r <= hhTable.getRowCount(); r++)
        {
            id = (int) hhTable.getValueAt(r, hhTable.getColumnPosition(HH_ID_FIELD_NAME));
            if (id > maxHhId) maxHhId = id;
        }
        hhIndexArray = new int[maxHhId + 1];

        // get an index array for households sorted in random order - to remove the original order
        int[] firstSortedIndices = getRandomOrderHhIndexArray(hhTable.getRowCount());

        // get a second index array for households sorted in random order - to select a sample from the randomly ordered hhs
        int[] randomSortedIndices = getRandomOrderHhIndexArray(hhTable.getRowCount());

        hhs = null;

        int numHouseholdsInSample = (int) (hhTable.getRowCount() * sampleRate);
        Household[] hhArray = new Household[numHouseholdsInSample];


        
//        String outputFileName = "sample_hh_mgra_taz_seed_" + sampleSeed + ".csv";
//        PrintWriter outStream = null;
//        try {
//            outStream = new PrintWriter(new BufferedWriter(new FileWriter(new File(outputFileName))));
//            outStream.println("i,mgra,taz");
//        }
//        catch (IOException e) {
//            logger.fatal(String.format("Exception occurred opening output skims file: %s.", outputFileName));
//            throw new RuntimeException(e);
//        }


        Set<Integer> mgrasUsed = new HashSet<>();
        int[] hhOriginSortArray = new int[numHouseholdsInSample];
        for (int i = 0; i < numHouseholdsInSample; i++)
        {
            int r = firstSortedIndices[randomSortedIndices[i]] + 1;
//            int hhId = (int) hhTable.getValueAt(r, hhTable.getColumnPosition(HH_ID_FIELD_NAME));
            int hhMgra = (int) hhTable.getValueAt(r, hhTable.getColumnPosition(HH_HOME_MGRA_FIELD_NAME));
            int hhTaz = (int) hhTable.getValueAt(r, hhTable.getColumnPosition(HH_HOME_TAZ_FIELD_NAME));
            hhOriginSortArray[i] = hhMgra;
            mgrasUsed.add(hhMgra);

//            outStream.println(i + "," + hhMgra + "," + hhTaz);
        }

//        outStream.close();
//        System.exit(1);
        
        
            
        logger.info( mgrasUsed.size() + " unique MGRA values in the " + (sampleRate*100) + "% sample." );
        
        // get an index array for households sorted in order of home mgra
        int[] newOrder = new int[numHouseholdsInSample];
        int[] sortedIndices = IndexSort.indexSort(hhOriginSortArray);
        for (int i = 0; i < sortedIndices.length; i++)
        {
            int k = sortedIndices[i];
            newOrder[k] = i;
        }

        // for each household in the sample
        for (int i = 0; i < numHouseholdsInSample; i++)
        {
            int r = firstSortedIndices[randomSortedIndices[i]] + 1;
            try
            {
                // create a Household object
                Household hh = new Household(modelStructure);

                // get required values from table record and store in Household
                // object
                id = (int) hhTable.getValueAt(r, hhTable.getColumnPosition(HH_ID_FIELD_NAME));
                hh.setHhId(id, inputRandomSeed);

                // set the household in the hhIndexArray in random order
                int newIndex = newOrder[i];
                hhIndexArray[hh.getHhId()] = newIndex;

                int htaz = (int) hhTable.getValueAt(r, hhTable.getColumnPosition(HH_HOME_TAZ_FIELD_NAME));
                hh.setHhTaz(htaz);

                int hmgra = (int) hhTable.getValueAt(r, hhTable.getColumnPosition(HH_HOME_MGRA_FIELD_NAME));
                hh.setHhMgra(hmgra);

                int countyid = (int) hhTable.getValueAt(r, hhTable.getColumnPosition(HH_COUNTYID_FIELD_NAME));
                hh.setCountyId(countyid);
                
                // autos could be modeled or from PUMA
                int numAutos = (int) hhTable.getValueAt(r, hhTable
                        .getColumnPosition(HH_AUTOS_FIELD_NAME));
                hh.setHhAutos(numAutos);

                // set the hhSize variable and create Person objects for each person
                int numPersons = (int) hhTable.getValueAt(r, hhTable
                        .getColumnPosition(HH_SIZE_FIELD_NAME));
                hh.setHhSize(numPersons);

                int numWorkers = (int) hhTable.getValueAt(r, hhTable
                        .getColumnPosition(HH_WORKERS_FIELD_NAME));
                hh.setHhWorkers(numWorkers);

                int incomeInDollars = (int) hhTable.getValueAt(r, hhTable.getColumnPosition(HH_INCOME_DOLLARS_FIELD_NAME));
                if(incomeInDollars >= 150000)
                	hh.setHhIncome(5);
                else if(incomeInDollars >= 100000)
                	hh.setHhIncome(4);
                else if(incomeInDollars >= 60000)
                	hh.setHhIncome(5);
                else if(incomeInDollars >= 30000)
                	hh.setHhIncome(2);
                else
                	hh.setHhIncome(1);

                hh.setHhIncomeInDollars(incomeInDollars);

                // 0=Housing unit, 1=Institutional group quarters, 2=Noninstitutional
                // group quarters
                int unitType = (int) hhTable.getValueAt(r, hhTable
                        .getColumnPosition(HH_UNITTYPE_FIELD_NAME));
                hh.setUnitType(unitType);

                // 1=Family household:married-couple, 2=Family household:male
                // householder,no wife present, 3=Family household:female
                // householder,no
                // husband present
                // 4=Nonfamily household:male householder, living alone, 5=Nonfamily
                // household:male householder, not living alone,
                // 6=Nonfamily household:female householder, living alone,
                // 7=Nonfamily household:female householder, not living alone
                int type = (int) hhTable.getValueAt(r, hhTable
                        .getColumnPosition(HH_TYPE_FIELD_NAME));
                hh.setHhType(type);

                // 1=mobile home, 2=one-family house detached from any other house,
                // 3=one-family house attached to one or more houses,
                // 4=building with 2 apartments, 5=building with 3 or 4 apartments,
                // 6=building with 5 to 9 apartments,
                // 7=building with 10 to 19 apartments, 8=building with 20 to 49
                // apartments,
                // 9=building with 50 or more apartments, 10=Boat,RV,van,etc.
                int bldgsz = (int) hhTable.getValueAt(r, hhTable
                        .getColumnPosition(HH_BLDGSZ_FIELD_NAME));
                hh.setHhBldgsz(bldgsz);

                hh.initializeWindows();
                hhArray[newIndex] = hh;

            } catch (Exception e)
            {

                logger.fatal(String.format(
                    "exception caught mapping household data record to a Household object, r=%d, id=%d.",
                    r, id));
                throw new RuntimeException(e);

            }

        }

        int[] personHhStart = new int[maxHhId + 1];
        int[] personHhEnd = new int[maxHhId + 1];

        // get hhid for person record 1
        int hhid = (int) personTable.getValueAt(1, personTable
                .getColumnPosition(PERSON_HH_ID_FIELD_NAME));
        personHhStart[hhid] = 1;
        int oldHhid = hhid;

        for (int r = 1; r <= personTable.getRowCount(); r++)
        {

            // get the Household object for this person data to be stored in
            hhid = (int) personTable.getValueAt(r, personTable
                    .getColumnPosition(PERSON_HH_ID_FIELD_NAME));

            if (hhid != oldHhid)
            {
                personHhEnd[oldHhid] = r - 1;
                oldHhid = hhid;
                personHhStart[hhid] = r;
            }

        }
        personHhEnd[hhid] = personTable.getRowCount();

        int r = 0;
        int p = 0;
        int persId = 0;
        int persNum = 0;
        int fieldCount = 0;

        for (int i = 0; i < numHouseholdsInSample; i++)
        {

            try
            {

                r = firstSortedIndices[randomSortedIndices[i]] + 1;

                hhid = (int) hhTable.getValueAt(r, hhTable
                        .getColumnPosition(PERSON_HH_ID_FIELD_NAME));

                int index = hhIndexArray[hhid];
                Household hh = hhArray[index];

                persNum = 1;

                for (p = personHhStart[hhid]; p <= personHhEnd[hhid]; p++)
                {

                    fieldCount = 0;
                    
                    // get the Person object for this person data to be stored in
                    persId = (int) personTable.getValueAt(p, personTable.getColumnPosition(PERSON_PERSON_ID_FIELD_NAME));
                    Person person = hh.getPerson(persNum++);
                    person.setPersId(persId);
                    fieldCount++;

                    // get required values from table record and store in Person
                    // object
                    int age = (int) personTable.getValueAt(p, personTable.getColumnPosition(PERSON_AGE_FIELD_NAME));
                    person.setPersAge(age);
                    fieldCount++;

                    int gender = (int) personTable.getValueAt(p, personTable.getColumnPosition(PERSON_GENDER_FIELD_NAME));
                    person.setPersGender(gender);
                    fieldCount++;

                    int pecasOcc = (int)personTable.getValueAt( p, personTable.getColumnPosition( PERSON_OCCP_FIELD_NAME ) );
                    if (pecasOcc == 0) logger.warn("pecasOccup==0 for occ=" + pecasOcc);
                    person.setPersPecasOccup( pecasOcc );
                    fieldCount++;

                    // read fields for determining person's employment category
                    int esr = (int)personTable.getValueAt( p, personTable.getColumnPosition( PERSON_ESR_FIELD_NAME ) );
                    int wkhp = (int)personTable.getValueAt( p, personTable.getColumnPosition( PERSON_HOURS_WORKED_FIELD_NAME ) );
                    int wkw = (int)personTable.getValueAt( p, personTable.getColumnPosition( PERSON_WEEKS_WORKED_FIELD_NAME ) );
                    // 1-employed FT, 2-employed PT, 3-not employed, 4-under age 16
                    int empCat = computeEmploymentCategory( age, esr, wkhp, wkw); 
                    person.setPersEmploymentCategory( empCat );
                    fieldCount++;

                    // determine person's student category
                    // 1-in high school or lower, 2-in trade school, college or higher, 3-not attending school 
                    int schg = (int)personTable.getValueAt( p, personTable.getColumnPosition(PERSON_GRADE_ATTENDING_FIELD_NAME));
                    int studentCat = computeStudentCategory(schg, age, empCat);
                    person.setPersStudentCategory( studentCat );
                    fieldCount++;

                    // determine person's type category 
                    // 1-FT worker age 16+, 2-PT worker nonstudent age 16+, 3-university student, 4-nonworker nonstudent age 16-64,
                    // 5-nonworker nonstudent age 65+, 6-"age 16-19 student, not FT wrkr or univ stud", 7-age 6-15 schpred, 8  under age 6 presch
                    int personType = computePersonType( age, empCat, studentCat );
                    person.setPersonTypeCategory( personType );
                    fieldCount++;

                    // Person educational attainment level to determine high school
                    // graduate status ( < 9 - not a graduate, 10+ - high school
                    // graduate
                    // and beyond)
                    int educ = (int) personTable.getValueAt(p, personTable.getColumnPosition(PERSON_EDUCATION_ATTAINMENT_FIELD_NAME));
                    if (educ >= 9)
                        person.setPersonIsHighSchoolGraduate(true);
                    else
                        person.setPersonIsHighSchoolGraduate(false);
                    fieldCount++;

                    // Person educational attainment level to determine higher
                    // education status ( > 12 - at least a bachelor's degree )
                    if (educ >= 13)
                        person.setPersonHasBachelors(true);
                    else
                        person.setPersonHasBachelors(false);
                    fieldCount++;

                    // Person grade enrolled in ( 0-"not enrolled", 1-"preschool",
                    // 2-"Kindergarten", 3-"Grade 1 to grade 4",
                    // 4-"Grade 5 to grade 8", 5-"Grade 9 to grade 12",
                    // 6-"College undergraduate", 7-"Graduate or professional school"
                    // )
                    int grade = (int) personTable.getValueAt(p, personTable.getColumnPosition(PERSON_GRADE_ATTENDING_FIELD_NAME));
                    person.setPersonIsGradeSchool(false);
                    person.setPersonIsHighSchool(false);
                    if (grade >= 2 && grade <= 4) {
                        // change person type if person was 5 or under but enrolled in K-8.
                        if ( person.getPersonIsPreschoolChild() == 1 )
                            person.setPersonTypeCategory( Person.PersonType.Student_age_6_15_schpred.ordinal() );
                        
                        person.setPersonIsGradeSchool(true);
                    }
                    else if (grade == 5) {
                        person.setPersonIsHighSchool(true);
                    }
                    fieldCount++;

                    // if person is a university student but has school age student
                    // category value, reset student category value
                    if (personType == Person.PersonType.University_student.ordinal()
                            && studentCat != Person.StudentStatus.STUDENT_COLLEGE_OR_HIGHER
                                    .ordinal())
                    {
                        studentCat = Person.StudentStatus.STUDENT_COLLEGE_OR_HIGHER.ordinal();
                        person.setPersStudentCategory(studentCat);
                        invalidPersonTypeCount1++;
                        
                        //ensure they are not tagged as grade or high school student
                        person.setPersonIsGradeSchool(false);
                        person.setPersonIsHighSchool(false);
                        
                    }
                    // if person is a student of any kind but has full-time
                    // employment status, reset student category value to non-student
                    else if (studentCat != Person.StudentStatus.NON_STUDENT.ordinal()
                            && empCat == Person.EmployStatus.FULL_TIME.ordinal())
                    {
                        studentCat = Person.StudentStatus.NON_STUDENT.ordinal();
                        person.setPersStudentCategory(studentCat);
                        invalidPersonTypeCount2++;
                    }
                    fieldCount++;

                    // check consistency of student category and person type
                    if (studentCat == Person.StudentStatus.NON_STUDENT.ordinal())
                    {

                        if (person.getPersonIsStudentNonDriving() == 1
                                || person.getPersonIsStudentDriving() == 1)
                        {
                            studentCat = Person.StudentStatus.STUDENT_HIGH_SCHOOL_OR_LESS.ordinal();
                            person.setPersStudentCategory(studentCat);
                            invalidPersonTypeCount3++;
                        }

                    }
                    fieldCount++;

                }

            } catch (Exception e)
            {

                logger.fatal(String.format(
                    "exception caught mapping person data record to a Person object, i=%d, r=%d, p=%d, hhid=%d, persid=%d, persnum=%d, fieldCount=%d.",
                    i, r, p, hhid, persId, persNum, fieldCount));
                throw new RuntimeException(e);

            }

        } // person loop

        hhs = hhArray;

        logger.warn(invalidPersonTypeCount1 + " person type = university and student category = non-student person records had their student category changed to university or higher.");
        logger.warn(invalidPersonTypeCount2 + " Student category = student and employment category = full-time worker person records had their student category changed to non-student.");
        logger.warn(invalidPersonTypeCount3 + " Student category = non-student and person type = student person records had their student category changed to student high school or less.");

        logger.info("Setting distributed values of time. "); 
        setDistributedValuesOfTime(); 
        
    }

    /**
     * if called, must be called after readData so that the size of the full
     * population is known.
     * 
     * @param hhFileName
     * @param persFileName
     * @param numHhs
     */
    public void createSamplePopulationFiles(String hhFileName, String persFileName,
            String newHhFileName, String newPersFileName, int numHhs)
    {

        int maximumHhId = 0;
        for (int i = 0; i < hhs.length; i++)
        {
            int id = hhs[i].getHhId();
            if (id > maximumHhId) maximumHhId = id;
        }

        int[] testHhs = new int[maximumHhId + 1];

        int[] sortedIndices = getRandomOrderHhIndexArray(hhs.length);

        for (int i = 0; i < numHhs; i++)
        {
            int k = sortedIndices[i];
            int hhId = hhs[k].getHhId();
            testHhs[hhId] = 1;
        }

        String hString = "";
        int hCount = 0;
        try
        {

            logger.info(String.format("writing sample household file for %d households", numHhs));

            PrintWriter out = new PrintWriter(new BufferedWriter(new FileWriter(newHhFileName)));
            BufferedReader in = new BufferedReader(new FileReader(hhFileName));

            // read headers and write to output files
            hString = in.readLine();
            out.write(hString + "\n");
            hCount++;
            int count = 0;

            while ((hString = in.readLine()) != null)
            {
                hCount++;
                int endOfField = hString.indexOf(',');
                int hhId = Integer.parseInt(hString.substring(0, endOfField));

                // if it's a sample hh, write the hh and the person records
                if (testHhs[hhId] == 1)
                {
                    out.write(hString + "\n");
                    count++;
                    if (count == numHhs) break;
                }
            }

            out.close();

        } catch (IOException e)
        {
            logger.fatal("IO Exception caught creating sample synpop household file.");
            logger.fatal(String.format("reading hh file = %s, writing sample hh file = %s.",
                    hhFileName, newHhFileName));
            logger.fatal(String.format("hString = %s, hCount = %d.", hString, hCount));
        }

        String pString = "";
        int pCount = 0;
        try
        {

            logger.info(String.format("writing sample person file for selected households"));

            PrintWriter out = new PrintWriter(new BufferedWriter(new FileWriter(newPersFileName)));
            BufferedReader in = new BufferedReader(new FileReader(persFileName));

            // read headers and write to output files
            pString = in.readLine();
            out.write(pString + "\n");
            pCount++;
            int count = 0;
            int oldId = 0;
            while ((pString = in.readLine()) != null)
            {
                pCount++;
                int endOfField = pString.indexOf(',');
                int hhId = Integer.parseInt(pString.substring(0, endOfField));

                // if it's a sample hh, write the hh and the person records
                if (testHhs[hhId] == 1)
                {
                    out.write(pString + "\n");
                    if (hhId > oldId) count++;
                } else
                {
                    if (count == numHhs) break;
                }

                oldId = hhId;

            }

            out.close();

        } catch (IOException e)
        {
            logger.fatal("IO Exception caught creating sample synpop person file.");
            logger.fatal(String.format(
                    "reading person file = %s, writing sample person file = %s.", persFileName,
                    newPersFileName));
            logger.fatal(String.format("pString = %s, pCount = %d.", pString, pCount));
        }

    }
    
    /* 
     * Function determine person type. Returns:
	  * 	1 - FT worker age 16+
	  * 	2 - PT worker non-student age 16+
	  * 	3 - university student
	  * 	4 - non-worker non-student age 16-64
	  *     5 - non-worker non-student age 65+
	  *     6 - age 16-19 student, not FT worker or university student
	  *     7 - age 6-15 pre-drive school student
	  * 	8 - under age 6 children
	  */
    private int computePersonType(int age, int empCat, int studentCat) {

    	int personType=0;
		   
		if (empCat==1)	// full time worker
			personType = Person.PersonType.FT_worker_age_16plus.ordinal();
		else 
			if (studentCat==3) 		// not studying
				if (empCat==2)		// part-time worker
					personType = Person.PersonType.PT_worker_nonstudent_age_16plus.ordinal();
				else {
					//empCat==3, not employed and not studying
					if (age>=RETIREMENT_AGE) 		// retired
						personType = Person.PersonType.Nonworker_nonstudent_age_65plus.ordinal();		
					else if (age<MIN_SCHOOL_AGE) 	// young child not studying
						personType = Person.PersonType.Preschool_under_age_6.ordinal();		
					else							// unemployed, non-student, age 16-64 
						personType = Person.PersonType.Nonworker_nonstudent_age_16_64.ordinal();		
				}
			else if (studentCat==2)	// University/GED/Trade student either working PT or not employed
					personType = Person.PersonType.University_student.ordinal();
			else {
				 // studentCat==1, student in high school or lower
				if (age<MIN_SCHOOL_AGE)			// young children in daycare/preschool or non-student
					personType = Person.PersonType.Preschool_under_age_6.ordinal();			
				else if (age>=MIN_DRIVING_AGE)	// student of driving age (16-19)
					personType = Person.PersonType.Student_age_16_19_not_FT_wrkr_or_univ_stud.ordinal();
				else							// grade~high school student too young to drive
					personType = Person.PersonType.Student_age_6_15_schpred.ordinal();			
			}		
			
		return personType;
	}


	 /* 
     * Function determine the student status of a person. Returns:
     *		1 - student in high school or lower (including nursery and preschool)
 	  *     2 - student in trade school, college or higher
     *     3 - not attending school 
     */
     private int computeStudentCategory(int schg, int age, int empCat) {
		int studentCat;
    
		if ( (empCat==1) || (schg<1) ) {// full time workers or those with no grade-attending info cannot be students 
			studentCat = Person.StudentStatus.NON_STUDENT.ordinal();
			if (age<MIN_DRIVING_AGE) // but if under minimum driving age, reset to high school or lower
					studentCat = Person.StudentStatus.STUDENT_HIGH_SCHOOL_OR_LESS.ordinal(); 				
		}
		else 
			if (schg>=6) { // attending college or above
				studentCat = Person.StudentStatus.STUDENT_COLLEGE_OR_HIGHER.ordinal();
				if (age<MIN_DRIVING_AGE) // but if under minimum driving age, reset to high school or lower
					studentCat = Person.StudentStatus.STUDENT_HIGH_SCHOOL_OR_LESS.ordinal();
			}
			else {		// attending high school or lower
				studentCat = Person.StudentStatus.STUDENT_HIGH_SCHOOL_OR_LESS.ordinal();
				if (age>MAX_SCHOOL_AGE)	// but if too old for school, reset to college or above
					studentCat = Person.StudentStatus.STUDENT_COLLEGE_OR_HIGHER.ordinal();
			}
		
		return studentCat;
	}

    
    /* 
     * Function determine the employment category of a person. Returns:
	  * 	1 - employed fulltime
	  * 	2 - employed parttime
	  * 	3 - age 16 and over and not employed
	  * 	4 - under age 16
	  */
	private int computeEmploymentCategory(int age, int esr, int wkhp, int wkw) {
    	 int empCat = 0;
     		
    	 if (age < MIN_EMPLOYMENT_AGE )	// under employment age
    		 empCat = Person.EmployStatus.UNDER16.ordinal();
    	 else {
    		 if ( (esr==3) || (esr==6) )	// over employment age and not employed
    			 empCat = Person.EmployStatus.NOT_EMPLOYED.ordinal();
    		 else
    			 if ( (wkhp>=35) && (wkw>=1) && (wkw<=4) ) // over employment age, working at least 35 hrs a week and 27+weeks a year
    				 empCat = Person.EmployStatus.FULL_TIME.ordinal();
    			 else
    				 empCat = Person.EmployStatus.PART_TIME.ordinal();
    	 }
    		 
    	 return empCat;
	}

    public static void main(String args[]) throws Exception
    {

        String serverAddress = HH_DATA_SERVER_ADDRESS;
        int serverPort = HH_DATA_SERVER_PORT;

        // optional arguments
        for (int i = 0; i < args.length; i++)
        {
            if (args[i].equalsIgnoreCase("-hostname"))
            {
                serverAddress = args[i + 1];
            }

            if (args[i].equalsIgnoreCase("-port"))
            {
                serverPort = Integer.parseInt(args[i + 1]);
            }
        }

        Remote.config(serverAddress, serverPort, null, 0);

        SandagHouseholdDataManager2 hhDataManager = new SandagHouseholdDataManager2();

        ItemServer.bind(hhDataManager, HH_DATA_SERVER_NAME);

        System.out.println(String.format( "MTCTM2 Household Data Manager server started on: %s:%d", serverAddress, serverPort) );

    }

    public int[] getJointToursByHomeMgra(String purposeString)
    {
        // TODO Auto-generated method stub
        return null;
    }

}
