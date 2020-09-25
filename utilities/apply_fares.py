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
import time as _time
import os as _os
import argparse as _argparse
import traceback as _traceback
import json as _json

from string import letters as _letters
from collections import defaultdict as _defaultdict

_INF = 1e400
MAX_TRANSFER_DISTANCE = 15000  # feet


class ApplyFares(object):

    def __init__(self):
        self.scenario = None
        self.dot_far_file = None
        self.fare_matrix_file = None

    def execute(self):
        self._log = []
        faresystems = self.parse_dot_far_file()
        fare_matrices = self.parse_fare_matrix_file()

        try:
            network = self.scenario.get_network()
            self.create_attribute("TRANSIT_SEGMENT", "@board_cost", self.scenario, network)
            self.create_attribute("TRANSIT_SEGMENT", "@invehicle_cost", self.scenario, network)
            # identify the lines by faresystem
            for line in network.transit_lines():
                fs_id = int(line["@faresystem"])
                try:
                    fs_data = faresystems[fs_id]
                except KeyError:
                    raise Exception("Line %s with @faresystem '%s' not found in fares.far table" % (line.id, fs_id))
                fs_data["LINES"].append(line)
                fs_data["NUM LINES"] += 1
                fs_data["NUM SEGMENTS"] += len(list(line.segments()))

            self._log.append({"type": "header", "content": "Base fares by faresystem"})
            for fs_id, fs_data in faresystems.iteritems():
                self._log.append(
                    {"type": "text", "content": "FAREZONE {}: {} {}".format(fs_id, fs_data["STRUCTURE"], fs_data["NAME"])})
                lines = fs_data["LINES"]
                if len(lines) == 0:
                    self._log.append(
                        {"type": "text2", "content": "No lines associated with this farezone"})
                elif fs_data["STRUCTURE"] == "FLAT":
                    self.generate_base_board(lines, fs_data["IBOARDFARE"])
                elif fs_data["STRUCTURE"] == "FROMTO":
                    fare_matrix = fare_matrices[fs_data["FAREMATRIX ID"]]
                    self.generate_fromto_approx(network, lines, fare_matrix, fs_data)

            faresystem_groups = self.group_faresystems(faresystems, network)
            journey_levels = self.generate_transfer_fares(faresystems, faresystem_groups, network)
            bank_dir = _os.path.dirname(self.scenario.emmebank.path)
            with open(_os.path.join(bank_dir, "journey_levels.ems"), 'w') as jl_spec:
                _json.dump(journey_levels, jl_spec, indent=4)
        except Exception as error:
            self._log.append({"type": "text", "content": "error during apply fares"})
            self._log.append({"type": "text", "content": unicode(error)})
            self._log.append({"type": "text", "content": _traceback.format_exc()})
            raise
        finally:
            log_content = []
            header = ["NUMBER", "NAME", "NUM LINES", "NUM SEGMENTS", "FAREMATRIX ID", "NUM ZONES", "NUM MATRIX RECORDS"]
            for fs_id, fs_data in faresystems.iteritems():
                log_content.append([str(fs_data.get(h, "")) for h in header])
            self._log.insert(0, {
                "content": log_content,
                "type": "table",
                "header": header,
                "title": "Faresystem data"
            })

            self.log_report()
            self.log_text_report()

    def parse_dot_far_file(self):
        data = {}
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
                # TEMPORARY workaround - manually added MODE to match @line_mode as @faresystem was missing
                try:
                    fs_data["MODE"] = int(fs_data["MODE"])
                except: 
                    pass
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

                data[fs_data["NUMBER"]] = fs_data

        return data

    def parse_fare_matrix_file(self):
        data = _defaultdict(lambda: _defaultdict(dict))
        with open(self.fare_matrix_file, 'r') as f:
            for i, line in enumerate(f):
                if line:
                    tokens = line.split()
                    if len(tokens) != 4:
                        raise Exception("FareMatrix file line %s: expecting 4 values" % i)
                    system, orig, dest, fare = tokens
                    data[int(system)][int(orig)][int(dest)] = float(fare)
        return data

    def generate_base_board(self, lines, board_fare):
        self._log.append(
            {"type": "text2", "content": "Set @board_cost to %s on %s lines" % (board_fare, len(lines))})
        for line in lines:
            for segment in line.segments():
                segment["@board_cost"] = board_fare

    def generate_fromto_approx(self, network, lines, fare_matrix, fs_data):
        network.create_attribute("LINK", "invehicle_cost")
        network.create_attribute("LINK", "board_cost")

        fs_data["NUM MATRIX RECORDS"] = 0
        valid_farezones = set(fare_matrix.keys())
        for mapping in fare_matrix.values():
            zones = list(mapping.keys())
            fs_data["NUM MATRIX RECORDS"] += len(zones)
            valid_farezones.update(set(zones))
        fs_data["NUM ZONES"] = len(valid_farezones)
        # # insert default z->z value if missing
        # for zone in valid_farezones:
        #     if zone not in fare_matrix[zone]:
        #         fare_matrix[zone][zone] = min(fare_matrix[zone].itervalues())
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
                            raise Exception("Error in fromto faresystem %s estimation: on line %s first node %s "
                                            "does not have a valid @farezone ID" % (fs_data["NUMBER"], line, seg.i_node))
                        farezone = prev_farezone
                    else:
                        prev_farezone = farezone
                    zone_nodes[farezone].add(seg.i_node)
        self._log.append(
            {"type": "text2", "content": "Farezone IDs and node count: %s" % (
                ", ".join(["%s: %s" % (k, len(v)) for k, v in zone_nodes.iteritems()]))})

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
        for zone, nodes in zone_nodes.iteritems():
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
                segment["@invehicle_cost"] = segment.link.invehicle_cost
                segment["@board_cost"] = segment.link.board_cost
        network.delete_attribute("LINK", "invehicle_cost")
        network.delete_attribute("LINK", "board_cost")

    def zone_boundary_crossing_approx(self, lines, valid_farezones, fare_matrix, fs_data):
        farezone_warning =  "Warning: no value in fare matrix for @farezone ID '%s' "\
           "found on line %s at node %s (using @farezone from previous segment in itinerary)"

        self._log.append(
        {"type": "text2", "content": "Using zone boundary crossings approximation"})
        for line in lines:
            prev_farezone = 0
            prev_seg = None
            for seg in line.segments(include_hidden=False):
                if not (seg.allow_alightings or seg.allow_boardings):
                    continue
                farezone = int(seg.i_node["@farezone"])
                if farezone not in valid_farezones:
                    if farezone != 0:
                        self._log.append({
                            "type": "text3", "content": farezone_warning % (farezone, line, seg.i_node)})
                    if prev_farezone != 0:
                        farezone = prev_farezone
                    else:
                        raise Exception("Error in fromto faresystem %s estimation: on line %s first node %s "
                                        "does not have a valid @farezone ID" % (fs_data["NUMBER"], line, seg.i_node))
                try:
                    board_cost = fare_matrix[farezone][farezone]
                except KeyError:
                    raise Exception("No entry in farematrix %s for faresystem %s estimation at segment %s "
                                    "farezones %s-%s" % (fs_data["FAREMATRIX ID"], fs_data["NUMBER"], seg, farezone, farezone))
                seg.link["board_cost"] = board_cost
                if prev_farezone !=0 and farezone != prev_farezone:
                    try:
                        prev_seg.link["invehicle_cost"] = fare_matrix[prev_farezone][farezone] - prev_seg.link["board_cost"]
                    except KeyError:
                        raise Exception("No entry from-to %s-%s in farematrix %s for faresystem %s (estimation at segment %s)"
                                        % (farezone, next_farezone, fs_data["FAREMATRIX ID"], fs_data["NUMBER"], seg))
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
                b.append(cost)
                a_indices = [0]*index
                path_links = path_builder.find_path(
                    orig_node, dest_node, lambda l: l in valid_links, lambda l: l.length)
                
                a_indices[path_links[0].board_index] = 1
                for link in path_links:
                    if link.invehicle_index == -1:
                        continue
                    a_indices[link.invehicle_index] = 1
                A.append(a_indices)

        x, res, rank, s = _np.linalg.lstsq(A, b, rcond=None)
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
                path_links = path_builder.find_path(
                    orig_node, dest_node, lambda l: l in valid_links, lambda l: l.length)
                path_cost = (path_links[0].board_cost + sum(l.invehicle_cost for l in path_links))
                row.append("%s, $%.2f" % (cost, path_cost))
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

    def group_faresystems(self, faresystems, network):
        self._log.append(
            {"type": "header", "content": "Faresystem groups"})
        for fs_index, fs_data in enumerate(faresystems.itervalues()):
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
        for fs_id, fs_data in faresystems.iteritems():
            fs_data["distance"] = []
            fs_data["xfer_fares"] = xfer_fares = {}
            for fs_id2, fs_data2 in faresystems.iteritems():
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
                            self._log.append(
                                {"type": "text2", "content": "Warning: non-zero transfer within this faresystem not supported"})
                    else:
                        xfer = "BOARD+%s" % fs_data2["FAREFROMFS"][fs_id]
                else:
                    xfer = fs_data2["FAREFROMFS"][fs_id]
                xfer_fares[fs_id2] = xfer

        distance_table = [["p/q"] + list(faresystems.keys())]
        for fs, fs_data in faresystems.iteritems():
            distance_table.append([fs] + [("%.0f" % d if isinstance(d, float) else d) for d in fs_data["distance"]])
        self._log.append(
            {"type": "text2", "content": "Table of distance between stops in faresystems (feet)"})
        self._log.append({"content": distance_table, "type": "table"})

        def matching_xfer_fares(fares, xfer_fares_list):
            for xfer_fares in xfer_fares_list:
                for fs_id, xfer_fare in fares.iteritems():
                    xfer_fare2 = xfer_fares[fs_id]
                    if xfer_fare != xfer_fare2 and (xfer_fare != "TOO_FAR" and xfer_fare2 != "TOO_FAR"):
                        return False
            return True

        # group faresystems together which have the same transfer-to pattern
        group_xfer_fares = []
        for fs_id, fs_data in faresystems.iteritems():
            xfers = fs_data["xfer_fares"]
            is_matched = False
            for xfer_fares_list, group in group_xfer_fares:
                is_matched = matching_xfer_fares(xfers, xfer_fares_list)
                if is_matched:
                    group.append(fs_id)
                    xfer_fares_list.append(xfers)
                    break
            if not is_matched:
                group_xfer_fares.append(([xfers], [fs_id]))
       
        self._log.append(
            {"type": "header", "content": "Faresystems grouped by compatible transfer fares"})
        self._log.append(
            {"type": "text2", "content": "Max transfer distance: %s" % MAX_TRANSFER_DISTANCE})
        xfer_fares_table = [["p/q"] + list(faresystems.keys())]
        faresystem_groups = []
        for xfer_fares_list, group in group_xfer_fares:
            xfer_fares = {}
            for fs_id in faresystems.keys():
                to_fares = [f[fs_id] for f in xfer_fares_list if f[fs_id] != "TOO_FAR"]
                fare = to_fares[0] if len(to_fares) > 0 else 0.0
                xfer_fares[fs_id] = fare
            faresystem_groups.append((group, xfer_fares))
            for fs_id in group:
                xfer_fares_table.append([fs_id] + list(faresystems[fs_id]["xfer_fares"].values()))
            self._log.append(
                {"type": "text2", "content": "Faresystems: %s" % ", ".join([str(x) for x in group])})

        self._log.append(
            {"type": "header", "content": "Transfer fares list by faresystem, sorted by group"})
        self._log.append({"content": xfer_fares_table, "type": "table"})

        return faresystem_groups

    def generate_transfer_fares(self, faresystems, faresystem_groups, network):
        self.create_attribute("TRANSIT_LINE", "#src_mode", self.scenario, network, "STRING")
        self.create_attribute("TRANSIT_LINE", "#src_veh", self.scenario, network, "STRING")

        transit_modes = set([m for m in network.modes() if m.type == "TRANSIT"])
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
            for a, v in attributes.iteritems():
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
                "boarding_cost": {"on_segments": boarding_cost_id}
            })
            level_mode = network.create_mode("TRANSIT", get_mode_id())
            transition_rules.append({"mode": level_mode.id, "next_journey_level": level})
            level_vehicles = {}
            for fs_id in fs_ids:
                fs_data = faresystems[fs_id]
                for line in fs_data["LINES"]:
                    for segment in line.segments():
                        segment.link.modes |= set([level_mode])
                    if line.vehicle.id in level_vehicles:
                        new_vehicle = level_vehicles[line.vehicle.id]
                    else:
                        new_vehicle = network.create_transit_vehicle(get_vehicle_id(), level_mode)
                        for a in network.attributes("TRANSIT_VEHICLE"):
                            new_vehicle[a] = line.vehicle[a]
                        level_vehicles[line.vehicle.id] = new_vehicle
                    line.vehicle = new_vehicle

            # set boarding cost on all lines
            # xferfares is a list of transfer fares, as a number or a string "BOARD+" + a number
            for line in network.transit_lines():
                to_faresystem = int(line["@faresystem"])
                xferboard_cost = xfer_fares[to_faresystem]
                if xferboard_cost == "TOO_FAR":
                    pass  # use zero cost as transfer from this fs to line is impossible
                elif isinstance(xferboard_cost, str) and xferboard_cost.startswith("BOARD+"):
                    xferboard_cost = float(xferboard_cost[6:])
                    for segment in line.segments():
                        segment[boarding_cost_id] = xferboard_cost + segment["@board_cost"]
                else:
                    for segment in line.segments():
                        segment[boarding_cost_id] = xferboard_cost
            level += 1
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

        _m.logbook_write("Apply fares report", report.render())

    def log_text_report(self):
        bank_dir = _os.path.dirname(self.scenario.emmebank.path)
        timestamp = _time.strftime("%Y%m%d-%H%M%S")
        with open(_os.path.join(bank_dir, "apply_fares_report_%s.txt" % timestamp), 'w') as report:
            try:
                for item in self._log:
                    if item["type"] == "header":
                        report.write("%s\n" % item["content"])
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
                    back_links[outgoing] = link
                    if outgoing.j_node == dest_node:
                        link_found = True
                        break
                    outgoing_cost = costs[link] + cost_func(link)
                    costs[link] = outgoing_cost
                    push(outgoing, outgoing_cost)
        except RuntimeError:
            pass  # RuntimeError if heap is empty
        if not link_found:
            raise Exception("No path found between %s and %s" % (orig_node, dest_node))
        prev_link = back_links[outgoing]
        route = [outgoing]
        while prev_link:
            route.append(prev_link)
            prev_link = back_links[prev_link]
        return list(reversed(route))


def bounding_rect(shape):
    if shape.bounds:
        x_min, y_min, x_max, y_max = shape.bounds
        return _geom.Polygon([(x_min, y_max), (x_max, y_max), (x_max, y_min), (x_min, y_min)])
    return _geom.Point()


if __name__ == "__main__":
    parser = _argparse.ArgumentParser(description="Run fare calculations for Emme scenariofrom secified fares.far and farematrix.txt")
    parser.add_argument('-e', '--emmebank', help="Full path to Emme database (emmebank) file",
                        default=os.path.abspath(os.getcwd()))
    parser.add_argument('-s', '--scenario', help="Emme scenario ID")
    parser.add_argument('-f', '--dot_far', help="the .far file descriping the fare systems")
    parser.add_argument('-m', '--fare_matrix', help="the fare matrix file with the fromto fares")
    args = parser.parse_args()

    emmebank = _eb.Emmebank(args.emmebank)
    apply_fares = ApplyFares()
    apply_fares.scenario = emmebank.scenario(args.scenario)
    apply_fares.dot_far_file = args.dot_far
    apply_fares.fare_matrix_file = args.fare_matrix

    apply_fares.execute()
