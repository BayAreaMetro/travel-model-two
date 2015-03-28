USAGE=r"""

 Usage: build_drive_access_skims.py

 This script builds transit drive access skims. It takes the following inputs:

  1) TAZ->TAZ highway skims by time-of-day
  2) MAZ->TAZ correspondence
  3) MAZ->TAP walk access skims
  4) N->(TAZ/MAZ/TAP/EXT) SEQ correspondence

    The script builds (by time-of-day), the shortest path from each TAZ->TAP by creating a virtual
    shortest path from TAZ->TAZ->MAZ->TAP. The first link is given by the highway skim (1), the 
    second value (zero-cost) is provided by the MAZ-TAZ corresponence (2). The third link is 
    privided by the MAZ->TAP walk access skim.

    The output of this script is a csv file with the following columns:

        ORIG_TAZ   - Origin TAZ (sequential numbering)
        MODE       - The (transit) mode
        TIMEPERIOD - The time period
        DEST_TAP   - Destination TAP (sequential numbering)
        DEST_MAZ   - Destination MAZ (sequential numbering)
        DEST_TAZ   - Destination TAZ (sequential numbering)
        DRIVE_TIME - Drive time from ORIG_TAZ to DEST_TAZ (minutes)
        DRIVE_DIST - Drive distance from ORIG_TAZ to DEST_TAZ (miles)
        DRIVE_BTOLL- Drive bridge toll from ORIG_TAZ to DEST_TAZ (in year 2010 cents)
        WALK_DIST  - Walk access distance from the MAZ centroid to the TAP (feet)
        TOTAL_TIME - Generalized cost for drive+walk in minutes

    crf 8/2013 - Initial revision
    lmz 3/2015 - Updated to use pandas and for maintanence & readability

  TODO: How does this relate to the (poorly named) tap_data_builder.py which is presumably doing stuff for parking?
        Seems like this is redundant?
        That process outputs hwy\tap_data.csv which is apparently specified in runtime\mtctm2.properties as the "tap.data.file"
"""
import collections,datetime,gc,os,re,sys,time
import numpy, pandas
# from memory_profiler import profile

TIMEPERIODS = ['EA','AM','MD','PM','EV']

WALK_SPEED = 3.0 * 5280.0 / 60.0   # 3 miles/hour x 5280 feet/mile x hour/60min = 264 feet/min

MODE_MAP = [\
    {'mode_num':1, 'mode_str':'LOCAL_BUS'    },
    {'mode_num':2, 'mode_str':'EXPRESS_BUS'  },
    {'mode_num':3, 'mode_str':'FERRY_SERVICE'},
#   {'mode_num':3, 'mode_str':'ignore'       },  # TODO: Why?
    {'mode_num':4, 'mode_str':'LIGHT_RAIL'   },
    {'mode_num':5, 'mode_str':'HEAVY_RAIL'   },
    {'mode_num':6, 'mode_str':'COMMUTER_RAIL'}]

def readPropertiesFile(properties_filename):
    """
    Reads a properties file, where comments start with ';' or '#' characters.
    Returns properties as an ordered dictionary
    Keys are made upper-case
    """
    properties_dict = collections.OrderedDict()
    properties_file = open(properties_filename, 'r')
    comment_pattern = re.compile("([^;#]*)[;#]?(.*)?")
    for line in properties_file:

        line = line.strip() # strip leading and trailing whitespace
        if len(line) == 0 or line[0] in [';','#']: continue # blank or comment

        # strip the comment and split on equals
        comment_match = comment_pattern.search(line)
        line          = comment_match.group(1)
        line_parts    = line.split("=")
        val           = line_parts[1].strip()
        # see if we can make it an int
        try:      val = int(line_parts[1])
        except:   pass
        # see if we can make it a float
        try:      val = float(line_parts[1])
        except:   pass
        properties_dict[line_parts[0].strip().upper()] = val
    properties_file.close()

    print "Read properties from %s:" % properties_filename
    for key,val in properties_dict.iteritems():
        print "  [%s] -> [%s] %s" % (key, str(val), str(type(val)))
    return properties_dict

