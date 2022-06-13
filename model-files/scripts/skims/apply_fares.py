#///////////////////////////////////////////////////////////////////////////////
#////                                                                        ///
#//// Copyright INRO, 2020.                                                  ///
#//// Rights to use and modify are granted to the                            ///
#//// Metropolitan Transportation Commission (MTC)                           ///
#//// and partner agencies.                                                  ///
#//// This copyright notice must be preserved.                               ///
#////                                                                        ///
#//// apply_fares.py                                                         ///
#////                                                                        ///
#////     Usage:                                                             ///
#////                                                                        ///
#////                                                                        ///
#////                                                                        ///
#////                                                                        ///
#///////////////////////////////////////////////////////////////////////////////

import inro.modeller as _m
import inro.emme.database.emmebank as _eb
import inro.emme.core.services as _services

import shapely.geometry as _geom
import numpy as _np

try:
    from scipy.optimize import nnls as _nnls
except ImportError:
    print("scipy not installed, cannot estimate station-to-station fares")

import time as _time
import os as _os
import argparse as _argparse
import traceback as _traceback
import json as _json

from collections import defaultdict as _defaultdict
from copy import deepcopy as _copy

_join, _dir = _os.path.join, _os.path.dirname
_INF = 1e400
MAX_TRANSFER_DISTANCE = 15000  # feet
_local_modes = ['b']
_premium_modes = ['x', 'f', 'l', 'h', 'r']


