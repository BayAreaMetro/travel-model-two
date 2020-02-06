"""
This script contains methods used to build the MTC bicycle network.
The bicycle network is processed from the Bike Mapper network, which
is held in a geodatabase, and involves transferring Bike Mapper network 
attributes to the appropriate steet network links. The Bike Mapper and
street network may not  be from the same source (TANA) network, so the
transfer has to rely completely on geographic matching, not attribute
mapping.

On a broad level, this process involves determining what subset of steet
network links actually belong to the bicycle network (by selecting a
subset of valid street links and overlaying them with a buffer built
around the entire Bike Mapper network), and then connecting the correct
Bike Mapper data to each of these links (by overlaying each street
network link with buffers built around the Bike Mapper network and split
by attribute levels.

There are two "modes" in this script: The first determines which street
links are bicycle routes and attaches the pertinent bike data to them. The
other mode determines which network links (including both streets and pedestrian 
paths) contain bicycle "trail" routes. The former mode acts on the source
network shapefile because it retains the shapes of the links, which is needed
for correct mapping. The trails mode instead uses the combined street/pedestrian
network output from Cube, because it contains the pedestrian links (which have
enough shape information to be mapped).
"""

import os,math,csv
import arcpy
import numpy


############## INPUTS - CHANGE FOR SPECIFIC RUN #############
BIKE_GDB = 'D:/Projects/MTC/networks/DBs/BikeNetwork.gdb'
BIKE_LINKS_LAYER_ORIGINAL = 'Routes_v6'
BIKE_TRAILS_LAYER_ORIGINAL = 'Trails_v6'
HIGHWAY_LINKS_LAYER_FULL = 'D:/Projects/MTC/networks/networks data/shapefiles/ca_nw_Intersect_sp.shp'
HIGHWAY_LINKS_PED_LAYER_FULL = 'tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split.shp'
WORKING_DIR = 'D:/Projects/MTC/networks/bike'
SPLIT_STREETS_FILE = 'D:/Projects/MTC/networks/osm/link_split_ped.csv'
DELETE_LINK_FILE = 'D:/Projects/MTC/networks/osm/link_delete_ped.csv'
MISSING_BIKE_TRAIL_LINKS_LAYER = 'D:/Projects/MTC/networks/bike/missing_trail_links.shp'
#############################################################

TRAILS_MODE = False
def setBikeTrailsMode():
    global TRAILS_MODE
    TRAILS_MODE = True

#if this is true, then the temporary working geodatabase will be deleted at the end of the process
DELETE_WORKING_FILES = False

BIKE_LINKS_LAYER_FULL = 'BM_Route_Network_projected'
BIKE_LINKS_LAYER = 'Bike_Links_projected'
MISSING_BIKE_LINKS_LAYER = 'missing_bike_links'

WORKING_GDB = os.path.join(WORKING_DIR,'temp.gdb').replace('\\','/')
STREET_LINKS_LAYER_FULL = 'base_street_network'
STREET_LINKS_LAYER_BIKE_INTERSECT = 'street_network_bike_intersect'
STREET_BIKE_LINKS_LAYER = 'bike_street_network'

BIKE_LINKS_FULL_BUFFER = 'BM_Buffer'
BIKE_LINKS_SPLIT_BUFFER = 'BM_Buffer_Split'
SPLIT_BUFFER_FIELDS = ['B_CLASS','REPRIORITIZE','GRADE_CAT','PED_FLAG']
SPLIT_BUFFER_FIELDS_TRAIL = ['CNTYPE','B_CLASS','REPRIORITIZE','GRADE_CAT','PED_FLAG']
BIKE_STREET_LINKS_FULL_BUFFER = 'bike_street_network_buffer'

OUTPUT_FILE = os.path.join(WORKING_DIR,'bike_links.csv').replace('\\','/')
OUTPUT_FILE_TRAILS = os.path.join(WORKING_DIR,'bike_trail_links.csv').replace('\\','/')

