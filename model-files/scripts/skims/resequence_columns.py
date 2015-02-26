"""

USAGE: python resequence_columns.py skim_file_in.csv [skim_file_in2.csv ...] skim_file_out.csv

Reads skim_file_in.csv and replaces columns in the file based on the column names and
the mapping in hwy/mtc_final_network_zone_seq.csv

If multiple skim_file_in.csvs are specified, then joins them on their common fields first.

 - XXX_TAZ_N : maps N to TAZSEQ, new column is XXX_TAZ
 - XXX_MAZ_N : maps N to MAZSEQ, new column is XXX_MAZ
 - XXX_TAP_N : maps N to TAPSEQ, new column is XXX_TAP
 - XXX_EXT_N : maps N to EXTSEQ, new column is XXX_EXT

TODO: is there a need to go backwards?

"""
import datetime,sys,os
import numpy, pandas

if __name__ == '__main__':

    zone_seq_mapping_file   = os.path.join('hwy','mtc_final_network_zone_seq.csv')
    skim_infiles            = sys.argv[1:-1]
    skim_outfile            = sys.argv[-1]

    print "%s resequence_columns.py %s %s" % (datetime.datetime.now().strftime("%c"),
                                              str(skim_infiles), skim_outfile)

    sequence_mapping        = pandas.DataFrame.from_csv(zone_seq_mapping_file)
    sequence_mapping.reset_index(inplace=True)
    actions_performed       = 0

    # read the input skims, joining if necessary
    skim_df                 = None
    skim_df_init            = False
    for skim_infile in skim_infiles:
        my_skim_df          = pandas.io.parsers.read_csv(skim_infile, skip_blank_lines=True) # last line of skim is funny
        my_skim_df.reset_index(drop=True,inplace=True)

        if not skim_df_init:
            skim_df         = my_skim_df
            skim_df_init    = True
        else:
            prev_len        = skim_df.shape[0]
            assert(my_skim_df.shape[0] == prev_len)
            skim_df         = skim_df.merge(right=my_skim_df, how='inner')
            assert(   skim_df.shape[0] == prev_len)
            actions_performed += 1
    print "%s input skims read" % datetime.datetime.now().strftime("%c")

    # resequence
    new_colnames = []
    for colname in list(skim_df.columns.values):

        if len(colname) >= 6 and colname[-6:] in ['_TAZ_N','_MAZ_N','_TAP_N','_EXT_N']:
            new_colname = colname[:-2]           # e.g. XXX_TAZ
            seq_colname = colname[-5:-2]+'SEQ'   # e.g. TAZSEQ
            seq_df      = sequence_mapping.loc[:,['N',seq_colname]]
            seq_df.rename(columns={'N':colname, seq_colname:new_colname}, inplace=True)
            skim_df     = pandas.merge(left=skim_df, right=seq_df, how='left')
            new_colnames.append(new_colname)
            actions_performed += 1
        else:
            new_colnames.append(colname)

    skim_df = skim_df[new_colnames]

    # verify we did *something*
    if actions_performed == 0:
        print "No actions performed -- something must be wrong"
        sys.exit(2)

    # verify no joins failed
    for colname in new_colnames:
        if sum(skim_df[colname].isnull()) > 0:
            print "There are %d instances of null %s." % (sum(skim_df[colname].isnull()), colname)
            sys.exit(2)

    skim_df.to_csv(skim_outfile, index=False)
    print "%s done with %d actions performed" % (datetime.datetime.now().strftime("%c"), actions_performed)
