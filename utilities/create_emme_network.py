#///////////////////////////////////////////////////////////////////////////////
#////                                                                        ///
#////                                                                        ///
#//// init_emme_project.py                                                   ///
#////                                                                        ///
#////     Usage: init_emme_project.py [-r root] [-t title]                   ///
#////                                                                        ///
#////         [-r root]: Specifies the root directory in which to create     ///
#////              the Emme project.                                         ///
#////              If omitted, defaults to the current working directory     ///
#////         [-t title]: The title of the Emme project and Emme database.   ///
#////              If omitted, defaults to SANDAG empty database.            ///
#////         [-v emmeversion]: Emme version to use to create the project.   ///
#////              If omitted, defaults to 4.3.7.                            ///
#////                                                                        ///
#////                                                                        ///
#////                                                                        ///
#////                                                                        ///
#///////////////////////////////////////////////////////////////////////////////


import apply_fares as _apply_fares

import inro.emme.desktop.app as _app
import inro.emme.desktop.types as _ws_types
import inro.emme.database.emmebank as _eb
import inro.modeller as _m

import argparse
import os
import shutil as _shutil
import pandas as pd
import math
from collections import defaultdict as _defaultdict

# ------------- input files------------
emme_mode_transaction_file = "emme_modes.txt"
emme_vehicle_transaction_file = "emme_vehicles.txt"
emme_network_transaction_file = "emme_network.txt"
extra_node_attr_file = "emme_extra_node_attributes.txt"
extra_link_attr_file = "emme_extra_link_attributes.txt"
update_extra_link_attr_file = "emme_update_extra_link_attributes.txt"
emme_transit_network_file = "emme_transit_lines.txt"
extra_transit_line_attr_file = "emme_extra_line_attributes.txt"
extra_transit_segment_attr_file = "emme_extra_segment_attributes.txt"
emme_transit_time_function_file = "emme_transit_time_function.txt"

# ------------- run parameters ---------
_all_periods = ['EA', 'AM', 'MD', 'PM', 'EV']
# mapping time of day period to emme scenario_id
period_to_scenario_dict = {
    'EA': 1000,
    'AM': 2000,
    'MD': 3000,
    'PM': 4000,
    'EV': 5000,
}

# modeller = _m.Modeller()
WKT_PROJECTION = 'PROJCS["NAD_1983_StatePlane_California_VI_FIPS_0406_Feet",GEOGCS["GCS_North_American_1983",DATUM["North_American_Datum_1983",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Lambert_Conformal_Conic_2SP"],PARAMETER["False_Easting",6561666.666666666],PARAMETER["False_Northing",1640416.666666667],PARAMETER["Central_Meridian",-116.25],PARAMETER["Standard_Parallel_1",32.78333333333333],PARAMETER["Standard_Parallel_2",33.88333333333333],PARAMETER["Latitude_Of_Origin",32.16666666666666],UNIT["Foot_US",0.30480060960121924],AUTHORITY["EPSG","102646"]]'


