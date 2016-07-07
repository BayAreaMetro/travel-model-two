import os,sys,csv

BASE_DIR = sys.argv[1]
PED_LINKS = os.path.join(BASE_DIR,r'documentation\mtc_ped_network_links.csv')
BIKE_LINKS = os.path.join(BASE_DIR,r'documentation\mtc_bike_network_links.csv')
MOTORIZED_LINKS = os.path.join(BASE_DIR,r'documentation\mtc_md_auto_network_links.csv')
SEQ_FILE = os.path.join(BASE_DIR,r'hwy\mtc_final_network_zone_seq.csv')

TAP_TAP_EUCLID = os.path.join(BASE_DIR,r'documentation\distance_euclidean_tap_tap.csv')
TAZ_TAZ_EUCLID = os.path.join(BASE_DIR,r'documentation\distance_euclidean_taz_taz.csv')
MAZ_MAZ_EUCLID = os.path.join(BASE_DIR,r'documentation\distance_euclidean_maz_maz.csv')
MAZ_TAP_EUCLID = os.path.join(BASE_DIR,r'documentation\distance_euclidean_maz_tap.csv')
MAZ_MAZ_DRIVE_EUCLID = os.path.join(BASE_DIR,r'documentation\distance_euclidean_maz_maz_drive.csv')

TAP_TAP_PED_SKIM = os.path.join(BASE_DIR,r'skims\ped_distance_tap_tap.txt')
MAZ_TAP_PED_SKIM = os.path.join(BASE_DIR,r'skims\ped_distance_maz_tap.txt')
MAZ_MAZ_PED_SKIM = os.path.join(BASE_DIR,r'skims\ped_distance_maz_maz.txt')
TAZ_TAZ_BIKE_SKIM = os.path.join(BASE_DIR,r'skims\bike_distance_taz_taz.txt')
MAZ_TAP_BIKE_SKIM = os.path.join(BASE_DIR,r'skims\bike_distance_maz_tap.txt')
MAZ_MAZ_BIKE_SKIM = os.path.join(BASE_DIR,r'skims\bike_distance_maz_maz.txt')
MAZ_MAZ_DRIVE_SKIM = os.path.join(BASE_DIR,r'skims\HWYSKIM_MAZMAZ_DIST_DA.txt')
MAZ_MAZ_DRIVE_TOLL_SKIM = os.path.join(BASE_DIR,r'skims\HWYSKIM_MAZMAZ_BTOLL_DA.txt')

TIME_TOKEN = '@token_period@'
TIME_PERIODS = ['EA','AM','MD','PM','EV']
TAZ_TAZ_DA = os.path.join(BASE_DIR,r'documentation\skim_da_' + TIME_TOKEN + '_taz.csv')
TAZ_TAZ_COM = os.path.join(BASE_DIR,r'documentation\skim_com_' + TIME_TOKEN + '_taz.csv')
AIR_TRIPS = os.path.join(BASE_DIR,r'documentation\air_' + TIME_TOKEN + '_taz.csv')
IX_TRIPS = os.path.join(BASE_DIR,r'documentation\ix_' + TIME_TOKEN + '_taz.csv')
TRUCK_PAS = os.path.join(BASE_DIR,r'nonres\TruckTG.dat')
TRUCK_TRIPS = os.path.join(BASE_DIR,r'documentation\trucks_' + TIME_TOKEN + '_taz.csv')
#AIR_2005_TRIPS = os.path.join(BASE_DIR,r'documentation\air_2005_taz.csv')

SAMPLE_SIZE = 0.2
INDIV_TRIP_FILE = os.path.join(BASE_DIR,r'ctramp_output\indivTripData_2.csv')
INDIV_TOUR_FILE = os.path.join(BASE_DIR,r'ctramp_output\indivTourData_2.csv')
JOINT_TRIP_FILE = os.path.join(BASE_DIR,r'ctramp_output\jointTripData_2.csv')
JOINT_TOUR_FILE = os.path.join(BASE_DIR,r'ctramp_output\jointTourData_2.csv')
CTRAMP_PERSON_DATA_FILE = os.path.join(BASE_DIR,r'ctramp_output\personData_2.csv')

PED_NETWORK_OUT = os.path.join(BASE_DIR,r'documentation\mtc_ped_network_data.csv')
BIKE_NETWORK_OUT = os.path.join(BASE_DIR,r'documentation\mtc_bike_network_data.csv')
MOTORIZED_NETWORK_OUT = os.path.join(BASE_DIR,r'documentation\mtc_motorized_network_data.csv')
AIR_TRIPS_OUT = os.path.join(BASE_DIR,r'documentation\mtc_air_data.csv')
TRUCK_TRIPS_OUT = os.path.join(BASE_DIR,r'documentation\mtc_truck_data.csv')
IX_TRIPS_OUT = os.path.join(BASE_DIR,r'documentation\mtc_ix_data.csv')
CTRAMP_TT_OUT = os.path.join(BASE_DIR,r'documentation\mtc_ctramp_data.csv')




