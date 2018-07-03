"""
add_bike_links.py
Adds the new (non-street) bike links to the street network, snapping bike link
endpoints to street endpoints if they are within a given buffer.
"""

import os,math
import arcpy
import rtree

SOURCE_NETWORK_SHAPEFILE = 'tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split_bikesub.shp'
ADDITIONAL_BIKE_LINKS_SHAPEFILE = 'D:/Projects/MTC/networks/bike/missing_trail_links.shp'
LINK_OUTPUT = 'missing_bike_trail_links.csv'
NODE_OUTPUT = 'missing_bike_trail_nodes.csv'

SNAP_DIST_FEET = 50
VALID_LINKS_QUERY = "(CNTYPE = 'PED') OR (RAMP = 0 AND FRC > 2)"
BIKE_FIELDS = ['B_CLASS','REPRIORITIZE','GRADE_CAT','PED_FLAG','FEET','NAME']
EXISTING_BIKE_FIELDS = ['B_CLASS','REPRIORITI','GRADE_CAT','PED_FLAG','Shape_Leng','NAME']

WORKING_GDB = 'temp.gdb'

def getLargestNodeNumber():
    """
    Get the highest node number in the current network.
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    arcpy.Statistics_analysis(SOURCE_NETWORK_SHAPEFILE,'node_number_stats',[['A','MAX'],['B','MAX']],'')
    rows = arcpy.SearchCursor('node_number_stats')
    for row in rows: #only one row
        max_node = max(row.MAX_A,row.MAX_B)
    return max_node
    
def getDistance(point1,point2):
    """
    Get the Euclidean distance between two points.
    """
    return math.sqrt(((point1[0] - point2[0])**2) + ((point1[1] - point2[1])**2))

def getBikeLinkData():
    """
    Collect the bike link information.
    Returns a mapping: ((fx,fy),(tx,ty)) -> [bike data]
    """
    bike_links = {}
    desc = arcpy.Describe(ADDITIONAL_BIKE_LINKS_SHAPEFILE)
    shape_field = desc.ShapeFieldName
    rows = arcpy.SearchCursor(ADDITIONAL_BIKE_LINKS_SHAPEFILE)
    for row in rows:
        feat = row.getValue(shape_field)
        key = ((feat.firstPoint.X,feat.firstPoint.Y),(feat.lastPoint.X,feat.lastPoint.Y))
        data = []
        for field in EXISTING_BIKE_FIELDS:
            data.append(row.getValue(field))
        bike_links[key] = data
    return bike_links

def buildNodeIndex():
    """
    Build a spatial index for the street network endpoint nodes.
    """
    node_index = rtree.index.Index()
    
    desc = arcpy.Describe(SOURCE_NETWORK_SHAPEFILE)
    shape_field = desc.ShapeFieldName
    rows = arcpy.SearchCursor(SOURCE_NETWORK_SHAPEFILE,VALID_LINKS_QUERY)
    node_xy = {}
    for row in rows:
        a = row.getValue('A')
        b = row.getValue('B')
        feat = row.getValue(shape_field)
        if not a in node_xy:
            x = feat.firstPoint.X
            y = feat.firstPoint.Y
            node_index.insert(a,(x,y,x,y))
            node_xy[a] = (x,y)
        if not b in node_xy:
            x = feat.lastPoint.X
            y = feat.lastPoint.Y
            node_index.insert(b,(x,y,x,y))
            node_xy[b] = (x,y)
    return (node_index,node_xy)

def snapBikeLinksToNodes(bike_links,node_index,node_xy,node_number_start):
    """
    Snap new bike link endpoints to street nodes, if they're within the specified buffer.
    If a node is not snapped, assign it a new number and save that node's location
    information.
    """
    node_number = node_number_start
    new_bike_links = {}
    new_nodes = {}
    for key in bike_links:
        a = key[0]
        b = key[1]
        nearest_node = list(node_index.nearest((a[0],a[1],a[0],a[1]),1))[0]
        if getDistance(a,node_xy[nearest_node]) < SNAP_DIST_FEET:
            a = nearest_node
        else:
            new_nodes[node_number] = a
            a = node_number
            node_number += 1
        nearest_node = list(node_index.nearest((b[0],b[1],b[0],b[1]),1))[0]
        if getDistance(b,node_xy[nearest_node]) < SNAP_DIST_FEET:
            b = nearest_node
        else:
            new_nodes[node_number] = b
            b = node_number
            node_number += 1
        new_bike_links[(a,b)] = bike_links[key]
    return (new_bike_links,new_nodes)
    
    
def writeBikeLinkAdditions(bike_links,new_nodes,link_output,node_output):
    """
    Write the bike street network additions. This includes both link and node additions.
    """
    with open(link_output,'wb') as f:
        header = ['A','B','CNTYPE'] + BIKE_FIELDS
        f.write(','.join(header) + os.linesep)
        for bike_link in bike_links:
            data = [bike_link[0],bike_link[1],'BIKE'] + bike_links[bike_link]
            f.write(','.join(map(str,data)) + os.linesep)
            
    with open(node_output,'wb') as f:
        header = ['N','A','B']
        f.write(','.join(header) + os.linesep)
        for node in new_nodes:
            xy = new_nodes[node]
            data = [node,xy[0],xy[1]]
            f.write(','.join(map(str,data)) + os.linesep)
    
print 'Collecting new bike link data'
bike_links = getBikeLinkData()
print 'Building network node index'
(node_index,node_xy) = buildNodeIndex()
print 'Getting node start number'
node_number_start = getLargestNodeNumber() + 1
print 'Snapping bike link endpoints to street nodes'
(bike_links,new_nodes) = snapBikeLinksToNodes(bike_links,node_index,node_xy,node_number_start)
print 'Writing new link and node data'
writeBikeLinkAdditions(bike_links,new_nodes,LINK_OUTPUT,NODE_OUTPUT)