class ApplyFares(object):

    def __init__(self):
        self.scenario = None
        self.period = ""
        self.dot_far_file = None
        self.fare_matrix_file = None
        self.vot = None
        self.network = None

    def execute(self):
        self._log = []
        faresystems = self.parse_dot_far_file()
        fare_matrices = self.parse_fare_matrix_file()

        try:
            network = self.network = self.scenario.get_network()
            self.create_attribute("TRANSIT_SEGMENT", "@board_cost", self.scenario, network)
            self.create_attribute("TRANSIT_SEGMENT", "@invehicle_cost", self.scenario, network)
            # identify the lines by faresystem
            for line in network.transit_lines():
                fs_id = int(line["@faresystem"])
                try:
                    fs_data = faresystems[fs_id]
                except KeyError:
                    self._log.append({
                        "type": "text", 
                        "content": ("Line {} has @faresystem '{}' which was "
                                    "not found in fares.far table").format(line.id, fs_id)})
                    continue
                fs_data["LINES"].append(line)
                fs_data["NUM LINES"] += 1
                fs_data["NUM SEGMENTS"] += len(list(line.segments()))
                # Set final hidden segment allow_boardings to False so that the boarding cost is not 
                # calculated for this segment (has no next segment)
                line.segment(-1).allow_boardings = False

            self._log.append({"type": "header", "content": "Base fares by faresystem"})
            for (fs_id, fs_data) in faresystems.items():
                self._log.append(
                    {"type": "text", "content": "FAREZONE {}: {} {}".format(fs_id, fs_data["STRUCTURE"], fs_data["NAME"])})
                lines = fs_data["LINES"]
                fs_data["MODE_SET"] = set(l.mode.id for l in lines)
                fs_data["MODES"] = ", ".join(fs_data["MODE_SET"])
                if fs_data["NUM LINES"] == 0:
                    self._log.append(
                        {"type": "text2", "content": "No lines associated with this faresystem"})
                elif fs_data["STRUCTURE"] == "FLAT":
                    self.generate_base_board(lines, fs_data["IBOARDFARE"])
                elif fs_data["STRUCTURE"] == "FROMTO":
                    fare_matrix = fare_matrices[fs_data["FAREMATRIX ID"]]
                    self.generate_fromto_approx(network, lines, fare_matrix, fs_data)

            self.faresystem_distances(faresystems, network)
            faresystem_groups = self.group_faresystems(faresystems, network)
            journey_levels, mode_map = self.generate_transfer_fares(
                faresystems, faresystem_groups, network)
            self.save_journey_levels("ALLPEN", journey_levels)
            local_modes = []
            for mode in _local_modes:
                local_modes.extend(mode_map[mode])
            local_levels = self.filter_journey_levels_by_mode(local_modes, journey_levels)
            self.save_journey_levels("BUS", local_levels)
            premium_modes = []
            for mode in _premium_modes:
                premium_modes.extend(mode_map[mode])
            premium_levels = self.filter_journey_levels_by_mode(premium_modes, journey_levels)
            self.save_journey_levels("PREM", premium_levels)

        except Exception as error:
            self._log.append({"type": "text", "content": "error during apply fares"})
            self._log.append({"type": "text", "content": str(error)})
            self._log.append({"type": "text", "content": _traceback.format_exc()})
            raise
        finally:
            log_content = []
            header = ["NUMBER", "NAME", "NUM LINES", "NUM SEGMENTS", "MODES", "FAREMATRIX ID", 
                      "NUM ZONES", "NUM MATRIX RECORDS"]
            for (fs_id, fs_data) in faresystems.items():
                log_content.append([str(fs_data.get(h, "")) for h in header])
            self._log.insert(0, {
                "content": log_content,
                "type": "table",
                "header": header,
                "title": "Faresystem data"
            })

            self.log_report()
            self.log_text_report()

        self.scenario.publish_network(network)

        return journey_levels

    def parse_dot_far_file(self):
        data = {}
        numbers = []
        with open(self.dot_far_file, 'r') as f:
            for line in f:
                fs_data = {}
                word = []
                key = None
                for c in line:
                    if key == "FAREFROMFS":
                        word.append(c)
                    elif c == "=":
                        key = "".join(word)
                        word = []
                    elif c == ",":
                        fs_data[key.strip()] = "".join(word)
                        key = None
                        word = []
                    elif c == "\n":
                        pass
                    else:
                        word.append(c)
                fs_data[key.strip()] = "".join(word)

                fs_data["NUMBER"] = int(fs_data["FARESYSTEM NUMBER"])
                if fs_data["STRUCTURE"] != "FREE":
                    fs_data["FAREFROMFS"] = [float(x) for x in fs_data["FAREFROMFS"].split(",")]
                if fs_data["STRUCTURE"] == "FLAT":
                    fs_data["IBOARDFARE"] = float(fs_data["IBOARDFARE"])
                elif fs_data["STRUCTURE"] == "FROMTO":
                    fmi, one, farematrix_id = fs_data["FAREMATRIX"].split(".")
                    fs_data["FAREMATRIX ID"] = int(farematrix_id)
                fs_data["LINES"] = []
                fs_data["NUM LINES"] = 0
                fs_data["NUM SEGMENTS"] = 0
                numbers.append(fs_data["NUMBER"])

                data[fs_data["NUMBER"]] = fs_data
        for fs_data in data.values():
            if "FAREFROMFS" in fs_data:
                fs_data["FAREFROMFS"] = dict(zip(numbers, fs_data["FAREFROMFS"]))
        return data

    def parse_fare_matrix_file(self):
        data = _defaultdict(lambda: _defaultdict(dict))
        with open(self.fare_matrix_file, 'r') as f:
            for i, line in enumerate(f):
                if line:
                    tokens = line.split()
                    if len(tokens) != 4:
                        raise Exception("FareMatrix file line {}: expecting 4 values".format(i))
                    system, orig, dest, fare = tokens
                    data[int(system)][int(orig)][int(dest)] = float(fare)
        return data

    def generate_base_board(self, lines, board_fare):
        self._log.append(
            {"type": "text2", "content": "Set @board_cost to {} on {} lines".format(board_fare, len(lines))})
        for line in lines:
            for segment in line.segments():
                segment["@board_cost"] = board_fare

    def generate_fromto_approx(self, network, lines, fare_matrix, fs_data):
        network.create_attribute("LINK", "invehicle_cost")
        network.create_attribute("LINK", "board_cost")
        farezone_warning1 = "Warning: faresystem {} estimation: on line {} first node {} "\
            "does not have a valid @farezone ID. Using {} valid farezone {}." 

        fs_data["NUM MATRIX RECORDS"] = 0
        valid_farezones = set(fare_matrix.keys())
        for mapping in fare_matrix.values():
            zones = list(mapping.keys())
            fs_data["NUM MATRIX RECORDS"] += len(zones)
            valid_farezones.update(set(zones))
        fs_data["NUM ZONES"] = len(valid_farezones)
        valid_fz_str = ", ".join([str(x) for x in valid_farezones])
        self._log.append(
            {"type": "text2", "content": "{} valid zones: {}".format(fs_data["NUM ZONES"], valid_fz_str)})

        valid_links = set([])
        zone_nodes = _defaultdict(lambda: set([]))
        for line in lines:
            prev_farezone = 0
            for seg in line.segments(include_hidden=True):
                if seg.link:
                    valid_links.add(seg.link)
                if (seg.allow_alightings or seg.allow_boardings):
                    farezone = int(seg.i_node["@farezone"])
                    if farezone not in valid_farezones:
                        if prev_farezone == 0:
                            # DH added first farezone fix instead of exception
                            prev_farezone = list(valid_farezones)[0]
                            src_msg = "first"
                        else:
                            src_msg = "previous"
                        farezone = prev_farezone
                        self._log.append({
                            "type": "text3", 
                            "content": farezone_warning1.format(fs_data["NUMBER"], line, seg.i_node, src_msg, prev_farezone)})
                    else:
                        prev_farezone = farezone
                    zone_nodes[farezone].add(seg.i_node)
        self._log.append(
            {"type": "text2", "content": "Farezone IDs and node count: %s" % (
                ", ".join(["%s: %s" % (k, len(v)) for (k, v) in zone_nodes.items()]))})

        # Two cases:
        #  - zone / area fares with boundary crossings, different FS may overlap:
        #         handle on a line-by-line bases with boarding and incremental segment costs
        #         for local and regional bus lines
        #  - station-to-station fares
        #         handle as an isolated system with the same costs on for all segments on a link
        #         and from boarding nodes by direction.
        #         Used mostly for BART, but also used Amtrack, some ferries and express buses
        #         Can support multiple boarding stops with same farezone provided it is an isolated leg,
        #         e.g. BART zone 85 Oakland airport connector (when operated a bus with multiple stops).

        count_single_node_zones = 0.0
        count_multi_node_zones = 0.0
        for (zone, nodes) in zone_nodes.items():
            if len(nodes) > 1:
                count_multi_node_zones += 1.0
            else:
                count_single_node_zones += 1.0
        # use station-to-station approximation if >90% of zones are single node
        is_area_fare = count_multi_node_zones / (count_multi_node_zones + count_single_node_zones) > 0.1

        if is_area_fare:
            self.zone_boundary_crossing_approx(lines, valid_farezones, fare_matrix, fs_data)
        else:
            self.station_to_station_approx(lines, valid_farezones, fare_matrix, fs_data, zone_nodes, valid_links, network)

        # copy costs from links to segments
        for line in lines:
            for segment in line.segments():
                segment["@invehicle_cost"] = max(segment.link.invehicle_cost, 0)
                segment["@board_cost"] = max(segment.link.board_cost, 0)
        network.delete_attribute("LINK", "invehicle_cost")
        network.delete_attribute("LINK", "board_cost")

    def zone_boundary_crossing_approx(self, lines, valid_farezones, fare_matrix, fs_data):
        farezone_warning1 = "Warning: no value in fare matrix for @farezone ID %s "\
           "found on line %s at node %s (using @farezone from previous segment in itinerary)"
        farezone_warning2 = "Warning: faresystem %s estimation on line %s: first node %s "\
            "does not have a valid @farezone ID. "
        farezone_warning3 = "Warning: no entry in farematrix %s from-to %s-%s: board cost "\
            "at segment %s set to %s."
        farezone_warning4 = "WARNING: the above issue has occured more than once for the same line. "\
            "There is a feasible boarding-alighting on the this line with no fare defined in "\
            "the fare matrix."
        farezone_warning5 = "Warning: no entry in farematrix %s from-to %s-%s: "\
            "invehicle cost at segment %s set to %s"
        matrix_id = fs_data["FAREMATRIX ID"]

        self._log.append(
            {"type": "text2", "content": "Using zone boundary crossings approximation"})
        for line in lines:
            prev_farezone = 0
            same_farezone_missing_cost = False
            # Get list of stop segments
            stop_segments = [seg for seg in line.segments(include_hidden=True)
                             if (seg.allow_alightings or seg.allow_boardings)]
            # Get list of all segments
            all_segments = [seg for seg in line.segments(include_hidden=True)]

            for i, seg in enumerate(stop_segments):
                farezone = int(seg.i_node["@farezone"])
                if farezone not in valid_farezones:
                    self._log.append({
                        "type": "text3", "content": farezone_warning1 % (farezone, line, seg.i_node)})
                    if prev_farezone != 0:
                        farezone = prev_farezone
                        msg = "farezone from previous stop segment,"
                    else:
                        # DH added first farezone fix instead of exception
                        farezone = list(valid_farezones)[0]
                        self._log.append({
                            "type": "text3", 
                            "content": farezone_warning2 % (fs_data["NUMBER"], line, seg.i_node)
                        })
                        msg = "first valid farezone in faresystem,"
                    self._log.append({
                            "type": "text3", 
                            "content": "Using %s farezone %s" % (msg, farezone)
                        })
                if seg.allow_boardings:
                    # get the cost travelling within this farezone as base boarding cost
                    board_cost = fare_matrix.get(farezone, {}).get(farezone)
                    if board_cost is None:
                        # If this entry is missing from farematrix, 
                        # use next farezone if both previous stop and next stop are in different farezones
                        next_seg = stop_segments[i+1]
                        next_farezone = next_seg.i_node["@farezone"]
                        if next_farezone != farezone and prev_farezone != farezone:
                            board_cost = fare_matrix.get(farezone, {}).get(next_farezone)
                    if board_cost is None:
                        # use the smallest fare found from this farezone as best guess 
                        # as a reasonable boarding cost
                        board_cost = min(fare_matrix[farezone].values())
                        self._log.append({
                            "type": "text3",
                            "content": farezone_warning3 % (
                                matrix_id, farezone, farezone, seg, board_cost)})
                        if same_farezone_missing_cost == farezone:
                            self._log.append({"type": "text3", "content": farezone_warning4})
                        same_farezone_missing_cost = farezone
                    if seg.link:
                        seg.link.board_cost = max(board_cost, seg.link.board_cost)

                farezone = int(seg.i_node["@farezone"])
                # Set the zone-to-zone fare increment from the previous stop
                if prev_farezone != 0 and farezone != prev_farezone:
                    try:
                        invehicle_cost = fare_matrix[prev_farezone][farezone] - prev_seg.link.board_cost
                        fare_zone_data_is_complete = False
                        # Find the boundary_segment between previous stop (prev_seg) and current stop (seg).
                        # The boundary_segment is the segment for which fare zone of I node is different from fare zone of J node.
                        for boundary_segment in all_segments[prev_seg.number:seg.number+1]:
                            if boundary_segment.j_node and boundary_segment.i_node['@farezone'] != boundary_segment.j_node['@farezone']:
                                boundary_segment.link.invehicle_cost = max(invehicle_cost, boundary_segment.link.invehicle_cost)
                                fare_zone_data_is_complete = True
                                break
                        # If no boundary segment was found, the previous stop is assumed to be the boundary segment.
                        if fare_zone_data_is_complete is False:
                            prev_seg.link.invehicle_cost =  max(invehicle_cost, prev_seg.link.invehicle_cost)
                    except KeyError:
                        self._log.append({
                            "type": "text3", 
                            "content": farezone_warning5 % (matrix_id, prev_farezone, farezone, prev_seg, 0)})
                if farezone in valid_farezones:
                    prev_farezone = farezone
                prev_seg = seg

    def station_to_station_approx(self, lines, valid_farezones, fare_matrix, fs_data, zone_nodes, valid_links, network):
        network.create_attribute("LINK", "board_index", -1)
        network.create_attribute("LINK", "invehicle_index", -1)
        self._log.append(
            {"type": "text2", "content": "Using station-to-station least squares estimation"})
        index = 0
        farezone_area_index = {}
        for link in valid_links:
            farezone = link.i_node["@farezone"]
            if farezone not in valid_farezones:
                continue
            if len(zone_nodes[farezone]) == 1:
                link.board_index = index
                index += 1
                link.invehicle_index = index
                index += 1
            else:
                # in multiple station cases ALL boardings have the same index
                if farezone not in farezone_area_index:
                    farezone_area_index[farezone] = index
                    index += 1
                link.board_index = farezone_area_index[farezone]
                # only zone boundary crossing links get in-vehicle index
                if link.j_node["@farezone"] != farezone and link.j_node["@farezone"] in valid_farezones:
                    link.invehicle_index = index
                    index += 1

        A = []
        b = []
        pq_pairs = []
        path_builder = SPBuilder(network)

        def lookup_node(z):
            try:
                return next(iter(zone_nodes[z]))
            except StopIteration:
                return None

        for p in valid_farezones:
            q_costs = fare_matrix.get(p, {})
            orig_node = lookup_node(p)
            for q in valid_farezones:
                cost = q_costs.get(q, "n/a")
                dest_node = lookup_node(q)
                pq_pairs.append((p, q, orig_node, dest_node, cost))
                if q == p or orig_node is None or dest_node is None or cost == "n/a":
                    continue
                try:
                    path_links = path_builder.find_path(
                        orig_node, dest_node, lambda l: l in valid_links, lambda l: l.length)
                except NoPathFound:
                    continue
                b.append(cost)
                a_indices = [0]*index

                a_indices[path_links[0].board_index] = 1
                for link in path_links:
                    if link.invehicle_index == -1:
                        continue
                    a_indices[link.invehicle_index] = 1
                A.append(a_indices)

        #x, res, rank, s = _np.linalg.lstsq(A, b, rcond=None)
        # Use scipy non-negative least squares solver
        x, rnorm = _nnls(A, b)
        result = [round(i, 2) for i in x]

        header = ["Boarding node", "J-node", "Farezone", "Board cost", "Invehicle cost"]
        table_content = []
        for link in valid_links:
            if link.board_index != -1:
                link.board_cost = result[link.board_index]
            if link.invehicle_index != -1:
                link.invehicle_cost = result[link.invehicle_index]
            if link.board_cost or link.invehicle_cost:
                table_content.append(
                    [link.i_node.id, link.j_node.id, int(link.i_node["@farezone"]), link.board_cost, link.invehicle_cost])

        self._log.append(
            {"type": "text2", "content": "Table of boarding and in-vehicle costs"})
        self._log.append({"content": table_content, "type": "table", "header": header})
        network.delete_attribute("LINK", "board_index")
        network.delete_attribute("LINK", "invehicle_index")

        # validation and reporting
        header = ["p/q"]
        table_content = []
        prev_p = None
        row = None
        for p, q, orig_node, dest_node, cost in pq_pairs:
            if prev_p != p:
                header.append(p)
                if row:
                    table_content.append(row)
                row = [p]
            cost = "$%.2f" % cost if isinstance(cost, float) else cost
            if orig_node is None or dest_node is None:
                row.append("%s, UNUSED" % (cost))
            else:
                try:
                    path_links = path_builder.find_path(
                        orig_node, dest_node, lambda l: l in valid_links, lambda l: l.length)
                    path_cost = (path_links[0].board_cost + sum(l.invehicle_cost for l in path_links))
                    row.append("%s, $%.2f" % (cost, path_cost))
                except NoPathFound:
                    row.append("%s, NO PATH" % (cost))
            prev_p = p
        table_content.append(row)

        self._log.append(
            {"type": "text2", "content": "Table of origin station p to destination station q input cost, estimated cost"})
        self._log.append({"content": table_content, "type": "table", "header": header})

    def create_attribute(self, domain, name, scenario=None, network=None, atype=None):
        if scenario:
            if atype is None:
                if scenario.extra_attribute(name):
                    scenario.delete_extra_attribute(name)
                scenario.create_extra_attribute(domain, name)
            else:
                if scenario.network_field(domain, name):
                    scenario.delete_network_field(domain, name)
                scenario.create_network_field(domain, name, atype)
        if network:
            if name in network.attributes(domain):
                network.delete_attribute(domain, name)
            network.create_attribute(domain, name)

    def faresystem_distances(self, faresystems, network):
        self._log.append(
            {"type": "header", "content": "Faresystem distances"})
        self._log.append(
            {"type": "text2", "content": "Max transfer distance: %s" % MAX_TRANSFER_DISTANCE})
        for (fs_index, fs_data) in faresystems.items():
            stops = set([])
            for line in fs_data["LINES"]:
                for stop in line.segments(True):
                    if stop.allow_alightings or stop.allow_boardings:
                        stops.add(stop.i_node)
            fs_data["shape"] = _geom.MultiPoint([(stop.x, stop.y) for stop in stops])
            fs_data["bounding_rect"] = bounding_rect(fs_data["shape"])
            fs_data["NUM STOPS"] = len(fs_data["shape"])
            fs_data["FS_INDEX"] = fs_index

        # get distances between every pair of zone systems
        # determine transfer fares which are too far away to be used
        for (fs_id, fs_data) in faresystems.items():
            fs_data["distance"] = []
            fs_data["xfer_fares"] = xfer_fares = {}
            for (fs_id2, fs_data2) in faresystems.items():
                if fs_data["NUM LINES"] == 0 or fs_data2["NUM LINES"] == 0:
                    distance = "n/a"
                elif fs_id == fs_id2:
                    distance = 0
                else:
                    # Get distance between bounding boxes as first approximation
                    distance = fs_data["bounding_rect"].distance(fs_data2["bounding_rect"])
                    if distance <= MAX_TRANSFER_DISTANCE:
                        # if within tolerance get more precise distance between all stops
                        distance = fs_data["shape"].distance(fs_data2["shape"])
                fs_data["distance"].append(distance)

                if distance == "n/a" or distance > MAX_TRANSFER_DISTANCE:
                    xfer = "TOO_FAR"
                elif fs_data2["STRUCTURE"] == "FREE":
                    xfer = 0.0
                elif fs_data2["STRUCTURE"] == "FROMTO":
                    # Transfering to the same FS in fare matrix is ALWAYS free
                    # for the farezone approximation
                    if fs_id == fs_id2:
                        xfer = 0.0
                        if fs_data2["FAREFROMFS"][fs_id] != 0:
                            self._log.append({
                                "type": "text3", 
                                "content": "Warning: non-zero transfer within 'FROMTO' faresystem not supported"})
                    else:
                        xfer = "BOARD+%s" % fs_data2["FAREFROMFS"][fs_id]
                else:
                    xfer = fs_data2["FAREFROMFS"][fs_id]
                xfer_fares[fs_id2] = xfer

        distance_table = [["p/q"] + list(faresystems.keys())]
        for (fs, fs_data) in faresystems.items():
            distance_table.append([fs] + [("%.0f" % d if isinstance(d, float) else d) for d in fs_data["distance"]])
        self._log.append(
            {"type": "text2", "content": "Table of distance between stops in faresystems (feet)"})
        self._log.append({"content": distance_table, "type": "table"})

    def group_faresystems(self, faresystems, network):
        self._log.append(
            {"type": "header", "content": "Faresystem groups for ALL MODES"})
        def matching_xfer_fares(xfer_fares_list1, xfer_fares_list2):
            for xfer_fares1 in xfer_fares_list1:
                for xfer_fares2 in xfer_fares_list2:
                    for fs_id, fare1 in xfer_fares1.items():
                        fare2 = xfer_fares2[fs_id]
                        if fare1 != fare2 and (fare1 != "TOO_FAR" and fare2 != "TOO_FAR"):
                            return False
            return True

        # group faresystems together which have the same transfer-to pattern, 
        # first pass: only group by matching mode patterns to minimize the number
        #             of levels with multiple modes
        group_xfer_fares_mode = []
        for (fs_id, fs_data) in faresystems.items():
            fs_modes = fs_data["MODE_SET"]
            if not fs_modes:
                continue
            xfers = fs_data["xfer_fares"]
            is_matched = False
            for xfer_fares_list, group, modes in group_xfer_fares_mode:
                # only if mode sets match
                if set(fs_modes) == set(modes):
                    is_matched = matching_xfer_fares([xfers], xfer_fares_list)
                    if is_matched:
                        group.append(fs_id)
                        xfer_fares_list.append(xfers)
                        modes.extend(fs_modes)
                        break
            if not is_matched:
                group_xfer_fares_mode.append(([xfers], [fs_id], list(fs_modes)))

        # second pass attempt to group together this set 
        #   to minimize the total number of levels and modes
        group_xfer_fares = []
        for xfer_fares_list, group, modes in group_xfer_fares_mode:
            is_matched = False
            for xfer_fares_listB, groupB, modesB in group_xfer_fares:
                is_matched = matching_xfer_fares(xfer_fares_list, xfer_fares_listB)
                if is_matched:
                    xfer_fares_listB.extend(xfer_fares_list)
                    groupB.extend(group)
                    modesB.extend(modes)
                    break
            if not is_matched:
                group_xfer_fares.append((xfer_fares_list, group, modes))

        self._log.append(
            {"type": "header", "content": "Faresystems grouped by compatible transfer fares"})
        xfer_fares_table = [["p/q"] + list(faresystems.keys())]
        faresystem_groups = []
        i = 0
        for xfer_fares_list, group, modes in group_xfer_fares:
            xfer_fares = {}
            for fs_id in faresystems.keys():
                to_fares = [f[fs_id] for f in xfer_fares_list if f[fs_id] != "TOO_FAR"]
                fare = to_fares[0] if len(to_fares) > 0 else 0.0
                xfer_fares[fs_id] = fare
            faresystem_groups.append((group, xfer_fares))
            for fs_id in group:
                xfer_fares_table.append([fs_id] + list(faresystems[fs_id]["xfer_fares"].values()))
            i += 1
            self._log.append(
                {"type": "text2", "content": "Level %s faresystems: %s modes: %s" %
                    (i, ", ".join([str(x) for x in group]), ", ".join([str(m) for m in modes]))})

        self._log.append(
            {"type": "header", "content": "Transfer fares list by faresystem, sorted by group"})
        self._log.append({"content": xfer_fares_table, "type": "table"})

        return faresystem_groups

    def generate_transfer_fares(self, faresystems, faresystem_groups, network):
        self.create_attribute("MODE", "#orig_mode", self.scenario, network, "STRING")
        self.create_attribute("TRANSIT_LINE", "#src_mode", self.scenario, network, "STRING")
        self.create_attribute("TRANSIT_LINE", "#src_veh", self.scenario, network, "STRING")

        transit_modes = set([m for m in network.modes() if m.type == "TRANSIT"])
        mode_desc = {m.id: m.description for m in transit_modes}
        get_mode_id = network.available_mode_identifier
        get_vehicle_id = network.available_transit_vehicle_identifier

        meta_mode = network.create_mode("TRANSIT", get_mode_id())
        meta_mode.description = "Meta mode"
        for link in network.links():
            if link.modes.intersection(transit_modes):
                link.modes |= set([meta_mode])
        lines = _defaultdict(lambda: [])
        for line in network.transit_lines():
            lines[line.vehicle.id].append(line)
            line["#src_mode"] = line.mode.id
            line["#src_veh"] = line.vehicle.id
        for vehicle in network.transit_vehicles():
            temp_veh = network.create_transit_vehicle(get_vehicle_id(), vehicle.mode.id)
            veh_id = vehicle.id
            attributes = {a: vehicle[a] for a in network.attributes("TRANSIT_VEHICLE")}
            for line in lines[veh_id]:
                line.vehicle = temp_veh
            network.delete_transit_vehicle(vehicle)
            new_veh = network.create_transit_vehicle(veh_id, meta_mode.id)
            for (a, v) in attributes.items():
                new_veh[a] = v
            for line in lines[veh_id]:
                line.vehicle = new_veh
            network.delete_transit_vehicle(temp_veh)
        for link in network.links():
            link.modes -= transit_modes
        for mode in transit_modes:
            network.delete_mode(mode)

        # transition rules will be the same for every journey level
        transition_rules = []
        journey_levels = [
            {
                "description": "base",
                "destinations_reachable": True,
                "transition_rules": transition_rules,
                "waiting_time": None,
                "boarding_time": None,
                "boarding_cost": None
            }
        ]
        mode_map = _defaultdict(lambda: [])
        level = 1
        for fs_ids, xfer_fares in faresystem_groups:
            boarding_cost_id = "@from_level_%s" % level
            self.create_attribute("TRANSIT_SEGMENT", boarding_cost_id, self.scenario, network)
            journey_levels.append({
                "description": "Level_%s fs: %s" % (level, ",".join([str(x) for x in fs_ids])) ,
                "destinations_reachable": True,
                "transition_rules": transition_rules,
                "waiting_time": None,
                "boarding_time": None,
                "boarding_cost": {
                    "global": None, "at_nodes": None, "on_lines": None,
                    "on_segments": {"penalty": boarding_cost_id, "perception_factor": 1}
                },
            })

            level_modes = {}
            level_vehicles = {}
            for fs_id in fs_ids:
                fs_data = faresystems[fs_id]
                for line in fs_data["LINES"]:
                    level_mode = level_modes.get(line["#src_mode"])
                    if level_mode is None:
                        level_mode = network.create_mode("TRANSIT", get_mode_id())
                        level_mode.description = mode_desc[line["#src_mode"]]
                        level_mode["#orig_mode"] = line["#src_mode"]
                        transition_rules.append({"mode": level_mode.id, "next_journey_level": level})
                        level_modes[line["#src_mode"]] = level_mode
                        mode_map[line["#src_mode"]].append(level_mode.id)
                    for segment in line.segments():
                        segment.link.modes |= set([level_mode])
                    new_vehicle = level_vehicles.get(line.vehicle.id)
                    if new_vehicle is None:
                        new_vehicle = network.create_transit_vehicle(get_vehicle_id(), level_mode)
                        for a in network.attributes("TRANSIT_VEHICLE"):
                            new_vehicle[a] = line.vehicle[a]
                        level_vehicles[line.vehicle.id] = new_vehicle
                    line.vehicle = new_vehicle

            # set boarding cost on all lines
            # xferfares is a list of transfer fares, as a number or a string "BOARD+" + a number
            for line in network.transit_lines():
                to_faresystem = int(line["@faresystem"])
                try:
                    xferboard_cost = xfer_fares[to_faresystem]
                except KeyError:
                    continue  # line does not have a valid faresystem ID
                if xferboard_cost == "TOO_FAR":
                    pass  # use zero cost as transfer from this fs to line is impossible
                elif isinstance(xferboard_cost, str) and xferboard_cost.startswith("BOARD+"):
                    xferboard_cost = float(xferboard_cost[6:])
                    for segment in line.segments():
                        if segment.allow_boardings:
                            segment[boarding_cost_id] = max(xferboard_cost + segment["@board_cost"], 0)
                else:
                    for segment in line.segments():
                        if segment.allow_boardings:
                            segment[boarding_cost_id] = max(xferboard_cost, 0)
            level += 1

        for vehicle in network.transit_vehicles():
            if vehicle.mode == meta_mode:
                network.delete_transit_vehicle(vehicle)
        for link in network.links():
            link.modes -= set([meta_mode])
        network.delete_mode(meta_mode)
        self._log.append(
            {"type": "header", "content": "Mapping from original modes to modes for transition table"})
        for orig_mode, new_modes in mode_map.items():
            self._log.append(
                {"type": "text2", "content": "%s : %s" % (orig_mode, ", ".join(new_modes))})
        return journey_levels, mode_map

    def save_journey_levels(self, name, journey_levels):
        spec_dir = _join(_dir(_dir(self.scenario.emmebank.path)), "Specifications")
        path = _join(spec_dir, "%s_%s_journey_levels.ems" % (self.period, name))
        with open(path, 'w') as jl_spec_file:
            spec = {"type": "EXTENDED_TRANSIT_ASSIGNMENT", "journey_levels": journey_levels}
            _json.dump(spec, jl_spec_file, indent=4)

    def filter_journey_levels_by_mode(self, modes, journey_levels):
        # remove rules for unused modes from provided journey_levels
        # (restrict to provided modes)
        journey_levels = _copy(journey_levels)
        for level in journey_levels:
            rules = level["transition_rules"]
            rules = [_copy(r) for r in rules if r["mode"] in modes]
            level["transition_rules"] = rules
        # count level transition rules references to find unused levels
        num_levels = len(journey_levels)
        level_count = [0] * num_levels

        def follow_rule(next_level):
            level_count[next_level] += 1
            if level_count[next_level] > 1:
                return
            for rule in journey_levels[next_level]["transition_rules"]:
                follow_rule(rule["next_journey_level"])

        follow_rule(0)
        # remove unreachable levels
        # and find new index for transition rules for remaining levels
        level_map = {i: i for i in range(num_levels)}
        for level_id, count in reversed(list(enumerate(level_count))):
            if count == 0:
                for index in range(level_id, num_levels):
                    level_map[index] -= 1
                del journey_levels[level_id]
        # re-index remaining journey_levels
        for level in journey_levels:
            for rule in level["transition_rules"]:
                next_level = rule["next_journey_level"]
                rule["next_journey_level"] = level_map[next_level]
        return journey_levels

    def log_report(self):
        # log to logbook ONLY if Modeller is already initialized
        try:
            _m.Modeller()
        except AssertionError:
            return
        report = _m.PageBuilder(title="Fare calculation report")
        try:
            for item in self._log:
                if item["type"] == "header":
                    report.add_html("<h3 style='margin-left:10px'>%s</h3>" % item["content"])
                elif item["type"] == "text":
                    report.add_html("<div style='margin-left:20px'>%s</div>" % item["content"])
                elif item["type"] == "text2":
                    report.add_html("<div style='margin-left:30px'>%s</div>" % item["content"])
                elif item["type"] == "text3":
                    report.add_html("<div style='margin-left:40px'>%s</div>" % item["content"])
                elif item["type"] == "table":
                    table_msg = []
                    if "header" in item:
                        table_msg.append("<tr>")
                        for label in item["header"]:
                            table_msg.append("<th>%s</th>" % label)
                        table_msg.append("</tr>")
                    for row in item["content"]:
                        table_msg.append("<tr>")
                        for cell in row:
                            table_msg.append("<td>%s</td>" % cell)
                        table_msg.append("</tr>")
                    title = "<h3>%s</h3>" % item["title"] if "title" in item else ""
                    report.add_html("""
                        <div style='margin-left:20px'>
                            %s
                            <table>%s</table>
                        </div>
                        <br>
                        """ % (title, "".join(table_msg)))

        except Exception as error:
            # no raise during report to avoid masking real error
            report.add_html("Error generating report")
            report.add_html(unicode(error))
            report.add_html(_traceback.format_exc())

        _m.logbook_write("Apply fares report %s" % self.period, report.render())

    def log_text_report(self):
        bank_dir = _os.path.dirname(self.scenario.emmebank.path)
        timestamp = _time.strftime("%Y%m%d-%H%M%S")
        path = _os.path.join(bank_dir, "apply_fares_report_%s_%s.txt" % (self.period, timestamp))
        with open(path, 'w') as report:
            try:
                for item in self._log:
                    if item["type"] == "header":
                        report.write("\n%s\n" % item["content"])
                        report.write("-" * len(item["content"]) + "\n\n")
                    elif item["type"] == "text":
                        report.write("    %s\n" % item["content"])
                    elif item["type"] == "text2":
                        report.write("        %s\n" % item["content"])
                    elif item["type"] == "text3":
                        report.write("            %s\n" % item["content"])
                    elif item["type"] == "table":
                        table_msg = []
                        cell_length = [0] * len(item["content"][0])
                        if "header" in item:
                            for i, label in enumerate(item["header"]):
                                cell_length[i] = max(cell_length[i], len(str(label)))
                        for row in item["content"]:
                            for i, cell in enumerate(row):
                                cell_length[i] = max(cell_length[i], len(str(cell)))
                        if "header" in item:
                            row_text = []
                            for label, length in zip(item["header"], cell_length):
                                row_text.append("%-*s" % (length, label))
                            table_msg.append(" ".join(row_text))
                        for row in item["content"]:
                            row_text = []
                            for cell, length in zip(row, cell_length):
                                row_text.append("%-*s" % (length, cell))
                            table_msg.append(" ".join(row_text))
                        if "title" in item:
                            report.write("%s\n" % item["title"])
                            report.write("-" * len(item["title"]) + "\n")
                        table_msg.extend(["", ""])
                        report.write("\n".join(table_msg))
            except Exception as error:
                # no raise during report to avoid masking real error
                report.write("Error generating report\n")
                report.write(unicode(error) + "\n")
                report.write(_traceback.format_exc())


