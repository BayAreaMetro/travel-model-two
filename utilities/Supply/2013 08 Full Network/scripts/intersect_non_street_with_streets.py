"""
intersect_non_street_with_streets.py
Determines the intersection points between the non-street and street networks and
splits the links at those points.
"""

import os,math
from operator import itemgetter
import arcpy

NETWORK_SHAPEFILE = 'tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split_bikesub2.shp'
LINK_OUT_FILE = 'D:/Projects/MTC/networks/bike/link_split_bike.csv'
LINK_DELETE_FILE = 'D:/Projects/MTC/networks/bike/link_delete_bike.csv'
POINT_OUT_FILE = 'D:/Projects/MTC/networks/bike/new_nodes_bike.csv'
BUFFER_DISTANCE = 50
STREET_SELECTION_QUERY = "(RAMP = 0 AND FRC > 2 AND CNTYPE <> 'TAZ' AND CNTYPE <> 'MAZ' AND CNTYPE <> 'TAP') OR (CNTYPE <> 'PED' )"

WORKING_GDB = 'temp.gdb'
NON_STREET_LAYER = 'non_streets'
STREET_LAYER = 'street'
STREET_INTERSECT_LAYER = 'street_intersect'
NON_STREET_SELECTION_QUERY = "CNTYPE = 'BIKE'"

def createWorkingGdb():
    """
    Create the temporary working geodatabase. If it already exists, delete it first.
    """
    deleteWorkingGdb()
    path = os.path.split(WORKING_GDB)
    arcpy.CreateFileGDB_management('.',path[1])

def deleteWorkingGdb():
    """
    Delete the temporary working geodatabase.
    """
    if os.path.exists(WORKING_GDB):
        arcpy.Delete_management(WORKING_GDB)

def getLargestNodeNumber():
    """
    Get the highest node number in the current network.
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    arcpy.Statistics_analysis(NETWORK_SHAPEFILE,'node_number_stats',[['A','MAX'],['B','MAX']],'')
    rows = arcpy.SearchCursor('node_number_stats')
    for row in rows: #only one row
        max_node = max(row.MAX_A,row.MAX_B)
    return max_node

def createIntersectionLayers():
    """
    Create street and non-street only layers.
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    arcpy.MakeFeatureLayer_management(NETWORK_SHAPEFILE,NON_STREET_LAYER,NON_STREET_SELECTION_QUERY)
    arcpy.MakeFeatureLayer_management(NETWORK_SHAPEFILE,STREET_LAYER,STREET_SELECTION_QUERY)

