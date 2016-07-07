"""
    tap_data_builder.py model_run_dir 

    inputs: model_run_dir - the directory the model is running in (directory with INPUTS, hwy, etc.)

    This script builds the tap data file. This file is a csv data file which contains data about taps
    and is used by the CTRAMP model. It consists of the following columns:
    
        tap - the tap number (in CTRAMP sequential numbering)
        tap_original - the original tap number (in the CUBE network)
        lotid - the lot id; this is the same as tap
        taz - the taz the tap is associated with (see tap_to_taz_for_parking.job)
        capacity - the capacity of the lot; this is set to 9999 by default, but could be changed after 
                   this process has run
                   
    This script uses the following files:
    
        mtc_final_netwok_zone_seq.csv - the file holding the correspondence between network zone numbers and
                                        CTRAMP sequential numbering
        tap_to_taz_for_parking.txt - the file holding the walk distance shortest path tree from taps to tazs
        
    Output: tap_data.csv (as described above)
    
    crf 11/2013

"""

import os,sys

model_run_dir = sys.argv[1]
zone_mappng_file = os.path.join(model_run_dir,r'hwy\mtc_final_network_zone_seq.csv')
infile = os.path.join(model_run_dir,r'hwy\tap_to_taz_for_parking.txt')
outfile = os.path.join(model_run_dir,r'hwy\tap_data.csv')

#read the sequence mapping and build mappings and a list of all taps
seq_mapping = {}
taps = []
tap_mapping = {}
for line in open(zone_mappng_file):
    data = map(int,line.strip().split(','))
    if data[1] > 0:
        seq_mapping[data[0]] = str(data[1])
    if data[2] > 0:
        seq_mapping[data[0]] = str(data[2])
    if data[3] > 0:
        seq_mapping[data[0]] = str(data[3])
        taps.append(data[0])
    if data[4] > 0:
        seq_mapping[data[0]] = str(data[4])

#create the data for the file, using the tap to taz file as the structure for the loop
# only the taz that is closest to a given tap is retained
data = {}
for line in open(infile):
    line = line.strip()
    if len(line) == 0:
        continue
    line = line.split(',')
    tap = int(line[0])
    taz = int(line[1])
    distance = float(line[4])
    if (not tap in data) or (distance < data[tap][0]):
        data[tap] = (distance,[seq_mapping[tap],tap,seq_mapping[tap],seq_mapping[taz],9999])

#write the output file
f = open(outfile,'wb')
f.write(','.join(['tap','tap_original','lotid','taz','capacity']) + os.linesep)
taps.sort()
for tap in taps:
    tappy = tap
    #if it isn't in our list, then just pick the next lowest tap - not the greatest, but ok
    # this occurs because the shortest path for tap->taz is limited to a few miles
    # this should not happen, if it is reported, then the threshold for cutting off tap->taz
    # skims should be increased
    if not tappy in data:
        print 'tap (' + str(tappy) + ')not captured in tap->taz (for parking) script; max distance for that should be increased'
    while not tappy in data: 
        tappy -= 1
    d = list(data[tappy][1])
    if tap != tappy:
        d[0] = seq_mapping[tap]
        d[1] = tap
        d[2] = seq_mapping[tap]
    f.write(','.join(map(str,d)) + os.linesep)
f.close()
