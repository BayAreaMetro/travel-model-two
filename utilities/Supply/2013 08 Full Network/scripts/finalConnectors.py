
#Build final TAZ connectors
#"C:\Python27\ArcGIS10.1\python.exe" finalConnectors.py

import math
import os
from dbfpy import dbf
from rtree import index
import csv

NODE_DBF_FILE          = "C:/Users/stabler/Desktop/tazs/temp4_nodes.dbf" #deliverable 031913 network
LINK_DBF_FILE          = "C:/Users/stabler/Desktop/tazs/temp4_links.dbf"
CONNECTORS_FILE        = "C:/Users/stabler/Desktop/tazs/connectorsTAZFinal.txt"
COUNTY_OFFSET          = 100000    # Node numbering county offset
MAX_CONNECTORS         = 8
TANA_OFFSET            = 3000000

# Read DBF file of TANA network shape file with unconnected TAZ and MAZ
# centroids links. Use this to determine which nodes are not eligible for
# consideration in building connectors.
linksDb = dbf.Dbf(LINK_DBF_FILE)
print "Reading links"

tazDist = dict()
for rec in linksDb:

    #assignable links
    if rec["CNTYPE"] == "TAZ":
      
      a = rec["A"]
      b = rec["B"]
      vol = rec["V_1"]
      if a < TANA_OFFSET: #tana node
        zone = a
        cnode = b
      else:
        zone = b
        cnode = a
      
      if zone not in tazDist:
        tazDist[zone] = dict()
      
      tazDist[zone][cnode] = vol
      
# get nodes
nodeXY = dict()
nodesDb = dbf.Dbf(NODE_DBF_FILE)
for rec in nodesDb:
    n = rec["N"]
    xCoord = rec["X"]
    yCoord = rec["Y"]
    countyN = rec["COUNTY_N"] #to get back to original TAZ numbers
    nodeXY[n] = [xCoord,yCoord,countyN]
    
#create connector file
outFile = open(CONNECTORS_FILE, "wb")

lines = []
#Iterate through tazs
for zone in tazDist:

    # get nodes
    nodesDict = tazDist[zone]
    numNodes= len(nodesDict)
    nodesSorted = list()
    for i in sorted(nodesDict,key=nodesDict.get):
      nodesSorted.append(i)
    
    #write out N most used
    for i in range(0, min(numNodes, MAX_CONNECTORS)):
      distance = math.sqrt(math.pow(nodeXY[zone][0] - nodeXY[nodesSorted[i]][0], 2.0) + math.pow(nodeXY[zone][1] - nodeXY[nodesSorted[i]][1], 2.0))
      lines.append("%i,%i,%f,%i,%i%s" % (zone, nodesSorted[i], distance, nodeXY[zone][2], nodesSorted[i], os.linesep))
      lines.append("%i,%i,%f,%i,%i%s" % (nodesSorted[i], zone, distance, nodesSorted[i], nodeXY[zone][2], os.linesep))

#write lines
outFile.writelines(lines)
outFile.close()