#this query picks what street links are available for bike
#VALID_BIKE_LINKS_QUERY = 'RAMP = 0 AND FRC > 3'
VALID_BIKE_LINKS_QUERY = 'RAMP = 0 AND FRC > 2'
VALID_BIKE_TRAIL_LINKS_QUERY = "(CNTYPE = 'PED') OR (" + VALID_BIKE_LINKS_QUERY + ")"

#A_FIELD_ROADS = 'F_JNCTID_h'
#B_FIELD_ROADS = 'T_JNCTID_h'
A_FIELD_ROADS = 'A'
B_FIELD_ROADS = 'B'
A_FIELD_TRAILS = 'A'
B_FIELD_TRAILS = 'B'

#these values were decided on based on experience
buffer_in_feet = 50
PERCENT_OVERLAY_ACCEPT_CRITERION = 0.8


def createWorkingGdb():
    """
    Create the temporary working geodatabase. If it already exists, delete it first.
    """
    if os.path.exists(WORKING_GDB):
        arcpy.Delete_management(WORKING_GDB)
    path = os.path.split(WORKING_GDB)
    arcpy.CreateFileGDB_management(path[0],path[1])

def reprojectBikeLinks():
    """
    Reproject the Bike Mapper links to the same coordinate system as the street network.
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    outWorkspace = arcpy.env.workspace
    install_dir = arcpy.GetInstallInfo()['InstallDir']
    NAD_83_DIRECTORY = r'Coordinate Systems/Projected Coordinate Systems/State Plane/NAD 1983 (US Feet)/NAD 1983 StatePlane California VI FIPS 0406 (US Feet).prj'
    out_coordinate_system = os.path.join(install_dir, NAD_83_DIRECTORY)
    layer = BIKE_LINKS_LAYER_ORIGINAL
    if TRAILS_MODE:
        layer = BIKE_TRAILS_LAYER_ORIGINAL
    arcpy.Project_management(BIKE_GDB + '/' + layer,BIKE_LINKS_LAYER_FULL,out_coordinate_system,'NAD_1983_To_WGS_1984_5')
    
    
def removeHighwayLinksFromStreetNetwork():
    """
    Create a subset of street links that are valid for use by bicycles.
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    if TRAILS_MODE:
        arcpy.MakeFeatureLayer_management(HIGHWAY_LINKS_PED_LAYER_FULL,STREET_LINKS_LAYER_FULL,VALID_BIKE_TRAIL_LINKS_QUERY)
    else:
        arcpy.MakeFeatureLayer_management(HIGHWAY_LINKS_PED_LAYER_FULL,STREET_LINKS_LAYER_FULL,VALID_BIKE_LINKS_QUERY)
     
def buildFullBikeLinkBuffer(buffer_in_feet):
    """
    Build a buffer around the entire Bike Mapper network.
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    arcpy.Select_analysis(BIKE_LINKS_LAYER_FULL,BIKE_LINKS_LAYER,'B_CLASS>0')
    arcpy.Buffer_analysis(BIKE_LINKS_LAYER,BIKE_LINKS_FULL_BUFFER,str(buffer_in_feet) + ' Feet','','','ALL')

def intersectHighwayWithBikeLinks():
    """
    Intersect the street network with the bicycle network buffer, keeping those link parts that are within the buffer.
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    bike_links_buffer = BIKE_LINKS_FULL_BUFFER
    arcpy.Intersect_analysis([STREET_LINKS_LAYER_FULL,bike_links_buffer], STREET_LINKS_LAYER_BIKE_INTERSECT,'','','LINE')
    

