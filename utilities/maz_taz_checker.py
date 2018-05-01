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

import csv, logging, os, sys
import pandas
import arcpy

WORKSPACE          = "M:\\Data\\GIS layers\\TM2_maz_taz_v2.2"
CROSSWALK_ROOT     = "blocks_mazs_tazs"
CROSSWALK_DBF      = os.path.join(WORKSPACE, "{0}.dbf".format(CROSSWALK_ROOT))

CENSUS_BLOCK_DIR   = "M:\\Data\\Census\\Geography\\tl_2010_06_tabblock10"
CENSUS_BLOCK_ROOT  = "tl_2010_06_tabblock10_9CountyBayArea"
CENSUS_BLOCK_SHP   = os.path.join(CENSUS_BLOCK_DIR, "{0}.shp".format(CENSUS_BLOCK_ROOT))
CENSUS_BLOCK_COLS  = ["STATEFP10", "COUNTYFP10", "TRACTCE10", "BLOCKCE10", "GEOID10", "ALAND10", "AWATER10"]

CENSUS_BLOCK_NEIGHBOR_DBF = os.path.join(CENSUS_BLOCK_DIR, "tl_2010_06_tabblock10_9CBA_neighbors.dbf")

# output files
LOG_FILE           = os.path.join(WORKSPACE, "maz_taz_checker.log")
CROSSWALK_OUT      = os.path.join(WORKSPACE, "blocks_mazs_tazs_updated.csv")
MAZS_SHP           = "mazs_TM2_v2_2"
TAZS_SHP           = "tazs_TM2_v2_2"


def move_small_block_to_neighbor(blocks_maz_layer, blocks_maz_df, blocks_neighbor_df,
                                 maz_multiple_geo_df, bigger_geo, crosswalk_out_df):
    """
    The most simplistic fix is to move small blocks to a neighboring maz/taz
    """
    logging.info("move_small_block_to_neighbor for {0}".format(bigger_geo))
    for maz,row in maz_multiple_geo_df.iterrows():
        logging.info("Attempting to fix maz {0:6d}  ".format(maz))

        # this one we'll leave; see Notes
        if maz == 16495:
            logging.info("Special exception -- skipping")
            continue

        # if it spans more than 3, leave it for now
        if row[bigger_geo] > 3:
            logging.info("Spans more than 2 {0} elements {1}".format(bigger_geo, row[bigger_geo]))
            continue

        # let's look at the blocks in this maz in the blocks_maz_df
        this_maz_blocks_df = blocks_maz_df.loc[ blocks_maz_df.maz == maz]
        logging.debug("\n{0}".format(this_maz_blocks_df))
        this_maz_aland = this_maz_blocks_df.ALAND10.sum()

        # check if the odd one or two out are smaller
        this_maz_grouped = this_maz_blocks_df.groupby(bigger_geo)
        for name,group in this_maz_grouped:
            land_pct = group.ALAND10.sum()/this_maz_aland
            logging.debug("group {0} has {1} rows and {2:.1f} percent of land".format(name, len(group), 100.0*land_pct))
            logging.debug("\n{0}".format(group))

            # 25% or less is ok to move
            if land_pct > 0.25: continue

            # these blocks are candidates for moving -- let's look at where to move to
            for block_index,block_row in group.iterrows():

                # find the neighboring blocks
                this_block_id = block_row["GEOID10"]
                # look at neighbors for candidates
                this_block_neighbors = blocks_neighbor_df.loc[blocks_neighbor_df.src_GEOID1 == this_block_id].copy()
                # only neighbors in the same block group
                this_block_neighbors = this_block_neighbors.loc[ this_block_neighbors.nbr_GEIOID10_BG == block_row["GEOID10_BG"]]

                if len(this_block_neighbors) == 0:
                    logging.debug("  No neighbors in same block group")
                    continue

                # pick the neighboring block with the most length adjacent
                this_block_neighbors.sort_values(by="LENGTH", ascending=False, inplace=True)
                # print(this_block_neighbors)
                this_neighbor_id = this_block_neighbors.nbr_GEOID1.iloc[0]
                logging.info("  => block {0} picking up maz/taz from neighboring block {1}".format(this_block_id, this_neighbor_id))

                # look up the neighbor's maz and taz to inherit
                match_row = crosswalk_out_df.loc[ crosswalk_out_df.GEOID10 == this_neighbor_id]
                crosswalk_out_df.loc[ crosswalk_out_df.GEOID10 == this_block_id, "maz"] = match_row["maz"].iloc[0]
                crosswalk_out_df.loc[ crosswalk_out_df.GEOID10 == this_block_id, "taz"] = match_row["taz"].iloc[0]
                logging.debug("\n{0}".format(crosswalk_out_df.loc[ (crosswalk_out_df.GEOID10 == this_block_id)|
                                                                   (crosswalk_out_df.GEOID10 == this_neighbor_id) ]))

        # return


