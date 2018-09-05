import argparse,collections,copy,datetime,math,numpy,os,pandas,re,sys
import partridge
import Wrangler

import Levenshtein
from sklearn.cluster import DBSCAN, AgglomerativeClustering, SpectralClustering

USAGE = """

Create transit schedule from spreadsheet or gtfs.

Specify an operator set -- currently support Caltrain_NB, Caltrain_SB and SonomaCounty.

For Caltrain, the schedule is read from a spreadsheet since this is a typical representation of the Caltrain schedule.
The lines are then clustered based on their stop pattern and those are converted into Local/Limited/Baby Bullet lines.

For SonomaCounty, the route alignment is pulled from the existing network coding.  For each route/direction, the existing
network coding doesn't indicate which direction it's for, so that needs to be configured for bi-directional routes.  The
longest (most stops) coding is assumed to be the prototype line, and it's renamed for legibility according to configuration,
and the frequencies are set according the the gtfs frequencies for the route/direction.

"""

USERNAME     = os.environ["USERNAME"]
LOG_FILENAME = "createTransitSchedule_{}_info.log"
TM2_INPUTS   = os.path.join(r"C:\\Users", USERNAME, "Box\\Modeling and Surveys\\Development\\Travel Model Two Development\\Model Inputs")
TRN_NETFILE  = os.path.join(TM2_INPUTS,"2015_revised_mazs","trn")
TRN_LABELFILE= os.path.join(TM2_INPUTS,"TM2 Transit Nodes.csv")

OPERATOR_SET_DICT = {
    "Caltrain_NB":{
        "schedule_file": r"M:\\Data\\Transit\\Schedules\\Caltrain\\Caltrain.xlsx",
        "sheet_name"   : "2015 Northbound",
        "existing_re"  : "^CT_N",
        "lin_prefix"   : "CT_NB",
        "winner_label" : "agg_avg_09",
        # line attributes
        "MODE"         : 130,
        "OPERATOR"     : 17,
        "USERA1"       : "\"Caltrain\"",
        "USERA2"       : "\"Commuter rail\"",
        "VEHICLETYPE"  : 50
    },
    "Caltrain_SB":{
        "schedule_file": r"M:\\Data\\Transit\\Schedules\\Caltrain\\Caltrain.xlsx",
        "sheet_name"   : "2015 Southbound",
        "existing_re"  : "^CT_S",
        "lin_prefix"   : "CT_SB",
        "winner_label" : "agg_avg_12",
        # line attributes
        "MODE"         : 130,
        "OPERATOR"     : 17,
        "USERA1"       : "\"Caltrain\"",
        "USERA2"       : "\"Commuter rail\"",
        "VEHICLETYPE"  : 50
    },
    "SonomaCounty":{
        "schedule_file": r"M:\\Data\\Transit\\511\\Dec 2014\\GTFS\\GTFSTransitData_SO_2014.11.12.zip",
        "service_date" : datetime.date(2015, 4, 22), # average wednesday
        "existing_re"  : "^SO_",
        "lin_prefix"   : "SO_",
        "existing_route_re": { # (route_id, direction_id) => (existing regex string, new line name)
            ("12" ,0L):("^SO_12$",         "SO_12"),
            ("14" ,0L):("^SO_14",          "SO_14"),
            ("20" ,0L):("^SO_20b",         "SO_20_EB"),  # 20b are eastbound
            ("20" ,1L):("^SO_20[a]?$",     "SO_20_WB"),  # 20, 20a are westbound,
            ("20X",0L):("^SO_20X$",        "SO_20X_EB"), # 20X eastbound
            ("20X",1L):("^SO_20Xa",        "SO_20X_WB"), # 20Xa westbound
            ("22", 0L):("^SO_22[a]?$",     "SO_22_EB"),  # 22,22a eastbound
            ("22", 1L):("^SO_22[bc]$",     "SO_22_WB"),  # 22b,22c westbound
            ("26", 0L):("^SO_26a$",        "SO_26_WB"),  # 26a, westbound
            ("26", 1L):("^SO_26$",         "SO_26_EB"),  # 26, eastbound
            ("30", 0L):("^SO_30[bc]?$",    "SO_30_EB"),  # 30,30b,30c eastbound
            ("30", 1L):("^SO_30[ade]$",    "SO_30_WB"),  # 30a,30d,30e westbound
            ("30X",0L):("^SO_30X$",        "SO_30X_EB"), # 30x eastbound
            ("30X",1L):("^SO_30X[ab]$",    "SO_30X_WB"), # 30x westbound
            ("32", 0L):("^SO_32[ac]?$",    "SO_32_SL"),  # 32 shuttle south loop
            ("32", 1L):("^SO_32[bde]$",    "SO_32_NL"),  # 32 shuttle north loop
            ("34", 0L):("^SO_34a$",        "SO_34_WB"), # 34 westbound
            ("34", 1L):("^SO_34$",         "SO_34_EB"), # 34 eastbound
            ("38", 0L):("^SO_38$",         "SO_38_NB"), # 38 northbound
            ("38", 1L):("^SO_38a$",        "SO_38_SB"), # 38 southbound
            ("40", 0L):("^SO_40$",         "SO_40_EB"), # 40 eastbound
            ("40", 1L):("^SO_40a$",        "SO_40_WB"), # 40 westbound
            ("42", 0L):("^SO_42a$",        "SO_42_NB"), # 42 northbound
            ("42", 1L):("^SO_42$",         "SO_42_SB"), # 42 southbound
            ("44", 0L):("^SO_44[bcd]$",    "SO_44_SB"), # 44b,44c,44d southbound
            ("44", 1L):("^SO_44[afgh]?$",  "SO_44_NB"), # 44,44a,44f,44g,44h northbound
            ("46", 0L):("^SO_46$",         "SO_46_SB"), # 46 southbound
            ("46", 1L):("^SO_46a$",        "SO_46_NB"), # 46 northbound
            ("48", 0L):("^SO_48[ab]$",     "SO_48_NB"), # 48 northbound
            ("48", 1L):("^SO_48$",         "SO_48_SB"), # 48 southbound
            ("48X",0L):("^SO_48X",         "SO_48X_SB"), # 48x southbound
            ("60", 0L):("^SO_60[cdehij]$", "SO_60_NB"), # 60c, 60d, 60e 60h, 60i, 60j northbound
            ("60", 1L):("^SO_60[ab]?$",    "SO_60_SB"), # 60, 60a, 60b southbound
            ("60X",0L):("^SO_60X[b]?$",    "SO_60X_NB"), # 60X 60Xb northbound
            ("60X",1L):("^SO_60X[a]$",     "SO_60X_SB"), # 60Xa sourthbound
            ("62", 0L):("^SO_62$",         "SO_62_NB"), # 62 northbound
            ("62", 1L):("^SO_62a$",        "SO_62_SB"), # 62 southbound
        },
    }
}

