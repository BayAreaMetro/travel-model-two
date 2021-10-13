# Calculate upstream and downstream interchange distance

# Interchange nodes are labeled in Cube script
# This script looks through links to determine shortest paths to interchanges
# from SANDAG ABM: import_network.py

import heapq as _heapq
import csv
import os
import pandas as pd
import argparse

def csvImport(csvfile):
    # read from CSV
    df = pd.read_csv(csvfile, sep=',',dtype={'A': int,'B': int,'FT': int,'DISTANCE': float,'INTXNODE': str,'INTXLOC': str})
    return df

def csvExport(df,csvfile):
    # write data back to CSV
    df.to_csv(csvfile, index=False)

def interchange_distance(orig_link, direction):
    visited = set([])
    visited_add = visited.add
    back_links = {}
    heap = []
    if direction == "DOWNSTREAM":
        #get_links = lambda l: l.j_node.outgoing_links()
        #get_links = lambda l: links.loc[(links.A == l.B) | ((links.B == l.B) & (links.A != l.A))]
        # Adds link distances until reaching a node tagged BEFORE/AFTER interchange.
        # These are currently set for all freeway ramps by locating nodes where incoming links != outgoing links
        # TODO update nodes to only tag major interchanges
        get_links = lambda l: links.loc[(links.A == l.B)]
        check_far_node = lambda l: True if l.INTXB == "BEFORE" or l.INTXB == "AFTER" else False
    elif direction == "UPSTREAM":
        #get_links = lambda l: l.i_node.incoming_links()
        #get_links = lambda l: links.loc[((links.A == l.A) & (links.B != l.B)) | (links.B == l.A)]
        # TODO update nodes to only tag major interchanges
        get_links = lambda l: links.loc[(links.B == l.A)]
        check_far_node = lambda l: True if l.INTXA == "BEFORE" or l.INTXA == "AFTER" else False
    # Shortest path search for nearest interchange node along freeway
    for link in get_links(orig_link).itertuples():
        _heapq.heappush(heap, (link.DISTANCE, link))
    interchange_found = False
    try:
        while not interchange_found:
            link_cost, link = _heapq.heappop(heap)
            if link in visited:
                continue
            visited_add(link)
            #pdb.set_trace()
            if check_far_node(link):
                interchange_found = True
                break
            for next_link in get_links(link).itertuples():
                if next_link in visited:
                    continue
                next_cost = link_cost + link.DISTANCE
                _heapq.heappush(heap, (next_cost, next_link))
    except IndexError:
        # IndexError if heap is empty
        # case where start / end of highway, dist = 99
        return 99
    return (orig_link.DISTANCE / 2.0) + link_cost

parser = argparse.ArgumentParser(description="Find nearest freeway interchanges", formatter_class=argparse.RawDescriptionHelpFormatter,)
parser.add_argument("input_csv",  metavar="input.csv",   help="Input csv link table")
parser.add_argument("output_csv", metavar="output.csv",  help="Output csv file")

args = parser.parse_args()

links = csvImport(args.input_csv)
links["downdist"] = None
links["updist"] = None

for i, link in links.iterrows():
    links.at[i,"downdist"] = interchange_distance(link, "DOWNSTREAM")
    links.at[i,"updist"] = interchange_distance(link, "UPSTREAM")

csvExport(links,args.output_csv)
