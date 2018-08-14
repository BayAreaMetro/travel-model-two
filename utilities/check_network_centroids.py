USAGE="""

"""

# maz 10186, 16084, 111433, 411178 are exceptions

# use python in c:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3
import arcpy, pandas
import logging, os, sys

WORKSPACE  = "M:\\Data\\GIS layers\\tm2_2015_network"
LOG_FILE   = "check_network_centroids.log"

SHAPEFILES = {
    "nodes":"network_nodes.shp",
    "maz"  :"M:\\Data\\GIS layers\\TM2_maz_taz_v2.2\\mazs_TM2_v2_2.shp",
    "taz"  :"M:\\Data\\GIS layers\\TM2_maz_taz_v2.2\\tazs_TM2_v2_2.shp"
}

# http://bayareametro.github.io/travel-model-two/input/#roadway-network
NODE_SELECTION = {
    "taz":
"""((N >      0) AND (N <  10000)) OR
   ((N > 100000) AND (N < 110000)) OR
   ((N > 200000) AND (N < 210000)) OR
   ((N > 300000) AND (N < 310000)) OR
   ((N > 400000) AND (N < 410000)) OR
   ((N > 500000) AND (N < 510000)) OR
   ((N > 600000) AND (N < 610000)) OR
   ((N > 700000) AND (N < 710000)) OR
   ((N > 800000) AND (N < 810000))""",
    "maz":
"""((N >  10000) AND (N <  90000)) OR
   ((N > 110000) AND (N < 190000)) OR
   ((N > 210000) AND (N < 290000)) OR
   ((N > 310000) AND (N < 390000)) OR
   ((N > 410000) AND (N < 490000)) OR
   ((N > 510000) AND (N < 590000)) OR
   ((N > 610000) AND (N < 690000)) OR
   ((N > 710000) AND (N < 790000)) OR
   ((N > 810000) AND (N < 890000))"""
}


