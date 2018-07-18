"""
Classes for building public transit network from the RTD geodatabase. Supports
building network, generating link and node sequence, analyzing stops, and
creating the TAP system.
"""

import arcpy
import os
import sys
import math
import pyodbc
import cPickle
import logging
import random
import string
from rtree import index

##############################################################################
# Enumerations
##############################################################################
class Mode:
    """
    Enumeration of transit modes
    """    
    LOCAL_BUS     = 1
    EXPRESS_BUS   = 2
    FERRY         = 3
    LIGHT_RAIL    = 4
    HEAVY_RAIL    = 5
    COMMUTER_RAIL = 6
    
    @staticmethod
    def getModeFromLookupTable(mode_name):
        mode_name = mode_name.lower()
        if mode_name == "local bus":
            return Mode.LOCAL_BUS
        elif mode_name == "express bus":
            return Mode.EXPRESS_BUS
        elif mode_name == "ferry service":
            return Mode.FERRY
        elif mode_name == "light rail":
            return Mode.LIGHT_RAIL
        elif mode_name == "heavy rail":
            return Mode.HEAVY_RAIL
        elif mode_name == "commuter rail":
            return Mode.COMMUTER_RAIL
            
    @staticmethod
    def getModeName(mode_code):
        if mode_code == Mode.LOCAL_BUS:
            return "Local bus"
        elif mode_code == Mode.EXPRESS_BUS:
            return "Express bus"
        elif mode_code == Mode.FERRY:
            return "Ferry service"
        elif mode_code == Mode.LIGHT_RAIL:
            return "Light rail"
        elif mode_code == Mode.HEAVY_RAIL:
            return "Heavy rail"
        elif mode_code == Mode.COMMUTER_RAIL:
            return "Commuter rail"
    
class LineFileType:
    """
    Enumeration of cube Line file types
    """
    PTLINE   = 1
    TRNBUILD = 2


##############################################################################
# Node and Link classes
##############################################################################
class Node:
    """
    Represents a network node.
    """
    MAX_ID = -1
    
    def __init__(self, nodeId, x, y):
        """Constructor"""
        self.nodeId = nodeId
        self.x = x
        self.y = y
        Node.MAX_ID = max(Node.MAX_ID,nodeId)


class Link:
    """
    Represents a network link with Node references to the from and to nodes.
    """
    MAX_ID = -1
    
    def __init__(self, linkId, fromNode, toNode, oneWay):
        self.linkId = linkId
        self.fromNode = fromNode
        self.toNode = toNode
        self.oneWay = oneWay
        Link.MAX_ID = max(Link.MAX_ID,linkId)


class TransitStop:
    """Represents an RTD transit stop"""
    def __init__(self, stopPointId, routeId, patternId, routePattern, sourceOID, seqNo):
        self.stopPointId = stopPointId
        self.routePattern = routePattern
        self.routeId = routeId
        self.patternId = patternId
        self.sourceOID = sourceOID
        self.seqNo = seqNo
        self.tanaNode = -1
        
        self.inRegion = True
        
    def basicEqual(self,otherStop):
        return self.stopPointId == otherStop.stopPointId and \
               self.routePattern == otherStop.routePattern and \
               self.routeId == otherStop.routeId and \
               self.patternId == otherStop.patternId and \
               self.sourceOID == otherStop.sourceOID and \
               self.seqNo == otherStop.seqNo and \
               self.tanaNode == otherStop.tanaNode


class TransitRoute:
    """
    Represents a transit line, with attributes for the pattern, five time of day headways,
    the agency, mode, and lists of the link sequence and node sequence.
    """
    def __init__(self, name, routeId = 0, patternId = 0, longName = '', eaHeadway = 0,
                 amHeadway = 0, mdHeadway = 0, pmHeadway = 0, evHeadway = 0, mode = 0):
        self.name = name
        self.longName = longName
        self.routeId = routeId
        self.patternId = patternId
        self.eaHeadway = eaHeadway    # early AM headway
        self.amHeadway = amHeadway    # AM peak headway
        self.mdHeadway = mdHeadway    # midday headway
        self.pmHeadway = pmHeadway    # PM peak headway
        self.evHeadway = evHeadway    # evening headway
        self.agency = ''
        self.mode = mode
        self.linkSequence = []
        self.nodeSequence = []
        self.new_name = ''
        self.mode_group = ''