def init_emme_project(root, title, emmeversion, port=59673):
    # emme_dir = os.path.join(root, emme_project_folder)
    # if os.path.exists(emme_dir):
    #     _shutil.rmtree(emme_dir)
    print "Creating Emme project folder with name: %s" % title
    project_path = _app.create_project(root, title)
    desktop = _app.start(  # will not close desktop when program ends
        project=project_path, user_initials="RSG", visible=True, port=port)
    # desktop = _app.start_dedicated(
    #     project=project_path, user_initials="DH", visible=True)
    project = desktop.project
    project.name = "MTC Emme Project"
    prj_file_path = os.path.join(root, 'NAD 1983 StatePlane California VI FIPS 0406 Feet.prj')
    with open(prj_file_path, 'w') as f:
        f.write(WKT_PROJECTION)
    project.spatial_reference_file = prj_file_path
    project.initial_view = _ws_types.Box(4700000, 3450000, 4970000, 4030000)
    project_root = os.path.dirname(project_path)
    dimensions = {
        'scalar_matrices': 9999,
        'destination_matrices': 999,
        'origin_matrices': 999,
        'full_matrices': 1000,

        'scenarios': 30,
        'centroids': 6500,
        'regular_nodes': 600000,
        'links': 1000000,
        'turn_entries': 1,
        'transit_vehicles': 200,
        'transit_lines': 2000,
        'transit_segments': 2000000,
        'extra_attribute_values': 100000000,

        'functions': 99,
        'operators': 5000,
        'sola_analyses': 240
    }

    os.mkdir(os.path.join(project_root, "Database"))
    emmebank = _eb.create(os.path.join(project_root, "Database", "emmebank"), dimensions)
    emmebank.title = title
    emmebank.coord_unit_length = 0.000189394  # feet to miles
    emmebank.unit_of_length = "mi"
    emmebank.unit_of_cost = "$"
    emmebank.unit_of_energy = "MJ"
    emmebank.node_number_digits = 6
    emmebank.use_engineering_notation = True
    for period, scenario_id in period_to_scenario_dict.items():
        scenario = emmebank.create_scenario(scenario_id)
        scenario.title = period
    # emmebank.dispose()

    desktop.data_explorer().add_database(emmebank.path)

    all_databases = desktop.data_explorer().databases()
    print len(all_databases), "databases in project"
    # opening first database
    for database in all_databases:
        print database.name(), len(database.scenarios())
        database.open()
        break

    # desktop.add_modeller_toolbox(os.path.join(root, "scripts/oregon_metro_abm/resources/import_from_visum_4.4.2.mtbx"))
    # desktop.add_modeller_toolbox(os.path.join(root, "scripts/oregon_metro_abm/src/emme/toolbox/portland_toolbox_1_0_0.mtbx"))
    project.save()
    return desktop


def connect_to_running_desktop(port):
    # useful for debugging when you want to test a single step and not re-create the entire project
    desktop = _app.connect(port=port)
    # desktop = _app.connect()
    return desktop


def import_modes(input_dir, modeller, scenario_id):
    print "importing modes"
    if modeller is None:
        modeller = _m.Modeller()
    scenario = modeller.emmebank.scenario(scenario_id)
    process_modes_tool_path = "inro.emme.data.network.mode.mode_transaction"
    process_modes_tool = modeller.tool(process_modes_tool_path)
    input_file = os.path.join(input_dir, emme_mode_transaction_file).replace("\\","/")
    process_modes_tool(transaction_file=input_file,
        revert_on_error=True,
        scenario=scenario)


def import_network(input_dir, modeller, scenario_id):
    print "importing network"
    if modeller is None:
        modeller = _m.Modeller()
    scenario = modeller.emmebank.scenario(scenario_id)
    process_network_tool_path = "inro.emme.data.network.base.base_network_transaction"
    process_network_tool = modeller.tool(process_network_tool_path)
    input_file = os.path.join(input_dir, emme_network_transaction_file).replace("\\","/")
    process_network_tool(transaction_file=input_file,
        revert_on_error=True,
        scenario=scenario)


def import_extra_node_attributes(input_dir, modeller, scenario_id):
    print "importing node attributes"
    if modeller is None:
        modeller = _m.Modeller()
    scenario = modeller.emmebank.scenario(scenario_id)
    import_extra_attributes_tool_path = "inro.emme.data.extra_attribute.import_extra_attributes"
    import_extra_attributes_tool = modeller.tool(import_extra_attributes_tool_path)
    input_file = os.path.join(input_dir, extra_node_attr_file)
    import_extra_attributes_tool(
        file_path=input_file,
        scenario=scenario,
        field_separator=",",
        has_header=True,
        column_labels="FROM_HEADER",
        import_definitions=True,
        revert_on_error=True
    )


def import_extra_link_attributes(input_dir, modeller, scenario_id, update=False):
    print "importing link attributes"
    if modeller is None:
        modeller = _m.Modeller()
    scenario = modeller.emmebank.scenario(scenario_id)
    import_extra_attributes_tool_path = "inro.emme.data.extra_attribute.import_extra_attributes"
    import_extra_attributes_tool = modeller.tool(import_extra_attributes_tool_path)
    input_file = os.path.join(input_dir, extra_link_attr_file)
    if update:
        input_file = os.path.join(input_dir, update_extra_link_attr_file)
    import_extra_attributes_tool(
        file_path=input_file,
        scenario=scenario,
        field_separator=",",
        has_header=True,
        column_labels="FROM_HEADER",
        import_definitions=True,
        revert_on_error=False
    )


