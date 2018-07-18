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
    "Caltrain"                       : "GTFSTransitData_CT_2014.11.27.zip",
    "Angel Island - Tiburon Ferry"   : "GTFSTransitData_AT_2014.12.08.zip",
    "San Francisco MUNI"             : "GTFSTransitData_SF_2014.11.29.zip",
	"Vallejo Baylink Ferry"          : "GTFSTransitData_SB_2014.11.29.zip",
	"Blue and Gold"                  : "GTFSTransitData_BG_2014.11.27.zip",
	"Amtrak Capitol Cor. & Reg. Svc" : "GTFSTransitData_AM_2014.11.12.zip",
	"BART"                           : "GTFSTransitData_BA_2014.11.26.zip",
	"ACE"                            : "GTFSTransitData_CE_2014.11.27.zip",
	"Golden Gate Ferry"              : "GTFSTransitData_GF_2014.11.27.zip",
	"Alameda Harbor Bay Ferry"       : "GTFSTransitData_SB_2014.11.29.zip",
	"Alameda/Oakland Ferry"          : "GTFSTransitData_SB_2014.11.29.zip",
	"Vallejo Baylink Ferry"          : "GTFSTransitData_SB_2014.11.29.zip",
	"Santa Clara VTA"                : "GTFSTransitData_SC_2014.12.05.zip",
	"Blue and Gold"                  : "GTFSTransitData_BG_2014.11.27.zip"
}