def nonmotorizedNetworkCrosstab(output_file,network_file):
    ft_cntype = {}
    ft_length = {}
    cntype_length = {}
    #A,B,CNTYPE,FT,FEET,HIGWAYT,PEDFLAG
    with open(network_file) as network:
        for line in network:
            line = line.strip()
            if len(line) == 0:
                continue
            line = line.split(',')
            cntype = line[2]
            ft = int(line[3])
            if (ft == 0) and ((len(line[5]) > 3) or (line[6].find('Y') > -1)):
                ft = 'pedestrian'
            length = float(line[4])
            if not ft in ft_cntype:
                ft_cntype[ft] = {}
                ft_length[ft] = 0.0
            if not cntype in cntype_length:
                cntype_length[cntype] = 0.0
            if not cntype in ft_cntype[ft]:
                ft_cntype[ft][cntype] = 0
            ft_length[ft] += length
            cntype_length[cntype] += length
            ft_cntype[ft][cntype] += 1
    with open(output_file,'wb') as of:
        cntypes = cntype_length.keys()
        fts = ft_length.keys()
        cntypes.sort()
        fts.sort()
        of.write(','.join(map(str,['ft'] + cntypes)) + os.linesep)
        for ft in fts:
            data = [ft]
            for cntype in cntypes:
                if (ft in ft_cntype) and (cntype in ft_cntype[ft]):
                    data.append(ft_cntype[ft][cntype])
                else:
                    data.append(0)
            of.write(','.join(map(str,data)) + os.linesep)
        
        of.write(os.linesep)
        
        of.write('ft,miles' + os.linesep)
        for ft in fts:
            of.write(','.join(map(str,[ft,ft_length[ft] / 5280.0])) + os.linesep)
        
        of.write(os.linesep)
        
        of.write('cntype,miles' + os.linesep)
        for cntype in cntypes:
            of.write(','.join(map(str,[cntype,cntype_length[cntype] / 5280.0])) + os.linesep)
            
def motorizedNetworkCrosstab(output_file,network_file):
    ft_cntype = {}
    ft_at = {}
    ft_ffs = {}
    ft_ave_ffs = {}
    ft_length = {}
    at_length = {}
    cntype_length = {}
    #A,B,CNTYPE,FT,FFS,AT,FEET,HIGHWAYT,PEDFLAG
    with open(network_file) as network:
        for line in network:
            line = line.strip()
            if len(line) == 0:
                continue
            line = line.split(',')
            cntype = line[2]
            ft = int(line[3])
            if (ft == 0) and ((len(line[7]) > 3) or (line[8].find('Y') > -1)):
                ft = 'pedestrian'
            ffs = float(line[4])
            ffs_class = 0
            if ffs > 0:
                if ffs < 25:
                    ffs_class = 1
                elif ffs < 35:
                    ffs_class = 2
                elif ffs < 45:
                    ffs_class = 3
                elif ffs < 55:
                    ffs_class = 4
                elif ffs < 65:
                    ffs_class = 5
                else:
                    ffs_class = 6
            at = int(line[5])
            length = float(line[6])
            if not ft in ft_cntype:
                ft_cntype[ft] = {}
                ft_length[ft] = 0.0
                ft_at[ft] = {}
                ft_ffs[ft] = {}
                for i in range(7):
                    ft_ffs[ft][i] = 0
                ft_ave_ffs[ft] = 0.0
            if not cntype in cntype_length:
                cntype_length[cntype] = 0.0
            if not at in at_length:
                at_length[at] = 0.0
            if not cntype in ft_cntype[ft]:
                ft_cntype[ft][cntype] = 0
            if not at in ft_at[ft]:
                ft_at[ft][at] = 0
            
            
            ft_length[ft] += length
            cntype_length[cntype] += length
            ft_cntype[ft][cntype] += 1
            ft_at[ft][at] += 1
            ft_ffs[ft][ffs_class] += 1
            ft_ave_ffs[ft] += length * ffs
            at_length[at] += length
    
    with open(output_file,'wb') as of:
        cntypes = cntype_length.keys()
        fts = ft_length.keys()
        ats = at_length.keys()
        cntypes.sort()
        fts.sort()
        of.write(','.join(map(str,['ft'] + cntypes)) + os.linesep)
        for ft in fts:
            data = [ft]
            for cntype in cntypes:
                if (ft in ft_cntype) and (cntype in ft_cntype[ft]):
                    data.append(ft_cntype[ft][cntype])
                else:
                    data.append(0)
            of.write(','.join(map(str,data)) + os.linesep)
        
        of.write(os.linesep)
        
        of.write(','.join(map(str,['ft'] + ats)) + os.linesep)
        for ft in fts:
            data = [ft]
            for at in ats:
                if (ft in ft_at) and (at in ft_at[ft]):
                    data.append(ft_at[ft][at])
                else:
                    data.append(0)
            of.write(','.join(map(str,data)) + os.linesep)
        
        of.write(os.linesep)
        
        of.write(','.join(map(str,['ft'] + range(7))) + os.linesep)
        for ft in fts:
            data = [ft]
            for i in range(7):
                if (ft in ft_ffs):
                    data.append(ft_ffs[ft][i])
                else:
                    data.append(0)
            of.write(','.join(map(str,data)) + os.linesep)
        
        of.write(os.linesep)
        
        of.write('ft,miles' + os.linesep)
        for ft in fts:
            of.write(','.join(map(str,[ft,ft_length[ft] / 5280.0])) + os.linesep)
        
        of.write(os.linesep)
        
        of.write('cntype,miles' + os.linesep)
        for cntype in cntypes:
            of.write(','.join(map(str,[cntype,cntype_length[cntype] / 5280.0])) + os.linesep)
        
        of.write(os.linesep)
        
        of.write('at,miles' + os.linesep)
        for at in ats:
            of.write(','.join(map(str,[at,at_length[at] / 5280.0])) + os.linesep)
        
        of.write(os.linesep)
        
        of.write('ft,average speed' + os.linesep)
        for ft in fts:
            of.write(','.join(map(str,[ft,ft_ave_ffs[ft] / ft_length[ft]])) + os.linesep)
            
