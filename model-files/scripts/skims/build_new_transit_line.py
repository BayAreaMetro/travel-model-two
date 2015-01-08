"""
    build_new_transit_line.py in_line_file out_line_file node_mapping_file
    
    This is a simple script which uses an existing node mapping file to transfer a transit
    line file with a set node sequence to an updated numbering scheme. All line data (including
    stop/pass-through nodes) is retained in the process.

    inputs: in_line_file - the input line file, with each entry ending in a N=... node sequence
            node_mapping_file - the location of the (csv) node mapping file, which has
                                columns (new_node,old_node), and no header

    outputs: out_link_file - the output transit line file, with updated node numbers

    crf 8/2013

"""
import os,sys,math

line_file = sys.argv[1]
out_line_file = sys.argv[2]
node_mapping = sys.argv[3]

#first, read in the node mapping
node_map = {}
for line in open(node_mapping):
    #N,OLD_NODE
    line = line.strip().split()
    if len(line) < 2:
        continue
    node_map[int(line[1].strip())] = int(line[0].strip())

#next, read in the transit lines, change the node, and write out the results
f = open(out_line_file,'wb')
for line in open(line_file):
    line = line.strip().split(' N=')
    if len(line) < 2: #keep everything before node sequence as-is
        f.write(line[0] + os.linesep)
        continue
    f.write(line[0] + ' N=')
    seq = []
    for n in line[1].split(','):
        n = int(n)
        #make sure that the sign of the nodes (for stop/pass-through) is retained
        sign = int(math.copysign(1,n))
        new_n = sign*node_map[n*sign]
        seq.append(new_n)
    f.write(','.join(map(str,seq)) + os.linesep)
f.close()
        