TIME_PERIODS = pandas.DataFrame([{"time_period":"EA", "start_hour": 3.0, "duration":3.0, "freq_index":0},
                                 {"time_period":"AM", "start_hour": 6.0, "duration":4.0, "freq_index":1},
                                 {"time_period":"MD", "start_hour":10.0, "duration":5.0, "freq_index":2},
                                 {"time_period":"PM", "start_hour":15.0, "duration":4.0, "freq_index":3},
                                 {"time_period":"EV", "start_hour":19.0, "duration":8.0, "freq_index":4}])

def addTripStopsToStopSequence(stop_sequence_df, trip_id, trip_stops_df):
    """
    Given a stop sequence dataframe, adds another trip
    More details to come
    """

    num_duplicates = trip_stops_df.duplicated(subset=["stop_id"]).sum()
    if num_duplicates > 0:
        Wrangler.WranglerLogger.debug("Duplicate stop_ids\n{}".format(trip_stops_df))
        error_str = "addTripStopsToStopSequence() received trip_stops_df with {} duplicate stop_ids which isn't handled yet".format(num_duplicates)
        raise NotImplementedError(error_str)

    # rename stop_sequence as the trip_id and make it a float
    trip_stops_df = trip_stops_df.copy()
    trip_stops_df[trip_id] = trip_stops_df["stop_sequence"].astype(numpy.float)
    trip_stops_df = trip_stops_df[["stop_id", trip_id]]

    # first one - just keep it as - but rename the stop_sequence to be the trip_id
    if len(stop_sequence_df) == 0:
        return trip_stops_df

    Wrangler.WranglerLogger.debug("addTripStopsToStopSequence initial stop_sequence_df:\n{}".format(stop_sequence_df))
    Wrangler.WranglerLogger.debug("addTripStopsToStopSequence {}:\n{}".format(trip_id, trip_stops_df))
    # outer join on stop id
    existing_cols  = list(stop_sequence_df.columns)
    existing_trips = existing_cols[1:]
    assert(existing_cols[0] == "stop_id")

    stop_sequence_df = pandas.merge(left=stop_sequence_df,
                                    right=trip_stops_df,
                                    how="outer")
    stop_sequence_df = stop_sequence_df[existing_cols + [trip_id]].sort_values(by=existing_trips + [trip_id])
    stop_sequence_df["next_seq"] = stop_sequence_df[trip_id].shift(-1)
    stop_sequence_df["prev_seq"] = stop_sequence_df[trip_id].shift( 1)

    # Wrangler.WranglerLogger.debug(stop_sequence_df)

    # sequence should be less than next
    # sequence should be greater than prev
    stop_sequence_df["bad"] = 0
    stop_sequence_df.loc[ stop_sequence_df[trip_id] > stop_sequence_df["next_seq"], "bad" ] = 1
    stop_sequence_df.loc[ stop_sequence_df[trip_id] < stop_sequence_df["prev_seq"], "bad" ] = 1

    if stop_sequence_df["bad"].sum() > 0:
        Wrangler.WranglerLogger.debug("Sequencing problem\n{}".format(stop_sequence_df))
        error_str = "addTripStopsToStopSequence() found inconsistent stop sequencing"
        raise NotImplementedError(error_str)

    stop_sequence_df = stop_sequence_df.drop(columns=["next_seq","prev_seq","bad"])
    return stop_sequence_df


