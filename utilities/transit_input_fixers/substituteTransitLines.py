import argparse, datetime, os, re, sys
import Wrangler


USAGE = """

Substitute transit lines for an operator.

Writes out new line file as transitLines_[date_time].lin

"""
USERNAME     = os.environ["USERNAME"]
TM2_INPUTS   = os.path.join(r"C:\\Users", USERNAME, "Box\\Modeling and Surveys\\Development\\Travel Model Two Development\\Model Inputs")
TRN_NETFILE  = os.path.join(TM2_INPUTS,"2015_revised_mazs","trn")
LOG_FILENAME = "substitute_TransitLines_{}.log"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("del_regex", help="Regex for line names to delete")
    parser.add_argument("new_line_file", type=str, nargs="+", help="New line file(s) to incorporate")
    args = parser.parse_args()

    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M")

    log_filename = LOG_FILENAME.format(now_str)
    Wrangler.setupLogging(None, log_filename)

    # read the transit line file
    trn_net = Wrangler.TransitNetwork(modelType=Wrangler.Network.MODEL_TYPE_TM2, modelVersion=1.0,
                                      basenetworkpath=TRN_NETFILE, isTiered=True, networkName="transitLines")
    # remove the ones we want to remove
    del_re = re.compile(args.del_regex)
    keep_lines = []
    for trn_line in trn_net.lines:
        # keep comments
        if isinstance(trn_line, str):
            keep_lines.append(trn_line)
            continue

        if del_re.match(trn_line.name):
            Wrangler.WranglerLogger.info("  Removing line {}".format(trn_line))
        else:
            keep_lines.append(trn_line)
    trn_net.lines = keep_lines

    # add the new ones
    for new_line_file in args.new_line_file:
        new_line_realpath = os.path.realpath(new_line_file)
        Wrangler.WranglerLogger.info("Reading line file {}".format(new_line_realpath))

        path_file = os.path.split(new_line_realpath)
        file_ext  = os.path.splitext(path_file[1])

        # create empty files fares.far, fareMatrix.txt
        for empty_files in ["fares.far", "fareMatrix.txt"]:
            f = open(os.path.join(path_file[0], empty_files),"w")
            f.write("")
            f.close()

        new_net = Wrangler.TransitNetwork(modelType=Wrangler.Network.MODEL_TYPE_TM2, modelVersion=1.0,
                                          basenetworkpath=path_file[0], isTiered=True, networkName=file_ext[0])
        for new_net_line in new_net.lines:
            if isinstance(new_net_line, str): continue

            Wrangler.WranglerLogger.info("  Adding {}".format(new_net_line))
            trn_net.lines.append(new_net_line)

    # write it
    out_file = "transitLines_{}".format(now_str)
    trn_net.write(name=out_file, writeEmptyFiles=False, suppressQuery=False, suppressValidation=True)
    Wrangler.WranglerLogger.info("Wrote {}.lin".format(out_file))
