"""
    transfer_maz_maz_vols.py base_dir period
    
    Transfer the maz->maz assignment volumes (used for preloading the taz->taz assignment) from
    the base network numbering to the assignment network's numbering.
    
    Inputs: avgload@period@_taz_to_node.txt - base -> assignment network node correspondence
            maz_preload_@period@_vols.csv   - maz->maz assignment volumes
            
    Outputs: maz_preload_@period@_seq_vols.csv   - maz->maz assignment volumes
    
    author: crf (2 2014)
"""

import os,sys

base_dir = sys.argv[1]
period = sys.argv[2]

node_correspondence_file = os.path.join(base_dir,'hwy/avgload' + period + '_taz_to_node.txt')
maz_vols_file = os.path.join(base_dir,'hwy/maz_preload_' + period + '_vols.csv')
output_vols_file = os.path.join(base_dir,'hwy/maz_preload_' + period + '_seq_vols.csv')

#read node correspondence
node_correspondence = {}
with open(node_correspondence_file) as f:
    for line in f:
        line = line.strip()
        if len(line) == 0:
            continue
        line = line.split()
        node_correspondence[int(float(line[1]))] = int(float(line[0]))
    
with open(output_vols_file,'wb') as of:
    with open(maz_vols_file) as f:
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            line = line.split(',')
            a = int(float(line[0]))
            b = int(float(line[1]))
            vol = float(line[2])
            if (not a in node_correspondence) or (not b in node_correspondence) or (vol == 0.0):
                continue
            of.write(','.join(map(str,(node_correspondence[a],node_correspondence[b],line[2]))) + os.linesep)
