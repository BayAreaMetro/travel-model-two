USAGE=r"""
 Usage: python build_walk_transfer_bypass_links.py pseudo_tap_nodes.csv pseudo_tap_links.csv

 This script does the following:

 1) Reads the transit nodes file (hwy/mtc_transit_network_node_xy.csv) and for nodes that are TAPs
    (e.g. have a TAPSEQ), a new pseudo TAP node is created starting at PSEUDO_TAP_START and with the
    same coordinates but offset by PSEUDO_TAP_{X,Y}_OFFSET.

 2) Reads the TAP-to-stop file (hwy/mtc_tap_to_stop_connectors.csv) and transforms TAP -> pseudo tap,
    calculating the Euclidean distance from the pseudo TAP to the stop.  Also appends the reverse
    of these links (stop to pseudo TAP) to the list.

 3) Reads the TAP-to-TAP file (skims/ped_distance_tap_tap-origN.csv).  Transforms TAP to TAP to be
    pseudo TAP to pseudo TAP.

  Outputs pseudo TAP node file, and link file containing:
    pseudo TAP to stops,
    stops to pseudo TAPs, and
    pseudo TAP to pseudo TAPs.

  Update:  sn  (11/2/2014): Added code to compute eucledian distances between pseudo-taps and stops
           lmz (3/10/2015): Consolidated multiple python scripts and use pandas.
"""

import os,sys
import numpy
import pandas

PSEUDO_TAP_START    = 901000
PSEUDO_TAP_X_OFFSET = 7.0
PSEUDO_TAP_Y_OFFSET = 7.0

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print USAGE
        sys.exit(2)

    pseudo_tap_nodes_outfile= sys.argv[1]
    pseudo_tap_links_outfile= sys.argv[2]

    transit_nodes_file      = os.path.join('hwy',   'mtc_transit_network_node_xy.csv')
    tap_to_stops_file       = os.path.join('hwy',   'mtc_tap_to_stop_connectors.csv')
    ped_tap_tap_file        = os.path.join('skims', 'ped_distance_tap_tap-origN.csv')

    # Read the transit nodes to start
    transit_nodes           = pandas.read_table(transit_nodes_file, names=['N','X','Y','TAPSEQ'], delimiter=',')
    taps                    = transit_nodes.loc[transit_nodes.TAPSEQ>0]

    # Create the pseudo taps - these are just all the TAP nodes + PSEUDO_TAP_START
    taps.is_copy            = False # quit your warnings
    taps.sort(columns='TAPSEQ', inplace=True)
    taps['PSEUDO_TAP_N']    = taps.TAPSEQ + PSEUDO_TAP_START
    taps['PSEUDO_TAP_X']    = taps.X      + PSEUDO_TAP_X_OFFSET
    taps['PSEUDO_TAP_Y']    = taps.Y      + PSEUDO_TAP_Y_OFFSET
    taps[['PSEUDO_TAP_N','PSEUDO_TAP_X','PSEUDO_TAP_Y']].to_csv(pseudo_tap_nodes_outfile, index=False)
    print "Wrote %d tap nodes" % taps.shape[0]

    print taps.head()

    # Convert the TAP to STOP nodes to PSEUDO TAP to STOP nodes
    tap_to_stops            = pandas.read_table(tap_to_stops_file, names=['A','B'], delimiter=',')
    # tap_to_stops.A_MOD      = tap_to_stops.A % 100000
    # print tap_to_stops.A_MOD.describe()
    # print tap_to_stops[tap_to_stops.B<1000000]

    tap_to_stops            = pandas.merge(left=tap_to_stops, right=taps, how='left',
                                           left_on='A', right_on='N')
    tap_to_stops            = tap_to_stops[['PSEUDO_TAP_N','PSEUDO_TAP_X','PSEUDO_TAP_Y','B']]

    # Get the STOP node coords
    tap_to_stops            = pandas.merge(left=tap_to_stops, right=transit_nodes, how='left',
                                          left_on='B', right_on='N')
    # Calculate the Euclidean distance
    tap_to_stops['FEET_SQ'] = (tap_to_stops.PSEUDO_TAP_X-tap_to_stops.X)*(tap_to_stops.PSEUDO_TAP_X-tap_to_stops.X) + \
                              (tap_to_stops.PSEUDO_TAP_Y-tap_to_stops.Y)*(tap_to_stops.PSEUDO_TAP_Y-tap_to_stops.Y)
    tap_to_stops['FEET']    = numpy.sqrt(tap_to_stops.FEET_SQ)

    # this is what we'll write out
    pseudo_tap_links        = tap_to_stops[['PSEUDO_TAP_N','B','FEET']]
    pseudo_tap_links.rename(columns={'PSEUDO_TAP_N':'A_N', 'B':'B_N'}, inplace=True)

    # reverse it and concatenate
    pseudo_tap_reverse      = pseudo_tap_links.copy()
    pseudo_tap_reverse.rename(columns={'A_N':'B_N', 'B_N':'C_N'}, inplace=True)
    pseudo_tap_reverse.rename(columns={'C_N':'A_N'}, inplace=True)
    pseudo_tap_links        = pseudo_tap_links.append(pseudo_tap_reverse).reset_index()
    pseudo_tap_links.sort(columns=["index","A_N"], inplace=True)

    # Read the TAP to TAP links
    ped_tap_tap_df          = pandas.DataFrame.from_csv(ped_tap_tap_file)
    ped_tap_tap_df.reset_index(inplace=True)

    # Make them Pseudo TAP to Pseudo TAP links
    ped_tap_tap_df          = pandas.merge(left=ped_tap_tap_df, right=taps, how='left',
                                           left_on='ORIG_TAP_N', right_on='N')
    ped_tap_tap_df          = ped_tap_tap_df[['PSEUDO_TAP_N','DEST_TAP_N','FEET']]
    ped_tap_tap_df.rename(columns={'PSEUDO_TAP_N':'A_N'}, inplace=True)
    ped_tap_tap_df          = pandas.merge(left=ped_tap_tap_df, right=taps, how='left',
                                           left_on='DEST_TAP_N', right_on='N')
    ped_tap_tap_df          = ped_tap_tap_df[['A_N','PSEUDO_TAP_N','FEET']]
    ped_tap_tap_df.rename(columns={'PSEUDO_TAP_N':'B_N'}, inplace=True)

    # Add them to our list
    pseudo_tap_links        = pseudo_tap_links.append(ped_tap_tap_df)

    # One more column
    pseudo_tap_links['CNTYPE'] = 'TRWALK'
    pseudo_tap_links = pseudo_tap_links[['A_N','B_N','CNTYPE','FEET']]

    # Write it
    pseudo_tap_links.to_csv(pseudo_tap_links_outfile, index=False)
    print "Wrote %d pseudo tap links" % pseudo_tap_links.shape[0]