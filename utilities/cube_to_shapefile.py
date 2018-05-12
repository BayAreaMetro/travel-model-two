USAGE = """

Create shapefile of Cube network.

For now, this only does the roadway network; transit networks is a todo.

"""

import argparse, csv, logging, os, subprocess, sys, traceback
import numpy, pandas

RUNTPP_PATH     = "C:\\Program Files (x86)\\Citilabs\\CubeVoyager"
PROJ_FILE       = "NAD 1983 StatePlane California VI FIPS 0406 (US Feet).prj"
LOG_FILE        = "cube_to_shapefile.log"

# temporary files in the CWD
NODE_DBFFILE    = "nodes.dbf"
LINK_DBFFILE    = "links.dbf"
LINK_POINTS_DBF = "link_points_table.dbf"
LINK_NOATTRS    = "link_noattr"
LINK_NOATTRS_SHP= "{0}.shp".format(LINK_NOATTRS)

# shapefiles
NODE_SHPFILE    = "network_nodes.shp"
LINK_SHPFILE    = "network_links.shp"

def runCubeScript(workingdir, script_filename, script_env):
    """
    Run the cube script specified in the workingdir specified.
    Returns the return code.
    """
    # run it
    proc = subprocess.Popen("{0} {1}".format(os.path.join(RUNTPP_PATH,"runtpp"), script_filename), 
                            cwd=workingdir, env=script_env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in proc.stdout:
        line_str = line.decode("utf-8")
        line_str = line_str.strip('\r\n')
        logging.info("  stdout: {0}".format(line_str))
    for line in proc.stderr:
        line_str = line.decode("utf-8")
        line_str = line_str.strip('\r\n')
        logging.info("  stderr: {0}".format(line_str))
    retcode = proc.wait()
    if retcode == 2:
        raise Exception("Failed to run Cube script %s" % (script_filename))
    logging.info("  Received {0} from 'runtpp {1}'".format(retcode, script_filename))

# from maz_taz_checker.py, I am sorry.  Library?!
def rename_fields(input_feature, output_feature, old_to_new):
    """
    Renames specified fields in input feature class/table
    old_to_new: {old_field: [new_field, new_alias]}
    """
    field_mappings = arcpy.FieldMappings()
    field_mappings.addTable(input_feature)

    for (old_field_name, new_list) in old_to_new.items():
        mapping_index          = field_mappings.findFieldMapIndex(old_field_name)
        if mapping_index < 0:
            message = "Field: {0} not in {1}".format(old_field_name, input_feature)
            raise Exception(message)

        field_map              = field_mappings.fieldMappings[mapping_index]
        output_field           = field_map.outputField
        output_field.name      = new_list[0]
        output_field.aliasName = new_list[1]
        field_map.outputField  = output_field
        field_mappings.replaceFieldMap(mapping_index, field_map)

    # use merge with single input just to use new field_mappings
    arcpy.Merge_management(input_feature, output_feature, field_mappings)
    return output_feature

if __name__ == '__main__':

    # assume code dir is where this script is
    CODE_DIR    = os.path.dirname(os.path.realpath(__file__))
    WORKING_DIR = os.getcwd()

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

    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("netfile", metavar="network.net", nargs=1, help="Cube input network file")
    args = parser.parse_args()

    # setup the environment
    script_env                 = os.environ.copy()
    script_env["PATH"]         = "{0};{1}".format(script_env["PATH"],RUNTPP_PATH)
    script_env["NET_INFILE"]   = args.netfile[0]
    script_env["NODE_OUTFILE"] = NODE_DBFFILE
    script_env["LINK_OUTFILE"] = LINK_DBFFILE

    # run the script to create NODE_DBFFILE and LINK_DBFFILE
    runCubeScript(WORKING_DIR, os.path.join(CODE_DIR, "export_network.job"), script_env)

    # MakeXYEventLayer_management
    import arcpy
    arcpy.env.workspace = WORKING_DIR

    # don't care if this fails, just want to head off error since arcpy gets mad if we try to overwrite
    try:
        arcpy.Delete_management(NODE_SHPFILE)
    except Exception as err:
        logging.debug(err.args[0])

    try:
        arcpy.Delete_management(LINK_POINTS_DBF)
    except Exception as err:
        logging.debug(err.args[0])

    try:
        arcpy.Delete_management(LINK_NOATTRS_SHP)
    except Exception as err:
        logging.debug(err.args[0])

    try:
        arcpy.Delete_management(LINK_SHPFILE)
    except Exception as err:
        logging.debug(err.args[0])

    try:
        node_layer = "node_layer"
        arcpy.MakeXYEventLayer_management(NODE_DBFFILE, in_x_field="X", in_y_field="Y",
                                          out_layer=node_layer, spatial_reference=os.path.join(WORKING_DIR, PROJ_FILE))
        arcpy.CopyFeatures_management(node_layer, NODE_SHPFILE)
        logging.info("Created {0}".format(NODE_SHPFILE))

        # create Dataframe
        node_field_names = [
            "N","X","Y","COUNTY","MODE","STOP","PNR_CAP",
            "PNR1","PNR2","PNR3","PNR4","PNR5",
            "PNR_FEE1","PNR_FEE2","PNR_FEE3","PNR_FEE4","PNR_FEE5", "FAREZONE"
        ]
        nodes_df = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray(in_table=node_layer, field_names=node_field_names))
        logging.info("nodes_df has length {0}".format(len(nodes_df)))
        logging.info(nodes_df.head())

        # for links, first we make a points layer with A and B points
        link_table_layer = "link_table_layer"
        arcpy.MakeTableView_management(LINK_DBFFILE, link_table_layer)
        if len(arcpy.ListFields(link_table_layer, "A_B"))==0:
            arcpy.AddField_management(link_table_layer, "A_B", "TEXT", 21)
            arcpy.CalculateField_management(link_table_layer, "A_B", "str(!A!)+'_'+str(!B!)", "PYTHON3")
            logging.info("Calculated A_B")

        links_df = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray(in_table=link_table_layer, field_names=["A","B","A_B"]))
        logging.debug("links_df has length {0}".format(len(links_df)))
        logging.debug("\n{0}".format(links_df.head()))

        link_A_points_df = pandas.merge(left=links_df[["A_B","A"]], right=nodes_df[["N","X","Y"]], left_on="A", right_on="N", how="left")
        link_B_points_df = pandas.merge(left=links_df[["A_B","B"]], right=nodes_df[["N","X","Y"]], left_on="B", right_on="N", how="left")

        assert( len(link_A_points_df.loc[ pandas.isnull(link_A_points_df.X) ]) == 0)
        assert( len(link_A_points_df.loc[ pandas.isnull(link_B_points_df.X) ]) == 0)

        # sort field
        link_A_points_df["node"] = 1
        link_B_points_df["node"] = 2
        link_points_df = pandas.concat([link_A_points_df, link_B_points_df], axis="index")
        link_points_df.reset_index(drop=True, inplace=True)
        logging.debug("\n{0}".format(link_points_df.head()))

        link_points_arr = numpy.array(link_points_df[["A_B","N","X","Y","node"]].to_records(),
                                      numpy.dtype([('index',numpy.uint32),
                                                   ('A_B',"U21"),
                                                   ('N',numpy.uint32),
                                                   ('X',numpy.double),
                                                   ('Y',numpy.double),
                                                   ('node',numpy.int8)]))

        # convert to a Table
        link_points_table = LINK_POINTS_DBF
        arcpy.da.NumPyArrayToTable(link_points_arr, os.path.join(WORKING_DIR,link_points_table))
        logging.info("Created table {0}".format(link_points_table))

        # create points
        link_points_layer = "link_points_layer"
        arcpy.MakeXYEventLayer_management(table=link_points_table, in_x_field="X", in_y_field="Y",
                                          out_layer=link_points_layer, spatial_reference=os.path.join(WORKING_DIR, PROJ_FILE))
        logging.info("Made layer {0}".format(link_points_layer))

        arcpy.PointsToLine_management(link_points_layer, LINK_NOATTRS_SHP, "A_B", "node")
        logging.info("Created initial links in {0}".format(LINK_NOATTRS_SHP))

        # join it to the rest of the attributes
        link_layer = "link_layer"
        arcpy.MakeFeatureLayer_management(LINK_NOATTRS_SHP, link_layer)
        arcpy.AddJoin_management(link_layer, "A_B", LINK_DBFFILE, "A_B")
        logging.info("Joined with link attributes")

        #  list the link fields
        link_fields = arcpy.ListFields(link_layer)
        rename_dict = {}
        for field in link_fields:
            logging.info("  {0:50s} is a type of {1:15s} with a length of {2}".format(field.name, field.type, field.length))
            if field.name.startswith("links."):
                # this is odd, renaming a field to itself, but that's because the default is to rename to links.XXX
                rename_dict[field.name[6:]] = [field.name[6:], field.name[6:]]
        # print(rename_dict)

        # drop a couple useless fields
        arcpy.DeleteField_management(link_layer, ["Id"])

        # rename the other fields to their original
        rename_fields(link_layer, LINK_SHPFILE, rename_dict)
        logging.info("Created links in {0}".format(LINK_SHPFILE))

    except Exception as err:
        logging.error(err.args[0])
        traceback.print_exc(file=sys.stdout)

    # clean up temporary files
    try:
        arcpy.Delete_management(LINK_POINTS_DBF)
    except Exception as err:
        logging.debug(err.args[0])

    try:
        arcpy.Delete_management(LINK_NOATTRS_SHP)
    except Exception as err:
        logging.debug(err.args[0])