def import_vehicles(input_dir, modeller, scenario_id):
    print "importing transit vehicles"
    if modeller is None:
        modeller = _m.Modeller()
    scenario = modeller.emmebank.scenario(scenario_id)
    process_vehicles_tool_path = "inro.emme.data.network.transit.vehicle_transaction"
    process_vehicles_tool = modeller.tool(process_vehicles_tool_path)
    input_file = os.path.join(input_dir, emme_vehicle_transaction_file).replace("\\","/")
    process_vehicles_tool(transaction_file=input_file,
        revert_on_error=True,
        scenario=scenario)


def import_transit_time_functions(input_dir, modeller, scenario_id):
    print "importing transit time functions"
    if modeller is None:
        modeller = _m.Modeller()
    scenario = modeller.emmebank.scenario(scenario_id)
    process_functions_tool_path = "inro.emme.data.function.function_transaction"
    process_functions_tool = modeller.tool(process_functions_tool_path)
    input_file = os.path.join(input_dir, emme_transit_time_function_file).replace("\\","/")
    process_functions_tool(
        transaction_file=input_file,
        throw_on_error=True)


def import_transit_lines(input_dir, modeller, scenario_id):
    print "importing transit network"
    if modeller is None:
        modeller = _m.Modeller()
    scenario = modeller.emmebank.scenario(scenario_id)
    process_transit_lines_tool_path = "inro.emme.data.network.transit.transit_line_transaction"
    process_transit_lines_tool = modeller.tool(process_transit_lines_tool_path)
    input_file = os.path.join(input_dir, emme_transit_network_file).replace("\\","/")
    process_transit_lines_tool(transaction_file=input_file,
        revert_on_error=False,
        scenario=scenario)


def import_extra_transit_line_attributes(input_dir, modeller, scenario_id):
    print "importing extra transit line attributes"
    if modeller is None:
        modeller = _m.Modeller()
    scenario = modeller.emmebank.scenario(scenario_id)
    import_extra_attributes_tool_path = "inro.emme.data.extra_attribute.import_extra_attributes"
    import_extra_attributes_tool = modeller.tool(import_extra_attributes_tool_path)
    input_file = os.path.join(input_dir, extra_transit_line_attr_file)
    import_extra_attributes_tool(
        file_path=input_file,
        scenario=scenario,
        field_separator=",",
        has_header=True,
        column_labels="FROM_HEADER",
        import_definitions=True,
        revert_on_error=False
    )


def import_extra_transit_segment_attributes(input_dir, modeller, scenario_id):
    print "importing extra transit segment attributes"
    if modeller is None:
        modeller = _m.Modeller()
    scenario = modeller.emmebank.scenario(scenario_id)
    import_extra_attributes_tool_path = "inro.emme.data.extra_attribute.import_extra_attributes"
    import_extra_attributes_tool = modeller.tool(import_extra_attributes_tool_path)
    input_file = os.path.join(input_dir, extra_transit_segment_attr_file)
    import_extra_attributes_tool(
        file_path=input_file,
        scenario=scenario,
        field_separator=",",
        has_header=True,
        column_labels="FROM_HEADER",
        import_definitions=True,
        revert_on_error=False
    )


