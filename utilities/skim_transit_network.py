import inro.modeller as _m
import inro.emme.database.emmebank as _eb
import inro.emme.core.exception as _except
import traceback as _traceback
from copy import deepcopy as _copy
from collections import defaultdict as _defaultdict, OrderedDict
import contextlib as _context

import multiprocessing as _multiprocessing
import argparse
import re as _re
import time as _time
import numpy
import os
import sys
import math

try:
    import openmatrix as _omx
    def open_file(file_path, mode):
        return OmxMatrix(_omx.open_file(file_path, mode))
except Exception, e:
    import omx as _omx
    def open_file(file_path, mode):
        return OmxMatrix(_omx.openFile(file_path, mode))

_all_periods = ['AM']
# _all_periods = ['EA', 'AM', 'MD', 'PM', 'EV']
_all_components = ['transit_skims']

num_processors = 20
transit_modes = ['b', 'x', 'f', 'l', 'h', 'r']
aux_transit_modes = ['w', 'a', 'e']

# initialize matrix variables
_matrix_cache = {}
_matrices = {}
_matrix_count = {}


def connect_to_desktop(port=59673):
    print _app.App.port
    desktop = _app.connect(port=port)
    # desktop = _app.connect()
    return desktop


# ------------------------------------ Initialize matrices -----------------------------------------

@_m.logbook_trace("Create and initialize matrices", save_arguments=True)
def initialize_matrices(components, periods, scenario, delete_all_existing=False):
    attributes = {
        "components": components,
        "periods": periods,
        "delete_all_existing": delete_all_existing
    }
    if periods == "all":
        periods = _all_periods[:]
    if delete_all_existing:
        with _m.logbook_trace("Delete all existing matrices"):
            for matrix in scenario.emmebank.matrices():
                scenario.emmebank.delete_matrix(matrix)
    create_matrix_tool = _m.Modeller().tool("inro.emme.data.matrix.create_matrix")
    generate_matrix_list(scenario)
    matrices = []
    for component in components:
        matrices.extend(create_matrices(component, periods, scenario, create_matrix_tool))
    create_matrix_tool("ms1", "zero", "zero", scenario=scenario, overwrite=True)
    return matrices


def create_matrices(component, periods, scenario, create_matrix_tool):
    with _m.logbook_trace("Create matrices for component %s" % (component.replace("_", " "))):
        emmebank = scenario.emmebank
        matrices = []
        for period in periods + ["ALL"]:
            with _m.logbook_trace("For period %s" % (period)):
                for ident, name, desc in _matrices[component][period]:
                    existing_matrix = emmebank.matrix(name)
                    if existing_matrix and (existing_matrix.id != ident):
                        raise Exception("Matrix name conflict '%s', with id %s instead of %s. Delete all matrices first."
                            % (name, existing_matrix.id, ident))
                    matrices.append(create_matrix_tool(ident, name, desc, scenario=scenario, overwrite=True))
    return matrices


def generate_matrix_list(scenario):
    global _matrices
    global _matrix_count
    _matrices = dict(
        (name, dict((k, []) for k in _all_periods + ["ALL"]))
        for name in _all_components)
    _matrix_count = {"ms": 2, "md": 100, "mo": 100, "mf": 100}

    # for component in self._all_components:
    #     fcn = getattr(component)
    #     fcn()
    get_transit_skims()
    # check dimensions can fit full set of matrices
    type_names = [
        ('mf', 'full_matrices'),
        ('mo', 'origin_matrices'),
        ('md', 'destination_matrices'),
        ('ms', 'scalar_matrices')]
    dims = scenario.emmebank.dimensions
    for prefix, name in type_names:
        if _matrix_count[prefix] > dims[name]:
            raise Exception("emmebank capacity error, increase %s to at least %s" % (name, _matrix_count[prefix]))
    return _matrices


def get_matrix_names(component, periods, scenario):
    generate_matrix_list(scenario)
    matrices = []
    for period in periods:
        matrices.extend([m[1] for m in _matrices[component][period]])
    return matrices


def add_matrices(component, period, matrices):
    for ident, name, desc in matrices:
        _matrices[component][period].append([ident+str(_matrix_count[ident]), name, desc])
        _matrix_count[ident] += 1


