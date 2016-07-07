
import os,sys,csv,math
from rtree import index

model_run_dir = sys.argv[1]

ZONE_SEQ_FILE = os.path.join(model_run_dir,r'hwy\mtc_final_network_zone_seq.csv')
NODE_CSV_FILE = os.path.join(model_run_dir,r'documentation\mtc_final_network_with_tolls_nodes.csv')
OUTFILE_BASE = os.path.join(model_run_dir,r'documentation\distance_euclidean_')

maz_maz_buff = 3*5280
maz_tap_buff = 3*5280
tap_tap_buff = 0.5*5280
maz_maz_drive_buff = 5*5280

print "Reading MAZ/TAZ/TAP numbers"
mazs = {}
tazs = {}
taps = {}
with open(ZONE_SEQ_FILE,'rb') as csvfile:
    zone_reader = csv.reader(csvfile,skipinitialspace=True)
    for row in zone_reader:
        data = map(int,row)
        if data[1] > 0:
            tazs[data[0]] = None
        elif data[2] > 0:
            mazs[data[0]] = None
        elif data[3] > 0:
            taps[data[0]] = None
  
print "Reading nodes"
maz_index = index.Index()
maz_tap_index = index.Index()
#taz_index = index.Index()
tap_index = index.Index()
with open(NODE_CSV_FILE,'rb') as node_file:
    node_reader = csv.reader(node_file,skipinitialspace=True)
    for row in node_reader:
        n = int(row[0])
        xCoord = float(row[1])
        yCoord = float(row[2])
        if n in mazs:
            mazs[n] = (xCoord,yCoord)
            maz_index.insert(n,(xCoord, yCoord, xCoord, yCoord))
            maz_tap_index.insert(n,(xCoord, yCoord, xCoord, yCoord))
        if n in tazs:
            tazs[n] = (xCoord,yCoord)
            #taz_index.insert(n,(xCoord, yCoord, xCoord, yCoord))
        if n in taps:
            taps[n] = (xCoord,yCoord)
            tap_index.insert(n,(xCoord, yCoord, xCoord, yCoord))
            maz_tap_index.insert(n,(xCoord, yCoord, xCoord, yCoord))

def euclideanDistance(a,b):
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

print 'writing maz-maz pairs'
finished_pairs = {}
buffer = maz_maz_buff
with open(OUTFILE_BASE + 'maz_maz.csv','wb') as outfile:
    for maz in mazs:
        coord = mazs[maz]
        x,y = coord
        close_mazs = maz_index.intersection((x-buffer,y-buffer,x+buffer,y+buffer))
        for id in close_mazs:
            if (id,maz) in finished_pairs:
                continue
            outfile.write(','.join(map(str,[maz,id,euclideanDistance(coord,mazs[id])])) + os.linesep)
            finished_pairs[(maz,id)] = None

print 'writing maz-maz drive pairs' #skips walk pairs - already in buffer
buffer = maz_maz_drive_buff
with open(OUTFILE_BASE + 'maz_maz_drive.csv','wb') as outfile:
    for maz in mazs:
        coord = mazs[maz]
        x,y = coord
        close_mazs = maz_index.intersection((x-buffer,y-buffer,x+buffer,y+buffer))
        for id in close_mazs:
            if (id,maz) in finished_pairs:
                continue
            outfile.write(','.join(map(str,[maz,id,euclideanDistance(coord,mazs[id])])) + os.linesep)
            finished_pairs[(maz,id)] = None

print 'writing tap-tap pairs'
finished_pairs = {}
buffer = tap_tap_buff
with open(OUTFILE_BASE + 'tap_tap.csv','wb') as outfile:
    for tap in taps:
        coord = taps[tap]
        x,y = coord
        close_taps = tap_index.intersection((x-buffer,y-buffer,x+buffer,y+buffer))
        for id in close_taps:
            if (id,tap) in finished_pairs:
                continue
            outfile.write(','.join(map(str,[tap,id,euclideanDistance(coord,taps[id])])) + os.linesep)
            finished_pairs[(tap,id)] = None

print 'writing maz-tap pairs'
finished_pairs = {}
buffer = maz_tap_buff
with open(OUTFILE_BASE + 'maz_tap.csv','wb') as outfile:
    for maz in mazs:
        coord = mazs[maz]
        x,y = coord
        close_taps = maz_tap_index.intersection((x-buffer,y-buffer,x+buffer,y+buffer))
        for tap in close_taps:
            if not tap in taps:
                continue
            outfile.write(','.join(map(str,[maz,tap,euclideanDistance(coord,taps[tap])])) + os.linesep)

print 'writing taz-taz pairs'
finished = {}
with open(OUTFILE_BASE + 'taz_taz.csv','wb') as outfile:
    for ftaz in tazs:
        coord = tazs[ftaz]
        x,y = coord
        for ttaz in tazs:
            if ttaz in finished:
                continue
            outfile.write(','.join(map(str,[ftaz,ttaz,euclideanDistance(coord,tazs[ttaz])])) + os.linesep)
        finished[ftaz] = None
