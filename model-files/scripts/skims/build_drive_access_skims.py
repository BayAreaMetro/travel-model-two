"""
    build_drive_access_skims.py model_run_dir block_file_dir

    inputs: model_run_dir - the directory the model is running in (directory with INPUTS, hwy, etc.)
            block_file_dir - the directory holding the block parameter files

    This script builds transit drive access skims. It takes the following inputs:
    
        1) TAZ->TAZ highway skims (time) by time-of-day
        2) MAZ->TAZ correspondence
        3) MAZ->TAP walk access skims
        4) N->(TAZ/MAZ/TAP/EXT) SEQ correspondence
    
    The script builds (by time-of-day), the shortest path from each TAZ->TAP by creating a virtual
    shortest path from TAZ->TAZ->MAZ->TAP. The first link is given by the highway skim (1), the 
    second value (zero-cost) is provided by the MAZ-TAZ corresponence (2). The third link is 
    privided by the MAZ->TAP walk access skim.
    
    The output of this script is a csv file with the following columns:
    
        FTAZ,MODE,PERIOD,TTAP,TMAZ,TTAZ,DTIME,DDIST,DTOLL,WDIST
    
    Where:
        FTAZ - From TAZ (sequential numbering)
        MODE - The (transit) mode
        PERIOD - The time period
        TTAP - To TAP (sequential numbering)
        TMAZ - To MAZ (sequential numbering)
        TTAZ - To TAZ (sequential numbering)
        DTIME - Drive time
        DDIST - Drive distance
        DTOLL - Drive bridge toll
        WDIST - Walk access distance
    
    crf 8/2013

"""

import os,sys,re
import time as pytime

base_dir = sys.argv[1]
block_dir = sys.argv[2]

PERIOD_TOKEN = '@PERIOD@'
id_mode_map = {1:'LOCAL_BUS',
               2:'EXPRESS_BUS',
               #3:'FERRY_SERVICE',
               3:'LIGHT_RAIL',
               4:'LIGHT_RAIL',
               5:'HEAVY_RAIL',
               6:'COMMUTER_RAIL'}
#input files
#skim_taz_to_node_file = os.path.join(base_dir,r'hwy\avgload' + PERIOD_TOKEN + '_taz_to_node.txt')
#taz_to_tazn_mapping_file = os.path.join(base_dir,r'hwy\node_maz_taz_data.csv')
#maz_to_taz_mapping_file = os.path.join(base_dir,r'hwy\node_maz_taz_lookup.csv')
maz_to_taz_mapping_file = os.path.join(base_dir,r'landuse\maz_data.csv')
hwy_parameter_block_file = os.path.join(block_dir,r'hwyParam.block')
ped_maz_tap_distance_file = os.path.join(base_dir,r'skims\ped_distance_maz_tap.txt')
transit_line_file = os.path.join(base_dir,r'trn\transitLines.lin')
network_tap_nodes_file = os.path.join(base_dir,r'hwy\mtc_final_network_tap_nodes.csv')
network_tap_links_file = os.path.join(base_dir,r'hwy\mtc_final_network_tap_links.csv')
skim_taz_taz_time_file = os.path.join(base_dir,r'skims\DA_' + PERIOD_TOKEN + '_taz_time.csv')
drive_tansit_skim_out_file = os.path.join(base_dir,r'skims\drive_maz_taz_tap.csv')
n_seq_file = os.path.join(base_dir,r'hwy\mtc_final_network_zone_seq.csv')



start_time = pytime.time()

periods = ['EA','AM','MD','PM','EV']

print 'reading node->taz/maz/tap sequence mapping'
seq_mapping = {}
tazseq_mapping = {}
mazseq_mapping = {}
tapseq_mapping = {}
extseq_mapping = {}
for line in open(n_seq_file):
    data = map(int,line.strip().split(','))
    if data[1] > 0:
        seq_mapping[data[0]] = data[1]
        tazseq_mapping[data[1]] = data[0]
    if data[2] > 0:
        seq_mapping[data[0]] = data[2]
        mazseq_mapping[data[2]] = data[0]
    if data[3] > 0:
        seq_mapping[data[0]] = data[3]
        tapseq_mapping[data[3]] = data[0]
    if data[4] > 0:
        seq_mapping[data[0]] = data[4]
        extseq_mapping[data[4]] = data[0]