def readTransitLinesFile(transit_filename):
    """
    Reads transit line file and does a simple parsing of it.
    Returns pandas DataFrame with columns TIMEPERIOD, mode_num, mode_str, STOP
    """
    # read transit lines to pull out tod and stop information
    stops_by_tod_and_mode = {}
    for period in TIMEPERIODS:
        stops_by_tod_and_mode[period] = {}
    #LINE NAME="EM_HOLLIS", USERA1="Emery Go-Round", USERA2="Local bus", MODE=12, ONEWAY=T, XYSPEED=15, HEADWAY[1]=60.0, HEADWAY[2]=12.0, HEADWAY[3]=20.0, HEADWAY[4]=12.0, HEADWAY[5]=30.0, N=2565595,...
    for line in open(transit_filename):
        split_line = map(str.strip,re.split('[=,]',line.strip()))
        if len(split_line) < 3:
            continue
        mode = split_line[split_line.index('USERA2') + 1].replace('"','').upper().replace(' ','_')
        tod = []
        for i in range(len(TIMEPERIODS)):
            tod.append(float(split_line[split_line.index('HEADWAY[' + str(i+1) + ']') + 1]) > 0.0)
            period = TIMEPERIODS[i]
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
                    stops_by_tod_and_mode[TIMEPERIODS[i]][mode][n] = None


    # stops_by_tod_and_mode =
    #  dictionary { timeperiod ('AM', etc) -> { mode string ('LOCAL_BUS', etc) -> { stop# -> None }}}
    df_list = []
    for timeperiod in TIMEPERIODS:
        for mode_dict in MODE_MAP:
            if mode_dict['mode_str'] not in stops_by_tod_and_mode[timeperiod]: continue
            stops = sorted(stops_by_tod_and_mode[timeperiod][mode_dict['mode_str']].keys())
            for stop in stops:
                df_list.append( (timeperiod, mode_dict['mode_num'], mode_dict['mode_str'], stop) )
    return pandas.DataFrame(df_list, columns=['TIMEPERIOD','mode_num','mode_str','STOP'])