def replace_route_for_lines_with_nntime_and_created_segments(network, input_dir):
    stop_attributes_path = os.path.join(input_dir, 'all_stop_attributes.csv')
    stop_attributes_df = pd.read_csv(stop_attributes_path)
    transit_line_path = os.path.join(input_dir, 'lines_that_need_links_created.csv')
    transit_line_df = pd.read_csv(transit_line_path)

    with _m.logbook_trace("Creating links for specified transit lines"):
        for idx, line in transit_line_df.iterrows():
            if line['keep_line'] == 0:
                continue
            print "Creating line %s (%s) with new links" % (line['line_name'], line['LINE'])
            transit_line = network.transit_line(line['line_name'])
            if transit_line is not None:
                network.delete_transit_line(line['line_name'])
            stops_for_line = stop_attributes_df[stop_attributes_df['LINE'] == line['LINE']]
            transit_vehicle = network.transit_vehicle(line['vehicle'])
            line_mode = transit_vehicle.mode

            for idx, stop in stops_for_line.iterrows():
                if pd.isna(stop['next_node_id']):
                    # no more stops
                    break
                link = network.link(stop['node_id'], stop['next_node_id'])
                if link is None:
                    print "link from %s to %s doesn't exist, creating new link" % \
                        (stop['node_id'], stop['next_node_id'])
                    link = network.create_link(stop['node_id'], stop['next_node_id'], set([line_mode]))
                    link.length = link.shape_length
                    link['@trantime'] = link.length / line['XYSPEED'] * 60  # mi / mph * 60 min/mi = min
            network.create_transit_line(line['line_name'], transit_vehicle.id, list(stops_for_line['node_id'].values))

            # setting extra attributes
            new_line = network.transit_line(line['line_name'])
            new_line['@headway1'] = line['HEADWAY[1]']
            new_line['@headway2'] = line['HEADWAY[2]']
            new_line['@headway3'] = line['HEADWAY[3]']
            new_line['@headway4'] = line['HEADWAY[4]']
            new_line['@headway5'] = line['HEADWAY[5]']
            new_line['headway'] = line['headway']
            new_line['description'] = line['descr']
            new_line['@uses_nntime'] = line['uses_NNTIME']
            new_line['speed'] = line['speed']
            new_line['@faresystem'] = line['FARESYSTEM']
            new_line['@line_mode'] = line['MODE']



def fill_transit_times_for_created_segments(network):
    segments_fixed = 0
    lines_with_created_segments = []

    for line in network.transit_lines():
        for segment in line.segments(include_hidden=False):
            if segment['@link_trantime'] == 0:
                seg_link = segment.link
                segment['@link_trantime'] = seg_link['@trantime']
                segments_fixed += 1
                if line.id not in lines_with_created_segments:
                    lines_with_created_segments.append(line.id)
    print "Number of transit lines modified: %s" % len(lines_with_created_segments)
    print "Number of created segments assigned link trantime: %s" % segments_fixed


def distribute_nntime_among_segments(segments_for_current_nntime, nntime):
    total_length = 0
    for segment in segments_for_current_nntime:
        total_length += segment.link.length

    for segment in segments_for_current_nntime:
        segment['@tot_nntime'] = nntime
        segment['@nn_trantime'] = nntime * (segment.link.length / total_length)
        # segment['@nn_trantime'] = segment['@tot_nntime'] * (segment.link.length / total_length)
        # new_nn_trantime = segment['@tot_nntime'] * (segment.link.length / total_length)
        # print "Segment: %s, total_length: %s, length: %s, tot_nntime: %s, nn_trantime: %s," % \
        #     (segment.id, total_length, segment.link.length, segment['@tot_nntime'], segment['@nn_trantime'])


def distribute_nntime(network, input_dir):
    # redundant for lines that do not have missing segments and use NNTIME
    stop_attributes_path = os.path.join(input_dir, 'all_stop_attributes.csv')
    stop_attributes_df = pd.read_csv(stop_attributes_path)

    print "Setting transit station-to-station times (NNTIME in Cube)"

    for line in network.transit_lines():
        if (line['@uses_nntime'] == 0):
            continue
        # print "distributing NNTIME for line %s" % line.id
        segments_for_current_nntime = []
        for segment in line.segments(include_hidden=False):
            # i_node = segment.link.i_node
            j_node = segment.link.j_node
            segments_for_current_nntime.append(segment)

            nntime_df = stop_attributes_df.loc[
                (stop_attributes_df['NAME'] == line.id)
                & (stop_attributes_df['node_id'] == int(j_node)),
                'NNTIME'
            ]
            # print "%s" % nntime_df
            if nntime_df.notna().any():
                nntime = nntime_df.values[0]
                # NNTIME applies to all segments ending at node_id
                # print "Distributing %s NNTIME among %s segments " % \
                    # (nntime, len(segments_for_current_nntime))
                distribute_nntime_among_segments(segments_for_current_nntime, nntime)
                segments_for_current_nntime = []

    # # if nntime exists, use that for ivtt, else use the link trantime
    # for line in network.transit_lines():
    #     for segment in line.segments(include_hidden=False):
    #         if segment['@nn_trantime'] > 0:
    #             segment['@trantime_final'] = segment['@nn_trantime']
    #         else:
    #             segment['@trantime_final'] = segment['@link_trantime']
    #         segment.data1 = segment['@trantime_final']
    #         segment.transit_time_func = 2  # tf2 = us1 (data1)