def getZoneSeqMapping(file):
    seq_map = {}
    with open(file,'rb') as csvfile:
        zone_reader = csv.reader(csvfile,skipinitialspace=True)
        for row in zone_reader:
            data = map(int,row)
            if data[1] > 0:
                seq = data[1]
            elif data[2] > 0:
                seq = data[2]
            elif data[3] > 0:
                seq = data[3]
            seq_map[data[0]] = seq
    return seq_map

def skimSummary(skim_file,distance_column,zone_euclidean_files,outfile,seq_map):
    ed = {}
    for zone_euclidean_file in zone_euclidean_files:
        with open(zone_euclidean_file) as f:
            for line in f:
                line = line.strip()
                if len(line) == 0:
                    continue
                line = line.split(',')
                a = seq_map[int(line[0])]
                b = seq_map[int(line[1])]
                d = float(line[2])
                ed[(a,b)] = d
                ed[(b,a)] = d
    
    skim_count = 0
    skim_slip_count = 0
    ratio_sum = 0.0
    ratio_max = 0.0
    rmx = ()
    ratio_min = 99999.0
    rmn = ()
    skim_sum = 0.0
    nz_count = 0
    with open(skim_file) as f:
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            line = line.split(',')
            a = int(line[0])
            b = int(line[1])
            d = float(line[distance_column])
            skim_count += 1
            if not (a,b) in ed:
                skim_slip_count += 1
            else:
                edd = ed[(a,b)]
                if edd > 0:
                    ratio = d / edd
                    ratio_sum += ratio
                    if ratio_max < ratio:
                        ratio_max = ratio
                        rmx = (d,edd,a,b)
                    if ratio_min > ratio:
                        ratio_min = ratio
                        rmn = (d,edd,a,b)
            if d > 0:
                skim_sum += d
                nz_count += 1
    ratio_ave = ratio_sum / (skim_count - skim_slip_count)
    nz_average = skim_sum / nz_count
    print('euclidean count: ' + str(len(ed)))
    print('skim count: ' + str(skim_count))
    print('skim slip count: ' + str(skim_slip_count))
    print('ratio average: ' + str(ratio_ave))
    print('ratio max: ' + str(ratio_max) + ' ' + str(rmx))
    print('ratio min: ' + str(ratio_min) + ' ' + str(rmn))
    print('non-zero average: ' + str(nz_average))
    print('non-zero count: ' + str(nz_count))
                    
            

def readTazSkim(time_periods,time_token,taz_skim):
    skims = {}
    for time_period in time_periods:
        skim = {}
        with open(taz_skim.replace(time_token,time_period)) as f:
            for line in f:
                line = line.strip().split(',')
                skim[(int(line[0]),int(line[1]))] = (float(line[3]),float(line[4]))
        skims[time_period] = skim
    return skims
    
