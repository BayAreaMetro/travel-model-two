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

print 'reading transit lines from {}'.format(transit_line_file)
linesByNode = dict()
trn_line = ""
for temp_line in open(transit_line_file):
  # strip leading and trailing whitespace
  temp_line = temp_line.strip()

  # if our line has a comment - cut it out
  semicolon_index = temp_line.find(";")
  if semicolon_index >= 0:
    temp_line = temp_line[:semicolon_index].strip()
    
  # skip blank lines
  if len(temp_line)==0: continue

  # append to our transit line string
  trn_line = trn_line + temp_line

  # if it ends in a comma, continue until we find the end
  if temp_line[-1]=="," or temp_line[-2] == "N":
    continue

  # print("trn_line={}".format(trn_line))

  split_line = list(map(str.strip,re.split('[=,]',trn_line.strip())))
  if len(split_line) < 3:
    continue
  
  lineName = split_line[1]
  iter = split_line.index('N') + 1
  while iter < len(split_line):
    #skip NNTIME,TIME,ACCESS,etc token and value
    if split_line[iter] in ["NNTIME", "TIME", "ACCESS", "ACCESS_C", "DELAY", "DELAY_C", "DWELL", "DWELL_C"]:
        iter = iter + 2
        continue
    #skip N token
    if (split_line[iter] == "N"):
        iter = iter + 1
        continue
    n = int(split_line[iter])
    if n > 0:
      if n not in linesByNode:
        linesByNode[n] = set()
      linesByNode[n].add(lineName.replace('"',""))
    iter = iter + 1

  # just processed the line, rset
  trn_line = ""
	
#  for i in range(split_line.index('N') + 1,len(split_line)):
#    n = int(split_line[i])
#    if n > 0:
#      if n not in linesByNode:
#        linesByNode[n] = set()
#      linesByNode[n].add(lineName.replace('"',""))

print 'reading tap connectors'
access_links = []
with open(network_tap_links_file, 'rb') as csvfile:
  tapreader = csv.reader(csvfile, skipinitialspace=True)
  for row in tapreader:
    access_links.append(row)

print 'reading zone sequence file'
tapToSeqTap = dict()
with open(zone_seq_file, 'rb') as csvfile:
  tapreader = csv.DictReader(csvfile)
  for row in tapreader:
    node_id = int(row["N"])
    seq_tap_id = int(row["TAPSEQ"])
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
print("wrote {}".format(tap_lines_file))

end_time = pytime.time()
print 'elapsed time in minutes: ' + str((end_time - start_time) / 60.0)
