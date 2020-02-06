import csv,os,math,sys
from dbfpy import dbf

base_dir = sys.argv[1]
maz_file = os.path.join(base_dir,'maz_data.csv')
old_taz_lat_long_file = os.path.join(base_dir,'taz1454_lat_long.csv')
new_taz_lat_long_file = os.path.join(base_dir,'tazs_new_centroids.csv')
taz_old2new_mapping_file = os.path.join(base_dir,'output','taz_2_old.csv')

airport_files = ['2007_fromOAK',
                 '2007_fromSFO',
                 '2007_fromSJC',
                 '2007_toOAK',
                 '2007_toSFO',
                 '2007_toSJC',
                 '2035_fromOAK',
                 '2035_fromSFO',
                 '2035_fromSJC',
                 '2035_toOAK',
                 '2035_toSFO',
                 '2035_toSJC']


#first build old->new taz correspondence (actually is just old taz that is closest to each new taz)
def getDistance(p1,p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

old_taz_lat_long = {}
with open(old_taz_lat_long_file) as f:
    for line in csv.DictReader(f,skipinitialspace=True):
        #taz1454	long	lat
        taz = int(line['taz1454'])
        long = float(line['long'])
        lat = float(line['lat'])
        old_taz_lat_long[(lat,long)] = taz

taz_new2old_map = {}
with open(new_taz_lat_long_file) as f:
    for line in csv.DictReader(f,skipinitialspace=True):
        #taz	long	lat
        taz = int(line['taz'])
        long = float(line['long'])
        lat = float(line['lat'])
        coord = (lat,long)
        otaz = -1
        dist = 99999999.0
        for otaz_coord in old_taz_lat_long:
            d = getDistance(coord,otaz_coord)
            if d < dist:
                dist = d
                otaz = old_taz_lat_long[otaz_coord]
        taz_new2old_map[taz] = otaz


pop = {}
emp = {}
area = {}
with open(maz_file,'rb') as f:
    for line in csv.DictReader(f,skipinitialspace=True):
        taz = int(line['TAZ_ORIGINAL'])
        if not taz in pop:
            pop[taz] = 0.0
            emp[taz] = 0.0
            area[taz] = 0.0
        pop[taz] += float(line['POP'])
        emp[taz] += float(line['emp_total'])
        area[taz] += float(line['ACRES'])

w1 = {}
w2 = area
for taz in pop:
    w1[taz] = pop[taz] + 2.5*emp[taz]

taz_old2new = {}
for taz in taz_new2old_map:
    old_taz = taz_new2old_map[taz]
    if not old_taz in taz_old2new:
        taz_old2new[old_taz] = []
    taz_old2new[old_taz].append(taz)

print len(taz_old2new)
print len(taz_new2old_map)

taz_mapping = {} #new_taz -> (old_taz,%)
for old_taz in taz_old2new:
    w1_sum = 0.0
    w2_sum = 0.0
    for taz in taz_old2new[old_taz]:
        w1_sum += w1[taz]
        w2_sum += w2[taz]
    if w1_sum > 0:
        w = w1
        w_sum = w1_sum
    else:
        w = w2
        w_sum = w2_sum
    s = 0.0
    for taz in taz_old2new[old_taz]:
        p = w[taz]/w_sum
        taz_mapping[taz] = (old_taz,p)
        s += p
    else:
        taz_mapping[taz] = (old_taz,1.0 - (s - p)) #revert last one to ensure sum to 1

with open(taz_old2new_mapping_file,'wb') as f:
    f.write(','.join(['taz','oldtaz','percent']) + os.linesep)
    for taz in taz_mapping:
        f.write(','.join(map(str,(taz,taz_mapping[taz][0],taz_mapping[taz][1]))) + os.linesep)

#mapping for airports should be:
# oak: 874 -> (1,560)
# sfo: 239 -> (6,426)
# sjc: 434 -> (7,879)
airport_data = {} #file -> taz -> line
skipped = {}
for airport_file in airport_files:
    inbound = airport_file.find('to') > -1

    airport_csv = os.path.join(base_dir,'output',airport_file + '.csv')
    airport_data[airport_csv] = {}
    db = dbf.Dbf(os.path.join(base_dir,'airport',airport_file + '.dbf'))
    fields = db.fieldNames
    totals = {}
    subtotals = {}
    for field in fields[2:]:
        totals[field] = 0.0 # actual column totals
        subtotals[field] = 0.0 #calculated column totals
    airport_data[airport_csv][0] = ','.join(fields)
    first = True
    for rec in db:
        old_taz_origin = int(rec['ORIG'])
        old_taz_dest = int(rec['DEST'])
        if first:
            if inbound:
                airport_data[airport_csv][-1] = ','.join(map(str,[] + ['0']*(len(fields) - 2))) #empty line
            else:
                airport_data[airport_csv][-1] = ','.join(map(str,[] + ['0']*(len(fields) - 2))) #empty line
            first = False
        for field in totals:
            totals[field] += rec[field]
        if inbound:
            if not old_taz_origin in taz_old2new:
                if not old_taz_origin in skipped:
                    skipped[old_taz_origin] = 0
                for field in fields[2:]:
                    skipped[old_taz_origin] += rec[field]
                continue
            if first:
                airport_data[airport_csv][-1] = ','.join(map(str,['%d',airport] + ['0']*(len(fields) - 2))) #empty line
                first = False
            airport = taz_old2new[old_taz_dest][0]
            for taz in taz_old2new[old_taz_origin]:
                taz = int(taz)
                percent = taz_mapping[taz][1]
                data = [taz,airport]
                for field in fields[2:]: #skip origin/destination
                    value = rec[field]*percent
                    data.append(value)
                    subtotals[field] += value
                airport_data[airport_csv][taz] = data
        else:
            if not old_taz_dest in taz_old2new:
                if not old_taz_dest in skipped:
                    skipped[old_taz_dest] = 0
                for field in fields[2:]:
                    skipped[old_taz_dest] += rec[field]
                continue
            if first:
                airport_data[airport_csv][-1] = ','.join(map(str,[airport,'%d'] + ['0']*(len(fields) - 2))) #empty line
                first = False
            airport = taz_old2new[old_taz_origin][0]
            for taz in taz_old2new[old_taz_dest]:
                taz = int(taz)
                percent = taz_mapping[taz][1]
                data = [airport,taz]
                for field in fields[2:]: #skip origin/destination
                    value = rec[field]*percent
                    data.append(value)
                    subtotals[field] += value
                airport_data[airport_csv][taz] = data
    db.close()
    #apply correction so that trip totals match
    correction = {}
    for field in totals:
        if subtotals[field] == 0.0:
            correction[field] = 1.0
        else:
            correction[field] = totals[field] / subtotals[field]
    for taz in airport_data[airport_csv]:
        if taz < 1:
            continue #skip default and field headers
        data = airport_data[airport_csv][taz]
        for i in range(2,len(data)):
            data[i] *= correction[fields[i]]
        airport_data[airport_csv][taz] = ','.join(map(str,data))

print "writing files"
tazs = pop.keys()
tazs.sort()
for airport_csv in airport_data:
    with open(airport_csv,'wb') as f:
        data = airport_data[airport_csv]
        default = data[-1]
        f.write(data[0] + os.linesep)
        for taz in tazs:
            if not taz in data:
                f.write((default % (taz)) + os.linesep)
            else:
                f.write(data[taz] + os.linesep)

for taz in skipped:
    print str(taz) + ':' + str(skipped[taz])
print len(skipped.keys())
