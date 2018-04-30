USAGE = """

MAZ and TAZ checker.

Reads the definition of MAZs and TAZs in blocks_mazs_tazs.dbf (converted from csv using csv_to_dbf.R)

The following verifcations are performed
  - Verifies that there are not multiple tazs or counties per maz
  - Counts/lists first 30 mazs with multiple block groups, tracts
  - Verifies that there are not multiple counties per taz
  - Counts/lists first 30 tazs with multiple tracts
  - Verifies that all blocks with nonzero land area are assigned a maz/taz
  - Verifies that all blocks with zero land area are not assigned a maz/taz

Creates a dissolved maz shapefile and a dissolved taz shapefile.

  Notes:
  - Block "06 075 017902 1009" (maz 10186, taz 592) is the little piece of Alameda island that the Census 2010
    calls San Francisco.  Left in SF as its own maz.

  - Blocks "06 075 980401 100[1,2,3]" (maz 16084, taz 287) are the Farallon Islands.  It's a standalone maz.

  - Blocks "06 075 017902 10[05,80]" (maz 16495, taz 312) is a tiny sliver that's barely land so not worth
    making a new maz, so that maz includes a second tract (mostly water)

  TODO: Remove the maz=0/taz=0 rows from the dissolved shapefiles

"""

# use python in c:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3
# in order to import arcpy

import os, sys
import pandas
import arcpy

WORKSPACE          = "M:\\Data\\GIS layers\\TM2_maz_taz_v2.2"
CROSSWALK_ROOT     = "blocks_mazs_tazs"
CROSSWALK_DBF      = os.path.join(WORKSPACE, "{0}.dbf".format(CROSSWALK_ROOT))

CENSUS_BLOCK_DIR   = "M:\\Data\\Census\\Geography\\tl_2010_06_tabblock10"
CENSUS_BLOCK_ROOT  = "tl_2010_06_tabblock10_9CountyBayArea"
CENSUS_BLOCK_DBF   = os.path.join(CENSUS_BLOCK_DIR, "{0}.dbf".format(CENSUS_BLOCK_ROOT))
CENSUS_BLOCK_SHP   = os.path.join(CENSUS_BLOCK_DIR, "{0}.shp".format(CENSUS_BLOCK_ROOT))
CENSUS_BLOCK_COLS  = ["STATEFP10", "COUNTYFP10", "TRACTCE10", "BLOCKCE10", "GEOID10", "ALAND10", "AWATER10"]

# output files
MAZS_SHP           = "mazs_TM2_v2_2"
TAZS_SHP           = "tazs_TM2_v2_2"


def move_small_block_to_neighbor(blocks_maz_layer, blocks_maz_df, maz_multiple_geo_df, bigger_geo):
    """
    The most simplistic fix is to move small blocks to a neighboring maz/taz
    """
    print("move_small_block_to_neighbor for {0}".format(bigger_geo))
    for maz,row in maz_multiple_geo_df.iterrows():
        print("maz {0:6d}".format(maz), end="")

        # this one we'll leave; see Notes
        if maz == 16495:
            print("Special exception -- skipping")
            continue

        # if it spans more than 2, leave it for nwo
        if row[bigger_geo] > 2:
            print("Spans more than 2 {0} elements {1}".format(bigger_geo, row[bigger_geo]))
            continue

        print("")

        # let's look at the blocks in this maz in the blocks_maz_df
        this_maz_blocks_df = blocks_maz_df.loc[ blocks_maz_df.maz == maz]
        print(this_maz_blocks_df)
        this_maz_aland = this_maz_blocks_df.ALAND10.sum()
        print(this_maz_aland)

        # find the blocks in this maz
        arcpy.SelectLayerByAttribute_management(blocks_maz_layer, "NEW_SELECTION", "\"maz\"={0}".format(maz))
        print("Selected feature count: " + str(arcpy.GetCount_management(blocks_maz_layer)[0]))
        # sys.exit()
        return