if __name__ == '__main__':
    Wrangler.setupLogging(LOG_FILENAME, LOG_FILENAME.replace("info","debug"))
    pandas.options.display.width = 300
    pandas.options.display.max_rows = 1000

    # read the PT transit network line file
    trn_net = Wrangler.TransitNetwork(champVersion=4.3, basenetworkpath=TRN_NETFILE, isTiered=True, networkName="transitLines")

    # read the transit stop labels
    Wrangler.WranglerLogger.info("Reading transit stop labels from %s" % TRN_LABELFILE)
    trn_stop_labels = pandas.read_csv(TRN_LABELFILE, dtype={"GTFS stop_id NB/inbound":object, "GTFS stop_id SB/outbound":object})
    # keep only those with TM2 Node set - then we can make them ints
    trn_stop_labels = trn_stop_labels.loc[ pandas.notnull(trn_stop_labels["TM2 Node"]) ]
    trn_stop_labels["TM2 Node"] = trn_stop_labels["TM2 Node"].astype(int)

    for operator in ["Caltrain", "San Francisco MUNI","Vallejo Baylink Ferry", "Blue and Gold", "Amtrak Capitol Cor. & Reg. Svc", "BART",
	                 "ACE", "Golden Gate Ferry", "Alameda Harbor Bay Ferry","Alameda/Oakland Ferry","Vallejo Baylink Ferry", "Santa Clara VTA", "Blue and Gold"]:
        Wrangler.WranglerLogger.info("Processing operator %s" % operator)

        # get the stop labels for this operator
        operator_stop_labels = trn_stop_labels.loc[ trn_stop_labels["Operator"] == operator ]
        Wrangler.WranglerLogger.debug("operator_stop_labels.head()\n%s" % operator_stop_labels.head())
        operator_stop_label_dict = operator_stop_labels.set_index(["TM2 Node"]).to_dict(orient="index")

        # read GTFS
        fullpath = os.path.join(GTFS_DIR, GTFS_NETWORKS[operator])
        service_ids_by_date = partridge.read_service_ids_by_date(fullpath)
        service_ids = service_ids_by_date[datetime.date(2015,03,11)]
        feed = partridge.feed(fullpath, view={'trips.txt':{'service_id':service_ids}})

        # lets see the stop_times with the stop names
        gtfs_stop_times = pandas.merge(left=feed.stop_times,
                                       right=feed.stops[["stop_id","stop_name"]]).sort_values(by=["trip_id","stop_sequence"])
        # and the route_id and direction_id
        gtfs_stop_times = pandas.merge(left=gtfs_stop_times,
                                       right=feed.trips[["trip_id","route_id","direction_id"]], how="left")
        # and route_long_name and route_type
        gtfs_stop_times = pandas.merge(left=gtfs_stop_times,
                                       right=feed.routes[["route_id","route_long_name","route_type"]], how="left")
        # => filter out buses since the travel time comes from traffic
        gtfs_stop_times = gtfs_stop_times.loc[gtfs_stop_times.route_type != 3,:]

        # join TM2 node number from both the gtfs cols in the mapping
        for gtfs_col in ["GTFS stop_id NB/inbound","GTFS stop_id SB/outbound"]:
            gtfs_stop_times = pandas.merge(left    =gtfs_stop_times,
                                           right   =operator_stop_labels[["TM2 Node",gtfs_col]].rename(columns={gtfs_col:"stop_id"}),
                                           how     ="left",
                                           on      ="stop_id",
                                           suffixes=["_col1","_col2"])
        # two different tm2 rows is an error
        error_rows = gtfs_stop_times.loc[ pandas.notnull(gtfs_stop_times["TM2 Node_col1"])&
                                          pandas.notnull(gtfs_stop_times["TM2 Node_col2"])&
                                         (gtfs_stop_times["TM2 Node_col1"]!=gtfs_stop_times["TM2 Node_col2"])]
        if len(error_rows) > 0:
            Wrangler.WranglerLogger.warn("Multiple TM2 nodes for stops:\n%s" % error_rows)

        # consolidate tm2 nodes from joining on both gtfs cols
        gtfs_stop_times.rename(columns={"TM2 Node_col1":"tm2_node"}, inplace=True)
        gtfs_stop_times.loc[ pandas.isnull(gtfs_stop_times["tm2_node"]), "tm2_node"] = gtfs_stop_times["TM2 Node_col2"]
        gtfs_stop_times.drop(["TM2 Node_col2"], axis=1, inplace=True)

        # no TM2 nodes is an error
        error_rows = gtfs_stop_times.loc[ pandas.isnull(gtfs_stop_times["tm2_node"]) ]
        if len(error_rows) > 0:
            error_rows = error_rows[["route_type","route_id","route_long_name","direction_id","stop_id","stop_name","tm2_node"]].drop_duplicates()
            Wrangler.WranglerLogger.warn("Missing TM2 nodes for the following stops\n%s" % error_rows)

        # fill in and make int
        gtfs_stop_times.loc[ pandas.isnull(gtfs_stop_times.tm2_node), "tm2_node" ] = -1
        gtfs_stop_times["tm2_node"] = gtfs_stop_times["tm2_node"].astype(int)

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
                                  on      = ["route_type","route_id","route_long_name","direction_id","trip_id","linknum"],
                                  suffixes= ["_a","_b"] )
        # drop some useless cols -- note if there are dwells here then keep arrival_time_a
        gtfs_links.drop(["arrival_time_a","departure_time_b","num_stops","stop_sequence_b","stop_name_b"], axis=1, inplace=True)

        # some operators have time points only for specific stops
        # the goal is to build a dictionary for [tmnode1, tmnode2] => link time (in minutes) from tmnode1 to tmnode2
        # for these, we'll have [tmnode1, tmnode2, ... tmnodeX] => link time (in minutes) from tmnode1 to tmnodeX
        gtfs_links["stop_seq_a_withtime"] = gtfs_links["stop_sequence_a"]
        gtfs_links.loc[ pandas.isnull(gtfs_links["departure_time_a"]) , "stop_seq_a_withtime"] = None
        # fill stop_seq_a_withtime down for grouping
        gtfs_links["stop_seq_a_withtime"] = gtfs_links["stop_seq_a_withtime"].fillna(method="ffill")

        # Wrangler.WranglerLogger.info("\n%s" % gtfs_links.loc[gtfs_links.trip_id.isin(["6515333","6515334"])])
        #        trip_id  departure_time_a stop_id_a  stop_sequence_a                       stop_name_a route_id  direction_id       route_long_name  route_type  tm2_node_a  linknum  arrival_time_b stop_id_b  tm2_node_b  stop_seq_a_withtime
        # 53809  6515333           58620.0    115184                1               Jones St & Beach St        F             0  F-Market And Wharves           0     1032657        1             NaN    113092     1032774                  1.0
        # 53810  6515333               NaN    113092                2               Beach St & Mason St        F             0  F-Market And Wharves           0     1032774        2         58860.0    113095     1032585                  1.0
        # 53811  6515333           58860.0    113095                3            Beach St & Stockton St        F             0  F-Market And Wharves           0     1032585        3             NaN    114502     1032734                  3.0
        # 53812  6515333               NaN    114502                4          The Embarcadero & Bay St        F             0  F-Market And Wharves           0     1032734        4             NaN    114529     1032504                  3.0
        # 53813  6515333               NaN    114529                5      The Embarcadero & Sansome St        F             0  F-Market And Wharves           0     1032504        5             NaN    114516     1032469                  3.0
        # 53814  6515333               NaN    114516                6    The Embarcadero & Greenwich St        F             0  F-Market And Wharves           0     1032469        6             NaN    114518     1032571                  3.0
        # 53815  6515333               NaN    114518                7        The Embarcadero & Green St        F             0  F-Market And Wharves           0     1032571        7             NaN    114504     1032602                  3.0
        # 53816  6515333               NaN    114504                8        THE EMBARCADERO & BROADWAY        F             0  F-Market And Wharves           0     1032602        8             NaN    114534     1032581                  3.0
        # 53817  6515333               NaN    114534                9   The Embarcadero & Washington St        F             0  F-Market And Wharves           0     1032581        9             NaN    117283     1032769                  3.0
        # 53818  6515333               NaN    117283               10  The Embarcadero & Ferry Building        F             0  F-Market And Wharves           0     1032769       10         59580.0    114726     1032540                  3.0
        # 53819  6515333           59580.0    114726               11           Don Chee Way/Steuart St        F             0  F-Market And Wharves           0     1032540       11             NaN    115669     1032615                 11.0
        # 53820  6515333               NaN    115669               12              Market St & Drumm St        F             0  F-Market And Wharves           0     1032615       12         59880.0    115657     1032528                 11.0
        # 53821  6515333           59880.0    115657               13            Market St & Battery St        F             0  F-Market And Wharves           0     1032528       13             NaN    115639     1032535                 13.0
        # 53822  6515333               NaN    115639               14                Market St & 2nd St        F             0  F-Market And Wharves           0     1032535       14             NaN    115678     1032462                 13.0
        # 53823  6515333               NaN    115678               15             Market St & Kearny St        F             0  F-Market And Wharves           0     1032462       15         60180.0    115694     1032467                 13.0
        # 53824  6515333           60180.0    115694               16           Market St & Stockton St        F             0  F-Market And Wharves           0     1032467       16             NaN    115655     1032468                 16.0
        # 53825  6515333               NaN    115655               17               Market St & 5th  St        F             0  F-Market And Wharves           0     1032468       17             NaN    115695     1032547                 16.0
        # 53826  6515333               NaN    115695               18             Market St & Taylor St        F             0  F-Market And Wharves           0     1032547       18         60480.0    115656     1032704                 16.0
        # 53827  6515333           60480.0    115656               19                Market St & 7th St        F             0  F-Market And Wharves           0     1032704       19             NaN    115676     1032591                 19.0
        # 53828  6515333               NaN    115676               20               Market St & Hyde St        F             0  F-Market And Wharves           0     1032591       20             NaN    115680     1032674                 19.0
        # 53829  6515333               NaN    115680               21             Market St & Larkin St        F             0  F-Market And Wharves           0     1032674       21         60780.0    115696     1032639                 19.0
        # 53830  6515333           60780.0    115696               22          Market St & Van Ness Ave        F             0  F-Market And Wharves           0     1032639       22             NaN    115672     1032648                 22.0
        # 53831  6515333               NaN    115672               23              Market St & Gough St        F             0  F-Market And Wharves           0     1032648       23             NaN    115681     1032714                 22.0
        # 53832  6515333               NaN    115681               24             Market St & Laguna St        F             0  F-Market And Wharves           0     1032714       24             NaN    115659     1032643                 22.0
        # 53833  6515333               NaN    115659               25           Market St & Buchanan St        F             0  F-Market And Wharves           0     1032643       25         61200.0    115661     1032524                 22.0
        # 53834  6515333           61200.0    115661               26             Market St & Church St        F             0  F-Market And Wharves           0     1032524       26             NaN    115690     1032494                 26.0
        # 53835  6515333               NaN    115690               27            Market St & Sanchez St        F             0  F-Market And Wharves           0     1032494       27             NaN    115686     1032610                 26.0
        # 53836  6515333               NaN    115686               28                Market St & Noe St        F             0  F-Market And Wharves           0     1032610       28         61500.0    113311     1032507                 26.0
        # 53837  6515334           58980.0    115184                1               Jones St & Beach St        F             0  F-Market And Wharves           0     1032657        1             NaN    113092     1032774                  1.0
        # 53838  6515334               NaN    113092                2               Beach St & Mason St        F             0  F-Market And Wharves           0     1032774        2         59220.0    113095     1032585                  1.0
        # 53839  6515334           59220.0    113095                3            Beach St & Stockton St        F             0  F-Market And Wharves           0     1032585        3             NaN    114502     1032734                  3.0
        # 53840  6515334               NaN    114502                4          The Embarcadero & Bay St        F             0  F-Market And Wharves           0     1032734        4             NaN    114529     1032504                  3.0
        # 53841  6515334               NaN    114529                5      The Embarcadero & Sansome St        F             0  F-Market And Wharves           0     1032504        5             NaN    114516     1032469                  3.0
        # 53842  6515334               NaN    114516                6    The Embarcadero & Greenwich St        F             0  F-Market And Wharves           0     1032469        6             NaN    114518     1032571                  3.0
        # 53843  6515334               NaN    114518                7        The Embarcadero & Green St        F             0  F-Market And Wharves           0     1032571        7             NaN    114504     1032602                  3.0
        # 53844  6515334               NaN    114504                8        THE EMBARCADERO & BROADWAY        F             0  F-Market And Wharves           0     1032602        8             NaN    114534     1032581                  3.0
        # 53845  6515334               NaN    114534                9   The Embarcadero & Washington St        F             0  F-Market And Wharves           0     1032581        9             NaN    117283     1032769                  3.0
        # 53846  6515334               NaN    117283               10  The Embarcadero & Ferry Building        F             0  F-Market And Wharves           0     1032769       10         59940.0    114726     1032540                  3.0
        # 53847  6515334           59940.0    114726               11           Don Chee Way/Steuart St        F             0  F-Market And Wharves           0     1032540       11             NaN    115669     1032615                 11.0
        # 53848  6515334               NaN    115669               12              Market St & Drumm St        F             0  F-Market And Wharves           0     1032615       12         60240.0    115657     1032528                 11.0
        # 53849  6515334           60240.0    115657               13            Market St & Battery St        F             0  F-Market And Wharves           0     1032528       13             NaN    115639     1032535                 13.0
        # 53850  6515334               NaN    115639               14                Market St & 2nd St        F             0  F-Market And Wharves           0     1032535       14             NaN    115678     1032462                 13.0
        # 53851  6515334               NaN    115678               15             Market St & Kearny St        F             0  F-Market And Wharves           0     1032462       15         60540.0    115694     1032467                 13.0
        # 53852  6515334           60540.0    115694               16           Market St & Stockton St        F             0  F-Market And Wharves           0     1032467       16             NaN    115655     1032468                 16.0
        # 53853  6515334               NaN    115655               17               Market St & 5th  St        F             0  F-Market And Wharves           0     1032468       17             NaN    115695     1032547                 16.0
        # 53854  6515334               NaN    115695               18             Market St & Taylor St        F             0  F-Market And Wharves           0     1032547       18         60840.0    115656     1032704                 16.0
        # 53855  6515334           60840.0    115656               19                Market St & 7th St        F             0  F-Market And Wharves           0     1032704       19             NaN    115676     1032591                 19.0
        # 53856  6515334               NaN    115676               20               Market St & Hyde St        F             0  F-Market And Wharves           0     1032591       20             NaN    115680     1032674                 19.0
        # 53857  6515334               NaN    115680               21             Market St & Larkin St        F             0  F-Market And Wharves           0     1032674       21         61140.0    115696     1032639                 19.0
        # 53858  6515334           61140.0    115696               22          Market St & Van Ness Ave        F             0  F-Market And Wharves           0     1032639       22             NaN    115672     1032648                 22.0
        # 53859  6515334               NaN    115672               23              Market St & Gough St        F             0  F-Market And Wharves           0     1032648       23             NaN    115681     1032714                 22.0
        # 53860  6515334               NaN    115681               24             Market St & Laguna St        F             0  F-Market And Wharves           0     1032714       24             NaN    115659     1032643                 22.0
        # 53861  6515334               NaN    115659               25           Market St & Buchanan St        F             0  F-Market And Wharves           0     1032643       25         61560.0    115661     1032524                 22.0
        # 53862  6515334           61560.0    115661               26             Market St & Church St        F             0  F-Market And Wharves           0     1032524       26             NaN    115690     1032494                 26.0
        # 53863  6515334               NaN    115690               27            Market St & Sanchez St        F             0  F-Market And Wharves           0     1032494       27             NaN    115686     1032610                 26.0
        # 53864  6515334               NaN    115686               28                Market St & Noe St        F             0  F-Market And Wharves           0     1032610       28         61860.0    113311     1032507                 26.0

        # write this to look at
        debug_file = "gtfs_links_debug.csv"
        gtfs_links.to_csv(debug_file, index=False)
        Wrangler.WranglerLogger.info("Wrote %s for debugging" % debug_file)

        gtfs_links_ext = gtfs_links.groupby(["route_type","route_id","direction_id","trip_id","stop_seq_a_withtime"]).aggregate( \
                            {"stop_sequence_a"  :lambda x: tuple(x),
                             "stop_id_a"        :lambda x: tuple(x),
                             "tm2_node_a"       :lambda x: tuple(x),
                             "departure_time_a" :"first",
                             "arrival_time_b"   :"last",
                             "tm2_node_b"       :"last"}).reset_index(drop=False)
        gtfs_links_ext["linktime"] = (gtfs_links_ext["arrival_time_b"] - gtfs_links_ext["departure_time_a"])/60.0

        # add the end node to the tm2_node list
        def append_tuple(row):
            x_list = list(row["tm2_node_a"])
            x_list.append(row["tm2_node_b"])
            return tuple(x_list)

        print gtfs_links_ext.head()
        gtfs_links_ext["tm2_nodes"] = gtfs_links_ext.apply(append_tuple, axis=1)
        gtfs_links_ext.drop(["tm2_node_a","tm2_node_b"], axis=1, inplace=True)

        # Wrangler.WranglerLogger.info("\n%s" % gtfs_links_ext.loc[gtfs_links_ext.trip_id.isin(["6515333","6515334"])])
        #     route_type route_id       route_long_name  direction_id  trip_id  stop_seq_a_withtime                                          stop_id_a            stop_sequence_a  arrival_time_b  departure_time_a  linktime                                          tm2_nodes
        # 0            0        F  F-Market And Wharves             0  6515333                  1.0                                   (115184, 113092)                     (1, 2)         58860.0           58620.0       4.0                        (1032657, 1032774, 1032585)
        # 1            0        F  F-Market And Wharves             0  6515333                  3.0  (113095, 114502, 114529, 114516, 114518, 11450...  (3, 4, 5, 6, 7, 8, 9, 10)         59580.0           58860.0      12.0  (1032585, 1032734, 1032504, 1032469, 1032571, ...
        # 2            0        F  F-Market And Wharves             0  6515333                 11.0                                   (114726, 115669)                   (11, 12)         59880.0           59580.0       5.0                        (1032540, 1032615, 1032528)
        # 3            0        F  F-Market And Wharves             0  6515333                 13.0                           (115657, 115639, 115678)               (13, 14, 15)         60180.0           59880.0       5.0               (1032528, 1032535, 1032462, 1032467)
        # 4            0        F  F-Market And Wharves             0  6515333                 16.0                           (115694, 115655, 115695)               (16, 17, 18)         60480.0           60180.0       5.0               (1032467, 1032468, 1032547, 1032704)
        # 5            0        F  F-Market And Wharves             0  6515333                 19.0                           (115656, 115676, 115680)               (19, 20, 21)         60780.0           60480.0       5.0               (1032704, 1032591, 1032674, 1032639)
        # 6            0        F  F-Market And Wharves             0  6515333                 22.0                   (115696, 115672, 115681, 115659)           (22, 23, 24, 25)         61200.0           60780.0       7.0      (1032639, 1032648, 1032714, 1032643, 1032524)
        # 7            0        F  F-Market And Wharves             0  6515333                 26.0                           (115661, 115690, 115686)               (26, 27, 28)         61500.0           61200.0       5.0               (1032524, 1032494, 1032610, 1032507)
        # 8            0        F  F-Market And Wharves             0  6515334                  1.0                                   (115184, 113092)                     (1, 2)         59220.0           58980.0       4.0                        (1032657, 1032774, 1032585)
        # 9            0        F  F-Market And Wharves             0  6515334                  3.0  (113095, 114502, 114529, 114516, 114518, 11450...  (3, 4, 5, 6, 7, 8, 9, 10)         59940.0           59220.0      12.0  (1032585, 1032734, 1032504, 1032469, 1032571, ...
        # 10           0        F  F-Market And Wharves             0  6515334                 11.0                                   (114726, 115669)                   (11, 12)         60240.0           59940.0       5.0                        (1032540, 1032615, 1032528)
        # 11           0        F  F-Market And Wharves             0  6515334                 13.0                           (115657, 115639, 115678)               (13, 14, 15)         60540.0           60240.0       5.0               (1032528, 1032535, 1032462, 1032467)
        # 12           0        F  F-Market And Wharves             0  6515334                 16.0                           (115694, 115655, 115695)               (16, 17, 18)         60840.0           60540.0       5.0               (1032467, 1032468, 1032547, 1032704)
        # 13           0        F  F-Market And Wharves             0  6515334                 19.0                           (115656, 115676, 115680)               (19, 20, 21)         61140.0           60840.0       5.0               (1032704, 1032591, 1032674, 1032639)
        # 14           0        F  F-Market And Wharves             0  6515334                 22.0                   (115696, 115672, 115681, 115659)           (22, 23, 24, 25)         61560.0           61140.0       7.0      (1032639, 1032648, 1032714, 1032643, 1032524)
        # 15           0        F  F-Market And Wharves             0  6515334                 26.0                           (115661, 115690, 115686)               (26, 27, 28)         61860.0           61560.0       5.0               (1032524, 1032494, 1032610, 1032507)

        # now aggregate across trips and routes
        gtfs_link_times = gtfs_links_ext.groupby(["tm2_nodes"]).aggregate({"linktime":"mean"}).reset_index(drop=False)

        Wrangler.WranglerLogger.info("\n%s" % gtfs_link_times.head())
        Wrangler.WranglerLogger.info("\n%s" % gtfs_link_times.tail())

        # write this to look at
        debug_file = "gtfs_links_ext.csv"
        gtfs_links_ext.to_csv(debug_file, index=False)
        Wrangler.WranglerLogger.info("Wrote %s for debugging" % debug_file)

        gtfs_link_times_dict = gtfs_link_times.set_index(["tm2_nodes"]).to_dict(orient="index")
        # Wrangler.WranglerLogger.debug(gtfs_link_times_dict)

        # looks like  {(1032567, 1032555, 1032473): {'linktime': 4.678362573099415} ...}

        # process the lines for this operator in the TM2 network
        for line in trn_net:
            if line['USERA1'] == '"' + operator + '"':  # operator with quotes

                # Vallejo Baylink Ferry -- VB_200* is really a bus -- fix
                if line.name.startswith('VB_200'):
                    line['USERA2'] = '"Express bus"'
                    line['MODE']   = 93
                    continue

                # don't do local or express bus -- transit time is from traffic
                if line['USERA2'] in ['"Local bus"','"Express bus"']: continue

                Wrangler.WranglerLogger.debug("Processing operator [%s] of type [%s] line [%s]" % (line['USERA1'], line['USERA2'], line.name))
                stop_nums  = []
                stop_names = []

                for node_idx in range(len(line.n)):

                    node_num = abs(int(line.n[node_idx].num))
                    node_name = None
                    if node_num in operator_stop_label_dict and "Station" in operator_stop_label_dict[node_num]:
                        node_name = operator_stop_label_dict[node_num]["Station"]
                    else:
                        Wrangler.WranglerLogger.warn("No node name/gtfs correspondence for node %d" % node_num)

                    # mark link times for stops
                    if line.n[node_idx].isStop():

                        stop_nums.append(node_num)
                        if node_name: stop_names.append(node_name)

                        # not first stop
                        if len(stop_nums) >= 2:
                            # find the link time for stop sequence
                            if tuple(stop_nums) in gtfs_link_times_dict:
                                line.n[node_idx]["NNTIME"] = "%.2f" % gtfs_link_times_dict[tuple(stop_nums)]["linktime"]
                                # reset
                                stop_nums = []
                                stop_names = []
                                stop_nums.append(node_num)
                                if node_name: stop_names.append(node_name)

                            else:
                                pass


                    # add the station name as a comment
                    if node_name:
                        line.n[node_idx].comment = "; " + node_name

                if len(stop_nums) > 0:
                    Wrangler.WranglerLogger.warn("Line [%s]: Couldn't find link time for stops %s named %s" % (line.name, str(stop_nums), str(stop_names)))

    # trn_net.write(path=".", name="transitLines", writeEmptyFiles=False, suppressValidation=True)

    # code to output a transit input summary as a csv file
    #fileObj = open("transit_input_summary.txt", "w")
    #fileObj.write("Operator" + ", " + "Transit_mode" + ", " + "Line Name" + ", " + "Headway_EA" + ", " + "Headway_AM" + ", "  + "Headway_MD" + ", " + "Headway_PM" + ", "  + "Headway_EV" + ", "  "Vehicle Type" + "\n")
    #for line in trn_net:
    #        fileObj.write(line['USERA1']+ ", " + line['USERA2']+ ", " + line.name + ", " + line['HEADWAY[1]'] + ", " + line['HEADWAY[2]'] + ", " + line['HEADWAY[3]'] + ", " + line['HEADWAY[4]'] + ", " + line['HEADWAY[5]'] + ", " + line['VEHICLETYPE'] + "\n")
    #fileObj.close()

    df = pandas.DataFrame()
    for line in trn_net:
        df = df.append({'Operator': line['USERA1'], 'Transit_mode': line['USERA2'], 'Line_name': line.name, 'Headway_EA': line['HEADWAY[1]'], 'Headway_AM': line['HEADWAY[2]'], 'Headway_MD': line['HEADWAY[3]'], 'Headway_PM': line['HEADWAY[4]'], 'Headway_EV': line['HEADWAY[5]'], 'Vehicle_type': line['VEHICLETYPE']}, ignore_index=True)

    df = df.sort_values(by=['Operator', 'Transit_mode', 'Line_name'], ascending=[True, True, True])
    # print df
    df.to_csv('transit_input_summary.csv')
    df = df[['Operator','Transit_mode','Line_name','Headway_EA','Headway_AM','Headway_MD','Headway_PM','Headway_EV','Vehicle_type']]
    # print df



    df.to_csv('transit_input_summary.csv', index = False)
