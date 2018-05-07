USAGE = """

MAZ and TAZ checker.

Reads the definition of MAZs and TAZs in blocks_mazs_tazs.dbf (converted from csv using csv_to_dbf.R)

The following verifcations are performed
  - Verifies that there are not multiple tazs or counties per maz
  - Verifies that there are not multiple counties per taz
  - Verifies that all blocks with nonzero land area are assigned a maz/taz
  - Verifies that all blocks with zero land area are not assigned a maz/taz

Also, given the following issue:
  - Counts/lists first 30 mazs with multiple block groups, tracts
The script attempts to fix them with move_small_block_to_neighbor()
  - For each small (<25 percent land area) blocks in the maz
  - Looks at neighboring blocks in the same block group
  - If there are any with a maz, picks the one with the most border length in common
  - Move the original block to inherit the maz/taz of this neighbor

If the mazs are aok, then given the following issue:
  - Counts/lists first 30 tazs with multiple tracts
The script attempts to fix them with split_taz_for_tract()
  - For each taz that spans multiple tracts, if the smallest portion in a tract is
    non-trivial (>10 percent of land), then split the taz on the tract boundary,
    creating new tazs.

This draft update is saved into blocks_mazs_tazs_updated.csv

  Notes:
  - Block "06 075 017902 1009" (maz 10186, taz 592) is the little piece of Alameda island that the Census 2010
    calls San Francisco.  Left in SF as its own maz.

  - Blocks "06 075 980401 100[1,2,3]" (maz 16084, taz 287) are the Farallon Islands.  It's a standalone maz but the
    taz spans tracts because it's not worth it's own taz.

  - Block "06 081 608002 2004" (maz 112279, taz 100178) spans a block group boundary but not doing so would split up
    and island with two blocks.

  - Blocks "06 075 017902 10[05,80]" (maz 16495, taz 312) is a tiny sliver that's barely land so not worth
    making a new maz, so that maz includes a second tract (mostly water)

  - Blocks "06 041 104300 10[17,18,19]" (maz 810745, taz 800095) spans a block group/tract boundary but the're a
    tiny bit on the water's edge and moving them would separate them from the rest of the maz/taz

  - Blocks "06 041 122000 100[0,1,2]" (maz 813480, taz 800203) are a tract that is inside another tract so keeping
    as is so as not to create a donut hole maz

  - Block "06 013 301000 3000" (maz 410304, taz 400507) is a block that Census 2010 claims has no land area ("Webb Tract")
    but appears to be a delta island so it's an exception to the zero-land/non-zero water blocks having a maz/taz

"""
EXEMPT_MAZ = [     16495, 112279, 810745, 813480]
EXEMPT_TAZ = [287,                800095, 800203]

EXEMPT_NOLAND_BLOCK = ["060133010003000"]

# use python in c:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3
# in order to import arcpy

import argparse, csv, logging, os, sys
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


def move_small_block_to_neighbor(blocks_maz_df, blocks_neighbor_df,
                                 maz_multiple_geo_df, bigger_geo, crosswalk_out_df):
    """
    The simplest fix is to move small blocks to a neighboring maz/taz.
    Returns number of blocks moved.
    """
    blocks_moved = 0
    logging.info("move_small_block_to_neighbor for {0}".format(bigger_geo))
    for maz,row in maz_multiple_geo_df.iterrows():
        logging.info("Attempting to fix maz {0:6d}".format(maz))

        # these we'll leave; see Notes
        if maz in EXEMPT_MAZ:
            logging.info("Special exception -- skipping")
            continue

        # if it spans more than 3, leave it for now
        if row[bigger_geo] > 3:
            logging.info("Spans more than 3 {0} elements {1} -- skipping".format(bigger_geo, row[bigger_geo]))
            continue

        # if there's three, 25% or less is ok to move
        # it two, 32% or less
        if row[bigger_geo] == 3:
            pct_threshold = 0.25
        else:
            pct_threshold = 0.32

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

            # is this land area too much to move?
            if land_pct > pct_threshold: continue

            # these blocks are candidates for moving -- let's look at where to move to
            for block_index,block_row in group.iterrows():

                # find the neighboring blocks
                this_block_id = block_row["GEOID10"]
                this_block_maz = block_row["maz"]
                # look at neighbors for candidates
                this_block_neighbors = blocks_neighbor_df.loc[blocks_neighbor_df.src_GEOID1 == this_block_id].copy()
                # only neighbors in the same block group with maz/taz set and maz differs
                this_block_neighbors = this_block_neighbors.loc[ (this_block_neighbors.nbr_GEIOID10_BG == block_row["GEOID10_BG"]) &
                                                                 (this_block_neighbors.maz != 0) &
                                                                 (this_block_neighbors.maz != this_block_maz)]

                if len(this_block_neighbors) == 0:
                    logging.debug("  No neighbors in same block group with maz/taz")
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
                blocks_moved += 1
                logging.debug("\n{0}".format(crosswalk_out_df.loc[ (crosswalk_out_df.GEOID10 == this_block_id)|
                                                                   (crosswalk_out_df.GEOID10 == this_neighbor_id) ]))

    logging.info("====> moved {0} blocks to neighbor".format(blocks_moved))
    return blocks_moved

