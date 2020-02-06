
#Builds text file of TAZ connectors used as input to Cube
#"C:\Python27\ArcGIS10.1\python.exe" buildConnectorsTAZAll.py

import math
import os
from dbfpy import dbf
from rtree import index
import csv

NODE_DBF_FILE          = "C:/Users/stabler/Desktop/tazs/nodes.dbf" #deliverable 031913 network
LINK_DBF_FILE          = "C:/Users/stabler/Desktop/tazs/links.dbf"
TAZ_VERTICES_FILE      = "C:/Users/stabler/Desktop/tazs/TAZVertices.csv"
CONNECTORS_FILE        = "C:/Users/stabler/Desktop/tazs/connectorsTAZ.txt"
COUNTY_OFFSET          = 100000    # Node numbering county offset
counties = ["Sonoma","Solano","SantaClara","SanMateo","SanFrancisco","Napa","Marin","ContraCosta","Alameda"]
countyCodes = [9,8,7,6,5,4,3,2,1] #need to update these later

def main():

    # Read DBF file of TANA network shape file with unconnected TAZ and MAZ
    # centroids links. Use this to determine which nodes are not eligible for
    # consideration in building connectors.
    linksDb = dbf.Dbf(LINK_DBF_FILE)
    print "Reading links and building exclude list"
    tazExcludeSet = set()
    assignableDict = dict()       # dictionary of nodes: key = node, value = assignable
    tanaNodesFTs = dict()
    
    for rec in linksDb:

        #assignable links
        if (rec["A"] in assignableDict):
            assignableDict[rec["A"]].append(rec["ASSIGNABLE"])
        else:
            assignableDict[rec["A"]] = [rec["ASSIGNABLE"]]
        
        if (rec["B"] in assignableDict):
            assignableDict[rec["B"]].append(rec["ASSIGNABLE"])
        else:
            assignableDict[rec["B"]] = [rec["ASSIGNABLE"]]
            
        #FT 0	Connector, 1	Freeway to Freeway, 2	Freeway, 3	Expressway, 4	Collector, 5	Ramp, 7	Major Arterial
        if (rec["A"] in tanaNodesFTs):
            tanaNodesFTs[rec["A"]].append(rec["FT"])
        else:
            tanaNodesFTs[rec["A"]] = [rec["FT"]]
            
        if (rec["B"] in tanaNodesFTs):
            tanaNodesFTs[rec["B"]].append(rec["FT"])
        else:
            tanaNodesFTs[rec["B"]] = [rec["FT"]]
    
    tazExcludeSet = tazExcludeSet.union(set([i for i in assignableDict.keys() if sum(assignableDict[i]) == 0]))
    tanaNodes = dict()
    taz = dict()
    
    # Create spatial indexes for TAZ candidate nodes.
    spIndexTaz = index.Index()
    TazVerticesDict = dict()
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
            if (n not in tazExcludeSet):   # TAZ records
              if 4 in tanaNodesFTs[n] or 7 in tanaNodesFTs[n]: #Ensure has a collector or major arterial
                spIndexTaz.insert(n, (xCoord, yCoord, xCoord, yCoord))
        else:
            taz[n] = (xCoord, yCoord)
            TazVerticesDict[n] = []

    #Read taz vertices
    taz_verts = []
    with open(TAZ_VERTICES_FILE, 'rb') as csvfile:
      tazvertreader = csv.reader(csvfile, skipinitialspace=True)
      for row in tazvertreader:
        taz_verts.append(row)
    taz_verts_col_names = taz_verts.pop(0)

    # Assign each TAZ vertex to a network node
    tazv_univ_ids = set()
    print "Assign each TAZ vertex to a network node"
    for rec in taz_verts:
        county = str(rec[0])
        tazv = int(rec[1])
        xCoord = float(rec[2])
        yCoord = float(rec[3])
        
        countyCode = countyCodes[counties.index(county)]
        tazv_univ = (countyCode-1) * COUNTY_OFFSET + tazv
        tazv_univ_ids.add(tazv_univ)        
        nearestNode = list(spIndexTaz.nearest( (xCoord,yCoord,xCoord,yCoord),1))[0]
        
        #for debugging
        rec.append(countyCode)
        rec.append(tazv_univ)
        rec.append(nearestNode)

        #add to spatial index for taz 
        xcoord = tanaNodes[nearestNode][0]
        ycoord = tanaNodes[nearestNode][1]
        TazVerticesDict[tazv_univ].append([nearestNode, xcoord, ycoord])

    #create connector file
    outFile = open(CONNECTORS_FILE, "wb")
    
    lines = []
    #Iterate through tazs
    for zone in tazv_univ_ids:
    
        #create nodes list for taz
        nodes = set()
        for i in TazVerticesDict[zone]:
          nodes.add(i[0])
        nodes = list(nodes)
          
        # Calculate the distance for each new connector, and write to/from, from/to to make link bidirectional. 
        for i in range(0, len(nodes)):
          distance = math.sqrt(math.pow(taz[zone][0] - tanaNodes[nodes[i]][0], 2.0) + math.pow(taz[zone][1] - tanaNodes[nodes[i]][1], 2.0))
          lines.append(str(zone) + "," + str(nodes[i]) + "," + str(distance) + os.linesep)
          lines.append(str(nodes[i]) + "," + str(zone) + "," + str(distance) + os.linesep)
    
    #write lines
    outFile.writelines(lines)
    outFile.close()

if __name__ == '__main__':
    main()
