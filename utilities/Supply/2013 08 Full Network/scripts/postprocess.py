#post-process
#first, run netToShapefileForPostprocess.s
#next, overlay all nodes to counties, and make a mapping:
#  {node_id->new_node_id}
#  for anything < 900,000 use the new county numbering codes
#          < 100,000 -> +300,000 (1 -> 4)
#          < 200,000 -> +300,000 (2 -> 5)
#          < 300,000 -> +600,000 (3 -> 9)
#          < 400,000 -> +300,000 (4 -> 7)
#          < 500,000 -> -400,000 (5 -> 1)
#          < 600,000 -> -400,000 (6 -> 2)
#          < 700,000 -> -400,000 (7 -> 3)
#          < 800,000 -> -200,000 (8 -> 6)
#          < 900,000 -> -100,000 (9 -> 8)
#  for anything >= 900,000 and < 5,000,000 or > 7,000,000 transfer using the following start points 
#          San Francisco: 1,000,000
#          San Mateo: 1,500,000
#          Santa Clara: 2,000,000
#          Alameda: 2,500,000
#          Contra Costa: 3,000,000
#          Solano: 3,500,000
#          Napa: 4,000,000
#          Sonoma: 4,500,000
#          Marin: 5,000,000
# for anything > 5,000,000 and < 7,000,000, use the following formula:
#     source_node = node_map[node_id - 2,000,000] + 5,500,000 (new range: [5,000,000 , 10,000,000))
# for any taps (node_id < 1,000,000 and (node_id % 100,000) >= 90,000:
#     find associated node (cnode) for each tap
#     get offset from x/y coordinates
#     new x (same formula for y) = x + 24*offset (25 foot offsets from other node/taps)
#
# for each transit line in .lin file, for each line that is ferry or rail of some sort:
#     get line identifier (name?) and then split out all of the nodes
#     for each node, find associated tap
#     open arc route stops layer and get all of the stops from that file for the route
#     map nodes to route stops; if there isn't a one-to-one match, have to deal with that...
#     add new nodes, links to tap, and change node number in route file
#     add travel time for each link
# for all other transit lines:
#     change node number base on new numbering map

import os,math,string
from operator import itemgetter
import arcpy
import pyodbc

NODE_OUTFILE = r'D:\Projects\MTC\networks\pp\postprocess_node.csv'
LINK_OUTFILE = r'D:\Projects\MTC\networks\pp\postprocess_link.csv'
TRANSIT_OUTFILE = r'D:\Projects\MTC\networks\pp\transitLines.lin'

TRANSIT_INFILE = r'D:\Projects\MTC\networks\transit\transitLines.lin'
SOURCE_LINKS = r'D:\Projects\MTC\networks\pp\postprocess_temp_link.shp'
SOURCE_NODES = r'D:\Projects\MTC\networks\pp\postprocess_temp_node.shp'
COUNTY_DIR = r'D:\Projects\MTC\networks\MAZs\MAZ'
SOURCE_COUNTY = r'D:\Projects\MTC\networks\MAZs\County\mtc_county_project.shp'
COUNTY_MAP = ['075','081','085','001','013','095','055','097','041']
COUNTY_ID_FIELD = 'COUNTYFP10'

NAD_83_DIRECTORY = r'Coordinate Systems/Projected Coordinate Systems/State Plane/NAD 1983 (US Feet)/NAD 1983 StatePlane California VI FIPS 0406 (US Feet).prj'
TRANSIT_STOPS = r'D:\Projects\MTC\networks\DBs\RTD_June2011.gdb\RTDStopsRouteBuilder_June2011'
DB_CONN_STRING = 'DRIVER={SQL Server Native Client 10.0};SERVER=w-ampdx-d-tfs05;DATABASE=RTD;UID=app_user;PWD=app_user'

NODE_X_INDEX = 0
NODE_Y_INDEX = 1
NODE_ID_INDEX = 2
NODE_COUNTY_INDEX = 3

WORKING_GDB = 'temp.gdb'

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

def collectNodes():
    """
    Get all of the node information in the form: {node_id,[x,y,new_node,county]} (new_node starts out as node_id and county is blank)
    """
    nodes = {}
    rows = arcpy.SearchCursor(SOURCE_NODES,'','','X;Y;N')
    for row in rows: 
        nodes[row.N] = [row.X,row.Y,row.N,-1]
    return nodes
    