def fix_bad_walktimes(network):
    for link in network.links():
        if link['@ntl_mode'] != 2:
            continue
        if link.shape_length > .25:
            network.delete_link(link)
            continue
        if link['@feet'] == 2:
            link.length = link.shape_length
            link['@walktime'] = link.length / 3 * 60  # mi / 3mph * 60 min/hr = walktime in mins
            link.data2 = link['@walktime']


def split_tap_connectors_to_prevent_walk(network):
    tap_stops = _defaultdict(lambda: [])
    new_node_id = init_node_id(network)
    all_transit_modes = set([mode for mode in network.modes() if mode.type == "TRANSIT"])
    node_attributes = network.attributes("NODE")
    node_attributes.remove("x")
    node_attributes.remove("y")

    access_mode = set([network.mode("a")])
    transfer_mode =  network.mode("w")
    egress_mode =  set([network.mode("e")])

    # Mark TAP adjacent stops and split TAP connectors
    for centroid in network.centroids():
        out_links = list(centroid.outgoing_links())
        in_links = list(centroid.incoming_links())
        for link in out_links + in_links:
            link.length = 0.0005  # setting length so that connector access time = 0.01
        for link in out_links:
            real_stop = link.j_node
            has_adjacent_transfer_links = False
            has_adjacent_walk_links = False
            for stop_link in real_stop.outgoing_links():
                if stop_link == link.reverse_link:
                    continue
                if transfer_mode in stop_link.modes :
                    has_adjacent_transfer_links = True
                if egress_mode in stop_link.modes :
                    has_adjacent_walk_links = True

            if has_adjacent_transfer_links or has_adjacent_walk_links:
                length = link.length
                new_node_id += 1
                tap_stop = network.split_link(centroid, real_stop, new_node_id, include_reverse=True, proportion=0.5)
                for attr in node_attributes:
                    tap_stop[attr] = real_stop[attr]
                # tap_stop["@network_adj"] = 1
                tap_stops[real_stop].append(tap_stop)
                transit_access_link = network.link(real_stop, tap_stop)
                for link in transit_access_link, transit_access_link.reverse_link:
                    link.modes = all_transit_modes
                    link.length = 0
                    # for p in ["ea", "am", "md", "pm", "ev"]:
                    #     link["@time_link_" + p] = 0
                egress_link = network.link(tap_stop, centroid)
                egress_link.modes = egress_mode
                egress_link.reverse_link.modes = access_mode
                egress_link.length = length
                egress_link.reverse_link.length = length

    line_attributes = network.attributes("TRANSIT_LINE")
    seg_attributes = network.attributes("TRANSIT_SEGMENT")

    # re-route the transit lines through the new TAP-stops
    for line in network.transit_lines():
        # store segment data for re-routing
        seg_data = {}
        itinerary = []
        tap_segments = []

        for seg in line.segments(include_hidden=True):
            seg_data[(seg.i_node, seg.j_node, seg.loop_index)] = dict((k, seg[k]) for k in seg_attributes)

            itinerary.append(seg.i_node.number)
            if seg.i_node in tap_stops and (seg.allow_boardings or seg.allow_alightings):
                # insert tap_stop, real_stop loop after tap_stop
                real_stop = seg.i_node
                tap_access = []
                tap_egress = []
                for tap_stop in tap_stops[real_stop]:
                    itinerary.extend([tap_stop.number, real_stop.number])
                    tap_access.append(len(itinerary) - 3)
                    tap_egress.append(len(itinerary) - 2)
                real_seg = len(itinerary) - 1
                # track new segments to update stopping pattern
                tap_segments.append({
                    "access": tap_access,
                    "egress": tap_egress,
                    "real": real_seg
                })

        if tap_segments:
            # store line data for re-routing
            line_data = dict((k, line[k]) for k in line_attributes)
            line_data["id"] = line.id
            line_data["vehicle"] = line.vehicle
            # delete old line, then re-create on new, re-routed itinerary
            network.delete_transit_line(line)

            new_line = network.create_transit_line(
                line_data.pop("id"),
                line_data.pop("vehicle"),
                itinerary)
            # copy line attributes back
            for k, v in line_data.iteritems():
                new_line[k] = v
            # copy segment attributes back
            for seg in new_line.segments(include_hidden=True):
                data = seg_data.get((seg.i_node, seg.j_node, seg.loop_index), {})
                for k, v in data.iteritems():
                    seg[k] = v
            # set boarding, alighting and dwell time on new tap access / egress segments
            for tap_ref in tap_segments:
                real_seg = new_line.segment(tap_ref["real"])
                for access_ref in tap_ref["access"]:
                    access_seg = new_line.segment(access_ref)
                    for k in seg_attributes:
                        access_seg[k] = real_seg[k]
                    access_seg.allow_boardings = False
                    access_seg.allow_alightings = False
                    access_seg.transit_time_func = 1  # special 0-cost ttf
                    access_seg.dwell_time = 0

                first_access_seg = new_line.segment(tap_ref["access"][0])
                first_access_seg.allow_alightings = real_seg.allow_alightings
                first_access_seg.dwell_time = real_seg.dwell_time

                for egress_ef in tap_ref["egress"]:
                    egress_seg = new_line.segment(egress_ef)
                    for k in seg_attributes:
                        egress_seg[k] = real_seg[k]
                    egress_seg.allow_boardings = real_seg.allow_boardings
                    egress_seg.allow_alightings = real_seg.allow_alightings
                    egress_seg.transit_time_func = 1  # special 0-cost ttf
                    egress_seg.dwell_time = 0

                real_seg.allow_alightings = False
                real_seg.dwell_time = 0


