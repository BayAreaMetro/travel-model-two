"""
skim_zone_transfer.py zone_mapping_file skim_file columns_to_transfer [transfer_types...]

    Transfer the zones listed in a csv skim file to the sequence zone numbering. The transfer
    will happen to the first n columns, where n is specified when calling this script

    Arguments: zone_mapping_file: a headerless csv file holding a mapping from zone->TAZ,MAZ,TAP,EXT
               skim_file: the (headerless csv ) skim file to transfer - it will be replaced by this process
               columns_to_transfer: the number of columns to transfer
               transfer_types: if present, they type of transfer for each column; if this is present, then
                               the number of types listed must equal columns_to_transfer
                               the valid types are:
                                 SEQ - going from original node numbering to sequence numbering
                                 TAZ - going from sequence to original node numbering for TAZs
                                 MAZ - going from sequence to original node numbering for MAZs
                                 TAP - going from sequence to original node numbering for TAPs
                                 EXT - going from sequence to original node numbering for EXTs

"""
import sys,os

zone_mapping_file = os.path.abspath(sys.argv[1])
skim_file = os.path.abspath(sys.argv[2])
columns_to_transfer = int(sys.argv[3])
transfer = []
for i in range(columns_to_transfer):
    if len(sys.argv) > 4:
        transfer.append(sys.argv[4+i].upper())
    else:
        transfer.append('SEQ')
    

seq_mapping = {}
taz_mapping = {}
maz_mapping = {}
tap_mapping = {}
ext_mapping = {}
for line in open(zone_mapping_file):
    data = map(int,line.strip().split(','))
    if data[1] > 0:
        seq_mapping[data[0]] = str(data[1])
        taz_mapping[data[1]] = str(data[0])
    if data[2] > 0:
        seq_mapping[data[0]] = str(data[2])
        maz_mapping[data[2]] = str(data[0])
    if data[3] > 0:
        seq_mapping[data[0]] = str(data[3])
        tap_mapping[data[3]] = str(data[0])
    if data[4] > 0:
        seq_mapping[data[0]] = str(data[4])
        ext_mapping[data[4]] = str(data[0])

if transfer:
    for i in range(columns_to_transfer):
        if transfer[i] == 'TAZ':
            transfer[i] = taz_mapping
        elif transfer[i] == 'MAZ':
            transfer[i] = maz_mapping
        elif transfer[i] == 'TAP':
            transfer[i] = tap_mapping
        elif transfer[i] == 'SEQ':
            transfer[i] = seq_mapping
        elif transfer[i] == 'EXT':
            transfer[i] = ext_mapping
        else:
            raise Exception('Unknown transfer: ' + transfer[i])

temp_skim_file = skim_file + '.tmp'
f = open(temp_skim_file,'wb')
for line in open(skim_file):
    data = line.strip().split(',')
    for i in range(columns_to_transfer):
        data[i] = transfer[i][int(data[i])]
    f.write(','.join(data) + os.linesep)
f.close()

os.remove(skim_file)
os.rename(temp_skim_file,skim_file)