print 'reading maz->taz'
#read maz->taz mapping
mazn_tazn_mapping = {}
#maz,taz
header = None
for line in open(maz_to_taz_mapping_file):
    data = line.strip().split(',')
    if header is None:
        header = data
        col_taz = header.index('TAZ_ORIGINAL')
        col_maz = header.index('MAZ_ORIGINAL')
        continue
    mazn_tazn_mapping[int(data[col_maz])] = int(data[col_taz])
    
#read param block
print 'reading hwy parameter block data'
block_data = {}
for line in open(hwy_parameter_block_file):
    line = line.strip()
    if len(line) == 0:
        continue
    line = line.split('=')
    key = line[0].strip()
    value = float(line[1].split(';')[0].strip())
    block_data[key] = value
    
global auto_op_cost
global vot
global walk_rate
auto_op_cost = block_data['AUTOOPCOST'] / 5280 #correct for feet
vot = 0.6 / block_data['VOT'] #turn into minutes / cents
walk_rate = 60.0 / 3.0 / 5280.0

print 'reading maz->tap skims and building tap->maz/taz lookup'
#read maz->tap walk skims
#build tap-> (closest) (maz,taz,maz->tap walk_time)
tapn_tazn_lookup = {}
tapns = {}
for line in open(ped_maz_tap_distance_file):
    line = line.strip().split(',')
    mazn = mazseq_mapping[int(line[0])]
    tapn = tapseq_mapping[int(line[1])]
    distance = float(line[4])
    walk_time = walk_rate*distance
    tapns[tapn] = None
    tazn = mazn_tazn_mapping[mazn]
    if (not tapn in tapn_tazn_lookup) or (tapn_tazn_lookup[tapn][2] > walk_time):
        tapn_tazn_lookup[tapn] = (mazn,tazn,walk_time,distance)
tapns = list(tapns.keys())
tapns.sort()


print 'reading transit lines'
#read transit lines to pull out tod and stop information
stops_by_tod_and_mode = {}
for period in periods:
    stops_by_tod_and_mode[period] = {}
#LINE NAME="EM_HOLLIS", USERA1="Emery Go-Round", USERA2="Local bus", MODE=12, ONEWAY=T, XYSPEED=15, HEADWAY[1]=60.0, HEADWAY[2]=12.0, HEADWAY[3]=20.0, HEADWAY[4]=12.0, HEADWAY[5]=30.0, N=2565595,...
for line in open(transit_line_file):
    split_line = map(str.strip,re.split('[=,]',line.strip()))
    if len(split_line) < 3:
        continue
    mode = split_line[split_line.index('USERA2') + 1].replace('"','').upper().replace(' ','_')
    tod = []
    for i in range(len(periods)):
        tod.append(float(split_line[split_line.index('HEADWAY[' + str(i+1) + ']') + 1]) > 0.0)
        period = periods[i]
        if not mode in stops_by_tod_and_mode[period]:
            stops_by_tod_and_mode[period][mode] = {}
    stop_nodes = {}
    for i in range(split_line.index('N') + 1,len(split_line)):
        n = int(split_line[i])
        if n > 0:
            stop_nodes[n] = None
    for i in range(len(tod)):
        if tod[i]:
            for n in stop_nodes:
                stops_by_tod_and_mode[periods[i]][mode][n] = None

                
id_mode_map = {1:'LOCAL_BUS',
               2:'EXPRESS_BUS',
               #3:'FERRY_SERVICE',
               3:'LIGHT_RAIL',
               4:'LIGHT_RAIL',
               5:'HEAVY_RAIL',
               6:'COMMUTER_RAIL'}
print 'building tap->mode'
tapn_to_mode = {}
for line in open(network_tap_nodes_file):
    tapn,mode = map(int,line.strip().split(','))
    tapn_to_mode[tapn] = id_mode_map[mode]

    
print 'building tod->mode->taps'
tod_mode_tapn = {}
for period in periods:
    tod_mode_tapn[period] = {}
    for mode_id in id_mode_map:
        tod_mode_tapn[period][id_mode_map[mode_id]] = {}