def intersectNonStreetWithStreets():
    """
    Intersect each non-street link with the streets layer and get list of intersecting streets for each.
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    #first intersect all non-street with all highway to get a smaller set to intersect
    arcpy.SelectLayerByLocation_management(STREET_LAYER,'INTERSECT',NON_STREET_LAYER)
    intersecting_streets = 'intersecting_streets'
    #arcpy.CopyFeatures_management(STREET_LAYER,intersecting_streets)
    arcpy.MakeFeatureLayer_management(STREET_LAYER,intersecting_streets)
    arcpy.SelectLayerByAttribute_management(STREET_LAYER,'CLEAR_SELECTION')
    print 'intersecting streets: ' + str(arcpy.GetCount_management(intersecting_streets).getOutput(0))
    
    arcpy.SelectLayerByLocation_management(NON_STREET_LAYER,'INTERSECT',STREET_LAYER)
    intersecting_non_streets = 'intersecting_non_streets'
    arcpy.MakeFeatureLayer_management(NON_STREET_LAYER,intersecting_non_streets)
    arcpy.SelectLayerByAttribute_management(NON_STREET_LAYER,'CLEAR_SELECTION')
    print 'intersecting non-streets: ' + str(arcpy.GetCount_management(intersecting_non_streets).getOutput(0))
    
    arcpy.SpatialJoin_analysis(intersecting_non_streets,intersecting_streets,STREET_INTERSECT_LAYER + '_fc','JOIN_ONE_TO_MANY','','','CROSSED_BY_THE_OUTLINE_OF')
    arcpy.MakeFeatureLayer_management(STREET_INTERSECT_LAYER + '_fc',STREET_INTERSECT_LAYER)
    arcpy.SelectLayerByAttribute_management(STREET_INTERSECT_LAYER,'','Join_Count > 0')
    
    non_street_to_streets = {}
    rows = arcpy.SearchCursor(STREET_INTERSECT_LAYER)
    for row in rows:
        key = (row.A,row.B)
        if not key in non_street_to_streets:
            non_street_to_streets[key] = {}
        key2 = (row.A_1,row.B_1)
        non_street_to_streets[key][key2] = None
    
    del row
    del rows
    print 'update non-streets: ' + str(len(non_street_to_streets))
    
    return non_street_to_streets
    
def getCoordinatesFromLineLayer(desired_abs,layer,coordinates_container):
    """
    Get all of the node xy positions for links in the A/B node list (desired_abs).
    """
    desc = arcpy.Describe(layer)
    shape_field = desc.ShapeFieldName
    rows = arcpy.SearchCursor(layer)
    for row in rows:
        key = (row.A,row.B)
        if key in desired_abs:
            p = row.A
            if not p in coordinates_container:
                feat = row.getValue(shape_field)
                coordinates_container[p] = (feat.firstPoint.X,feat.firstPoint.Y)
            p = row.B
            if not p in coordinates_container:
                feat = row.getValue(shape_field)
                coordinates_container[p] = (feat.lastPoint.X,feat.lastPoint.Y)
    
def getCoordinates(non_street_to_streets):
    """
    Get the coordinates for all of the endpoints defining the non-street/street links in non_street_to_streets map.
    """
    coordinates = {}
    #first non-streets
    getCoordinatesFromLineLayer(non_street_to_streets,NON_STREET_LAYER,coordinates)
    #now streets
    #first collect all streets
    streets = {}
    for non_street in non_street_to_streets:
        for street in non_street_to_streets[non_street]:
            if not street in streets:
                streets[street] = None
    getCoordinatesFromLineLayer(streets,STREET_LAYER,coordinates)
    return coordinates
    
def getIntersectionPoint(non_street_point,street_point,coordinates):
    """
    Get the intersection point of two lines (defined by non_street_point and street point as (start_point,end_point)).
    """
    (x1,y1) = coordinates[non_street_point[0]]
    (x2,y2) = coordinates[non_street_point[1]]
    (x3,y3) = coordinates[street_point[0]]
    (x4,y4) = coordinates[street_point[1]]
    den = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
    n1 = (x1*y2 - y1*x2)
    n2 = (x3*y4 - y3*x4)
    px = (n1*(x3 - x4) - n2*(x1 - x2)) / den
    py = (n1*(y3 - y4) - n2*(y1 - y2)) / den
    return (px,py)
    
def buildNonStreetStreetSplits(non_street_to_streets,coordinates):
    """
    Build the locations for the new split points, and the links that they pertain to.
    """
    splits = {}
    new_points = {}
    finished_links = {}
    counter = 1
    
    for non_street in non_street_to_streets:
        if not non_street in splits:
            splits[non_street] = {}
    
        rnon_street = (non_street[1],non_street[0])
        if rnon_street in finished_links:
            flinks = finished_links[rnon_street]
        else:
            if not non_street in finished_links:
                finished_links[non_street] = {}
            flinks = finished_links[non_street]
            
        for street in non_street_to_streets[non_street]:
            if not street in splits:
                splits[street] = {}
            rstreet = (street[1],street[0])
            if rstreet in flinks:
                point = flinks[rstreet]
            else:
                if street in flinks:
                    point = flinks[street]
                else:
                    new_points[counter] = getIntersectionPoint(non_street,street,coordinates)
                    point = counter
                    flinks[street] = point
                    counter += 1
            
            if not point in splits[non_street]:
                splits[non_street][point] = None
            if not point in splits[street]:
                splits[street][point] = None
    
    return (splits,new_points)
    
def getDistance(point1,point2):
    """
    Get the Euclidean distance between two points.
    """
    return math.sqrt(((point1[0] - point2[0])**2) + ((point1[1] - point2[1])**2))
    
def cleanPoints(points,collapse_buffer,starting_node_number):
    """
    Clean the new nodes by collapsing all of those that are within collapse_buffer.
    Also, renumber the nodes to valid (unused) node numbers for network.
    """
    
    points_mapping = {}
    points_to_collapse = {}
    keys = []
    for point in points:
        keys.append((point,points[point][0],points[point][1]))
    sorted(keys,key=itemgetter(1,2))
    point1 = None
    last_key = None
    for key in keys:
        point2 = points[key[0]]
        if not point1 is None:
            distance = getDistance(point1,point2)
            if distance < collapse_buffer:
                points_to_collapse[key[0]] = last_key[0]
        point1 = point2
        last_key = key
    
    final_point_set = {}
    for point in points:
        map_point = point
        while map_point in points_to_collapse:
            map_point = points_to_collapse[map_point]
        points_mapping[point] = map_point
        final_point_set[map_point] = None
    
    new_points = {}
    new_point_mapping = {}
    node_number = starting_node_number
    for point in points:
        if point in final_point_set:
            new_points[node_number] = points[point]
            new_point_mapping[point] = node_number
            node_number += 1
    for point in points_mapping:
        points_mapping[point] = new_point_mapping[points_mapping[point]]
    print 'collapsed ' + str(len(points)) + ' to ' + str(len(new_points))
    return (new_points,points_mapping)
    
def remapPoints(points_mapping,splits):
    """
    Remap the link split points to the new (collapsed) points.
    """
    original_count = 0
    new_count = 0
    keys = list(splits.keys())
    for s in keys:
        split = splits[s]
        original_count += len(split)
        nsplit = {}
        for key in split:
            nsplit[points_mapping[key]] = None
        splits[s] = nsplit
        new_count += len(nsplit)
    print 'original split count ' + str(original_count) + ' reduced to ' + str(new_count)
    
def orderPoints(splits,points,coordinates):
    """
    Order the split points so that they are in increasing distance order from from node.
    """
    for s in list(splits.keys()):
        pts = []
        for point in splits[s]:
            pts.append((point,points[point][0]))
        x1 = coordinates[s[0]][0]
        x2 = coordinates[s[1]][0]
        sorted(pts,key=itemgetter(1),reverse=(x1 > x2)) #sort by x, reverse if from node is bigger (in x) than to node
        final_pts = []
        for pt in pts:
            final_pts.append(pt[0])
        splits[s] = final_pts
        
def writeOutLinkResultsForLayer(layer,data_fields,splits,points,f,coordinates):
    """
    Write the link split data for a specific layer. This can be used by any layer and will write to a file handle (f).
    """
    finished_abs = {}
    rows = arcpy.SearchCursor(layer)
    for row in rows:
        ab = (row.A,row.B)
        if ab in splits:
            split_points = splits[ab]
            last_point = ab[0]
            for split_point in split_points:
                key = (last_point,split_point)
                if key in finished_abs:
                    last_point = split_point
                    continue
                else:
                    finished_abs[key] = None
                data = []
                for field in data_fields:
                    if field == 'A':
                        data.append(last_point)
                    elif field == 'B':
                        data.append(split_point)
                    elif field == 'FEET':
                        if last_point == ab[0]:
                            data.append(getDistance(points[split_point],coordinates[ab[0]]))
                        else:
                            data.append(getDistance(points[split_point],points[last_point]))
                    else:
                        data.append(row.getValue(field))
                last_point = split_point
                f.write(','.join(map(str,data)) + os.linesep)
            
            key = (last_point,ab[1])
            if not key in finished_abs:
                data = []
                for field in data_fields:
                    if field == 'A':
                        data.append(last_point)
                    elif field == 'B':
                        data.append(ab[1])
                    elif field == 'FEET':
                        data.append(getDistance(points[last_point],coordinates[ab[1]]))
                    else:
                        data.append(row.getValue(field))
                last_point = split_point
                f.write(','.join(map(str,data)) + os.linesep)
        
def writeOutResults(link_file,delete_link_file,point_file,splits,new_points,coordinates):
    """
    Write out a link and node files that can be read into Cube.
    """
    arcpy.env.workspace = WORKING_GDB
    
    f = open(link_file,'wb')
    fields = arcpy.ListFields(NON_STREET_LAYER)
    desc = arcpy.Describe(NON_STREET_LAYER)
    oid_field = desc.OIDFieldName
    shape_field = desc.shapeFieldName
    data_fields = []
    for field in fields:
        fname = field.name
        if fname != oid_field and fname != shape_field:
            data_fields.append(fname)
    f.write(','.join(data_fields) + os.linesep)
    writeOutLinkResultsForLayer(NON_STREET_LAYER,data_fields,splits,new_points,f,coordinates)
    writeOutLinkResultsForLayer(STREET_LAYER,data_fields,splits,new_points,f,coordinates)
    f.close()
    
    f = open(delete_link_file,'wb')
    f.write('a,b,cntype' + os.linesep)
    for split in splits:
        f.write(','.join([str(split[0]),str(split[1]),'DELETE']) + os.linesep)
    f.close()
    
    f = open(point_file,'wb')
    f.write('point,x,y' + os.linesep)
    for point in new_points:
        (x,y) = new_points[point]
        f.write(','.join([str(point),str(x),str(y)]) + os.linesep)
    f.close()
    
    

def readResultsIntoGeodatabase(link_file,point_file):
    """
    Read the split results into a geodatabase, for analysis.
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    
    spatial_reference = spatialRef = arcpy.Describe(NETWORK_SHAPEFILE).spatialReference
    
    points_table = 'new_points_table'
    points_layer = 'new_points'
    arcpy.TableToTable_conversion (point_file,WORKING_GDB,points_table)
    arcpy.MakeXYEventLayer_management (points_table,'x','y',points_layer + '_layer',spatial_reference)
    arcpy.FeatureClassToFeatureClass_conversion (points_layer + '_layer',WORKING_GDB,points_layer)