# @profile
def main():
    # input files
    param_block_file           = os.path.join('CTRAMP', 'scripts', 'block', 'hwyParam.block')
    param_block_file2          = os.path.join('hwy',         'autoopcost.properties')

    zone_seq_mapping_file      = os.path.join('hwy',         'mtc_final_network_zone_seq.csv')
    maz_to_taz_mapping_file    = os.path.join('landuse',     'maz_data.csv')
    ped_maz_tap_distance_file  = os.path.join('skims',       'ped_distance_maz_tap.csv')
    transit_line_file          = os.path.join('trn',         'transitLines.lin')
    network_tap_nodes_file     = os.path.join('hwy',         'mtc_final_network_tap_nodes.csv')
    network_tap_links_file     = os.path.join('hwy',         'mtc_final_network_tap_links.csv')
    skim_taz_taz_file          = os.path.join('skims',       'DA_%s_taz_time.csv')
    drive_transit_skim_out_file= os.path.join('skims',       'drive_maz_taz_tap.csv')

    start_time = time.time()

    print '%s Reading hwy parameter block data' % datetime.datetime.now().strftime("%c")
    block_dict  = readPropertiesFile(param_block_file)
    block_dict.update(readPropertiesFile(param_block_file2))

    print '%s Reading %s for node -> taz/maz/tap sequence mapping' % (datetime.datetime.now().strftime("%c"), zone_seq_mapping_file)
    sequence_mapping           = pandas.DataFrame.from_csv(zone_seq_mapping_file)
    sequence_mapping.reset_index(inplace=True)

    print '%s Reading %s for maz -> taz' % (datetime.datetime.now().strftime("%c"), maz_to_taz_mapping_file)
    maz_taz_df = pandas.DataFrame.from_csv(maz_to_taz_mapping_file)
    maz_taz_df.reset_index(inplace=True)
    maz_taz_df = maz_taz_df[['MAZ','TAZ']]

    print '%s Reading %s for maz -> tap skims' % (datetime.datetime.now().strftime("%c"), ped_maz_tap_distance_file)
    ped_maz_tap_df = pandas.DataFrame.from_csv(ped_maz_tap_distance_file)
    ped_maz_tap_df.reset_index(inplace=True)
    ped_maz_tap_df['WALK_TIME'] = ped_maz_tap_df['FEET']/WALK_SPEED   # minutes
    # ped_maz_tap has columns ORIG_MAZ, DEST_TAP, DEST2_TAP, SP_DISTANCE, FEET, WALK_TIME

    # Find closest MAZ for each TAP
    print '%s Finding closest MAZ' % datetime.datetime.now().strftime("%c"),
    ped_closest_maz_tap_df = ped_maz_tap_df.loc[ped_maz_tap_df.groupby('DEST_TAP')['WALK_TIME'].idxmin()]
    print ' of %d TAPs' % len(ped_closest_maz_tap_df)
    del ped_maz_tap_df
    # print ped_closest_maz_tap_df.head()

    mode_map = pandas.DataFrame(MODE_MAP)

    print '%s Reading %s to correspond TAPs and modes' % (datetime.datetime.now().strftime("%c"), network_tap_nodes_file)
    tap_mode_df = pandas.read_table(network_tap_nodes_file, names=['TAP','mode_num'], delimiter=',')
    tap_mode_df = pandas.merge(left=tap_mode_df, right=mode_map, how='left')

    print '%s Reading %s for TAP links' % (datetime.datetime.now().strftime("%c"), network_tap_links_file)
    tap_link_df    = pandas.read_table(network_tap_links_file, names=['A','B'], delimiter=',')
    tap_to_stop_df = tap_link_df[(tap_link_df.A < 900000) & (tap_link_df.B >= 1000000)]
    # stop_to_tap_df = tap_link_df[(tap_link_df.B < 900000) & (tap_link_df.A >= 1000000)]
    print ' -> Read %d links' % len(tap_link_df)
    print ' -> Read %d tap to stop links' % len(tap_to_stop_df)
    # print ' -> Read %d stop to tap links' % len(stop_to_tap_df)

    # add modes to TAP links
    tap_to_stop_df = pandas.merge(left=tap_to_stop_df, right=tap_mode_df, how='left',
                                  left_on='A', right_on='TAP')
    # make sure TAP is always set and drop A
    assert(pandas.isnull(tap_to_stop_df.TAP).sum() == 0)
    tap_to_stop_df = tap_to_stop_df[['TAP','B','mode_num','mode_str']]
    del tap_mode_df

    # read the stops we want to get to per time period
    print '%s Reading %s for transit lines' % (datetime.datetime.now().strftime("%c"), transit_line_file)
    timeperiod_mode_stop_df = readTransitLinesFile(transit_line_file)

    # associate those stops (with their modes) with TAPS
    timeperiod_mode_stop_df = pandas.merge(left=timeperiod_mode_stop_df,           right=tap_to_stop_df,
                                           left_on=('STOP','mode_num','mode_str'), right_on=('B','mode_num','mode_str'),
                                           how='left')

    print " %d stops failed to link to TAPS" % pandas.isnull(timeperiod_mode_stop_df.TAP).sum()
    # print timeperiod_mode_stop_df.loc[pandas.isnull(timeperiod_mode_stop_df.TAP),:] # any fails?

    # no longer care about stops, just TAPS
    timeperiod_mode_tap_df = timeperiod_mode_stop_df[['TIMEPERIOD','mode_num','mode_str','TAP']]
    timeperiod_mode_tap_df = timeperiod_mode_tap_df.loc[pandas.isnull(timeperiod_mode_tap_df.TAP) == False, :]

    # free memory
    del tap_link_df
    del tap_to_stop_df
    del timeperiod_mode_stop_df

    # resequence TAPs
    timeperiod_mode_tap_df.rename(columns={'TAP':'TAP_N'}, inplace=True)
    tapseq = sequence_mapping[['N','TAPSEQ']]
    tapseq.rename(columns={'N':'TAP_N', 'TAPSEQ':'TAP'}, inplace=True)
    timeperiod_mode_tap_df = pandas.merge(left=timeperiod_mode_tap_df,          right=tapseq,     how='left')

    # get closest MAZ
    timeperiod_mode_tap_df = pandas.merge(left=timeperiod_mode_tap_df,          right=ped_closest_maz_tap_df,
                                          left_on='TAP',                        right_on='DEST_TAP',
                                          how='left')
    print " %s TAPs failed to link to MAZs" % pandas.isnull(timeperiod_mode_tap_df.ORIG_MAZ).sum(),
    # print timeperiod_mode_tap_df.loc[pandas.isnull(timeperiod_mode_tap_df.ORIG_MAZ),:]
    print pandas.unique(timeperiod_mode_tap_df.loc[pandas.isnull(timeperiod_mode_tap_df.ORIG_MAZ),:].TAP_N.ravel())
    timeperiod_mode_tap_df = timeperiod_mode_tap_df.loc[pandas.isnull(timeperiod_mode_tap_df.ORIG_MAZ)==False,:]

    # the join made these floats because there were some nulls - return them to ints
    timeperiod_mode_tap_df.loc[:,['ORIG_MAZ','DEST_TAP']] = timeperiod_mode_tap_df.loc[:,['ORIG_MAZ','DEST_TAP']].astype(numpy.int64)

    # associate with TAZ
    timeperiod_mode_tap_df.rename(columns={'ORIG_MAZ':'MAZ'}, inplace=True)
    timeperiod_mode_tap_df = pandas.merge(left=timeperiod_mode_tap_df,         right=maz_taz_df,  how = 'left')
    timeperiod_mode_tap_df = timeperiod_mode_tap_df[['TIMEPERIOD','mode_num','mode_str','TAP','MAZ','TAZ','FEET','WALK_TIME']]
    timeperiod_mode_tap_df.rename(columns={'TAP':'DEST_TAP','MAZ':'DEST_MAZ','TAZ':'DEST_TAZ','FEET':'WALK_DIST'}, inplace=True)
    # timeperiod_mode_tap_df has columns TIMEPERIOD, mode_num, mode_str, DEST_TAP, DEST_MAZ, DEST_TAZ, WALK_DIST, WALK_TIME

    min_per_cent = 0.6 / block_dict['VOT'] # (1/VOT) hours/dollar x 60 min/hour x 0.01 dollars/cents = 0.6/VOT min/cent

    header_written = False
    for timeperiod in TIMEPERIODS:
        print "%s Reading %s to taz-to-taz driving skims" % (datetime.datetime.now().strftime("%c"),
                                                             skim_taz_taz_file % timeperiod),
        hwy_skim_df = pandas.read_table(skim_taz_taz_file % timeperiod,
                                        names=['ORIG_TAZ','DEST_TAZ','DUMMY','TIMEDA','DISTDA','BTOLLDA'],
                                        delimiter=',')
        # fill in BTOLLDA = NaN
        hwy_skim_df.BTOLLDA.fillna(0, inplace=True)

                                           # minutes                year 2010 cents             miles              2010 cents/mile
        hwy_skim_df['gen_cost_minutes'] = hwy_skim_df.TIMEDA + ( hwy_skim_df.BTOLLDA + (hwy_skim_df.DISTDA*block_dict['AUTOOPCOST']) )*min_per_cent
        hwy_skim_df = hwy_skim_df[['ORIG_TAZ','DEST_TAZ','TIMEDA','DISTDA','BTOLLDA','gen_cost_minutes']] # drop column DUMMY

        print "->  %d rows read" % len(hwy_skim_df)

        # Do it by timeperiod and mode because the memory requirement is large
        for mode_dict in MODE_MAP:

            taz_tap_df = pandas.merge(left=hwy_skim_df,
                                      right=timeperiod_mode_tap_df.loc[(timeperiod_mode_tap_df.TIMEPERIOD==timeperiod) & \
                                                                       (timeperiod_mode_tap_df.mode_num==mode_dict['mode_num']),:],
                                      on='DEST_TAZ')
            taz_tap_df['TOTAL_TIME'] = taz_tap_df.gen_cost_minutes + taz_tap_df.WALK_TIME

            print "  %d rows for %s %s DEST_TAZ x TAP" % (len(taz_tap_df), timeperiod, mode_dict['mode_str'])
            if len(taz_tap_df) == 0: continue

            # Find minimum gencost TAZ-TAZ
            taz_tap_df = taz_tap_df.loc[taz_tap_df.groupby('ORIG_TAZ')['TOTAL_TIME'].idxmin()]
            print "  %d rows after aggregating to lowest generalized cost for each orig_taz/mode" % len(taz_tap_df)

            taz_tap_df.rename(columns={'TIMEDA':'DRIVE_TIME','DISTDA':'DRIVE_DIST','BTOLLDA':'DRIVE_BTOLL'}, inplace=True)
            taz_tap_df = taz_tap_df[['ORIG_TAZ','mode_str','TIMEPERIOD','DEST_TAP','DEST_MAZ','DEST_TAZ','DRIVE_TIME','DRIVE_DIST','DRIVE_BTOLL','WALK_DIST','TOTAL_TIME']]

            taz_tap_df.to_csv(drive_transit_skim_out_file, index=False, float_format="%.2f",
                              mode = 'w' if not header_written else 'a',
                              header=True if not header_written else False )
            header_written = True
            print "%s Wrote %s - timeperiod %s mode %s" % (datetime.datetime.now().strftime("%c"),
                                                           drive_transit_skim_out_file, 
                                                           timeperiod,
                                                           mode_dict['mode_num'])
            del taz_tap_df
            gc.collect()

        del hwy_skim_df
        gc.collect()

if __name__ == '__main__':
    main()