def get_transit_skims():
    tmplt_matrices = [
        ("GENCOST",    "total impedance"),
        ("FIRSTWAIT",  "first wait time"),
        ("XFERWAIT",   "transfer wait time"),
        ("TOTALWAIT",  "total wait time"),
        ("FARE",       "fare"),
        ("XFERS",      "num transfers"),
        ("ACCWALK",    "access walk time"),
        ("XFERWALK",   "transfer walk time"),
        ("EGRWALK",    "egress walk time"),
        ("TOTALWALK",  "total walk time"),
        ("TOTALIVTT",  "total in-vehicle time"),
        ("DWELLTIME",  "dwell time"),
        ("LBIVTT",     "local bus in-vehicle time"),
        ("EBIVTT",     "express bus in-vehicle time"),
        ("LRIVTT",     "light rail in-vehicle time"),
        ("HRIVTT",     "heavy rail in-vehicle time"),
        ("CRIVTT",     "commuter rail in-vehicle time"),
        ("FRIVTT",     "ferry in-vehicle time"),
        ("LBDIST",     "local bus IV distance"),
        ("EBDIST",     "express bus IV distance"),
        ("LRDIST",     "light rail IV distance"),
        ("HRDIST",     "heavy rail IV distance"),
        ("CRDIST",     "commuter rail IV distance"),
        ("FRDIST",     "ferry IV distance"),
        ("TOTDIST",    "Total transit distance"),
        ("IN_VEHICLE_COST",    "In vehicle cost"),
        ("LAYOVER_BOARD",    "layover board"),
        ("PERCEIVED_FARE",    "perceived fare"),
    ]
    skim_sets = [
        ("BUS",    "Local bus only"),
        ("PREM",   "Premium modes only"),
        ("ALLPEN", "All w/ xfer pen")
    ]
    for period in _all_periods:
        for set_name, set_desc in skim_sets:
            add_matrices("transit_skims", period,
                [("mf", period + "_" + set_name + "_" + name,
                  period + " " + set_desc + ": " + desc)
                 for name, desc in tmplt_matrices])


def temp_matrices(emmebank, mat_type, total=1, default_value=0.0):
    matrices = []
    try:
        while len(matrices) != int(total):
            try:
                ident = emmebank.available_matrix_identifier(mat_type)
            except _except.CapacityError:
                raise _except.CapacityError(
                    "Insufficient room for %s required temp matrices." % total)
            matrices.append(emmebank.create_matrix(ident, default_value))
        yield matrices[:]
    finally:
        for matrix in matrices:
            # In case of transient file conflicts and lag in windows file handles over the network
            # attempt to delete file 10 times with increasing delays 0.05, 0.2, 0.45, 0.8 ... 5
            remove_matrix = lambda: emmebank.delete_matrix(matrix)
            retry(remove_matrix)


def retry(fcn, attempts=10, init_wait=0.05, error_types=(RuntimeError, WindowsError)):
    for attempt in range(1, attempts + 1):
        try:
            fcn()
            return
        except error_types:
            if attempt > attempts:
                raise
            _time.sleep(init_wait * (attempt**2))


def parse_num_processors(value):
    max_processors = _multiprocessing.cpu_count()
    if isinstance(value, int):
        return value
    if isinstance(value, basestring):
        if value == "MAX":
            return max_processors
        if _re.match("^[0-9]+$", value):
            return int(value)
        result = _re.split("^MAX[\s]*-[\s]*", value)
        if len(result) == 2:
            return max(max_processors - int(result[1]), 1)
    if value:
        return int(value)
    return value

# ---------------------------------------- Skimming ----------------------------------------------

def perform_assignment_and_skim(modeller, scenario, period, data_table_name=None, assignment_only=False,
                                skims_only=True, num_processors="MAX-1"):
    attrs = {
            "period": period,
            "scenario": scenario.id,
            "data_table_name": data_table_name,
            "assignment_only": assignment_only,
            "skims_only": skims_only,
            "num_processors": num_processors,
        }
    # if not scenario.has_traffic_results:
    #     raise Exception("missing traffic assignment results for period %s scenario %s" % (period, scenario))
    emmebank = scenario.emmebank
    # with setup(scenario, attrs) as set_up:
    # gen_utils.log_snapshot("Transit assignment", str(self), attrs)
    if not period in _all_periods:
        raise Exception('period: unknown value - specify one of %s' % _all_periods)
    num_processors = parse_num_processors(num_processors)
    params = get_perception_parameters(period)
    network = scenario.get_partial_network(
        element_types=["TRANSIT_LINE"], include_attributes=True)

    # holdover from sandag
    params["coaster_fare_percep"] = 0
    max_fare = 0

    # run_assignment(period, params, network, day_pass, skims_only, num_processors)
    run_assignment(modeller, scenario, period, params, network, skims_only, num_processors)

    if not assignment_only:
        # max_fare = day_pass for local bus and regional_pass for premium modes
        run_skims(modeller, scenario, "BUS", period, params, max_fare, num_processors, network)
        run_skims(modeller, scenario, "PREM", period, params, max_fare, num_processors, network)
        run_skims(modeller, scenario, "ALLPEN", period, params, max_fare, num_processors, network)
        mask_allpen(scenario, period)
        report(scenario, period)