def getHighwayAbLinksToKeep(cutoff_percentage):
    """
    Select the subset of street links with at least cutuff_percentage % of their length whithin the bike network buffer.
    Returns a set of a/b node tuples (in the form of a dict: (a_node,b_node) -> None)
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    rows = arcpy.SearchCursor(STREET_LINKS_LAYER_BIKE_INTERSECT)
    
    ab_to_length = {}
    for row in rows:
        if TRAILS_MODE:
            ab = (int(row.getValue(A_FIELD_TRAILS)),int(row.getValue(B_FIELD_TRAILS)))
        else:
            ab = (int(row.getValue(A_FIELD_ROADS)),int(row.getValue(B_FIELD_ROADS)))
        if not ab in ab_to_length:
            ab_to_length[ab] = 0.0
        ab_to_length[ab] += row.getValue('Shape_Length')
    
    abs_to_keep = {}
    desc = arcpy.Describe(STREET_LINKS_LAYER_FULL)
    shape_field = desc.ShapeFieldName
    rows = arcpy.SearchCursor(STREET_LINKS_LAYER_FULL)
    for row in rows:
        if TRAILS_MODE:
            ab = (int(row.getValue(A_FIELD_TRAILS)),int(row.getValue(B_FIELD_TRAILS)))
        else:
            ab = (int(row.getValue(A_FIELD_ROADS)),int(row.getValue(B_FIELD_ROADS)))
        if ab in ab_to_length:
            if TRAILS_MODE:
                feat = row.getValue(shape_field)
                base_length = getDistance((feat.firstPoint.X,feat.firstPoint.Y),(feat.lastPoint.X,feat.lastPoint.Y))
            else:
                #base_length = row.getValue('Shape_Leng')
                feat = row.getValue(shape_field)
                base_length = getDistance((feat.firstPoint.X,feat.firstPoint.Y),(feat.lastPoint.X,feat.lastPoint.Y))
            if ab_to_length[ab] / base_length >= cutoff_percentage:
                abs_to_keep[ab] = None
    print 'street links with bike attributes: ' + str(len(abs_to_keep))
    return abs_to_keep
    
def createBikeStreetNetwork(abs_to_keep):
    """
    Select out the street network links that have been identified as bike links.
    abs_to_keep is a set of a/b node tuples (in the form of a dict: (a_node,b_node) -> None)
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    temp_layer = 'temp_layer'
    arcpy.MakeFeatureLayer_management(STREET_LINKS_LAYER_FULL,temp_layer)
    id_field = arcpy.Describe(temp_layer).OIDFieldName
    rows = arcpy.SearchCursor(temp_layer)
    query = []
    for row in rows:
        if TRAILS_MODE:
            ab = (int(row.getValue(A_FIELD_TRAILS)),int(row.getValue(B_FIELD_TRAILS)))
        else:
            ab = (int(row.getValue(A_FIELD_ROADS)),int(row.getValue(B_FIELD_ROADS)))
        if ab in abs_to_keep:
            query.append(str(row.getValue(id_field)))
    query_string = id_field + ' IN' + str(tuple(map(int,query))).replace('L','')
    temp_layer2 = temp_layer + '2'
    arcpy.MakeFeatureLayer_management(temp_layer,temp_layer2,query_string)
    #have to copy because previous step only creates temporary layer
    arcpy.CopyFeatures_management(temp_layer2,STREET_BIKE_LINKS_LAYER)
     