if __name__ == '__main__':

    pandas.options.display.width = 300
    pandas.options.display.float_format = '{:.2f}'.format

    arcpy.env.workspace = WORKSPACE
    arcpy.env.qualifiedFieldNames = False

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

    for geo_type in ["maz", "taz"]:

        # it's ok if this fails
        for try_deleting in ["node_{}_centroids.shp".format(geo_type),
                             "{}s_copy.shp".format(geo_type),
                             "{}_contains_centroids.shp".format(geo_type),
                             "{}_contains_centroids_mismatch.shp".format(geo_type)]:
            try:
                arcpy.Delete_management(try_deleting)
                logging.debug("Deleted {}".format(try_deleting))
            except:
                pass

        try:

            # Load the nodes and use the definition query to select only the maz/taz centroids
            node_layer = "node_{}_lyr".format(geo_type)
            arcpy.MakeFeatureLayer_management(SHAPEFILES["nodes"], node_layer, NODE_SELECTION[geo_type])
            result = arcpy.GetCount_management(node_layer)
            logging.info('MakeFeatureLayer      : {0:20} has {1:8} records'.format(node_layer, result[0]))

            # Save these to a new layer/shapefile (trying to join with the original layer loses rows for some reason)
            node_centroids = "node_{}_centroids".format(geo_type)
            arcpy.CopyFeatures_management(node_layer, "{}.shp".format(node_centroids))
            arcpy.MakeFeatureLayer_management("{}.shp".format(node_centroids), node_centroids)
            logging.info('CopyFeatures          : {0:20} has {1:8} records'.format(node_centroids, result[0]))

            # Load the shapefile layer
            shape_layer = "shape_{}_lyr".format(geo_type)
            arcpy.MakeFeatureLayer_management(SHAPEFILES[geo_type], shape_layer)
            result = arcpy.GetCount_management(shape_layer)
            logging.info('MakeFeatureLayer      : {0:20} has {1:8} records'.format(shape_layer, result[0]))

            # 3 classes of problems
            ########################
            # 1) maz/taz exists, centroid does not
            logging.info("1) {} exists, centroid does not".format(geo_type))

            # Make a local copy of the shapefile for the new field
            shape_local = "{}s_copy".format(geo_type)
            arcpy.CopyFeatures_management(shape_layer, "{}.shp".format(shape_local))
            arcpy.MakeFeatureLayer_management("{}.shp".format(shape_local), shape_local)
            logging.info('CopyFeatures          : {0:20} has {1:8} records'.format(shape_local, result[0]))

            # Join shapefile on nodes N
            arcpy.AddJoin_management(shape_local, geo_type, node_centroids, "N", "KEEP_ALL")
            result = arcpy.GetCount_management(shape_local)
            logging.info('AddJoin               : {0:20} has {1:8} records'.format(shape_local, result[0]))

            # set noCentroid for null N
            arcpy.AddField_management(shape_local, "noCentroid", "SHORT", 6)
            arcpy.CalculateField_management(shape_local, "noCentroid", '0 if !N! else 1', "PYTHON3")
            logging.info('CalculateField        : {0:20} has {1:8} records'.format(shape_local, result[0]))

            # remove the join, we're done
            arcpy.RemoveJoin_management (shape_local, node_centroids)

            # create pandas dataframe of table
            fields = arcpy.ListFields(shape_local)
            field_names = []
            for field in fields:
                logging.info("  {0:50s} is a type of {1:15s} with a length of {2}".format(field.name, field.type, field.length))
                if field.name not in ["FID","Shape"]: field_names.append(field.name)
            shape_local_df = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray(
                             in_table=shape_local, field_names=field_names))

            # filter to only those with noCentroid
            shape_local_df = shape_local_df.loc[ shape_local_df.noCentroid == 1]
            logging.debug("{} rows:\n{}".format(len(shape_local_df), str(shape_local_df)))

            # 2) maz/taz does not exist, centroid does
            logging.info("2) {} does not exist, centroid does".format(geo_type))

            # Join centroid node N on shapefile
            arcpy.AddJoin_management(node_centroids, "N", shape_local, geo_type, "KEEP_ALL")
            result = arcpy.GetCount_management(node_centroids)
            logging.info('AddJoin               : {0:20} has {1:8} records'.format(node_centroids, result[0]))

            # set xtraCentroid for null Shape
            arcpy.AddField_management(node_centroids, "xtraCentro", "SHORT", 6)
            arcpy.CalculateField_management(node_centroids, "xtraCentro", '0 if !{}! else 1'.format(geo_type), "PYTHON3")
            result = arcpy.GetCount_management(node_centroids)
            logging.info('CalculateField        : {0:20} has {1:8} records'.format(node_centroids, result[0]))

            # remove the join, we're done
            arcpy.RemoveJoin_management (node_centroids, shape_local)

            # create pandas dataframe of table
            fields = arcpy.ListFields(node_centroids)
            field_names = []
            for field in fields:
                logging.info("  {0:50s} is a type of {1:15s} with a length of {2}".format(field.name, field.type, field.length))
                if field.name not in ["FID","Shape"]: field_names.append(field.name)
            node_centroids_df = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray(
                                in_table=node_centroids, field_names=field_names))

            # filter to only those with xtraCentro
            node_centroids_df = node_centroids_df.loc[ node_centroids_df.xtraCentro == 1]
            logging.debug("{} rows:\n{}".format(len(node_centroids_df), str(node_centroids_df)))

            # 3) both exist, but centroid is not within the maz/taz boundary
            logging.info("3) {} and centroid both exist - containment check".format(geo_type))

            # Spatial join the shapefile on nodes
            contains_centroids = "{}_contains_centroids".format(geo_type)
            arcpy.SpatialJoin_analysis(shape_local, node_centroids, "{}.shp".format(contains_centroids),
                                       join_operation="JOIN_ONE_TO_MANY", join_type="KEEP_ALL", match_option="CONTAINS")
            result = arcpy.GetCount_management("{}.shp".format(contains_centroids))
            logging.info('SpatialJoin           : {0:20} has {1:8} records'.format(contains_centroids + ".shp", result[0]))

            # Select the mismatches only
            arcpy.MakeFeatureLayer_management("{}.shp".format(contains_centroids), contains_centroids)
            arcpy.SelectLayerByAttribute_management (contains_centroids, "NEW_SELECTION", "{} <> N".format(geo_type))

            # Save it
            contains_mismatch = "{}_contains_centroids_mismatch.shp".format(geo_type)
            arcpy.CopyFeatures_management(contains_centroids, contains_mismatch)
            result = arcpy.GetCount_management(contains_mismatch)
            logging.info('SelectLayerByAttribute: {0:20} has {1:8} records'.format(contains_mismatch, result[0]))

            # create pandas dataframe of table
            fields = arcpy.ListFields(contains_mismatch)
            field_names = []
            for field in fields:
                logging.info("  {0:50s} is a type of {1:15s} with a length of {2}".format(field.name, field.type, field.length))
                if field.name not in ["FID","Shape"]: field_names.append(field.name)
            contains_mismatch_df = pandas.DataFrame(arcpy.da.FeatureClassToNumPyArray(
                                in_table=contains_mismatch, field_names=field_names))

            # filter to only those with xtraCentro
            logging.debug("{} rows:\n{}".format(len(contains_mismatch_df), str(contains_mismatch_df)))

        except Exception as inst:
            logging.error(type(inst))
            logging.error(inst.args)
            logging.error(inst)
            logging.error(arcpy.GetMessages())
            raise