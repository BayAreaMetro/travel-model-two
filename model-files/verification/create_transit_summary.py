USAGE = """
Read transit assignment link output by time period and creates a few summaries.

  1) trn_boards_all_timeperiods.csv is really the raw assignment link output but
     all time periods consolidated into one file columns:
     A, B, MODE, OPERATOR, NAME, LONGNAME, LINKSEQ,
     DIST_EA, TIME_EA, HEADWAY_1_EA, VOL_EA, ONA_EA, OFFB_EA,
     DIST_AM, TIME_AM, HEADWAY_2_AM, VOL_AM, ONA_AM, OFFB_AM,
     DIST_MD, TIME_MD, HEADWAY_2_MD, VOL_MD, ONA_MD, OFFB_MD,
     DIST_PM, TIME_PM, HEADWAY_2_PM, VOL_PM, ONA_PM, OFFB_PM,
     DIST_EV, TIME_EV, HEADWAY_2_EV, VOL_EV, ONA_EV, OFFB_EV

  2) trn_boards_lines.csv is the links aggregated to lines.  columns:
     MODE, OPERATOR, NAME, LONGNAME,
     DIST_EA, TIME_EA, HEADWAY_1_EA, VOL_EA, ONA_EA, OFFB_EA,
     DIST_AM, TIME_AM, HEADWAY_2_AM, VOL_AM, ONA_AM, OFFB_AM,
     DIST_MD, TIME_MD, HEADWAY_2_MD, VOL_MD, ONA_MD, OFFB_MD,
     DIST_PM, TIME_PM, HEADWAY_2_PM, VOL_PM, ONA_PM, OFFB_PM,
     DIST_EV, TIME_EV, HEADWAY_2_EV, VOL_EV, ONA_EV, OFFB_EV

  3) trn_boards_modes.csv is the lines aggregated to modes.  columns:
     OPERATOR, MODE,
     DIST_EA, TIME_EA, ONA_EA, OFFB_EA, VOL_EA,
     DIST_AM, TIME_AM, ONA_AM, OFFB_AM, VOL_AM,
     DIST_MD, TIME_MD, ONA_MD, OFFB_MD, VOL_MD,
     DIST_PM, TIME_PM, ONA_PM, OFFB_PM, VOL_PM,
     DIST_EV, TIME_EV, ONA_EV, OFFB_EV, VOL_EV

"""

import argparse,collections,os,sys
import simpledbf
import numpy,pandas
import re

TIME_PERIODS = collections.OrderedDict([ # time period to duration
    ("EA", 3.0),
    ("AM", 4.0),
    ("MD", 5.0),
    ("PM", 4.0),
    ("EV", 8.0)])
KEY_COLS     = ["A","B","LINKSEQ","MODE","OPERATOR","NAME","LONGNAME"]
RAW_OUTFILE  = "trn_boards_all_timeperiods.csv"
LINE_OUTFILE = "trn_boards_lines.csv"
MODE_OUTIFLE = "trn_boards_modes.csv"
ROUTE_OUTFILE = "trn_boards_routes.csv"

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("trn_dir", help="Location of transit assignment files (trn_link_onoffs_[EA,AM,MD,PM,EV].dbf")
    parser.add_argument("--byclass",  action="store_true", help="Include user class outputs (VOL, ONA, OFFB)")
    args = parser.parse_args()

    all_linko_df = pandas.DataFrame()
    for time_period in TIME_PERIODS.keys():
#   for testing:
#    for time_period in ['EA']:

        linko_file = os.path.join(args.trn_dir, "trn_link_onoffs_{}.dbf".format(time_period))
        linko_dbf  = simpledbf.Dbf5(linko_file)
        linko_df   = linko_dbf.to_dataframe()

        print("Read {} lines from {}".format(len(linko_df), linko_file))

        # for now, we want boardings so
        # filter down to just transit links (no access/egress)
        linko_df = linko_df.loc[ linko_df.MODE < 900 ]
        # and those with positive ONA
        linko_df = linko_df.loc[ linko_df.ONA > 0 ]
        print("Filtered to {} transit links with boardings".format(len(linko_df)))

        # drop columns starting with REV
        colnames = list(linko_df.columns)
        rev_colnames = [colname for colname in colnames if colname[:4]=="REV_"]
        linko_df.drop(labels=rev_colnames, axis="columns", inplace=True)
        # as well as OFFA and ONB since ONA and OFFB are sufficient
        offa_onb_colnames = [colname for colname in colnames if colname[:4]=="OFFA" or colname[:3]=="ONB"]
        linko_df.drop(labels=offa_onb_colnames, axis="columns", inplace=True)
        # and STOPA, STOPB since neither are useful right now
        linko_df.drop(labels=["STOPA","STOPB"], axis="columns", inplace=True)

        # drop userclass
        if not args.byclass:
            class_colnames = ["VOL_1","ONA_1","OFFB_1",
                              "VOL_2","ONA_2","OFFB_2",
                              "VOL_3","ONA_3","OFFB_3"]
            linko_df.drop(labels=class_colnames, axis="columns", inplace=True)

        # rename columns that aren't key columns
        colnames = list(linko_df.columns)
        rename_cols = {}
        for colname in colnames:
            if colname in KEY_COLS: continue
            rename_cols[colname] = "{}_{}".format(colname, time_period)
        linko_df.rename(columns=rename_cols, inplace=True)

        # join together
        if len(all_linko_df) == 0:
            all_linko_df = linko_df
        else:
            all_linko_df = pandas.merge(left=all_linko_df, right=linko_df, how="outer")
            print("Joined to linko for all timeperiods: {} rows".format(len(all_linko_df)))

