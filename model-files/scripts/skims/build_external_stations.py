"""
    build_external_stations.py node_offset base_dir external_station_file node_correspondence_file output_node_file output_link_file

    This script reads the externals station information in external_station_file and outputs node
    and link files which can be read with cube to add the external station and connector links
    a network.

    The external_station_file should contain at least the following fields:

        ext_zone       - the zone/node number for the external station
        x              - the x coordinate for the station location
        y              - the y coordinate for the station location
        entrance_nodes - a semicolon delimited list of nodes that the station should connect to

    To keep things simple, links in both directions are built between the station and entrance nodes,
    regardless of whether or not the node is attached to a one-way road or not (in the case of a
    connector built in the incorrect direction, it will never get used).

    The node_correspondence_file is used to transfer the node/link numbers to those used in the specific
    network. The node_offset is the number of internal nodes in the network. The (sequential) external
    zone numbering will begin at (node_offset + 1).

    version:  Travel Model Zed
    authors:  crf (02 11 2014)

"""

import os,sys,csv,math

node_offset = int(sys.argv[1])
base_dir = sys.argv[2]
external_station_file = os.path.join(base_dir,sys.argv[3])
node_correspondence_file = os.path.join(base_dir,sys.argv[4])
output_node_file = os.path.join(base_dir,sys.argv[5])
output_link_file = os.path.join(base_dir,sys.argv[6])


#first build external station data
external_stations = {}
node_correspondence = {}
node_number = node_offset
with open(external_station_file) as f:
    for line in csv.DictReader(f,skipinitialspace=True):
        node_number += 1
        external_station = int(line['ext_zone'])
        x = float(line['x'])
        y = float(line['y'])
        entrance_nodes = map(int,line['entrance_nodes'].split(';'))
        external_stations[node_number] = (x,y,external_station,entrance_nodes)
        for entrance_node in entrance_nodes:
            node_correspondence[entrance_node] = None

#now get necessary node correspondence
with open(node_correspondence_file) as f:
    for line in f:
        new_node,old_node,x,y = line.strip().split()
        old_node = int(float(old_node))
        if old_node in node_correspondence:
            node_correspondence[old_node] = (int(float(new_node)),float(x),float(y))


#finally build output files
#node first
new_nodes = external_stations.keys()
new_nodes.sort()
with open(output_node_file,'wb') as f:
    for new_node in new_nodes:
        external_station = external_stations[new_node]
        #n,x,y,old_node
        f.write(','.join(map(str,(new_node,external_station[0],external_station[1],external_station[2]))) + os.linesep)

#now link
with open(output_link_file,'wb') as f:
    for new_node in new_nodes:
        x,y,external_station,entrance_nodes = external_stations[new_node]
        for entrance_node in entrance_nodes:
            b,bx,by = node_correspondence[entrance_node]
            distance = math.sqrt((bx - x)**2 + (by - y)**2)
            #a,b,cntype,feet,capclass,old_a,old_b
            f.write(','.join(map(str,(new_node,b,'EXT',distance,external_station,entrance_node))) + os.linesep)
            f.write(','.join(map(str,(b,new_node,'EXT',distance,entrance_node,external_station))) + os.linesep)