def gtfsToSchedule(operator_set, feed, existing_trn_net):
    """
    """
    Wrangler.WranglerLogger.debug("gtfsToSchedule.  ROUTES:\n{}".format(feed.routes))

    # assign stop times to timeperiods
    time_period_dict = TIME_PERIODS.set_index("time_period").to_dict(orient="index")

    stop_times_df = feed.stop_times.copy()
    stop_times_df["time_period"] = ""
    stop_times_df.loc[ pandas.notnull(stop_times_df["departure_time"]), "time_period" ] = "EV"
    stop_times_df.loc[ stop_times_df["departure_time"] > time_period_dict["EA"]["start_hour"]*60*60, "time_period" ] = "EA"
    stop_times_df.loc[ stop_times_df["departure_time"] > time_period_dict["AM"]["start_hour"]*60*60, "time_period" ] = "AM"
    stop_times_df.loc[ stop_times_df["departure_time"] > time_period_dict["MD"]["start_hour"]*60*60, "time_period" ] = "MD"
    stop_times_df.loc[ stop_times_df["departure_time"] > time_period_dict["PM"]["start_hour"]*60*60, "time_period" ] = "PM"
    stop_times_df.loc[ stop_times_df["departure_time"] > time_period_dict["EV"]["start_hour"]*60*60, "time_period" ] = "EV"
    Wrangler.WranglerLogger.debug("stop_times_df head\n{}".format(stop_times_df.head(10)))


    new_trn_net = Wrangler.TransitNetwork(modelType = Wrangler.Network.MODEL_TYPE_TM2,
                                          modelVersion = 1.0, networkName=operator_set)
    new_trn_net.program = Wrangler.TransitParser.PROGRAM_PT

    for route_id in sorted(feed.routes["route_id"].tolist()):
        Wrangler.WranglerLogger.info("==================== ROUTE {} =========================================".format(route_id))

        # is this route bi-directional?
        route_by_dir_df = feed.trips.loc[ feed.trips.route_id==route_id , ["route_id", "trip_headsign", "direction_id"]]
        route_by_dir_df = route_by_dir_df.groupby(["direction_id"]).agg({"route_id":"count", "trip_headsign":"first"}).reset_index()
        route_by_dir_df.rename(columns={"route_id":"trip_count"}, inplace=True)
        Wrangler.WranglerLogger.info("Route by direction:\n{}".format(route_by_dir_df))

        gtfs_direction_ids = route_by_dir_df["direction_id"].tolist()
        Wrangler.WranglerLogger.info("gtfs_direction_ids = {}".format(gtfs_direction_ids))

        for direction_id in gtfs_direction_ids:

            # if not bidirectional, assume all the existing lines with this route number are this route
            # if bidirectional than the existing network lines need to be split by direction
            if len(gtfs_direction_ids) == 1:
                route_re_str = "{}{}".format(OPERATOR_SET_DICT[operator_set]["existing_re"], route_id)
                Wrangler.WranglerLogger.info("Route {} assuming existing network lines {}".format(route_id, route_re_str))
                new_lin_name = OPERATOR_SET_DICT[operator_set]["lin_prefix"] + route_id

            else:
                # bidirectional -- look to configuration
                route_dir_tuple = (route_id, direction_id)
                if route_dir_tuple in OPERATOR_SET_DICT[operator_set]["existing_route_re"]:
                    route_re_str = OPERATOR_SET_DICT[operator_set]["existing_route_re"][route_dir_tuple][0]
                    new_lin_name = OPERATOR_SET_DICT[operator_set]["existing_route_re"][route_dir_tuple][1]
                    Wrangler.WranglerLogger.info("Route/Dir {} assuming existing network lines {}".format(route_dir_tuple, route_re_str))
                else:
                    # warn later
                    route_re_str = None
                    new_lin_name = None

            trips_for_route_df = feed.trips.loc[ (feed.trips.route_id==route_id)&
                                                 (feed.trips.direction_id==direction_id) ]

            Wrangler.WranglerLogger.info("processing route {} direction {}; trips:\n{}".format(route_id,
                                          direction_id, trips_for_route_df))

            # get the schedules for those trips
            trip_ids           = trips_for_route_df.trip_id.tolist()
            trip_stop_times_df = stop_times_df.loc[ feed.stop_times.trip_id.isin(trip_ids)]
            # e.g.
            #        trip_id  arrival_time  departure_time   stop_id  stop_sequence time_period
            # 15737  5969406       25500.0         25500.0  12009440              1          AM
            # 15738  5969406           NaN             NaN  12009188              2            
            # 15739  5969406           NaN             NaN  12009801              3            
            # 15740  5969406           NaN             NaN  12009733              4            
            # 15741  5969406           NaN             NaN  12009802              5            


            # start with the longest lines and work backwards
            trip_lengths_df = trip_stop_times_df[["trip_id","stop_sequence"]].groupby(["trip_id"]).agg("count").reset_index()
            trip_lengths_df.sort_values(by="stop_sequence", ascending=False, inplace=True)
            Wrangler.WranglerLogger.info("trip lengths:\n{}".format(trip_lengths_df))

            # disabling this for now since transit route variations tend to be too complicated for this to work :(
            if False:
                # try to construct a single stop sequence for all trips
                trip_ids_by_len  = trip_lengths_df["trip_id"].tolist()
                stop_sequence_df = pandas.DataFrame()
                try:
                    for trip_id in trip_ids_by_len:
                        stop_sequence_df = addTripStopsToStopSequence(stop_sequence_df, trip_id, trip_stop_times_df.loc[trip_stop_times_df["trip_id"]==trip_id])

                    Wrangler.WranglerLogger.debug("Final stop sequence:\n{}".format(stop_sequence_df))

                except RuntimeError as error:
                    Wrangler.WranglerLogger.warn("Problem creating unified stop sequence for trips")
                    Wrangler.WranglerLogger.warn(error)
                    stop_sequence_df = pandas.DataFrame()

            # if we have no existing network lines to base this route on, continue
            # (we didn't continue earlier to get info on the gtfs lines being dropped)
            if route_re_str == None:
                Wrangler.WranglerLogger.warn("=======> Route/Dir {} lines not configured in existing network".format(route_dir_tuple))
                continue

            # for simplicity, we'll just copy the longest route
            route_re   = re.compile(route_re_str)
            proto_line = None
            max_stops  = 0
            for line in existing_trn_net.line(route_re):
                 stops = line.listNodeIds(ignoreStops=False)
                 Wrangler.WranglerLogger.info("Existing {} has length {}  First 5: {}  Last 5{}".format(
                                              str(line), line.numStops(), stops[:5], stops[-5:]))
                 if line.numStops() > max_stops:
                    max_stops = line.numStops()
                    proto_line = copy.copy(line)  # hmm may need to write TransitLine.copy()

            if proto_line == None:
                Wrangler.WranglerLogger.warn("=======> No existing routes coded for ROUTE {} (regex: {})".format(route_id, route_re_str))
                continue

            # set the frequency of the proto line:
            # assign each trip to a time period based on the max number of time points associated with each time period
            trip_freq_df = trip_stop_times_df.loc[ pandas.notnull(trip_stop_times_df["departure_time"]) ]
            trip_freq_df["count"] = 1
            trip_freq_df = trip_freq_df[["trip_id","time_period","count"]].groupby(["trip_id","time_period"]).agg({"count":"sum"})
            Wrangler.WranglerLogger.debug("trip_freq_df=\n{}".format(trip_freq_df))
            trip_freq_df = trip_freq_df.reset_index().sort_values("count", ascending=False).drop_duplicates(["trip_id"])
            Wrangler.WranglerLogger.debug("trip_freq_df=\n{}".format(trip_freq_df))
            # each trip is now assigned to a time period -- count them up
            trip_tps_dict = trip_freq_df.groupby("time_period").agg({"trip_id":"count"}).to_dict(orient="index")
            Wrangler.WranglerLogger.debug("trip_tps_dict=\n{}".format(trip_tps_dict))

            time_period_list = TIME_PERIODS.to_dict(orient="records")
            for tp_rec in time_period_list:
                time_period = tp_rec["time_period"]
                if time_period in trip_tps_dict:
                    frequency = tp_rec["duration"]*60/trip_tps_dict[time_period]["trip_id"]
                else:
                    frequency = 0
                proto_line.attr["HEADWAY[{}]".format(tp_rec["freq_index"]+1)] = frequency

            # add the line
            old_lin_name = proto_line.name
            proto_line.name = new_lin_name
            Wrangler.WranglerLogger.info("=======> From existing {} created {}".format(old_lin_name, str(proto_line)))
            Wrangler.WranglerLogger.info("")
            new_trn_net.lines.append(proto_line)

    # write it, such as it is
    new_trn_net.write(name=operator_set, writeEmptyFiles=False, suppressQuery=False, suppressValidation=True)


