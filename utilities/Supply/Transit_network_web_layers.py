# This script takes 15 shapefiles generated from Cube_to_shapefile.py as input and produces 15 web layers on ArcGIS Online

# The script is to be run within ArcGIS Pro's python window
# User will need top start a blank ArcGIS project (a .aprx file), open a basemap, and copy the following code in the Python window

import arcpy
import collections

INFILE_LOCATION = r"M:\Development\Travel Model Two\Supply\Transit\Network_QA\Cube_to_shapefile"

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

operator_files = [""]
operator_files = list(TRN_OPERATORS.keys())

# define projection
sr = arcpy.SpatialReference("NAD 1983 StatePlane California VI FIPS 0406 (US Feet)")

for operator_file in operator_files:

    operator_layer = INFILE_LOCATION + "/network_trn_lines_" + operator_file + ".shp"

    arcpy.DefineProjection_management(operator_layer, sr)

	# simplify the name of each layer
    aprx = arcpy.mp.ArcGISProject("CURRENT")	
    for m in aprx.listMaps():
        for lyr in m.listLayers():
            if lyr.name == "network_trn_lines_" + operator_file:
                print("Layer " + lyr.name + " is renamed to" + operator_file)
                lyr.name = operator_file 
       

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

# When the script is completed, user will have to go to ArcGIS Online, create a web map, and add the 15 layers to it
