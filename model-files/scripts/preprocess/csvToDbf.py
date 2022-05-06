USAGE="""

Quick script to convert csv to dbf file since Cube is unfriendly about csvs.

Goes through file twice, the first time to figure out types.

Try assuming ints, then floats, then strings.

"""
import dbfpy3
import argparse,collections,csv,os,sys

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("input_csv",  metavar="input.csv",   help="Input csv file to convert")
    parser.add_argument("output_dbf", metavar="output.dbf",  help="Output dbf file")

    args = parser.parse_args()

    csvfile   = open(args.input_csv)
    csvreader = csv.reader(csvfile)
    columns   = collections.OrderedDict()  # colname => [dbf_colname, "C", len1, len2]
    col_list  = []
    for row in csvreader:
        # header row
        if len(columns) == 0:
            col_list = row
            for colname in row:
                dbf_colname = colname[:10]
                # make it upper case
                dbf_colname = dbf_colname.upper()
                if len(colname) > 10: print("Truncating column {} to {}", colname, dbf_colname)
                columns[colname] = [dbf_colname, "N", 10] # try int first
            continue

        # subsequent rows
        for col_idx in range(len(row)):
            colname = col_list[col_idx]
            dbf_colname = columns[colname][0]

            # do we think it's an int?  try it
            if columns[colname][1] == "N" and len(columns[colname])==3:
                try:
                    val_int = int(row[col_idx])
                except:
                    # upgrade to float
                    columns[colname].append(5)

            # do we think it's a float? try it
            if columns[colname][1] == "N" and len(columns[colname])==4:
                try:
                    val_float = float(row[col_idx])
                except:
                    # upgrade to string
                    columns[colname] = [dbf_colname, "C", 1]

            # do we think it's a string? make sure it's long enough
            if columns[colname][1] == "C":
                columns[colname][2] = max(columns[colname][2], len(row[col_idx])+2)
    csvfile.close()
    print("Read {} and determined dbf columns".format(args.input_csv))

    # create the dbf
    new_dbf = dbfpy3.dbf.Dbf(args.output_dbf, new=True)

    for col in columns.keys():
        # print("{} : {}".format(col, columns[col]))
        # dbfpy3 wants type_code, name, length
        new_dbf.add_field( (columns[col][1], columns[col][0], columns[col][2]) )

    csvfile   = open(args.input_csv)
    csvreader = csv.reader(csvfile)
    header    = False
    for row in csvreader:
        # skip header
        if not header:
            header = True
            continue

        rec = new_dbf.new()
        for col_idx in range(len(row)):
            colname = col_list[col_idx]
            dbf_colname = columns[colname][0]
            print(dbf_colname)
            if columns[colname][1] == "N" and len(columns[colname]) == 3:
                rec[ dbf_colname ] = int(row[col_idx])
            elif columns[colname][1] == "N":
                rec[ dbf_colname] = float(row[col_idx])
            else:
                rec[ dbf_colname ] = row[col_idx]
        new_dbf.write(rec)

    csvfile.close()
    print(new_dbf)
    new_dbf.close()

    print("Wrote {}".format(args.output_dbf))
