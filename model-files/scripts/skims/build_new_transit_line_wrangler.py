"""
    build_new_transit_line_nw.py in_line_file out_line_file node_mapping_file

    This is a simple script which uses an existing node mapping file to transfer a transit
    line file with a set node sequence to an updated numbering scheme. All line data (including
    stop/pass-through nodes) is retained in the process.

    inputs: in_line_file - the input line file, with each entry ending in a N=... node sequence
            node_mapping_file - the location of the (csv) node mapping file, which has
                                columns (new_node,old_node), and no header

    outputs: out_link_file - the output transit line file, with updated node numbers

    This is a Wrangler version of build_new_transit_line.py
    NetworkWrangler: https://github.com/BayAreaMetro/NetworkWrangler
    To use, set PYTHONPATH to include location this is cloned as well as _static subdir

"""
import csv,os,sys,math
import Wrangler

line_file     = sys.argv[1]
out_line_file = sys.argv[2]
node_mapping  = sys.argv[3]

if __name__ == '__main__':

    #first, read in the node mapping
    node_map = {}
    reader = csv.DictReader(open(node_mapping))
    for line in reader:
        node_map[int(line["OLD_NODE"])] = int(line["N"])

    line_file_parts   = os.path.split(line_file)       # line_file_parts = ('trn', 'transitLines.lin')
    networkname_parts = line_file_parts[1].split(".")  # networkname_parts = ['transitLines', 'lin']
    node_update_count = 0
    trn_line_count    = 0

    # read the transit network
    trn_net = Wrangler.TransitNetwork(modelType = Wrangler.Network.MODEL_TYPE_TM2, modelVersion=1.0,
                                      basenetworkpath=line_file_parts[0], isTiered=True, networkName=networkname_parts[0])
    for line in trn_net:
        if not isinstance(line, Wrangler.TransitLine): continue

        for node in line.n: # array of Wrangler.Node instances
            old_num = node.getNum()
            node.replaceNum(node_map[old_num])
            node_update_count += 1

        trn_line_count += 1

    line_file_parts   = os.path.split(out_line_file)   # line_file_parts = ('trn', 'transitLines_new_nodes.lin')
    networkname_parts = line_file_parts[1].split(".")  # networkname_parts = ['transitLines_new_nodes', 'lin']
    trn_net.write(path=line_file_parts[0], name=networkname_parts[0], writeEmptyFiles=False, suppressQuery=True, suppressValidation=True, line_only=True)
    print("Updated {} nodes in {} lines".format(node_update_count, trn_line_count))
