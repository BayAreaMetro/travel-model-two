import arcpy
import collections

file_location = r"M:\Development\Travel Model Two\Supply\Transit\Network_QA\Cube_to_shapefile\network_trn_lines"

TRN_OPERATORS = collections.OrderedDict([
    # filename_append       # list of operator text
    ("_other" ,              []),
    ("_ferry",               ["Alameda Harbor Bay Ferry", "Alameda/Oakland Ferry","Angel Island - Tiburon Ferry",
                              "Oakland/South SSF Ferry", "South SF/Oakland Ferry", "Vallejo Baylink Ferry"]),
    ("_BART",                ["BART"]),
    ("_Caltrain",            ["Caltrain"]),
    ("_TriDelta",            ["TriDelta Transit"]),
    ("_Stanford",            ["Stanford Marguerite Shuttle"]),
    ("_WHEELS",              ["WHEELS"]),
    ("_WestCAT",             ["WestCAT"]),
    ("_GG_Transit",          ["Golden Gate Transit", "Golden Gate Ferry"]),
    ("_CC_CountyConnection", ["The County Connection"]),
    ("_SC_Transit",          ["Sonoma County Transit"]),
    ("_SM_SamTrans",         ["samTrans"]),
    ("_AC_Transit",          ["AC Transit", "AC Transbay"]),
    ("_SC_VTA",              ["Santa Clara VTA"]),
    ("_SF_Muni",             ["San Francisco MUNI"]),
])

operator_files = [""]
operator_files = list(TRN_OPERATORS.keys())

# define projection
sr = arcpy.SpatialReference("NAD 1983 StatePlane California VI FIPS 0406 (US Feet)")

for operator_file in operator_files:

#   operator_layer = r"M:\Development\Travel Model Two\Supply\Transit\Network_QA\Cube_to_shapefile\network_trn_lines" + operator_file + ".shp"
#   operator_layer = r"" + file_location + operator_file + ".shp"
   operator_layer = file_location + operator_file + ".shp"

   arcpy.DefineProjection_management(operator_layer, sr)


# publish web layers
# references: http://pro.arcgis.com/en/pro-app/arcpy/mapping/createweblayersddraft.htm
# import arcpy
# aprx = arcpy.mp.ArcGISProject('C:/Project/Counties.aprx')
# m = aprx.listMaps('USA Counties')[0]
# lyr = m.listLayers('Cities')[0]
# arcpy.mp.CreateWebLayerSDDraft(lyr, 'C:/Project/Cities.sddraft', 'Cities', 'MY_HOSTED_SERVICES', 'FEATURE_ACCESS')
# arcpy.StageService_server('C:/Project/Cities.sddraft', 'C:/Project/Cities.sd')
# arcpy.UploadServiceDefinition_server('C:/Project/Cities.sd', 'My Hosted Services')


aprx = arcpy.mp.ArcGISProject("CURRENT")
for m in aprx.listMaps():
    print("Map: {0} Layers".format(m.name))
    for lyr in m.listLayers():
        if lyr.isBroken:
            print("(BROKEN) " + lyr.name)
        else:
            print("  " + lyr.name)

        if lyr.name != 'Topographic':
            arcpy.mp.CreateWebLayerSDDraft(lyr, 'M:/Development/Travel Model Two/Supply/Transit/Network_QA/Cube_to_shapefile/' + lyr.name + '.sddraft', lyr.name, 'MY_HOSTED_SERVICES', 'FEATURE_ACCESS')
            arcpy.StageService_server('M:/Development/Travel Model Two/Supply/Transit/Network_QA/Cube_to_shapefile/' + lyr.name + '.sddraft', 'M:/Development/Travel Model Two/Supply/Transit/Network_QA/Cube_to_shapefile/' + lyr.name + '.sd')
            arcpy.UploadServiceDefinition_server('M:/Development/Travel Model Two/Supply/Transit/Network_QA/Cube_to_shapefile/' + lyr.name + '.sd', 'My Hosted Services')



# The process is not fully automated yet. 
# The script works if you run it for the first time. It'll take you to the point which 15 web layers will be created in your "my content" on ArcGIS online. You'll still need to create a web map and add all the layers to it.
# The intent is that in future updates you just need to overwrite the layers and not have to redo the web map.
# But currently the script has problems with overwriting the service definition (the line with "arcpy.UploadServiceDefinition_server")
# As a work around for now, I'll need to remove the web layers on ArcGIS online manually, and the recreate the web map. 
# URL for the web map: https://arcg.is/uLPeT