def find_next_unused_taz_id(crosswalk_out_df, taz):
    """
    Find the next unused taz id after taz
    """
    # this is a little wasteful but ok
    taz_ids = crosswalk_out_df["taz"].drop_duplicates() # series
    # also I'm assuming these are easy to find
    unused_taz_id = taz + 1
    while True:
        if unused_taz_id in taz_ids.values:
            unused_taz_id += 1
        else:
            logging.debug("find_next_unused_taz_id for {0:6d} returning {1:6d}".format(taz, unused_taz_id))
            return unused_taz_id
    return -1

def split_taz_for_tract(blocks_maz_df, taz_multiple_geo_df, crosswalk_out_df):
    """
    The simplest fix for TAZs that span tract boundaries is to split the TAZ.
    Since there aren't that many, let's do that so long as the tract portions are non-trivial (>10%)
    """
    tazs_split = 0
    logging.info("splitting taz for tract")
    for taz,row in taz_multiple_geo_df.iterrows():
        logging.info("Attempting to fix taz {0:6d}".format(taz))

        # if it spans more than 3, leave it for now
        if row[bigger_geo] > 3:
            logging.info("Spans more than 3 {0} elements {1} -- skipping".format(bigger_geo, row[bigger_geo]))
            continue

        # let's look at the blocks in this taz in the blocks_maz_df
        this_taz_blocks_df = blocks_maz_df.loc[ blocks_maz_df.taz == taz]
        this_taz_aland = this_taz_blocks_df.ALAND10.sum()

        # check if the chunks are all pretty big
        this_taz_grouped = this_taz_blocks_df.groupby(bigger_geo)
        groups_aland = this_taz_grouped.agg({"ALAND10":"sum"})
        groups_aland["ALAND10_pct"] = groups_aland["ALAND10"]/this_taz_aland
        logging.debug("\n{0}".format(groups_aland))

        # if too small, punt
        if groups_aland["ALAND10_pct"].min() < 0.10:
            logging.info("Tract/taz portion too small -- skipping")
            continue

        first = True
        for name,group in this_taz_grouped:
            land_pct = group.ALAND10.sum()/this_taz_aland
            # logging.debug("\n{0}".format(group))

            # don't touch the first tract
            if first:
                logging.info("  group {0} has {1:3d} rows and {2:.1f} percent of land".format(name, len(group), 100.0*land_pct))
                first = False
                continue

            # move the mazs in this tract to a new taz
            new_taz_id = find_next_unused_taz_id(crosswalk_out_df, taz)

            # convert these mazs into the new taz
            crosswalk_out_df.loc[ (crosswalk_out_df.taz==taz)&(crosswalk_out_df[bigger_geo]==name), "taz"] = new_taz_id
            logging.info("  group {0} has {1:3d} rows and {2:.1f} percent of land => new taz {3:6d}".format(name, len(group), 100.0*land_pct, new_taz_id))
            tazs_split += 1

    return tazs_split

def rename_fields(input_feature, output_feature, old_to_new):
    """
    Renames specified fields in input feature class/table
    old_to_new: {old_field: [new_field, new_alias]}
    """
    existing_field_names = [field.name for field in arcpy.ListFields(input_feature)]
    field_mappings = arcpy.FieldMappings()
    field_mappings.addTable(input_feature)

    for (old_field_name, new_list) in old_to_new.items():
        if old_field_name not in existing_field_names:
            message = "Field: {0} not in {1}".format(old_field_name, input_feature)
            raise Exception(message)

        mapping_index          = field_mappings.findFieldMapIndex(old_field_name)
        field_map              = field_mappings.fieldMappings[mapping_index]
        output_field           = field_map.outputField
        output_field.name      = new_list[0]
        output_field.aliasName = new_list[1]
        field_map.outputField  = output_field
        field_mappings.replaceFieldMap(mapping_index, field_map)

    # use merge with single input just to use new field_mappings
    arcpy.Merge_management(input_feature, output_feature, field_mappings)
    return output_feature