def setup(scenario, attrs):
    global _matrix_cache
    _matrix_cache = {}  # initialize cache at beginning of run
    emmebank = scenario.emmebank
    period = attrs["period"]
    with _m.logbook_trace("Transit assignment for period %s" % period, attributes=attrs):
        with temp_matrices(emmebank, "FULL", 3) as matrices:
            matrices[0].name = "TEMP_IN_VEHICLE_COST"
            matrices[1].name = "TEMP_LAYOVER_BOARD"
            matrices[2].name = "TEMP_PERCEIVED_FARE"
            try:
                yield
            finally:
                _matrix_cache = {}  # clear cache at end of run


def get_perception_parameters(period):
    perception_parameters = {
        "EA": {
            "vot": 0.27,
            "init_wait": 1.5,
            "xfer_wait": 3.0,
            "walk": 2.0,
            "init_headway": 'hdw',
            "xfer_headway": 'hdw',
            "fare": 0.0,
            "in_vehicle": 1.0,
            "fixed_link_time": 0.0,
        },
        "AM": {
            "vot": 0.27,
            "init_wait": 1.5,
            "xfer_wait": 3.0,
            "walk": 2.0,
            "init_headway": 'hdw',
            "xfer_headway": 'hdw',
            "fare": 0.0,
            "in_vehicle": 1.0,
            "fixed_link_time": 0.0,
        },
        "MD": {
            "vot": 0.27,
            "init_wait": 1.5,
            "xfer_wait": 3.0,
            "walk": 2.0,
            "init_headway": 'hdw',
            "xfer_headway": 'hdw',
            "fare": 0.0,
            "in_vehicle": 1.0,
            "fixed_link_time": 0.0,
        },
        "PM": {
            "vot": 0.27,
            "init_wait": 1.5,
            "xfer_wait": 3.0,
            "walk": 2.0,
            "init_headway": 'hdw',
            "xfer_headway": 'hdw',
            "fare": 0.0,
            "in_vehicle": 1.0,
            "fixed_link_time": 0.0,
        },
        "EV": {
            "vot": 0.27,
            "init_wait": 1.5,
            "xfer_wait": 3.0,
            "walk": 2.0,
            "init_headway": 'hdw',
            "xfer_headway": 'hdw',
            "fare": 0.0,
            "in_vehicle": 1.0,
            "fixed_link_time": 0.0,
        }
    }
    return perception_parameters[period]