def buildSplitBikeLinkBuffer(buffer_in_feet):
    """
    Build a buffer around the Bike Mapper network, where each shape (group) have a unique set of bicycle attributes.
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    arcpy.Select_analysis(BIKE_LINKS_LAYER_FULL,BIKE_LINKS_LAYER,'B_CLASS>0')
    # have to add ONEWAY so that we have access to this field when writing out the results
    #if TRAILS_MODE:
    #    arcpy.Buffer_analysis(BIKE_LINKS_LAYER,BIKE_LINKS_SPLIT_BUFFER,str(buffer_in_feet) + ' Feet','','','LIST',SPLIT_BUFFER_FIELDS_TRAIL + ['ONEWAY'])
    #else:
    arcpy.Buffer_analysis(BIKE_LINKS_LAYER,BIKE_LINKS_SPLIT_BUFFER,str(buffer_in_feet) + ' Feet','','','LIST',SPLIT_BUFFER_FIELDS + ['ONEWAY'])
    
    
def intersectBikeStreetNetworkWithSplitBuffer():
    """
    Intersect the street bike links with the Bike Mapper split buffers, and associate the Bike Mapper data with the street links.
    If a street link intersetcs more than one buffer, the buffer it most overlaps with is selected.
    Returns a dict mapping (a_node,b_node) tuples to a dict of Bike Mapper data (field_name -> value).
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    
    buffer_map = {} # street object id (A,B) -> {}  (buffer object id -> length in buffer)
    buffer_data_map = {} # buffer object id -> buffer data
    
    bike_links_buffer = BIKE_LINKS_SPLIT_BUFFER
    temp_layer_base = 'temp_layer_'
    id_field = arcpy.Describe(bike_links_buffer).OIDFieldName
    rows = arcpy.SearchCursor(bike_links_buffer)
    for row in rows:
        id = row.getValue(id_field)
        temp_layer = temp_layer_base + str(id)
        arcpy.MakeFeatureLayer_management(bike_links_buffer,temp_layer,id_field + ' = ' + str(id))
        intersect_layer = STREET_LINKS_LAYER_BIKE_INTERSECT + str(id)
        arcpy.Intersect_analysis([STREET_BIKE_LINKS_LAYER,temp_layer],intersect_layer,'','','LINE')
        
        intersect_rows = arcpy.SearchCursor(intersect_layer)
        for intersect_row in intersect_rows:
            if TRAILS_MODE:
                ab = (int(intersect_row.getValue(A_FIELD_TRAILS)),int(intersect_row.getValue(B_FIELD_TRAILS)))
            else:
                ab = (int(intersect_row.getValue(A_FIELD_ROADS)),int(intersect_row.getValue(B_FIELD_ROADS)))
            if not ab in buffer_map:
                buffer_map[ab] = {}
            bid_map = buffer_map[ab]
            if not id in bid_map:
                bid_map[id] = 0.0
            bid_map[id] += intersect_row.getValue('Shape_Length')
        arcpy.Delete_management(intersect_layer)
        
        bdm = {}
        if TRAILS_MODE:
            data_fields = SPLIT_BUFFER_FIELDS + ['ONEWAY']
        else:
            data_fields = SPLIT_BUFFER_FIELDS + ['ONEWAY']
        for field in data_fields:
            bdm[field] = row.getValue(field)
        buffer_data_map[id] = bdm
    
    #for some reason getting duplicate (a,b), but only happens rarely, so just noting it...
    bike_buffer_map = {} # street object id (A,B) -> buffer_data
    for ab in buffer_map:
        current_max = 0.0
        for bid in buffer_map[ab]:
            if buffer_map[ab][bid] > current_max:
                bike_buffer_map[ab] = buffer_data_map[bid]
                current_max = buffer_map[ab][bid]
                
    return bike_buffer_map
    
def writeBikeLinkUpdates(bike_buffer_map,output_file,street_splits):
    """
    Write the bike street network result data. Essentially puts out a csv file with a/b node columns,
    and then all of the (appropriate) Bike Mapper attribute data.
    """
    if TRAILS_MODE:
        header = ['A','B'] + SPLIT_BUFFER_FIELDS + ['REV']
    else:
        header = ['A','B'] + SPLIT_BUFFER_FIELDS
    with open(output_file,'wb') as f:
        writer = csv.DictWriter(f,header)
        writer.writer.writerow(writer.fieldnames)
        for ab in bike_buffer_map:
            abdir = 0
            oneway = bike_buffer_map[ab]['ONEWAY']
            if oneway == 'FT':
                abdir = 1
            elif oneway == 'TF':
                abdir = -1
            row = {}
            row['A'] = ab[0]
            row['B'] = ab[1]
            for field in SPLIT_BUFFER_FIELDS:
                row[field] = bike_buffer_map[ab][field]
            writer.writerow(row)
            #if abdir > -1:
            #    if ab in street_splits:
            #        for ab_split in street_splits[ab]:
            #            row['A'] = ab_split[0]
            #            row['B'] = ab_split[1]
            #            writer.writerow(row)
            #    else:
            #        row['A'] = ab[0]
            #        row['B'] = ab[1]
            #        writer.writerow(row)
            #if abdir < 1:
            #    ba = (ab[1],ab[0])
            #    if ba in street_splits:
            #        for ba_split in street_splits[ba]:
            #            row['A'] = ba_split[0]
            #            row['B'] = ba_split[1]
            #            writer.writerow(row)
            #    else:
            #        row['A'] = ba[0]
            #        row['B'] = ba[1]
            #        writer.writerow(row)
    
