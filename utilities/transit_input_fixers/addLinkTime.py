import Wrangler

USAGE = """

Skeleton script to update PT Transit Lines with link times.

"""


LOG_FILENAME = "addLinkTime_info.log"

TRN_NETFILE  = r"C:\\Users\\lzorn\\Box\\Modeling and Surveys\\Development\\Travel Model Two Development\\Model Inputs\\2015\\trn\\transit_lines"

if __name__ == '__main__':
    Wrangler.setupLogging(LOG_FILENAME, LOG_FILENAME.replace("info","debug"))

    trn_net = Wrangler.TransitNetwork(champVersion=4.3, basenetworkpath=TRN_NETFILE, isTiered=True, networkName="transitLines")

    for line in trn_net:
        if line['USERA1'] == '"Caltrain"':
            print line.name
            for node_idx in range(len(line.n)):
                line.n[node_idx].comment = "; node comment"  # this could be the station name to be human-readable
                line.n[node_idx]["TIME"] = 1.0


    trn_net.write(path=".", name="transitLines", writeEmptyFiles=False, suppressValidation=True)