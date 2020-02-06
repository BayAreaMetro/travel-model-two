# This script takes 15 shapefiles generated from Cube_to_shapefile.py as input and produces 15 web layers on ArcGIS Online

# The script is to be run within ArcGIS Pro's python window
# User will need top start a blank ArcGIS project (a .aprx file), open a basemap, and copy the following code in the Python window

import arcpy
import collections

INFILE_LOCATION = r"M:\Development\Travel Model Two\Supply\Transit\Network_QA\Cube_to_shapefile"

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

    operator_layer = INFILE_LOCATION + "/network_trn_lines_" + operator_file + ".shp"

    arcpy.DefineProjection_management(operator_layer, sr)

	# simplify the name of each layer
    for m in aprx.listMaps():
        for lyr in m.listLayers():
            if lyr.name == "network_trn_lines_" + operator_file:
                print("Layer " + lyr.name + " is renamed to " + operator_file + VERSION_INDICATOR)
                lyr.name = operator_file + VERSION_INDICATOR
       

# save the ArcGIS project
aprx.save()


# A references publishing web layers: http://pro.arcgis.com/en/pro-app/arcpy/mapping/createweblayersddraft.htm
# import arcpy
# aprx = arcpy.mp.ArcGISProject('C:/Project/Counties.aprx')
# m = aprx.listMaps('USA Counties')[0]
# lyr = m.listLayers('Cities')[0]
# arcpy.mp.CreateWebLayerSDDraft(lyr, 'C:/Project/Cities.sddraft', 'Cities', 'MY_HOSTED_SERVICES', 'FEATURE_ACCESS')
# arcpy.StageService_server('C:/Project/Cities.sddraft', 'C:/Project/Cities.sd')
# arcpy.UploadServiceDefinition_server('C:/Project/Cities.sd', 'My Hosted Services')


# publish web layers 
# aprx = arcpy.mp.ArcGISProject("CURRENT")
for m in aprx.listMaps():
    for lyr in m.listLayers():
	
        if lyr.name != 'Topographic':
            arcpy.mp.CreateWebLayerSDDraft(lyr, INFILE_LOCATION + "/" + lyr.name + '.sddraft', lyr.name, 'MY_HOSTED_SERVICES', 'FEATURE_ACCESS')
            arcpy.StageService_server(INFILE_LOCATION + "/"  + lyr.name + '.sddraft', 'M:/Development/Travel Model Two/Supply/Transit/Network_QA/Cube_to_shapefile/' + lyr.name + '.sd')
            arcpy.UploadServiceDefinition_server(INFILE_LOCATION + "/"  + lyr.name + '.sd', 'My Hosted Services')

print("Finished publishing web layers")

# Post-processing: when the script is completed, user will have to go to ArcGIS Online, create a web map, and add the 15 layers to it

# Note: the script will not overwrite web layers on ArcGIS Online. If users want to replace the web layers of a web map, they will need to delete the layers from ArcGIS Online manually
