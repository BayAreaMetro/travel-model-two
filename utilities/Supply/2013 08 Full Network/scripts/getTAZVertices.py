
#Output TAZ Vertices for Building Connectors
#Requires ArcInfo license to use the simplify polygon tool
#Ben Stabler, stabler@pbworld.com, 02/01/13
#"C:\Python26\ArcGIS10.0\python.exe" getTAZVertices.py

# libraries
import arcpy
import os
import sys
import math

#parameters
outFileName = "TAZVertices.csv"
arcpy.env.workspace = "C:/projects/mtc/networks/MAZs/TAZ"
counties = ["Sonoma","Solano","SantaClara","SanMateo","SanFrancisco","Napa","Marin","ContraCosta","Alameda"]
simplify = False

#check for ArcInfo for simplify line tool
if simplify:
  if arcpy.CheckProduct("ArcInfo") != "Available":
    print "ArcInfo license not available"
    sys.exit("ArcInfo license not available")

#open file
f = file(outFileName,"wt")
f.write("COUNTY,TAZ,X,Y\n")

#get taz vertices for each county
for county in counties:
  
  #get taz shapefile
  print "Processing " + county
  tazs = county + "TAZ.shp"
  if simplify:
    tazsSimpleName = tazs.replace(".shp","Simple.shp")
    #simplify polygon
    arcpy.cartography.SimplifyPolygon(tazs, tazsSimpleName, "POINT_REMOVE", 25, 0, "NO_CHECK", "NO_KEEP") #25ft
  
  #loop through records
  if simplify:
    rows = arcpy.SearchCursor(tazsSimpleName)
  else:
    rows = arcpy.SearchCursor(tazs)
  for row in rows:
    
    # Create the geometry object and geature feature id
    feat = row.getValue(arcpy.Describe(tazs).ShapeFieldName)
    tazLabel = row.getValue("TAZ")
    
    # Step through each part of the feature
    partnum = 0
    for part in feat:
        
        # Step through each vertex in the feature
        for pnt in feat.getPart(partnum):
            if pnt:
                # Print x,y coordinates of current point
                f.write(county + "," + str(tazLabel) + "," + str(pnt.X)  + "," + str(pnt.Y) + "\n")
        partnum += 1

  #delete simple polygon
  if simplify:
    arcpy.Delete_management(tazsSimpleName)

#close file
f.close()

