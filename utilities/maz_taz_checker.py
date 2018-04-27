USAGE = """

MAZ and TAZ checker.

Reads the definition of MAZs and TAZs in blocks_mazs_tazs.dbf (converted from csv using csv_to_dbf.R)

The following verifcations are performed
  - Verifies that all blocks with nonzero land area are assigned a maz/taz
  - Verifies that there are not multiple tazs or counties per maz
  - Counts/lists first 30 mazs with multiple block groups, tracts
  - Verifies that there are not multiple counties per taz

Creates a dissolved maz shapefile and a dissolved taz shapefile.

  Notes:
  - Block "06 075 017902 1009" (maz 10186, taz 592) is the little piece of Alameda island that the Census 2010
    calls San Francisco.  Left in SF as its own maz.

  - Blocks "06 075 980401 100[1,2,3]" (maz 16084, taz 287) are the Farallon Islands.  It's a standalone maz.

  - Blocks "06 075 017902 10[05,80]" (maz 16495, taz 312) is a tiny sliver that's barely land so not worth
    making a new maz, so that maz includes a second tract (mostly water)

  TODO: remove dependency on dbfread?  Since we're using arcpy, can just use that to read the dbf

"""

# use python in c:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3
# in order to import arcpy

import os, sys
import pandas
import dbfread
import arcpy

WORKSPACE          = "M:\\Data\\GIS layers\\TM2_maz_taz_v2.1"
CROSSWALK_ROOT     = "blocks_mazs_tazs"
CROSSWALK_DBF      = os.path.join(WORKSPACE, "{0}.dbf".format(CROSSWALK_ROOT))

CENSUS_BLOCK_DIR   = "M:\\Data\\Census\\Geography\\tl_2010_06_tabblock10"
CENSUS_BLOCK_ROOT  = "tl_2010_06_tabblock10_9CountyBayArea"
CENSUS_BLOCK_DBF   = os.path.join(CENSUS_BLOCK_DIR, "{0}.dbf".format(CENSUS_BLOCK_ROOT))
CENSUS_BLOCK_SHP   = os.path.join(CENSUS_BLOCK_DIR, "{0}.shp".format(CENSUS_BLOCK_ROOT))

# output files
MAZS_SHP           = "mazs_TM2_v2_1"
TAZS_SHP           = "tazs_TM2_v2_1"


class MyFieldParser(dbfread.FieldParser):
    def parse(self, field, data):
        try:
            return dbfread.FieldParser.parse(self, field, data)
        except ValueError:
            -1
            # return dbfread.InvalidValue(data)