class ApplyFaresTool(_m.Tool(), ApplyFares):

    scenario = _m.Attribute(str)
    dot_far_file = _m.Attribute(str)
    fare_matrix_file = _m.Attribute(str)

    tool_run_msg = ""

    def __init__(self):
        super(ApplyFaresTool, self).__init__()

    def page(self):
        pb = _m.ToolPageBuilder()
        pb.title = "Apply fares"
        #pb.description =?
        #pb.branding_text =?
        if self.scenario is None:
            self.scenario = _m.Modeller().scenario

        pb.add_select_scenario("scenario", title="Select scenario:")
        pb.add_select_file("dot_far_file", "file", "Select the .far file descriping the fare systems")
        pb.add_select_file("fare_matrix_file", "file", "Select the fare matrix file with the fromto fares")

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self.execute()
            self.tool_run_msg = _m.format_info("Tool completed")
        except Exception as e:
            self.tool_run_msg = _m.format_exception(e)

    def __call__(self, scenario, dot_far_file, fare_matrix_file):
        self.scenario = scenario
        self.dot_far_file = dot_far_file
        self.fare_matrix_file = fare_matrix_file
        self.execute()


class SPBuilder(object):
    def __init__(self, network):
        self._network = network

    def find_path(self, orig_node, dest_node, filter_func, cost_func):
        visited = set([])
        visited_add = visited.add
        costs = _defaultdict(lambda : _INF)
        back_links = {}
        heap = _services.Heap()
        pop, push = heap.pop, heap.insert

        link_found = False
        for outgoing in orig_node.outgoing_links():
            if filter_func(outgoing):
                back_links[outgoing] = None
                if outgoing.j_node == dest_node:
                    link_found = True
                    break
                costs[outgoing] = cost_func(outgoing)
                push(outgoing, cost_func(outgoing))
        try:
            while not link_found:
                link = pop()
                if link in visited:
                    continue
                visited_add(link)
                for outgoing in link.j_node.outgoing_links():
                    if not filter_func(outgoing):
                        continue
                    if outgoing in visited:
                        continue
                    outgoing_cost = costs[link] + cost_func(outgoing)
                    if outgoing_cost < costs[outgoing]:
                        back_links[outgoing] = link
                        costs[outgoing] = outgoing_cost
                        push(outgoing, outgoing_cost)
                    if outgoing.j_node == dest_node:
                        link_found = True
                        break
        except RuntimeError:
            pass  # RuntimeError if heap is empty
        if not link_found:
            raise NoPathFound("No path found between %s and %s" % (orig_node, dest_node))
        prev_link = outgoing
        route = []
        while prev_link:
            route.append(prev_link)
            prev_link = back_links[prev_link]
        return list(reversed(route))


