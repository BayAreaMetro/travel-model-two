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
trn_line          = ""
trn_line_count    = 0
node_update_count = 0
for temp_line in open(line_file):

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
    if temp_line[-1]==",":
        continue

    trn_line_count += 1
    # print("{} trn_line={}".format(trn_line_count, trn_line))

    line = trn_line.strip().split('N=')
    if len(line) < 2: #keep everything before node sequence as-is
        raise
        # f.write(line[0] + os.linesep)
        # continue

    # print the attributes that come before N
    f.write(line[0] + ' N=')

    for i in range(1,len(line)):
        seq = []

        # print("")
        # print("line[{}]={}".format(i,line[i]))

        for n in line[i].strip().split(','):
            str_n = n
            if str_n.lstrip('-').isdigit():
               n = int(n)
            else:
               if len(n)>0:
			      seq.append(n)
               continue
            #make sure that the sign of the nodes (for stop/pass-through) is retained
            sign = int(math.copysign(1,n))
            new_n = sign*node_map[n*sign]
            node_update_count += 1
            seq.append(new_n)
        if i < len(line)-1:
            seq.append(' N=')
        f.write(','.join(map(str,seq)))
    f.write(os.linesep)
    
    # just processed the line, rset
    trn_line = ""

f.close()
        
print("Updated {} nodes in {} lines".format(node_update_count, trn_line_count))