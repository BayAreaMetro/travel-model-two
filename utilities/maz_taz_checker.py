USAGE = """

MAZ and TAZ checker.

  - Verifies that all blocks with nonzero land area are assigned a maz/taz
  - Verifies(*) that there are not multiple tazs, tracts or counties per maz
  - TODO: add block group?

  Notes:
  - Block "060750179021009" (maz 315303, taz 300206) is the little piece of Alameda island that the Census 2010 
    calls San Francisco.  We put it in Alameda.

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
CROSSWALK_CSV      = os.path.join(WORKSPACE, "{0}.csv".format(CROSSWALK_ROOT))
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

    # verify one taz/TRACT/COUNTY per unique maz
    # add block group?
    for bigger_geo in ["taz","GEOID10_TRACT","GEOID10_COUNTY"]:
        maz_geo_df = blocks_maz_df[["maz",bigger_geo]].groupby(["maz"]).agg("nunique")
        maz_multiple_geo_df = maz_geo_df.loc[ maz_geo_df[bigger_geo] > 1]
        if len(maz_multiple_geo_df) == 0:
            print("Verified one {0} per maz".format(bigger_geo))
        else:
            error = "ERROR: Multiple {0} for a single maz:".format(bigger_geo)
            print(error)
            print(maz_multiple_geo_df)
            print("")
            # sys.exit(error)


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

        # create tazs shapefile
        arcpy.Dissolve_management (layer_name, TAZS_SHP, "{0}.taz".format(CROSSWALK_ROOT),
                                   [["{0}.ALAND10".format(CENSUS_BLOCK_ROOT),  "SUM"  ],
                                    ["{0}.AWATER10".format(CENSUS_BLOCK_ROOT), "SUM"  ],
                                    ["{0}.GEOID10".format(CENSUS_BLOCK_ROOT),  "COUNT"],  # count block per taz
                                    ["{0}.maz".format(CROSSWALK_ROOT),         "COUNT"]], # count maz per taz
                                   "MULTI_PART", "DISSOLVE_LINES")
        print("Dissolved mazs into {0}.shp".format(MAZS_SHP))

    except Exception as err:
        print(err.args[0])
