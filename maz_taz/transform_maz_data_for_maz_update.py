USAGE = """

  Translates maz data from one maz system to another given a simple intersect translation.

  Developed to update maz_data.csv from maz v1.0 to maz v2.2

"""

import os
import pandas

MAZ_TRANSLATION_FILE       = "M:\\Data\\GIS layers\\maz_taz_v1.0_vs_v2.2\\maz_v1_intersect_v22.xlsx"
MAZ_TRANSLATION_SRC_MAZ    = "maz_v1_0"
MAZ_TRANSLATION_TARGET_MAZ = "maz_v2_2"
MAZ_TRANSLATION_SRC_PCT    = "pct_of_maz_v1_0"

MAZ_DATA_V_1_0_FILE  = "Box\\Modeling and Surveys\\Development\\Travel Model Two Development\\Model Inputs\\2015\\landuse\\maz_data.csv"
MAZ_DATA_V_1_0_MAZ   = "MAZ_ORIGINAL"

MAZ_DATA_V_2_2_FILE  = "Box\\Modeling and Surveys\\Development\\Travel Model Two Development\\Model Inputs\\2015_revised_mazs\\landuse\\maz_data_from_v_1.csv"

# sum these over MAZs
COLS_SUM             = ["publicEnrollGradeKto8", "privateEnrollGradeKto8", "publicEnrollGrade9to12", "privateEnrollGrade9to12",
                        "comm_coll_enroll", "EnrollGradeKto8", "EnrollGrade9to12", "collegeEnroll", "otherCollegeEnroll", "AdultSchEnrl",
                        "hstallsoth", "hstallssam", "dstallsoth", "dstallssam", "mstallsoth", "mstallssam"]
# weighted average these over MAZs based on the given columns
COLS_AVG             = {"hparkcost"  :["hstallsoth", "hstallssam"],
                        "numfreehrs" :["hstallsoth", "hstallssam"],
                        "dparkcost"  :["dstallsoth", "dstallssam"],
                        "mparkcost"  :["mstallsoth", "mstallssam"]}
# these are ordinal - choose based on the given colums
COLS_ORDINAL         = {"ech_dist":"EnrollGradeKto8",
                        "hch_dist":"EnrollGrade9to12",
                        "parkarea":"area_calc"}  # area_calc is from the translation file

if __name__ == '__main__':

    pandas.options.display.width = 300
    pandas.options.display.float_format = '{:.2f}'.format

    # read the translation file
    translate_df = pandas.read_excel(MAZ_TRANSLATION_FILE, header=0)
    print("Read MAZ translation file {}".format(MAZ_TRANSLATION_FILE))
    print("Head:\n{}".format(translate_df.head()))

    # read the maz_data for maz v1.0
    full_path = os.path.join(os.environ["USERPROFILE"], MAZ_DATA_V_1_0_FILE)
    maz_source_df = pandas.read_csv(full_path)
    print("Read MAZ source data {}".format(full_path))

    # look at only the colums we care about
    cols = [MAZ_DATA_V_1_0_MAZ] + COLS_SUM + list(COLS_AVG.keys()) + list(COLS_ORDINAL.keys())
    maz_source_df = maz_source_df[cols]
    print("maz_source_df Length: {} Head:\n{}".format(len(maz_source_df), maz_source_df.head()))
    print("maz_source_df sum:\n{}".format(maz_source_df.sum()))

    # left join to the translation
    maz_source_df = pandas.merge(left    =maz_source_df,
                                 right   =translate_df,
                                 left_on =MAZ_DATA_V_1_0_MAZ,
                                 right_on=MAZ_TRANSLATION_SRC_MAZ)
    print("maz_source_df joined Length: {} Head:\n{}".format(len(maz_source_df), maz_source_df.head()))

    # COLS_SUM: want sum of (percent x val)
    for col in COLS_SUM:
        maz_source_df[col] = maz_source_df[MAZ_TRANSLATION_SRC_PCT]*maz_source_df[col]

    # COLS_AVG: want sum of (percent x weight x val) / (sum of percent x weight)
    for col in COLS_AVG.keys():
        temp_col = maz_source_df[col]
        maz_source_df[col] = 0
        for weight_col in COLS_AVG[col]:
            maz_source_df[col] = maz_source_df[col] + temp_col*maz_source_df[MAZ_TRANSLATION_SRC_PCT]*maz_source_df[weight_col]

    # group to target MAZ
    maz_target_df = maz_source_df[[MAZ_TRANSLATION_TARGET_MAZ] + COLS_SUM + list(COLS_AVG.keys())].groupby(MAZ_TRANSLATION_TARGET_MAZ).agg("sum")

    # COLS_AVG need to be divided by the sum of percent x weight
    for col in COLS_AVG.keys():
        temp_col = maz_target_df[col] - maz_target_df[col]  # to make the right size/index
        for weight_col in COLS_AVG[col]: # these are already summed now
            temp_col = temp_col + maz_target_df[weight_col]
        # divide
        maz_target_df[col] = maz_target_df[col] / temp_col

    # fillna and reset index
    maz_target_df.fillna(value=0, inplace=True)
    maz_target_df.reset_index(inplace=True)
    print("maz_target_df Length: {} Head:\n{}".format(len(maz_target_df), maz_target_df.head()))
    print("maz_target_df sum:\n{}".format(maz_target_df.sum()))

    # COLS_ORDINAL: groupby the maz and the column itself
    for col in COLS_ORDINAL.keys():
        weight_col = COLS_ORDINAL[col]
        # groupby the maz and the ordinal column, summing the weights
        maz_by_target_val = maz_source_df[[MAZ_TRANSLATION_TARGET_MAZ, col, weight_col]].groupby([MAZ_TRANSLATION_TARGET_MAZ, col]).agg("sum")

        # sort by the maz and the weight col - so the last one for the maz will be the biggest weight
        maz_by_target_val = maz_by_target_val.reset_index().sort_values(by=[MAZ_TRANSLATION_TARGET_MAZ,weight_col])

        # deduplicate, taking the last
        maz_by_target_val.drop_duplicates(subset=[MAZ_TRANSLATION_TARGET_MAZ], keep="last", inplace=True)
        print("maz_by_target_val Length: {} Head:\n{}".format(len(maz_by_target_val), maz_by_target_val.head()))

        # join to the result
        maz_target_df = pandas.merge(left=maz_target_df, right=maz_by_target_val[[MAZ_TRANSLATION_TARGET_MAZ,col]], how="left")

    print("maz_target_df Length: {} Head:\n{}".format(len(maz_target_df), maz_target_df.head()))
    print("maz_target_df sum:\n{}".format(maz_target_df.sum()))

    full_path = os.path.join(os.environ["USERPROFILE"], MAZ_DATA_V_2_2_FILE)
    maz_target_df.to_csv(full_path, index=False)
    print("Wrote {}".format(full_path))