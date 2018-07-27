USAGE="""

Generic renumbering script, since there are a lot of these floating around.

For example:

  python renumber.py popsyn\households.csv popsyn\households_renum.csv 
    --input_col MAZ TAZ --renum_join_col N N --renum_out_col MAZSEQ TAZSEQ
    --output_rename_col ORIG_MAZ ORIG_TAZ --output_new_col MAZ TAZ

Note that the same number of input_col, renum_join_col, renum_out_col and output_col
must be specified, since each one is required for a complete mapping.

"""

import argparse,os,sys
import pandas

RENUMBER_DEFINITION_FILE_DEFAULT=os.path.join("hwy","mtc_final_network_zone_seq.csv")

if __name__ == '__main__':

    pandas.options.display.width = 300

    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("input_csv",  metavar="input.csv",   help="Input file to renumber")
    parser.add_argument("output_csv", metavar="output.csv",  help="Output file with renumbering")
    parser.add_argument("--renumber_key_csv", metavar="renumber_key.csv", default=RENUMBER_DEFINITION_FILE_DEFAULT,
        help="Renumber key csv.  If not specified, will use {}".format(RENUMBER_DEFINITION_FILE_DEFAULT))
    parser.add_argument("--input_col",         metavar="input_col",        required=True, nargs="+", help="Input column(s) to renumber")
    parser.add_argument("--renum_join_col",    metavar="renum_join_col",   required=True, nargs="+", help="Join column(s) in the renumber key")
    parser.add_argument("--renum_out_col",     metavar="renum_out_col",    required=True, nargs="+", help="Output column(s) in the renumber key")
    parser.add_argument("--output_rename_col", metavar="output_rename_col",required=True, nargs="+", help="Rename of the input column(s)")
    parser.add_argument("--output_new_col",    metavar="output_new_col",   required=True, nargs="+", help="Name of new column(s) in output file")
    args = parser.parse_args()

    if len(args.input_col) != len(args.renum_join_col):
        print("Mismatching number of input_col and renum_join_col")
        print(USAGE)
        sys.exit(2)
    if len(args.input_col) != len(args.renum_out_col):
        print("Mismatching number of input_col and renum_out_col")
        print(USAGE)
        sys.exit(2)

    if len(args.input_col) != len(args.output_rename_col):
        print("Mismatching number of input_col and output_rename_col")
        print(USAGE)
        sys.exit(2)

    if len(args.input_col) != len(args.output_new_col):
        print("Mismatching number of input_col and output_new_col")
        print(USAGE)
        sys.exit(2)

    print(args)

    renumber_df = pandas.read_csv(args.renumber_key_csv)
    print("Read {} lines from renumber key at {}".format(len(renumber_df), args.renumber_key_csv))
    print(renumber_df.head())

    data_df = pandas.read_csv(args.input_csv)
    input_length = len(data_df)  # save for later -- we should output the same number
    print("Read {} lines from input file at {}".format(len(data_df), args.input_csv))
    print(data_df.head())

    # do the mapping
    for arg_index in range(len(args.input_col)):
        # for readability
        input_col         = args.input_col[arg_index]
        renum_join_col    = args.renum_join_col[arg_index]
        renum_out_col     = args.renum_out_col[arg_index]
        output_rename_col = args.output_rename_col[arg_index]
        output_new_col    = args.output_new_col[arg_index]

        # pick the relevant mapping
        mapping_df = renumber_df[[renum_join_col, renum_out_col]].drop_duplicates()
        # todo: any checks on this?  expect single join col
        data_df = pandas.merge(left=data_df, right=mapping_df, 
            left_on=input_col, right_on=renum_join_col, how="left")
        print("Joined {}={}".format(input_col, renum_join_col))
        print(data_df.head())
        assert(len(data_df) == input_length)

        # drop the renum_join_col if it's named something different from the input_col since they're the same
        if input_col != renum_join_col:
            data_df.drop(columns=[renum_join_col], inplace=True)
            print(data_df.head())

        # do the rename; input_col => output_rename_col
        #                renum_out_col => output_new_col
        data_df.rename(columns={input_col:output_rename_col, renum_out_col:output_new_col}, inplace=True)
        print(data_df.head())

    # write it
    data_df.to_csv(args.output_csv, index=False)
    print("Wrote {} lines to output file at {}".format(len(data_df), args.output_csv))