def readTazComSkim(time_periods,time_token,taz_skim):
    skims = {}
    for time_period in time_periods:
        skim = {}
        with open(taz_skim.replace(time_token,time_period)) as f:
            for line in f:
                line = line.strip().split(',')
                skim[(int(line[0]),int(line[1]))] = (float(line[3]),float(line[4]),float(line[5]),float(line[6]))
        skims[time_period] = skim
    return skims

def buildAirTripData(skims,time_periods,time_token,trips_files,outfile):
    airports = {947:'SFO',2523:'OAK',1801:'SJC'}
    modes = ['DA','SR2','SR3','DATOLL','SR2TOLL','SR3TOLL']
    outbounds = {}
    inbounds = {}
    for airport in airports:
        outbounds[airport] = 0
        inbounds[airport] = 0
    air_trip_dist = {}
    air_trip_time = {}
    air_trips_outbound = {}
    air_trips_inbound = {}
    for airport in airports:
        air_trip_dist[airport] = {}
        air_trip_time[airport] = {}
        air_trips_outbound[airport] = {}
        air_trips_inbound[airport] = {}
        for i in range(102): #0-1,1-2,...,99-100,100+
            air_trip_dist[airport][i] = 0
        for i in range(122):
            air_trip_time[airport][i] = 0
        for mode in modes:
            air_trips_outbound[airport][mode] = 0
            air_trips_inbound[airport][mode] = 0
    for time_period in time_periods:
        with open(trips_files.replace(time_token,time_period)) as fl:
            for line in fl:
                line = line.strip().split(',')
                f = int(line[0])
                t = int(line[1])
                trips = map(float,line[3:])
                if f in air_trips_outbound:
                    if t in air_trips_inbound:
                        for i in range(len(trips)):
                            air_trips_outbound[f][modes[i]] += trips[i] / 2
                            air_trips_inbound[t][modes[i]] += trips[i] / 2
                            outbounds[f] += trips[i] / 2
                            inbounds[t] += trips[i] / 2
                    else:
                        for i in range(len(trips)):
                            air_trips_outbound[f][modes[i]] += trips[i]
                            outbounds[f] += trips[i]
                elif t in air_trips_inbound:
                    for i in range(len(trips)):
                        air_trips_inbound[t][modes[i]] += trips[i]
                        inbounds[t] += trips[i]
                time,dist = skims[time_period][(f,t)]
                if f in air_trip_dist:
                    air_trip_dist[f][min(int(dist),101)] += sum(trips)
                    air_trip_time[f][min(int(time),121)] += sum(trips)
                elif t in air_trip_dist:
                    air_trip_dist[t][min(int(dist),101)] += sum(trips)
                    air_trip_time[t][min(int(time),121)] += sum(trips)
    
    with open(outfile,'wb') as f:
        header = ['type']
        for airport in airports:
            ap = airports[airport]
            header.append(ap + '_model')
        f.write(','.join(header) + os.linesep)
        data = ['inbound']
        for airport in airports:
            data.append(inbounds[airport])
        f.write(','.join(map(str,data)) + os.linesep)
        data = ['outbound']
        for airport in airports:
            data.append(outbounds[airport])
        f.write(','.join(map(str,data)) + os.linesep)
        f.write(os.linesep)
        
        header = ['mode']
        for airport in airports:
            for d in ['inbound','outbound']:
                header.append(airports[airport] + '_' + d)
        f.write(','.join(header) + os.linesep)
        for mode in modes:
            data = [mode]
            for airport in airports:
                data.append(air_trips_inbound[airport][mode])
                data.append(air_trips_outbound[airport][mode])
            f.write(','.join(map(str,data)) + os.linesep)
        f.write(os.linesep)
        
        header = ['dist_class']
        for airport in airports:
            header.append(airports[airport])
        f.write(','.join(header) + os.linesep)
        for i in range(102):
            data = [i]
            for airport in airports:
                data.append(air_trip_dist[airport][i])
            f.write(','.join(map(str,data)) + os.linesep)
        f.write(os.linesep)
        
        header = ['time_class']
        for airport in airports:
            header.append(airports[airport])
        f.write(','.join(header) + os.linesep)
        for i in range(122):
            data = [i]
            for airport in airports:
                data.append(air_trip_time[airport][i])
            f.write(','.join(map(str,data)) + os.linesep)
        f.write(os.linesep)   
        
  
