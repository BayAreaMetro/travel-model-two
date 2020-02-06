# mergeCentroids.py
#
# Merges all of the MAZ and TAZ centroids into a new shapefile and re-number
# the nodes, conforming to county offset and MAZ/TAZ offset. The first 10,000 IDs
# in each county are reserved for TAZs, and the next 90,000 for MAZs and TAPs.
#
# Each input shape file must have a county field indicating the county ID. The single 
# merged shapefile is then used as input for Cube to merge into the network.

import arcpy
import os

# county IDs:
# 1 - Alameda
# 2 - Contra Costa
# 3 - Marin
# 4 - Napa
# 5 - San Francisco
# 6 - San Mateo
# 7 - Santa Clara
# 8 - Solano
# 9 - Sonoma

MAZ_SHAPEFILE_PATH   = "\\\\w-ampdx-d-tfs05\d_projects\\MTC\\networks\\MAZs\\MAZCentroids"
TAZ_SHAPEFILE_PATH   = "\\\\w-ampdx-d-tfs05\d_projects\\MTC\\networks\\MAZs\\TAZCentroids"
OUT_SHAPEFILE_PATH   = "\\\\w-ampdx-d-tfs05\d_projects\\MTC\\networks\\networks data\\Shapefiles"
MAZ_OFFSET           = 10000
COUNTY_OFFSET        = 100000
TARGET_FC_NAME = "maz_taz_centroids.shp"
TARGET_FC_PATH = OUT_SHAPEFILE_PATH + os.sep + TARGET_FC_NAME


def workOnFc(fc, zoneType, calculation):
    fieldsList = [f.name for f in arcpy.Describe(fc).fields]
    if ("COUNTY" not in fieldsList):
        raise Exception("Feature class {0} missing field 'COUNTY'".format(fc))
    if (zoneType not in fieldsList):
        raise Exception("Feature class {0} missing field '{1}'".format(fc, zoneType))
    if ("N" in fieldsList):
        arcpy.DeleteField_management(fc, "N")
    arcpy.AddField_management(in_table = fc, field_name = "N", field_type = "LONG")
    arcpy.CalculateField_management(fc, "N", calculation, "PYTHON")
    

def main():
    arcpy.env.workspace = MAZ_SHAPEFILE_PATH
    featureClasses = arcpy.ListFeatureClasses()    
    if (os.path.exists(TARGET_FC_PATH)):
        arcpy.Delete_management(TARGET_FC_PATH)
        print "    Deleted existing merge feature class " + TARGET_FC_NAME
    
    # Create the target feature class. Use an MAZ shapefile as the template schema.
    arcpy.CreateFeatureclass_management(out_path = OUT_SHAPEFILE_PATH,
                                        out_name = TARGET_FC_NAME,
                                        template = MAZ_SHAPEFILE_PATH + os.sep + featureClasses[0],
                                        spatial_reference = MAZ_SHAPEFILE_PATH + os.sep + featureClasses[0])
    # delete the MAZ field from the target
    arcpy.DeleteField_management(TARGET_FC_PATH, "MAZ")    
    # add the renumbered zone field, N
    arcpy.AddField_management(in_table = TARGET_FC_PATH, field_name = "N", field_type = "LONG")
    print "    Created merge feature class " + TARGET_FC_NAME
        
    #loop through all MAZ FCs, add N field, and set it
    for fc in featureClasses:
        workOnFc(fc, "MAZ",
                 "!MAZ! + (!COUNTY! - 1) * " + str(COUNTY_OFFSET) + " + " + str(MAZ_OFFSET))
        # fieldsList = [f.name for f in arcpy.Describe(fc).fields]
        # if ("COUNTY" not in fieldsList):
            # raise Exception("Feature class {0} missing field 'COUNTY'".format(fc))
        # if ("MAZ" not in fieldsList):
            # raise Exception("Feature class {0} missing field 'MAZ'".format(fc))
        # if ("N" in fieldsList):
          # arcpy.DeleteField_management(fc, "N")
        # arcpy.AddField_management(in_table = fc, field_name = "N", field_type = "LONG")
        # arcpy.CalculateField_management(fc, "N",
                                        # "!MAZ! + (!COUNTY! - 1) * " + str(COUNTY_OFFSET) + " + " + str(MAZ_OFFSET),
                                        # "PYTHON")
    print "    Beginning MAZ Merge"
    arcpy.Append_management(featureClasses, TARGET_FC_PATH, "NO_TEST")
    mazCount = int(arcpy.GetCount_management(TARGET_FC_PATH).getOutput(0))
    print "         finished MAZ Merge"
    print "         merged " + str(mazCount) + " MAZs"
    
    # now merge in all the TAZs
    arcpy.env.workspace = TAZ_SHAPEFILE_PATH
    featureClasses = arcpy.ListFeatureClasses()
    print "found {0} TAZ centroids in {1}".format(len(featureClasses), TAZ_SHAPEFILE_PATH)
    for fc in featureClasses:
        workOnFc(fc, "TAZ",
                 "!TAZ! + (!COUNTY! - 1) * " + str(COUNTY_OFFSET))
        # fieldsList = [f.name for f in arcpy.Describe(fc).fields]
        # if ("COUNTY" not in fieldsList):
            # raise Exception("Feature class {0} missing field 'COUNTY'".format(fc))
        # if ("TAZ" not in fieldsList):
            # raise Exception("Feature class {0} missing field 'TAZ'".format(fc))
        # if ("N" in fieldsList):
          # arcpy.DeleteField_management(fc, "N")
        # arcpy.AddField_management(in_table = fc, field_name = "N", field_type = "LONG")
        # arcpy.CalculateField_management(fc, "N", "!TAZ! + (!COUNTY! - 1) * " + str(COUNTY_OFFSET),
                                        # "PYTHON")
    if (len(featureClasses) > 0):
        print "    Beginning TAZ Merge"
        arcpy.Append_management(featureClasses, TARGET_FC_PATH, "NO_TEST")
        tazCount = int(arcpy.GetCount_management(TARGET_FC_PATH).getOutput(0))
        print "         finished TAZ Merge"
        print "         merged " + str(tazCount - mazCount) + " TAZs"
    print "Merged shapefile written to " + TARGET_FC_PATH
    
if __name__ == '__main__':
    main()