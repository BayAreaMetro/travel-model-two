USAGE = """

  Translates maz/taz data from one maz/taz system to another given a simple intersect translation.

  Developed to update maz_data.csv from tm2 maz v1.0 to maz v2.2
  Extended to update taz airport trips from taz v1.0 to taz v2.2
  Extended to update the internal/external trips from tm1 taz to tm2 taz v2.2
  Extended to update the truck K factors from tm1 taz to tm2 taz v2.2

  Specify which type of conversion you want to do as an argument.

"""

import argparse, collections, itertools, os, sys
import pandas


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("convert_type", choices=["maz_data_v1_to_v22","airport_taz_v1_to_v22","ix_tm1_taz_to_tm2_taz_v22", "truck_tm1_taz_to_tm2_taz_v22"])
    args = parser.parse_args()

    INPUT_DATA_EXTRA_INDEX_COLS = None

    # Fill these in to define the mapping
    COLS_SUM      = []
    COLS_AVG      = {}
    COLS_ORDINAL  = {}

    if args.convert_type == "maz_data_v1_to_v22":
        # mazdata conversion

        # these are lists to iterate over
        INPUT_DATA_FILES  = [os.path.join(os.environ["USERPROFILE"], "Box\\Modeling and Surveys\\Development\\Travel Model Two Development\\Model Inputs\\2015\\landuse\\maz_data.csv")]
        INPUT_DATA_GEOS   = ["MAZ_ORIGINAL"]
        OUTPUT_DATA_FILES = [os.path.join(os.environ["USERPROFILE"], "Box\\Modeling and Surveys\\Development\\Travel Model Two Development\\Model Inputs\\2015_revised_mazs\\landuse\\maz_data_from_v_1.csv")]
        OUTPUT_DATA_GEOS  = ["maz_v2_2"]

        # translation
        GEO_TRANSLATION_FILE       = "M:\\Data\\GIS layers\\\maz_taz_conversion\\maz_v1_intersect_v22.xlsx"
        GEO_TRANSLATION_SRC_GEO    = "maz_v1_0"
        GEO_TRANSLATION_TARGET_GEO = "maz_v2_2"
        GEO_TRANSLATION_SRC_PCT    = "pct_of_maz_v1_0"

        # sum these over MAZs
        COLS_SUM         = ["publicEnrollGradeKto8", "privateEnrollGradeKto8", "publicEnrollGrade9to12", "privateEnrollGrade9to12",
                            "comm_coll_enroll", "EnrollGradeKto8", "EnrollGrade9to12", "collegeEnroll", "otherCollegeEnroll", "AdultSchEnrl",
                            "hstallsoth", "hstallssam", "dstallsoth", "dstallssam", "mstallsoth", "mstallssam", "park_area"]

        # weighted average these over MAZs based on the given columns
        COLS_AVG         = collections.OrderedDict([
            ("hparkcost" ,["hstallsoth", "hstallssam"]),
            ("numfreehrs",["hstallsoth", "hstallssam"]),
            ("dparkcost" ,["dstallsoth", "dstallssam"]),
            ("mparkcost" ,["mstallsoth", "mstallssam"])
        ])

        # these are ordinal - choose based on the given colums
        COLS_ORDINAL= collections.OrderedDict([
            ("ech_dist","EnrollGradeKto8" ),
            ("hch_dist","EnrollGrade9to12"),
            ("parkarea","area_calc"       ),  # area_calc is from the translation file
        ])

    elif args.convert_type == "airport_taz_v1_to_v22":
        # Airport TAZs themselves don't change

        # these are lists to iterate over
        INPUT_DATA_FILES  = []
        INPUT_DATA_GEOS   = []
        OUTPUT_DATA_FILES = []
        OUTPUT_DATA_GEOS  = []

        BASE_PATH = os.path.join(os.environ["USERPROFILE"], "Box\\Modeling and Surveys\\Development\\Travel Model Two Development\\Model Inputs")

        for airport_year in [2007,2035]:
            for tofrom in ["from","to"]:
                for airport in ["OAK","SFO","SJC"]:
                    INPUT_DATA_FILES.append(os.path.join(BASE_PATH, "2015", "nonres", "{}_{}{}.csv".format(airport_year,tofrom,airport)))
                    INPUT_DATA_GEOS.append("DEST" if tofrom=="from" else "ORIG")  # from X means ORIG fixed, so use DEST

                    OUTPUT_DATA_FILES.append(os.path.join(BASE_PATH, "2015_revised_mazs", "nonres", "{}_{}{}.csv".format(airport_year,tofrom,airport)))
                    OUTPUT_DATA_GEOS.append(INPUT_DATA_GEOS[-1])

        # translation
        GEO_TRANSLATION_FILE       = "M:\\Data\\GIS layers\\\maz_taz_conversion\\taz_v1_intersect_v22.xlsx"
        GEO_TRANSLATION_SRC_GEO    = "taz_v1_0"
        GEO_TRANSLATION_TARGET_GEO = "taz_v2_2"
        GEO_TRANSLATION_SRC_PCT    = "pct_of_taz_v1_0"

        COLS_SUM = [
            "EA_ES_DA","EA_ES_S2","EA_ES_S3","EA_PK_DA","EA_PK_S2","EA_PK_S3","EA_RN_DA","EA_RN_S2","EA_RN_S3","EA_TX_DA","EA_TX_S2","EA_TX_S3","EA_LI_DA","EA_LI_S2","EA_LI_S3","EA_VN_S3","EA_HT_S3","EA_CH_S3",
            "AM_ES_DA","AM_ES_S2","AM_ES_S3","AM_PK_DA","AM_PK_S2","AM_PK_S3","AM_RN_DA","AM_RN_S2","AM_RN_S3","AM_TX_DA","AM_TX_S2","AM_TX_S3","AM_LI_DA","AM_LI_S2","AM_LI_S3","AM_VN_S3","AM_HT_S3","AM_CH_S3",
            "MD_ES_DA","MD_ES_S2","MD_ES_S3","MD_PK_DA","MD_PK_S2","MD_PK_S3","MD_RN_DA","MD_RN_S2","MD_RN_S3","MD_TX_DA","MD_TX_S2","MD_TX_S3","MD_LI_DA","MD_LI_S2","MD_LI_S3","MD_VN_S3","MD_HT_S3","MD_CH_S3",
            "PM_ES_DA","PM_ES_S2","PM_ES_S3","PM_PK_DA","PM_PK_S2","PM_PK_S3","PM_RN_DA","PM_RN_S2","PM_RN_S3","PM_TX_DA","PM_TX_S2","PM_TX_S3","PM_LI_DA","PM_LI_S2","PM_LI_S3","PM_VN_S3","PM_HT_S3","PM_CH_S3",
            "EV_ES_DA","EV_ES_S2","EV_ES_S3","EV_PK_DA","EV_PK_S2","EV_PK_S3","EV_RN_DA","EV_RN_S2","EV_RN_S3","EV_TX_DA","EV_TX_S2","EV_TX_S3","EV_LI_DA","EV_LI_S2","EV_LI_S3","EV_VN_S3","EV_HT_S3","EV_CH_S3"
        ]

    elif args.convert_type == "ix_tm1_taz_to_tm2_taz_v22":

        # these are lists to iterate over - this is a two pass process.  Convert J first, then I.
        INPUT_DATA_FILES            = ["IXDaily2006x4.may2208.csv"          , "IXDaily2006x4.may2208_updated_j.csv"]
        INPUT_DATA_GEOS             = ["J"                                  , "I"]
        INPUT_DATA_EXTRA_INDEX_COLS = [["I"]                                , ["J_tm2"]]
        OUTPUT_DATA_FILES           = ["IXDaily2006x4.may2208_updated_j.csv", "IXDaily2006x4.may2208_updated_ij.csv"]
        OUTPUT_DATA_GEOS            = ["J_tm2"                              , "I_tm2"]

        # translation
        GEO_TRANSLATION_FILE       = "M:\\Data\\GIS layers\\\maz_taz_conversion\\taz_tm1_intersect_taz_tm2.xlsx"
        GEO_TRANSLATION_SRC_GEO    = "taz_tm1"
        GEO_TRANSLATION_TARGET_GEO = "taz_tm2_v2_2"
        GEO_TRANSLATION_SRC_PCT    = "pct_of_taz_tm1"

        # sum these over MAZs
        COLS_SUM         = ["IX_Daily_DA", "IX_DAILY_SR2", "IX_Daily_SR3", "IX_Daily_Total"]

    elif args.convert_type == "truck_tm1_taz_to_tm2_taz_v22":

        # these are lists to iterate over - this is a two pass process.  Convert J first, then I.
        INPUT_DATA_FILES            = ["truckkfact.k22.z1454.csv"]
        INPUT_DATA_GEOS             = ["I"]
        INPUT_DATA_EXTRA_INDEX_COLS = [["J"]]
        OUTPUT_DATA_FILES           = ["truck_kfactors_taz.csv"]
        OUTPUT_DATA_GEOS            = ["I_tm2", "J_tm2"]

        # translation
        GEO_TRANSLATION_FILE       = "M:\\Data\\GIS layers\\\maz_taz_conversion\\taz_tm1_intersect_taz_tm2.xlsx"
        GEO_TRANSLATION_SRC_GEO    = "taz_tm1"
        GEO_TRANSLATION_TARGET_GEO = "taz_tm2_v2_2"
        GEO_TRANSLATION_SRC_PCT    = "pct_of_taz_tm1"

        # this isn't really a sum, it'll be treated specially
        COLS_SUM                   = ["truck_k"]

    pandas.options.display.width = 300
    pandas.options.display.float_format = '{:.2f}'.format

    # read the translation file
    translate_df = pandas.read_excel(GEO_TRANSLATION_FILE, header=0)
    print("Read translation file {}".format(GEO_TRANSLATION_FILE))
    print("Head:\n{}".format(translate_df.head()))

    # iterate through the input files
    for input_number in range(len(INPUT_DATA_FILES)):

        INPUT_DATA_FILE   = INPUT_DATA_FILES[input_number]
        INPUT_DATA_GEO    = INPUT_DATA_GEOS[input_number]
        if INPUT_DATA_EXTRA_INDEX_COLS:
            INPUT_DATA_INDEX = INPUT_DATA_EXTRA_INDEX_COLS[input_number] # serves as index along with the INPUT_DATA_GEO
        else:
            INPUT_DATA_INDEX = []
        OUTPUT_DATA_FILE  = OUTPUT_DATA_FILES[input_number]
        OUTPUT_DATA_GEO   = OUTPUT_DATA_GEOS[input_number]


        # read the source data
        data_source_df = pandas.read_csv(INPUT_DATA_FILE)
        print("Read source data {}".format(INPUT_DATA_FILE))

        # look at only the colums we care about
        cols = [INPUT_DATA_GEO] + INPUT_DATA_INDEX + COLS_SUM + list(COLS_AVG.keys()) + list(COLS_ORDINAL.keys())
        data_source_df = data_source_df[cols]
        print("data_source_df Length: {} Head:\n{}".format(len(data_source_df), data_source_df.head()))
        # print("data_source_df sum:\n{}".format(data_source_df.sum()))

        # this one is special
        if args.convert_type == "truck_tm1_taz_to_tm2_taz_v22":
            # create a simple translation from target to source
            simple_translate_df = translate_df[[GEO_TRANSLATION_SRC_GEO, GEO_TRANSLATION_TARGET_GEO, "area_calc"]].copy()
            # don't include external zones
            simple_translate_df = simple_translate_df.loc[ simple_translate_df[GEO_TRANSLATION_SRC_GEO] <= 1454, :]

            # choose the one with the largest area_calc for each target (TM2) geography
            simple_translate_df = simple_translate_df.sort_values(by=[GEO_TRANSLATION_TARGET_GEO, "area_calc"], ascending=[True, False])
            simple_translate_df.drop_duplicates(subset=[GEO_TRANSLATION_TARGET_GEO], keep="first", inplace=True)

            simple_translate_df = simple_translate_df[[GEO_TRANSLATION_SRC_GEO, GEO_TRANSLATION_TARGET_GEO]].reset_index(drop=True)
            print("simple_translate_df Length: {} Head:\n{}".format(len(simple_translate_df), simple_translate_df.head()))

            # create I x J
            i_df = simple_translate_df.copy().rename({GEO_TRANSLATION_SRC_GEO:"I_{}".format(GEO_TRANSLATION_SRC_GEO),
                                                      GEO_TRANSLATION_TARGET_GEO:"I_{}".format(GEO_TRANSLATION_TARGET_GEO)},
                                                      axis='columns',)
            i_df["IJ"] = 1
            j_df = simple_translate_df.copy().rename({GEO_TRANSLATION_SRC_GEO:"J_{}".format(GEO_TRANSLATION_SRC_GEO),
                                                      GEO_TRANSLATION_TARGET_GEO:"J_{}".format(GEO_TRANSLATION_TARGET_GEO)},
                                                      axis='columns',)
            j_df["IJ"] = 1

            data_target_df = pandas.merge(left=i_df, right=j_df, on=["IJ"]).drop(columns=["IJ"])
            # print("data_target_df IxJ Length: {} Head:\n{}".format(len(data_target_df), data_target_df.head()))

            data_target_df = pandas.merge(left      = data_target_df,
                                          right     = data_source_df,
                                          left_on   = ["I_{}".format(GEO_TRANSLATION_SRC_GEO), "J_{}".format(GEO_TRANSLATION_SRC_GEO)],
                                          right_on  = ["I","J"],
                                          how       = "left")
            # drop I, J - duplicative; drop I_taz_tm1, J_taz_tm1 since we don't need them any more
            data_target_df.drop(columns=["I","J","I_{}".format(GEO_TRANSLATION_SRC_GEO), "J_{}".format(GEO_TRANSLATION_SRC_GEO)], inplace=True)

            # check everything joined
            assert( len(data_target_df.loc[ pandas.isnull(data_target_df.truck_k) ]) == 0 )

        else:

            # left join to the translation
            data_source_df = pandas.merge(left    =data_source_df,
                                          right   =translate_df,
                                          left_on =INPUT_DATA_GEO,
                                          right_on=GEO_TRANSLATION_SRC_GEO)
            print("data_source_df joined Length: {} Head:\n{}".format(len(data_source_df), data_source_df.head()))

            # COLS_SUM: want sum of (percent x val)
            for col in COLS_SUM:
                data_source_df[col] = data_source_df[GEO_TRANSLATION_SRC_PCT]*data_source_df[col]

            # COLS_AVG: want sum of (percent x weight x val) / (sum of percent x weight)
            for col in COLS_AVG.keys():
                temp_col = data_source_df[col]
                data_source_df[col] = 0
                for weight_col in COLS_AVG[col]:
                    data_source_df[col] = data_source_df[col] + temp_col*data_source_df[GEO_TRANSLATION_SRC_PCT]*data_source_df[weight_col]

            # group to target geography
            keep_cols = [GEO_TRANSLATION_TARGET_GEO] + INPUT_DATA_INDEX + COLS_SUM + list(COLS_AVG.keys())
            extra_cols = list(itertools.chain.from_iterable(COLS_AVG.values()))
            for extra_col in extra_cols:
                if extra_col not in keep_cols: keep_cols.append(extra_col)

            data_target_df = data_source_df[keep_cols].groupby([GEO_TRANSLATION_TARGET_GEO]+INPUT_DATA_INDEX).agg("sum")

            # COLS_AVG need to be divided by the sum of percent x weight
            for col in COLS_AVG.keys():
                temp_col = data_target_df[col] - data_target_df[col]  # to make the right size/index
                for weight_col in COLS_AVG[col]: # these are already summed now
                    temp_col = temp_col + data_target_df[weight_col]
                # divide
                data_target_df[col] = data_target_df[col] / temp_col

            # fillna and reset index
            data_target_df.fillna(value=0, inplace=True)
            data_target_df.reset_index(inplace=True)
            # print("data_target_df Length: {} Head:\n{}".format(len(data_target_df), data_target_df.head()))
            # print("data_target_df sum:\n{}".format(data_target_df.sum()))

            # COLS_ORDINAL: groupby the maz and the column itself
            for col in COLS_ORDINAL.keys():
                weight_col = COLS_ORDINAL[col]
                # groupby the maz and the ordinal column, summing the weights
                maz_by_target_val = data_source_df[[GEO_TRANSLATION_TARGET_GEO, col, weight_col]].groupby([GEO_TRANSLATION_TARGET_GEO, col]).agg("sum")

                # sort by the maz and the weight col - so the last one for the maz will be the biggest weight
                maz_by_target_val = maz_by_target_val.reset_index().sort_values(by=[GEO_TRANSLATION_TARGET_GEO,weight_col])

                # deduplicate, taking the last
                maz_by_target_val.drop_duplicates(subset=[GEO_TRANSLATION_TARGET_GEO], keep="last", inplace=True)

                # join to the result
                data_target_df = pandas.merge(left=data_target_df, right=maz_by_target_val[[GEO_TRANSLATION_TARGET_GEO,col]], how="left")

            # rename the output geo if needed
            if OUTPUT_DATA_GEO != GEO_TRANSLATION_TARGET_GEO:
                data_target_df.rename({GEO_TRANSLATION_TARGET_GEO:OUTPUT_DATA_GEO}, axis='columns', inplace=True)

        # special airport bit -- need the orig/dest column to be the airport in question
        if args.convert_type == "airport_taz_v1_to_v22":
            airport = OUTPUT_DATA_FILE[-7:-4]
            tofrom  = "to" if OUTPUT_DATA_FILE[-9:-7]=="to" else "from"

            # these didn't change from taz v1.0 to taz v2.2
            airport_taz = None
            if airport=="OAK":
                airport_taz = 300560
            elif airport=="SFO":
                airport_taz = 100426
            elif airport=="SJC":
                airport_taz = 200879
            else:
                raise RuntimeError("Don't understand airport {}".format(airport))

            # if from, insert constant column ORIG
            data_target_df.insert(loc   = 0 if tofrom=="from" else 1,
                                  column= "ORIG" if tofrom=="from" else "DEST",
                                  value = airport_taz)

        print("data_target_df Length: {} Head:\n{}".format(len(data_target_df), data_target_df.head()))
        # print("data_target_df sum:\n{}".format(data_target_df.sum()))

        data_target_df.to_csv(OUTPUT_DATA_FILE, index=False)
        print("Wrote {}".format(OUTPUT_DATA_FILE))