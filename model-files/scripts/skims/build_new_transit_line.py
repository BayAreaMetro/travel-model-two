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
import csv,os,sys,math,re

line_file = sys.argv[1]
out_line_file = sys.argv[2]
node_mapping = sys.argv[3]

#first, read in the node mapping
node_map = {}
reader = csv.DictReader(open(node_mapping))
for line in reader:
    node_map[int(line["OLD_NODE"])] = int(line["N"])

#next, read in the transit lines, change the node, and write out the results
f = open(out_line_file,'wb')
f.write(";;<<PT>><<LINE>>;;"+os.linesep)
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
    if temp_line[-1]=="," or temp_line[-2] == "N":
        continue

    trn_line_count += 1

    # if trn_line_count==4: sys.exit()
    # print("==================")
    # print("{} trn_line={}".format(trn_line_count, trn_line))

    line = trn_line.strip().split('N=')  # todo: this is not robust to whitespace between N and =
    if len(line) < 2: #keep everything before node sequence as-is
        raise
        # f.write(line[0] + os.linesep)
        # continue

    # change line based on time periods available, also remove LONGNAME
    basic_line_info = list(map(str.strip, re.split("[=,]", line[0])))

    basic_line_info[1] = '"line_{line_count}"'.format(line_count = trn_line_count)

    for i in range(len(basic_line_info) - 1):
        if i%2 == 0:
            basic_line_info[i] = str(basic_line_info[i]) + '='
        else:
            basic_line_info[i] = str(basic_line_info[i]) + ","

    basic_line_info_str = ''
    for info in basic_line_info:
        basic_line_info_str += str(info)

    # print the attributes that come before N
    f.write(basic_line_info_str + ' N=')

    for i in range(1,len(line)):
        seq = []
        # print("line[{}]={}".format(i,line[i]))
        last_is_non_node_attr = False

        for str_n in line[i].strip().split(','):
            # strip whitespace
            str_n = str_n.strip()
            if str_n=="": continue
            # print("str_n={}".format(str_n))

            if str_n.lstrip('-').isdigit():
               n = int(str_n)
            elif len(str_n)>0:
                # print(str_n)
                seq.append(str_n)
                last_is_non_node_attr = True
                continue

            #make sure that the sign of the nodes (for stop/pass-through) is retained
            sign = int(math.copysign(1,n))
            new_n = sign*node_map[n*sign]
            node_update_count += 1
            if last_is_non_node_attr:
                seq.append("N=" + str(new_n))
                last_is_non_node_attr = False
            else:
                seq.append(new_n)

        if i < len(line)-1:
            seq.append(' N=')
        # print(seq)
        f.write(','.join(map(str,seq)))
    f.write(os.linesep)
    
    # just processed the line, rset
    trn_line = ""

f.close()
        
print("Updated {} nodes in {} lines".format(node_update_count, trn_line_count))