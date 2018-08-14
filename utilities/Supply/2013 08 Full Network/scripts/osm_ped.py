
#Builds text file of OSM ped links to add to Cube
#"C:\Python26\ArcGIS10.0\python.exe" osm_ped.py
#Ben Stabler, stabler@pbworld.com, 04/17/13

############################################################

NODE_DBF_FILE      = "D:/projects/mtc/networks/osm/tana_mtc_nodes.dbf"
LINK_DBF_FILE      = "D:/projects/mtc/networks/osm/tana_mtc_links.dbf"
OSM_NODE_DBF_FILE  = "D:/projects/mtc/networks/osm/osm_nodes_sp.dbf"
OSM_LINK_DBF_FILE  = "D:/projects/mtc/networks/osm/osm_links_sp.dbf"
OSM_NODES_FILE     = "D:/projects/mtc/networks/osm/osm_nodes.txt"
OSM_LINKS_FILE     = "D:/projects/mtc/networks/osm/osm_links.txt"
SNAP_DIST_FEET     = 50
NEW_NODE_OFFSET    = 7000000

############################################################

import math
import os
from dbfpy import dbf
from rtree import index
import csv

print "Read TANA links and get link FT codes by node"
linksDb = dbf.Dbf(LINK_DBF_FILE)
tanaNodesFTs = dict()
for rec in linksDb:
    #build list of FT links for each node
    if (rec["A"] in tanaNodesFTs):
        tanaNodesFTs[rec["A"]].append(rec["FT"])
    else:
        tanaNodesFTs[rec["A"]] = [rec["FT"]]
    if (rec["B"] in tanaNodesFTs):
        tanaNodesFTs[rec["B"]].append(rec["FT"])
    else:
        tanaNodesFTs[rec["B"]] = [rec["FT"]]

print "Read nodes and add to index if any link FTs in [4,7]"
spIndexTANANodes = index.Index()
tanaNodes = dict()
nodesDb = dbf.Dbf(NODE_DBF_FILE)
for rec in nodesDb:
    n = rec["N"]
    xCoord = rec["X"]
    yCoord = rec["Y"]
    tanaNodes[n] = [xCoord,yCoord]
    if 4 in tanaNodesFTs[n] or 7 in tanaNodesFTs[n]:
      spIndexTANANodes.insert(n, (xCoord, yCoord, xCoord, yCoord))

print "Read OSM nodes"
new_node_id = NEW_NODE_OFFSET #renumber for later
osmNodes = dict()
nodesDb = dbf.Dbf(OSM_NODE_DBF_FILE)
for rec in nodesDb:
    n = rec["N"]
    xCoord = rec["X"]
    yCoord = rec["Y"]
    osmNodes[n] = [xCoord,yCoord,new_node_id]
    new_node_id = new_node_id + 1

print "Assign each OSM node the closest TANA node"
for n in osmNodes.keys():
    xCoord = float(osmNodes[n][0])
    yCoord = float(osmNodes[n][1])
    nearestNode = list(spIndexTANANodes.nearest( (xCoord,yCoord,xCoord,yCoord),1))[0]
    distance = math.sqrt(math.pow(xCoord - tanaNodes[nearestNode][0], 2.0) + math.pow(yCoord - tanaNodes[nearestNode][1], 2.0))
    osmNodes[n].append(nearestNode)
    osmNodes[n].append(distance)

print "Read OSM links and replace with snapped TANA node if within radius"
lines = []
osmLinks = dict()
osmNewNodes = dict()
linksDb = dbf.Dbf(OSM_LINK_DBF_FILE)
for rec in linksDb:

    #if both nodes snapped to the same node, only take closest
    useA = True
    useB = True
    if osmNodes[rec["A"]][4] < SNAP_DIST_FEET and osmNodes[rec["B"]][4] < SNAP_DIST_FEET:
      if osmNodes[rec["A"]][3] == osmNodes[rec["B"]][3]:
        if osmNodes[rec["A"]][4] > osmNodes[rec["B"]][4]:
          useA = False
        else:
          useB = False

    if osmNodes[rec["A"]][4] < SNAP_DIST_FEET and useA:
      finalA = osmNodes[rec["A"]][3] #nearest node
      aX = tanaNodes[finalA][0]
      aY = tanaNodes[finalA][1]
    else:
      finalA = osmNodes[rec["A"]][2] #renumbered node
      osmNewNodes[finalA] = finalA
      aX = osmNodes[rec["A"]][0]
      aY = osmNodes[rec["A"]][1]

    if osmNodes[rec["B"]][4] < SNAP_DIST_FEET and useB:
      finalB = osmNodes[rec["B"]][3] #nearest node
      bX = tanaNodes[finalB][0]
      bY = tanaNodes[finalB][1]
    else:
      finalB = osmNodes[rec["B"]][2] #renumbered node
      osmNewNodes[finalB] = finalB
      bX = osmNodes[rec["B"]][0]
      bY = osmNodes[rec["B"]][1]

    #write link
    feet = math.sqrt(math.pow(aX - bX, 2.0) + math.pow(aY - bY, 2.0))
    osmFlag = 1
    highwayT = rec["HighwayT"]
    lines.append("%i,%i,%f,%i,%s%s" % (finalA, finalB, feet, osmFlag, highwayT, os.linesep))
    
print "Create OSM link file"
outFile = open(OSM_LINKS_FILE, "wb")
outFile.writelines(lines) #A,B
outFile.close()

print "Create new OSM node file"
lines = []
for n in osmNodes.keys():
  
  xCoord = osmNodes[n][0]
  yCoord = osmNodes[n][1]
  newNode = osmNodes[n][2]
 
  #write node
  if newNode in osmNewNodes:
    lines.append("%i,%f,%f%s" % (newNode, xCoord, yCoord, os.linesep))
    
outFile = open(OSM_NODES_FILE, "wb")
outFile.writelines(lines) #N,X,Y
outFile.close()
