
#Get elevation (Z coordinate) for a node X,Y from USGS
#"C:\Python26\ArcGIS10.0\python.exe" updateElevations.py
#Chris Frazier, frazierc@pbworld.com, 05/22/13
#Ben Stabler, stabler@pbworld.com, 05/22/13

############################################################

NODES_SHPFILENAME = 'tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_bike.shp'
OUTPUT_FILENAME = 'nodeElevations.csv'

############################################################

import httplib,os,time
import xml.etree.ElementTree as et
import arcpy

def getElevation(xy_coord):
    host = 'gisdata.usgs.net'
    requestString = '/xmlwebservices2/elevation_service.asmx/getElevation?X_Value=%s&Y_Value=%s&Elevation_Units=feet&Source_Layer=Topobathy_California&Elevation_Only=true'

    h = httplib.HTTPConnection(host)
    headers = {'Host' : host}
    h.request('GET',requestString % xy_coord,headers=headers)
    r = h.getresponse()
    d = r.read()
    return float(et.fromstring(d).text)

def getElevations():
    
    #project nodes to lat/long
    llFileName = NODES_SHPFILENAME.replace(".shp","_latlong.shp")
    coordFileString = "Coordinate Systems/Geographic Coordinate Systems/World/WGS 1984.prj"
    prjFile = os.path.join(arcpy.GetInstallInfo()["InstallDir"],coordFileString)
    arcpy.Project_management(NODES_SHPFILENAME, llFileName, prjFile, "NAD_1983_To_WGS_1984_1")
    
    #create output file
    outFile = open(OUTPUT_FILENAME, "wb")
    
    #loop through the nodes
    lines = []
    rows = arcpy.SearchCursor(llFileName)
    for row in rows:
        n = row.getValue("N")
        feat = row.getValue(arcpy.Describe(llFileName).ShapeFieldName)
        x = feat.getPart().X #long
        y = feat.getPart().Y #lat
        z = int(getElevation((x,y))) #feet
        recLine = '%s,%s,%s,%s' % (n,x,y,z)
        lines.append(recLine + os.linesep)        
        print recLine

    #write lines
    outFile.writelines(lines)
    outFile.close()
    
    #remove temp lat/long file
    arcpy.Delete_management(llFileName)

#run elevation process
getElevations()
