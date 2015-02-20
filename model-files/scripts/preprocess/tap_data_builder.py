"""
  Usage: python tap_data_builder.py base_dir 

  This script builds the tap csv data file which maps all TAPs to the closest TAZ for that TAP.

  Input:

      base_dir argument - the directory in which the model runs (directory with INPUTS, hwy, etc.)

      base_dir\hwy\mtc_final_network_zone_seq.csv - the file holding the correspondence
        between network zone numbers and CTRAMP sequential numbering

      base_dir\hwy\tap_to_taz_for_parking.txt - the file holding the walk distance
        shortest path tree from taps to tazs
      
  Output: 

      base_dir\hwy\tap_data.csv with the following columns
        TAP - the tap number (in CTRAMP sequential numbering)
        TAP_original - the original tap number (in the CUBE network)
        lotid - the lot id; this is the same as tap
        TAP - the taz the tap is associated with (see tap_to_taz_for_parking.job)
        capacity - the capacity of the lot; this is set to 9999 by default, but could be changed after 
                   this process has run
  
  crf 11/2013

"""

import os,sys
import pandas

if __name__ == '__main__':
    base_dir                = sys.argv[1]
    zone_seq_mapping_file   = os.path.join(base_dir,'hwy',      'mtc_final_network_zone_seq.csv')
    infile                  = os.path.join(base_dir,'hwy',      'tap_to_taz_for_parking.txt')
    outfile                 = os.path.join(base_dir,'hwy',      'tap_data.csv')

    sequence_mapping        = pandas.DataFrame.from_csv(zone_seq_mapping_file)
    sequence_mapping.reset_index(inplace=True)

    tap_data                = pandas.read_table(infile, names=['TAP_original','TAZ_original','TAZ2','SP_DISTANCE','FEET'],
                                                delimiter=',')
    tap_data_grouped        = tap_data.groupby('TAP_original')

    tap_data_out_init       = False
    tap_data_out            = None
    taps                    = sequence_mapping[sequence_mapping.TAPSEQ > 0]
    for ind,row in taps.iterrows():
        try:
            sorted_group = tap_data_grouped.get_group(row['N']).sort(['FEET','TAZ_original'])
            if tap_data_out_init:
                tap_data_out = tap_data_out.append(sorted_group.head(1))
            else:
                tap_data_out = sorted_group.head(1)
                tap_data_out_init = True

        except KeyError:
            print 'tap %8d not captured in tap->taz (for parking) script' % row['N']
            # use the last one -- does this make sense?
            use_this = tap_data_out.tail(1).copy()
            use_this.loc[:,'TAP_original'] = row['N']
            tap_data_out = tap_data_out.append(use_this)

    tap_data_out.reset_index(inplace=True)

    # join to get the real TAZ
    tap_data_out = pandas.merge(left=sequence_mapping[['N','TAZSEQ']], right=tap_data_out, how='right',
                                left_on='N', right_on='TAZ_original')    # rename sequence column
    tap_data_out.rename(columns={'TAZSEQ':'TAZ', 'N':'dropN1'}, inplace=True)

    # join to get the real TAP
    tap_data_out = pandas.merge(left=sequence_mapping[['N','TAPSEQ']], right=tap_data_out, how='right',
                                left_on='N', right_on='TAP_original')
    tap_data_out.rename(columns={'TAPSEQ':'TAP', 'N':'dropN2'}, inplace=True)

    # drop others
    tap_data_out.drop(['index','FEET','SP_DISTANCE','TAZ_original','TAZ2','dropN1','dropN2'], axis=1, inplace=True)

    # are these really useful??
    tap_data_out['lotid']       = tap_data_out['TAP']
    tap_data_out['capacity']    = 9999

    # reorder and write
    tap_data_out = tap_data_out[['TAP','TAP_original','lotid','TAZ','capacity']]
    tap_data_out.to_csv(outfile, index=False)
    print "Wrote %s" % outfile
