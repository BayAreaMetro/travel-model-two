"""
    taz_matrix_transfer.py base_dir in_files,out_files

    inputs: base_dir - the directory the model is running in (directory with INPUTS, hwy, etc.)
            in_files - comma separated list of input (csv) matrix files, relative to base_dir
            out_files - comma separated list of output (csv) matrix files, relative to base_dir

    This script transfers csv matrices from the original taz numbering to the sequential taz
    numbering used internally by the model. It assumes the following about the input (and by
    implication output) csv files:
    
        1) There is a header line of some sort (is is copied).
        2) That the first two columns are zones (presumably from/to).

    The output of this will be a file for each in out_files (whose number must match those in in_files),
    using the sequential zone numbers. The output files must not be the same (name/location) as the 
    input files.
    
    crf 2/2014
"""

import os,sys

base_dir = sys.argv[1]
in_files = sys.argv[2].split(',')
out_files = sys.argv[3].split(',')

#first, create old->new mapping
taz_mapping = {}
with open(os.path.join(base_dir,'hwy','mtc_final_network_zone_seq.csv')) as f:
    for line in f:
        line = line.strip()
        if len(line) == 0:
            continue
        data = line.split(',')
        taz_mapping[int(data[0])] = int(data[1])

#transfer the zone numberings
for i in range(len(in_files)):
    with open(os.path.join(base_dir,in_files[i])) as f:
        with open(os.path.join(base_dir,out_files[i]),'wb') as of:
            first = True
            for line in f:
                line = line.strip()
                if first:
                    of.write(line + os.linesep)
                    first = False
                    continue
                if len(line) == 0:
                    continue
                data = line.split(',')
                data[0] = str(taz_mapping[int(data[0])])
                data[1] = str(taz_mapping[int(data[1])])
                of.write(','.join(data) + os.linesep)