def cleanLinkFile(link_file):
    fout = link_file + '.tmp'
    f = open(fout,'wb')
    
    string_cols = [5,7,8,11,17,24,28]
    first = True
    for line in open(link_file):
        if first:
            first = False
            f.write(line.strip() + os.linesep)
            continue
        line = line.strip().split(',')
        for col in string_cols:  
            column = line[col]
            if len(column) == 0 or column[0] != "'":
                if line[col].find("'") > -1:
                    line[col] = '"' + line[col].strip() + '"'
                else:
                    line[col] = "'" + line[col].strip() + "'"
        f.write(','.join(line) + os.linesep)
    f.close()
    os.remove(link_file)
    os.rename(fout,link_file)
   
     
#print 'creating temporary workspace'
createWorkingGdb()
print 'creating intersection layers'
createIntersectionLayers()
print 'intersection non-street links with streets'
non_street_to_streets = intersectNonStreetWithStreets()
print 'getting endpoint coordinates'
coordinates = getCoordinates(non_street_to_streets)
print 'building network split points'
(splits,new_points) = buildNonStreetStreetSplits(non_street_to_streets,coordinates)
print 'determining node number start point'
largest_node_number = getLargestNodeNumber()
print '    (' + str(largest_node_number) + ")"
print 'collapsing new points to ' + str(BUFFER_DISTANCE) + ' ft'
(new_points,points_mapping) = cleanPoints(new_points,BUFFER_DISTANCE,largest_node_number+1)
print 'remapping points'
remapPoints(points_mapping,splits)
print 'ordering split points'
orderPoints(splits,new_points,coordinates)
print 'writing out results'
writeOutResults(LINK_OUT_FILE,LINK_DELETE_FILE,POINT_OUT_FILE,splits,new_points,coordinates)
cleanLinkFile(LINK_OUT_FILE)
#print 'reading results into geodatabase'
#readResultsIntoGeodatabase(link_file,point_file)