def buildTruckData(skims,time_periods,time_token,pa_file,trips_files,outfile):
    tmodes = ['vsml','sml','med','lrg']
    mode_count = len(tmodes)
    pas = {'p':{},'a':{}}
    for tmode in tmodes:
        pas['p'][tmode] = 0.0
        pas['a'][tmode] = 0.0
    with open(pa_file) as f:
        #zone [productions] [attractions]
        for line in f:
            line = line.strip().split()
            for i in range(len(tmodes)):
                pas['p'][tmodes[i]] += float(line[1+i])
                pas['a'][tmodes[i]] += float(line[1+i+len(tmodes)])
                
    truck_trip_dist = {}
    truck_trip_time = {}
    for tmode in tmodes:
        truck_trip_dist[tmode] = {}
        truck_trip_time[tmode] = {}
        for i in range(102): #0-1,1-2,...,99-100,100+
            truck_trip_dist[tmode][i] = 0
        for i in range(122):
            truck_trip_time[tmode][i] = 0
    for time_period in time_periods:
        with open(trips_files.replace(time_token,time_period)) as fl:
            for line in fl:
                line = line.strip().split(',')
                f = int(line[0])
                t = int(line[1])
                trips = map(float,line[3:])
                time_med,dist_med,time_lrg,dist_lrg = skims[time_period][(f,t)]
                for i in range(len(trips)):
                    tmode = tmodes[i % mode_count]
                    if tmodes == 'lrg':
                        dist = dist_lrg
                        time = time_lrg
                    else:
                        dist = dist_med
                        time = time_med
                    truck_trip_dist[tmode][min(int(dist),101)] += trips[i]
                    truck_trip_time[tmode][min(int(time),121)] += trips[i]
    
    with open(outfile,'wb') as f:
        header = ['mode','productions','attractions']
        f.write(','.join(header) + os.linesep)
        for tmode in tmodes:
            f.write(','.join(map(str,[tmode,pas['p'][tmode],pas['a'][tmode]])) + os.linesep)
        f.write(os.linesep)
        
        header = ['dist_class']
        for tmode in tmodes:
            header.append(tmode)
        f.write(','.join(header) + os.linesep)
        for i in range(102):
            data = [i]
            for tmode in tmodes:
                data.append(truck_trip_dist[tmode][i])
            f.write(','.join(map(str,data)) + os.linesep)
        f.write(os.linesep)
        
        header = ['time_class']
        for tmode in tmodes:
            header.append(tmode)
        f.write(','.join(header) + os.linesep)
        for i in range(122):
            data = [i]
            for tmode in tmodes:
                data.append(truck_trip_time[tmode][i])
            f.write(','.join(map(str,data)) + os.linesep)
        f.write(os.linesep)  


def readNodeMapping(mapping_file):
    to_seq = {}
    from_seq = {'taz':{},'maz':{},'tap':{},'ext':{}}
    with open(mapping_file) as f:
        for line in f:
            zones = map(int,line.strip().split(','))
            if zones[1] > 0:
                t = 'taz'
                seq = zones[1]
            elif zones[2] > 0:
                t = 'maz'
                seq = zones[2]
            if zones[3] > 0:
                t = 'tap'
                seq = zones[3]
            if zones[4] > 0:
                t = 'ext'
                seq = zones[4]
            to_seq[zones[0]] = seq
            from_seq[t][seq] = zones[0]
    return (to_seq,from_seq)

COUNTIES = ['San Francisco','San Mateo','Santa Clara','Alameda','Contra Costa','Solano','Napa','Sonoma','Marin']
def getTazSeqCounty(seq_taz,node_mapping):
    return COUNTIES[node_mapping[1]['taz'][seq_taz] / 100000]
   
#1455	Cal-1	Sonoma/Mendocino
#1456	Cal-128	Sonoma/Mendocino
#1457	US-101	Sonoma/Mendocino
#1458	Cal-29	Napa/Lake
#1459	Cal-128	Napa/Yolo
#1460	I-505	Solano/Yolo
#1461	Cal-113	Solano/Yolo
#1462	I-80	Solano/Yolo
#1463	Cal-12	Solano/Sacramento
#1464#	Cal-160	Contra Costa/Sacto
#1465#	Cal-4	Contra Costa/San Joaquin
#1466	County J-4	Alameda/San Joaquin
#1467	I-580/I-205	Alameda/San Joaquin
#1468	Cal-152	Santa Clara/Merced
#1469	Cal-156	Santa Clara/San Benito
#1470	Cal-25	Santa Clara/San Benito
#1471	US-101	Santa Clara/San Benito
#1472	Cal-152	Santa Clara/Santa Cruz
#1473	Cal-17	Santa Clara/Santa Cruz
#1474	Cal-9	Santa Clara/Santa Cruz
#1475	Cal-1	San Mateo/Santa Cruz
EXT_COUNTIES = ['Sonoma',
                'Sonoma',
                'Sonoma',
                'Napa',
                'Napa',
                'Solano',
                'Solano',
                'Solano',
                'Solano',
                'Contra Costa',
                'Contra Costa',
                'Alameda',
                'Alameda',
                'Santa Clara',
                'Santa Clara',
                'Santa Clara',
                'Santa Clara',
                'Santa Clara',
                'Santa Clara',
                'Santa Clara',
                'San Mateo']
    