#    line_group_pattern = re.compile(r"([A-Z0-9]+_[A-Z0-9]+)")
    line_group_pattern = re.compile('[a-z]$')

    #create a new column called name_set
#    repl = lambda m: m.group(1)
    all_linko_df["NAME_SET"]=all_linko_df["NAME"].str.replace(line_group_pattern, '')

    # write the raw boardings
    outfilepath = os.path.join(args.trn_dir, RAW_OUTFILE)
    all_linko_df.to_csv(outfilepath, header=True, index=False)
    print("Wrote {} links to {}".format(len(all_linko_df), outfilepath))
    print(all_linko_df.head())

    aggregate_dict = collections.OrderedDict()
    for time_period in TIME_PERIODS.keys():
    # construct aggregation rows
        aggregate_dict["DIST_{}".format(time_period)] = 'first'
        aggregate_dict["TIME_{}".format(time_period)] = 'max'
        aggregate_dict["OFFB_{}".format(time_period)] = 'sum'
        aggregate_dict["ONA_{}".format(time_period)] = 'sum'
        aggregate_dict["VOL_{}".format(time_period)] = 'sum'

    # save a new data frame and drop a few columns
    nameset_linko_df = all_linko_df.drop(labels=["LINKSEQ", "NAME", "LONGNAME", "HEADWAY_1_EA"], axis="columns")

    # do the aggregation
    nameset_linko_df = nameset_linko_df.groupby(by=["A", "B", "MODE","OPERATOR","NAME_SET"]).agg(aggregate_dict).reset_index(drop=False)
    nameset_linko_df["ROUTE_A_B"]=nameset_linko_df["NAME_SET"].astype(str)+" "+nameset_linko_df["A"].astype(str)+"_"+nameset_linko_df["B"].astype(str)

    # write out the name set level link volumes
    outfilepath = os.path.join(args.trn_dir, ROUTE_OUTFILE)
    nameset_linko_df.to_csv(outfilepath, header=True, index=False)
    print("Wrote {} links to {}".format(len(nameset_linko_df), outfilepath))

    # write a line summary
    # todo: HEADWAY isn't additive
    all_linko_df.drop(labels=["A","B","LINKSEQ"], axis="columns", inplace=True)
    aggregate_dict = collections.OrderedDict()
    tp_num         = 0
    for time_period in TIME_PERIODS.keys():
        tp_num += 1
        # additive
        aggregate_dict["DIST_{}".format(time_period)] = 'sum'
        aggregate_dict["TIME_{}".format(time_period)] = 'sum'
        aggregate_dict[ "ONA_{}".format(time_period)] = 'sum'
        aggregate_dict["OFFB_{}".format(time_period)] = 'sum'
        # max
        aggregate_dict["HEADWAY_{}_{}".format(tp_num, time_period)] = 'max'
        aggregate_dict[       "VOL_{}".format(time_period)]         = 'max'
        if args.byclass:
            for setnum in [1,2,3]:
                aggregate_dict[ "ONA_{}_{}".format(setnum,time_period)] = 'sum'
                aggregate_dict["OFFB_{}_{}".format(setnum,time_period)] = 'sum'
                aggregate_dict[ "VOL_{}_{}".format(setnum,time_period)] = 'max'


    all_linko_df = all_linko_df.groupby(by=["MODE","OPERATOR","NAME","NAME_SET","LONGNAME"]).agg(aggregate_dict).reset_index(drop=False)
    # reorder columns
    all_linko_df = all_linko_df[["OPERATOR","MODE","NAME", "NAME_SET", "LONGNAME"] + aggregate_dict.keys()]
    outfilepath = os.path.join(args.trn_dir, LINE_OUTFILE)
    all_linko_df.to_csv(outfilepath, header=True, index=False)
    print("Wrote {} lines to {}".format(len(all_linko_df), outfilepath))

    # write a mode summary -- drop headways since they don't combine
    all_linko_df.drop(labels=["NAME","NAME_SET","LONGNAME","HEADWAY_1_EA","HEADWAY_2_AM",
                              "HEADWAY_3_MD","HEADWAY_4_PM","HEADWAY_5_EV"], axis="columns", inplace=True)
    all_linko_df = all_linko_df.groupby(by=["MODE","OPERATOR"]).agg(numpy.sum).reset_index(drop=False)
    # reorder columns
    del aggregate_dict["HEADWAY_1_EA"]
    del aggregate_dict["HEADWAY_2_AM"]
    del aggregate_dict["HEADWAY_3_MD"]
    del aggregate_dict["HEADWAY_4_PM"]
    del aggregate_dict["HEADWAY_5_EV"]
    all_linko_df = all_linko_df[["OPERATOR","MODE"] + aggregate_dict.keys()]
    outfilepath = os.path.join(args.trn_dir, MODE_OUTIFLE)
    all_linko_df.to_csv(outfilepath, header=True, index=False)
    print("Wrote {} modes to {}".format(len(all_linko_df), outfilepath))