isolated_tapns = {}
for line in open(network_tap_links_file):
    a,b = map(int,line.strip().split(','))
    if (a < 900000) and (a % 100000 > 90000):
        tapn = a
        stopn = b
    else:
        tapn = b
        stopn = a
    #stops_by_tod_and_mode[periods[i]][mode][n]
    if not tapn in tapn_to_mode:
        print 'tapn not found in (' + str(a) + ',' + str(b) + ')'
        continue
    mode = tapn_to_mode[tapn]
    for period in periods:
        if not tapn in tod_mode_tapn[period][mode]:
            #check to see if tap is available in this period
            if stopn in stops_by_tod_and_mode[periods[i]][mode]:
                if not tapn in tapn_tazn_lookup:
                    isolated_tapns[tapn] = None
                else:
                    tod_mode_tapn[period][mode][tapn] = tapn_tazn_lookup[tapn] #closest (mazn,tazn,walk_time from mazn to tapn,walk_distance from mazn to tapn)
print 'taps with no (apparent) walk access: ' + str(isolated_tapns.keys())

print 'building list of tazs with taps by tod'
tazs_with_taps = {} #period -> tazs
for period in periods:
    tazs_with_taps[period] = {}
    for mode in tod_mode_tapn[period]:
        for tapn in tod_mode_tapn[period][mode]:
            tazs_with_taps[period][tod_mode_tapn[period][mode][tapn][1]] = None

            
def formCost(time,dist,toll):
    return time + vot*(dist * auto_op_cost + toll)



# tod_mode_tapn[period][mode][tapn] = (mazn,tazn,distance)
drive_access_costs = {}
for period in periods:
    
    print 'reading taz->taz skim for ' + period + ' and building drive access skim'
    #read the taz->taz skim
    #skimtaz_tazn_map = skimtaz_tazn_mapping[period]
    skimtaz_tazn_map = tazseq_mapping
    tazn_tazn_skim = {}
    tazns = {} #unique set of taz nodes
    
    for line in open(skim_taz_taz_time_file.replace(PERIOD_TOKEN,period)):
        line = line.strip().split(',') #1,1,1,0.21,460.5  #I,J,[something],TIMEDA,DISTDA[,BTOLLDA]
        ftazn = skimtaz_tazn_map[int(line[0])]
        ttazn = skimtaz_tazn_map[int(line[1])]
        if not ftazn in tazn_tazn_skim:
            tazn_tazn_skim[ftazn] = {}
        if ttazn in tazs_with_taps[period]:
            time = float(line[3])
            dist = float(line[4])
            toll = 0.0
            if len(line) == 6:
                toll = float(line[5])
            tazn_tazn_skim[ftazn][ttazn] = (formCost(time,dist,toll),time,dist,toll)
        tazns[ftazn] = None
    tazns = list(tazns.keys())
    tazns.sort()
    
    print 'building drive access skims for period ' + period
    drive_access_costs[period] = {}
    for mode_id in id_mode_map:
        mode = id_mode_map[mode_id]
        drive_access_costs[period][mode] = {}
        for tazn in tazns:
            drive_access_costs[period][mode][tazn] = None
            for tapn in tod_mode_tapn[period][mode]:
                tapn_costs = tod_mode_tapn[period][mode][tapn]
                cost = tazn_tazn_skim[tazn][tapn_costs[1]][0] + tapn_costs[2]
                if (drive_access_costs[period][mode][tazn] is None) or (drive_access_costs[period][mode][tazn][0] > cost):
                    drive_access_costs[period][mode][tazn] = (cost,tapn)
    
print 'writing drive access skim results'
f = open(drive_tansit_skim_out_file,'wb')
f.write(','.join(['FTAZ','MODE','PERIOD','TTAP','TMAZ','TTAZ','DTIME','DDIST','DTOLL','WDIST']) + os.linesep)
for period in drive_access_costs:
    for mode in drive_access_costs[period]:
        for tazn in drive_access_costs[period][mode]:
            if not drive_access_costs[period][mode][tazn] is None:
                tapn = drive_access_costs[period][mode][tazn][1]
                (tmazn,ttazn,wtime,wdist) = tod_mode_tapn[period][mode][tapn]
                (fcost,time,dist,toll) = tazn_tazn_skim[tazn][ttazn]
                f.write(','.join(map(str,[seq_mapping[tazn],mode,period,seq_mapping[tapn],seq_mapping[tmazn],seq_mapping[ttazn],time,dist,toll,wdist])) + os.linesep)
f.close()
    
end_time = pytime.time()
print 'elapsed time in seconds: ' + str((end_time - start_time) / 1000.0)


        