def calculateScheduleBoardAlightHeadways(schedule_df, station_key_df):
    """
    Returns two dataframes:
    combined_headway_df with columns
      Station Name_board
      Station Num_board
      Station Name_alight
      Station Num_alight
      time_period
      duration (of time period)
      trip_count schedule
      avg_headway schedule

    board_alight_df with columns
      Station Name_board
      Station Name_alight
      Trip Number
      time_board
      time_alight
      board_hour
      time_period
    """
    Wrangler.WranglerLogger.debug("calculateScheduleBoardAlightHeadways")

    # melt the schedule to station, type, number, time point
    schedule_df = schedule_df.reset_index(drop=False).rename(columns={"index":"Station Name"})
    schedule_df = pandas.merge(left=schedule_df, right=station_key_df[["Station Name","Station Num"]], how="left")
    # columns are now Station Name, Station Num, Trip Number, time
    schedule_melt_df = pandas.melt(schedule_df, id_vars=["Station Num","Station Name"])
    schedule_melt_df = schedule_melt_df.loc[pandas.notnull(schedule_melt_df.value)]
    schedule_melt_df.rename(columns={"variable":"Trip Number","value":"time"}, inplace=True)
    # print(schedule_melt_df.head())
    #    Station Num      Station Name Trip Number                time
    # 6           07  San Jose Diridon         101 1900-01-01 04:30:00
    # 8           09       Santa Clara         101 1900-01-01 04:35:00
    # 9           10          Lawrence         101 1900-01-01 04:40:00
    # 10          11         Sunnyvale         101 1900-01-01 04:44:00
    # 11          12     Mountain View         101 1900-01-01 04:49:00
    board_alight_df = pandas.merge(left    =schedule_melt_df,
                                   right   =schedule_melt_df,
                                   how     ="outer",
                                   on      ="Trip Number",
                                   suffixes=["_board","_alight"])
    # Gotta alight after boarding
    board_alight_df = board_alight_df.loc[board_alight_df["Station Num_alight"] > board_alight_df["Station Num_board"]]

    # Assign a time period for the board/alight pair
    board_alight_df["board_hour" ] = board_alight_df["time_board"].dt.hour
    # Wrangler.WranglerLogger.debug(board_alight_df["board_hour"].value_counts())

    board_alight_df["time_period"] = "EV"
    board_alight_df.loc[ board_alight_df.board_hour >=  3, "time_period" ] = "EA"
    board_alight_df.loc[ board_alight_df.board_hour >=  6, "time_period" ] = "AM"
    board_alight_df.loc[ board_alight_df.board_hour >= 10, "time_period" ] = "MD"
    board_alight_df.loc[ board_alight_df.board_hour >= 15, "time_period" ] = "PM"
    board_alight_df.loc[ board_alight_df.board_hour >= 19, "time_period" ] = "EV"
    # Wrangler.WranglerLogger.debug(board_alight_df["time_period"].value_counts())
    Wrangler.WranglerLogger.debug("board_alight_df\n{}".format(board_alight_df.head()))


    # groupby board station, alight station, time period
    combined_headway_df = board_alight_df[["Station Name_board","Station Num_board","Station Name_alight","Station Num_alight","time_period", "Trip Number"]].groupby(
                                          ["Station Name_board","Station Num_board","Station Name_alight","Station Num_alight","time_period"]).agg("count")
    combined_headway_df = pandas.merge(left=combined_headway_df.reset_index(), right=TIME_PERIODS, how="left")
    combined_headway_df["avg_headway schedule"] = combined_headway_df["duration"]*60/combined_headway_df["Trip Number"]

    # column fixups
    combined_headway_df.rename(columns={"Trip Number":"trip_count schedule"}, inplace=True)
    combined_headway_df.drop(labels=["start_hour","freq_index"], axis="columns", inplace=True)

    Wrangler.WranglerLogger.debug("combined_headway_df\n{}".format(combined_headway_df.head()))

    return combined_headway_df, board_alight_df

def calculateTransitNetworkBoardAlightHeadways(trn_network, station_key_df, schedule_headways_df, line_name_regex, label):
    """
    Returns copy of schedule_headways_df, which has columns:
      Station Name_board
      Station Num_board
      Station Name_alight
      Station Num_alight
      time_period
      duration (of time period)
    Adds the following two columns:
      trip_count [label]
      avg_headway [label]
      avg_headway_diff [label] (avg_headway [label] - avg_headway schedule)
    Also returns a dictionary with:
      mae [timeperiod], or Mean Absolute Error (1/n sum of abs diff)
      rmse [timeperiod], or Root Mean Squared Error (sqrt 1/n sum diff squared)
    """
    # e.g. "AM" -> {"duration":4.0, "freq_index":1}
    time_period_dict = TIME_PERIODS.set_index("time_period").to_dict(orient="index")

    all_lines_df = pandas.DataFrame()

    # iterate through the relevant lines
    for line in trn_network.line(line_name_regex):
        Wrangler.WranglerLogger.debug("processing line: {}".format(line))

        # form an initial dataframe with columns line_name, time_period, freq, trip_count, duration
        freqs      = line.getFreqs()
        line_dicts = []
        line_df    = pandas.DataFrame()

        for time_period in time_period_dict.keys():
            freq_index = int(time_period_dict[time_period]["freq_index"])
            line_dict  = time_period_dict[time_period].copy()
            line_dict["time_period"] = time_period
            line_dict["freq"       ] = float(freqs[freq_index])
            line_dict["line_name"  ] = line.name
            # don't need this
            del line_dict["freq_index"]

            line_dicts.append(line_dict)

        line_df    = pandas.DataFrame(line_dicts)
        # drop the ones with freq=0
        line_df = line_df.loc[line_df.freq > 0]
        # set trip_count
        line_df["trip_count"] = line_df["duration"]*60.0/line_df["freq"]

        # create a dataframe for the station nodes with columns Station Node, line_name
        node_dicts = []
        for stop in line:
            node_dict = {"Station Node":stop, "line_name":line.name}
            node_dicts.append(node_dict)
        node_df = pandas.DataFrame(node_dicts)

        line_df = pandas.merge(left=line_df, right=node_df, how="outer")
        line_df = pandas.merge(left=line_df, right=station_key_df, how="left") # add Station Name, Station Num

        # add to all_lines
        all_lines_df = pandas.concat([all_lines_df, line_df])

    Wrangler.WranglerLogger.debug("all_lines_df has length {} and head\n{}".format(len(all_lines_df), all_lines_df.head()))
    #    duration  freq     line_name time_period trip_count  Station Node  Station Name Station Num
    # 0       4.0  60.0  CT_NORTHBOUr          AM        4.0       2116959        Gilroy          01
    # 1       4.0  60.0  CT_NORTHBOUr          AM        4.0       2117074    San Martin          02
    # 2       4.0  60.0  CT_NORTHBOUr          AM        4.0       2117027   Morgan Hill          03
    # 3       4.0  60.0  CT_NORTHBOUr          AM        4.0       2117070  Blossom Hill          04
    # 4       4.0  60.0  CT_NORTHBOUr          AM        4.0       2117060       Capitol          05
    # drop  freq - we'll use trip_count
    all_lines_df.drop(labels=["freq"], axis="columns", inplace=True)
    board_alight_df = pandas.merge(left    =all_lines_df,
                                   right   =all_lines_df,
                                   how     ="outer",
                                   on      =["line_name","time_period","duration","trip_count"],
                                   suffixes=["_board","_alight"])
    # Gotta alight after boarding
    board_alight_df = board_alight_df.loc[board_alight_df["Station Num_alight"] > board_alight_df["Station Num_board"]]
    Wrangler.WranglerLogger.debug("board_alight_df\n{}".format(board_alight_df.head()))

    # groupby board station, alight station, time period
    combined_headway_df = board_alight_df[["Station Name_board","Station Num_board","Station Name_alight","Station Num_alight","time_period","duration","trip_count"]].groupby(
                                          ["Station Name_board","Station Num_board","Station Name_alight","Station Num_alight","time_period","duration"]).agg({"trip_count":"sum"}, {"duration":"first"})
    combined_headway_df.reset_index(inplace=True)
    combined_headway_df["avg_headway {}".format(label)] = combined_headway_df["duration"]*60/combined_headway_df["trip_count"]
    combined_headway_df.rename(columns={"trip_count":"trip_count {}".format(label)}, inplace=True)

    # merge into schedule_headways_df
    combined_headway_df = pandas.merge(left=schedule_headways_df, right=combined_headway_df, how="outer")
    combined_headway_df["avg_headway_diff {}".format(label)] = combined_headway_df["avg_headway {}".format(label)] - \
                                                               combined_headway_df["avg_headway schedule"]
    Wrangler.WranglerLogger.debug("combined_headway_df\n{}".format(combined_headway_df.head()))

    ret_dict = {}
    for time_period in time_period_dict.keys():

        ret_dict["mae {}".format(time_period)] = \
            combined_headway_df.loc[ combined_headway_df["time_period"] == time_period,
                                     "avg_headway_diff {}".format(label)].abs().sum() / len(combined_headway_df)
        err_sq = combined_headway_df.loc[ combined_headway_df["time_period"] == time_period,
                                          "avg_headway_diff {}".format(label) ] ** 2
        ret_dict["rmse {}".format(time_period)] = math.sqrt( err_sq.sum() / len(err_sq))
    Wrangler.WranglerLogger.debug("ret_dict: {}".format(ret_dict))

    return combined_headway_df, ret_dict