def cleanup():
    """
    Clean up the working geodatabase.
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.Delete_management(BIKE_LINKS_FULL_BUFFER)
    arcpy.Delete_management(BIKE_LINKS_SPLIT_BUFFER)
    arcpy.Delete_management(BIKE_LINKS_LAYER_FULL)
    arcpy.Delete_management(BIKE_LINKS_LAYER)
    
    arcpy.env.workspace = WORKING_GDB
    arcpy.Delete_management(STREET_LINKS_LAYER_FULL)
    arcpy.Delete_management(STREET_LINKS_LAYER_BIKE_INTERSECT)
    arcpy.Delete_management(STREET_BIKE_LINKS_LAYER)
    
    arcpy.Delete_management(WORKING_GDB)


def buildBikeStreetLinkBuffer(buffer_in_feet):
    """
    Build a buffer around the entire street bike network.
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    arcpy.Buffer_analysis(STREET_BIKE_LINKS_LAYER,BIKE_STREET_LINKS_FULL_BUFFER,str(buffer_in_feet) + ' Feet','','','ALL')

def intersectBikeMapperWithBikeStreetLinkBuffer(percentage_limit,missing_links_file):
    """
    Intersect the Bike Mapper network with the street bike network.
    Any Bike Mapper links with less than percentage_limit % of their length within the buffer are flagged and a total count
    of these "missing links" is printed when this method finishes.
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    
    bike_link_lengths = {}
    #rows = arcpy.SearchCursor(BIKE_LINKS_LAYER,VALID_BIKE_LINKS_QUERY)
    rows = arcpy.SearchCursor(BIKE_LINKS_LAYER)
    for row in rows:
        #if TRAILS_MODE:
        #    key = row.getValue('ID')
        #else:
        #    a = row.getValue('F_JNCTID')
        #    b = row.getValue('T_JNCTID')
        #    key = (a,b)
        key = row.getValue('ID')
        bike_link_lengths[key] = row.getValue('Shape_Length')
    
    temp_layer = 'temp_layer_ibm'
    arcpy.MakeFeatureLayer_management(BIKE_STREET_LINKS_FULL_BUFFER,temp_layer)
    intersect_layer = temp_layer + '2'
    arcpy.Intersect_analysis([BIKE_LINKS_LAYER,BIKE_STREET_LINKS_FULL_BUFFER],intersect_layer,'','','LINE')
    
    intersect_lengths = {}
    intersect_rows = arcpy.SearchCursor(intersect_layer)
    for intersect_row in intersect_rows:
        #if TRAILS_MODE:
        #    key = intersect_row.getValue('ID')
        #else:
        #    a = intersect_row.getValue('F_JNCTID')
        #    b = intersect_row.getValue('T_JNCTID')
        #    key = (a,b)
        key = intersect_row.getValue('ID')
        if not key in intersect_lengths:
            intersect_lengths[key] = 0.0
        intersect_lengths[key] += intersect_row.getValue('Shape_Length')
    
    query = ''
    missing_indices = []
    for index in bike_link_lengths:
        if (not index in intersect_lengths) or (intersect_lengths[index]/bike_link_lengths[index] < percentage_limit):
            missing_indices.append(index)
            if len(query) > 0:
                query += ' OR '
            #if TRAILS_MODE:
            #    query += '(ID = ' + str(index) + ')'
            #else:
            #    query += '(F_JNCTID = ' + str(long(index[0])).replace('L','') + ' AND T_JNCTID = ' + str(long(index[1])).replace('L','') + ')'
            query += '(ID = ' + str(index) + ')'
    
    print 'total bike links: ' + str(len(bike_link_lengths))
    print 'missing bike links: ' + str(len(missing_indices))
    
    arcpy.Select_analysis(BIKE_LINKS_LAYER,missing_links_file,query)
    
def getSplitStreets():
    streets_to_split = {}
    split_streets = {}
    
    first = True
    for line in open(DELETE_LINK_FILE):
        if first:
            first = False
            continue
        data = line.strip().split(',')
        if len(data) > 1:
            a = int(data[0])
            b = int(data[1])
            if not a in streets_to_split:
                streets_to_split[a] = []
            streets_to_split[a].append(b)
    
    first = True
    abs = []
    for line in open(SPLIT_STREETS_FILE):
        if first:
            first = False
            continue
        data = line.strip().split(',')
        if len(data) > 1:
            a = int(float(data[0]))
            b = int(float(data[1]))
            if a in streets_to_split and len(abs) > 0:
                split_streets[(abs[0][0],abs[-1][1])] = abs
                abs = []
            abs.append((a,b))
    split_streets[(abs[0][0],abs[-1][1])] = abs
    return split_streets
    
def getDistance(point1,point2):
    """
    Get the Euclidean distance between two points.
    """
    return math.sqrt(((point1[0] - point2[0])**2) + ((point1[1] - point2[1])**2))
    
    
def main(trails_mode,create_gdb):
    if trails_mode:
        setBikeTrailsMode()
    if create_gdb:
        print 'creating working gdb'
        createWorkingGdb()
    print 'reprojecting bike links'
    reprojectBikeLinks()
    print 'dropping highway links from street network'
    removeHighwayLinksFromStreetNetwork()
    print 'building bike link buffer'
    buildFullBikeLinkBuffer(buffer_in_feet)
    print 'intersecting street links with bike links'
    intersectHighwayWithBikeLinks()
    print 'keeping highway links within buffer'
    abs_to_keep = getHighwayAbLinksToKeep(PERCENT_OVERLAY_ACCEPT_CRITERION)
    print 'creating bike street network'
    createBikeStreetNetwork(abs_to_keep)
    print 'building buffers for bike link data'
    buildSplitBikeLinkBuffer(buffer_in_feet)
    print 'intersecting bike street network with buffers'
    bike_buffer_map = intersectBikeStreetNetworkWithSplitBuffer()
    if TRAILS_MODE:
        street_splits = {}
    else:
        print 'collecting (ped) split streets'
    street_splits = getSplitStreets()
    print 'writing results'
    if TRAILS_MODE:
        writeBikeLinkUpdates(bike_buffer_map,OUTPUT_FILE_TRAILS,street_splits)
    else:
        writeBikeLinkUpdates(bike_buffer_map,OUTPUT_FILE,street_splits)
    
    print  'building bike street link buffer'
    buildBikeStreetLinkBuffer(buffer_in_feet)
    print 'intersecting bike mapper links with bike street links'
    if TRAILS_MODE:
        intersectBikeMapperWithBikeStreetLinkBuffer(PERCENT_OVERLAY_ACCEPT_CRITERION,MISSING_BIKE_TRAIL_LINKS_LAYER)
    else:
        intersectBikeMapperWithBikeStreetLinkBuffer(PERCENT_OVERLAY_ACCEPT_CRITERION,MISSING_BIKE_LINKS_LAYER)
    
#    print 'cleaning up'
#    if DELETE_WORKING_FILES:
#        cleanup()

#if __name__ == 'main':
#    main()
main(False,True) #regular bike links
main(True,False) #bike trails