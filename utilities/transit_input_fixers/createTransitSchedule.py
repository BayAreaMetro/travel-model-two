import datetime,os,numpy,pandas,re,sys
import Wrangler

import Levenshtein
from sklearn.cluster import DBSCAN, AgglomerativeClustering, SpectralClustering

USAGE = """

Create transit schedule from spreadsheet or gtfs.

"""

USERNAME     = os.environ["USERNAME"]
LOG_FILENAME = "createTransitSchedule.log"
TM2_INPUTS   = os.path.join(r"C:\\Users", USERNAME, "Box\\Modeling and Surveys\\Development\\Travel Model Two Development\\Model Inputs")
TRN_NETFILE  = os.path.join(TM2_INPUTS,"2015_revised_mazs","trn")
TRN_LABELFILE= os.path.join(TM2_INPUTS,"TM2 Transit Nodes.csv")
SCHEDULE_XLS = r"M:\\Data\\Transit\\Schedules\\Caltrain\\Caltrain.xlsx"

TIME_PERIODS = pandas.DataFrame([{"time_period":"EA", "duration":3.0, "freq_index":0},
                                 {"time_period":"AM", "duration":4.0, "freq_index":1},
                                 {"time_period":"MD", "duration":5.0, "freq_index":2},
                                 {"time_period":"PM", "duration":4.0, "freq_index":3},
                                 {"time_period":"EV", "duration":8.0, "freq_index":4}])

def calculateScheduleBoardAlightHeadways(schedule_df, station_key_df):
    """
    Returns two dataframes:
    combined_headway_df with columns
      Station Name_board
      Station Name_alight
      time_period
      duration (of time period)
      trip_count
      avg_headway

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
    # columns are now Station Name, Trip Numbers
    schedule_melt_df = pandas.melt(schedule_df, id_vars=["Station Name"])
    schedule_melt_df = schedule_melt_df.loc[pandas.notnull(schedule_melt_df.value)]
    schedule_melt_df.rename(columns={"value":"time"}, inplace=True)
    # print(schedule_melt_df.head())
    #         Station Name Trip Number                time
    # 6   San Jose Diridon         101 1900-01-01 04:30:00
    # 8        Santa Clara         101 1900-01-01 04:35:00
    # 9           Lawrence         101 1900-01-01 04:40:00
    # 10         Sunnyvale         101 1900-01-01 04:44:00
    # 11     Mountain View         101 1900-01-01 04:49:00

    board_alight_df = pandas.merge(left    =schedule_melt_df,
                                   right   =schedule_melt_df,
                                   how     ="outer",
                                   on      ="Trip Number",
                                   suffixes=["_board","_alight"])
    # Gotta alight after boarding
    board_alight_df = board_alight_df.loc[board_alight_df.time_alight > board_alight_df.time_board]

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
    combined_headway_df = board_alight_df[["Station Name_board","Station Name_alight","time_period", "Trip Number"]].groupby(
                                          ["Station Name_board","Station Name_alight","time_period"]).agg("count")
    combined_headway_df = pandas.merge(left=combined_headway_df.reset_index(), right=TIME_PERIODS, how="left")
    combined_headway_df["avg_headway"] = combined_headway_df["duration"]*60/combined_headway_df["Trip Number"]

    # column fixups
    combined_headway_df.rename(columns={"Trip Number":"trip_count"}, inplace=True)
    combined_headway_df.drop(labels=["freq_index"], axis="columns", inplace=True)

    Wrangler.WranglerLogger.debug("combined_headway_df\n{}".format(combined_headway_df.head()))

    return combined_headway_df, board_alight_df

def calculateTransitNetworkBoardAlightHeadways(trn_network, station_key_df, line_name_regex):
    """
    Retruns a dataframe, combined_headway_df, with columns:
      Station Name_board
      Station Name_alight
      time_period
      duration (of time period)
      trip_count
      avg_headway
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
    combined_headway_df = board_alight_df[["Station Name_board","Station Name_alight","time_period","duration","trip_count"]].groupby(
                                          ["Station Name_board","Station Name_alight","time_period","duration"]).agg({"trip_count":"sum"}, {"duration":"first"})
    combined_headway_df.reset_index(inplace=True)
    combined_headway_df["avg_headway"] = combined_headway_df["duration"]*60/combined_headway_df["trip_count"]
    Wrangler.WranglerLogger.debug("combined_headway_df\n{}".format(combined_headway_df.head()))
    return combined_headway_df