if __name__ == '__main__':
    pandas.options.display.width = 300
    pandas.options.display.float_format = '{:.2f}'.format

    # read the crosswalk, with the GEODID10 as text since that's how census shapefiles interpret itf
    crosswalk_dbf = dbfread.DBF(CROSSWALK_DBF, parserclass=MyFieldParser)
    print("Read ",CROSSWALK_DBF)
    crosswalk_df  = pandas.DataFrame(iter(crosswalk_dbf))

    # the GEOID10 = state(2) + county(3) + tract(6) + block(4)
    # block group is the firist digit of the block number
    crosswalk_df["GEOID10_BG"]     = crosswalk_df["GEOID10"].str[:12]
    crosswalk_df["GEOID10_TRACT"]  = crosswalk_df["GEOID10"].str[:11]
    crosswalk_df["GEOID10_COUNTY"] = crosswalk_df["GEOID10"].str[:5]

    print("Head: ")
    print(crosswalk_df.head())
    print("")

    print("Number of unique GEOID10: %d" % crosswalk_df.GEOID10.nunique())
    print("  Min: %s" % str(crosswalk_df.GEOID10.min()))
    print("  Max: %s" % str(crosswalk_df.GEOID10.max()))
    print("")

    # maz 0 aren't real -- these are blocks without mazs
    # split the blocks up
    blocks_nomaz_df = crosswalk_df.loc[crosswalk_df.maz == 0]
    blocks_maz_df   = crosswalk_df.loc[crosswalk_df.maz != 0]

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
    for bigger_geo in ["taz","GEOID10_BG","GEOID10_TRACT","GEOID10_COUNTY"]:
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
            if fatal: sys.exit(error)

    # verify one COUNTY per unique taz
    taz_county_df = blocks_maz_df[["taz","GEOID10_COUNTY"]].groupby(["taz"]).agg("nunique")
    taz_multiple_county_df = taz_county_df.loc[ taz_county_df["GEOID10_COUNTY"] > 1]
    if len(taz_multiple_county_df) == 0:
        print("Verified one county per taz")
    else:
        error = "ERROR: Multiple counties for a single taz: {1}".format(len(taz_multiple_county_df))
        print(error)
        print(taz_multiple_county_df)
        print("")
        sys.exit(error)  # this is required

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

    # read the 2017 vintage Census 2010 Block shapefile dbf
    blocks_dbf = dbfread.DBF(CENSUS_BLOCK_DBF, parserclass=MyFieldParser)
    print("Read ",CENSUS_BLOCK_DBF)
    # for i, record in enumerate(blocks_dbf):
    #    for name, value in record.items():
    #        if isinstance(value, dbfread.InvalidValue):
    #            print('records[{}][{!r}] == {!r}'.format(i, name, value))
    blocks_df  = pandas.DataFrame(iter(blocks_dbf))
    print("Head:")
    print(blocks_df.head())


    blocks_nomaz_df = pandas.merge(left =blocks_nomaz_df,
                                   right=blocks_df,
                                   how  ="left",
                                   on   ="GEOID10")

    block_nomaz_land_df = blocks_nomaz_df.loc[ blocks_nomaz_df.ALAND10 > 0 ]
    print("Number of blocks without maz/taz with land area: ", len(block_nomaz_land_df))
    if len(block_nomaz_land_df) > 0:
        print(block_nomaz_land_df)

    # create our maz shapefile
    try:
        arcpy.env.workspace = WORKSPACE
        arcpy.env.qualifiedFieldNames = False  # ?

        # create a feature layer
        layer_name = "tl_2010_06_tabblock10_9CountyBayArea_lyr"
        arcpy.MakeFeatureLayer_management(CENSUS_BLOCK_SHP, layer_name)
        print("Created feature layer")
        # join the feature layer to a table
        arcpy.AddJoin_management(layer_name, "GEOID10", CROSSWALK_DBF, "GEOID10")
        print("Joined to crosswalk dbf")

        # verify
        fields = arcpy.ListFields(layer_name)
        for field in fields:
            print("  {0} is a type of {1} with a length of {2}".format(field.name, field.type, field.length))

        # create mazs shapefile
        arcpy.Dissolve_management (layer_name, MAZS_SHP, "{0}.maz".format(CROSSWALK_ROOT),
                                   [["{0}.ALAND10".format(CENSUS_BLOCK_ROOT),  "SUM"  ],
                                    ["{0}.AWATER10".format(CENSUS_BLOCK_ROOT), "SUM"  ],
                                    ["{0}.GEOID10".format(CENSUS_BLOCK_ROOT),  "COUNT"],  # count block per maz
                                    ["{0}.taz".format(CROSSWALK_ROOT),         "FIRST"]], # verified taz are unique for maz above
                                   "MULTI_PART", "DISSOLVE_LINES")
        print("Dissolved mazs into {0}.shp".format(MAZS_SHP))

        # add maz mod 1000 to make it easier to add symbology
        arcpy.AddField_management("{0}.shp".format(MAZS_SHP), "maz_mod_1k", "SHORT")
        print("Added maz_mod_1k field")
        arcpy.CalculateField_management("{0}.shp".format(MAZS_SHP), "maz_mod_1k",
                                        "!maz! % 1000", "PYTHON3")
        print("Calculated maz_mod_1k field")

        # create tazs shapefile
        arcpy.Dissolve_management (layer_name, TAZS_SHP, "{0}.taz".format(CROSSWALK_ROOT),
                                   [["{0}.ALAND10".format(CENSUS_BLOCK_ROOT),  "SUM"  ],
                                    ["{0}.AWATER10".format(CENSUS_BLOCK_ROOT), "SUM"  ],
                                    ["{0}.GEOID10".format(CENSUS_BLOCK_ROOT),  "COUNT"],  # count block per taz
                                    ["{0}.maz".format(CROSSWALK_ROOT),         "COUNT"]], # count maz per taz
                                   "MULTI_PART", "DISSOLVE_LINES")
        print("Dissolved tazs into {0}.shp".format(TAZS_SHP))

        # add maz mod 1000 to make it easier to add symbology
        arcpy.AddField_management("{0}.shp".format(TAZS_SHP), "taz_mod_1k", "SHORT")
        print("Added taz_mod_1k field")
        arcpy.CalculateField_management("{0}.shp".format(TAZS_SHP), "taz_mod_1k",
                                        "!taz! % 1000", "PYTHON3")
        print("Calculated taz_mod_1k field")

    except Exception as err:
        print(err.args[0])