@_m.logbook_trace("Transit assignment by demand set", save_arguments=True)
def run_assignment(modeller, scenario, period, params, network, skims_only, num_processors):
    assign_transit = modeller.tool(
        "inro.emme.transit_assignment.extended_transit_assignment")

    walk_modes = ["a", "w", "e"]
    local_bus_mode = ["b"]
    premium_modes = ['x', 'f', 'l', 'h', 'r']

    # get the generic all-modes journey levels table
    # journey_levels = self.all_modes_journey_levels(params, network, day_pass_cost)
    # local_bus_journey_levels = self.filter_journey_levels_by_mode(local_bus_mode, journey_levels)
    # premium_modes_journey_levels = self.filter_journey_levels_by_mode(premium_modes, journey_levels)
    # All modes transfer penalty assignment uses penalty of 15 minutes
    # for level in journey_levels[1:]:
    #     level["boarding_time"] =  {"global": {"penalty": 15, "perception_factor": 1}}

    journey_levels = []
    local_bus_journey_levels = []
    premium_modes_journey_levels = []

    base_spec = {
        "type": "EXTENDED_TRANSIT_ASSIGNMENT",
        "modes": [],
        "demand": "",
        "waiting_time": {
            "effective_headways": params["init_headway"], "headway_fraction": 0.5,
            "perception_factor": params["init_wait"], "spread_factor": 1.0
        },
        # Fare attributes
        "boarding_cost": {"global": {"penalty": 0, "perception_factor": 1}},
        "boarding_time": {"global": {"penalty": 0, "perception_factor": 1}},
        "in_vehicle_cost": None,
        # "in_vehicle_cost": {"penalty": 0,
        #                     "perception_factor": params["coaster_fare_percep"]},
        "in_vehicle_time": {"perception_factor": params["in_vehicle"]},
        "aux_transit_time": {"perception_factor": params["walk"]},
        "aux_transit_cost": None,
        "journey_levels": [],
        "flow_distribution_between_lines": {"consider_total_impedance": False},
        "flow_distribution_at_origins": {
            "fixed_proportions_on_connectors": None,
            "choices_at_origins": "OPTIMAL_STRATEGY"
        },
        "flow_distribution_at_regular_nodes_with_aux_transit_choices": {
            "choices_at_regular_nodes": "OPTIMAL_STRATEGY"
        },
		#"circular_lines": {
		#	"stay": True
        #},
        "connector_to_connector_path_prohibition": None,
        "od_results": {"total_impedance": None},
        "performance_settings": {"number_of_processors": num_processors}
    }

    skim_parameters = OrderedDict([
        ("BUS", {
            "modes": walk_modes + local_bus_mode,
            "journey_levels": local_bus_journey_levels
        }),
        ("PREM", {
            "modes": walk_modes + premium_modes,
            "journey_levels": premium_modes_journey_levels
        }),
        ("ALLPEN", {
            "modes": walk_modes + local_bus_mode + premium_modes,
            "journey_levels": journey_levels
        }),
    ])

    if skims_only:
        access_modes = ["WLK"]
    else:
        access_modes = ["WLK", "PNR", "KNR"]
    add_volumes = False
    for a_name in access_modes:
        for mode_name, parameters in skim_parameters.iteritems():
            spec = _copy(base_spec)
            name = "%s_%s%s" % (period, a_name, mode_name)
            spec["modes"] = parameters["modes"]
            spec["demand"] = 'ms1' # zero demand matrix
            spec["journey_levels"] = parameters["journey_levels"]
            assign_transit(spec, class_name=name, add_volumes=add_volumes, scenario=scenario)
            add_volumes = True