def collectTaps(nodes):
    """
    Get all of the taps as tap_id -> connecting_node_id (connecting_node_id is the highway node the tap is connected to)
    also return a map of (stop) node_id -> list of taps this node is connected to
    """
    taps = {}
    nodes_to_taps = {}
    taps_distance = {} # holds shortest tap-node distance
    rows = arcpy.SearchCursor(SOURCE_LINKS,"CNTYPE = 'TAP'",'','A;B')
    for row in rows: 
        a = row.A
        b = row.B
        if (a < 1000000) and ((a % 100000) >= 90000):
            tap = a
            node = b
        elif (b < 1000000) and ((b % 100000) >= 90000):
            tap = b
            node = a
        else:
            continue
        tn = nodes[tap]
        nn = nodes[node]
        distance = getDistance((tn[NODE_X_INDEX],tn[NODE_Y_INDEX]),(nn[NODE_X_INDEX],nn[NODE_Y_INDEX]))
        if (not tap in taps) or (distance < taps_distance[tap]):
            taps[tap] = node
            taps_distance[tap] = distance
        if not node in nodes_to_taps:
            nodes_to_taps[node] = []
        nodes_to_taps[node].append(tap)
    return (taps,nodes_to_taps)

def collectTapModes(taps):
    tap_modes = {}
    rows = arcpy.SearchCursor(SOURCE_NODES,'MODE > 0','','N;MODE')
    for row in rows:
        tap = row.N
        if tap in taps:
           tap_modes[tap] = row.MODE 
    return tap_modes

def getDistance(point1,point2):
    """
    Get the Euclidean distance between two points.
    """
    return math.sqrt(((point1[0] - point2[0])**2) + ((point1[1] - point2[1])**2))
    