if __name__ == '__main__':

    pandas.options.display.width = 300
    pandas.options.display.float_format = '{:.2f}'.format

    try:
        arcpy.env.workspace = WORKSPACE
        arcpy.env.qualifiedFieldNames = False  # ?

        ########################################################
        # Create a feature layer from the 2010 block shapefile
        blocks_maz_layer = "blocks_maz_lyr"
        arcpy.MakeFeatureLayer_management(CENSUS_BLOCK_SHP, blocks_maz_layer)
        block_count = arcpy.GetCount_management(blocks_maz_layer)
        print("Created feature layer with {0} rows".format(block_count[0]))

        ########################################################
        # Join the census blocks to the maz/taz crosswalk
        arcpy.AddJoin_management(blocks_maz_layer, "GEOID10", CROSSWALK_DBF, "GEOID10")
        block_join_count = arcpy.GetCount_management(blocks_maz_layer)
        print("Joined to crosswalk dbf resulting in {0} rows".format(block_join_count[0]))

        # assert we didn't lose rows in the join
        assert(block_count[0]==block_join_count[0])

        # verify
        fields = arcpy.ListFields(blocks_maz_layer)
        for field in fields:
            print("  {0:20s} is a type of {1} with a length of {2}".format(field.name, field.type, field.length))

        # create Dataframe
        fields = ["{0}.{1}".format(CENSUS_BLOCK_ROOT,colname) for colname in CENSUS_BLOCK_COLS]
        fields.append("{0}.maz".format(CROSSWALK_ROOT))
        fields.append("{0}.taz".format(CROSSWALK_ROOT))
        blocks_maz_df = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray(
                        in_table=blocks_maz_layer,
                        field_names=fields))
        print("blocks_maz_df has length ", len(blocks_maz_df))

        # shorten the fields
        short_fields = CENSUS_BLOCK_COLS
        short_fields.append("maz")
        short_fields.append("taz")
        blocks_maz_df.rename(dict(zip(fields, short_fields)), axis='columns',inplace=True)

        # the GEOID10 = state(2) + county(3) + tract(6) + block(4)
        # block group is the firist digit of the block number
        blocks_maz_df["GEOID10_BG"]     = blocks_maz_df["GEOID10"].str[:12]
        blocks_maz_df["GEOID10_TRACT"]  = blocks_maz_df["GEOID10"].str[:11]
        blocks_maz_df["GEOID10_COUNTY"] = blocks_maz_df["GEOID10"].str[:5]
        print(blocks_maz_df.head())

    except Exception as err:
        print(err.args[0])

    print("Number of unique GEOID10: %d" % blocks_maz_df.GEOID10.nunique())
    print("  Min: %s" % str(blocks_maz_df.GEOID10.min()))
    print("  Max: %s" % str(blocks_maz_df.GEOID10.max()))
    print("")

    # maz 0 aren't real -- these are blocks without mazs
    # split the blocks up
    blocks_nomaz_df = blocks_maz_df.loc[blocks_maz_df.maz == 0]
    blocks_maz_df   = blocks_maz_df.loc[blocks_maz_df.maz != 0]

    print("Number of unique maz: ", blocks_maz_df.maz.nunique())
    print("   Min: ", blocks_maz_df.maz.min())
    print("   Max: ", blocks_maz_df.maz.max())
    print("")

    print("Number of unique taz: ", blocks_maz_df.taz.nunique())
    print("   Min: ", blocks_maz_df.taz.min())
    print("   Max: ", blocks_maz_df.taz.max())
    print("")

    # if maz is zero, taz should be zero
    assert(blocks_nomaz_df.taz == 0).all()
    # if maz is not zero, taz should not be zero
    assert(blocks_maz_df.taz != 0).all()

    # verify one taz/BLOCK GROUP/TRACT/COUNTY per unique maz
    # error for taz/COUNTY
    # warn/log for BLOCK GROUP/TRACT
    for bigger_geo in ["taz","GEOID10_COUNTY","GEOID10_TRACT","GEOID10_BG"]:
        maz_geo_df = blocks_maz_df[["maz",bigger_geo]].groupby(["maz"]).agg("nunique")
        maz_multiple_geo_df = maz_geo_df.loc[ maz_geo_df[bigger_geo] > 1]
        if len(maz_multiple_geo_df) == 0:
            print("Verified one {0} per maz".format(bigger_geo))
        else:
            if bigger_geo in ["GEOID10_BG","GEOID10_TRACT"]:
                fatal = False
            else:
                fatal = True

            error = "{0}: Multiple {1} for a single maz: {2}".format(
                    "ERROR" if fatal else "WARNING", bigger_geo, len(maz_multiple_geo_df))
            print(error)
            print(maz_multiple_geo_df.head(30))
            print("")
            if fatal:
                sys.exit(error)
            else:
                move_small_block_to_neighbor(blocks_maz_layer, blocks_maz_df, maz_multiple_geo_df, bigger_geo)

    # verify one TRACT/COUNTY per unique taz
    for bigger_geo in ["GEOID10_TRACT","GEOID10_COUNTY"]:
        taz_geo_df = blocks_maz_df[["taz",bigger_geo]].groupby(["taz"]).agg("nunique")
        taz_multiple_geo_df = taz_geo_df.loc[ taz_geo_df[bigger_geo] > 1]
        if len(taz_multiple_geo_df) == 0:
            print("Verified one {0} per taz".format(bigger_geo))
        else:
            if bigger_geo in ["GEOID10_COUNTY"]:
                fatal = True
            else:
                fatal = False
            error = "{0}: Multiple {1} for a single taz: {2}".format(
                    "ERROR" if fatal else "WARNING", bigger_geo, len(taz_multiple_geo_df))
            print(error)
            print(taz_multiple_geo_df)
            print("")
            if fatal: sys.exit(error)


    # count blocks per maz
    count_df = blocks_maz_df[["GEOID10","maz"]].groupby(["maz"]).agg("nunique")
    print("Number of blocks per maz: ")
    print("   Min: ", count_df["GEOID10"].min())
    print("   Max: ", count_df["GEOID10"].max())
    print("  Mean: ", count_df["GEOID10"].mean())
    print("")

    # count maz per taz
    count_df = blocks_maz_df[["maz","taz"]].groupby(["taz"]).agg("nunique")
    print("Number of maz per taz: ")
    print("   Min: ", count_df["maz"].min())
    print("   Max: ", count_df["maz"].max())
    print("  Mean: ", count_df["maz"].mean())
    print("")

    # lets look at the zeros
    print("Number of blocks without maz/taz: ", blocks_nomaz_df.GEOID10.nunique())

    # blocks with land should have mazs/tazs
    block_nomaz_land_df = blocks_nomaz_df.loc[ blocks_nomaz_df.ALAND10 > 0 ]
    print("Number of blocks without maz/taz with land area: ", len(block_nomaz_land_df))
    if len(block_nomaz_land_df) > 0:
        print(block_nomaz_land_df)
        print("")
        sys.exit("ERROR")

    # blocks with no land should not have mazs/tazs
    blocks_maz_noland_df = blocks_maz_df.loc[ blocks_maz_df.ALAND10 == 0]
    print("Number of blocks with maz/taz without land area: ", len(blocks_maz_noland_df))
    blocks_maz_noland_df[["GEOID10","ALAND10"]].to_csv("block_noland.csv", index=False)
    if len(blocks_maz_noland_df) > 0:
        print(blocks_maz_noland_df)
        print("")
        sys.exit("ERROR")

    # create our maz shapefile
    try:
        # clear selection
        arcpy.SelectLayerByAttribute_management(blocks_maz_layer, "CLEAR_SELECTION")

        # create mazs shapefile
        arcpy.Dissolve_management (blocks_maz_layer, MAZS_SHP, "{0}.maz".format(CROSSWALK_ROOT),
                                   [["{0}.ALAND10".format(CENSUS_BLOCK_ROOT),  "SUM"  ],
                                    ["{0}.AWATER10".format(CENSUS_BLOCK_ROOT), "SUM"  ],
                                    ["{0}.GEOID10".format(CENSUS_BLOCK_ROOT),  "COUNT"],  # count block per maz
                                    ["{0}.taz".format(CROSSWALK_ROOT),         "FIRST"]], # verified taz are unique for maz above
                                   "MULTI_PART", "DISSOLVE_LINES")
        print("Dissolved mazs into {0}.shp".format(MAZS_SHP))

        # create tazs shapefile
        arcpy.Dissolve_management (blocks_maz_layer, TAZS_SHP, "{0}.taz".format(CROSSWALK_ROOT),
                                   [["{0}.ALAND10".format(CENSUS_BLOCK_ROOT),  "SUM"  ],
                                    ["{0}.AWATER10".format(CENSUS_BLOCK_ROOT), "SUM"  ],
                                    ["{0}.GEOID10".format(CENSUS_BLOCK_ROOT),  "COUNT"],  # count block per taz
                                    ["{0}.maz".format(CROSSWALK_ROOT),         "COUNT"]], # count maz per taz
                                   "MULTI_PART", "DISSOLVE_LINES")
        print("Dissolved tazs into {0}.shp".format(TAZS_SHP))

    except Exception as err:
        print(err.args[0])
