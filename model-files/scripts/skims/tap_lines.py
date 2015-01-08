"""
  Generate a list of lines served for each TAP
  Takes as input the transit lines file, the tap connectors, and the zone renumbering file
  Outputs a list of line names for each TAP
  Ben Stabler, stabler@pbworld.com, 12/23/13
"""

import os,sys,re, csv
import time as pytime

################################################################################

base_dir = os.getcwd()

#input files
transit_line_file = os.path.join(base_dir,r'trn\transitLines.lin')
network_tap_links_file = os.path.join(base_dir,r'hwy\mtc_final_network_tap_links.csv')
zone_seq_file = os.path.join(base_dir,r'hwy\mtc_final_network_zone_seq.csv')

#output file
tap_lines_file = os.path.join(base_dir,r'trn\tapLines.csv')

################################################################################

start_time = pytime.time()

print 'reading transit lines'
linesByNode = dict()
for line in open(transit_line_file):
  split_line = map(str.strip,re.split('[=,]',line.strip()))
  if len(split_line) < 3:
    continue
  
  lineName = split_line[1]
  for i in range(split_line.index('N') + 1,len(split_line)):
    n = int(split_line[i])
    if n > 0:
      if n not in linesByNode:
        linesByNode[n] = set()
      linesByNode[n].add(lineName.replace('"',""))

print 'reading tap connectors'
access_links = []
with open(network_tap_links_file, 'rb') as csvfile:
  tapreader = csv.reader(csvfile, skipinitialspace=True)
  for row in tapreader:
    access_links.append(row)

print 'reading zone sequence file'
tapToSeqTap = dict()
with open(zone_seq_file, 'rb') as csvfile:
  tapreader = csv.reader(csvfile, skipinitialspace=True)
  for row in tapreader:
    node_id = int(row[0])
    seq_tap_id = int(row[3])
    if seq_tap_id > 0:
      tapToSeqTap[node_id] = seq_tap_id

#get nodes connected to each tap
nodesByTap = dict()
for linkRow in access_links:
  tap = int(linkRow[0])
  node = int(linkRow[1])
  
  if tap not in nodesByTap:
    nodesByTap[tap] = set()
  nodesByTap[tap].add(node)

#get lines for each tap
linesByTap = dict()
for tap in tapToSeqTap.keys():
  nodes = nodesByTap[tap]
    
  if tap not in linesByTap:
    linesByTap[tap] = set()
  for node in nodes:
    if node in linesByNode:
      lines = linesByNode[node]
      for line in lines:
        linesByTap[tap].add(line)

#write out tapLines file for CT-RAMP
f = file(tap_lines_file,"wt")
f.write("TAP,LINES\n")
for tap in linesByTap.keys():
  lines = " ".join(list(linesByTap[tap]))
  if lines != "":
    f.write("%s,%s\n" % (tapToSeqTap[tap],lines))
f.close()

end_time = pytime.time()
print 'elapsed time in seconds: ' + str((end_time - start_time) / 1000.0)