def init_node_id(network):
    new_node_id = max(n.number for n in network.nodes())
    new_node_id = math.ceil(new_node_id / 10000.0) * 10000
    return new_node_id


def update_link_trantime(network):
    # if nntime exists, use that for ivtt, else use the link trantime
    for line in network.transit_lines():
        for segment in line.segments(include_hidden=False):
            if segment['@nn_trantime'] > 0:
                segment['@trantime_final'] = segment['@nn_trantime']
            else:
                segment['@trantime_final'] = segment['@link_trantime']
            segment.data1 = segment['@trantime_final']
            segment.transit_time_func = 2  # tf2 = us1 (data1)

def calc_link_unreliability(network, period):
    factor_table = {
        "PEAK": {
            "FREEWAY":   {"CBD": 0.24, "UBD": 0.24, "URBAN": 0.16, "SUBURBAN": 0.08, "RURAL": 0.00},
            "PRIMARY":   {"CBD": 0.22, "UBD": 0.15, "URBAN": 0.10, "SUBURBAN": 0.05, "RURAL": 0.00},
            "SECONDARY": {"CBD": 0.11, "UBD": 0.08, "URBAN": 0.05, "SUBURBAN": 0.03, "RURAL": 0.00},
            "ROW":       {"CBD": 0.09, "UBD": 0.06, "URBAN": 0.04, "SUBURBAN": 0.02, "RURAL": 0.00},
            "RAIL":      {"CBD": 0.05, "UBD": 0.03, "URBAN": 0.02, "SUBURBAN": 0.01, "RURAL": 0.00},
        },
        "OFF_PEAK": {
            "FREEWAY":   {"CBD": 0.33, "UBD": 0.33, "URBAN": 0.22, "SUBURBAN": 0.11, "RURAL": 0.00},
            "PRIMARY":   {"CBD": 0.33, "UBD": 0.24, "URBAN": 0.16, "SUBURBAN": 0.08, "RURAL": 0.00},
            "SECONDARY": {"CBD": 0.17, "UBD": 0.12, "URBAN": 0.08, "SUBURBAN": 0.04, "RURAL": 0.00},
            "ROW":       {"CBD": 0.13, "UBD": 0.10, "URBAN": 0.06, "SUBURBAN": 0.03, "RURAL": 0.00},
            "RAIL":      {"CBD": 0.07, "UBD": 0.05, "URBAN": 0.03, "SUBURBAN": 0.02, "RURAL": 0.00},
        }
    }
    if period in ["AM", "PM"]:
        factor_table = factor_table["PEAK"]
    else:
        factor_table = factor_table["OFFPEAK"]
    for link in network.links():
        #facility_type = ?
        #area_type = ?
        # NOTE: 
        #link.data1 = factor_table[facility_type][area_type]
        pass