if __name__ == '__main__':

    pandas.options.display.width = 300
    pandas.options.display.float_format = '{:.2f}'.format

    # create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
    logger.addHandler(ch)
    # file handler
    fh = logging.FileHandler(LOG_FILE, mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
    logger.addHandler(fh)

    try:
        arcpy.env.workspace = WORKSPACE
        arcpy.env.qualifiedFieldNames = False  # ?

        ########################################################
        # Create a feature layer from the 2010 block shapefile
        blocks_maz_layer = "blocks_maz_lyr"
        arcpy.MakeFeatureLayer_management(CENSUS_BLOCK_SHP, blocks_maz_layer)
        block_count = arcpy.GetCount_management(blocks_maz_layer)
        logging.info("Created feature layer with {0} rows".format(block_count[0]))

        ########################################################
        # Join the census blocks to the maz/taz crosswalk
        arcpy.AddJoin_management(blocks_maz_layer, "GEOID10", CROSSWALK_DBF, "GEOID10")
        block_join_count = arcpy.GetCount_management(blocks_maz_layer)
        logging.info("Joined to crosswalk dbf resulting in {0} rows".format(block_join_count[0]))

        # assert we didn't lose rows in the join
        assert(block_count[0]==block_join_count[0])

        # verify
        fields = arcpy.ListFields(blocks_maz_layer)
        for field in fields:
            logging.info("  {0:50s} is a type of {1:15s} with a length of {2}".format(field.name, field.type, field.length))

        # create Dataframe
        fields = ["{0}.{1}".format(CENSUS_BLOCK_ROOT,colname) for colname in CENSUS_BLOCK_COLS]
        fields.append("{0}.maz".format(CROSSWALK_ROOT))
        fields.append("{0}.taz".format(CROSSWALK_ROOT))
        blocks_maz_df = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray(
                        in_table=blocks_maz_layer,
                        field_names=fields))
        logging.info("blocks_maz_df has length {0}".format(len(blocks_maz_df)))

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
        logging.info("\n{0}".format(blocks_maz_df.head()))

        # this is the one we'll modify and output
        crosswalk_out_df = blocks_maz_df[["GEOID10","maz","taz"]]

        #####################################################
        # Create a table from the 2010 block neighbor mapping
        # For use in move_small_block_to_neighbor()
        blocks_neighbor_df = pandas.DataFrame(arcpy.da.TableToNumPyArray(
                        in_table=CENSUS_BLOCK_NEIGHBOR_DBF,
                        field_names=["src_GEOID1","nbr_GEOID1","LENGTH","NODE_COUNT"]))
        blocks_neighbor_df["nbr_GEIOID10_BG"] = blocks_neighbor_df["nbr_GEOID1"].str[:12]
        logging.info("blocks_neighbor_df has length {0}".format(len(blocks_neighbor_df)))
        logging.info("\n{0}".format(blocks_neighbor_df.head()))

    except Exception as err:
        logging.info(err.args[0])

    logging.info("Number of unique GEOID10: {0}".format(blocks_maz_df.GEOID10.nunique()))
    logging.info("  Min: {0}".format(blocks_maz_df.GEOID10.min()))
    logging.info("  Max: {0}".format(blocks_maz_df.GEOID10.max()))
    logging.info("")

    # maz 0 aren't real -- these are blocks without mazs
    # split the blocks up
    blocks_nomaz_df = blocks_maz_df.loc[blocks_maz_df.maz == 0]
    blocks_maz_df   = blocks_maz_df.loc[blocks_maz_df.maz != 0]

    logging.info("Number of unique maz: {0}".format(blocks_maz_df.maz.nunique()))
    logging.info("   Min: {0}".format(blocks_maz_df.maz.min()))
    logging.info("   Max: {0}".format(blocks_maz_df.maz.max()))
    logging.info("")

    logging.info("Number of unique taz: {0}".format(blocks_maz_df.taz.nunique()))
    logging.info("   Min: {0}".format(blocks_maz_df.taz.min()))
    logging.info("   Max: {0}".format(blocks_maz_df.taz.max()))
    logging.info("")

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
            logging.info("Verified one {0} per maz".format(bigger_geo))
        else:
            if bigger_geo in ["GEOID10_BG","GEOID10_TRACT"]:
                fatal = False
            else:
                fatal = True

            error = "{0}: Multiple {1} for a single maz: {2}".format(
                    "ERROR" if fatal else "WARNING", bigger_geo, len(maz_multiple_geo_df))
            logging.warning(error)
            logging.warning("\n{0}".format(maz_multiple_geo_df.head(30)))
            logging.warning("")
            if fatal:
                sys.exit(error)
            else:
                move_small_block_to_neighbor(blocks_maz_layer, blocks_maz_df, blocks_neighbor_df,
                                             maz_multiple_geo_df, bigger_geo, crosswalk_out_df)

    # save updated draft crosswalk to look at
    crosswalk_out_df.sort_values(by="GEOID10", ascending=True, inplace=True)
    crosswalk_out_df.to_csv(CROSSWALK_OUT, index=False, quoting=csv.QUOTE_NONNUMERIC)
    logging.info("Wrote updated draft crosswalk to {0}".format(CROSSWALK_OUT))
    # verify one TRACT/COUNTY per unique taz
    for bigger_geo in ["GEOID10_TRACT","GEOID10_COUNTY"]:
        taz_geo_df = blocks_maz_df[["taz",bigger_geo]].groupby(["taz"]).agg("nunique")
        taz_multiple_geo_df = taz_geo_df.loc[ taz_geo_df[bigger_geo] > 1]
        if len(taz_multiple_geo_df) == 0:
            logging.info("Verified one {0} per taz".format(bigger_geo))
        else:
            if bigger_geo in ["GEOID10_COUNTY"]:
                fatal = True
            else:
                fatal = False
            error = "{0}: Multiple {1} for a single taz: {2}".format(
                    "ERROR" if fatal else "WARNING", bigger_geo, len(taz_multiple_geo_df))
            logging.warning(error)
            logging.warning("\n{0}".format(taz_multiple_geo_df))
            logging.warning("")
            if fatal: sys.exit(error)


    # count blocks per maz
    count_df = blocks_maz_df[["GEOID10","maz"]].groupby(["maz"]).agg("nunique")
    logging.info("Number of blocks per maz: ")
    logging.info("   Min: {0}".format(count_df["GEOID10"].min()))
    logging.info("   Max: {0}".format(count_df["GEOID10"].max()))
    logging.info("  Mean: {0}".format(count_df["GEOID10"].mean()))
    logging.info("")

    # count maz per taz
    count_df = blocks_maz_df[["maz","taz"]].groupby(["taz"]).agg("nunique")
    logging.info("Number of maz per taz: ")
    logging.info("   Min: {0}".format(count_df["maz"].min()))
    logging.info("   Max: {0}".format(count_df["maz"].max()))
    logging.info("  Mean: {0}".format(count_df["maz"].mean()))
    logging.info("")

    # lets look at the zeros
    logging.info("Number of blocks without maz/taz: {0}".format(blocks_nomaz_df.GEOID10.nunique()))

    # blocks with land should have mazs/tazs
    block_nomaz_land_df = blocks_nomaz_df.loc[ blocks_nomaz_df.ALAND10 > 0 ]
    logging.info("Number of blocks without maz/taz with land area: {0}".format(len(block_nomaz_land_df)))
    if len(block_nomaz_land_df) > 0:
        logging.fatal("\n{0}".format(block_nomaz_land_df))
        logging.fatal("")
        sys.exit("ERROR")

    # blocks with no land should not have mazs/tazs
    blocks_maz_noland_df = blocks_maz_df.loc[ blocks_maz_df.ALAND10 == 0]
    logging.info("Number of blocks with maz/taz without land area: {0}".format(len(blocks_maz_noland_df)))
    blocks_maz_noland_df[["GEOID10","ALAND10"]].to_csv("block_noland.csv", index=False)
    if len(blocks_maz_noland_df) > 0:
        logging.fatal("\n{0}".format(blocks_maz_noland_df))
        logging.fatal("")
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
        logging.info("Dissolved mazs into {0}.shp".format(MAZS_SHP))

        # create tazs shapefile
        arcpy.Dissolve_management (blocks_maz_layer, TAZS_SHP, "{0}.taz".format(CROSSWALK_ROOT),
                                   [["{0}.ALAND10".format(CENSUS_BLOCK_ROOT),  "SUM"  ],
                                    ["{0}.AWATER10".format(CENSUS_BLOCK_ROOT), "SUM"  ],
                                    ["{0}.GEOID10".format(CENSUS_BLOCK_ROOT),  "COUNT"],  # count block per taz
                                    ["{0}.maz".format(CROSSWALK_ROOT),         "COUNT"]], # count maz per taz
                                   "MULTI_PART", "DISSOLVE_LINES")
        logging.info("Dissolved tazs into {0}.shp".format(TAZS_SHP))

    except Exception as err:
        logging.error(err.args[0])
