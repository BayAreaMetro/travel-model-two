#transfer_truck_kfactors.py

import os,sys

base_dir = sys.argv[1]
ix_da_file = os.path.join(base_dir,'ix_trips','IXDailyDA.csv')
ix_sr2_file = os.path.join(base_dir,'ix_trips','IXDailySR2.csv')
ix_sr3_file = os.path.join(base_dir,'ix_trips','IXDailySR3.csv')
ix_total_file = os.path.join(base_dir,'ix_trips','IXDailyTotal.csv')
taz2old_file = os.path.join(base_dir,'output','taz_2_old.csv')
taz_file = os.path.join(base_dir,'taz_data.csv')
outfile = os.path.join(base_dir,'output','IXDaily2006x4.may2208.csv')

out_header = ['i','j'] #do this here so next step can get correct order

print 'loading ix data'
ix = {}
for ix_file in [ix_da_file,ix_sr2_file,ix_sr3_file,ix_total_file]:
    with open(ix_file) as f:
        first = True
        for row in f:
            row = row.strip()
            if len(row) == 0:
                continue
            row = row.split(',')
            if first:
                name = row[0]
                out_header.append(name)
                ix_data = {}
                to_tazs = [0]
                for i in range(1,len(row)):
                    to_tazs.append(int(row[i]))
                first = False
                continue
            from_taz = int(row[0])
            for i in range(1,len(row)):
                ix_data[(from_taz,to_tazs[i])] = float(row[i])
        ix[name] = ix_data

old_tazs = to_tazs[1:]

print 'loading taz2old'
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
        percentage = float(row[2])
        taz2old[taz] = (oldtaz,percentage)

#add externals to taz2old)
taz2old[900001] = (1455,1.0)
taz2old[900002] = (1456,1.0)
taz2old[900003] = (1457,1.0)
taz2old[900004] = (1458,1.0)
taz2old[900005] = (1459,1.0)
taz2old[900006] = (1460,1.0)
taz2old[900007] = (1461,1.0)
taz2old[900008] = (1462,1.0)
taz2old[900009] = (1463,1.0)
taz2old[900010] = (1464,1.0)
taz2old[900011] = (1465,1.0)
taz2old[900012] = (1466,1.0)
taz2old[900013] = (1467,1.0)
taz2old[900014] = (1468,1.0)
taz2old[900015] = (1469,1.0)
taz2old[900016] = (1470,1.0)
taz2old[900017] = (1471,1.0)
taz2old[900018] = (1472,1.0)
taz2old[900019] = (1473,1.0)
taz2old[900020] = (1474,1.0)
taz2old[900021] = (1475,1.0)


print 'loading taz data'
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
for taz in range(900001,900022):
    tazs.append(taz)

print 'building rescale'
#get not missing zones for rescaling
not_missing_otazs = {}
for taz in taz2old:
    not_missing_otazs[taz2old[taz][0]] = None

rescale_factors = {}
for mode in ix:
    total = 0.0
    captured = 0.0
    ix_data = ix[mode]
    for od in ix_data:
        value = ix_data[od]
        o,d = od
        total += value
        if (o in not_missing_otazs) and (d in not_missing_otazs):
            captured += value
    print str(total) + ':' + str(captured) + '  ' + mode
    rescale_factors[mode] = total/captured
print rescale_factors

print 'writing data'
tazs.sort()
modes = out_header[2:]
with open(outfile,'wb') as f:
    f.write(','.join(out_header) + os.linesep)
    ocounter = 0
    for otaz in tazs:
        ocounter += 1
        kotaz = -1
        if otaz in taz2old:
            kotaz,ofrac = taz2old[otaz]
        dcounter = 0
        for dtaz in tazs:
            dcounter += 1
            kdtaz = -1
            if dtaz in taz2old:
                kdtaz,dfrac = taz2old[dtaz]
            kfactor = 1.0
            if (kotaz > -1) and (kdtaz > -1): #skip if zero
                line = [ocounter,dcounter]
                vsum = 0.0
                for mode in modes:
                    value = ix[mode][(kotaz,kdtaz)]*ofrac*dfrac*rescale_factors[mode]
                    line.append(value)
                    vsum += value
                if vsum > 0:
                    f.write(','.join(map(str,line)) + os.linesep)