##############################################################################
# Main PublicTransit processing class
##############################################################################
class PublicTransit:
    """
    Public transit processing class. Contains methods to build transit
    network with stops, write the lines file, and generate TAPs.
    """    
    BASE_DIR                  = "D:\\Projects\\MTC\\networks\\"
    WORKING_GDB               = "d:\\projects\\MTC\\Intersect.gdb\\"
    RELEVANT_NODES            = "ca_jc_relevant_sp"                                                                    # Relevant nodes within the MTC region
    RTD_PATH                  = BASE_DIR + "DBs\\RTD_June2011.gdb"                                                     # RTD geodatabase path
    MODE_LOOKUP_FILE_NAME     = BASE_DIR + "transit\\mode_lookup.csv"                                                  # mode lookup file
    BUS_ROUTE_TRAVERSAL_EDGES = "BusRouteTraversalEdges"                                                               # network link sequence for bus routes
    ROADWAYS_FC               = 'Network/Roadways'                                                                     # TeleAtlas master roads network
    RTD_STOPS                 = 'Network/RTDStopsRouteBuilder_June2011'                                                # Stop points for all modes
    ROUTE_EDGES_FEATURE_LYR   = 'busRouteEdges'                                                                        # Temp feature layer used to get links on path
    BUS_ROUTES                = 'BusRoutes'
    NAD_83_DIRECTORY          = r"Coordinate Systems/Projected Coordinate Systems/" + \
                                "State Plane/NAD 1983 (US Feet)/" + \
                                "NAD 1983 StatePlane California VI FIPS 0406 (US Feet).prj"
    DB_CONN_STRING            = "DRIVER={SQL Server Native Client 10.0};" + \
                                "SERVER=w-ampdx-d-tfs05;DATABASE=RTD;" + \
                                "UID=app_user;PWD=app_user"
    OUTFILE_NAME              = BASE_DIR + "transitLines.lin"                                           # lines file
    LINE_FILE_TYPE            = LineFileType.TRNBUILD
    PICKLE_SAVE_FILE          = BASE_DIR + "data.pkl"
    SPATIAL_INDEX_FILE        = BASE_DIR + "spIndex"
    TANA_NODE_NUMBER_OFFSET   = 3000000                                                                 # after stripping first 7 digits of TANA nodes, add this offset to it
    TAPS_FILE_NAME            = BASE_DIR + "taps.txt"
    NODE_TO_TAP_FILE_NAME     = BASE_DIR + "nodes_to_taps.txt"
    TAZ_SHAPEFILE_PATH        = BASE_DIR + "MAZs\\TAZ"
    
    def __init__(self):
        """
        Create a new PublicTransit class instance. Initialize all class variables
        to empty.
        """
        
        self.linksDict = dict()
        self.nodesDict = dict()
        self.stopsByRoute = dict()
        self.stopsByNode = dict()
        self.routeXref = dict()
        self.transitRoutes = dict()
        self.spIndex = None


    def buildStopsDict(self):
        """
        Builds the dictionary of TransitStops for each route. Copies the RTD
        stops to a new feature class, projects them to NAD83, and then
        calculates the X,Y coordinates. Finally, snaps each stop to the
        nearest highway network node.
        
        Preconditions: nodesDict and linksDict must be populated
        
        """
    
        if len(self.nodesDict) == 0:
            raise Exception('Nodes dictionary is empty!')
        if len(self.linksDict) == 0:
            raise Exception('Links dictionary is empty!')
        
        self.stopsByRoute = dict()
        self.stopsByNode = dict()
        arcpy.env.workspace = PublicTransit.WORKING_GDB
        
        tempStops = "temp_stops"
        tempStopsSp = "temp_stops_sp"
        
        # Delete temp_stops and temp_stops_sp feature classes if they exist.
        if arcpy.Exists(tempStops):
            arcpy.Delete_management(tempStops)
        if arcpy.Exists(tempStopsSp):
            arcpy.Delete_management(tempStopsSp)
        arcpy.CopyFeatures_management(PublicTransit.RTD_PATH + PublicTransit.RTD_STOPS,
                                      tempStops)
    
        # Project temp_stops to CA state plane and add XY.
        install_dir = arcpy.GetInstallInfo()['InstallDir']
        out_coordinate_system = os.path.join(install_dir, PublicTransit.NAD_83_DIRECTORY)
        arcpy.Project_management(tempStops, tempStopsSp, out_coordinate_system,
                                 "NAD_1983_To_WGS_1984_1")
        arcpy.AddXY_management(tempStopsSp)
    
        # Create a search cursor to traverse all stops.
        stops = arcpy.SearchCursor(tempStopsSp, "", "",
                                   "CPT_STOPPOINTID; SCH_STOPPOINTSEQNO; " +
                                   "SCH_ROUTEID; SCH_PATTERNID; ROUTE_PATTERN; " +
                                   "SourceOID; POINT_X; POINT_Y",
                                   "ROUTE_PATTERN A; SCH_STOPPOINTSEQNO A")
        numStops = int(arcpy.GetCount_management(tempStopsSp).getOutput(0))
        print "Found %d stops" % numStops
    
        p = index.Property()
        p.overwrite = True
        self.spIndex = index.Index(PublicTransit.SPATIAL_INDEX_FILE,properties=p)
        
        # For each stop determine the nearest network node.
        scount = 0
        icount = 0
        for s in stops:
            # only create stops for routes which exist in RTD
            if not s.ROUTE_PATTERN in self.transitRoutes:
                continue
            scount += 1
            st = TransitStop(s.CPT_STOPPOINTID, s.SCH_ROUTEID, s.SCH_PATTERNID,
                             s.ROUTE_PATTERN, s.SourceOID, s.SCH_STOPPOINTSEQNO)
            # If the stop's linkId is in the links dictionary use the link from
            # and to node (these should all be bus routes since MTC's route
            # traversal FC was created for buses only at this time).
            if s.SourceOID in self.linksDict:
                link = self.linksDict[s.SourceOID]
                # Determine which node is nearest and snap to it.
                if self.__getDistance(s.POINT_X,
                                      s.POINT_Y,
                                      link.fromNode.x,
                                      link.fromNode.y) <= \
                   self.__getDistance(s.POINT_X,
                                      s.POINT_Y,
                                      link.toNode.x,
                                      link.toNode.y):
                    st.tanaNode = link.fromNode.nodeId
                else:
                    st.tanaNode = link.toNode.nodeId
                st.inRegion = True
    
            # The stop's link is not in linksDict. These are either stops 
            # outside the region or non-bus routes for which there are no
            # route traversal edges. Do a link lookup from the Roadways
            # feature class.
            else:
                arcpy.env.workspace = PublicTransit.RTD_PATH
                roadwaysSearch = arcpy.SearchCursor(PublicTransit.ROADWAYS_FC,
                                                    "LinkId = " + str(s.SourceOID),
                                                    "", "", "F_JNCTID; T_JNCTID", "")
                for r in roadwaysSearch:
                    fromNode = self.__getIdHash(r.F_JNCTID)
                    toNode = self.__getIdHash(r.T_JNCTID)
                    if fromNode in self.nodesDict and toNode in self.nodesDict:
                        if self.__getDistance(s.POINT_X,
                                              s.POINT_Y,
                                              self.nodesDict[fromNode].x,
                                              self.nodesDict[fromNode].y) <= \
                           self.__getDistance(s.POINT_X,
                                              s.POINT_Y,
                                              self.nodesDict[toNode].x,
                                              self.nodesDict[toNode].y):
                            st.tanaNode = fromNode
                        else:
                            st.tanaNode = toNode
                        st.inRegion = True
                    else:
                        st.inRegion = False
            
            # Add the stop to stopsByRoute and stopsByNode dictionaries
            if s.ROUTE_PATTERN in self.stopsByRoute:
                self.stopsByRoute[s.ROUTE_PATTERN].append(st)
            else:
                self.stopsByRoute[s.ROUTE_PATTERN] = [st]
            if (st.tanaNode in self.stopsByNode):
                self.stopsByNode[st.tanaNode].append(st)
            else:
                self.stopsByNode[st.tanaNode] = [st]
                # add the stop node to the spatial index
                if st.tanaNode in self.nodesDict:
                    icount += 1
                    self.spIndex.insert(st.stopPointId,
                                        (self.nodesDict[st.tanaNode].x,
                                        self.nodesDict[st.tanaNode].y,
                                        self.nodesDict[st.tanaNode].x,
                                        self.nodesDict[st.tanaNode].y))
        del stops
       
       
    def getModeLookupTable(self):
        """
        get lookup table for modes
        """
        mode_table = []
        header = None
        for line in open(PublicTransit.MODE_LOOKUP_FILE_NAME):
            line = line.strip()
            if len(line) == 0: 
                continue
            line = map(str.strip,line.split(","))
            if header is None:
                header = line
                #CPT_AGENCYID	AGENCYNAME	CPT_MODE	SCH_ROUTEDESIGNATOR	MODECODE	MODEGROUP
                continue
            data = {}
            for i in range(len(line)):
                data[header[i]] = line[i]
            mode_table.append(data)
        return mode_table
            
    def __cleanRouteName(self,name,used_names):
        specials = [" ","-","\\","/","."]
        for special in specials:
            name = name.replace(special,"")
        final_name = name
        if final_name.lower() in used_names:
            for letter in string.ascii_lowercase:
                final_name = name + letter
                if not final_name.lower() in used_names:
                    break
        used_names.append(final_name.lower())
        return final_name
    
    def buildRoutesDict(self):
        """
        Queries the RTD database and builds the dictionary of routes and route attributes,
        including headways for each time of day period.
        """
    
        # create route number and name xref dictionary
        arcpy.env.workspace = PublicTransit.RTD_PATH
        routes = arcpy.SearchCursor(PublicTransit.BUS_ROUTES, "", "", "RouteID; Name", "")
        self.routeXref = dict()
        for route in routes:
            self.routeXref[route.RouteID] = route.Name
            self.routeXref[route.Name] =  route.RouteID
        del routes
        
        #get mode lookup table
        mode_table = self.getModeLookupTable()
        
        # Query the RTD database for the route name, operator, mode, and headways.
        # We are querying for weekday routes (DAYTYPE_CLASS Weekday field = 'Y')
        conn = pyodbc.connect(PublicTransit.DB_CONN_STRING)
        cursor = conn.cursor()
        self.transitRoutes = dict()
        qry = """
            WITH t AS
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
            SELECT CPT_AGENCYID, AGENCYNAME, SCH_ROUTEID, SCH_PATTERNID, CPT_MODE, SCH_ROUTEDESIGNATOR, tod,
                60.0 / ROUND(AVG(CAST([HOURLY_FREQUENCY(Daily until HOUR_CLASS update)] AS FLOAT)), 0) as headway
            FROM t
            GROUP BY CPT_AGENCYID, AGENCYNAME, SCH_ROUTEID, SCH_PATTERNID, CPT_MODE, SCH_ROUTEDESIGNATOR, tod
            ORDER BY SCH_ROUTEID, SCH_PATTERNID, tod"""
    
        used_route_names = []
        # Iterate through result set and apply attributes.
        for row in cursor.execute(qry):
            routePattern = str(row.SCH_ROUTEID) + "_" + str(row.SCH_PATTERNID)
            if routePattern not in self.transitRoutes:
                self.transitRoutes[routePattern] = TransitRoute(routePattern,
                                                                routeId = row.SCH_ROUTEID,
                                                                patternId = row.SCH_PATTERNID)
                self.transitRoutes[routePattern].new_name = self.__cleanRouteName(row.CPT_AGENCYID + "_" + row.SCH_ROUTEDESIGNATOR[:(11 - 1 - len(row.CPT_AGENCYID))],used_route_names) #12 is the maximum name length
                self.transitRoutes[routePattern].agency = row.AGENCYNAME
                mode = -1
                for mode_row in mode_table:
                    if row.CPT_AGENCYID == mode_row["CPT_AGENCYID"] and row.CPT_MODE == mode_row["CPT_MODE"]:
                        if mode_row["SCH_ROUTEDESIGNATOR"] != "NA":
                            if row.SCH_ROUTEDESIGNATOR == mode_row["SCH_ROUTEDESIGNATOR"]:
                                mode = mode_row["MODECODE"]
                                mode_group = Mode.getModeFromLookupTable(mode_row["MODEGROUP"])
                                break #this is as detailed as we can get
                        else:
                            mode = mode_row["MODECODE"]
                            mode_group = Mode.getModeFromLookupTable(mode_row["MODEGROUP"])
                self.transitRoutes[routePattern].mode = mode
                self.transitRoutes[routePattern].mode_group = Mode.getModeName(mode_group)
            # set headways
            if row.tod == 'EA':
                self.transitRoutes[routePattern].eaHeadway = row.headway
            elif row.tod == 'AM':
                self.transitRoutes[routePattern].amHeadway = row.headway
            elif row.tod == 'MD':
                self.transitRoutes[routePattern].mdHeadway = row.headway
            elif row.tod == 'PM':
                self.transitRoutes[routePattern].pmHeadway = row.headway
            elif row.tod == 'EV':
                self.transitRoutes[routePattern].evHeadway = row.headway
        conn.close()
    
    
    def buildNodesDict(self):
        """
        Builds dictionary of relevant TANA nodes.
        """
        # Get relevant nodes from TANA ca_jc, intersect with BUS_ROUTE_TRAVERSAL_EDGES.
        # Then get the X,Y for the features.
        arcpy.env.workspace = PublicTransit.WORKING_GDB
        arcpy.AddXY_management(PublicTransit.RELEVANT_NODES)
        nodes = arcpy.SearchCursor(PublicTransit.RELEVANT_NODES, "", "",
                                   "ID_hash; POINT_X; POINT_Y", "")
        self.nodesDict = dict()
        numNodes = int(arcpy.GetCount_management(PublicTransit.RELEVANT_NODES).getOutput(0))
        print "Found %d nodes" % numNodes
        for node in nodes:
            self.nodesDict[node.ID_hash] = Node(node.ID_hash, node.POINT_X, node.POINT_Y)
            del node
        del nodes
    
    
    def buildLinksDict(self):
        """
        Creates a dictionary of the links in BusRouteTraversalEdges. Only
        stores links that are within the region.
        """
        
        arcpy.env.workspace = PublicTransit.RTD_PATH
        # Check if feature layer already exists; if so, delete it.
        if arcpy.Exists(PublicTransit.ROUTE_EDGES_FEATURE_LYR):
            arcpy.Delete_management(PublicTransit.ROUTE_EDGES_FEATURE_LYR)
        # Create a feature layer based on bus route traversal edges, and join to
        # the Roadways feature class.
        arcpy.MakeFeatureLayer_management(PublicTransit.BUS_ROUTE_TRAVERSAL_EDGES,
                                          PublicTransit.ROUTE_EDGES_FEATURE_LYR)
        routeTraversalEdgesJoinField = "SourceOID"
        roadwaysJoinField = "LinkId"
        arcpy.AddJoin_management(PublicTransit.ROUTE_EDGES_FEATURE_LYR,
                                 routeTraversalEdgesJoinField,
                                 PublicTransit.ROADWAYS_FC,
                                 roadwaysJoinField,
                                 "KEEP_COMMON")
        self.linksDict = dict()
        
        linkIdField = "Roadways.LinkId"
        fromNodeField = "Roadways.F_JNCTID"
        toNodeField = "Roadways.T_JNCTID"
        onewayField = "Roadways.ONEWAY"
        
        links = arcpy.SearchCursor(PublicTransit.ROUTE_EDGES_FEATURE_LYR, "", "",
                                   linkIdField + ";" + fromNodeField + ";" +
                                   toNodeField + ";" + onewayField, "")                
        print "Found %d links" % \
            int(arcpy.GetCount_management(PublicTransit.ROUTE_EDGES_FEATURE_LYR).getOutput(0))
            
        linkIter = 0
        # Add link to dictionary if both the from and to node are in the nodes dictionary.
        for l in links:
            linkId = l.getValue(linkIdField)
            fromNode = self.__getIdHash(l.getValue(fromNodeField))
            toNode = self.__getIdHash(l.getValue(toNodeField))
            oneWay = l.getValue(onewayField)
            if (linkId not in self.linksDict):
                if (fromNode in self.nodesDict and toNode in self.nodesDict):
                    self.linksDict[linkId] = Link(linkId, self.nodesDict[fromNode],
                                                  self.nodesDict[toNode], oneWay)
            linkIter += 1
            if (linkIter % 10000 == 0):
                print "processed %d links" % (linkIter)
            del l
        del links
        arcpy.Delete_management(PublicTransit.ROUTE_EDGES_FEATURE_LYR)
    
    
    def buildRouteLinkSequence(self):
        """
        Builds the link sequence for a bus route using the route traversal edges
        """
        arcpy.env.workspace = PublicTransit.RTD_PATH
        linkSeq = arcpy.SearchCursor(PublicTransit.BUS_ROUTE_TRAVERSAL_EDGES, "", "", "", "RouteId A; Cumul_Distance A")
        prevRouteId = -1
        for e in linkSeq:
            if (e.RouteId in self.routeXref):
                routePattern = self.routeXref[e.RouteId]
                if (routePattern in self.transitRoutes):    #not all routes are in RTD, so check
                    if (prevRouteId != e.RouteId):
                        self.transitRoutes[routePattern].linkSequence = []
                    self.transitRoutes[routePattern].linkSequence.append(e.SourceOID)
                prevRouteId = e.RouteId
            del e
        del linkSeq

        
    def writeRouteSequence(self):
        """
        Writes the network node traversal sequence to file from the link sequence.
        If the route does not have a link sequence, then the stop sequence is written.
        """
        print "writing route sequence"
        f = open(PublicTransit.OUTFILE_NAME, 'wb')
        if (PublicTransit.LINE_FILE_TYPE == LineFileType.PTLINE):
            lines = [";;<<PT>><<LINE>>;;" + os.linesep]
        elif (PublicTransit.LINE_FILE_TYPE == LineFileType.TRNBUILD):
            lines = [";;<<Trnbuild>>;;" + os.linesep]

        for t in self.transitRoutes:
            if t in self.stopsByRoute:
                i = 0
                self.transitRoutes[t].nodeSequence = []
                prevLinkId = -1
                # Bus routes have a link sequence from BusRouteTraversalEdges. Others just have stops.
                if (len(self.transitRoutes[t].linkSequence) > 0):
                    for link in self.transitRoutes[t].linkSequence:
                        # make sure this link is within the region (i.e., it is in linksDict)
                        if (link in self.linksDict):
                            nodeToAppend = -1
                            if (i == 0):
                                nodeToAppend = self.stopsByRoute[t][0].tanaNode
                                if (nodeToAppend == -1):
                                    if (self.linksDict[link].oneWay == "FT"):
                                        nodeToAppend = -self.linksDict[link].fromNode.nodeId
                                    elif (self.linksDict[link].oneWay == "TF"):
                                        nodeToAppend = -self.linksDict[link].toNode.nodeId
                                    else:   # open in both directions; determine traversal direction
                                        nodeToAppend = -self.linksDict[link].fromNode.nodeId                            
                            elif (i == 1):
                                if (len(self.transitRoutes[t].nodeSequence) > 0):
                                    if (self.linksDict[link].oneWay == "FT"):
                                        if (self.stopsByRoute[t][0].tanaNode != self.linksDict[link].fromNode.nodeId):
                                            self.transitRoutes[t].nodeSequence.append(-self.linksDict[link].fromNode.nodeId)
                                        nodeToAppend = -self.linksDict[link].toNode.nodeId
                                    elif (self.linksDict[link].oneWay == "TF"):
                                        if (self.stopsByRoute[t][0].tanaNode != self.linksDict[link].toNode.nodeId):
                                            self.transitRoutes[t].nodeSequence.append(-self.linksDict[link].toNode.nodeId)
                                        nodeToAppend = -self.linksDict[link].fromNode.nodeId
                                    else:    # open in both directions
                                        if (abs(self.transitRoutes[t].nodeSequence[0]) == self.linksDict[link].fromNode.nodeId):
                                            nodeToAppend = -self.linksDict[link].toNode.nodeId
                                        elif (abs(self.transitRoutes[t].nodeSequence[0]) == self.linksDict[link].toNode.nodeId):
                                            nodeToAppend = -self.linksDict[link].fromNode.nodeId
                                        elif (self.transitRoutes[t].linkSequence[0] in self.linksDict and 
                                            self.linksDict[self.transitRoutes[t].linkSequence[0]].toNode.nodeId == self.linksDict[link].fromNode.nodeId):
                                            self.transitRoutes[t].nodeSequence.append(-self.linksDict[link].fromNode.nodeId)
                                            nodeToAppend = -self.linksDict[link].toNode.nodeId
                                        elif (self.transitRoutes[t].linkSequence[0] in self.linksDict and 
                                            self.linksDict[self.transitRoutes[t].linkSequence[0]].fromNode.nodeId == self.linksDict[link].toNode.nodeId):
                                            self.transitRoutes[t].nodeSequence.append(-self.linksDict[link].toNode.nodeId)
                                            nodeToAppend = -self.linksDict[link].fromNode.nodeId

                            elif (prevLinkId != link and prevLinkId != -1):  # ensure there are no repeated links
                                if (self.linksDict[link].oneWay == "FT"):
                                    if (len(self.transitRoutes[t].nodeSequence) > 0 and 
                                        abs(self.transitRoutes[t].nodeSequence[-1]) == self.linksDict[link].fromNode.nodeId):
                                        nodeToAppend = -self.linksDict[link].toNode.nodeId
                                    elif (len(self.transitRoutes[t].nodeSequence) > 0):
                                        self.transitRoutes[t].nodeSequence.pop()
                                        if (len(self.transitRoutes[t].nodeSequence) > 0 and
                                            abs(self.transitRoutes[t].nodeSequence[-1]) == self.linksDict[link].fromNode.nodeId):
                                            nodeToAppend = -self.linksDict[link].toNode.nodeId

                                elif (self.linksDict[link].oneWay == "TF"):
                                    if (len(self.transitRoutes[t].nodeSequence) > 0 and
                                        abs(self.transitRoutes[t].nodeSequence[-1]) == self.linksDict[link].toNode.nodeId):
                                        nodeToAppend = -self.linksDict[link].fromNode.nodeId
                                    elif (len(self.transitRoutes[t].nodeSequence) > 0):
                                        self.transitRoutes[t].nodeSequence.pop()
                                        if (len(self.transitRoutes[t].nodeSequence) > 0 and
                                            abs(self.transitRoutes[t].nodeSequence[-1]) == self.linksDict[link].toNode.nodeId):
                                            nodeToAppend = -self.linksDict[link].fromNode.nodeId

                                else:   # open in both directions
                                    if (len(self.transitRoutes[t].nodeSequence) > 0):
                                        # determine direction based on the previous node in the sequence. If the previous
                                        # node is the same as this link's from node, append the toNode; otherwise append the fromNode.
                                        if (abs(self.transitRoutes[t].nodeSequence[-1]) == \
                                            self.linksDict[link].fromNode.nodeId):
                                            nodeToAppend = -self.linksDict[link].toNode.nodeId
                                        elif (abs(self.transitRoutes[t].nodeSequence[-1]) == \
                                            self.linksDict[link].toNode.nodeId):
                                            nodeToAppend = -self.linksDict[link].fromNode.nodeId
                                        # previous link doesn't connect to this because the previous link was a duplicate
                                        else:
                                            self.transitRoutes[t].nodeSequence.pop()
                                            if (len(self.transitRoutes[t].nodeSequence) > 0):
                                                # remove the last node in the sequence and check if the one before connects to this one
                                                if (abs(self.transitRoutes[t].nodeSequence[-1]) == \
                                                    self.linksDict[link].fromNode.nodeId):
                                                    nodeToAppend = -self.linksDict[link].toNode.nodeId
                                                elif (abs(self.transitRoutes[t].nodeSequence[-1]) == \
                                                    self.linksDict[link].toNode.nodeId):
                                                    nodeToAppend = -self.linksDict[link].fromNode.nodeId

                            # if the node is a stop on this route, set the node ID positive
                            if (nodeToAppend != -1):
                                if (i > 0 and abs(nodeToAppend) in [st.tanaNode for st in self.stopsByRoute[t]]):
                                    nodeToAppend = -1 * nodeToAppend
                                self.transitRoutes[t].nodeSequence.append(nodeToAppend)
                            prevLinkId = link
                        
                            i += 1
                    # if the last node is not a stop, remove it
                    if (len(self.transitRoutes[t].nodeSequence) > 0 and self.transitRoutes[t].nodeSequence[-1] < 0):
                        del(self.transitRoutes[t].nodeSequence[-1])
                    
                # if there are no links for the route, just record the stops as the nodes
                else:
                    self.transitRoutes[t].nodeSequence = [n.tanaNode for n in self.stopsByRoute[t] if n.tanaNode != -1]
                
                # Only write routes with a node sequence.
                if (len(self.transitRoutes[t].nodeSequence) > 0):
                    lines.append(self.__getPrintString(t, PublicTransit.LINE_FILE_TYPE) + os.linesep)
                else:
                    print "No node sequence for " + str(t) + " (" + self.transitRoutes[t].new_name + ")"
        f.writelines(lines)
        f.close()


    def __getDistance(self, p1x, p1y, p2x, p2y):
        return math.sqrt(math.pow(p1x - p2x, 2.0) + math.pow(p1y - p2y, 2.0))


    def __getIdHash(self, val):
        """Returns the last seven digits of a TeleAtlas node and adds the TANA_NODE_NUMBER_OFFSET to the node number.
        
        Keyword arguments:
        val -- raw TeleAtlas node number (should be 14 digits in length)
        
        Return type:
        int -- last seven digits of val with TANA_NODE_NUMBER_OFFSET added to it
        
        """
        return PublicTransit.TANA_NODE_NUMBER_OFFSET + int(("%1.0f" % val)[7:])


    def __getPrintString(self, t, lineType):
        """Creates a PTLINE or TRNBUILD print string for a TransitRoute.
        
        Keyword arguments:
        t: route name identifier string (route concatenated with pattern, separated by an underscore)
        lineType: a LineFileType enumerator indicating which type of line file to write
        
        Return type:
        str: a single transit line print string
        
        """
        printStr = ""
        if (lineType == LineFileType.PTLINE):
            #printStr = "LINE NAME=\"" + self.transitRoutes[t].name  + "\" " + \
            printStr = "LINE NAME=\"" + self.transitRoutes[t].new_name  + "\" " + \
                "MODE=" +  str(self.transitRoutes[t].mode) + " " + \
                "ONEWAY=T " + \
                "LONGNAME=\"\" " + \
                "XYSPEED=15 " + \
                "USERA1=\"" + self.transitRoutes[t].agency + "\" " + \
                "USERA2=\"" + self.transitRoutes[t].mode_group + "\" " + \
                "FREQ[1]=" + str(self.transitRoutes[t].eaHeadway) + " " + \
                "FREQ[2]=" + str(self.transitRoutes[t].amHeadway) + " " + \
                "FREQ[3]=" + str(self.transitRoutes[t].mdHeadway) + " " + \
                "FREQ[4]=" + str(self.transitRoutes[t].pmHeadway) + " " + \
                "FREQ[5]=" + str(self.transitRoutes[t].evHeadway) + " " + \
                "N=" + ",".join([str(p) for p in self.transitRoutes[t].nodeSequence])
                #"OPERATOR=\"" + self.transitRoutes[t].agency + "\" "
        elif (lineType == LineFileType.TRNBUILD):
            #printStr = "LINE NAME=\"" + self.transitRoutes[t].name  + "\", " + \
            printStr = "LINE NAME=\"" + self.transitRoutes[t].new_name  + "\", " + \
                "USERA1=\"" + self.transitRoutes[t].agency + "\", " + \
                "USERA2=\"" + self.transitRoutes[t].mode_group + "\", " + \
                "MODE=" +  str(self.transitRoutes[t].mode) + ", " + \
                "ONEWAY=T, " + \
                "XYSPEED=15, " + \
                "HEADWAY[1]=" + str(self.transitRoutes[t].eaHeadway) + ", " + \
                "HEADWAY[2]=" + str(self.transitRoutes[t].amHeadway) + ", " + \
                "HEADWAY[3]=" + str(self.transitRoutes[t].mdHeadway) + ", " + \
                "HEADWAY[4]=" + str(self.transitRoutes[t].pmHeadway) + ", " + \
                "HEADWAY[5]=" + str(self.transitRoutes[t].evHeadway) + ", " + \
                "N=" + ",".join([str(p) for p in self.transitRoutes[t].nodeSequence])
        return printStr


    def saveData(self):
        """
        Serialize the nodes, links, stops, and routes.
        """    
        self.spIndex.close()
        output = open(PublicTransit.PICKLE_SAVE_FILE, 'wb')        
        # cPickle the list using the highest protocol available.
        cPickle.dump(self.nodesDict, output, -1)
        cPickle.dump(self.linksDict, output, -1)
        cPickle.dump(self.stopsByRoute, output, -1)
        cPickle.dump(self.stopsByNode, output, -1)
        cPickle.dump(self.routeXref, output, -1)
        cPickle.dump(self.transitRoutes, output, -1)
        output.close()
        self.spIndex = index.Index(PublicTransit.SPATIAL_INDEX_FILE)
        
    def loadData(self):
        """
        De-serializes a PublicTransit instance, setting nodesDict, linksDict,
        stopsByRoute, stopsByNode, routeXref, transitRoutes, and spIndex.
        """
        infile = open(PublicTransit.PICKLE_SAVE_FILE, 'rb')
        self.nodesDict = cPickle.load(infile)
        self.linksDict = cPickle.load(infile)
        self.stopsByRoute = cPickle.load(infile)
        self.stopsByNode = cPickle.load(infile)
        self.routeXref = cPickle.load(infile)
        self.transitRoutes = cPickle.load(infile)
        infile.close()
        self.spIndex = index.Index(PublicTransit.SPATIAL_INDEX_FILE)
        #last step is to reconcile all of the nodes into single objects
        #use routePattern dictionary as the master
        self.stopsDict = {}
        for routePattern in self.stopsByRoute:
            for stop in self.stopsByRoute[routePattern]:
                if stop.stopPointId in self.stopsDict:
                    self.stopsDict[stop.stopPointId].append(stop)
                else:
                    self.stopsDict[stop.stopPointId] = [stop]
                if stop.tanaNode in self.stopsByNode:
                    for i in range(len(self.stopsByNode[stop.tanaNode])):
                        nodeStop = self.stopsByNode[stop.tanaNode][i]
                        if nodeStop.basicEqual(stop):
                            self.stopsByNode[stop.tanaNode][i] = stop

    def writeNetwork(self,nodeFile,linkFile):
        """
        Write the nodes and links to file.
        """
        f = open(nodeFile,"wb")
        f.write("nodeId,x,y" + os.linesep)
        for id,point in self.nodesDict.iteritems():
            f.write(",".join(map(str,(point.nodeId,point.x,point.y))) + os.linesep)
        f.close()
        
        f = open(linkFile,"wb")
        f.write("fromNode,toNode,linkId,oneWay" + os.linesep)
        for id,link in self.linksDict.iteritems():
            if link.oneWay == "FT":
                oneWay = 1
            if link.oneWay == "TF":
                oneWay = -1
            else:
                oneWay = 0
            f.write(",".join(map(str,(link.fromNode.nodeId,link.toNode.nodeId,link.linkId,oneWay))) + os.linesep)
        f.close()
        
    def __setTapDataStructures(self):
        self.stopsToKeep = []
        self.stopsToKeepIds = []
        
    def setStopsByDistance(self,threshold_by_density,mode,stop_usage,stop_density_buffer):
        #iterate through all routes, and keep just those stops 
        # that aren't within [threshold] of any other
        # if shared stops happen to be closer than this, we
        # will just let it happen
        
        stopDensities = self.createStopDensity(stop_density_buffer)
        thresholds = []
        for threshold in threshold_by_density:
            thresholds.append(threshold)
        thresholds.sort()
        nthresholds = {}
        for stop_id in stopDensities:
            density = stopDensities[stop_id]
            for threshold in thresholds:
                t = threshold_by_density[threshold]
                if density < threshold:
                    break
            nthresholds[stop_id] = t
        
        stopsToKeepMap = {}
        stopsToKeepIdsMap = {} #just to be a set
        stopToStopMap = {} #stop to stop that will be kept mapping
        
        #initialize with what has already been done
        for stopId in self.stopsToKeepIds:
            stopsToKeepIdsMap[stopId] = None
        skip_count = 0
        for routePattern in self.stopsByRoute:
            if self.transitRoutes[routePattern].mode != mode:
                continue
            lastStopPoint = None
            lastStopId = None
            lastStop = None
            distanceToLastStop = None
            lastTrueStopId = None
            lastTrueStop = None
            lastTrueStopPoint = None
            for stop in self.stopsByRoute[routePattern]:
                if stop.tanaNode in self.nodesDict:
                    stopId = stop.stopPointId
                    usage = stop_usage[stopId]
                    thresh = nthresholds[stopId] / math.sqrt(usage)
                    stopPoint = self.nodesDict[stop.tanaNode]
                    if not stopId in stopsToKeepMap:
                        stopsToKeepMap[stopId] = (stopId in stopsToKeepIdsMap)
                    if (lastStopPoint is None): #first stop is included
                        stopsToKeepMap[stopId] = True 
                    elif self.__getDistance(stopPoint.x,stopPoint.y,lastStopPoint.x,lastStopPoint.y) >= thresh:
                        stopsToKeepMap[stopId] = True
                    if stopsToKeepMap[stopId]: 
                        stopToStopMap[stopId] = [stopId]
                        lastStopPoint = stopPoint
                        lastStopId = stopId
                        lastStop = stop
                        if not stopId in stopsToKeepIdsMap:
                            #add to structures, if necessary
                            stopsToKeepIdsMap[stopId] = None
                            self.stopsToKeepIds.append(stopId)
                            #self.stopsToKeep.append(self.stopsByNode[stop.tanaNode][0])
                            self.stopsToKeep.append(stop)
                        #distanceToLastStop = None #only store distance if last stop not kept
                    elif (not stopId in stopToStopMap) or (stopToStopMap[stopId][0] != stopId):
                        #distanceToLastStop = self.__getDistance(stopPoint.x,stopPoint.y,lastStopPoint.x,lastStopPoint.y)
                        if not stopId in stopToStopMap:
                            stopToStopMap[stopId] = []
                        if not lastStopId in stopToStopMap[stopId]:
                            stopToStopMap[stopId].append(lastStopId)
                    lastTrueStopId = stopId
                    lastTrueStop = stop
                    lastTrueStopPoint = stopPoint
            if not stopsToKeepMap[lastTrueStopId]: #add last stop, if it wasn't already
                if not lastTrueStopId in stopsToKeepIdsMap:
                    #add to structures, if necessary
                    self.stopsToKeepIds.append(lastTrueStopId)
                    #self.stopsToKeep.append(self.stopsByNode[lastTrueStop.tanaNode][0])
                    self.stopsToKeep.append(lastTrueStop)
                    stopToStopMap[lastTrueStopId] = [lastTrueStopId]
                    stopsToKeepIdsMap[lastTrueStopId] = True
        self.stopToStopByMode[mode] = stopToStopMap
        
    def setPremiumStopAsTap(self,mode):
        #keep premium stops
        stopsToKeepIdsMap = {} #just to be a set
        stopToStopMap = {}
        #initialize with what has already been done
        for stopId in self.stopsToKeepIds:
            stopsToKeepIdsMap[stopId] = None
            
        for routePattern in self.stopsByRoute:
            if self.transitRoutes[routePattern].mode != mode:
                continue
            if not self.isModeLocal(self.transitRoutes[routePattern].mode):
                for stop in self.stopsByRoute[routePattern]:
                    if stop.tanaNode in self.nodesDict:
                        stopId = stop.stopPointId
                        if not stopId in stopsToKeepIdsMap:
                            stopsToKeepIdsMap[stopId] = None
                            self.stopsToKeepIds.append(stopId)
                            #self.stopsToKeep.append(self.stopsByNode[stop.tanaNode][0])
                            self.stopsToKeep.append(stop)
                            stopToStopMap[stopId] = [stopId]
        self.stopToStopByMode[mode] = stopToStopMap
                        
                        
    def createStopDensity(self,bufferInFeet):
        stopDensities = {}
        idx = index.Index()
        allStops = []
        for node in self.stopsByNode:
            for stop in self.stopsByNode[node]:
                if stop.tanaNode in self.nodesDict:
                    allStops.append(stop)
                    node = self.nodesDict[stop.tanaNode]
                    idx.insert(stop.stopPointId,(node.x,node.y,node.x,node.y))
        for stop in allStops:
            node = self.nodesDict[stop.tanaNode]
            stopsInBuffer = list(idx.intersection((node.x - bufferInFeet,node.y - bufferInFeet,
                                                        node.x + bufferInFeet,node.y + bufferInFeet)))
            stopDensities[stop.stopPointId] = len(stopsInBuffer) #include self, for simplicity
        return stopDensities
        
                      
    def condenseStops(self,bufferInFeet,mode):
        allStops = []
        for node in self.stopsByNode:
            stop = self.stopsByNode[node][0]
            if stop.tanaNode in self.nodesDict:
                allStops.append(stop)
            
        stopToStopReverse = {}
        for stopId in self.stopToStopByMode[mode]:
            counter = 0
            for ot in self.stopToStopByMode[mode][stopId]:
                if not ot in stopToStopReverse:
                    stopToStopReverse[ot] = []
                stopToStopReverse[ot].append((counter,stopId))
                counter += 1
    
        stops = self.stopsToKeep
        finalStops = {}
        condensedStops = {}
        idx = index.Index()
        for stop in stops:
            node = self.nodesDict[stop.tanaNode]
            idx.insert(stop.stopPointId,(node.x,node.y,node.x,node.y))
        for stop in stops:
            stopPointId = stop.stopPointId
            if stopPointId in condensedStops:
                continue
            finalStops[stopPointId] = stop #add to final set
            condensedStops[stopPointId] = stop
            node = self.nodesDict[stop.tanaNode]
            stopsInBuffer = list(idx.intersection((node.x - bufferInFeet,node.y - bufferInFeet,
                                                        node.x + bufferInFeet,node.y + bufferInFeet)))
            for otherStop in stopsInBuffer:
                if not otherStop in condensedStops:
                    condensedStops[otherStop] = stop
                    self.stopToStopByMode[mode][otherStop] = [stopPointId] #move it, and then move all of the others pointing to it as well
                    for otherOtherStop in stopToStopReverse[otherStop]:
                        self.stopToStopByMode[mode][otherOtherStop[1]][otherOtherStop[0]] = stopPointId
                    stopToStopReverse[stopPointId] += stopToStopReverse[otherStop]
                    stopToStopReverse[otherStop] = []
                    #for otherOtherStop in self.stopToStopByMode[mode]:
                    #    if self.stopToStopByMode[mode][otherOtherStop] == otherStop:
                    #        self.stopToStopByMode[mode][otherOtherStop] == stopPointId
        self.__setTapDataStructures()
        for stopPointId in finalStops:
            self.stopsToKeep.append(finalStops[stopPointId])
            self.stopsToKeepIds.append(stopPointId)
            
    
    def isModeLocal(self,mode):
        return mode <= Mode.EXPRESS_BUS
    
    def analyzeStops(self):
        self.stopsToKeepByMode = {}
        self.stopsToKeepIdsByMode = {}
        self.stopToStopByMode = {}
        stop_usage = {}
        modes = [Mode.LOCAL_BUS,Mode.EXPRESS_BUS,Mode.FERRY,Mode.LIGHT_RAIL,Mode.HEAVY_RAIL,Mode.COMMUTER_RAIL]
        
        
        for routePattern in self.stopsByRoute:
            for stop in self.stopsByRoute[routePattern]:
                if stop.tanaNode in self.nodesDict:
                    stopId = stop.stopPointId
                    if not stopId in stop_usage:
                        stop_usage[stopId] = 0
                    stop_usage[stopId] = stop_usage[stopId] + 1
        
        mode_thresholds = {}
        for mode in modes:
            if mode == Mode.LOCAL_BUS:
                mode_thresholds[mode] = {5:5280*1.0,15:5280*0.66,30:5280*0.5,50:5280*.33}
                #mode_thresholds[mode] = {2:5280*1.0,5:5280*0.66,10:5280*0.5,50:5280*.33}
            elif mode == Mode.EXPRESS_BUS:
                mode_thresholds[mode] = {15:5280*0.5,25:5280*0.33}
        for mode in modes:
            self.__setTapDataStructures()
            if self.isModeLocal(mode):
                self.setStopsByDistance(mode_thresholds[mode],mode,stop_usage,5280*.25) #1/4 mile
            else:
                self.setPremiumStopAsTap(mode)
            self.condenseStops(5280/8.0,mode)
            self.stopsToKeepByMode[mode] = self.stopsToKeep
            self.stopsToKeepIdsByMode[mode] = self.stopsToKeepIds

            
        
    def getCounties(self,stops,counties):
        arcpy.env.workspace = PublicTransit.TAZ_SHAPEFILE_PATH
        tmp = "in_memory\\temp"
        ptlyr = "ptlyr"
        if arcpy.Exists(tmp):
            arcpy.Delete_management(tmp)
            arcpy.Delete_management(ptlyr)
        arcpy.CreateFeatureclass_management("in_memory","temp","POINT",spatial_reference="AlamedaTAZ.shp")
        arcpy.AddField_management (tmp,"tanaNode","LONG")
        cur = arcpy.InsertCursor(tmp)
        
        for stop in stops:
            feat = cur.newRow()
            feat.shape = arcpy.Point(self.nodesDict[stop.tanaNode].x,self.nodesDict[stop.tanaNode].y)
            feat.tanaNode = stop.tanaNode
            cur.insertRow(feat)
        arcpy.MakeFeatureLayer_management(tmp,ptlyr)
        
        county_groups = {}
        count = 0
        for county in counties:
            resource = county.replace(" ","") + "TAZ.shp"
            lyr = resource + "_lyr"
            if not arcpy.Exists(lyr):
                arcpy.MakeFeatureLayer_management(resource,lyr)
            #arcpy.SelectLayerByLocation_management(ptlyr,overlap_type="WITHIN_A_DISTANCE",select_features=lyr,search_distance=50)
            arcpy.SelectLayerByLocation_management(ptlyr,overlap_type="COMPLETELY_WITHIN",select_features=lyr)
            for row in arcpy.SearchCursor(ptlyr,"","","tanaNode"):
                county_groups[row.tanaNode] = county
                count += 1
        for county in counties:
            resource = county.replace(" ","") + "TAZ.shp"
            lyr = resource + "_lyr"
            arcpy.SelectLayerByLocation_management(ptlyr,overlap_type="WITHIN_A_DISTANCE",select_features=lyr,search_distance=50)
            for row in arcpy.SearchCursor(ptlyr,"","","tanaNode"):
                if not row.tanaNode in county_groups:
                    county_groups[row.tanaNode] = county
                    count += 1
        return county_groups
        
    def getNewPoint(self,x,y,used_points):
        shifts = [1,-1,0]
        for xshift in shifts:
            for yshift in shifts:
                point = (x+xshift,y+yshift)
                if not point in used_points:
                    used_points[point] = None
                    return point
        return self.getNewPoint(x+1,y+1,used_points) #try from a new point
        
    def buildTaps(self):
        county_offset = 100000
        tap_offset = 90000
        counties = ["Alameda","Contra Costa","Marin","Napa","San Francisco","San Mateo","Santa Clara","Solano","Sonoma"]
        tap_number_by_county = {}
        county_index = {}
        counter = 0
        for county in counties:
            county_index[county] = counter
            tap_number_by_county[county] = 1 #current (non-offset) tap number
            counter += 1
        #build stopid to nodeid mapping
        stopIdToNodeIdMap = {}
        stopIdToCoord = {}
        
        for node in self.stopsByNode:
            for stop in self.stopsByNode[node]:
                if stop.tanaNode in self.nodesDict:
                    stopIdToNodeIdMap[stop.stopPointId] = self.nodesDict[stop.tanaNode].nodeId
                    stopIdToCoord[stop.stopPointId] = (self.nodesDict[stop.tanaNode].x,self.nodesDict[stop.tanaNode].y)
                  
    
        tap_points = {} # to hold used tap points
        stopIdToTapIdMap = {}
        stopIdToTapXY = {}
        #first build taps
        #tap_header = ["x","y","county","n","mode"]
        tap_lines = []
        for mode in self.stopsToKeepByMode:
            stopIdToTapIdMap[mode] = {}
            stopIdToTapXY[mode] = {}
            county_groups = self.getCounties(self.stopsToKeepByMode[mode],counties)
            for stop in self.stopsToKeepByMode[mode]:
                point = self.getNewPoint(self.nodesDict[stop.tanaNode].x,self.nodesDict[stop.tanaNode].y,tap_points)
                x = point[0]
                y = point[1]
                county = county_groups[stop.tanaNode]
                tapId = county_offset*county_index[county] + tap_offset + tap_number_by_county[county]
                tap_number_by_county[county] = tap_number_by_county[county] + 1
                nl = map(str,[x,y,county_index[county]+1,tapId,mode])
                for i in range(len(nl)):
                    nl[i] = nl[i].rjust(15)
                tap_lines.append("".join(nl))
                stopIdToTapIdMap[mode][stop.stopPointId] = tapId
                stopIdToTapXY[mode][stop.stopPointId] = (x,y)
                
        #node_header = ["nodeId","tapId","distance"]
        node_lines = []
        for mode in self.stopToStopByMode:
            for stopId in self.stopToStopByMode[mode]:
                if stopId in stopIdToNodeIdMap:
                    for sstop in self.stopToStopByMode[mode][stopId]:
                        tapId = stopIdToTapIdMap[mode][sstop]
                        tapCoord = stopIdToTapXY[mode][sstop]
                        nodeId = stopIdToNodeIdMap[stopId]
                        nodecoord = stopIdToCoord[stopId]
                        distance = self.__getDistance(tapCoord[0],tapCoord[1],nodecoord[0],nodecoord[1])
                        nl = map(str,[nodeId,tapId,distance])
                        for i in range(len(nl)):
                            nl[i] = nl[i].rjust(15)
                        node_lines.append("".join(nl))
                        nl = map(str,[tapId,nodeId,distance])
                        for i in range(len(nl)):
                            nl[i] = nl[i].rjust(15)
                        node_lines.append("".join(nl))
                        
        f = open(PublicTransit.TAPS_FILE_NAME,"wb")
        for line in tap_lines:
            f.write(line + os.linesep)
        f.close()
        f = open(PublicTransit.NODE_TO_TAP_FILE_NAME,"wb")
        for line in node_lines:
            f.write(line + os.linesep)
        f.close()
