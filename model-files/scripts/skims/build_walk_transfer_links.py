"""
    build_walk_transfer_links.py in_tap_connector_file out_tap_connector_file
    
    This is a simple script which reads the shortest path tap->tap walk distance skim file,and
    writes out a file with entries needed to update a cube network. These links are used as walk
    transfer links during transit skimming.

    inputs: in_tap_connector_file - the input tap-tap walk skim file

    outputs: out_tap_connector_file - the output tap-tap connector file, with columns (a_node,b_node,distance)

    crf 8/2013

"""

import os,sys

taps_connection = sys.argv[1]
taps_connectors = sys.argv[2]
    
f = open(taps_connectors,'wb')
finished_taps = {}
for line in open(taps_connection):
    line = line.strip().split(',')
    taps = (int(line[0]),int(line[1]))
    if not taps in finished_taps:
        #tap,tap,cntype,distance
        #write both directions
        f.write(','.join([line[0],line[1],'TRWALK',line[4]]) + os.linesep)
        f.write(','.join([line[1],line[0],'TRWALK',line[4]]) + os.linesep)
        finished_taps[taps] = None
        finished_taps[(taps[1],taps[0])] = None
f.close()