def createNetworkForSchedule(schedule_df, station_key_df, trips_df):
    """
    Quick attempt to create a network for the given schedule.
    """
    Wrangler.WranglerLogger.debug("createNetworkForSchedule: schedule_df\n{}".format(schedule_df.head(10)))
    Wrangler.WranglerLogger.debug("createNetworkForSchedule: station_key_df\n{}".format(station_key_df.head(10)))
    Wrangler.WranglerLogger.debug("createNetworkForSchedule: trips_df\n{}".format(trips_df.head(10)))

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

    clusterTrips_DBSCAN(trips_df, all_stops, eps=2, min_samples=2)
    clusterTrips_DBSCAN(trips_df, all_stops, eps=3, min_samples=2)
    clusterTrips_DBSCAN(trips_df, all_stops, eps=4, min_samples=2)

    clusterTrips_DBSCAN(trips_df, all_stops, eps=2, min_samples=3)
    clusterTrips_DBSCAN(trips_df, all_stops, eps=3, min_samples=3)
    clusterTrips_DBSCAN(trips_df, all_stops, eps=4, min_samples=3)

    clusterTrips_Spectral(trips_df, all_stops, n_clusters= 5)
    clusterTrips_Spectral(trips_df, all_stops, n_clusters= 6)
    clusterTrips_Spectral(trips_df, all_stops, n_clusters= 7)
    clusterTrips_Spectral(trips_df, all_stops, n_clusters= 8)
    clusterTrips_Spectral(trips_df, all_stops, n_clusters= 9)
    clusterTrips_Spectral(trips_df, all_stops, n_clusters=10)
    clusterTrips_Spectral(trips_df, all_stops, n_clusters=11)
    clusterTrips_Spectral(trips_df, all_stops, n_clusters=12)

    clusterTrips_Agglomerative(trips_df, all_stops, n_clusters= 5, linkage="complete")
    clusterTrips_Agglomerative(trips_df, all_stops, n_clusters= 6, linkage="complete")
    clusterTrips_Agglomerative(trips_df, all_stops, n_clusters= 7, linkage="complete")
    clusterTrips_Agglomerative(trips_df, all_stops, n_clusters= 8, linkage="complete")
    clusterTrips_Agglomerative(trips_df, all_stops, n_clusters= 9, linkage="complete")
    clusterTrips_Agglomerative(trips_df, all_stops, n_clusters=10, linkage="complete")
    clusterTrips_Agglomerative(trips_df, all_stops, n_clusters=11, linkage="complete")
    clusterTrips_Agglomerative(trips_df, all_stops, n_clusters=12, linkage="complete")

    clusterTrips_Agglomerative(trips_df, all_stops, n_clusters= 5, linkage="average")
    clusterTrips_Agglomerative(trips_df, all_stops, n_clusters= 6, linkage="average")
    clusterTrips_Agglomerative(trips_df, all_stops, n_clusters= 7, linkage="average")
    clusterTrips_Agglomerative(trips_df, all_stops, n_clusters= 8, linkage="average")
    clusterTrips_Agglomerative(trips_df, all_stops, n_clusters= 9, linkage="average")
    clusterTrips_Agglomerative(trips_df, all_stops, n_clusters=10, linkage="average")
    clusterTrips_Agglomerative(trips_df, all_stops, n_clusters=11, linkage="average")
    clusterTrips_Agglomerative(trips_df, all_stops, n_clusters=12, linkage="average")

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
    sc.fit(lev_similarity)
    print(sc.labels_)

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
    print(ac.labels_)

    trips_df["cluster"] = ac.labels_

    Wrangler.WranglerLogger.debug("clusterTrips_Agglomerative with n_clusters={} linkage={}".format(n_clusters, linkage))
    Wrangler.WranglerLogger.debug("===================================================\n{}".format(trips_df.sort_values(by=["cluster"])))

    return trips_df

if __name__ == '__main__':
    Wrangler.setupLogging(LOG_FILENAME, LOG_FILENAME.replace("info","debug"))
    pandas.options.display.width = 300
    pandas.options.display.max_rows = 1000

    # the first two columns are the station node and station names -- make those the index
    # skip the first two rows - they should have source and some sort of table name

    # for simplicity -- read the node/number first
    station_key_df = pandas.read_excel(SCHEDULE_XLS, usecols=[0,1], skiprows=4,
                                       header=None, names=["Station Node", "Station Name"])
    station_key_df["Station Num"] = station_key_df.index + 1
    station_key_df["Station Num"] = station_key_df["Station Num"].astype(str).str.zfill(2)
    Wrangler.WranglerLogger.debug("Station Key:\n{}".format(station_key_df.head()))

    # now read the schedule with just the station name which we'll use as the index column
    schedule_df = pandas.read_excel(SCHEDULE_XLS, header=[2,3], usecols="B:ZZ", index_col=0)
    # keep trip Number, Type and drop multiindex for simplicity
    trips_df = schedule_df.columns.to_frame().reset_index(drop=True)
    schedule_df.columns = schedule_df.columns.droplevel(0)
    Wrangler.WranglerLogger.debug("Trips:\n{}".format(trips_df.head()))

    # convert to datetime - the station name is an index
    for column in list(schedule_df.columns):
        schedule_df[column] = pandas.to_datetime(schedule_df[column], format="%H:%M:%S")

    Wrangler.WranglerLogger.debug("Read schedules from {}\n{}".format(SCHEDULE_XLS, schedule_df.head(10)))
    # Wrangler.WranglerLogger.debug("Schedule index: {}".format(schedule_df.index))

    schedule_headways_df, schedule_board_alight_df = calculateScheduleBoardAlightHeadways(schedule_df, station_key_df)

    createNetworkForSchedule(schedule_df, station_key_df, trips_df)
    sys.exit()

    # read the PT transit network line file
    trn_net = Wrangler.TransitNetwork(modelType=Wrangler.Network.MODEL_TYPE_TM2, modelVersion=1.0,
                                      basenetworkpath=TRN_NETFILE, isTiered=True, networkName="transitLines")
    # read the transit stop labels
    caltrain_nb_re = re.compile("^CT_NORTH")
    existing_pt_headways_df = calculateTransitNetworkBoardAlightHeadways(trn_net, station_key_df, caltrain_nb_re)

    # trn_net.write(path=".", name="transitLines", writeEmptyFiles=False, suppressValidation=True)
