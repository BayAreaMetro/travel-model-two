# use python in c:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3
import arcpy
import csv, os, sys

WORKSPACE    = "M:\\Application\\Model One\\RTP2017\\Scenarios\\2040_06_694\\INPUT\\trn\\transit_stop_shapefile_export\\NetworkProject2040"
BROKEN_SHAPE = "PTNetwork_PTNode.shp"
NODE_X_Y     = os.path.join(WORKSPACE, "..", "support_nodes.csv")
SPATIAL_REF  = 26910 # NAD_1983_UTM_Zone_10N for TM1

if __name__ == '__main__':

    arcpy.env.workspace = WORKSPACE
    arcpy.env.qualifiedFieldNames = False  # ?

    ########################################################
    # Read broken layer
    broken_layer = "broken_layer"
    arcpy.MakeFeatureLayer_management(BROKEN_SHAPE, broken_layer)
    parts_count = arcpy.GetCount_management(broken_layer)
    print("Created feature layer with {0} rows".format(parts_count[0]))

    # read the support support_nodes
    support_node_dict = {}  # node number -> x, y, comment
    with open(NODE_X_Y) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            support_node_dict[ int(row["NODE"])] = (float(row["X"]), float(row["Y"]), row["comment"])
    # print(support_node_dict[10910])

    with arcpy.da.UpdateCursor(broken_layer, ["SHAPE@","NODES"]) as cursor:
        for row in cursor:
            # print(row[0])
            # print(row[1])

            if row[0] == None:
                broken_node = row[1]
                print("Fixing null geometry for NODES {}".format(broken_node))

                row[0] = arcpy.PointGeometry( arcpy.Point(support_node_dict[broken_node][0],
                                                          support_node_dict[broken_node][1]),
                                              arcpy.SpatialReference(SPATIAL_REF) )
                cursor.updateRow(row)