def create_time_period_scenario(modeller, scenario_id, root, project_name, period):
    input_dir = os.path.join(root, "emme_network_transaction_files_{}".format(period))
    import_modes(input_dir, modeller, scenario_id)
    import_network(input_dir, modeller, scenario_id)
    import_extra_node_attributes(input_dir, modeller, scenario_id)
    import_extra_link_attributes(input_dir, modeller, scenario_id)
    import_vehicles(input_dir, modeller, scenario_id)
    import_transit_time_functions(input_dir, modeller, scenario_id)
    import_transit_lines(input_dir, modeller, scenario_id, include_first_hidden_data=False)
    import_extra_transit_line_attributes(input_dir, modeller, scenario_id)
    import_extra_transit_segment_attributes(input_dir, modeller, scenario_id)

    database_path = os.path.join(root, project_name, "Database")
    emmebank_path = os.path.join(database_path, "emmebank")
    emmebank = _eb.Emmebank(emmebank_path)
    scenario = emmebank.scenario(scenario_id)
    network = scenario.get_network()

    replace_route_for_lines_with_nntime_and_created_segments(network, input_dir)
    fill_transit_times_for_created_segments(network)
    distribute_nntime(network, input_dir)
    update_link_trantime(network)
    calc_link_unreliability(network, period)
    fix_bad_walktimes(network)
    scenario.publish_network(network)
    if emmebank.scenario(scenario_id + 1):
        emmebank.delete_scenario(scenario_id + 1)
    scenario = emmebank.copy_scenario(scenario, scenario_id + 1)

    apply_fares = _apply_fares.ApplyFares()
    apply_fares.scenario = scenario
    apply_fares.dot_far_file = os.path.join(root, "fares.far")
    apply_fares.fare_matrix_file = os.path.join(root, "fareMatrix.txt")
    apply_fares.execute()

    scenario = emmebank.copy_scenario(scenario_id + 1, scenario_id + 2)
    network = scenario.get_network()
    split_tap_connectors_to_prevent_walk(network)
    scenario.publish_network(network)
    emmebank.dispose()


def update_congested_link_times(modeller, scenario_id, root, project_name):
    input_dir = os.path.join(root, "emme_network_transaction_files_{}".format(period))
    emmebank = modeller.emmebank

    # loop through all three created scenarios and update link attributes
    for i in range(0,3):
        print "updating scenario_id %s" % (scenario_id + i)
        import_extra_link_attributes(input_dir, modeller, scenario_id + i, update=True)
        scenario = emmebank.scenario(scenario_id + i)
        network = scenario.get_network()
        print "applying updated times to transit segments"
        update_link_trantime(network)
        scenario.publish_network(network)
    emmebank.dispose()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new Emme project and database with MTC defaults.")
    parser.add_argument('-p', '--trn_path', help=r"path to the trn folder, default is the current_working_folder\trn",
                        default=os.path.join(os.getcwd(), 'trn'))
    parser.add_argument('-n', '--name', help="the project folder name created in the trn folder, default is mtc_emme",
                        default="mtc_emme")
    parser.add_argument('-v', '--emmeversion', help='the Emme version', default='4.4.5')
    parser.add_argument('-i', '--first_iteration', help='Is this the first iteration? yes or no, default is yes', default='yes')
    args = parser.parse_args()

    assert (args.first_iteration == 'yes') or (args.first_iteration == 'no'), \
        'Please specify "yes" or "no" for the first_iteration (-i) run-time argument'


    if args.first_iteration == 'yes':
        # create emme project
        desktop = init_emme_project(args.trn_path, args.name, args.emmeversion)
        # desktop = connect_to_running_desktop(port=4242)
    else:
        # or connect to already open desktop
        desktop = connect_to_running_desktop(port=59673)
        # desktop = connect_to_running_desktop(port=4242)
        # create modeller instance used to import data to project database
    modeller = _m.Modeller(desktop)


    for period in _all_periods:
        scenario_id = period_to_scenario_dict[period]
        if args.first_iteration == 'yes':
            print "creating %s scenarios" % period
            create_time_period_scenario(modeller, scenario_id, args.trn_path, args.name, period)

        else:
            print "updating %s scenarios" % period
            update_congested_link_times(modeller, scenario_id, args.trn_path, args.name)
