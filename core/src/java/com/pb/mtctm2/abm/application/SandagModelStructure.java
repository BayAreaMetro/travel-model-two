package com.pb.mtctm2.abm.application;


import com.pb.mtctm2.abm.ctramp.ModelStructure;

import java.util.HashMap;
import java.util.ArrayList;

import com.pb.mtctm2.abm.ctramp.Modes;

public class SandagModelStructure
        extends ModelStructure
{

    public final String[]        MANDATORY_DC_PURPOSE_NAMES                                         = {
            WORK_PURPOSE_NAME, UNIVERSITY_PURPOSE_NAME, SCHOOL_PURPOSE_NAME                         };
    public final String[]        WORK_PURPOSE_SEGMENT_NAMES                                         = {
            "low", "med", "high", "very high", "part time"                                          };
    public final String[]        UNIVERSITY_PURPOSE_SEGMENT_NAMES                                   = {};
    public final String[]        SCHOOL_PURPOSE_SEGMENT_NAMES                                       = {
            "predrive", "drive"                                                                     };

    public final int             USUAL_WORK_AND_SCHOOL_LOCATION_SOA_UEC_INDEX_WORK_LO               = 1;
    public final int             USUAL_WORK_AND_SCHOOL_LOCATION_SOA_UEC_INDEX_WORK_MD               = 2;
    public final int             USUAL_WORK_AND_SCHOOL_LOCATION_SOA_UEC_INDEX_WORK_HI               = 3;
    public final int             USUAL_WORK_AND_SCHOOL_LOCATION_SOA_UEC_INDEX_WORK_VHI              = 4;
    public final int             USUAL_WORK_AND_SCHOOL_LOCATION_SOA_UEC_INDEX_WORK_PT               = 5;
    public final int             USUAL_WORK_AND_SCHOOL_LOCATION_SOA_UEC_INDEX_UNIVERSITY_UNIVERSITY = 6;
    public final int             USUAL_WORK_AND_SCHOOL_LOCATION_SOA_UEC_INDEX_SCHOOL_UNDER_SIXTEEN  = 7;
    public final int             USUAL_WORK_AND_SCHOOL_LOCATION_SOA_UEC_INDEX_SCHOOL_SIXTEEN_PLUS   = 8;

    public final int             USUAL_WORK_AND_SCHOOL_LOCATION_UEC_INDEX_WORK                      = 1;
    public final int             USUAL_WORK_AND_SCHOOL_LOCATION_UEC_INDEX_UNIVERSITY                = 2;
    public final int             USUAL_WORK_AND_SCHOOL_LOCATION_UEC_INDEX_SCHOOL                    = 3;

    public final int             USUAL_WORK_AND_SCHOOL_LOCATION_MODE_CHOICE_UEC_INDEX_WORK          = 1;
    public final int             USUAL_WORK_AND_SCHOOL_LOCATION_MODE_CHOICE_UEC_INDEX_UNIVERSITY    = 2;
    public final int             USUAL_WORK_AND_SCHOOL_LOCATION_MODE_CHOICE_UEC_INDEX_SCHOOL        = 3;

    public final int             MANDATORY_STOP_FREQ_UEC_INDEX_WORK                                 = 1;
    public final int             MANDATORY_STOP_FREQ_UEC_INDEX_UNIVERSITY                           = 2;
    public final int             MANDATORY_STOP_FREQ_UEC_INDEX_SCHOOL                               = 3;

    public final int             MANDATORY_STOP_LOC_UEC_INDEX_WORK                                  = 1;
    public final int             MANDATORY_STOP_LOC_UEC_INDEX_UNIVERSITY                            = 1;
    public final int             MANDATORY_STOP_LOC_UEC_INDEX_SCHOOL                                = 1;

    public final int             MANDATORY_TRIP_MODE_CHOICE_UEC_INDEX_WORK                          = 1;
    public final int             MANDATORY_TRIP_MODE_CHOICE_UEC_INDEX_UNIVERSITY                    = 2;
    public final int             MANDATORY_TRIP_MODE_CHOICE_UEC_INDEX_SCHOOL                        = 3;

    public final String[]        NON_MANDATORY_DC_PURPOSE_NAMES                                     = {
            "escort", "shopping", "eatOut", "othMaint", "visit", "othDiscr"                         };
    public final String[]        ESCORT_PURPOSE_SEGMENT_NAMES                                       = {
            "kids", "no kids"                                                                       };
    public final String[]        SHOPPING_PURPOSE_SEGMENT_NAMES                                     = {};
    public final String[]        EAT_OUT_PURPOSE_SEGMENT_NAMES                                      = {};
    public final String[]        OTH_MAINT_PURPOSE_SEGMENT_NAMES                                    = {};
    public final String[]        SOCIAL_PURPOSE_SEGMENT_NAMES                                       = {};
    public final String[]        OTH_DISCR_PURPOSE_SEGMENT_NAMES                                    = {};

  
    public final String[]        AT_WORK_DC_PURPOSE_NAMES                                           = {"atwork"};
    public final String[]        AT_WORK_DC_SIZE_SEGMENT_NAMES                                      = {
            "cbd", "urban", "suburban", "rural"                                                     };

    public final int             AT_WORK_SOA_UEC_INDEX_EAT                                          = 16;
    public final int             AT_WORK_SOA_UEC_INDEX_BUSINESS                                     = 17;
    public final int             AT_WORK_SOA_UEC_INDEX_MAINT                                        = 18;

    public final int             AT_WORK_DC_UEC_INDEX_EAT                                           = 10;
    public final int             AT_WORK_DC_UEC_INDEX_BUSINESS                                      = 10;
    public final int             AT_WORK_DC_UEC_INDEX_MAINT                                         = 10;

    public final int             AT_WORK_MC_UEC_INDEX_EAT                                           = 5;
    public final int             AT_WORK_MC_UEC_INDEX_BUSINESS                                      = 5;
    public final int             AT_WORK_MC_UEC_INDEX_MAINT                                         = 5;

    public final int             SD_AT_WORK_PURPOSE_INDEX_EAT                                      = 1;
    public final int             SD_AT_WORK_PURPOSE_INDEX_BUSINESS                                 = 2;
    public final int             SD_AT_WORK_PURPOSE_INDEX_MAINT                                    = 3;

    public final int             AT_WORK_STOP_FREQ_UEC_INDEX_EAT                                    = 9;
    public final int             AT_WORK_STOP_FREQ_UEC_INDEX_BUSINESS                               = 9;
    public final int             AT_WORK_STOP_FREQ_UEC_INDEX_MAINT                                  = 9;

    // TODO: set these values from project specific code.
    public static final int[]    SOV_ALTS                                                           = {
            1, 2                                                                                    };
    public static final int[]    HOV_ALTS                                                           = {
        3, 4, 5, 6, 7, 8                                                                        };
    public static final int[]    HOV2_ALTS                                                           = {
        3, 4, 5                                                                        };
    public static final int[]    HOV3_ALTS                                                           = {
        6, 7, 8                                                                        };
    public static final int[]    WALK_ALTS                                                          = {
        9                                                                                       };
    public static final int[]    BIKE_ALTS                                                          = {
        10                                                                                      };
    public static final int[]    NON_MOTORIZED_ALTS                                                 = {
        9, 10                                                                                    };
    public static final int[]    TRANSIT_ALTS                                                       = {
        11, 12, 13                                                                     };
    public static final int[]    WALK_SET_ALTS                                                    = {
        11                                                                                      };
    public static final int[]    PNR_SET_ALTS                                                           = {
        12                                                                          };
    public static final int[]    KNR_SET_ALTS                                                           = {
        13                                                                          };
    public static final int[]    SCHOOL_BUS_ALTS                                                    = {
        14                                                                                     };
    public static final int[]    TRIP_SOV_ALTS                                                      = {
        1, 2                                                                                    };
    public static final int[]    TRIP_HOV_ALTS                                                      = {
        3, 4, 5, 6, 7, 8                                                                        };
    
    public static final int[]    OTHER_ALTS = {14};

    
    public static final String[] modeName = {"SOV_GP","SOV_PAY","SR2_GP","SR2_HOV","SR2_PAY","SR3_GP","SR3_HOV",
    	"SR3_PAY","WALK","BIKE","WLK_SET","PNR_SET","KNR_SET","SCHLBUS"};
    
    public static final int      MAXIMUM_TOUR_MODE_ALT_INDEX                                        = 14;

    
    public final double[][]      CDAP_6_PLUS_PROPORTIONS                                            = {
            {0.0, 0.0, 0.0}, {0.79647, 0.09368, 0.10985}, {0.61678, 0.25757, 0.12565},
            {0.69229, 0.15641, 0.15130}, {0.00000, 0.67169, 0.32831}, {0.00000, 0.54295, 0.45705},
            {0.77609, 0.06004, 0.16387}, {0.68514, 0.09144, 0.22342}, {0.14056, 0.06512, 0.79432}   };

    public static final String[] JTF_ALTERNATIVE_LABELS                                             = {
            "0_tours", "1_Shop", "1_Main", "1_Eat", "1_Visit", "1_Disc", "2_SS", "2_SM", "2_SE",
            "2_SV", "2_SD", "2_MM", "2_ME", "2_MV", "2_MD", "2_EE", "2_EV", "2_ED", "2_VV", "2_VD",
            "2_DD"                                                                                  };
    public static final String[] AWF_ALTERNATIVE_LABELS                                             = {
            "0_subTours", "1_eat", "1_business", "1_other", "2_business", "2 other",
            "2_eat_business"                                                                        };

    public static final int      MIN_DRIVING_AGE                                                    = 16;

    
    
    public SandagModelStructure()
    {
        super();

        jtfAltLabels = JTF_ALTERNATIVE_LABELS;
        awfAltLabels = AWF_ALTERNATIVE_LABELS;

        dcSizePurposeSegmentMap = new HashMap<String, HashMap<String, Integer>>();

        dcSizeIndexSegmentMap = new HashMap<Integer, String>();
        dcSizeSegmentIndexMap = new HashMap<String, Integer>();
        dcSizeArrayIndexPurposeMap = new HashMap<Integer, String>();
        dcSizeArrayPurposeIndexMap = new HashMap<String, Integer>();

        setMandatoryPurposeNameValues();

        setUsualWorkAndSchoolLocationSoaUecSheetIndexValues();
        setUsualWorkAndSchoolLocationUecSheetIndexValues();
        setUsualWorkAndSchoolLocationModeChoiceUecSheetIndexValues();

        setMandatoryStopFreqUecSheetIndexValues();
        setMandatoryStopLocUecSheetIndexValues();
        setMandatoryTripModeChoiceUecSheetIndexValues();

        setNonMandatoryPurposeNameValues();

        setAtWorkPurposeNameValues();

        setAtWorkDcSoaUecSheetIndexValues();
        setAtWorkDcUecSheetIndexValues();
        setAtWorkModeChoiceUecSheetIndexValues();

        setAtWorkStopFreqUecSheetIndexValues();

        createDcSizePurposeSegmentMap();

    }


    
    
    public String getSchoolPurpose(int age)
    {
        if (age < MIN_DRIVING_AGE) return (schoolPurposeName + "_" + SCHOOL_PURPOSE_SEGMENT_NAMES[0])
                .toLowerCase();
        else return (schoolPurposeName + "_" + SCHOOL_PURPOSE_SEGMENT_NAMES[1]).toLowerCase();
    }

    public String getSchoolPurpose()
    {
        return schoolPurposeName.toLowerCase();
    }

    public String getUniversityPurpose()
    {
        return universityPurposeName.toLowerCase();
    }

    public String getWorkPurpose(int incomeCategory)
    {
        return getWorkPurpose(false, incomeCategory);
    }

    public String getWorkPurpose(boolean isPtWorker, int incomeCategory)
    {
        if (isPtWorker) return (workPurposeName + "_" + WORK_PURPOSE_SEGMENT_NAMES[WORK_PURPOSE_SEGMENT_NAMES.length - 1])
                .toLowerCase();
        else return (workPurposeName + "_" + WORK_PURPOSE_SEGMENT_NAMES[incomeCategory - 1])
                .toLowerCase();
    }

    public boolean getTripModeIsSovOrHov(int tripMode)
    {

        for (int i = 0; i < TRIP_SOV_ALTS.length; i++)
        {
            if (TRIP_SOV_ALTS[i] == tripMode) return true;
        }

        for (int i = 0; i < TRIP_HOV_ALTS.length; i++)
        {
            if (TRIP_HOV_ALTS[i] == tripMode) return true;
        }

        return false;
    }

    public boolean getTourModeIsSov(int tourMode)
    {
        boolean returnValue = false;
        for (int i = 0; i < SOV_ALTS.length; i++)
        {
            if (SOV_ALTS[i] == tourMode)
            {
                returnValue = true;
                break;
            }
        }
        return returnValue;
    }

    public boolean getTourModeIsHov(int tourMode)
    {
        boolean returnValue = false;
        for (int i = 0; i < HOV_ALTS.length; i++)
        {
            if (HOV_ALTS[i] == tourMode) 
            {
                returnValue = true;
                break;
            }
        }
        return returnValue;
    }

    public boolean getTourModeIsS2(int tourMode)
    {
        boolean returnValue = false;
        for (int i = 0; i < HOV2_ALTS.length; i++)
        {
            if (HOV2_ALTS[i] == tourMode) 
            {
                returnValue = true;
                break;
            }
        }
        return returnValue;
    }

    public boolean getTourModeIsS3(int tourMode)
    {
        boolean returnValue = false;
        for (int i = 0; i < HOV3_ALTS.length; i++)
        {
            if (HOV3_ALTS[i] == tourMode) 
            {
                returnValue = true;
                break;
            }
        }
        return returnValue;
    }

    public boolean getTourModeIsSovOrHov(int tourMode)
    {
        for (int i = 0; i < SOV_ALTS.length; i++)
        {
            if (SOV_ALTS[i] == tourMode) return true;
        }

        for (int i = 0; i < HOV_ALTS.length; i++)
        {
            if (HOV_ALTS[i] == tourMode) return true;
        }

        return false;
    }

    public boolean getTourModeIsNonMotorized(int tourMode)
    {
        boolean returnValue = false;
        for (int i = 0; i < NON_MOTORIZED_ALTS.length; i++)
        {
            if (NON_MOTORIZED_ALTS[i] == tourMode)
            {
                returnValue = true;
                break;
            }
        }
        return returnValue;
    }

    public boolean getTourModeIsBike(int tourMode)
    {
        boolean returnValue = false;
        for (int i = 0; i < BIKE_ALTS.length; i++)
        {
            if (BIKE_ALTS[i] == tourMode)
            {
                returnValue = true;
                break;
            }
        }
        return returnValue;
    }

    public boolean getTourModeIsWalk(int tourMode)
    {
        boolean returnValue = false;
        for (int i = 0; i < WALK_ALTS.length; i++)
        {
            if (WALK_ALTS[i] == tourMode)
            {
                returnValue = true;
                break;
            }
        }
        return returnValue;
    }

    public boolean getTourModeIsTransit(int tourMode)
    {
        boolean returnValue = false;
        for (int i = 0; i < TRANSIT_ALTS.length; i++)
        {
            if (TRANSIT_ALTS[i] == tourMode)
            {
                returnValue = true;
                break;
            }
        }
        return returnValue;
    }
    
    public boolean getTripModeIsTransit(int tripMode)
    {
        boolean returnValue = false;
        for (int i = 0; i < TRANSIT_ALTS.length; i++)
        {
            if (TRANSIT_ALTS[i] == tripMode)
            {
                returnValue = true;
                break;
            }
        }
        return returnValue;
    }

    public boolean getTourModeIsWalkTransit(int tourMode)
    {
    	boolean returnValue = false;
        for (int i = 0; i < WALK_SET_ALTS.length; i++)
        {
            if (WALK_SET_ALTS[i] == tourMode)
            {
                returnValue = true;
                break;
            }
        }
        return returnValue;
    }

    public boolean getTourModeIsDriveTransit(int tourMode)
    {
        return (getTourModeIsPnr(tourMode) | getTourModeIsKnr(tourMode));
    }

    public boolean getTourModeIsPnr(int tourMode)
    {
        boolean returnValue = false;
        for (int i = 0; i < PNR_SET_ALTS.length; i++)
        {
            if (PNR_SET_ALTS[i] == tourMode)
            {
                returnValue = true;
                break;
            }
        }
        return returnValue;
    }

    public boolean getTourModeIsKnr(int tourMode)
    {
        boolean returnValue = false;
        for (int i = 0; i < KNR_SET_ALTS.length; i++)
        {
            if (KNR_SET_ALTS[i] == tourMode)
            {
                returnValue = true;
                break;
            }
        }
        return returnValue;
    }

    public boolean getTourModeIsSchoolBus(int tourMode)
    {
        boolean returnValue = false;
        for (int i = 0; i < SCHOOL_BUS_ALTS.length; i++)
        {
            if (SCHOOL_BUS_ALTS[i] == tourMode)
            {
                returnValue = true;
                break;
            }
        }
        return returnValue;
    }
    
    /**
     * Get the name of the mode
     * @param mode The mode index (1-26)
     * @return  The name of the mode
     */
    public String getModeName(int mode){
    	
    	return modeName[mode-1];
    	
    }

    private int createPurposeIndexMaps(String purposeName, String[] segmentNames, int index,
            String categoryString)
    {

        HashMap<String, Integer> segmentMap = new HashMap<String, Integer>();
        String key = "";
        if (segmentNames.length > 0)
        {
            for (int i = 0; i < segmentNames.length; i++)
            {
                segmentMap.put(segmentNames[i].toLowerCase(), i);
                key = purposeName.toLowerCase() + "_" + segmentNames[i].toLowerCase();
                dcSizeIndexSegmentMap.put(index, key);
                dcSizeSegmentIndexMap.put(key, index++);
            }
        } else
        {
            segmentMap.put(purposeName.toLowerCase(), 0);
            key = purposeName.toLowerCase() + "_" + purposeName.toLowerCase();
            dcSizeIndexSegmentMap.put(index, key);
            dcSizeSegmentIndexMap.put(key, index++);
        }
        dcSizePurposeSegmentMap.put(purposeName.toLowerCase(), segmentMap);

        return index;

    }

    /**
     * This method defines the segmentation for which destination choice size
     * variables are calculated.
     */
    private void createDcSizePurposeSegmentMap()
    {

        int index = 0;

        // put work purpose segments, by which DC Size calculations are segmented,
        // into a map to be stored by purpose name.
        index = createPurposeIndexMaps(WORK_PURPOSE_NAME, WORK_PURPOSE_SEGMENT_NAMES, index,
                MANDATORY_CATEGORY);

        // put university purpose segments, by which DC Size calculations are
        // segmented, into a map to be stored by purpose name.
        index = createPurposeIndexMaps(UNIVERSITY_PURPOSE_NAME, UNIVERSITY_PURPOSE_SEGMENT_NAMES,
                index, MANDATORY_CATEGORY);

        // put school purpose segments, by which DC Size calculations are segmented,
        // into a map to be stored by purpose name.
        index = createPurposeIndexMaps(SCHOOL_PURPOSE_NAME, SCHOOL_PURPOSE_SEGMENT_NAMES, index,
                MANDATORY_CATEGORY);

        // put escort purpose segments, by which DC Size calculations are segmented,
        // into a map to be stored by purpose name.
        index = createPurposeIndexMaps(ESCORT_PURPOSE_NAME, ESCORT_PURPOSE_SEGMENT_NAMES, index,
                INDIVIDUAL_NON_MANDATORY_CATEGORY);

        // put shopping purpose segments, by which DC Size calculations are
        // segmented, into a map to be stored by purpose name.
        index = createPurposeIndexMaps(SHOPPING_PURPOSE_NAME, SHOPPING_PURPOSE_SEGMENT_NAMES,
                index, INDIVIDUAL_NON_MANDATORY_CATEGORY);

        // put eat out purpose segments, by which DC Size calculations are segmented,
        // into a map to be stored by purpose name.
        index = createPurposeIndexMaps(EAT_OUT_PURPOSE_NAME, EAT_OUT_PURPOSE_SEGMENT_NAMES, index,
                INDIVIDUAL_NON_MANDATORY_CATEGORY);

        // put oth main purpose segments, by which DC Size calculations are
        // segmented, into a map to be stored by purpose name.
        index = createPurposeIndexMaps(OTH_MAINT_PURPOSE_NAME, OTH_MAINT_PURPOSE_SEGMENT_NAMES,
                index, INDIVIDUAL_NON_MANDATORY_CATEGORY);

        // put social purpose segments, by which DC Size calculations are segmented,
        // into a map to be stored by purpose name.
        index = createPurposeIndexMaps(SOCIAL_PURPOSE_NAME, SOCIAL_PURPOSE_SEGMENT_NAMES, index,
                INDIVIDUAL_NON_MANDATORY_CATEGORY);

        // put oth discr purpose segments, by which DC Size calculations are
        // segmented, into a map to be stored by purpose name.
        index = createPurposeIndexMaps(OTH_DISCR_PURPOSE_NAME, OTH_DISCR_PURPOSE_SEGMENT_NAMES,
                index, INDIVIDUAL_NON_MANDATORY_CATEGORY);

        // put at work purpose segments, by which DC Size calculations are segmented,
        // into a map to be stored by purpose name.
        index = createPurposeIndexMaps(AT_WORK_PURPOSE_NAME, AT_WORK_DC_SIZE_SEGMENT_NAMES, index,
                AT_WORK_CATEGORY);

    }

    public HashMap<String, HashMap<String, Integer>> getDcSizePurposeSegmentMap()
    {
        return dcSizePurposeSegmentMap;
    }

    private void setMandatoryPurposeNameValues()
    {

        int index = 0;

        WORK_PURPOSE_NAME = "work";
        UNIVERSITY_PURPOSE_NAME = "university";
        SCHOOL_PURPOSE_NAME = "school";

        int numDcSizePurposeSegments = 0;
        if (WORK_PURPOSE_SEGMENT_NAMES.length > 0) numDcSizePurposeSegments += WORK_PURPOSE_SEGMENT_NAMES.length;
        else numDcSizePurposeSegments += 1;
        if (UNIVERSITY_PURPOSE_SEGMENT_NAMES.length > 0) numDcSizePurposeSegments += UNIVERSITY_PURPOSE_SEGMENT_NAMES.length;
        else numDcSizePurposeSegments += 1;
        if (SCHOOL_PURPOSE_SEGMENT_NAMES.length > 0) numDcSizePurposeSegments += SCHOOL_PURPOSE_SEGMENT_NAMES.length;
        else numDcSizePurposeSegments += 1;

        mandatoryDcModelPurposeNames = new String[numDcSizePurposeSegments];

        workPurposeName = WORK_PURPOSE_NAME.toLowerCase();
        workPurposeSegmentNames = new String[WORK_PURPOSE_SEGMENT_NAMES.length];
        if (workPurposeSegmentNames.length > 0)
        {
            for (int i = 0; i < WORK_PURPOSE_SEGMENT_NAMES.length; i++)
            {
                workPurposeSegmentNames[i] = WORK_PURPOSE_SEGMENT_NAMES[i].toLowerCase();
                mandatoryDcModelPurposeNames[index] = workPurposeName + "_"
                        + workPurposeSegmentNames[i];
                dcModelPurposeIndexMap.put(mandatoryDcModelPurposeNames[index], index);
                dcModelIndexPurposeMap.put(index, mandatoryDcModelPurposeNames[index]);

                // a separate size term is calculated for each work purpose_segment
                dcSizeArrayIndexPurposeMap.put(index, mandatoryDcModelPurposeNames[index]);
                dcSizeArrayPurposeIndexMap.put(mandatoryDcModelPurposeNames[index], index);
                index++;
            }
        } else
        {
            mandatoryDcModelPurposeNames[index] = workPurposeName;
            dcModelPurposeIndexMap.put(mandatoryDcModelPurposeNames[index], index);
            dcModelIndexPurposeMap.put(index, mandatoryDcModelPurposeNames[index]);

            // a separate size term is calculated for each work purpose_segment
            String name = mandatoryDcModelPurposeNames[index] + "_"
                    + mandatoryDcModelPurposeNames[index];
            dcSizeArrayIndexPurposeMap.put(index, name);
            dcSizeArrayPurposeIndexMap.put(name, index);
            index++;
        }

        universityPurposeName = UNIVERSITY_PURPOSE_NAME.toLowerCase();
        universityPurposeSegmentNames = new String[UNIVERSITY_PURPOSE_SEGMENT_NAMES.length];
        if (universityPurposeSegmentNames.length > 0)
        {
            for (int i = 0; i < universityPurposeSegmentNames.length; i++)
            {
                universityPurposeSegmentNames[i] = UNIVERSITY_PURPOSE_SEGMENT_NAMES[i]
                        .toLowerCase();
                mandatoryDcModelPurposeNames[index] = universityPurposeName + "_"
                        + universityPurposeSegmentNames[i];
                dcModelPurposeIndexMap.put(mandatoryDcModelPurposeNames[index], index);
                dcModelIndexPurposeMap.put(index, mandatoryDcModelPurposeNames[index]);

                // a separate size term is calculated for each university
                // purpose_segment
                dcSizeArrayIndexPurposeMap.put(index, mandatoryDcModelPurposeNames[index]);
                dcSizeArrayPurposeIndexMap.put(mandatoryDcModelPurposeNames[index], index);
                index++;
            }
        } else
        {
            mandatoryDcModelPurposeNames[index] = universityPurposeName;
            dcModelPurposeIndexMap.put(mandatoryDcModelPurposeNames[index], index);
            dcModelIndexPurposeMap.put(index, mandatoryDcModelPurposeNames[index]);

            // a separate size term is calculated for each university purpose_segment
            String name = mandatoryDcModelPurposeNames[index] + "_"
                    + mandatoryDcModelPurposeNames[index];
            dcSizeArrayIndexPurposeMap.put(index, name);
            dcSizeArrayPurposeIndexMap.put(name, index);
            index++;
        }

        schoolPurposeName = SCHOOL_PURPOSE_NAME.toLowerCase();
        schoolPurposeSegmentNames = new String[SCHOOL_PURPOSE_SEGMENT_NAMES.length];
        if (schoolPurposeSegmentNames.length > 0)
        {
            for (int i = 0; i < schoolPurposeSegmentNames.length; i++)
            {
                schoolPurposeSegmentNames[i] = SCHOOL_PURPOSE_SEGMENT_NAMES[i].toLowerCase();
                mandatoryDcModelPurposeNames[index] = schoolPurposeName + "_"
                        + schoolPurposeSegmentNames[i];
                dcModelPurposeIndexMap.put(mandatoryDcModelPurposeNames[index], index);
                dcModelIndexPurposeMap.put(index, mandatoryDcModelPurposeNames[index]);

                // a separate size term is calculated for each school purpose_segment
                dcSizeArrayIndexPurposeMap.put(index, mandatoryDcModelPurposeNames[index]);
                dcSizeArrayPurposeIndexMap.put(mandatoryDcModelPurposeNames[index], index);
                index++;
            }
        } else
        {
            mandatoryDcModelPurposeNames[index] = schoolPurposeName;
            dcModelPurposeIndexMap.put(mandatoryDcModelPurposeNames[index], index);
            dcModelIndexPurposeMap.put(index, mandatoryDcModelPurposeNames[index]);

            // a separate size term is calculated for each school purpose_segment
            String name = mandatoryDcModelPurposeNames[index] + "_"
                    + mandatoryDcModelPurposeNames[index];
            dcSizeArrayIndexPurposeMap.put(index, name);
            dcSizeArrayPurposeIndexMap.put(name, index);
        }

    }

    private void setUsualWorkAndSchoolLocationSoaUecSheetIndexValues()
    {
        dcSoaUecIndexMap.put("work_low", USUAL_WORK_AND_SCHOOL_LOCATION_SOA_UEC_INDEX_WORK_LO);
        dcSoaUecIndexMap.put("work_med", USUAL_WORK_AND_SCHOOL_LOCATION_SOA_UEC_INDEX_WORK_MD);
        dcSoaUecIndexMap.put("work_high", USUAL_WORK_AND_SCHOOL_LOCATION_SOA_UEC_INDEX_WORK_HI);
        dcSoaUecIndexMap.put("work_very high",
                USUAL_WORK_AND_SCHOOL_LOCATION_SOA_UEC_INDEX_WORK_VHI);
        dcSoaUecIndexMap
                .put("work_part time", USUAL_WORK_AND_SCHOOL_LOCATION_SOA_UEC_INDEX_WORK_PT);
        dcSoaUecIndexMap.put("university",
                USUAL_WORK_AND_SCHOOL_LOCATION_SOA_UEC_INDEX_UNIVERSITY_UNIVERSITY);
        dcSoaUecIndexMap.put("school_predrive",
                USUAL_WORK_AND_SCHOOL_LOCATION_SOA_UEC_INDEX_SCHOOL_UNDER_SIXTEEN);
        dcSoaUecIndexMap.put("school_drive",
                USUAL_WORK_AND_SCHOOL_LOCATION_SOA_UEC_INDEX_SCHOOL_SIXTEEN_PLUS);
    }

    private void setUsualWorkAndSchoolLocationUecSheetIndexValues()
    {
        dcUecIndexMap.put("work_low", USUAL_WORK_AND_SCHOOL_LOCATION_UEC_INDEX_WORK);
        dcUecIndexMap.put("work_med", USUAL_WORK_AND_SCHOOL_LOCATION_UEC_INDEX_WORK);
        dcUecIndexMap.put("work_high", USUAL_WORK_AND_SCHOOL_LOCATION_UEC_INDEX_WORK);
        dcUecIndexMap.put("work_very high", USUAL_WORK_AND_SCHOOL_LOCATION_UEC_INDEX_WORK);
        dcUecIndexMap.put("work_part time", USUAL_WORK_AND_SCHOOL_LOCATION_UEC_INDEX_WORK);
        dcUecIndexMap.put("university", USUAL_WORK_AND_SCHOOL_LOCATION_UEC_INDEX_UNIVERSITY);
        dcUecIndexMap.put("school_predrive", USUAL_WORK_AND_SCHOOL_LOCATION_UEC_INDEX_SCHOOL);
        dcUecIndexMap.put("school_drive", USUAL_WORK_AND_SCHOOL_LOCATION_UEC_INDEX_SCHOOL);
    }

    private void setUsualWorkAndSchoolLocationModeChoiceUecSheetIndexValues()
    {
        tourModeChoiceUecIndexMap.put("work_low",
                USUAL_WORK_AND_SCHOOL_LOCATION_MODE_CHOICE_UEC_INDEX_WORK);
        tourModeChoiceUecIndexMap.put("work_med",
                USUAL_WORK_AND_SCHOOL_LOCATION_MODE_CHOICE_UEC_INDEX_WORK);
        tourModeChoiceUecIndexMap.put("work_high",
                USUAL_WORK_AND_SCHOOL_LOCATION_MODE_CHOICE_UEC_INDEX_WORK);
        tourModeChoiceUecIndexMap.put("work_very high",
                USUAL_WORK_AND_SCHOOL_LOCATION_MODE_CHOICE_UEC_INDEX_WORK);
        tourModeChoiceUecIndexMap.put("work_part time",
                USUAL_WORK_AND_SCHOOL_LOCATION_MODE_CHOICE_UEC_INDEX_WORK);
        tourModeChoiceUecIndexMap.put("university",
                USUAL_WORK_AND_SCHOOL_LOCATION_MODE_CHOICE_UEC_INDEX_UNIVERSITY);
        tourModeChoiceUecIndexMap.put("school_predrive",
                USUAL_WORK_AND_SCHOOL_LOCATION_MODE_CHOICE_UEC_INDEX_SCHOOL);
        tourModeChoiceUecIndexMap.put("school_drive",
                USUAL_WORK_AND_SCHOOL_LOCATION_MODE_CHOICE_UEC_INDEX_SCHOOL);
    }

    private void setMandatoryStopFreqUecSheetIndexValues()
    {
        stopFreqUecIndexMap.put("work_low", MANDATORY_STOP_FREQ_UEC_INDEX_WORK);
        stopFreqUecIndexMap.put("work_med", MANDATORY_STOP_FREQ_UEC_INDEX_WORK);
        stopFreqUecIndexMap.put("work_high", MANDATORY_STOP_FREQ_UEC_INDEX_WORK);
        stopFreqUecIndexMap.put("work_very high", MANDATORY_STOP_FREQ_UEC_INDEX_WORK);
        stopFreqUecIndexMap.put("work_part time", MANDATORY_STOP_FREQ_UEC_INDEX_WORK);
        stopFreqUecIndexMap.put("university", MANDATORY_STOP_FREQ_UEC_INDEX_UNIVERSITY);
        stopFreqUecIndexMap.put("school_predrive", MANDATORY_STOP_FREQ_UEC_INDEX_SCHOOL);
        stopFreqUecIndexMap.put("school_drive", MANDATORY_STOP_FREQ_UEC_INDEX_SCHOOL);
    }

    private void setMandatoryStopLocUecSheetIndexValues()
    {
        stopLocUecIndexMap.put(WORK_PURPOSE_NAME, MANDATORY_STOP_LOC_UEC_INDEX_WORK);
        stopLocUecIndexMap.put(UNIVERSITY_PURPOSE_NAME, MANDATORY_STOP_LOC_UEC_INDEX_WORK);
        stopLocUecIndexMap.put(SCHOOL_PURPOSE_NAME, MANDATORY_STOP_LOC_UEC_INDEX_WORK);
    }

    private void setMandatoryTripModeChoiceUecSheetIndexValues()
    {
        tripModeChoiceUecIndexMap.put(WORK_PURPOSE_NAME, MANDATORY_TRIP_MODE_CHOICE_UEC_INDEX_WORK);
        tripModeChoiceUecIndexMap.put(UNIVERSITY_PURPOSE_NAME,
                MANDATORY_TRIP_MODE_CHOICE_UEC_INDEX_UNIVERSITY);
        tripModeChoiceUecIndexMap.put(SCHOOL_PURPOSE_NAME,
                MANDATORY_TRIP_MODE_CHOICE_UEC_INDEX_SCHOOL);
    }

    private void setNonMandatoryPurposeNameValues()
    {

        ESCORT_PURPOSE_NAME = "escort";
        SHOPPING_PURPOSE_NAME = "shopping";
        EAT_OUT_PURPOSE_NAME = "eatout";
        OTH_MAINT_PURPOSE_NAME = "othmaint";
        SOCIAL_PURPOSE_NAME = "visit";
        OTH_DISCR_PURPOSE_NAME = "othdiscr";

        // initialize index to the length of the mandatory names list already
        // developed.
        int index = dcSizeArrayPurposeIndexMap.size();

        ESCORT_SEGMENT_NAMES = ESCORT_PURPOSE_SEGMENT_NAMES;

        // ESCORT is the only non-mandatory purpose with segments
        ArrayList<String> purposeNamesList = new ArrayList<String>();
        for (int i = 0; i < NON_MANDATORY_DC_PURPOSE_NAMES.length; i++)
        {
            if (NON_MANDATORY_DC_PURPOSE_NAMES[i].equalsIgnoreCase(ESCORT_PURPOSE_NAME))
            {
                for (int j = 0; j < ESCORT_SEGMENT_NAMES.length; j++)
                {
                    String name = (ESCORT_PURPOSE_NAME + "_" + ESCORT_SEGMENT_NAMES[j])
                            .toLowerCase();
                    purposeNamesList.add(name);
                    dcModelPurposeIndexMap.put(name, index);
                    dcModelIndexPurposeMap.put(index, name);

                    // a separate size term is calculated for each non-mandatory
                    // purpose_segment
                    dcSizeArrayIndexPurposeMap.put(index, name);
                    dcSizeArrayPurposeIndexMap.put(name, index);
                    index++;
                }
            } else
            {
                String name = NON_MANDATORY_DC_PURPOSE_NAMES[i].toLowerCase();
                purposeNamesList.add(name);
                dcModelPurposeIndexMap.put(name, index);
                dcModelIndexPurposeMap.put(index, name);

                // a separate size term is calculated for each non-mandatory
                // purpose_segment
                dcSizeArrayIndexPurposeMap.put(index, name + "_" + name);
                dcSizeArrayPurposeIndexMap.put(name + "_" + name, index);
                index++;
            }
        }

        int escortOffset = ESCORT_SEGMENT_NAMES.length;

        jointDcModelPurposeNames = new String[purposeNamesList.size() - escortOffset];
        nonMandatoryDcModelPurposeNames = new String[purposeNamesList.size()];
        for (int i = 0; i < purposeNamesList.size(); i++)
        {
            nonMandatoryDcModelPurposeNames[i] = purposeNamesList.get(i);
            if (i > escortOffset - 1)
                jointDcModelPurposeNames[i - escortOffset] = purposeNamesList.get(i);
        }

    }

 
    private void setAtWorkPurposeNameValues()
    {

        AT_WORK_PURPOSE_NAME = "atwork";

        AT_WORK_EAT_PURPOSE_NAME = "eat";
        AT_WORK_BUSINESS_PURPOSE_NAME = "business";
        AT_WORK_MAINT_PURPOSE_NAME = "other";

        AT_WORK_PURPOSE_INDEX_EAT = SD_AT_WORK_PURPOSE_INDEX_EAT;
        AT_WORK_PURPOSE_INDEX_BUSINESS = SD_AT_WORK_PURPOSE_INDEX_BUSINESS;
        AT_WORK_PURPOSE_INDEX_MAINT = SD_AT_WORK_PURPOSE_INDEX_MAINT;

        AT_WORK_SEGMENT_NAMES = new String[3];
        AT_WORK_SEGMENT_NAMES[0] = AT_WORK_EAT_PURPOSE_NAME;
        AT_WORK_SEGMENT_NAMES[1] = AT_WORK_BUSINESS_PURPOSE_NAME;
        AT_WORK_SEGMENT_NAMES[2] = AT_WORK_MAINT_PURPOSE_NAME;

        // initialize index to the length of the home-based tour names list already
        // developed.
        int index = dcSizeArrayPurposeIndexMap.size();

        // the same size term is used by each at-work soa model
        dcSizeArrayIndexPurposeMap.put(index, AT_WORK_PURPOSE_NAME + "_" + AT_WORK_PURPOSE_NAME);
        dcSizeArrayPurposeIndexMap.put(AT_WORK_PURPOSE_NAME + "_" + AT_WORK_PURPOSE_NAME, index);

        ArrayList<String> purposeNamesList = new ArrayList<String>();
        for (int j = 0; j < AT_WORK_SEGMENT_NAMES.length; j++)
        {
            String name = (AT_WORK_PURPOSE_NAME + "_" + AT_WORK_SEGMENT_NAMES[j]).toLowerCase();
            purposeNamesList.add(name);
            dcModelPurposeIndexMap.put(name, index);
            dcModelIndexPurposeMap.put(index, name);
            index++;
        }

        atWorkDcModelPurposeNames = new String[purposeNamesList.size()];
        for (int i = 0; i < purposeNamesList.size(); i++)
        {
            atWorkDcModelPurposeNames[i] = purposeNamesList.get(i);
        }

    }

    private void setAtWorkDcSoaUecSheetIndexValues()
    {
        dcSoaUecIndexMap.put("atwork_eat", AT_WORK_SOA_UEC_INDEX_EAT);
        dcSoaUecIndexMap.put("atwork_business", AT_WORK_SOA_UEC_INDEX_BUSINESS);
        dcSoaUecIndexMap.put("atwork_other", AT_WORK_SOA_UEC_INDEX_MAINT);
    }

    private void setAtWorkDcUecSheetIndexValues()
    {
        dcUecIndexMap.put("atwork_eat", AT_WORK_DC_UEC_INDEX_EAT);
        dcUecIndexMap.put("atwork_business", AT_WORK_DC_UEC_INDEX_BUSINESS);
        dcUecIndexMap.put("atwork_other", AT_WORK_DC_UEC_INDEX_MAINT);
    }

    private void setAtWorkModeChoiceUecSheetIndexValues()
    {
        tourModeChoiceUecIndexMap.put("atwork_eat", AT_WORK_MC_UEC_INDEX_EAT);
        tourModeChoiceUecIndexMap.put("atwork_business", AT_WORK_MC_UEC_INDEX_BUSINESS);
        tourModeChoiceUecIndexMap.put("atwork_other", AT_WORK_MC_UEC_INDEX_MAINT);
    }

    private void setAtWorkStopFreqUecSheetIndexValues()
    {
        stopFreqUecIndexMap.put("atwork_eat", AT_WORK_STOP_FREQ_UEC_INDEX_EAT);
        stopFreqUecIndexMap.put("atwork_business", AT_WORK_STOP_FREQ_UEC_INDEX_BUSINESS);
        stopFreqUecIndexMap.put("atwork_other", AT_WORK_STOP_FREQ_UEC_INDEX_MAINT);
    }

    public double[][] getCdap6PlusProps()
    {
        return CDAP_6_PLUS_PROPORTIONS;
    }

    public String getModelPeriodLabel(int period)
    {
        return MODEL_PERIOD_LABELS[period];
    }
    
    public int getNumberModelPeriods(){
    	return MODEL_PERIOD_LABELS.length;
    }

    public String getSkimMatrixPeriodString(int period)
    {
        int index = getSkimPeriodIndex(period);
        return SKIM_PERIOD_STRINGS[index];
    }

    public int getDefaultAmPeriod()
    {
        return getTimePeriodIndexForTime(800);
    }

    public int getDefaultPmPeriod()
    {
        return getTimePeriodIndexForTime(1700);
    }

    public int getDefaultMdPeriod()
    {
        return getTimePeriodIndexForTime(1400);
    }

    public int[] getSkimPeriodCombinationIndices()
    {
        return SKIM_PERIOD_COMBINATION_INDICES;
    }

    public int getSkimPeriodCombinationIndex(int startPeriod, int endPeriod)
    {

        int startPeriodIndex = getSkimPeriodIndex(startPeriod);
        int endPeriodIndex = getSkimPeriodIndex(endPeriod);

        if (SKIM_PERIOD_COMBINATIONS[startPeriodIndex][endPeriodIndex] < 0)
        {
            String errorString = String
                    .format(
                            "startPeriod=%d, startPeriod=%d, endPeriod=%d, endPeriod=%d is invalid combination.",
                            startPeriod, startPeriodIndex, endPeriod, endPeriodIndex);
            throw new RuntimeException(errorString);
        } else
        {
            return SKIM_PERIOD_COMBINATIONS[startPeriodIndex][endPeriodIndex];
        }

    }

    public int getMaxTourModeIndex()
    {
        return MAXIMUM_TOUR_MODE_ALT_INDEX;
    }

    public HashMap<String, Integer> getWorkSegmentNameIndexMap()
    {
        return workSegmentNameIndexMap;
    }

    public void setWorkSegmentNameIndexMap(HashMap<String, Integer> argMap)
    {
        workSegmentNameIndexMap = argMap;
    }

    public HashMap<String, Integer> getSchoolSegmentNameIndexMap()
    {
        return schoolSegmentNameIndexMap;
    }

    public void setSchoolSegmentNameIndexMap(HashMap<String, Integer> argMap)
    {
        schoolSegmentNameIndexMap = argMap;
    }

    public HashMap<Integer, String> getWorkSegmentIndexNameMap()
    {
        return workSegmentIndexNameMap;
    }

    public void setWorkSegmentIndexNameMap(HashMap<Integer, String> argMap)
    {
        workSegmentIndexNameMap = argMap;
    }

    public HashMap<Integer, String> getSchoolSegmentIndexNameMap()
    {
        return schoolSegmentIndexNameMap;
    }

    public void setSchoolSegmentIndexNameMap(HashMap<Integer, String> argMap)
    {
        schoolSegmentIndexNameMap = argMap;
    }

    public void setJtfAltLabels( String[] labels )
    {
        jtfAltLabels = labels;
    }

    public String[] getJtfAltLabels()
    {
        return jtfAltLabels;
    }


    public boolean getTripModeIsWalkTransit(int tripMode)
    {

        for (int i = 0; i < WALK_SET_ALTS.length; i++) {
            if ( WALK_SET_ALTS[i] == tripMode )
                return true;
        }

        return false;
    }

    public boolean getTripModeIsPnrTransit(int tripMode)
    {

        for (int i = 0; i < PNR_SET_ALTS.length; i++) {
            if ( PNR_SET_ALTS[i] == tripMode )
                return true;
        }

        return false;
    }

    public boolean getTripModeIsKnrTransit(int tripMode)
    {

        for (int i = 0; i < KNR_SET_ALTS.length; i++) {
            if ( KNR_SET_ALTS[i] == tripMode )
                return true;
        }

        return false;
    }

 
    
}