def getExtCounty(seq_ext,node_mapping):
    return EXT_COUNTIES[seq_ext - len(node_mapping[1]['taz']) - 1]

def buildIxData(time_periods,time_token,trips_files,outfile,node_mapping):
    taz_count = len(node_mapping[1]['taz'])
    ix_trips = {'in':{},'out':{},'xx':{}}
    for county in COUNTIES:
        ix_trips['in'][county] = {}
        ix_trips['out'][county] = {}
        ix_trips['xx'][county] = {}
        for county2 in COUNTIES:
            ix_trips['in'][county][county2] = 0.0
            ix_trips['out'][county][county2] = 0.0
            ix_trips['xx'][county][county2] = 0.0
            
    for time_period in time_periods:
        with open(trips_files.replace(time_token,time_period)) as fl:
            for line in fl:
                line = line.strip().split(',')
                f = int(line[0])
                t = int(line[1])
                trips = map(float,line[2:])
                fext = f > taz_count
                text = t > taz_count
                if fext:
                    fc = getExtCounty(f,node_mapping)
                    if text:
                        tc = getExtCounty(t,node_mapping)
                        t = 'xx'
                    else:
                        tc = getTazSeqCounty(t,node_mapping)
                        t = 'in'
                else:
                    fc = getTazSeqCounty(f,node_mapping)
                    tc = getExtCounty(t,node_mapping)
                    t = 'out'
                ix_trips[t][fc][tc] += sum(trips)
    
    with open(outfile,'wb') as f:
        for t in ix_trips:
            f.write(','.join([t] + COUNTIES) + os.linesep)
            for c1 in COUNTIES:
                d = [c1]
                for c2 in COUNTIES:
                    d.append(str(ix_trips[t][c1][c2]))
                f.write(','.join(d) + os.linesep)
            f.write(os.linesep)

def readPersonData(datafile):
    hhids = []
    pids = []
    first = True
    with open(datafile) as f:
        for line in f:
            if first:
                first = False
                continue
            line = line.strip().split(',')
            hhids.append(int(line[0]))
            pids.append(int(line[1]))
    return (hhids,pids)

