# DefineProjection example (Python window)

import arcpy

# the roadway network should be available on Box
# e.g. C:\Users\ftsang\Box\Modeling and Surveys\Development\Travel Model Two Development\Model Inputs\2015\hwy

infc = r"C:\Users\ftsang\Documents\ArcGIS\projects\TM2_network\mtc_final_network_base.shp"

# Shapefiles are projected in "1983 State Plane California VI US Feet" according to the document "Travel Model Two: Initial Representation of Space"
# See: C:\Users\ftsang\Box\Modeling and Surveys\Development\Travel Model Two Development\Documentation\2013_01_17_RELEASE_Initial_Representation_of_Space.pdf
# Note that in ArcGIS the projection is spelt in a different way from the document (as below)

sr = arcpy.SpatialReference("NAD 1983 StatePlane California VI FIPS 0406 (US Feet)")

arcpy.DefineProjection_management(infc, sr)