@_m.logbook_trace("Extract skims", save_arguments=True)
def run_skims(modeller, scenario, name, period, params, max_fare, num_processors, network):
    emmebank = scenario.emmebank
    matrix_calc = modeller.tool(
        "inro.emme.matrix_calculation.matrix_calculator")
    network_calc = modeller.tool(
        "inro.emme.network_calculation.network_calculator")
    matrix_results = modeller.tool(
        "inro.emme.transit_assignment.extended.matrix_results")
    path_analysis = modeller.tool(
        "inro.emme.transit_assignment.extended.path_based_analysis")
    strategy_analysis = modeller.tool(
        "inro.emme.transit_assignment.extended.strategy_based_analysis")

    class_name = "%s_WLK%s" % (period, name)
    skim_name = "%s_%s" % (period, name)
    # self.run_skims.logbook_cursor.write(name="Extract skims for %s, using assignment class %s" % (name, class_name))

    with _m.logbook_trace("First and total wait time, number of boardings, fares, total walk time, in-vehicle time"):
        # First and total wait time, number of boardings, fares, total walk time, in-vehicle time
        spec = {
            "type": "EXTENDED_TRANSIT_MATRIX_RESULTS",
            "actual_first_waiting_times": 'mf"%s_FIRSTWAIT"' % skim_name,
            "actual_total_waiting_times": 'mf"%s_TOTALWAIT"' % skim_name,
            "total_impedance": 'mf"%s_GENCOST"' % skim_name,
            "by_mode_subset": {
                "modes": [mode.id for mode in network.modes() if mode.type == "TRANSIT" or mode.type == "AUX_TRANSIT"],
                "avg_boardings": 'mf"%s_XFERS"' % skim_name,
                "actual_in_vehicle_times": 'mf"%s_TOTALIVTT"' % skim_name,
                "actual_in_vehicle_costs": 'mf"%s_IN_VEHICLE_COST"' % skim_name,
                "actual_total_boarding_costs": 'mf"%s_FARE"' % skim_name,
                "perceived_total_boarding_costs": 'mf"%s_PERCEIVED_FARE"' % skim_name,
                "actual_aux_transit_times": 'mf"%s_TOTALWALK"' % skim_name,
            },
        }
        matrix_results(spec, class_name=class_name, scenario=scenario, num_processors=num_processors)
    with _m.logbook_trace("Distance and in-vehicle time by mode"):
        mode_combinations = [
            ("LB", ["b"], ["IVTT", "DIST"]),
            ("EB", ["x"], ["IVTT", "DIST"]),
            ("FR", ['f'], ["IVTT", "DIST"]),
            ("LR", ['l'], ["IVTT", "DIST"]),
            ("HR", ['h'], ["IVTT", "DIST"]),
            ("CR", ['r'], ["IVTT", "DIST"]),
        ]
        for mode_name, modes, skim_types in mode_combinations:
            dist = 'mf"%s_%sDIST"' % (skim_name, mode_name) if "DIST" in skim_types else None
            ivtt = 'mf"%s_%sIVTT"' % (skim_name, mode_name) if "IVTT" in skim_types else None
            spec = {
                "type": "EXTENDED_TRANSIT_MATRIX_RESULTS",
                "by_mode_subset": {
                    "modes": modes,
                    "distance": dist,
                    "actual_in_vehicle_times": ivtt,
                },
            }
            matrix_results(spec, class_name=class_name, scenario=scenario, num_processors=num_processors)
        # Sum total distance
        spec = {
            "type": "MATRIX_CALCULATION",
            "constraint": None,
            "result": 'mf"%s_TOTDIST"' % skim_name,
            "expression": ('mf"{0}_LBDIST" + mf"{0}_LRDIST" + mf"{0}_CRDIST"'
                           ' + mf"{0}_FRDIST" + mf"{0}_HRDIST"  + mf"{0}_EBDIST"').format(skim_name),
        }
        matrix_calc(spec, scenario=scenario, num_processors=num_processors)

    # convert number of boardings to number of transfers
    # and subtract transfers to the same line at layover points
    with _m.logbook_trace("Number of transfers and total fare"):
        # spec = {
        #     "trip_components": {"boarding": "@layover_board"},
        #     "sub_path_combination_operator": "+",
        #     "sub_strategy_combination_operator": "average",
        #     "selected_demand_and_transit_volumes": {
        #         "sub_strategies_to_retain": "ALL",
        #         "selection_threshold": {"lower": -999999, "upper": 999999}
        #     },
        #     "results": {
        #         "strategy_values": 'mf"%s_LAYOVER_BOARD"' % skim_name ,
        #     },
        #     "type": "EXTENDED_TRANSIT_STRATEGY_ANALYSIS"
        # }
        # strategy_analysis(spec, class_name=class_name, scenario=scenario, num_processors=num_processors)
        spec = {
            "type": "MATRIX_CALCULATION",
            "constraint":{
                "by_value": {
                    "od_values": 'mf"%s_XFERS"' % skim_name,
                    "interval_min": 1, "interval_max": 9999999,
                    "condition": "INCLUDE"},
            },
            "result": 'mf"%s_XFERS"' % skim_name,
            "expression": '(%s_XFERS - 1).max.0' % skim_name,
        }
        matrix_calc(spec, scenario=scenario, num_processors=num_processors)

        # sum in-vehicle cost and boarding cost to get the fare paid
        spec = {
            "type": "MATRIX_CALCULATION",
            "constraint": None,
            "result": 'mf"%s_FARE"' % skim_name,
            "expression": '(%s_FARE + %s_IN_VEHICLE_COST).min.%s' % (skim_name, skim_name, max_fare),
        }
        matrix_calc(spec, scenario=scenario, num_processors=num_processors)

    # walk access time - get distance and convert to time with 3 miles / hr
    with _m.logbook_trace("Walk time access, egress and xfer"):
        path_spec = {
            "portion_of_path": "ORIGIN_TO_INITIAL_BOARDING",
            "trip_components": {"aux_transit": "length",},
            "path_operator": "+",
            "path_selection_threshold": {"lower": 0, "upper": 999999 },
            "path_to_od_aggregation": {
                "operator": "average",
                "aggregated_path_values": 'mf"%s_ACCWALK"' % skim_name,
            },
            "type": "EXTENDED_TRANSIT_PATH_ANALYSIS"
        }
        path_analysis(path_spec, class_name=class_name, scenario=scenario, num_processors=num_processors)

        # walk egress time - get distance and convert to time with 3 miles/ hr
        path_spec = {
            "portion_of_path": "FINAL_ALIGHTING_TO_DESTINATION",
            "trip_components": {"aux_transit": "length",},
            "path_operator": "+",
            "path_selection_threshold": {"lower": 0, "upper": 999999 },
            "path_to_od_aggregation": {
                "operator": "average",
                "aggregated_path_values": 'mf"%s_EGRWALK"' % skim_name
            },
            "type": "EXTENDED_TRANSIT_PATH_ANALYSIS"
        }
        path_analysis(path_spec, class_name=class_name, scenario=scenario, num_processors=num_processors)

        spec_list = [
        {    # walk access time - convert to time with 3 miles/ hr
            "type": "MATRIX_CALCULATION",
            "constraint": None,
            "result": 'mf"%s_ACCWALK"' % skim_name,
            "expression": '60.0 * %s_ACCWALK / 3.0' % skim_name,
        },
        {    # walk egress time - convert to time with 3 miles/ hr
            "type": "MATRIX_CALCULATION",
            "constraint": None,
            "result": 'mf"%s_EGRWALK"' % skim_name,
            "expression": '60.0 * %s_EGRWALK / 3.0' % skim_name,
        },
        {   # transfer walk time = total - access - egress
            "type": "MATRIX_CALCULATION",
            "constraint": None,
            "result": 'mf"%s_XFERWALK"' % skim_name,
            "expression": '({name}_TOTALWALK - {name}_ACCWALK - {name}_EGRWALK).max.0'.format(name=skim_name),
        }]
        matrix_calc(spec_list, scenario=scenario, num_processors=num_processors)

    # transfer wait time
    with _m.logbook_trace("Wait time - xfer"):
        spec = {
            "type": "MATRIX_CALCULATION",
            "constraint":{
                "by_value": {
                    "od_values": 'mf"%s_TOTALWAIT"' % skim_name,
                    "interval_min": 0, "interval_max": 9999999,
                    "condition": "INCLUDE"},
            },
            "result": 'mf"%s_XFERWAIT"' % skim_name,
            "expression": '({name}_TOTALWAIT - {name}_FIRSTWAIT).max.0'.format(name=skim_name),
        }
        matrix_calc(spec, scenario=scenario, num_processors=num_processors)

    # with _m.logbook_trace("Calculate dwell time"):
    #     with gen_utils.temp_attrs(scenario, "TRANSIT_SEGMENT", ["@dwt_for_analysis"]):
    #         values = scenario.get_attribute_values("TRANSIT_SEGMENT", ["dwell_time"])
    #         scenario.set_attribute_values("TRANSIT_SEGMENT", ["@dwt_for_analysis"], values)
    #
    #         spec = {
    #             "trip_components": {"in_vehicle": "@dwt_for_analysis"},
    #             "sub_path_combination_operator": "+",
    #             "sub_strategy_combination_operator": "average",
    #             "selected_demand_and_transit_volumes": {
    #                 "sub_strategies_to_retain": "ALL",
    #                 "selection_threshold": {"lower": -999999, "upper": 999999}
    #             },
    #             "results": {
    #                 "strategy_values": 'mf"%s_DWELLTIME"' % skim_name,
    #             },
    #             "type": "EXTENDED_TRANSIT_STRATEGY_ANALYSIS"
    #         }
    #         strategy_analysis(spec, class_name=class_name, scenario=scenario, num_processors=num_processors)

    # expr_params = _copy(params)
    # expr_params["xfers"] = 15.0
    # expr_params["name"] = skim_name
    # spec = {
    #     "type": "MATRIX_CALCULATION",
    #     "constraint": None,
    #     "result": 'mf"%s_GENCOST"' % skim_name,
    #     "expression": ("{xfer_wait} * {name}_TOTALWAIT "
    #                    "- ({xfer_wait} - {init_wait}) * {name}_FIRSTWAIT "
    #                    "+ 1.0 * {name}_TOTALIVTT + 0.5 * {name}_LBIVTT"
    #                    "+ (1 / {vot}) * ({name}_PERCEIVED_FARE + {coaster_fare_percep} * {name}_IN_VEHICLE_COST)"
    #                    "+ {xfers} *({name}_XFERS.max.0) "
    #                    "+ {walk} * {name}_TOTALWALK").format(**expr_params)
    # }
    # matrix_calc(spec, scenario=scenario, num_processors=num_processors)
    return