class NoPathFound(Exception):
    pass


def bounding_rect(shape):
    if shape.bounds:
        x_min, y_min, x_max, y_max = shape.bounds
        return _geom.Polygon([(x_min, y_max), (x_max, y_max), (x_max, y_min), (x_min, y_min)])
    return _geom.Point()


if __name__ == "__main__":
    parser = _argparse.ArgumentParser(description="Run fare calculations for Emme scenariofrom secified fares.far and farematrix.txt")
    parser.add_argument('-e', '--emmebank', help="Full path to Emme database (emmebank) file",
                        default=_os.path.abspath(_os.getcwd()))
    parser.add_argument('-s', '--src_scenario', help="Source Emme scenario ID")
    parser.add_argument('-d', '--dst_scenario', help="Destination Emme scenario ID (same as source if not specified)")
    parser.add_argument('-f', '--dot_far', help="the .far file describing the fare systems")
    parser.add_argument('-m', '--fare_matrix', help="the fare matrix file with the fromto fares")
    args = parser.parse_args()
    emmebank_path = args.emmebank
    src_scen_num = int(args.src_scenario)
    dst_scen_num = args.dst_scenario
    if not emmebank_path.endswith("emmebank"):
        emmebank_path = _os.path.join(emmebank_path, "emmebank")
    emmebank = _eb.Emmebank(emmebank_path)
    if dst_scen_num:
        if emmebank.scenario(dst_scen_num):
            emmebank.delete_scenario(dst_scen_num)
        scenario = emmebank.copy_scenario(src_scen_num, dst_scen_num)
    else:
        scenario = emmebank.scenario(src_scen_num)
    apply_fares = ApplyFares()
    apply_fares.scenario = scenario
    apply_fares.dot_far_file = args.dot_far
    apply_fares.fare_matrix_file = args.fare_matrix

    apply_fares.execute()

