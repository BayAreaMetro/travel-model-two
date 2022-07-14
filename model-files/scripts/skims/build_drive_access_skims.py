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
    updated: 12/2021 by david.hensle@rsginc.com

"""

import csv,os,sys,re
import time as pytime
import pandas as pd

base_dir = sys.argv[1]
block_dir = sys.argv[2]

PERIOD_TOKEN = '@PERIOD@'
id_mode_map = {1:'LOCAL_BUS',
               2:'EXPRESS_BUS',
               3:'FERRY_SERVICE',
               4:'LIGHT_RAIL',
               5:'HEAVY_RAIL',
               6:'COMMUTER_RAIL'}

mode_settings_dict = {
    # mode: maximum taz->tap drive dist in miles, closest number of taps to include
    'LOCAL_BUS': {'MAX_DIST': 10, 'N_TAPS': 1},
    'EXPRESS_BUS': {'MAX_DIST': 10, 'N_TAPS': 1},
    'FERRY_SERVICE': {'MAX_DIST': 30, 'N_TAPS': 1},
    'LIGHT_RAIL': {'MAX_DIST': 15, 'N_TAPS': 2},
    'HEAVY_RAIL': {'MAX_DIST': 15, 'N_TAPS': 2},
    'COMMUTER_RAIL': {'MAX_DIST': 15, 'N_TAPS': 2},
}
#input files
#skim_taz_to_node_file = os.path.join(base_dir,r'hwy\avgload' + PERIOD_TOKEN + '_taz_to_node.txt')
#taz_to_tazn_mapping_file = os.path.join(base_dir,r'hwy\node_maz_taz_data.csv')
#maz_to_taz_mapping_file = os.path.join(base_dir,r'hwy\node_maz_taz_lookup.csv')
maz_to_taz_mapping_file = os.path.join(base_dir,r'landuse\maz_data_withDensity.csv')
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

print('reading node->taz/maz/tap sequence mapping')
seq_mapping = {}
tazseq_mapping = {}
mazseq_mapping = {}
tapseq_mapping = {}
extseq_mapping = {}
reader = csv.DictReader(open(n_seq_file))
for data in reader:
    if int(data["TAZSEQ"]) > 0:
        seq_mapping[   int(data["N"     ])] = int(data["TAZSEQ"])
        tazseq_mapping[int(data["TAZSEQ"])] = int(data["N"     ])
    if int(data["MAZSEQ"]) > 0:
        seq_mapping[   int(data["N"     ])] = int(data["MAZSEQ"])
        mazseq_mapping[int(data["MAZSEQ"])] = int(data["N"     ])
    if int(data["TAPSEQ"]) > 0:
        seq_mapping[   int(data["N"     ])] = int(data["TAPSEQ"])
        tapseq_mapping[int(data["TAPSEQ"])] = int(data["N"     ])
    if int(data["EXTSEQ"]) > 0:
        seq_mapping[   int(data["N"     ])] = int(data["EXTSEQ"])
        extseq_mapping[int(data["EXTSEQ"])] = int(data["N"     ])

print('reading maz->taz')
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
print('reading hwy parameter block data')
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

print('reading maz->tap skims and building tap->maz/taz lookup')
#read maz->tap walk skims
#build tap-> (closest) (maz,taz,maz->tap walk_time)
tapn_tazn_lookup = {}
tapns = {}
for line in open(ped_maz_tap_distance_file):
    line = line.strip().split(',')
    try:
        mazn = mazseq_mapping[int(line[0])]
        tapn = tapseq_mapping[int(line[1])]
    except Exception as e:
        if line==['']: continue     # continue blank line
        if line==['\x1a']: continue # continue on EOF -- for loop will end
        print(e)
        print("line={}".format(line))
        raise e
    distance = float(line[4])
    walk_time = walk_rate*distance
    tapns[tapn] = None
    tazn = mazn_tazn_mapping[mazn]
    if (not tapn in tapn_tazn_lookup) or (tapn_tazn_lookup[tapn][2] > walk_time):
        tapn_tazn_lookup[tapn] = (mazn,tazn,walk_time,distance)
tapns = list(tapns.keys())
tapns.sort()


print('reading transit lines from {}'.format(transit_line_file))
#read transit lines to pull out tod and stop information
stops_by_tod_and_mode = {}
for period in periods:
    stops_by_tod_and_mode[period] = {}
#LINE NAME="EM_HOLLIS", USERA1="Emery Go-Round", USERA2="Local bus", MODE=12, ONEWAY=T, XYSPEED=15, HEADWAY[1]=60.0, HEADWAY[2]=12.0, HEADWAY[3]=20.0, HEADWAY[4]=12.0, HEADWAY[5]=30.0, N=2565595,...
trn_line = ""
for temp_line in open(transit_line_file):
    # strip leading and trailing whitespace
    temp_line = temp_line.strip()

    # if our line has a comment - cut it out
    semicolon_index = temp_line.find(";")
    if semicolon_index >= 0:
        temp_line = temp_line[:semicolon_index].strip()

    # skip blank lines
    if len(temp_line)==0: continue

    # append to our transit line string
    trn_line = trn_line + temp_line

    # if it ends in a comma, continue until we find the end
    if temp_line[-1] == "," or temp_line[-2] == "N":
        continue

    # print("trn_line={}".format(trn_line))

    # split it on equals or comma
    split_line = list(map(str.strip, re.split("[=,]", trn_line)))
    # print("split_line={}".format(split_line))

    if len(split_line) < 3:
        continue
    mode = split_line[split_line.index('USERA2') + 1].replace('"','').upper().replace(' ','_')
    # print("mode={}".format(mode))

    tod = []
    for i in range(len(periods)):
        if "HEADWAY[{index}]".format(index=i + 1) not in split_line:
            tod.append(False)
        else:
            tod.append(
                float(split_line[split_line.index("HEADWAY[" + str(i + 1) + "]") + 1])
                > 0.0
            )
        period = periods[i]
        if not mode in stops_by_tod_and_mode[period]:
            stops_by_tod_and_mode[period][mode] = {}
    # print("tod={}".format(tod))
    # print("stops_by_tod_and_mode={}".format(stops_by_tod_and_mode))

    stop_nodes = {}
    iter = split_line.index('N') + 1
    while iter < len(split_line):
        #skip NNTIME,TIME,ACCESS,etc token and value
        if split_line[iter] in ["NNTIME", "TIME", "ACCESS", "ACCESS_C", "DELAY", "DELAY_C", "DWELL", "DWELL_C"]:
            iter = iter + 2
            continue
        #skip N token
        if (split_line[iter] == "N"):
            iter = iter + 1
            continue
        n = int(split_line[iter])
        if n > 0:
           stop_nodes[n] = None
        iter = iter + 1
#    for i in range(split_line.index('N') + 1,len(split_line)):
#        n = int(split_line[i])
#        if n > 0:
#            stop_nodes[n] = None
    for i in range(len(tod)):
        if tod[i]:
            for n in stop_nodes:
                stops_by_tod_and_mode[periods[i]][mode][n] = None
    trn_line = ""


print('building tap->mode')
all_tapn = []
for line in open(network_tap_nodes_file):
    all_tapn.append(int(line))

print('building tod->mode->taps')
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
    if not tapn in all_tapn:
        print('tapn not found in ({}),{})'.format(a,b))
        continue
    # mode = tapn_to_mode[tapn]
    for mode_id in id_mode_map:
        mode = id_mode_map[mode_id]
        for period in periods:
            if not tapn in tod_mode_tapn[period][mode]:
                # check to see if tap is available in this period
                if stopn in stops_by_tod_and_mode[period][mode]:
                    if not tapn in tapn_tazn_lookup:
                        isolated_tapns[tapn] = None
                    else:
                        tod_mode_tapn[period][mode][tapn] = tapn_tazn_lookup[
                            tapn
                        ]  # closest (mazn,tazn,walk_time from mazn to tapn,walk_distance from mazn to tapn)

print('taps with no (apparent) walk access: {}'.format(isolated_tapns.keys()))


# ------------------------------------------
# modifications to extend number of taps and set maximum distances

# turn above dictionary into pandas dataframe
tod_mode_tapn_df = pd.DataFrame.from_dict({(i,j,k): tod_mode_tapn[i][j][k]
                                          for i in tod_mode_tapn.keys()
                                          for j in tod_mode_tapn[i].keys()
                                          for k in tod_mode_tapn[i][j].keys()},
                                         orient='index',
                                         columns=['TMAZ', 'TTAZ', 'WTIME', 'WDIST'])

tod_mode_tapn_df[['PERIOD', 'MODE', 'TTAP']] = pd.DataFrame(tod_mode_tapn_df.index.to_list(), index=tod_mode_tapn_df.index)
tod_mode_tapn_df.reset_index(inplace=True, drop=True)

tod_mode_tapn_df['TMAZ'] = tod_mode_tapn_df['TMAZ'].map(seq_mapping)
tod_mode_tapn_df['TTAZ'] = tod_mode_tapn_df['TTAZ'].map(seq_mapping)
tod_mode_tapn_df['TTAP'] = tod_mode_tapn_df['TTAP'].map(seq_mapping)

# build each time period separately and concatenate results at the end
# (building separately because each time period has different skims and network)
total_table_array = []
for period in periods:
    print('building drive access skims for period {}'.format(period))
    # grab taps serviced in this period and their tazs
    taps_for_period = tod_mode_tapn_df.loc[tod_mode_tapn_df['PERIOD'] == period]

    # read the taz->taz skim
    taz_skim_df = pd.read_csv(skim_taz_taz_time_file.replace(PERIOD_TOKEN,period),
                              names=['FTAZ', 'TTAZ', 'unknown', 'DTIME', 'DDIST', 'DTOLL'])

    # reduce the size of the file before merge
    largest_dist = max([mode_settings_dict[mode]['MAX_DIST'] for mode in mode_settings_dict.keys()])
    taz_skim_df = taz_skim_df[(taz_skim_df['DDIST'] < largest_dist) & taz_skim_df['TTAZ'].isin(taps_for_period['TTAZ'])]

    # set time of day period
    taz_skim_df['PERIOD'] = period

    # join skim values to taps
    tod_mode_tapn_costs = pd.merge(
        taz_skim_df[['FTAZ', 'TTAZ','PERIOD', 'DTIME', 'DDIST', 'DTOLL']],
        taps_for_period,
        how='left',
        on=['TTAZ', 'PERIOD'])

    # discard any tazs that do not contain a tap
    tod_mode_tapn_costs = tod_mode_tapn_costs[~tod_mode_tapn_costs['TTAP'].isna()]

    # select the nearest N TAPS by mode within the maximum set drive distance
    all_tod_available_taps = None
    for mode in mode_settings_dict.keys():
#         print(mode)
        max_dist = mode_settings_dict[mode]['MAX_DIST']
        n_taps = mode_settings_dict[mode]['N_TAPS']
#         print(f"max_dist: {max_dist}, n_taps: {n_taps}")

        mode_cut = tod_mode_tapn_costs[
            (tod_mode_tapn_costs['MODE'] == mode)
            & (tod_mode_tapn_costs['DDIST'] < max_dist)]

        if len(mode_cut) == 0:
            print("No taps within {} miles for mode {}".format(max_dist, mode))
            continue

        # select entries for the closest N taps to this TAZ for this mode and this time of day
        selection = mode_cut.groupby(['FTAZ', 'PERIOD', 'MODE'])['DDIST'].nsmallest(n_taps)

        # get index locations of selection to extract from the full list
        # groupby can end up with only one index level due to unique values (this happens for ferrys)
        if selection.index.nlevels == 1:
            available_taps = selection.index
        else:
            available_taps = selection.index.get_level_values(3)

        # create a list of index values for selected taps accross all modes
        if all_tod_available_taps is None:
            all_tod_available_taps = available_taps
        else:
            all_tod_available_taps = all_tod_available_taps.append(available_taps)

    # create an array of selected taz->tap dataframes, one for each time of day period
    total_table_array.append(tod_mode_tapn_costs.loc[all_tod_available_taps])

# Join all time periods back together
final_df = pd.concat(total_table_array)

# fill missing toll values
final_df['DTOLL'] = final_df['DTOLL'].fillna(0)

print('writing drive access skim results')
output_col_order = ['FTAZ', 'MODE', 'PERIOD', 'TTAP', 'TMAZ', 'TTAZ', 'DTIME', 'DDIST', 'DTOLL', 'WDIST']
final_df[output_col_order].to_csv(drive_tansit_skim_out_file, index=False)

end_time = pytime.time()
print('elapsed time in minutes: {}'.format((end_time - start_time) / 60.0))
