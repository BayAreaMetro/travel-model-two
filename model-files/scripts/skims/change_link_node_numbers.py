"""
    change_link_node_numbers.py in_link_file out_link_file node_mapping_file
    
    This is a simple script which uses an existing node mapping file to transfer a link
    file with a/b nodes in the first two entries to a/b in an updated numbering scheme.
    All columns subsequent to the first two are retained as the are currently written.

    inputs: in_link_file - the input link csv file, with columns (a_node,b_node,....)
            node_mapping_file - the location of the (csv) node mapping file, which has
                                columns (new_node,old_node), and no header

    outputs: out_link_file - the output (csv) file, which looks exactly like the input, only
                             with updated node numbers

    crf 9/2013

"""

import os,sys

link_file = sys.argv[1]
out_link_file = sys.argv[2]
node_mapping = sys.argv[3]

#first collect all of the node mappings
node_map = {}
for line in open(node_mapping):
    #N,OLD_NODE
    line = line.strip().split()
    if len(line) < 2:
        continue
    node_map[int(line[1].strip())] = int(line[0].strip())

#now read the link file, transfer the a/b nodes, and write the new file
f = open(out_link_file,'wb')
for line in open(link_file):
    line = line.strip().split(',')
    if len(line) < 2:
        f.write(line[0] + os.linesep)
        continue
    #only changing first two entries
    line[0] = str(node_map[int(line[0])])
    line[1] = str(node_map[int(line[1])])
    f.write(','.join(line) + os.linesep)
f.close()