def createNetworkForSchedule(operator_set, schedule_df, station_key_df, trips_df, schedule_headways_df):
    """
    Quick attempt to create a network for the given schedule.

    Adds headways to schedule_headways_df
    """
    Wrangler.WranglerLogger.debug("createNetworkForSchedule: schedule_df\n{}".format(schedule_df.head(10)))
    Wrangler.WranglerLogger.debug("createNetworkForSchedule: station_key_df\n{}".format(station_key_df.head(10)))
    Wrangler.WranglerLogger.debug("createNetworkForSchedule: trips_df\n{}".format(trips_df.head(10)))
    Wrangler.WranglerLogger.debug("createNetworkForSchedule: schedule_headways_df\n{}".format(schedule_headways_df.head(10)))

    # iterate through each trip and figure out what time period it's in by what time period the most stops are in
    trip_records = trips_df.to_dict("records")
    for trip_rec in trip_records:

        trip_id = trip_rec["Trip Number"]
        trip_schedule_df = schedule_df[[trip_id]]
        trip_schedule_df = trip_schedule_df.loc[ pandas.notnull(trip_schedule_df[trip_id] )] # remove NaT rows
        trip_schedule_df["time_period"] = "EV"
        trip_schedule_df["stop_hour"  ] = trip_schedule_df[trip_id].dt.hour
        trip_schedule_df.loc[ trip_schedule_df.stop_hour >=  3, "time_period" ] = "EA"
        trip_schedule_df.loc[ trip_schedule_df.stop_hour >=  6, "time_period" ] = "AM"
        trip_schedule_df.loc[ trip_schedule_df.stop_hour >= 10, "time_period" ] = "MD"
        trip_schedule_df.loc[ trip_schedule_df.stop_hour >= 15, "time_period" ] = "PM"
        trip_schedule_df.loc[ trip_schedule_df.stop_hour >= 19, "time_period" ] = "EV"

        # set the time_period to the most frequent stop time period
        trip_rec["time_period"] = trip_schedule_df["time_period"].value_counts().index[0]

    # put the trips dataframe back together, now with columns Trip Number, Trip Type, and time_period
    trips_df = pandas.DataFrame(trip_records)
    Wrangler.WranglerLogger.debug("trips with time_periods:\n{}".format(trips_df))

    # start with the most frequent version of each Trip Type in each time_period
    trip_groups = trips_df.groupby(["Trip Type"])

    stop_names_list = station_key_df.to_dict(orient="list")["Station Name"]
    trips_list = trips_df.to_dict(orient="list")["Trip Number"]


    # transforme the schedule into a series of strings, one for each trip
    schedule_str_df = pandas.notnull(schedule_df).replace({True:"S",False:"."}).transpose()
    all_stops = pandas.Series(schedule_str_df.values.tolist()).str.join("")
    trips_df["all_stops"] = all_stops
    # print(trips_list)
    #   Trip Number Trip Type time_period                      all_stops
    # 0         101     Local          EA  ......S.SSSSSSSSSSSSSSSSSSSSS
    # 1         103     Local          EA  .....SS.SSSSSSSSSSSSSSSSSSSSS
    # 2         305        BB          AM  ......S....S..S....S...S....S
    # 3         207   Limited          AM  .....SS.SSSSSSSSS..S...S.S..S
    # 4         309        BB          AM  .....SS...S...S.S....S.S....S

    all_stops.index = schedule_str_df.index
    # print(all_stops)
    #    Trip Number                       stop_str
    # 0          101  ......S.SSSSSSSSSSSSSSSSSSSSS
    # 1          103  .....SS.SSSSSSSSSSSSSSSSSSSSS
    # 2          305  ......S....S..S....S...S....S
    # 3          207  .....SS.SSSSSSSSS..S...S.S..S
    # 4          309  .....SS...S...S.S....S.S....S

    # Don't bother with DBSCAN because it calls a few trips noise
    # clusterTrips_DBSCAN(trips_df, all_stops, eps=2, min_samples=2)
    # clusterTrips_DBSCAN(trips_df, all_stops, eps=3, min_samples=2)
    # clusterTrips_DBSCAN(trips_df, all_stops, eps=4, min_samples=2)

    # clusterTrips_DBSCAN(trips_df, all_stops, eps=2, min_samples=3)
    # clusterTrips_DBSCAN(trips_df, all_stops, eps=3, min_samples=3)
    # clusterTrips_DBSCAN(trips_df, all_stops, eps=4, min_samples=3)

    any_re = re.compile(".*")

    combined_headway_all_df = schedule_headways_df
    summary_dict_list = []
    for nc in range(5,13):
        label = "spectral_{:02d}".format(nc)
        clusterTrips_Spectral(trips_df, all_stops, n_clusters= nc)
        trn_net, single_trip_type_pct = tripClusterToNetwork(operator_set, schedule_df, station_key_df, trips_df)
        combined_headway_all_df, summary_dict = calculateTransitNetworkBoardAlightHeadways(
                                                    trn_net, station_key_df, combined_headway_all_df, any_re, label=label)
        summary_dict["label"] = label
        summary_dict["single_trip_type_pct"] = single_trip_type_pct
        summary_dict_list.append(summary_dict)

        # write if it's the winning label
        if ("winner_label" in OPERATOR_SET_DICT[operator_set]) and (label == OPERATOR_SET_DICT[operator_set]["winner_label"]):
            trn_net.write(name=operator_set, writeEmptyFiles=False, suppressQuery=False, suppressValidation=True)

    for nc in range(5,13):
        label = "agg_complete_{:02d}".format(nc)
        clusterTrips_Agglomerative(trips_df, all_stops, n_clusters= nc, linkage="complete")
        trn_net, single_trip_type_pct = tripClusterToNetwork(operator_set, schedule_df, station_key_df, trips_df)
        combined_headway_all_df, summary_dict = calculateTransitNetworkBoardAlightHeadways(
                                                    trn_net, station_key_df, combined_headway_all_df, any_re, label=label)
        summary_dict["label"] = label
        summary_dict["single_trip_type_pct"] = single_trip_type_pct
        summary_dict_list.append(summary_dict)

        # write if it's the winning label
        if ("winner_label" in OPERATOR_SET_DICT[operator_set]) and (label == OPERATOR_SET_DICT[operator_set]["winner_label"]):
            trn_net.write(name=operator_set, writeEmptyFiles=False, suppressQuery=False, suppressValidation=True)

    for nc in range(5,13):
        label = "agg_avg_{:02d}".format(nc)
        clusterTrips_Agglomerative(trips_df, all_stops, n_clusters= nc, linkage="average")
        trn_net, single_trip_type_pct = tripClusterToNetwork(operator_set, schedule_df, station_key_df, trips_df)
        combined_headway_all_df, summary_dict = calculateTransitNetworkBoardAlightHeadways(
                                                    trn_net, station_key_df, combined_headway_all_df, any_re, label=label)
        summary_dict["label"] = label
        summary_dict["single_trip_type_pct"] = single_trip_type_pct
        summary_dict_list.append(summary_dict)

        # write if it's the winning label
        if ("winner_label" in OPERATOR_SET_DICT[operator_set]) and (label == OPERATOR_SET_DICT[operator_set]["winner_label"]):
            trn_net.write(name=operator_set, writeEmptyFiles=False, suppressQuery=False, suppressValidation=True)

    summary_df = pandas.DataFrame(summary_dict_list)
    Wrangler.WranglerLogger.debug("summary\n{}".format(summary_df))
    return combined_headway_all_df, summary_df