def buildTripTourData(sample_size,hh_ids,person_ids,itrips,jtrips,itours,jtours,outfile):
    #itour
    #hh_id,person_id,person_num,person_type,tour_id,tour_category,tour_purpose,orig_mgra,dest_mgra,start_period,end_period,tour_mode,tour_distance,tour_time,atWork_freq,num_ob_stops,num_ib_stops,out_btap,out_atap,in_btap,in_atap,util_1,util_2,util_3,util_4,util_5,util_6,util_7,util_8,util_9,util_10,util_11,util_12,util_13,util_14,util_15,util_16,util_17,util_18,util_19,util_20,util_21,util_22,util_23,util_24,util_25,util_26,prob_1,prob_2,prob_3,prob_4,prob_5,prob_6,prob_7,prob_8,prob_9,prob_10,prob_11,prob_12,prob_13,prob_14,prob_15,prob_16,prob_17,prob_18,prob_19,prob_20,prob_21,prob_22,prob_23,prob_24,prob_25,prob_26
    #1784171,4438072,1,1,0,MANDATORY,Work,1,513,8,27,14,4.600000,10.270000,4,0,0,652,685,685,652,-4.575951,-999.000000,-7.258962,-999.000000,-999.000000,-6.543040,-999.000000,-999.000000,-999.000000,-8.238935,-2.991010,-4.311682,-4.110646,-2.738966,-999.000000,-8.046000,-999.000000,-5.588011,-5.387171,-5.737395,-7.524529,-999.000000,-7.011541,-6.330701,-7.160925,-999,0.124664,0.000000,0.001425,0.000000,0.000000,0.004698,0.000000,0.000000,0.000000,0.003260,0.220258,0.000898,0.002074,0.629536,0.000000,0.000000,0.000000,0.002917,0.006735,0.001565,0.000012,0.000000,0.000105,0.001796,0.000056,0.0
    #jtour
    #hh_id,tour_id,tour_category,tour_purpose,tour_composition,tour_participants,orig_mgra,dest_mgra,start_period,end_period,tour_mode,tour_distance,tour_time,num_ob_stops,num_ib_stops,out_btap,out_atap,in_btap,in_atap,util_1,util_2,util_3,util_4,util_5,util_6,util_7,util_8,util_9,util_10,util_11,util_12,util_13,util_14,util_15,util_16,util_17,util_18,util_19,util_20,util_21,util_22,util_23,util_24,util_25,util_26,prob_1,prob_2,prob_3,prob_4,prob_5,prob_6,prob_7,prob_8,prob_9,prob_10,prob_11,prob_12,prob_13,prob_14,prob_15,prob_16,prob_17,prob_18,prob_19,prob_20,prob_21,prob_22,prob_23,prob_24,prob_25,prob_26
    #820999,0,JOINT_NON_MANDATORY,Maintenance,3,1 2,1,2863,19,19,3,3.170000,8.100000,0,3,0,0,0,0,-999.000000,-999.000000,-2.137954,-999.000000,-999.000000,-4.395305,-999.000000,-999.000000,-999.000000,-7.216661,-5.944395,-9.372482,-7.825008,-6.609491,-999.000000,-999.000000,-999.000000,-999.000000,-999.000000,-999.000000,-16.315069,-999.000000,-17.043730,-16.387794,-16.594976,-999,0.000000,0.000000,0.950317,0.000000,0.000000,0.022077,0.000000,0.000000,0.000000,0.005973,0.020351,0.000000,0.000008,0.001274,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.000000,0.0
    #itrip
    #hh_id,person_id,person_num,tour_id,stop_id,inbound,tour_purpose,orig_purpose,dest_purpose,orig_mgra,dest_mgra,parking_mgra,stop_period,trip_mode,trip_board_tap,trip_alight_tap,tour_mode,TRIP_TIME,TRIP_DISTANCE,TRIP_COST
    #1784171,4438072,1,0,-1,0,Work,Home,Work,1,513,0,8,14,652,685,14,38.4386,4.6,0
    #jtrip
    #hh_id,tour_id,stop_id,inbound,tour_purpose,orig_purpose,dest_purpose,orig_mgra,dest_mgra,parking_mgra,stop_period,trip_mode,num_participants,trip_board_tap,trip_alight_tap,tour_mode,TRIP_TIME,TRIP_DISTANCE,TRIP_COST
    #820999,0,-1,0,Maintenance,Home,Maintenance,1,2863,-1,19,3,2,0,0,3,7.95,3.18,0
    
    mode_map = {1 : 'DRIVEALONEFREE',
                2 : 'DRIVEALONEPAY',
                3 : 'SHARED2GP',
                4 : 'SHARED2HOV',
                5 : 'SHARED2PAY',
                6 : 'SHARED3GP',
                7 : 'SHARED3HOV',
                8 : 'SHARED3PAY',
                9 : 'WALK',
                10 : 'BIKE',
                11 : 'WALK_LOC',
                12 : 'WALK_EXP',
                13 : 'WALK_BRT',
                14 : 'WALK_LR',
                15 : 'WALK_CR',
                16 : 'PNR_LOC',
                17 : 'PNR_EXP',
                18 : 'PNR_BRT',
                19 : 'PNR_LR',
                20 : 'PNR_CR',
                21 : 'KNR_LOC',
                22 : 'KNR_EXP',
                23 : 'KNR_BRT',
                24 : 'KNR_LR',
                25 : 'KNR_CR',
                26 : 'SCHBUS'}
        
    
    def accumulate(infile,hhid,pid,tid,mid):
        hh_t = {}
        person_t = {}
        mode_tourtype_t = {}
        for hh_id in hh_ids:
            hh_t[hh_id] = 0
        for person_id in person_ids:
            person_t[person_id] = 0
            
        with open(infile) as f:
            first = True
            for line in f:
                if first:
                    first = False
                    continue
                line = line.strip().split(',')
                hh_id = int(line[hhid])
                hh_t[hh_id] += 1
                if not pid is None:
                    person_id = int(line[pid])
                    person_t[person_id] += 1
                mode = int(line[mid])
                tourtype = line[tid]
                if not mode in mode_tourtype_t:
                    mode_tourtype_t[mode] = {}
                if not tourtype in mode_tourtype_t[mode]:
                    mode_tourtype_t[mode][tourtype] = 0
                mode_tourtype_t[mode][tourtype] += 1
        hhh = {}
        for hh_id in hh_t:
            count = hh_t[hh_id]
            if not count in hhh:
                hhh[count] = 0
            hhh[count] += 1
        ph = {}
        if not pid is None:
            for p_id in person_t:
                count = person_t[p_id]
                if not count in ph:
                    ph[count] = 0
                ph[count] += 1
             
             
        return (hhh,ph,mode_tourtype_t)
    
    ihh_trips,iperson_trips,imode_tourtype_trips = accumulate(itrips,0,1,6,13)
    ihh_tours,iperson_tours,imode_tourtype_tours = accumulate(itours,0,1,6,11)
    jhh_trips,_,jmode_tourtype_trips = accumulate(jtrips,0,None,4,11)
    jhh_tours,_,jmode_tourtype_tours = accumulate(jtours,0,None,3,10)
    
    with open(outfile,'wb') as f:
        f.write('tours/trips per hh' + os.linesep)
        f.write(','.join(['count','indiv_tours','indiv_trips','joint_tours','joint_trips']) + os.linesep)
        m = 0
        for mm in ihh_trips:
            m = max(mm,m)
        for mm in ihh_tours:
            m = max(mm,m)
        for mm in jhh_trips:
            m = max(mm,m)
        for mm in jhh_tours:
            m = max(mm,m)
        for c in range(m):
            data = [c]
            for x in (ihh_tours,ihh_trips,jhh_tours,jhh_trips):
                if c in x:
                    data.append(x[c])
                else:
                    data.append(0)
            f.write(','.join(map(str,data)) + os.linesep)
        f.write(os.linesep)
        
        f.write('tours/trips per person' + os.linesep)
        f.write(','.join(['count','indiv_tours','indiv_trips']) + os.linesep)
        m = 0
        for mm in iperson_trips:
            m = max(mm,m)
        for mm in iperson_tours:
            m = max(mm,m)
        for c in range(m):
            data = [c]
            for x in (iperson_tours,iperson_trips):
                if c in x:
                    data.append(x[c])
                else:
                    data.append(0)
            f.write(','.join(map(str,data)) + os.linesep)
        f.write(os.linesep)
        
        a = ('indiv tours','indiv trips','joint tours','joint trips')
        b = (imode_tourtype_tours,imode_tourtype_trips,jmode_tourtype_trips,jmode_tourtype_tours)
        modes = []
        for m in mode_map:
            modes.append(mode_map[m])
        modes.sort()
        tourtypes = {}
        for ts in b:
            for m in ts:
                for tt in ts[m]:
                    tourtypes[tt] = None
        tourtypes = list(tourtypes.keys())
        tourtypes.sort()
        for i in range(4):
            f.write(a[i] + ' by tourtype and mode' + os.linesep)
            f.write(','.join(['mode'] + tourtypes) + os.linesep)
            for m in mode_map:
                data = [mode_map[m]]
                for tourtype in tourtypes:
                    if (m in b[i]) and (tourtype in b[i][m]):
                        data.append(b[i][m][tourtype] / sample_size) 
                    else:
                        data.append(0)
                f.write(','.join(map(str,data)) + os.linesep)
            f.write(os.linesep)


     

