"""
Calculate MAZ Area Type Using Buffered Pop + Emp Density Measure
And Then Set Each Link Area Type to Nearest MAZ for Link A and B Node
python codeLinkAreaType.py model_directory
"""


import math, os, csv, sys
from rtree import index

model_run_dir = sys.argv[1]
MAZ_DATA_FILE = os.path.join(model_run_dir,r'landuse\maz_data.csv')
NODE_CSV_FILE = os.path.join(model_run_dir,r'hwy\mtc_final_network_with_tolls_nodes.csv')
LINK_CSV_FILE = os.path.join(model_run_dir,r'hwy\mtc_final_network_with_tolls_links.csv')
AREA_TYPE_FILE = os.path.join(model_run_dir,r'hwy\link_area_type.csv')
BUFF_DIST       = 5280 * 0.5

print "Reading MAZ data"
mazData = []
with open(MAZ_DATA_FILE, 'rb') as csvfile:
  mazreader = csv.reader(csvfile, skipinitialspace=True)
  for row in mazreader:
    mazData.append(row)
mazDataColNames = mazData.pop(0)

mazLandUse = dict()
origMazToSeqMaz = dict()
for row in mazData:
  maz = row[mazDataColNames.index("MAZ")]
  pop = row[mazDataColNames.index("POP")]
  emp = row[mazDataColNames.index("emp_total")]
  acres = row[mazDataColNames.index("ACRES")]
  mazLandUse[maz] = [maz, pop, emp, acres,-1,-1,-1] #-1,-1,-1 = x,y,area type
  
  #create sequential lookup to join to network
  orig_maz_id = row[mazDataColNames.index("MAZ_ORIGINAL")]
  origMazToSeqMaz[orig_maz_id] = maz

print "Reading nodes"
mazs = dict()
nodes = dict()
spIndexMaz = index.Index()
with open(NODE_CSV_FILE,'rb') as node_file:
  node_reader = csv.reader(node_file,skipinitialspace=True)
  for row in node_reader:
    n = row[0]
    xCoord = float(row[1])
    yCoord = float(row[2])
    if n in origMazToSeqMaz:
      mazLandUse[origMazToSeqMaz[n]][4] = xCoord
      mazLandUse[origMazToSeqMaz[n]][5] = yCoord
      spIndexMaz.insert(int(origMazToSeqMaz[n]), (xCoord, yCoord, xCoord, yCoord))
    nodes[n] = [n, xCoord, yCoord]

print "Calculate buffered MAZ measures"
for k in mazLandUse.keys():
  
  #get maz data
  x = float(mazLandUse[k][4])
  y = float(mazLandUse[k][5])
  
  total_pop = 0
  total_emp = 0
  total_acres = 0

  #get all mazs within square box around maz
  idsList = spIndexMaz.intersection((x-BUFF_DIST, y-BUFF_DIST, x+BUFF_DIST, y+BUFF_DIST))
  for id in idsList:
    pop = int(mazLandUse[str(id)][1])
    emp = int(mazLandUse[str(id)][2])
    acres = float(mazLandUse[str(id)][3])
    
    #accumulate measures
    total_pop = total_pop + pop
    total_emp = total_emp + emp
    total_acres = total_acres + acres
  
  #calculate buffer area type
  if total_acres>0:
    mazLandUse[k][6] = (1 * total_pop + 2.5 * total_emp) / total_acres
  else:
    mazLandUse[k][6] = 0
  
  #code area type class
  if mazLandUse[k][6] < 6:
    mazLandUse[k][6] = 5 #rural
  elif mazLandUse[k][6] < 30:
    mazLandUse[k][6] = 4 #suburban
  elif mazLandUse[k][6] < 55:
    mazLandUse[k][6] = 3 #urban
  elif mazLandUse[k][6] < 100:
    mazLandUse[k][6] = 2 #urban business
  elif mazLandUse[k][6] < 300:
    mazLandUse[k][6] = 1 #cbd
  else:
    mazLandUse[k][6] = 0 #regional core

print "Find nearest MAZ for each link, take min area type of A or B node"
lines = ["A,B,AREATYPE" + os.linesep]

with open(LINK_CSV_FILE,'rb') as link_file:
  link_reader = csv.reader(link_file,skipinitialspace=True)
  for row in link_reader:
    a = int(row[0])
    b = int(row[1])
    cntype = row[2]
    ax = nodes[str(a)][1]
    ay = nodes[str(a)][2]
    bx = nodes[str(b)][1]
    by = nodes[str(b)][2]
    
    #find nearest, take min area type of A or B node
    if cntype in ["TANA","USE","TAZ","EXT"]:
      aMaz = list(spIndexMaz.nearest((ax, ay, ax, ay), 1))[0]
      bMaz = list(spIndexMaz.nearest((bx, by, bx, by), 1))[0]
      aAT = mazLandUse[str(aMaz)][6]
      bAT = mazLandUse[str(bMaz)][6]
      linkAT = min(aAT, bAT)
    else:
      linkAT = -1 #NA
      
    #add to output file
    lines.append("%i,%i,%i%s" % (a, b, linkAT, os.linesep))

#create output file
print "Write link area type CSV file"
outFile = open(AREA_TYPE_FILE, "wb")
outFile.writelines(lines)
outFile.close()
