# This script takes 15 shapefiles generated from Cube_to_shapefile.py as input and add them to a .aprx

# The script is to be run within ArcGIS Pro's python window
# User will need top start a blank ArcGIS project (a .aprx file), open a basemap, and copy the following code in the Python window

import arcpy
import collections

INFILE_LOCATION = r"M:\Development\Travel Model Two\Supply\Transit\Network_QA\Cube_to_shapefile_Sep2018RMWG"

# the version indicator will appear as a suffix of the map layer
# it is needed so that different versions of the same operator's web map can be saved on ArcGIS online
VERSION_INDICATOR = ""

TRN_OPERATORS = collections.OrderedDict([
    # filename_append       # list of operator text
    ("other" ,              []),
    ("ferry",               ["Alameda Harbor Bay Ferry", "Alameda/Oakland Ferry","Angel Island - Tiburon Ferry",
                              "Oakland/South SSF Ferry", "South SF/Oakland Ferry", "Vallejo Baylink Ferry"]),
    ("BART",                ["BART"]),
    ("Caltrain",            ["Caltrain"]),
    ("TriDelta",            ["TriDelta Transit"]),
    ("Stanford",            ["Stanford Marguerite Shuttle"]),
    ("WHEELS",              ["WHEELS"]),
    ("WestCAT",             ["WestCAT"]),
    ("GG_Transit",          ["Golden Gate Transit", "Golden Gate Ferry"]),
    ("CC_CountyConnection", ["The County Connection"]),
    ("SC_Transit",          ["Sonoma County Transit"]),
    ("SM_SamTrans",         ["samTrans"]),
    ("AC_Transit",          ["AC Transit", "AC Transbay"]),
    ("SC_VTA",              ["Santa Clara VTA"]),
    ("SF_Muni",             ["San Francisco MUNI"]),
])

# refer to current ArcGIS project
aprx = arcpy.mp.ArcGISProject("CURRENT")

operator_files = [""]
operator_files = list(TRN_OPERATORS.keys())

# define projection
sr = arcpy.SpatialReference("NAD 1983 StatePlane California VI FIPS 0406 (US Feet)")

for operator_file in operator_files:

    operator_layer = INFILE_LOCATION + "/network_trn_stops_" + operator_file + ".shp"

    arcpy.DefineProjection_management(operator_layer, sr)

	# simplify the name of each layer
    for m in aprx.listMaps():
        for lyr in m.listLayers():
            if lyr.name == "network_trn_stops_" + operator_file:
                print("Layer " + lyr.name + " is renamed to " + operator_file + VERSION_INDICATOR)
                lyr.name = operator_file + VERSION_INDICATOR


# save the ArcGIS project
aprx.save()

# manually update the coordinate system of the map to WGS 84
# see the instructions for "Set the coordinate system from a layer" in:
# http://pro.arcgis.com/en/pro-app/help/mapping/properties/specify-a-coordinate-system.htm
# this is done manually as it seems it is not possible to modify the spatial reference of a map/map frame using arcpy
# see: https://community.esri.com/ideas/12767-allow-arcpymp-to-modify-spatial-reference-property-of-mapmapframe

# final step: manually publish it as a web map