def tagNodesWithCounty(nodes):
    """
    Add county information to nodes
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    
    node_layer = 'node_layer'
    arcpy.MakeFeatureLayer_management(SOURCE_NODES,node_layer)
    county_layer = 'county_layer'
    nc_layer = 'node_county_layer'
    for i in range(len(COUNTY_MAP)):
        arcpy.MakeFeatureLayer_management(SOURCE_COUNTY,county_layer,COUNTY_ID_FIELD + " = '" + COUNTY_MAP[i] + "'")
        arcpy.SelectLayerByLocation_management(node_layer,'WITHIN',county_layer)
        arcpy.MakeFeatureLayer_management(node_layer,nc_layer)
        rows = arcpy.SearchCursor(nc_layer,'','','N')
        for row in rows:
            nodes[row.N][NODE_COUNTY_INDEX] = i+1

def renumberNodes(nodes):
    """
    Renumber all nodes
    """
    nodes_missing_counties = []
    county_indexing = []
    for i in range(9):
        county_indexing.append(i*500000 + 1000000)
        
    for node in nodes:
        if node < 100000:
            node_id = node+300000
        elif node < 200000:
            node_id = node+300000
        elif node < 300000:
            node_id = node+600000
        elif node < 400000:
            node_id = node+300000
        elif node < 500000:
            node_id = node-400000
        elif node < 600000:
            node_id = node-400000
        elif node < 700000:
            node_id = node-400000
        elif node < 800000:
            node_id = node-200000
        elif node < 900000:
            node_id = node-100000
        elif node < 5000000 or node >= 7000000:
            county = nodes[node][NODE_COUNTY_INDEX]
            if county < 0:
                nodes_missing_counties.append(node)
                node_id = -1
            else:
                node_id = county_indexing[county-1]
                county_indexing[county-1] += 1
        else:
            continue #catch on next loop
        nodes[node][NODE_ID_INDEX] = node_id
        
    for node in nodes:
        if node >= 5000000 and node < 7000000:
            node_id = nodes[node - 2000000][NODE_ID_INDEX] + 4500000
            nodes[node][NODE_ID_INDEX] = node_id
    return (nodes_missing_counties,county_indexing)

def shiftTaps(nodes,taps):
    """
    Move saps so that they are 25 ft. away from connecting node and each other
    """
    distance_shifts = {}
    node_to_tap = {}
    for tap in taps:
        node = taps[tap]
        node_x = nodes[node][NODE_X_INDEX]
        node_y = nodes[node][NODE_Y_INDEX]
        tap_x = nodes[tap][NODE_X_INDEX]
        tap_y = nodes[tap][NODE_Y_INDEX]
        shift_x = int(round(tap_x - node_x))
        shift_y = int(round(tap_y - node_y))
        new_x = node_x + shift_x*25.0
        new_y = node_y + shift_y*25.0
        nodes[tap][NODE_X_INDEX] = new_x
        nodes[tap][NODE_Y_INDEX] = new_y
        if not node in node_to_tap:
            node_to_tap[node] = {}
        node_to_tap[node][(shift_x,shift_y)] = tap
        shift_x = abs(shift_x)
        shift_y = abs(shift_y)
        if not shift_x in distance_shifts:
            distance_shifts[shift_x] = 0
        distance_shifts[shift_x] += 1
        if not shift_y in distance_shifts:
            distance_shifts[shift_y] = 0
        distance_shifts[shift_y] += 1
    for node in node_to_tap:
        if (0,0) in node_to_tap[node]:
            b = 0
            shifts = [1,0,-1]
            for i in shifts:
                for j in shifts:
                    if not (i,j) in node_to_tap[node]:
                        tap = node_to_tap[node][(0,0)]
                        nodes[tap][NODE_X_INDEX] = nodes[node][NODE_X_INDEX] + i*25
                        nodes[tap][NODE_Y_INDEX] = nodes[node][NODE_Y_INDEX] + j*25
                        #print 'fixed ' + str(tap)
                        b = 1
                        break
                if b > 0:
                    break
                        
    #print 'distance shift distribution: ' + str(distance_shifts)

def writeNodes(nodes,outfile):
    """
    Write the nodes to a file that can be read in by a cube network process
    """
    f = open(outfile,'wb')
    header = ['N','X','Y','COUNTY','MODE','TYPE','ID']
    f.write(','.join(header) + os.linesep)
    rows = arcpy.SearchCursor(SOURCE_NODES)
    nodes_to_drop = {}
    for row in rows: 
        node_data = nodes[row.N]
        county = node_data[NODE_COUNTY_INDEX]
        if county < 0:
            nodes_to_drop[row.N] = None
            continue
        data = []
        for col in header:
            if col == 'X':
                data.append(str(node_data[NODE_X_INDEX]))
            elif col == 'Y':
                data.append(str(node_data[NODE_Y_INDEX]))
            elif col == 'N':
                data.append(str(node_data[NODE_ID_INDEX]))
            elif col == 'COUNTY':
                data.append(str(county))
            else:
                data.append(str(row.getValue(col)))
        f.write(','.join(data) + os.linesep)
    f.close()
    return nodes_to_drop

def writeLines(nodes,nodes_to_drop,outfile):
    """
    Write the links to a file that can be read in by a cube network process
    """
    f = open(outfile,'wb')
    header = []
    for field in arcpy.ListFields(SOURCE_LINKS):
        header.append(field.name)
    header = header[2:] #skip arc junk
    f.write(','.join(header) + os.linesep)
    
    finished_links = {}
    rows = arcpy.SearchCursor(SOURCE_LINKS)
    for row in rows: 
        a = row.A
        b = row.B
        if (a in nodes_to_drop) or (b in nodes_to_drop):
            continue
        ft = row.ONEWAY
        if (b,a) in finished_links and finished_links[(b,a)] == ft:
            continue
        finished_links[(a,b)] = ft
        #data = []
        line = ''
        for col in header:
            if col == 'A':
                #data.append(str(nodes[a][NODE_ID_INDEX]))
                d = str(nodes[a][NODE_ID_INDEX])
            elif col == 'B':
                #data.append(str(nodes[b][NODE_ID_INDEX]))
                d = str(nodes[b][NODE_ID_INDEX])
            elif col == 'F_JNCTID' or col == 'T_JNCTID':
                #data.append(str(int(row.getValue(col))))
                d = str(int(row.getValue(col)))
            else:
                try:
                    #data.append(str(row.getValue(col)))
                    d = str(row.getValue(col))
                except:
                    #data.append(str(row.getValue(col).encode('UTF-8')))
                    d = str(row.getValue(col).encode('UTF-8'))
            line += ',' + d
        #f.write(','.join(data) + os.linesep)
        f.write(line[1:] + os.linesep)
    f.close()
    
def collectNonBusTransit():
    """
    collect the non-bus transit information from the database
    return routes: route_name -> [SCH_ROUTEID,SCH_PATTERNID,[],mode] (the third entry is a placeholde for stop locations)
    """
    qry = """ WITH t AS
            (
                SELECT CPT_AGENCYID, AGENCYNAME, SCH_ROUTEID, SCH_PATTERNID, CPT_MODE, SCH_ROUTEDESIGNATOR,
                CASE
                    WHEN HOUR_CLASS >= 3 and HOUR_CLASS < 6 THEN 'EA'
                    WHEN HOUR_CLASS >= 6 and HOUR_CLASS < 10 THEN 'AM'
                    WHEN HOUR_CLASS >= 10 and HOUR_CLASS < 15 THEN 'MD'
                    WHEN HOUR_CLASS >= 15 and HOUR_CLASS < 19 THEN 'PM'
                    WHEN (HOUR_CLASS BETWEEN 19 AND 24) OR HOUR_CLASS < 3 THEN 'EV'
                END AS tod,
                [HOURLY_FREQUENCY(Daily until HOUR_CLASS update)], HOUR_CLASS
                FROM dbo.[ROUTE HEADWAY AND FREQUENCY]
                WHERE DAYTYPE_CLASS IN
                    (SELECT dc.CLASS FROM dbo.DAYTYPE_CLASS dc WHERE WEEKDAY = 'Y')
            )
            SELECT CPT_AGENCYID, AGENCYNAME, SCH_ROUTEID, SCH_PATTERNID, CPT_MODE, SCH_ROUTEDESIGNATOR
            FROM t
            WHERE CPT_MODE in ('F','T','LR')
            GROUP BY CPT_AGENCYID, AGENCYNAME, SCH_ROUTEID, SCH_PATTERNID, CPT_MODE, SCH_ROUTEDESIGNATOR
            ORDER BY SCH_ROUTEID, SCH_PATTERNID """
        
    specials = [" ","-","\\","/","."]
    used_names = []
            
    routes = {}
    conn = pyodbc.connect(DB_CONN_STRING)
    cursor = conn.cursor()
    for row in cursor.execute(qry):
        name = row.CPT_AGENCYID + "_" + row.SCH_ROUTEDESIGNATOR[:(11 - 1 - len(row.CPT_AGENCYID))] #boosted from PublicTransit.py
        for special in specials:
            name = name.replace(special,"")
        if name.lower() in used_names:
            for letter in string.ascii_lowercase:
                final_name = name + letter
                if not final_name.lower() in used_names:
                    name = final_name
                    break
        used_names.append(name.lower())
        if row.CPT_MODE == 'F':
            mode = 3
        elif row.CPT_MODE == 'T':
            if row.AGENCYNAME == 'BART':
                mode = 5
            else:
                mode= 6
        elif row.CPT_MODE == 'LR':
            mode = 4
        routes[name] = [row.SCH_ROUTEID,row.SCH_PATTERNID,[],mode]
    conn.close()
    
    return routes

def addStopDataToRoutes(routes):
    """
    add stop data to the non-bus route data already collected
    """
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    
    tempStops = 'temp_stops'
    tempStopsSp = 'temp_stops_sp'
    if arcpy.Exists(tempStops):
        arcpy.Delete_management(tempStops)
    if arcpy.Exists(tempStopsSp):
        arcpy.Delete_management(tempStopsSp)
    arcpy.CopyFeatures_management(TRANSIT_STOPS,tempStops)
    out_coordinate_system = os.path.join(arcpy.GetInstallInfo()['InstallDir'],NAD_83_DIRECTORY)
    arcpy.Project_management(tempStops,tempStopsSp,out_coordinate_system,'NAD_1983_To_WGS_1984_1')
    arcpy.AddXY_management(tempStopsSp)
    
    for route in routes:
        qry = 'SCH_ROUTEID = ' + str(routes[route][0]) + ' AND SCH_PATTERNID = ' + str(routes[route][1])
        stops = arcpy.SearchCursor(tempStopsSp,qry,'','CPT_STOPPOINTID;SCH_STOPPOINTSEQNO;SCH_ROUTEID;SCH_PATTERNID;POINT_X;POINT_Y','SCH_STOPPOINTSEQNO A')
        for row in stops:
            routes[route][2].append((row.POINT_X,row.POINT_Y))

def switchPointsToNodes(routes,county_indexing,nodes_data):
    """
    change the x-y coordinates for non-bus stops to actual nodes
    return a list of node entries to append to the node file
    """
    #return: stop_nodes = ['N','X','Y','COUNTY','MODE','TYPE','ID']
    point_list = {}
    point_mode = {}
    id = 100 # to ensure we aren't accidentally matching ids
    for route in routes:
        for point in routes[route][2]:
            if not point in point_list:
                point_list[point] = id
                point_mode[id] = {}
                id += 1
            point_mode[point_list[point]][routes[route][3]] = None # will be used to check if nodes are shared by different modes
    
    arcpy.env.workspace = WORKING_GDB
    arcpy.env.overwriteOutput = True
    pt = arcpy.Point()
    out_coordinate_system = os.path.join(arcpy.GetInstallInfo()['InstallDir'],NAD_83_DIRECTORY)
    spatial_ref = arcpy.SpatialReference(out_coordinate_system)
    pt_geoms = []
    point_order = []
    for point in point_list:
        pt.X = point[0]
        pt.Y = point[1]
        point_order.append(point_list[point])
        pt_geoms.append(arcpy.PointGeometry(pt,spatial_ref))
    nodes_layer = 'non_bus_nodes'
    if arcpy.Exists(nodes_layer):
        arcpy.Delete_management(nodes_layer)
    arcpy.CopyFeatures_management(pt_geoms,nodes_layer)
    
    node_map = {}
    stop_nodes = []
    node_layer = 'node_layer'
    arcpy.MakeFeatureLayer_management(nodes_layer,node_layer)
    county_layer = 'county_layer'
    nc_layer = 'node_county_layer'
    neg_counter = -100 #placeholder for old ids
    for i in range(len(COUNTY_MAP)):
        arcpy.MakeFeatureLayer_management(SOURCE_COUNTY,county_layer,COUNTY_ID_FIELD + " = '" + COUNTY_MAP[i] + "'")
        arcpy.SelectLayerByLocation_management(node_layer,'WITHIN',county_layer)
        arcpy.MakeFeatureLayer_management(node_layer,nc_layer)
        arcpy.AddXY_management(nc_layer)
        rows = arcpy.SearchCursor(nc_layer,'','','OBJECTID;POINT_X;POINT_Y')
        for row in rows:
            id = point_order[row.OBJECTID - 1]
            x = row.POINT_X
            y = row.POINT_Y
            n = county_indexing[i]
            county_indexing[i] += 1
            node_map[id] = n
            modes = point_mode[id]
            if len(modes) > 1:
                print 'more than one mode for ' + str((x,y)) + ' : ' + str(modes)
            stop_nodes.append([n,x,y,i+1,modes.keys()[0],0,0])
            nodes_data[neg_counter] = [x,y,n,None]
            neg_counter -= 1
    
    for route in routes:
        for point in range(len(routes[route][2])):
            routes[route][2][point] = node_map[point_list[routes[route][2][point]]]
    
    return stop_nodes

def appendData(data,outfile):
    """
    append the routestops to the already created node file
    """
    #data is list of string data
    f = open(outfile,'ab')
    for d in data:
        f.write(','.join(map(str,d)) + os.linesep)
    f.close()

def writeTransit(transit_infile,nodes,transit_outfile,node_outfile,link_outfile,non_bus_routes):
    """
    Write the transit lines to a file that can be read in by the Cube transit network creation process
    """
    non_bus_stop_nodes = {} # each entry is mode -> node_number -> [original_stop1, original_stop2,...]
    
    ftransit = open(transit_outfile,'wb')
    fnode = open(node_outfile,'ab')
    flink = open(link_outfile,'ab')
    first = True
    for line in open(transit_infile):
        if first:
            ftransit.write(line)
            first = False
            continue
        data = line.strip().split(' N=')
        non_bus_route = None
        for route in non_bus_routes:
            if data[0].find('NAME="' + route + '"') > -1:
                non_bus_route = route
                break
        if (not non_bus_route is None):
            original_stops = data[1].strip().split(',')
            if len(original_stops) != len(non_bus_routes[non_bus_route][2]):
                #deal with this...
                ftransit.write('todo...' + os.linesep)
            else:
                updata = []
                last_node = -908
                for i in range(len(original_stops)):
                    node = non_bus_routes[non_bus_route][2][i]
                    mode = non_bus_routes[non_bus_route][3]
                    if node < 0 or last_node == node:
                        continue
                    original_stop = original_stops[i]
                    prefix = ''
                    if original_stop < 0:
                        prefix = '-'
                        original_stop = original_stop[1:]
                    updata.append(prefix + str(node))
                    if not mode in non_bus_stop_nodes:
                        non_bus_stop_nodes[mode] = {}
                    if not node in non_bus_stop_nodes[mode]:
                        non_bus_stop_nodes[mode][node] = []
                    non_bus_stop_nodes[mode][node].append(int(original_stops[i]))
                    last_node = node
                ftransit.write(data[0] + ' N=' + ','.join(updata) + os.linesep)
        else:
            updata = []
            last_node = -908
            for node in data[1].strip().split(','):
                node = node.strip()
                prefix = ''
                if node[0] == '-':
                    prefix = '-'
                    node = node[1:]
                node_id = nodes[int(node)][NODE_ID_INDEX]
                if node_id > 0 and node_id != last_node:
                    updata.append(prefix + str(node_id))
                    last_node = node_id
            ftransit.write(data[0] + ' N=' + ','.join(updata) + os.linesep)
    ftransit.close()
    fnode.close()
    flink.close()
    return non_bus_stop_nodes
    
def formNewTransitLinks(non_bus_routes,non_bus_stop_nodes,nodes_to_taps,node_info,tap_modes):
    #node_info is node_id->[x,y,new_node_id,...]
    #first transit links
    #then tap connectors
    #links; A	B	F_JNCTID	T_JNCTID	FRC	NAME	FREEWAY	TOLLRD	ONEWAY	KPH	MINUTES	CARRIAGE	LANES	RAMP	SPEEDCAT	FEET	ASSIGNABLE	CNTYPE	TRANSIT	USECLASS	TOLLBOOTH	FT	FFS	NUMLANES	HIGHWAYT	B_CLASS	REPRIORITIZN	GRADE_CAT	PED_FLAG
    # [A,B,F_JNCTID,T_JNCTID,FRC,NAME,FREEWAY,TOLLRD,ONEWAY,KPH,MINUTES,CARRIAGE,LANES,RAMP,SPEEDCAT,FEET,ASSIGNABLE,CNTYPE,TRANSIT,USECLASS,TOLLBOOTH,FT,FFS,NUMLANES,HIGHWAYT,B_CLASS,REPRIORITIZ,GRADE_CAT,PED_FLAG]
    #default_link = [A,B,0,0,0,0,0,'','',0,MINUTES,'',0,0,0,FEET,0,CNTYPE,TRANSIT,0,0,0,0,0,'','','','','']
    
    #build node id->point
    node_points = {}
    original_node_points = {}
    for node_id in node_info:
        node_data = node_info[node_id]
        p = (node_data[NODE_X_INDEX],node_data[NODE_Y_INDEX])
        node_points[node_data[NODE_ID_INDEX]] = p
        original_node_points[node_id] = p
    
    mode_to_taps = {}
    for tap in tap_modes:
        mode = tap_modes[tap]
        if not mode in mode_to_taps:
            mode_to_taps[mode] = []
        mode_to_taps[mode].append(tap)
    
    finished_links = {}
    links = []
    for route in non_bus_routes:
        stops = non_bus_routes[route][2]
        mode = non_bus_routes[route][3]
        last_stop = stops[0]
        for i in range(1,len(stops)):
            stop = stops[i]
            if last_stop == stop:
                continue
            if not (last_stop,stop) in finished_links:
                if mode == 3:
                    m = 'FERRY'
                elif mode == 4:
                    m = 'LRAIL'
                elif mode == 5:
                    m = 'HRAIL'
                elif mode == 6:
                    m = 'CRAIL'
                distance = getDistance(node_points[last_stop],node_points[stop])
                time = -1 #todo: add this in later? 
                link = [last_stop,stop,0,0,0,0,0,'','',0,time,'',0,0,0,distance,0,m,1,0,0,0,0,0,'','','','','',0]
                links.append(map(str,link))
                finished_links[(last_stop,stop)] = None
                finished_links[(stop,last_stop)] = None
            last_stop = stop
    
    finished_tap_links = {} #tap -> list of nodes connected
    for mode in non_bus_stop_nodes:
        for stop in non_bus_stop_nodes[mode]:
            for original_stop in non_bus_stop_nodes[mode][stop]:
                if not original_stop in nodes_to_taps:
                    continue
                taps = nodes_to_taps[original_stop]
                distance = 9999999
                tap = -1
                for t in taps: #pick closest tap
                    if not tap_modes[t] == mode:
                        continue
                    d = getDistance(node_points[stop],original_node_points[t])
                    if d < distance:
                        distance = d
                        tap = node_info[t][NODE_ID_INDEX]
                if tap == -1:
                    #find closest tap because we didn't
                    for t in mode_to_taps[mode]:
                        d = getDistance(node_points[stop],original_node_points[t])
                        if d < distance:
                            distance = d
                            tap = node_info[t][NODE_ID_INDEX]
                if tap == -1:
                    print 'bad tap for original stop: ' + str(original_stop)
                if not tap in finished_tap_links:
                    finished_tap_links[tap] = []
                if not stop in finished_tap_links[tap]:
                    finished_tap_links[tap].append(stop)
                    link = [stop,tap,0,0,0,0,0,'','',0,0,'',0,0,0,distance,0,'TAP',1,0,0,0,0,0,'','','','','',0]
                    links.append(map(str,link))
    return links

def cleanLinkFile(link_file):
    fout = link_file + '.tmp'
    f = open(fout,'wb')
    
    string_cols = [5,7,8,11,17,24,28]
    first = True
    for line in open(link_file):
        if first:
            first = False
            f.write(line.strip() + ',REV' + os.linesep)
            continue
        line = line.strip().split(',')
        for col in string_cols:  
            column = line[col]
            if len(column) == 0 or column[0] != "'":
                if line[col].find("'") > -1:
                    line[col] = '"' + line[col].strip() + '"'
                else:
                    line[col] = "'" + line[col].strip() + "'"
        if line[8] == "'FT'":
            dir = '1'
        elif line[8] == "'TF'":
            dir = '1'
            #a = line[0]
            #b = line[1]
            #line[1] = a
            #line[0] = b
            line[8] = "'FT'"
        else:
            dir = '2'
        line.append(dir)
        f.write(','.join(line) + os.linesep)
    f.close()
    os.remove(link_file)
    os.rename(fout,link_file)

def cleanDuplicateLinks(link_file):
    dupe = ",0,0,0,'',0,'','',0,0.0,'',0,0,0,0.0,0,'',0,0,0,0,0.0,0,'',"
    dupes = {}
    for line in open(link_file):
        line = line.strip()
        if line.find(dupe) > -1:
            line = line.split(dupe)
            dupes[line[0]] = line[1]
    
    for line in open(link_file):
        line = line.strip()
        if line.find(dupe) < 0:
            line = line.split(',')
            token = line[0] + ',' + line[1]
            if token in dupes:
                dupes.pop(token)
    print len(dupes)
    for token in dupes.keys()[:20]:
        print token + ' ' + dupes[token]

print 'creating working GDB'
createWorkingGdb()
print 'collecting node information'
nodes = collectNodes()
print 'tagging nodes with counties'
tagNodesWithCounty(nodes)
print 'renumbering nodes'
(missing_nodes,county_indexing) = renumberNodes(nodes)
#print 'missing ' + str(len(missing_nodes)) + ' nodes'
print 'collecting taps'
(taps,nodes_to_taps) = collectTaps(nodes)
print 'collecting tap modes'
tap_modes = collectTapModes(taps)
print 'shifting taps'
shiftTaps(nodes,taps)
print 'writing network'
print '    nodes'
nodes_to_drop = writeNodes(nodes,NODE_OUTFILE)
print '    links'
writeLines(nodes,nodes_to_drop,LINK_OUTFILE)
print 'collecting non-bus information from database'
non_bus_routes = collectNonBusTransit()
print 'adding stop data to non-bus routes'
addStopDataToRoutes(non_bus_routes)
print 'setting nodes for non-bus route stops'
stop_nodes = switchPointsToNodes(non_bus_routes,county_indexing,nodes)
print 'writing non-bus route nodes'
appendData(stop_nodes,NODE_OUTFILE)
print 'writing transit'
non_bus_stop_nodes = writeTransit(TRANSIT_INFILE,nodes,TRANSIT_OUTFILE,NODE_OUTFILE,LINK_OUTFILE,non_bus_routes)
print 'form new transit links'
new_links = formNewTransitLinks(non_bus_routes,non_bus_stop_nodes,nodes_to_taps,nodes,tap_modes)
print 'writing non-bus transit links and connectors'
appendData(new_links,LINK_OUTFILE)
print 'cleaning link file for Cube'
cleanLinkFile(LINK_OUTFILE)
cleanDuplicateLinks(LINK_OUTFILE)
