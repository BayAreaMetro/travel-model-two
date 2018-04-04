import datetime,os,pandas,sys
import partridge
import Wrangler

USAGE = """

Skeleton script to update PT Transit Lines with link times.

"""

USERNAME     = os.environ["USERNAME"]
LOG_FILENAME = "addLinkTime_info.log"
TM2_INPUTS   = os.path.join(r"C:\\Users", USERNAME, "Box\\Modeling and Surveys\\Development\\Travel Model Two Development\\Model Inputs")
TRN_NETFILE  = os.path.join(TM2_INPUTS,"2015","trn","transit_lines")
TRN_LABELFILE= os.path.join(TM2_INPUTS,"TM2 Transit Nodes.csv")
GTFS_DIR     = r"M:\\Data\\Transit\\511\\Dec 2014\\GTFS"

GTFS_NETWORKS = {
    "San Francisco MUNI": "GTFSTransitData_SF_2014.11.29.zip"
}

if __name__ == '__main__':
    Wrangler.setupLogging(LOG_FILENAME, LOG_FILENAME.replace("info","debug"))
    pandas.options.display.width = 180
    pandas.options.display.max_rows = 1000

    # read the PT transit network line file
    trn_net = Wrangler.TransitNetwork(champVersion=4.3, basenetworkpath=TRN_NETFILE, isTiered=True, networkName="transitLines")

    # read the transit stop labels
    Wrangler.WranglerLogger.info("Reading transit stop labels from %s" % TRN_LABELFILE)
    trn_stop_labels = pandas.read_csv(TRN_LABELFILE, dtype={"GTFS STOP ID SB":object, "GTFS STOP ID NB":object})
    # keep only those with TM2 Node set - then we can make them ints
    trn_stop_labels = trn_stop_labels.loc[ pandas.notnull(trn_stop_labels["TM2 Node"]) ]
    trn_stop_labels["TM2 Node"] = trn_stop_labels["TM2 Node"].astype(int)
    trn_stop_labels.set_index("TM2 Node", inplace=True)

    for operator in ["San Francisco MUNI"]:
        Wrangler.WranglerLogger.info("Processing operator %s" % operator)

        # get the stop labels for this operator
        operator_stop_labels = trn_stop_labels.loc[ trn_stop_labels["Operator"] == operator ]
        Wrangler.WranglerLogger.debug("operator_stop_labels.head()\n%s" % operator_stop_labels.head())
        # make into a dictionary for quick lookup by TM2 node number
        operator_stop_label_dict = operator_stop_labels.to_dict(orient="index")

        # read GTFS
        fullpath = os.path.join(GTFS_DIR, GTFS_NETWORKS[operator])
        service_ids_by_date = partridge.read_service_ids_by_date(fullpath)
        service_ids = service_ids_by_date[datetime.date(2015,03,11)]
        feed = partridge.feed(fullpath, view={'trips.txt':{'service_id':service_ids}})

        # lets see the stop_times with the stop names
        gtfs_stop_times = pandas.merge(left=feed.stop_times,
                                       right=feed.stops[["stop_id","stop_name"]]).sort_values(by=["trip_id","stop_sequence"])
        Wrangler.WranglerLogger.debug("gtfs_stop_times.head()\n%s" % gtfs_stop_times.head())

        # first we need the number of stops because the last stop is the end of the line
        gtfs_trip_maxstops = gtfs_stop_times[["trip_id","stop_sequence"]].groupby("trip_id").max()
        gtfs_trip_maxstops = gtfs_trip_maxstops.reset_index().rename(columns={"stop_sequence":"num_stops"})
        Wrangler.WranglerLogger.debug("gtfs_trip_maxstops.head()\n%s" % gtfs_trip_maxstops.head())

        # calculate link (stop-to-stop) times by combining each stop with next stop to make a link
        gtfs_stop_a = pandas.merge(left=gtfs_stop_times, right=gtfs_trip_maxstops, how="left")
        gtfs_stop_a = gtfs_stop_a.loc[ gtfs_stop_a["stop_sequence"] != gtfs_stop_a["num_stops"]]
        gtfs_stop_a.loc[:, "linknum"] = gtfs_stop_a["stop_sequence"]
        gtfs_stop_b = gtfs_stop_times.loc[ gtfs_stop_times["stop_sequence"] != 1].copy()
        gtfs_stop_b.loc[:, "linknum"] = gtfs_stop_b["stop_sequence"] - 1

        gtfs_links = pandas.merge(left    = gtfs_stop_a,
                                  right   = gtfs_stop_b,
                                  how     = "left",
                                  on      = ["trip_id","linknum"],
                                  suffixes= ["_a","_b"] )
        # drop some useless cols -- note if there are dwells here then keep arrival_time_a
        gtfs_links.drop(["arrival_time_a","departure_time_b","num_stops", "stop_sequence_a","stop_sequence_b"], axis=1, inplace=True)
        # drop rows with NaN times
        bad_rows = gtfs_links.loc[ pandas.isnull(gtfs_links["departure_time_a"]) | (pandas.isnull(gtfs_links["arrival_time_b"])) ]
        Wrangler.WranglerLogger.warn("Dropping %d links with missing times:\n%s" % (len(bad_rows), str(bad_rows)))
        gtfs_links = gtfs_links.loc[ pandas.notnull(gtfs_links["departure_time_a"]) & (pandas.notnull(gtfs_links["arrival_time_b"])) ]

        # calculate linktime in minutes
        gtfs_links["linktime"] = (gtfs_links["arrival_time_b"] - gtfs_links["departure_time_a"])/60.0

        # for simplicity, average across all trips
        gtfs_link_times = gtfs_links[["stop_id_a","stop_name_a","stop_id_b","stop_name_b","linktime"]].groupby(["stop_id_a","stop_name_a","stop_id_b","stop_name_b"]).mean().reset_index()
        Wrangler.WranglerLogger.debug("gtfs_link_times\n%s" % gtfs_link_times.head())

        # add TM2 node ids for stop_id_a and stop_id_b, from NB or SB
        for link_end in ["a","b"]:
            gtfs_link_times["tm2_node_%s" % link_end] = None
            for gtfs_col in ["NB","SB"]:
                gtfs_link_times = pandas.merge(left    =gtfs_link_times,
                                               left_on ="stop_id_%s" % link_end,
                                               right   =operator_stop_labels.reset_index()[["TM2 Node","GTFS STOP ID %s" % gtfs_col]],
                                               right_on="GTFS STOP ID %s" % gtfs_col,
                                               how     ="left")
                gtfs_link_times.loc[ pandas.notnull(gtfs_link_times["TM2 Node"]), "tm2_node_%s" % link_end] = gtfs_link_times["TM2 Node"]
                gtfs_link_times.drop(["TM2 Node","GTFS STOP ID %s" % gtfs_col], axis=1, inplace=True)

        Wrangler.WranglerLogger.debug("gtfs_link_times\n%s" % gtfs_link_times.head())
        gtfs_link_times_dict = gtfs_link_times.set_index(["tm2_node_a","tm2_node_b"]).to_dict(orient="index")


        # process the lines for this operator in the TM2 network
        for line in trn_net:
            if line['USERA1'] == '"' + operator + '"':  # operator with quotes
                prev_stop_num  = -1
                prev_stop_name = None

                for node_idx in range(len(line.n)):

                    node_num = abs(int(line.n[node_idx].num))
                    node_name = None
                    if node_num in operator_stop_label_dict and "Station" in operator_stop_label_dict[node_num]:
                        node_name = operator_stop_label_dict[node_num]["Station"]
                    else:
                        Wrangler.WranglerLogger.warn("No node name/gtfs correspondence for node %d" % node_num)

                    # mark link times for stops
                    if line.n[node_idx].isStop():

                        # not first stop
                        if prev_stop_num >= 0:
                            # find the link time for prev_stop_num -> node_num
                            if (prev_stop_num, node_num) in gtfs_link_times_dict:
                                line.n[node_idx]["NNTIME"] = "%.2f" % gtfs_link_times_dict[(prev_stop_num, node_num)]["linktime"]
                            else:
                                Wrangler.WranglerLogger.warn("Line [%s]: Couldn't find link time for %d %20s -> %d %20s" %
                                                             (line.name, prev_stop_num, prev_stop_name,node_num, node_name))
                        # set for next stop
                        prev_stop_num  = node_num
                        prev_stop_name = node_name

                    # add the station name as a comment
                    if node_name:
                        line.n[node_idx].comment = "; " + node_name



    trn_net.write(path=".", name="transitLines", writeEmptyFiles=False, suppressValidation=True)