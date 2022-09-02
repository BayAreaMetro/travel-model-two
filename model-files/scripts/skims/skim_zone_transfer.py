"""
skim_zone_transfer.py zone_mapping_file skim_file columns_to_transfer [transfer_types...]

    Transfer the zones listed in a csv skim file to the sequence zone numbering. The transfer
    will happen to the first n columns, where n is specified when calling this script

    Arguments: zone_mapping_file: a csv file holding a mapping from zone->TAZ,MAZ,TAP,EXT
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
import csv,sys,os,shutil

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
reader = csv.DictReader(open(zone_mapping_file))
for data in reader:
    if int(data["TAZSEQ"]) > 0:
        seq_mapping[int(data["N"     ])] = str(data["TAZSEQ"])
        taz_mapping[int(data["TAZSEQ"])] = str(data["N"     ])
    if int(data["MAZSEQ"]) > 0:
        seq_mapping[int(data["N"     ])] = str(data["MAZSEQ"])
        maz_mapping[int(data["MAZSEQ"])] = str(data["N"     ])
    if int(data["TAPSEQ"]) > 0:
        seq_mapping[int(data["N"     ])] = str(data["TAPSEQ"])
        tap_mapping[int(data["TAPSEQ"])] = str(data["N"     ])
    if int(data["EXTSEQ"]) > 0:
        seq_mapping[int(data["N"     ])] = str(data["EXTSEQ"])
        ext_mapping[int(data["EXTSEQ"])] = str(data["N"     ])

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

# save the original?
# shutil.copy2(skim_file, skim_file + '.bak')

temp_skim_file = skim_file + '.tmp'
f = open(temp_skim_file,'w')
for line in open(skim_file):
    data = line.strip().split(',')
    for i in range(columns_to_transfer):
        try:
            data[i] = transfer[i][int(data[i])]
        except Exception as inst:
            # for some reason this file has lots of blank lines -- workaround this
            if data == ['']: continue
            # handle EOF
            if data == ['\x1a']: continue
            print(data)
            raise inst
    f.write(','.join(data) + os.linesep)
f.close()

os.remove(skim_file)
os.rename(temp_skim_file,skim_file)