print('building sequence map')
seq_map = getZoneSeqMapping(SEQ_FILE)

print('bike taz-taz')
skimSummary(TAZ_TAZ_BIKE_SKIM,4,[TAZ_TAZ_EUCLID],None,seq_map)
#print('drive maz-maz')
#skimSummary(MAZ_MAZ_DRIVE_SKIM,4,[MAZ_MAZ_EUCLID,MAZ_MAZ_DRIVE_EUCLID],None,seq_map)
#print('drive maz-maz toll')
#skimSummary(MAZ_MAZ_DRIVE_TOLL_SKIM,4,[MAZ_MAZ_EUCLID,MAZ_MAZ_DRIVE_EUCLID],None,seq_map)

#print('reading taz skims')
#skims = readTazSkim(TIME_PERIODS,TIME_TOKEN,TAZ_TAZ_DA)
#print('building airport data')
#buildAirTripData(skims,TIME_PERIODS,TIME_TOKEN,AIR_TRIPS,AIR_TRIPS_OUT)
#del skims
#
#print('reading taz truck skims')
#com_skims = readTazComSkim(TIME_PERIODS,TIME_TOKEN,TAZ_TAZ_COM)
#print('building truck data')
#buildTruckData(com_skims,TIME_PERIODS,TIME_TOKEN,TRUCK_PAS,TRUCK_TRIPS,TRUCK_TRIPS_OUT)
#del com_skims

#print('reading sequence data')
#node_mapping = readNodeMapping(SEQ_FILE)
#print('building ix data')
#buildIxData(TIME_PERIODS,TIME_TOKEN,IX_TRIPS,IX_TRIPS_OUT,node_mapping)

#print('reading ctramp person data')
#hh_ids,person_ids = readPersonData(CTRAMP_PERSON_DATA_FILE)
#print('building trip and tour data')
#buildTripTourData(SAMPLE_SIZE,hh_ids,person_ids,INDIV_TRIP_FILE,JOINT_TRIP_FILE,INDIV_TOUR_FILE,JOINT_TOUR_FILE,CTRAMP_TT_OUT)