import arcpy
import pandas

print("Step 0:   Processing " + input_file_name + " ...")

# overwrite existing files
arcpy.env.overwriteOutput = True

# Travel Model Two Steps
working_directory    = workspace
input_csv_file       = working_directory + "\\" + input_file_name
spatial_ref          = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]"

print("Step 1:   Geo-coding to Travel Model Two Geographies ...")
xy_event_layer_name  = "EventLyr"
xy_event_feature     = working_directory + tm2_geodatabase + "\\" + xy_event_layer_name

spatial_join_name    = "SpatialJoin_Lyr"
spatial_join_feature = working_directory + tm2_geodatabase + "\\" + spatial_join_name
maz_feature          = working_directory + tm2_geodatabase + "\mazs"

csv_output_all      = working_directory + "gis_geocode.csv"
csv_output_custom   = working_directory + output_file_name

# create the xy event layer
arcpy.MakeXYEventLayer_management(input_csv_file, x_field, y_field, xy_event_layer_name, spatial_ref , "")
print("Step 1a:  XY event layer created ...")

# copy features
arcpy.CopyFeatures_management(xy_event_layer_name, xy_event_feature, "", "0", "0", "0")
print("Step 1b:  Copying features ...")

# spatial join
arcpy.SpatialJoin_analysis(xy_event_feature, maz_feature, spatial_join_feature, "JOIN_ONE_TO_ONE", "KEEP_ALL","" , "INTERSECT", "", "")
print("Step 1c:  Geo-coded points to MAZ and TAZ boundaries ...")

# write data out to a csv
field_names = [f.name for f in arcpy.ListFields(spatial_join_feature) if f.type != 'Geometry']
with open (csv_output_all,'w') as f:
    f.write(','.join(field_names)+'\n')
    with arcpy.da.SearchCursor(spatial_join_feature, field_names) as cursor:
        for row in cursor:
            f.write(','.join([("\"" + str(r) + "\"") for r in row])+'\n')
print("Step 1d:  Write to " + csv_output_all + " ...")

# read/write the information I need
data_frame = pandas.read_csv(csv_output_all)

for i, column in enumerate(data_frame.columns):
    if column not in keep_fields:
        del data_frame[column]

print("Step 1e:  Write to " + csv_output_custom + " ...")

data_frame.to_csv(csv_output_custom, header = True, index = False, float_format="%.7f")

print ("Finished:  OnBoardGeocoding for " + input_file_name + ".\n\n")