"""
Builds text file of MAZ connectors used as input by Cube to generate new links. 
MAZ connectors are created by loading the TANA links DBF and nodes DBF
"C:\Python26\ArcGIS10.0\python.exe" buildConnectorsMAZ.py
"""

import math
import os
from dbfpy import dbf
from rtree import index

NODE_DBF_FILE          = "C:/projects/mtc/tana_sp_with_maz_taz_nodes.dbf"
LINK_DBF_FILE          = "C:/projects/mtc/tana_sp_with_maz_taz_links.dbf"
CONNECTORS_FILE        = "C:/projects/mtc/connectorsMAZ.txt"

NUM_NEAREST_NODES_MAZ  = 2         # number of nearest network nodes to use for creating MAZ connectors
COUNTY_OFFSET          = 100000    # Node numbering county offset
MAZ_OFFSET             = 10000     # Within-county MAZ offset (e.g. 10,000 - 99999, 110,000 - 199,999, etc.)


def main():
    # Read DBF file of TANA network shape file with unconnected TAZ and MAZ
    # centroids links. Use this to determine which nodes are not eligible for
    # consideration in building connectors.
    linksDb = dbf.Dbf(LINK_DBF_FILE)
    print "Reading links and building exclude list"
    mazExcludeSet = set()         # Use a set to prevent inserting duplicate nodes
    assignableDict = dict()       # dictionary of nodes: key = node, value = assignable
    
    for rec in linksDb:
        # If the link is a freeway or ferry add the A node to the MAZ exclude list.
        if (rec["FREEWAY"] == 1 or rec["FT"] != 0):
            mazExcludeSet.add(rec["A"])
        if (rec["A"] in assignableDict):
            assignableDict[rec["A"]].append(rec["ASSIGNABLE"])
        else:
            assignableDict[rec["A"]] = [rec["ASSIGNABLE"]]
    
    tanaNodes = dict()
    maz = dict()
    
    # Create spatial indexes for MAZ candidate nodes.
    spIndexMaz = index.Index()
    print "Reading nodes and creating spatial index"
        
    # Iterate through the nodes and add TANA nodes to the spatial indexes if
    # they are not in the exclude sets.
    nodesDb = dbf.Dbf(NODE_DBF_FILE)
    for rec in nodesDb:
        n = rec["N"]
        xCoord = rec["X"]
        yCoord = rec["Y"]
        if (rec["COUNTY"] == 0):
            tanaNodes[n] = (xCoord, yCoord)
            if (n not in mazExcludeSet):     # MAZ records
                spIndexMaz.insert(n, (xCoord, yCoord, xCoord, yCoord))
        else:
            maz[n] = (xCoord, yCoord)

    outFile = open(CONNECTORS_FILE, "wb")
    print "Evaluating nearest..."
    
    lines = []
    # Iterate through maz dict and find the nearest neighbors for each.
    # Use appropriate sptial index based on which nodes were excluded for
    # use in connectors.
    for zone in maz:
        if not (zone % COUNTY_OFFSET < MAZ_OFFSET):
          nearestNodes = list(spIndexMaz.nearest((maz[zone][0], maz[zone][1], maz[zone][0], maz[zone][1]), NUM_NEAREST_NODES_MAZ))
        
          # Calculate the distance for each new connector, and write to/from, from/to to make link bidirectional. 
          for i in range(0, len(nearestNodes)):
            distance = math.sqrt(math.pow(maz[zone][0] - tanaNodes[nearestNodes[i]][0], 2.0) + math.pow(maz[zone][1] - tanaNodes[nearestNodes[i]][1], 2.0))
            lines.append(str(zone) + "," + str(nearestNodes[i]) + "," + str(distance) + os.linesep)
            lines.append(str(nearestNodes[i]) + "," + str(zone) + "," + str(distance) + os.linesep)
    outFile.writelines(lines)
    outFile.close()


if __name__ == '__main__':
    main()