def clusterTrips_DBSCAN(trips_df, trip_series, eps, min_samples):
    """
    Given a list of trips in a series, returns clusters of trips using
    DBSCAN - Density-Based Spatial Clustering of Applications with Noise
    http://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html

    trips_df example:
        Trip Number Trip Type time_period                      all_stops
      0         101     Local          EA  ......S.SSSSSSSSSSSSSSSSSSSSS
      1         103     Local          EA  .....SS.SSSSSSSSSSSSSSSSSSSSS
      2         305        BB          AM  ......S....S..S....S...S....S
      3         207   Limited          AM  .....SS.SSSSSSSSS..S...S.S..S
      4         309        BB          AM  .....SS...S...S.S....S.S....S

    trip_series example:
      Trip Number
      101     ......S.SSSSSSSSSSSSSSSSSSSSS
      103     .....SS.SSSSSSSSSSSSSSSSSSSSS
      305     ......S....S..S....S...S....S
      207     .....SS.SSSSSSSSS..S...S.S..S
      309     .....SS...S...S.S....S.S....S
      211     ......S.S.SS...SSSSSSSSSSSSSS

    Sets the column, cluster, in trips_df based on the results.
    """

    trip_series_list = trip_series.tolist()
    # print(trip_series_list)

    def dist_metric(x,y):
        i,j = int(x[0]), int(y[0]) # extract indices
        return Levenshtein.distance(trip_series_list[i], trip_series_list[j])

    # represent trips as [[0][1][2]...[n-1]] for n trips
    trip_indices = numpy.arange(len(trip_series_list)).reshape(-1,1)
    db = DBSCAN(eps=eps, min_samples=min_samples, metric=dist_metric).fit(trip_indices)

    trips_df["cluster"] = db.labels_

    Wrangler.WranglerLogger.debug("clusterTrips_DBSCAN with eps={} min_samples={}".format(eps, min_samples))
    Wrangler.WranglerLogger.debug("===================================================\n{}".format(trips_df.sort_values(by=["cluster"])))

    return trips_df

def clusterTrips_Spectral(trips_df, trip_series, n_clusters):
    """
    Given a list of trips in a series, returns clusters of trips using
    SpectralClustering
    http://scikit-learn.org/stable/modules/generated/sklearn.cluster.SpectralClustering.html

    trips_df example:
        Trip Number Trip Type time_period                      all_stops
      0         101     Local          EA  ......S.SSSSSSSSSSSSSSSSSSSSS
      1         103     Local          EA  .....SS.SSSSSSSSSSSSSSSSSSSSS
      2         305        BB          AM  ......S....S..S....S...S....S
      3         207   Limited          AM  .....SS.SSSSSSSSS..S...S.S..S
      4         309        BB          AM  .....SS...S...S.S....S.S....S

    trip_series example:
      Trip Number
      101     ......S.SSSSSSSSSSSSSSSSSSSSS
      103     .....SS.SSSSSSSSSSSSSSSSSSSSS
      305     ......S....S..S....S...S....S
      207     .....SS.SSSSSSSSS..S...S.S..S
      309     .....SS...S...S.S....S.S....S
      211     ......S.S.SS...SSSSSSSSSSSSSS

    Sets the column, cluster, in trips_df based on the results.
    """
    trip_series_list = trip_series.tolist()

    words = numpy.asarray(trip_series_list)
    lev_similarity = numpy.array([[Levenshtein.distance(w1,w2) for w1 in words] for w2 in words])
    sc = SpectralClustering(n_clusters=n_clusters, affinity="precomputed", n_init=100)
    # print(trip_series_list)
    # print(lev_similarity)

    sc.fit(lev_similarity)
    # print(sc.labels_)

    trips_df["cluster"] = sc.labels_

    Wrangler.WranglerLogger.debug("clusterTrips_Spectral with n_clusters={}".format(n_clusters))
    Wrangler.WranglerLogger.debug("===================================================\n{}".format(trips_df.sort_values(by=["cluster"])))

    return trips_df