def dissolve_into_shapefile(blocks_maz_layer, maz_or_taz):
    """
    Dissolve the blocks into final MAZ/TAZ shapefile
    """
    shapefile = MAZS_SHP if maz_or_taz=="maz" else TAZS_SHP

    # don't care if this fails, just want to head off error since arcpy gets mad if we try to overwrite
    try:
        arcpy.Delete_management("{0}_temp.shp".format(shapefile))
    except Exception as err:
        logging.debug(err.args[0])

    # don't care if this fails, just want to head off error since arcpy gets mad if we try to overwrite
    try:
        arcpy.Delete_management("{0}.shp".format(shapefile))
    except Exception as err:
        logging.debug(err.args[0])

    try:
        # create mazs shapefile -- save as temp since we'll do a bit more to it
        fields = [["{0}.ALAND10".format(CENSUS_BLOCK_ROOT),  "SUM"  ],
                  ["{0}.AWATER10".format(CENSUS_BLOCK_ROOT), "SUM"  ],
                  ["{0}.GEOID10".format(CENSUS_BLOCK_ROOT),  "COUNT"],  # count block per maz
                 ]
        if maz_or_taz=="maz":
            # list the taz for the maz
            fields.append(["{0}.taz".format(CROSSWALK_ROOT), "FIRST"]) # verified taz are unique for maz above
        else:
            # count the mazs per taz
            fields.append(["{0}.maz".format(CROSSWALK_ROOT), "COUNT"])

        arcpy.Dissolve_management (blocks_maz_layer, "{0}_temp".format(shapefile),
                                   "{0}.{1}".format(CROSSWALK_ROOT, maz_or_taz), fields,
                                   "MULTI_PART", "DISSOLVE_LINES")
        logging.info("Dissolved {0}s into {1}_temp.shp".format(maz_or_taz, shapefile))

        # calculate partcount
        my_layer = "my_{0}_layer".format(maz_or_taz)
        arcpy.MakeFeatureLayer_management("{0}_temp.shp".format(shapefile), my_layer)
        arcpy.AddField_management(my_layer, "partcount", "SHORT", 6)
        arcpy.CalculateField_management(my_layer, "partcount", "!Shape.partCount!", "PYTHON3")
        logging.info("Calculated part count for {0}s".format(maz_or_taz))

        # add perimeter.  In meters because ALAND10 is square meters
        arcpy.AddGeometryAttributes_management(my_layer, "PERIMETER_LENGTH_GEODESIC", "METERS")
        logging.info("Calulated perimeter length for {0}s".format(maz_or_taz))

        # add perimeter squared over area
        arcpy.AddField_management(my_layer, "psq_overa", "DOUBLE", 10, 0)
        arcpy.CalculateField_management(my_layer, "psq_overa", "!PERIM_GEO!*!PERIM_GEO!/!ALAND10!", "PYTHON3")
        logging.info("Calculated perim*perim/area for {0}s".format(maz_or_taz))

        # delete maz/taz=0, that's not a real maz/taz
        arcpy.SelectLayerByAttribute_management(my_layer, "NEW_SELECTION", "{0} > 0".format(maz_or_taz))
        logging.info("Selected out water for {0}s".format(maz_or_taz))

        # Write the selected features to a new feature class and rename fields for clarity
        # todo: the alias names don't seem to be getting picked up, not sure why
        old_to_new = {"GEOID10":    ["blockcount","block count"],
                      "PERIM_GEO":  ["PERIM_GEO", "perimeter in meters"],
                      "psq_overa":  ["psq_overa", "perimeter squared over area"]}

        if maz_or_taz == "taz": old_to_new["maz"] = ["mazcount", "maz count"]

        rename_fields(my_layer, shapefile, old_to_new)
        logging.info("Saving final {0}s into {1}.shp".format(maz_or_taz, shapefile))

        # delete the temp
        arcpy.Delete_management("{0}_temp.shp".format(shapefile))

        # create geojson
        arcpy.FeaturesToJSON_conversion("{0}.shp".format(shapefile), "{0}.json".format(shapefile),
                                        geoJSON="GEOJSON")
        logging.info("Created {0}.json".format(shapefile))

    except Exception as err:
        logging.error(err.args[0])

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("--dissolve", dest="dissolve", action="store_true", help="Creates a dissolved maz shapefile and a dissolved taz shapefile.")
    args = parser.parse_args()

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
        crosswalk_out_df = blocks_maz_df[["GEOID10","maz","taz","GEOID10_TRACT"]]

        #####################################################
        # Create a table from the 2010 block neighbor mapping
        # For use in move_small_block_to_neighbor()
        blocks_neighbor_df = pandas.DataFrame(arcpy.da.TableToNumPyArray(
                        in_table=CENSUS_BLOCK_NEIGHBOR_DBF,
                        field_names=["src_GEOID1","nbr_GEOID1","LENGTH","NODE_COUNT"]))
        blocks_neighbor_df["nbr_GEIOID10_BG"] = blocks_neighbor_df["nbr_GEOID1"].str[:12]
        # get the maz/taz for these neighbors
        blocks_neighbor_df = pandas.merge(left    =blocks_neighbor_df,
                                          right   =blocks_maz_df[["GEOID10","maz","taz"]],
                                          how     ="left",
                                          left_on ="nbr_GEOID1",
                                          right_on="GEOID10")
        logging.info("blocks_neighbor_df has length {0}".format(len(blocks_neighbor_df)))
        logging.info("\n{0}".format(blocks_neighbor_df.head()))

    except Exception as err:
        logging.error(err.args[0])

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
    blocks_moved = 0
    for bigger_geo in ["taz","GEOID10_COUNTY","GEOID10_TRACT","GEOID10_BG"]:
        maz_geo_df = blocks_maz_df[["maz",bigger_geo]].groupby(["maz"]).agg("nunique")
        maz_multiple_geo_df = maz_geo_df.loc[ (maz_geo_df[bigger_geo] > 1) & ( maz_geo_df.index.isin(EXEMPT_MAZ)==False) ]
        if len(maz_multiple_geo_df) == 0:
            logging.info("Verified one {0} per maz".format(bigger_geo))
            continue

        if bigger_geo in ["GEOID10_BG","GEOID10_TRACT"]:
            # warn and try to fix
            logging.warning("Multiple {0} for a single maz: {1}".format(bigger_geo, len(maz_multiple_geo_df)))
            logging.warning("\n{0}".format(maz_multiple_geo_df.head(30)))
            blocks_moved += move_small_block_to_neighbor(blocks_maz_df, blocks_neighbor_df,
                                                         maz_multiple_geo_df, bigger_geo, crosswalk_out_df)
        else:
            # fatal
            logging.fatal("Multiple {0} for a single maz: {1}".format(bigger_geo, len(maz_multiple_geo_df)))
            logging.fatal("\n{0}".format(maz_multiple_geo_df.head(30)))
            sys.exit(2)

    # verify one TRACT/COUNTY per unique taz
    tazs_split = 0
    for bigger_geo in ["GEOID10_TRACT","GEOID10_COUNTY"]:
        taz_geo_df = blocks_maz_df[["taz",bigger_geo]].groupby(["taz"]).agg("nunique")
        taz_multiple_geo_df = taz_geo_df.loc[ (taz_geo_df[bigger_geo] > 1) & (taz_geo_df.index.isin(EXEMPT_TAZ)==False) ]
        if len(taz_multiple_geo_df) == 0:
            logging.info("Verified one {0} per taz".format(bigger_geo))
            continue

        if bigger_geo in ["GEOID10_TRACT"]:
            # warn
            logging.warning("Multiple {0} for a single taz: {1}".format(bigger_geo, len(taz_multiple_geo_df)))
            logging.warning("\n{0}".format(taz_multiple_geo_df.head(30)))
            # try to fix if mazs are all stable (so blocks_moved == 0) -- that should be fixed first
            if blocks_moved == 0:
                tazs_split = split_taz_for_tract(blocks_maz_df, taz_multiple_geo_df, crosswalk_out_df)
        else:
            # fatal
            logging.fatal("Multiple {0} for a single taz: {1}".format(bigger_geo, len(taz_multiple_geo_df)))
            logging.fatal("\n{0}".format(taz_multiple_geo_df.head(30)))
            sys.exit()

    # save updated draft crosswalk to look at if blocks have been moved or tazs have been split
    if (blocks_moved > 0) or (tazs_split > 0):
        crosswalk_out_df = crosswalk_out_df[["GEOID10","maz","taz"]]
        crosswalk_out_df.sort_values(by="GEOID10", ascending=True, inplace=True)
        crosswalk_out_df.to_csv(CROSSWALK_OUT, index=False, quoting=csv.QUOTE_NONNUMERIC)
        logging.info("Wrote updated draft crosswalk to {0}".format(CROSSWALK_OUT))

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
    blocks_maz_noland_df = blocks_maz_df.loc[ (blocks_maz_df.ALAND10 == 0)&(blocks_maz_df.GEOID10.isin(EXEMPT_NOLAND_BLOCK)==False) ]
    logging.info("Number of blocks with maz/taz without land area: {0}".format(len(blocks_maz_noland_df)))
    blocks_maz_noland_df[["GEOID10","ALAND10"]].to_csv("block_noland.csv", index=False)
    if len(blocks_maz_noland_df) > 0:
        logging.fatal("\n{0}".format(blocks_maz_noland_df))
        logging.fatal("")
        sys.exit("ERROR")

    # if we're not instructed to do this, we're done
    if args.dissolve == False: sys.exit(0)

    logging.info("Dissolving blocks into MAZs and TAZs")

    # clear selection
    arcpy.SelectLayerByAttribute_management(blocks_maz_layer, "CLEAR_SELECTION")

    dissolve_into_shapefile(blocks_maz_layer, "maz")

    dissolve_into_shapefile(blocks_maz_layer, "taz")


    sys.exit(0)