def mask_allpen(scenario, period):
    # Reset skims to 0 if not both local and premium
    skims = [
        "FIRSTWAIT", "TOTALWAIT", "DWELLTIME", "BUSIVTT", "XFERS", "TOTALWALK",
        "LBIVTT", "EBIVTT", "LRIVTT", "HRIVTT", "CRIVTT", "FRIVTT",
        "GENCOST", "XFERWAIT", "FARE",
        "ACCWALK", "XFERWALK", "EGRWALK", "TOTALIVTT",
        "LBDIST", "EBDIST", "LRDIST", "HRDIST", "CRDIST"]
    localivt_skim = get_matrix_data(scenario, period + "_ALLPEN_LBIVTT")
    totalivt_skim = get_matrix_data(scenario, period + "_ALLPEN_TOTALIVTT")
    has_premium = numpy.greater((totalivt_skim - localivt_skim), 0)
    has_both = numpy.greater(localivt_skim, 0) * has_premium
    for skim in skims:
        mat_name = period + "_ALLPEN_" + skim
        data = get_matrix_data(scenario, mat_name)
        set_matrix_data(scenario, mat_name, data * has_both)


def get_matrix_data(scenario, name):
    data = _matrix_cache.get(name)
    if data is None:
        matrix = scenario.emmebank.matrix(name)
        data = matrix.get_numpy_data(scenario)
        _matrix_cache[name] = data
    return data