def clusterTrips_Agglomerative(trips_df, trip_series, n_clusters, linkage):
    """
    Given a list of trips in a series, returns clusters of trips using
    AgglomerativeClustering
    http://scikit-learn.org/stable/modules/generated/sklearn.cluster.AgglomerativeClustering.html

    trips_df example:
        Trip Number Trip Type time_period                      all_stops
      0         101     Local          EA  ......S.SSSSSSSSSSSSSSSSSSSSS
      1         103     Local          EA  .....SS.SSSSSSSSSSSSSSSSSSSSS
      2         305        BB          AM  ......S....S..S....S...S....S
      3         207   Limited          AM  .....SS.SSSSSSSSS..S...S.S..S
      4         309        BB          AM  .....SS...S...S.S....S.S....S

    trip_series example:
      Trip Number
      101     ......S.SSSSSSSSSSSSSSSSSSSSS
      103     .....SS.SSSSSSSSSSSSSSSSSSSSS
      305     ......S....S..S....S...S....S
      207     .....SS.SSSSSSSSS..S...S.S..S
      309     .....SS...S...S.S....S.S....S
      211     ......S.S.SS...SSSSSSSSSSSSSS

    Sets the column, cluster, in trips_df based on the results.
    """
    trip_series_list = trip_series.tolist()

    words = numpy.asarray(trip_series_list)
    lev_similarity = numpy.array([[Levenshtein.distance(w1,w2) for w1 in words] for w2 in words])
    ac = AgglomerativeClustering(n_clusters=n_clusters, affinity="precomputed", linkage=linkage)
    ac.fit(lev_similarity)
    # print(ac.labels_)

    trips_df["cluster"] = ac.labels_

    Wrangler.WranglerLogger.debug("clusterTrips_Agglomerative with n_clusters={} linkage={}".format(n_clusters, linkage))
    Wrangler.WranglerLogger.debug("===================================================\n{}".format(trips_df.sort_values(by=["cluster"])))

    return trips_df

