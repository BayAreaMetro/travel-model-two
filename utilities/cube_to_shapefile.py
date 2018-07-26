USAGE = """

Create shapefile of Cube network, roadway and transit.

"""

import argparse, collections, csv, logging, os, subprocess, sys, traceback
import numpy, pandas
import Wrangler

RUNTPP_PATH     = "C:\\Program Files (x86)\\Citilabs\\CubeVoyager"
LOG_FILE        = "cube_to_shapefile.log"

# shapefiles
NODE_SHPFILE    = "network_nodes.shp"
LINK_SHPFILE    = "network_links.shp"

TRN_LINES_SHPFILE = "network_trn_lines{}.shp"
TRN_LINKS_SHPFILE = "network_trn_links{}.shp"
TRN_STOPS_SHPFILE = "network_trn_stops{}.shp"

TRN_OPERATORS = collections.OrderedDict([
    # filename_append       # list of operator text
    ("_SF_Muni",             ["San Francisco MUNI"]),
    ("_SC_VTA",              ["Santa Clara VTA"]),
    ("_AC_Transit",          ["AC Transit", "AC Transbay"]),
    ("_SM_SamTrans",         ["samTrans"]),
    ("_SC_Transit",          ["Sonoma County Transit"]),
    ("_CC_CountyConnection", ["The County Connection"]),
    ("_GG_Transit",          ["Golden Gate Transit", "Golden Gate Ferry"]),
    ("_WestCAT",             ["WestCAT"]),
    ("_WHEELS",              ["WHEELS"]),
    ("_Stanford",            ["Stanford Marguerite Shuttle"]),
    ("_TriDelta",            ["TriDelta Transit"]),
    ("_Caltrain",            ["Caltrain"]),
    ("_BART",                ["BART"]),
    ("_ferry",               ["Alameda Harbor Bay Ferry", "Alameda/Oakland Ferry","Angel Island - Tiburon Ferry",
                              "Oakland/South SSF Ferry", "South SF/Oakland Ferry", "Vallejo Baylink Ferry"]),
    ("_other" ,              []),  # this will get filled in with operators not covered already
])

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
    parser.add_argument("netfile",  metavar="network.net", nargs=1, help="Cube input roadway network file")
    parser.add_argument("--linefile", metavar="transit.lin", nargs=1, help="Cube input transit line file", required=False)
    parser.add_argument("--by_operator", action="store_true", help="Split transit lines by operator")
    args = parser.parse_args()
    print(args)

    # setup the environment
    script_env                 = os.environ.copy()
    script_env["PATH"]         = "{0};{1}".format(script_env["PATH"],RUNTPP_PATH)
    script_env["NET_INFILE"]   = args.netfile[0]
    script_env["NODE_OUTFILE"] = NODE_SHPFILE
    script_env["LINK_OUTFILE"] = LINK_SHPFILE

    # run the script to do the work
    # runCubeScript(WORKING_DIR, os.path.join(CODE_DIR, "export_network.job"), script_env)
    print("Wrote network node file to {}".format(NODE_SHPFILE))
    print("Wrote network link file to {}".format(LINK_SHPFILE))

    # MakeXYEventLayer_management
    import arcpy
    arcpy.env.workspace = WORKING_DIR

    # define the spatial reference
    sr = arcpy.SpatialReference(102646)
    arcpy.DefineProjection_management(NODE_SHPFILE, sr)
    arcpy.DefineProjection_management(LINK_SHPFILE, sr)

    # if we don't have a transit file, then we're done
    if not args.linefile: sys.exit(0)

    operator_files = [""]
    if args.by_operator:
        operator_files = list(TRN_OPERATORS.keys())

    # store cursors here
    line_cursor      = {}
    link_cursor      = {}
    stop_cursor      = {}
    operator_to_file = {}

    for operator_file in operator_files:
        if args.by_operator:
            for op_txt in TRN_OPERATORS[operator_file]:
                operator_to_file[op_txt] = operator_file

        # delete shapefiles if one exists already
        arcpy.Delete_management(TRN_LINES_SHPFILE.format(operator_file))
        arcpy.Delete_management(TRN_LINKS_SHPFILE.format(operator_file))
        arcpy.Delete_management(TRN_STOPS_SHPFILE.format(operator_file))

        # create the lines shapefile
        arcpy.CreateFeatureclass_management(WORKING_DIR, TRN_LINES_SHPFILE.format(operator_file), "POLYLINE")
        arcpy.AddField_management(TRN_LINES_SHPFILE.format(operator_file), "NAME", "TEXT", field_length=25)
        arcpy.AddField_management(TRN_LINES_SHPFILE.format(operator_file), "HEADWAY_EA", "FLOAT")
        arcpy.AddField_management(TRN_LINES_SHPFILE.format(operator_file), "HEADWAY_AM", "FLOAT")
        arcpy.AddField_management(TRN_LINES_SHPFILE.format(operator_file), "HEADWAY_MD", "FLOAT")
        arcpy.AddField_management(TRN_LINES_SHPFILE.format(operator_file), "HEADWAY_PM", "FLOAT")
        arcpy.AddField_management(TRN_LINES_SHPFILE.format(operator_file), "HEADWAY_EV", "FLOAT")
        arcpy.AddField_management(TRN_LINES_SHPFILE.format(operator_file), "MODE",       "SHORT")
        arcpy.AddField_management(TRN_LINES_SHPFILE.format(operator_file), "MODE_TYPE",  "TEXT", field_length=15)
        arcpy.AddField_management(TRN_LINES_SHPFILE.format(operator_file), "OPERATOR_T", "TEXT", field_length=40)
        arcpy.AddField_management(TRN_LINES_SHPFILE.format(operator_file), "VEHICLETYP","SHORT")
        arcpy.AddField_management(TRN_LINES_SHPFILE.format(operator_file), "OPERATOR",   "SHORT")

        line_cursor[operator_file] = arcpy.da.InsertCursor(TRN_LINES_SHPFILE.format(operator_file), ["NAME", "SHAPE@",
                                   "HEADWAY_EA", "HEADWAY_AM", "HEADWAY_MD", "HEADWAY_PM", "HEADWAY_EV",
                                   "MODE", "MODE_TYPE", "OPERATOR_T", "VEHICLETYP", "OPERATOR"])

        # create the lines shapefile
        arcpy.CreateFeatureclass_management(WORKING_DIR, TRN_LINKS_SHPFILE.format(operator_file), "POLYLINE")
        arcpy.AddField_management(TRN_LINKS_SHPFILE.format(operator_file), "NAME",    "TEXT", field_length=25)
        arcpy.AddField_management(TRN_LINKS_SHPFILE.format(operator_file), "A",       "LONG")
        arcpy.AddField_management(TRN_LINKS_SHPFILE.format(operator_file), "B",       "LONG")
        arcpy.AddField_management(TRN_LINKS_SHPFILE.format(operator_file), "SEQ",     "SHORT")

        link_cursor[operator_file] = arcpy.da.InsertCursor(TRN_LINKS_SHPFILE.format(operator_file),
                                                           ["NAME", "SHAPE@", "A", "B", "SEQ"])

        # create the stops shapefile
        arcpy.CreateFeatureclass_management(WORKING_DIR, TRN_STOPS_SHPFILE.format(operator_file), "POINT")
        arcpy.AddField_management(TRN_STOPS_SHPFILE.format(operator_file), "NAME",     "TEXT", field_length=25)
        arcpy.AddField_management(TRN_STOPS_SHPFILE.format(operator_file), "N",        "LONG")
        arcpy.AddField_management(TRN_STOPS_SHPFILE.format(operator_file), "SEQ",      "SHORT")
        arcpy.AddField_management(TRN_STOPS_SHPFILE.format(operator_file), "IS_STOP",  "SHORT")

        stop_cursor[operator_file] = arcpy.da.InsertCursor(TRN_STOPS_SHPFILE.format(operator_file),
                                                           ["NAME", "SHAPE@", "N", "SEQ", "IS_STOP"])

    print(operator_to_file)

    # read the node points
    nodes_array = arcpy.da.TableToNumPyArray(in_table="{}.DBF".format(NODE_SHPFILE[:-4]),
                                             field_names=["N","X","Y"])
    nodes_x =  dict(zip(nodes_array["N"].tolist(), nodes_array["X"].tolist()))
    nodes_y =  dict(zip(nodes_array["N"].tolist(), nodes_array["Y"].tolist()))

    (trn_file_base, trn_file_name) = os.path.split(args.linefile[0])
    print(trn_file_base, trn_file_name)
    trn_net = Wrangler.TransitNetwork(champVersion=4.3, basenetworkpath=trn_file_base, isTiered=True, networkName=trn_file_name[:-4])
    print("Read trn_net: {}".format(trn_net))

    # build lines and links
    line_count = 0
    link_count = 0
    stop_count = 0
    for line in trn_net:
        # print(line)

        line_point_array = arcpy.Array()
        link_point_array = arcpy.Array()
        last_n = -1
        seq    = 1
        op_txt = line.attr['USERA1'].strip('\""')

        if not args.by_operator:
            operator_file = ""
        elif op_txt in operator_to_file:
            operator_file = operator_to_file[op_txt]
        else:
            operator_file = "_other"
            operator_to_file[op_txt] = operator_file
            if op_txt not in TRN_OPERATORS[operator_file]:
                TRN_OPERATORS[operator_file].append(op_txt)

        print("Adding line {:4}/{:4} {:25} operator {:40} to operator_file [{}]".format(
              line_count+1,len(trn_net.lines),
              line.name, op_txt, operator_file))
        # for attr_key in line.attr: print(attr_key, line.attr[attr_key])

        for node in line.n:
            n = abs(int(node.num))
            is_stop = 1 if node.isStop() else 0
            # print(node.num, n, node.attr, node.stop)
            point = arcpy.Point( nodes_x[n], nodes_y[n] )

            # start at 0 for stops
            stop_cursor[operator_file].insertRow([line.name, point, n, seq-0, is_stop])
            stop_count += 1

            # add to line array
            line_point_array.add(point)

            link_point_array.add(point)
            if link_point_array.count > 1:
                plink_shape = arcpy.Polyline(link_point_array)
                link_cursor[operator_file].insertRow([line.name, plink_shape,
                                                      last_n, n, seq])
                link_count += 1
                link_point_array.remove(0)

            last_n = n
            seq += 1

        pline_shape = arcpy.Polyline(line_point_array)
        line_cursor[operator_file].insertRow([line.name, pline_shape,
                                              float(line.attr['HEADWAY[1]']),
                                              float(line.attr['HEADWAY[2]']),
                                              float(line.attr['HEADWAY[3]']),
                                              float(line.attr['HEADWAY[4]']),
                                              float(line.attr['HEADWAY[5]']),
                                              line.attr['MODE'],
                                              line.attr['USERA2'].strip('\""'), # mode type
                                              op_txt, # operator
                                              line.attr['VEHICLETYPE'],
                                              line.attr['OPERATOR']
                                            ])
        line_count += 1

    del stop_cursor
    print("Wrote {} stops to {}".format(stop_count, TRN_STOPS_SHPFILE))

    del line_cursor
    print("Wrote {} lines to {}".format(line_count, TRN_LINES_SHPFILE))

    del link_cursor
    print("Write {} links to {}".format(link_count, TRN_LINKS_SHPFILE))