def set_matrix_data(scenario, name, data):
    matrix = scenario.emmebank.matrix(name)
    _matrix_cache[name] = data
    matrix.set_numpy_data(data, scenario)


def report(scenario, period):
    text = ['<div class="preformat">']
    matrices = get_matrix_names("transit_skims", [period], scenario)
    num_zones = len(scenario.zone_numbers)
    num_cells = num_zones ** 2
    text.append(
        "Number of zones: %s. Number of O-D pairs: %s. "
        "Values outside -9999999, 9999999 are masked in summaries.<br>" % (num_zones, num_cells))
    text.append("%-25s %9s %9s %9s %13s %9s" % ("name", "min", "max", "mean", "sum", "mask num"))
    for name in matrices:
        data = get_matrix_data(scenario, name)
        data = numpy.ma.masked_outside(data, -9999999, 9999999, copy=False)
        stats = (name, data.min(), data.max(), data.mean(), data.sum(), num_cells-data.count())
        text.append("%-25s %9.4g %9.4g %9.4g %13.7g %9d" % stats)
    text.append("</div>")
    title = 'Transit impedance summary for period %s' % period
    report = _m.PageBuilder(title)
    report.wrap_html('Matrix details', "<br>".join(text))
    _m.logbook_write(title, report.render())


# ----------------------------------- Export Matrix Data -------------------------------------------
class OmxMatrix(object):
    def __init__(self, matrix):
        self.matrix = matrix

    def mapping(self, name):
        return self.matrix.mapping(name)

    def list_mappings(self):
        return self.matrix.listMappings()

    def __getitem__(self, key):
        return self.matrix[key]

    def __setitem__(self, key, value):
        self.matrix[key] = value

    def create_mapping(self, name, ids):
        exception_raised = False
        try:
            self.matrix.create_mapping(name, ids) # Emme 44 and above
        except Exception, e:
            exception_raised = True

        if exception_raised:
            self.matrix.createMapping(name, ids) # Emme 437

    def create_matrix(self, key, obj, chunkshape, attrs):
        exception_raised = False
        try: # Emme 44 and above
            self.matrix.create_matrix(
                key,
                obj=obj,
                chunkshape=chunkshape,
                attrs=attrs
            )
        except Exception, e:
            exception_raised = True
        if exception_raised: # Emme 437
            self.matrix.createMatrix(
                key,
                obj=obj,
                chunkshape=chunkshape,
                attrs=attrs
            )

    def close(self):
        self.matrix.close()


