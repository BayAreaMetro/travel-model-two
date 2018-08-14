#transfer_truck_kfactors.py

import os,sys

base_dir = sys.argv[1]
kfactor_file = os.path.join(base_dir,'truck_model','truck_kfactor.csv')
taz2old_file = os.path.join(base_dir,'output','taz_2_old.csv')
outfile = os.path.join(base_dir,'output','kfactors_taz.csv')
taz_file = os.path.join(base_dir,'taz_data.csv')

taz2old = {}
with open(taz2old_file) as f:
    first = True
    for row in f:
        if first:
            first = False
            continue
        row = row.strip()
        if len(row) == 0:
            continue
        row = row.split(',')
        taz = int(row[0])
        oldtaz = int(row[1])
        taz2old[taz] = oldtaz

kfactors = {}
with open(kfactor_file) as f:
    first = True
    for row in f:
        if first:
            first = False
            continue
        row = row.strip()
        if len(row) == 0:
            continue
        row = row.split(',')
        taz = int(row[0])
        kfactors[taz] = [0] + map(float,row[1:])

tazs = []
with open(taz_file) as f:
    first = True
    for row in f:
        if first:
            first = False
            continue
        row = row.strip()
        if len(row) == 0:
            continue
        row = row.split(',')
        tazs.append(int(row[1]))

tazs.sort()
with open(outfile,'wb') as f:
    f.write(','.join(['i','j','kfactor']) + os.linesep)
    for otaz in tazs:
        kotaz = -1
        if otaz in taz2old:
            kotaz = taz2old[otaz]
        for dtaz in tazs:
            kdtaz = -1
            if dtaz in taz2old:
                kdtaz = taz2old[dtaz]
            kfactor = 1.0
            if (kotaz > -1) and (kdtaz > -1):
                kfactor = kfactors[kotaz][kdtaz]
            f.write(','.join(map(str,[otaz,dtaz,kfactor])) + os.linesep)