def tripClusterToNetwork(operator_set, schedule_df, station_key_df, trips_df):
    """
    Returns a Wrangler.TransitNetwork of the given schedule, stations and trips,
    plus a single (float) metric: percent of lines containing a single Trip Type
    """
    trn_net = Wrangler.TransitNetwork(modelType = Wrangler.Network.MODEL_TYPE_TM2,
                                      modelVersion = 1.0, networkName=operator_set)
    trn_net.program = Wrangler.TransitParser.PROGRAM_PT
    type_counts = collections.Counter()

    trn_line_dict = {}

    # iterate through clusters
    lines_with_single_trip_type = 0
    for cluster_id in sorted(trips_df["cluster"].unique().tolist()):
        Wrangler.WranglerLogger.debug("Creating line from cluster {}".format(cluster_id))

        cluster_trips_df = trips_df.loc[ trips_df.cluster == cluster_id ]

        # check how many trip types this spans
        unique_trip_type_set = set(cluster_trips_df["Trip Type"].tolist())
        if len(unique_trip_type_set) == 1:
            lines_with_single_trip_type += 1
        Wrangler.WranglerLogger.debug("Cluster trips (with {} Trip Types):\n{}".format(
                                      len(unique_trip_type_set), cluster_trips_df))

        # Figure out frequency for each time period - create  time_period -> trip count dictionary
        trip_count = cluster_trips_df.groupby("time_period").size().to_dict()

        trn_line = Wrangler.TransitLine(name="{}_{:02d}".format(OPERATOR_SET_DICT[operator_set]["lin_prefix"], cluster_id))

        time_period_list = TIME_PERIODS.to_dict(orient="records")
        for tp_rec in time_period_list:
            time_period = tp_rec["time_period"]
            if time_period in trip_count:
                frequency = tp_rec["duration"]*60/trip_count[time_period]
            else:
                frequency = 0
            trn_line.attr["HEADWAY[{}]".format(tp_rec["freq_index"]+1)] = frequency

        # add the other lin attributes
        for lin_attr_name in ["MODE", "OPERATOR", "USERA1", "USERA2", "VEHICLETYPE"]:
            trn_line.attr[lin_attr_name] = OPERATOR_SET_DICT[operator_set][lin_attr_name]

        trn_line.attr["MODE"] = OPERATOR_SET_DICT[operator_set]["MODE"]
        Wrangler.WranglerLogger.debug(trn_line)

        # use the first most common stop pattern
        cluster_all_stops_grouped = cluster_trips_df.groupby(["all_stops"])
        stop_pattern = cluster_all_stops_grouped.size().sort_values(ascending=False).index[0]
        trip_number  = cluster_all_stops_grouped.get_group(stop_pattern).iloc[0]["Trip Number"]
        trip_type    = cluster_all_stops_grouped.get_group(stop_pattern).iloc[0]["Trip Type"]
        type_counts[trip_type] += 1
        trn_line.name = "{}_{}{:02d}".format(OPERATOR_SET_DICT[operator_set]["lin_prefix"], trip_type, type_counts[trip_type])
        Wrangler.WranglerLogger.debug("{} Using stop pattern: [{}] and trip number {}".format(
                                        trn_line.name, stop_pattern, trip_number))

        # trip_schedule has the schedule to convert, with columns Station Name, stop_time
        trip_schedule_df = schedule_df[trip_number].to_frame().reset_index().rename(
                                    columns={"index":"Station Name",trip_number:"stop_time"})
        # get Station Num
        trip_schedule_df = pandas.merge(left=trip_schedule_df, right=station_key_df, how="left")
        # drop non-stops
        trip_stops_df = trip_schedule_df.loc[ pandas.notnull(trip_schedule_df["stop_time"])]
        # set prev stop time
        trip_stops_df["prev_stop_time"] = trip_stops_df["stop_time"].shift(1)
        trip_stops_df["link_time"] = trip_stops_df["stop_time"] - trip_stops_df["prev_stop_time"]
        trip_stops_df.loc[ trip_stops_df["link_time"] < pandas.to_timedelta("0 seconds"), "link_time"] = trip_stops_df["link_time"] + pandas.to_timedelta("1 day")
        neg_link_time_df = trip_stops_df.loc[ trip_stops_df["link_time"] < pandas.to_timedelta("0 seconds") ]
        if len(neg_link_time_df) > 0:
            Wrangler.WranglerLogger.fatal("negative link times:\n{}".format(neg_link_time_df))
            sys.exit(2)

        first_station_num = trip_stops_df.iloc[0]["Station Num"]
        last_station_num  = trip_stops_df.iloc[-1]["Station Num"]
        # Wrangler.WranglerLogger.debug("first_station_num: {}  last_station_num: {}".format(first_station_num, last_station_num))

        # put the link times back into trip_schedule_df and trim to first/last stations
        trip_schedule_df = pandas.merge(left=trip_schedule_df, right=trip_stops_df[["Station Num","link_time"]], how="left")
        trip_schedule_df = trip_schedule_df.loc[ trip_schedule_df["Station Num"] >= first_station_num ]
        trip_schedule_df = trip_schedule_df.loc[ trip_schedule_df["Station Num"] <=  last_station_num ]
        # Wrangler.WranglerLogger.debug("trip_schedule_df:\n{}".format(trip_schedule_df))

        for stop_rec in trip_schedule_df.to_dict(orient="records"):
            # print(stop_rec)
            stop_node = Wrangler.Node(int(stop_rec["Station Node"]))

            # no stop_time means not a stop
            if "stop_time" not in stop_rec or pandas.isnull(stop_rec["stop_time"]):
                stop_node.setStop(False)

            if "link_time" in stop_rec and not math.isnan(stop_rec["link_time"].total_seconds()):
                stop_node.attr["NNTIME"] = stop_rec["link_time"].total_seconds()/60.0
            stop_node.comment = "  ; " + stop_rec["Station Name"]
            trn_line.n.append(stop_node)

        trn_line_dict[trn_line.name] = trn_line

    # add the lines in alpha order
    for line_name in sorted(trn_line_dict.keys()):
        trn_net.lines.append(trn_line_dict[line_name])

    # return it
    single_trip_type_pct = float(lines_with_single_trip_type)/float(len(trn_net.lines))
    Wrangler.WranglerLogger.debug("==> lines with single trip type: {}/{} = {}".format(
                                  lines_with_single_trip_type, len(trn_net.lines), single_trip_type_pct))
    return trn_net, single_trip_type_pct


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("operator_set", help="Operator and operator subset", choices=sorted(OPERATOR_SET_DICT.keys()))
    args = parser.parse_args()

    log_filename = LOG_FILENAME.format(args.operator_set)
    Wrangler.setupLogging(log_filename, log_filename.replace("info","debug"))
    pandas.options.display.width = 300
    pandas.options.display.max_rows = 1000
    numpy.random.seed(seed=32)

    # read the PT transit network line file
    existing_trn_net = Wrangler.TransitNetwork(modelType=Wrangler.Network.MODEL_TYPE_TM2, modelVersion=1.0,
                                               basenetworkpath=TRN_NETFILE, isTiered=True, networkName="transitLines")
    operator_set_re = re.compile(OPERATOR_SET_DICT[args.operator_set]["existing_re"])

    schedule_file = OPERATOR_SET_DICT[args.operator_set]["schedule_file"]
    if schedule_file.endswith(".xlsx"):
        # the first two columns are the station node and station names -- make those the index
        # skip the first two rows - they should have source and some sort of table name

        # for simplicity -- read the node/number first
        station_key_df = pandas.read_excel(schedule_file,
                                           sheet_name=OPERATOR_SET_DICT[args.operator_set]["sheet_name"],
                                           usecols=[0,1], skiprows=4,
                                           header=None, names=["Station Node", "Station Name"])
        station_key_df["Station Num"] = station_key_df.index + 1
        station_key_df["Station Num"] = station_key_df["Station Num"].astype(str).str.zfill(2)
        Wrangler.WranglerLogger.debug("Station Key:\n{}".format(station_key_df.head()))

        # now read the schedule with just the station name which we'll use as the index column
        schedule_df = pandas.read_excel(schedule_file,
                                        sheet_name=OPERATOR_SET_DICT[args.operator_set]["sheet_name"],
                                        header=[2,3], usecols="B:ZZ", index_col=0)
        # keep trip Number, Type and drop multiindex for simplicity
        trips_df = schedule_df.columns.to_frame().reset_index(drop=True)
        schedule_df.columns = schedule_df.columns.droplevel(0)
        Wrangler.WranglerLogger.debug("Trips:\n{}".format(trips_df.head()))

        # convert to datetime - the station name is an index
        for column in list(schedule_df.columns):
            schedule_df[column] = pandas.to_datetime(schedule_df[column], format="%H:%M:%S")

        # In theory, the below lines could be used for the GTFS version as well
        # But in practice, the GTFS version is being used for more complicated bus systems
        # So we'll be lifting more from the existing network coding (using the existing route alightment)
        Wrangler.WranglerLogger.debug("Read schedules from {}\n{}".format(schedule_file, schedule_df.head(10)))

        schedule_headways_df, schedule_board_alight_df = calculateScheduleBoardAlightHeadways(schedule_df, station_key_df)

        combined_headway_all_df, summary_df = createNetworkForSchedule(args.operator_set, schedule_df,
                                                                       station_key_df, trips_df, schedule_headways_df)

        # read the transit stop labels
        combined_headway_all_df, existing_summary_dict = calculateTransitNetworkBoardAlightHeadways(
                                                            existing_trn_net, station_key_df, combined_headway_all_df,
                                                            operator_set_re, label="existing")
        existing_summary_dict["label"] = "existing"
        summary_df = summary_df.append(existing_summary_dict, ignore_index=True)
        summary_df.to_csv("{}_summaries.csv".format(args.operator_set), header=True, index=False)

        # merge and write them all
        combined_headway_all_df.to_csv("{}_headways.csv".format(args.operator_set), header=True, index=False)

    elif schedule_file.endswith(".zip"):
        # read gtfs
        service_ids_by_date = partridge.read_service_ids_by_date(schedule_file)
        service_ids = service_ids_by_date[OPERATOR_SET_DICT[args.operator_set]["service_date"]]
        Wrangler.WranglerLogger.debug("Service ids: {}".format(service_ids))

        gtfs_feed = partridge.feed(schedule_file, view={'trips.txt':{'service_id':service_ids}})
        gtfsToSchedule(args.operator_set, gtfs_feed, existing_trn_net)

        sys.exit()