class ExportOMX(object):
    def __init__(self, file_path, scenario, omx_key="NAME"):
        self.file_path = file_path
        self.scenario = scenario
        self.emmebank = scenario.emmebank
        self.omx_key = omx_key

    @property
    def omx_key(self):
        return self._omx_key

    @omx_key.setter
    def omx_key(self, omx_key):
        self._omx_key = omx_key
        text_encoding = self.emmebank.text_encoding
        if omx_key == "ID_NAME":
            self.generate_key = lambda m: "%s_%s" % (
                m.id.encode(text_encoding), m.name.encode(text_encoding))
        elif omx_key == "NAME":
            self.generate_key = lambda m: m.name.encode(text_encoding)
        elif omx_key == "ID":
            self.generate_key = lambda m: m.id.encode(text_encoding)

    def __enter__(self):
        self.trace = _m.logbook_trace(name="Export matrices to OMX",
            attributes={
                "file_path": self.file_path, "omx_key": self.omx_key,
                "scenario": self.scenario, "emmebank": self.emmebank.path})
        self.trace.__enter__()
        self.omx_file = _omx.open_file(self.file_path, 'w')
        try:
            self.omx_file.create_mapping('zone_number', self.scenario.zone_numbers)
        except LookupError:
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.omx_file.close()
        self.trace.__exit__(exc_type, exc_val, exc_tb)

    def write_matrices(self, matrices):
        if isinstance(matrices, dict):
            for key, matrix in matrices.iteritems():
                self.write_matrix(matrix, key)
        else:
            for matrix in matrices:
                self.write_matrix(matrix)

    def write_matrix(self, matrix, key=None):
        text_encoding = self.emmebank.text_encoding
        matrix = self.emmebank.matrix(matrix)
        if key is None:
            key = self.generate_key(matrix)
        numpy_array = matrix.get_numpy_data(self.scenario.id)
        if matrix.type == "DESTINATION":
            n_zones = len(numpy_array)
            numpy_array = _numpy.resize(numpy_array, (1, n_zones))
        elif matrix.type == "ORIGIN":
            n_zones = len(numpy_array)
            numpy_array = _numpy.resize(numpy_array, (n_zones, 1))
        attrs = {"description": matrix.description.encode(text_encoding)}
        self.write_array(numpy_array, key, attrs)

    def write_clipped_array(self, numpy_array, key, a_min, a_max=None, attrs={}):
        if a_max is not None:
            numpy_array = numpy_array.clip(a_min, a_max)
        else:
            numpy_array = numpy_array.clip(a_min)
        self.write_array(numpy_array, key, attrs)

    def write_array(self, numpy_array, key, attrs={}):
        shape = numpy_array.shape
        if len(shape) == 2:
            chunkshape = (1, shape[0])
        else:
            chunkshape = None
        attrs["source"] = "Emme"
        numpy_array = numpy_array.astype(dtype="float64", copy=False)
        omx_matrix = self.omx_file.create_matrix(
            key, obj=numpy_array, chunkshape=chunkshape, attrs=attrs)


@_m.logbook_trace("Export transit skims to OMX", save_arguments=True)
def export_matrices_to_omx(omx_file, periods, scenario, big_to_zero=False):
    attributes = {"omx_file": omx_file, "periods": periods, "big_to_zero": big_to_zero}
    # gen_utils.log_snapshot("Export transit skims to OMX", str(self), attributes)
    # init_matrices = _m.Modeller().tool("sandag.initialize.initialize_matrices")
    matrices = get_matrix_names("transit_skims", periods, scenario)
    with ExportOMX(omx_file, scenario, omx_key="NAME") as exporter:
        if big_to_zero:
            emmebank = scenario.emmebank
            for name in matrices:
                matrix = emmebank.matrix(name)
                array = matrix.get_numpy_data(scenario)
                array[array>10E6] = 0
                exporter.write_array(array, exporter.generate_key(matrix))
        else:
            exporter.write_matrices(matrices)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skim an already created Emme transit network.")
    parser.add_argument('-r', '--root', help="path to the root ABM folder, default is the working folder",
                        default=os.path.abspath(os.getcwd()))
    parser.add_argument('-n', '--name', help="the project folder name",
                        default="mtc_emme_3")
    args = parser.parse_args()

    # or connect to already open desktop for debugging
    desktop = connect_to_desktop(port=59673)
    modeller = _m.Modeller(desktop)

    # create modeller instance used to import data to project database
    database_path = os.path.join(args.root, args.name, "Database")
    emmebank_path = os.path.join(database_path, "emmebank")
    emmebank = _eb.Emmebank(emmebank_path)
    scenario = emmebank.scenario(1000)
    network = scenario.get_network()

    initialize_matrices(components=['transit_skims'], periods=['AM'], scenario=scenario, delete_all_existing=True)

    perform_assignment_and_skim(modeller, scenario, period='AM', data_table_name=None, assignment_only=False,
                                    skims_only=True, num_processors="MAX-1")
    # run_transit_assignment()
    # create_transit_skims()
