import inro.modeller as _m
import inro.emme.database.emmebank as _eb
import inro.emme.desktop.app as _app
import inro.emme.core.exception as _except
import inro.emme.desktop.worksheet as _worksheet
import traceback as _traceback
from copy import deepcopy as _copy
from collections import defaultdict as _defaultdict, OrderedDict
import contextlib as _context

from create_emme_network import period_to_scenario_dict

import multiprocessing as _multiprocessing
import argparse as _argparse
import re as _re
import time as _time
import numpy
import os as _os
import json as _json
from copy import deepcopy as _copy


try:
    import openmatrix as _omx
    def open_file(file_path, mode):
        return OmxMatrix(_omx.open_file(file_path, mode))
except Exception, e:
    import omx as _omx
    def open_file(file_path, mode):
        return OmxMatrix(_omx.openFile(file_path, mode))

# _all_periods = ['EV']
_all_periods = ['EA', 'AM', 'MD', 'PM', 'EV']
_all_components = ['transit_skims']
_all_access_modes = ['WLK', 'PNR', 'KNRTNC', 'KNRPRV']
_all_sets = ['set1', 'set2', 'set3']
_set_dict = {
     'BUS': 'set1',
     'PREM': 'set2',
     'ALLPEN': 'set3'}

_hours_in_period = {
    'EA': 3,  # 3:00 to 6:00 AM
    'AM': 3,  # 6:00 to 9:00 AM
    'MD': 6.5,  # 9:00 AM to 3:30 PM
    'PM': 3.5,  # 3:30 PM to 7:00 PM
    'EV': 8,  # 7:00 PM to 3:00 AM
}

# TODO: make global lists tuples
transit_modes = ['b', 'x', 'f', 'l', 'h', 'r']
aux_transit_modes = ['w', 'a', 'e']
_walk_modes = ["a", "w", "e"]
_local_modes = ["b"]
_premium_modes = ['x', 'f', 'l', 'h', 'r']

# initialize matrix variables
# TODO: need a proper cache implementation and invalidation
#       removed for now to make sure it doesn't cause issues with iteration
#_matrix_cache = {}
_matrices = {}
_matrix_count = {}

_segment_cost_function = """
min_seat_weight = 1.0
max_seat_weight = 1.4
power_seat_weight = 2.2
min_stand_weight = 1.4
max_stand_weight = 1.6
power_stand_weight = 3.4

def calc_segment_cost(transit_volume, capacity, segment):
    if transit_volume == 0:
        return 0.0
    line = segment.line
    # need assignment period in seated_capacity calc?
    seated_capacity = line.vehicle.seated_capacity * {0} * 60 / line.headway
    num_seated = min(transit_volume, seated_capacity)
    num_standing = max(transit_volume - seated_capacity, 0)

    vcr = transit_volume / capacity
    crowded_factor = (((
           (min_seat_weight+(max_seat_weight-min_seat_weight)*(transit_volume/capacity)**power_seat_weight)*num_seated
           +(min_stand_weight+(max_stand_weight-min_stand_weight)*(transit_volume/capacity)**power_stand_weight)*num_standing
           )/(transit_volume+0.01)))

    # Toronto implementation limited factor between 1.0 and 10.0
    return crowded_factor
"""

_headway_cost_function = """
max_hdwy_growth = 1.5
max_hdwy = 999.98


def calc_eawt(segment, vcr, headway):
    # EAWT_AM = 0. 259625 + 1. 612019*(1/Headway) + 0.005274*(Arriving V/C) + 0. 591765*(Total Offs Share)
    # EAWT_MD = 0. 24223 + 3.40621* (1/Headway) + 0.02709*(Arriving V/C) + 0. 82747 *(Total Offs Share)
    line = segment.line
    prev_segment = line.segment(segment.number - 1)
    alightings = 0
    total_offs = 0
    all_segs = iter(line.segments(True))
    prev_seg = next(all_segs)
    for seg in all_segs:
        total_offs += prev_seg.transit_volume - seg.transit_volume + seg.transit_boardings
        if seg == segment:
            alightings = total_offs
        prev_seg = seg
    if total_offs < 0.001:
        total_offs = 9999  # added due to divide by zero error
    if headway < .01:
        headway = 9999
    eawt = 0.259625 + 1.612019*(1/headway) + 0.005274*(vcr) + 0.591765*(alightings / total_offs)
    # if mode is LRT / BRT mult eawt * 0.4, if HRT /commuter mult by 0.2
    # use either .mode.id or ["#src_mode"] if fares are used
    mode_char = line{0}
    if mode_char in ["l", "x"]:
        eawt_factor = 0.4
    elif mode_char in ["h", "c", "f"]:
        eawt_factor = 0.2
    else:
        eawt_factor = 1
    return eawt * eawt_factor


def calc_adj_headway(transit_volume, transit_boardings, headway, capacity, segment):
    prev_hdwy = segment["@phdwy"]
    delta_cap = max(capacity - transit_volume + transit_boardings, 0)
    adj_hdwy = min(max_hdwy, prev_hdwy * min((transit_boardings+1) / (delta_cap+1), 1.5))
    adj_hdwy = max(headway, adj_hdwy)
    return adj_hdwy

def calc_headway(transit_volume, transit_boardings, headway, capacity, segment):
    vcr = transit_volume / capacity
    eawt = calc_eawt(segment, vcr, segment.line.headway)
    adj_hdwy = calc_adj_headway(transit_volume, transit_boardings, headway, capacity, segment)
    return adj_hdwy + eawt

"""


def connect_to_desktop(port=59673):
    desktop = _app.connect(port=port)
    return desktop


def start_desktop(root, title="mtc_emme", port=59673):
    emme_project = _os.path.join(root, title, title + ".emp")
    desktop = _app.start(  # will not close desktop when program ends
        project=emme_project, user_initials="RSG", visible=True, port=port)
    return desktop


# ------------------------------------ Initialize matrices -----------------------------------------

# @_m.logbook_trace("Create and initialize matrices", save_arguments=True)
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
        # ("GENCOST",    "total impedance"),
        ("FIRSTWAIT",  "first wait time"),
        ("XFERWAIT",   "transfer wait time"),
        ("TOTALWAIT",  "total wait time"),
        ("FARE",       "fare"),
        ("XFERS",      "num transfers"),
        ("XFERWALK",   "transfer walk time"),
        ("TOTALWALK",  "total walk time"),
        ("TOTALIVTT",  "total in-vehicle time"),
        ("LBIVTT",     "local bus in-vehicle time"),
        ("EBIVTT",     "express bus in-vehicle time"),
        ("LRIVTT",     "light rail in-vehicle time"),
        ("HRIVTT",     "heavy rail in-vehicle time"),
        ("CRIVTT",     "commuter rail in-vehicle time"),
        ("FRIVTT",     "ferry in-vehicle time"),
        ("IN_VEHICLE_COST",    "In vehicle cost"),
        ("LINKREL",     "Link reliability"),
        ("CROWD",       "Crowding penalty"),
        ("EAWT",        "Extra added wait time"),
        ("CAPPEN",      "Capacity penalty"),
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

def create_full_matrix(matrix_name, matrix_description, scenario):
    create_matrix_tool = _m.Modeller().tool("inro.emme.data.matrix.create_matrix")
    matrix = scenario.emmebank.matrix('mf' + matrix_name)
    if matrix is not None:
        matrix_id=matrix.id
    else:
        matrix_id='mf'

    create_matrix_tool(
        matrix_id=matrix_id,
        matrix_name=matrix_name,
        matrix_description=matrix_description,
        overwrite=True,
        default_value=0,
        scenario=scenario)


def create_empty_demand_matrices(period, scenario):
    summed_matrix_name_template = "TRN_{set}_{period}"
    with _m.logbook_trace("Create empty demand matrices for period %s" % period):
        for set_num in _all_sets:
            summed_matrix_name = summed_matrix_name_template.format(period=period, set=set_num)
            create_full_matrix(summed_matrix_name, 'demand summed across access modes', scenario)


def import_demand_matrices(period, scenario, ctramp_output_folder, num_processors="MAX-1"):
    omx_filename_template = "transit_{period}_{access_mode}_TRN_{set}_{period}.omx"
    matrix_name_template = "{access_mode}_TRN_{set}_{period}"
    summed_matrix_name_template = "TRN_{set}_{period}"
    num_processors = parse_num_processors(num_processors)
    import_from_omx_tool = _m.Modeller().tool("inro.emme.data.matrix.import_from_omx")
    matrix_calc_tool = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

    with _m.logbook_trace("Importing demand matrices for period %s" % period):
        for set_num in _all_sets:
            sum_expression = ''
            for access_mode in _all_access_modes:
                omx_filename = omx_filename_template.format(period=period, access_mode=access_mode, set=set_num)
                omx_filename_path = _os.path.join(ctramp_output_folder, omx_filename)
                matrix_name = matrix_name_template.format(period=period, access_mode=access_mode, set=set_num)

                create_full_matrix(matrix_name, omx_filename, scenario)

                import_from_omx_tool(
                    file_path=omx_filename_path,
                    matrices={matrix_name: 'mf' + matrix_name},
                    zone_mapping='NO',
                    scenario=scenario)

                if sum_expression == '':
                    sum_expression = 'mf' + matrix_name
                else:
                    sum_expression = sum_expression + ' + mf' + matrix_name

            # Sum demand accross access modes:
            summed_matrix_name = summed_matrix_name_template.format(period=period, set=set_num)
            create_full_matrix(summed_matrix_name, 'demand summed across access modes', scenario)
            spec = {
                "type": "MATRIX_CALCULATION",
                "constraint": None,
                "result": 'mf' + summed_matrix_name,
                "expression": sum_expression,
            }
            matrix_calc_tool(spec, scenario=scenario, num_processors=num_processors)


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

def perform_assignment_and_skim(modeller, scenario, period, assignment_only=False, num_processors="MAX-1", use_fares=False, use_ccr=False):
    attrs = {
            "period": period,
            "scenario": scenario.id,
            "assignment_only": assignment_only,
            "num_processors": num_processors,
        }
    emmebank = scenario.emmebank

    if not period in _all_periods:
        raise Exception('period: unknown value - specify one of %s' % _all_periods)
    num_processors = parse_num_processors(num_processors)
    params = get_perception_parameters(period)
    network = scenario.get_network()
    # network = scenario.get_partial_network(
    #     element_types=["TRANSIT_LINE", "TRANSIT_SEGMENT"], include_attributes=True)

    with _m.logbook_trace("Transit assignment and skims for period %s" % period):
        run_assignment(modeller, scenario, period, params, network, num_processors, use_fares, use_ccr)

        if not assignment_only:
            with _m.logbook_trace("Skims for Local-only (set1)"):
                run_skims(modeller, scenario, "BUS", period, _local_modes, params, num_processors, network, use_fares, use_ccr)
            with _m.logbook_trace("Skims for Premium-only (set2)"):
                run_skims(modeller, scenario, "PREM", period, _premium_modes, params, num_processors, network, use_fares, use_ccr)
            with _m.logbook_trace("Skims for Local+Premium (set3)"):
                run_skims(modeller, scenario, "ALLPEN", period, _local_modes + _premium_modes, params, num_processors, network, use_fares, use_ccr)
                mask_allpen(scenario, period)
            #report(scenario, period)


# def setup(scenario, attrs):
#     #global _matrix_cache
#     #_matrix_cache = {}  # initialize cache at beginning of run
#     emmebank = scenario.emmebank
#     period = attrs["period"]
#     with _m.logbook_trace("Transit assignment for period %s" % period, attributes=attrs):
#         with temp_matrices(emmebank, "FULL", 3) as matrices:
#             matrices[0].name = "TEMP_IN_VEHICLE_COST"
#             matrices[1].name = "TEMP_LAYOVER_BOARD"
#             matrices[2].name = "TEMP_PERCEIVED_FARE"
#             yield
#             #try:
#             #    yield
#             #finally:
#             #    _matrix_cache = {}  # clear cache at end of run


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


# @_m.logbook_trace("Transit assignment by demand set", save_arguments=True)
def run_assignment(modeller, scenario, period, params, network, num_processors, use_fares=False, use_ccr=False):
    base_spec = {
        "type": "EXTENDED_TRANSIT_ASSIGNMENT",
        "modes": [],
        "demand": "",  # demand matrix specified below
        "waiting_time": {
            "effective_headways": params["init_headway"], "headway_fraction": 0.5,
            "perception_factor": params["init_wait"], "spread_factor": 1.0
        },
        "boarding_cost": {"global": {"penalty": 0, "perception_factor": 1}},
        "boarding_time": {"global": {"penalty": 10, "perception_factor": 1}},
        "in_vehicle_cost": None,
        # "in_vehicle_cost": {"penalty": 0, "perception_factor": 1},
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
        "circular_lines": {"stay": False},
        "connector_to_connector_path_prohibition": None,
        "od_results": {"total_impedance": None},
        "performance_settings": {"number_of_processors": num_processors}
    }
    if use_fares:
        # fare attributes
        fare_perception = 1 / params['vot']
        base_spec["boarding_cost"] = {"on_segments": {"penalty": "@board_cost", "perception_factor": fare_perception}}
        base_spec["in_vehicle_cost"] = {"penalty": "@invehicle_cost", "perception_factor": fare_perception}

        fare_modes = _defaultdict(lambda: set([]))
        for line in network.transit_lines():
            fare_modes[line["#src_mode"]].add(line.mode.id)

        def get_fare_modes(src_modes):
            out_modes = set([])
            for mode in src_modes:
                out_modes.update(fare_modes[mode])
            return list(out_modes)

        local_modes = get_fare_modes(_local_modes)
        premium_modes = get_fare_modes(_premium_modes)
        project_dir = _os.path.dirname(_os.path.dirname(scenario.emmebank.path))
        with open(_os.path.join(project_dir, "Specifications", "%s_BUS_journey_levels.ems" % period), 'r') as f:
            local_journey_levels = _json.load(f)["journey_levels"]
        with open(_os.path.join(project_dir, "Specifications", "%s_PREM_journey_levels.ems" % period), 'r') as f:
            premium_modes_journey_levels = _json.load(f)["journey_levels"]
        with open(_os.path.join(project_dir, "Specifications", "%s_ALLPEN_journey_levels.ems" % period), 'r') as f:
            journey_levels = _json.load(f)["journey_levels"]
        for level in journey_levels:
            if level["boarding_cost"]:
                level["boarding_cost"]["on_segments"]["perception_factor"] = fare_perception
        mode_attr = '["#src_mode"]'
    else:
        local_modes = list(_local_modes)
        premium_modes = list(_premium_modes)
        local_journey_levels = []
        premium_modes_journey_levels = []
        journey_levels = []
        mode_attr = '.mode.id'

    skim_parameters = OrderedDict([
        ("BUS", {
            "modes": _walk_modes + local_modes,
            "journey_levels": local_journey_levels
        }),
        ("PREM", {
            "modes": _walk_modes + premium_modes,
            "journey_levels": premium_modes_journey_levels
        }),
        ("ALLPEN", {
            "modes": _walk_modes + local_modes + premium_modes,
            "journey_levels": journey_levels
        }),
    ])

    if use_ccr:
        assign_transit = modeller.tool(
            "inro.emme.transit_assignment.capacitated_transit_assignment")
        #  assign all 3 classes of demand at the same time
        specs = []
        names = []
        demand_matrix_template = "mfTRN_{set}_{period}"
        for mode_name, parameters in skim_parameters.iteritems():
            spec = _copy(base_spec)
            spec["modes"] = parameters["modes"]
            # name = "%s_%s%s" % (period, a_name, mode_name)
            # demand_matrix = demand_matrix_template.format(
            #     access_mode=a_name, set=_set_dict[mode_name], period=period)
            name = "%s_%s" % (period, mode_name)
            demand_matrix = demand_matrix_template.format(
                set=_set_dict[mode_name], period=period)

            if emmebank.matrix(demand_matrix).get_numpy_data(scenario.id).sum() == 0:
                continue   # don't include if no demand
            spec["demand"] = demand_matrix
            spec["journey_levels"] = parameters["journey_levels"]
            specs.append(spec)
            names.append(name)
        func = {
            "segment": {
                "type": "CUSTOM",
                "python_function": _segment_cost_function.format(_hours_in_period[period]),
                "congestion_attribute": "us3",
                "orig_func": False
            },
            "headway": {
                "type": "CUSTOM",
                "python_function": _headway_cost_function.format(mode_attr),
            },
            "assignment_period": _hours_in_period[period]
        }
        stop = {
            "max_iterations": 3,  # changed from 10 for testing
            "relative_difference": 0.01,
            "percent_segments_over_capacity": 0.01
        }
        assign_transit(specs, congestion_function=func, stopping_criteria=stop, class_names=names, scenario=scenario,
                       log_worksheets=False)
    else:
        assign_transit = modeller.tool(
            "inro.emme.transit_assignment.extended_transit_assignment")
        add_volumes = False
        for mode_name, parameters in skim_parameters.iteritems():
            spec = _copy(base_spec)
            name = "%s_%s" % (period, mode_name)
            spec["modes"] = parameters["modes"]
            #spec["demand"] = 'ms1' # zero demand matrix
            spec["demand"] = "mfTRN_{set}_{period}".format(set=_set_dict[mode_name], period=period)
            # spec['od_results'] = {'total_impedance': 'mf{}_{}_IMPED'.format(period, mode_name)}
            spec["journey_levels"] = parameters["journey_levels"]
            assign_transit(spec, class_name=name, add_volumes=add_volumes, scenario=scenario)
            add_volumes = True


def get_strat_spec(components, matrix_name):
    spec = {
        "trip_components": components,
        "sub_path_combination_operator": "+",
        "sub_strategy_combination_operator": "average",
        "selected_demand_and_transit_volumes": {
            "sub_strategies_to_retain": "ALL",
            "selection_threshold": {"lower": -999999, "upper": 999999}
        },
        "analyzed_demand": None,
        "constraint": None,
        "results": {"strategy_values": matrix_name},
        "type": "EXTENDED_TRANSIT_STRATEGY_ANALYSIS"
    }
    return spec


# @_m.logbook_trace("Extract skims", save_arguments=True)
def run_skims(modeller, scenario, name, period, valid_modes, params, num_processors, network, use_fares=False, use_ccr=False):
    emmebank = scenario.emmebank
    matrix_calc = modeller.tool(
        "inro.emme.matrix_calculation.matrix_calculator")
    network_calc = modeller.tool(
        "inro.emme.network_calculation.network_calculator")
    create_extra = modeller.tool(
        "inro.emme.data.extra_attribute.create_extra_attribute")
    matrix_results = modeller.tool(
        "inro.emme.transit_assignment.extended.matrix_results")
    path_analysis = modeller.tool(
        "inro.emme.transit_assignment.extended.path_based_analysis")
    strategy_analysis = modeller.tool(
        "inro.emme.transit_assignment.extended.strategy_based_analysis")

    class_name = "%s_%s" % (period, name)
    skim_name = "%s_%s" % (period, name)
    # self.run_skims.logbook_cursor.write(name="Extract skims for %s, using assignment class %s" % (name, class_name))

    with _m.logbook_trace("First and total wait time, number of boardings, fares, total walk time"):
        # First and total wait time, number of boardings, fares, total walk time, in-vehicle time
        spec = {
            "type": "EXTENDED_TRANSIT_MATRIX_RESULTS",
            "actual_first_waiting_times": 'mf"%s_FIRSTWAIT"' % skim_name,
            "actual_total_waiting_times": 'mf"%s_TOTALWAIT"' % skim_name,
            # "total_impedance": 'mf"%s_GENCOST"' % skim_name,
            "by_mode_subset": {
                "modes": [m.id for m in network.modes() if m.type in ["TRANSIT", "AUX_TRANSIT"]],
                "avg_boardings": 'mf"%s_XFERS"' % skim_name,
                #"actual_in_vehicle_times": 'mf"%s_TOTALIVTT"' % skim_name,
                "actual_aux_transit_times": 'mf"%s_TOTALWALK"' % skim_name,
            },
        }
        if use_fares:
            spec["by_mode_subset"]["actual_in_vehicle_costs"] = 'mf"%s_IN_VEHICLE_COST"' % skim_name
            spec["by_mode_subset"]["actual_total_boarding_costs"] = 'mf"%s_FARE"' % skim_name
        matrix_results(spec, class_name=class_name, scenario=scenario, num_processors=num_processors)

    with _m.logbook_trace("In-vehicle time by mode"):
        mode_combinations = [
            ("LB", 'b'),
            ("EB", 'x'),
            ("FR", 'f'),
            ("LR", 'l'),
            ("HR", 'h'),
            ("CR", 'r'),
        ]
        # map to used modes in apply fares case
        fare_modes = _defaultdict(lambda: set([]))
        if use_fares:
            for line in network.transit_lines():
                fare_modes[line["#src_mode"]].add(line.mode.id)
        else:
            fare_modes = dict((m, [m]) for m in valid_modes)
        # set to fare_modes and filter out unused modes
        mode_combinations = [(n, list(fare_modes[m])) for n, m  in mode_combinations if m in valid_modes]

        total_ivtt_expr = []
        if use_ccr:
            scenario.create_extra_attribute("TRANSIT_SEGMENT", "@mode_timtr")
            try:
                for mode_name, modes in mode_combinations:
                    network.create_attribute("TRANSIT_SEGMENT", "@mode_timtr")
                    for line in network.transit_lines():
                        if line.mode.id in modes:
                            for segment in line.segments():
                                # segment["@mode_timtr"] = segment["@base_timtr"]
                                # segment["@mode_timtr"] = segment["@trantime_final"]
                                segment["@mode_timtr"] = segment["@timtr"]
                    mode_timtr = network.get_attribute_values("TRANSIT_SEGMENT", ["@mode_timtr"])
                    network.delete_attribute("TRANSIT_SEGMENT", "@mode_timtr")
                    scenario.set_attribute_values("TRANSIT_SEGMENT", ["@mode_timtr"], mode_timtr)
                    ivtt = 'mf"%s_%sIVTT"' % (skim_name, mode_name)
                    total_ivtt_expr.append(ivtt)
                    spec = get_strat_spec({"in_vehicle": "@mode_timtr"}, ivtt)
                    strategy_analysis(spec, class_name=class_name, scenario=scenario, num_processors=num_processors)
            finally:
                scenario.delete_extra_attribute("@mode_timtr")
        else:
            for mode_name, modes in mode_combinations:
                ivtt = 'mf"%s_%sIVTT"' % (skim_name, mode_name)
                total_ivtt_expr.append(ivtt)
                spec = {
                    "type": "EXTENDED_TRANSIT_MATRIX_RESULTS",
                    "by_mode_subset": {"modes": modes, "actual_in_vehicle_times": ivtt},
                }
                matrix_results(spec, class_name=class_name, scenario=scenario, num_processors=num_processors)

    with _m.logbook_trace("Calculate total IVTT, number of transfers, transfer walk and wait times"):
        spec_list = [
            {   # sum total ivtt across all modes
                "type": "MATRIX_CALCULATION",
                "constraint": None,
                "result": 'mf"%s_TOTALIVTT"' % skim_name,
                "expression": "+".join(total_ivtt_expr),
            },
            {   # convert number of boardings to number of transfers
                "type": "MATRIX_CALCULATION",
                "constraint":{
                    "by_value": {
                        "od_values": 'mf"%s_XFERS"' % skim_name,
                        "interval_min": 0, "interval_max": 9999999,
                        "condition": "INCLUDE"},
                },
                "result": 'mf"%s_XFERS"' % skim_name,
                "expression": '(%s_XFERS - 1).max.0' % skim_name,
            },
            {   # transfer walk time = total - access - egress
                "type": "MATRIX_CALCULATION",
                "constraint": None,
                "result": 'mf"%s_XFERWALK"' % skim_name,
                "expression": '({name}_TOTALWALK - 0.66).max.0'.format(name=skim_name),
            },
            {
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
        ]
        if use_fares:
            spec_list.append(
                {   # sum in-vehicle cost and boarding cost to get the fare paid
                    "type": "MATRIX_CALCULATION",
                    "constraint": None,
                    "result": 'mf"%s_FARE"' % skim_name,
                    "expression": '(%s_FARE + %s_IN_VEHICLE_COST)' % (skim_name, skim_name),
                })
        matrix_calc(spec_list, scenario=scenario, num_processors=num_processors)

    if use_ccr:
        with _m.logbook_trace("Calculate CCR skims"):
            # TODO: factor this to run once ...
            create_extra("TRANSIT_SEGMENT", "@eawt", "extra added wait time", overwrite=True, scenario=scenario)
            # create_extra("TRANSIT_SEGMENT", "@crowding_factor", "crowding factor along segments", overwrite=True, scenario=scenario)
            create_extra("TRANSIT_SEGMENT", "@capacity_penalty", "capacity penalty at boarding", overwrite=True, scenario=scenario)
            network = scenario.get_partial_network(["TRANSIT_LINE", "TRANSIT_SEGMENT"], include_attributes=True)
            attr_map = {
                "TRANSIT_SEGMENT": ["@phdwy", "transit_volume", "transit_boardings"],
                "TRANSIT_VEHICLE": ["seated_capacity", "total_capacity"],
                "TRANSIT_LINE": ["headway"],
            }
            if use_fares:
                # only if use_fares, otherwise will use .mode.id
                attr_map["TRANSIT_LINE"].append("#src_mode")
                mode_name = '["#src_mode"]'
            else:
                mode_name = '.mode.id'
            for domain, attrs in attr_map.items():
                values = scenario.get_attribute_values(domain, attrs)
                network.set_attribute_values(domain, attrs, values)

            enclosing_scope = {"network": network, "scenario": scenario}
            # code = compile(_segment_cost_function, "segment_cost_function", "exec")
            # exec(code, enclosing_scope)
            code = compile(_headway_cost_function.format(mode_name), "headway_cost_function", "exec")
            exec(code, enclosing_scope)
            calc_eawt = enclosing_scope["calc_eawt"]
            hdwy_fraction = 0.5 # fixed in assignment spec

            # NOTE: assume assignment period is 1 hour
            for segment in network.transit_segments():
                headway = segment.line.headway
                veh_cap = line.vehicle.total_capacity
                # capacity = 60.0 * veh_cap / line.headway
                capacity = 60.0 * _hours_in_period[period] * veh_cap / line.headway
                transit_volume = segment.transit_volume
                vcr = transit_volume / capacity
                segment["@eawt"] = calc_eawt(segment, vcr, headway)
                # segment["@crowding_penalty"] = calc_segment_cost(transit_volume, capacity, segment)
                segment["@capacity_penalty"] = max(segment["@phdwy"] - segment["@eawt"] - headway, 0) * hdwy_fraction

            values = network.get_attribute_values('TRANSIT_SEGMENT', ["@eawt", "@capacity_penalty"])
            scenario.set_attribute_values('TRANSIT_SEGMENT', ["@eawt", "@capacity_penalty"], values)

            # # Link unreliability
            # spec = get_strat_spec({"in_vehicle": "ul1"}, "%s_LINKREL" % skim_name)
            # strategy_analysis(spec, class_name=class_name, scenario=scenario, num_processors=num_processors)

            # Crowding penalty
            spec = get_strat_spec({"in_vehicle": "@ccost"}, "%s_CROWD" % skim_name)
            strategy_analysis(spec, class_name=class_name, scenario=scenario, num_processors=num_processors)

            # skim node reliability, Extra added wait time (EAWT)
            spec = get_strat_spec({"boarding": "@eawt"}, "%s_EAWT" % skim_name)
            strategy_analysis(spec, class_name=class_name, scenario=scenario, num_processors=num_processors)

            # skim capacity penalty
            spec = get_strat_spec({"boarding": "@capacity_penalty"}, "%s_CAPPEN" % skim_name)
            strategy_analysis(spec, class_name=class_name, scenario=scenario, num_processors=num_processors)

    return


def save_per_iteration_flows(scenario):
    strat_data = scenario.transit_strategies.data
    strat_data["analyze_individual_slices"] = True
    try:
        scenario.transit_strategies.data = strat_data
        create_attr = modeller.tool(
            "inro.emme.data.extra_attribute.create_extra_attribute")
        network_results = modeller.tool(
            "inro.emme.transit_assignment.extended.network_results")

        for strat in scenario.transit_strategies.strat_files():
            print strat.name
            _, num, class_name = strat.name.split()
            attr_name = ("@%s_it%s" % (class_name, num)).lower()
            create_attr("TRANSIT_SEGMENT", attr_name, scenario=scenario, overwrite=True)
            spec = {
                "type": "EXTENDED_TRANSIT_NETWORK_RESULTS",
                "on_segments": {"transit_volumes": attr_name},
            }
            network_results(spec, scenario=scenario, class_name=strat.name)
    finally:
        del strat_data["analyze_individual_slices"]
        scenario.transit_strategies.data = strat_data


def mask_allpen(scenario, period):
    # Reset skims to 0 if not both local and premium
    skims = [
        "FIRSTWAIT", "TOTALWAIT", "XFERS", "TOTALWALK",
        "LBIVTT", "EBIVTT", "LRIVTT", "HRIVTT", "CRIVTT", "FRIVTT",
        "XFERWAIT", "FARE",
        "XFERWALK", "TOTALIVTT",
        "LINKREL", "CROWD", "EAWT", "CAPPEN"]
    localivt_skim = get_matrix_data(scenario, period + "_ALLPEN_LBIVTT")
    totalivt_skim = get_matrix_data(scenario, period + "_ALLPEN_TOTALIVTT")
    has_premium = numpy.greater((totalivt_skim - localivt_skim), 0)
    has_both = numpy.greater(localivt_skim, 0) * has_premium
    for skim in skims:
        mat_name = period + "_ALLPEN_" + skim
        data = get_matrix_data(scenario, mat_name)
        set_matrix_data(scenario, mat_name, data * has_both)


def mask_transfers(scenario, period, max_transfers=3):
    # Reset skims to 0 if number of transfers is greater than max_transfers
    skims = [
        "FIRSTWAIT", "TOTALWAIT", "XFERS", "TOTALWALK",
        "LBIVTT", "EBIVTT", "LRIVTT", "HRIVTT", "CRIVTT", "FRIVTT",
        "XFERWAIT", "FARE",
        "XFERWALK", "TOTALIVTT",
        "LINKREL", "CROWD", "EAWT", "CAPPEN"]

    for set in ['_BUS_', '_PREM_', '_ALLPEN_']:
        xfers = get_matrix_data(scenario, period + set + "XFERS")
        xfer_mask = numpy.less_equal(xfers, max_transfers)
        for skim in skims:
            mat_name = period + set + skim
            data = get_matrix_data(scenario, mat_name)
            set_matrix_data(scenario, mat_name, data * xfer_mask)


def get_matrix_data(scenario, name):
    # data = _matrix_cache.get(name)
    # if data is None:
    matrix = scenario.emmebank.matrix(name)
    if matrix is None:
        raise Exception("No matrix with name %s" % name)
    return matrix.get_numpy_data(scenario.id)
    #_matrix_cache[name] = data
    # return data


def set_matrix_data(scenario, name, data):
    matrix = scenario.emmebank.matrix(name)
    #_matrix_cache[name] = data
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


# @_m.logbook_trace("Export transit skims to OMX", save_arguments=True)
def export_matrices_to_omx(omx_file, periods, scenario, big_to_zero=False, max_transfers=None):
    attributes = {"omx_file": omx_file, "periods": periods, "big_to_zero": big_to_zero}
    if max_transfers is not None:
        for period in periods:
            mask_transfers(scenario, period, max_transfers=max_transfers)
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


def export_boardings_by_line(desktop, output_transit_boardings_file):
    project = desktop.project
    table = project.new_network_table("TRANSIT_LINE")
    column = _worksheet.Column()

    # Creating total boardings by line table
    column.expression = "line"
    column.name = "line_name"
    table.add_column(0, column)

    column.expression = "description"
    column.name = "description"
    table.add_column(1, column)

    column.expression = "ca_board_t"
    column.name = "total_boardings"
    table.add_column(2, column)

    column.expression = "#src_mode"
    column.name = "mode"
    table.add_column(3, column)

    column.expression = "@line_mode"
    column.name = "line_mode"
    table.add_column(4, column)

    table.export(output_transit_boardings_file)
    table.close()


if __name__ == "__main__":
    parser = _argparse.ArgumentParser(description="Skim an already created Emme transit network.")
    parser.add_argument('-p', '--trn_path', help=r"path to the trn folder, default is the current_working_folder\trn",
                        default=_os.path.join(_os.getcwd(), 'trn'))
    parser.add_argument('-s', '--skims_path', help=r"path to the skims folder, default is the current_working_folder\skims",
                        default=_os.path.join(_os.getcwd(), 'skims'))
    parser.add_argument('-i', '--first_iteration', help='Is this the first iteration? yes or no, default is yes', default='yes')
    parser.add_argument('--save_iter_flows', action="store_true", help='Save per-iteration flows in scenarios', default=False)
    parser.add_argument('-t', '--time_periods', help='List of time periods as EA,AM,MD,PM,EV or ALL', default='ALL')
    parser.add_argument('-o', '--port', help='Port to connect to Emme desktop session', default=59673, type=int)
    parser.add_argument('-d', '--skip_import_demand', action="store_true", help='Skip import of CT-RAMP demand')
    parser.add_argument('-n', '--num_processors', help='Number of processors to use, can specify MAX-#', default='MAX-4')

    args = parser.parse_args()
    assert (args.first_iteration == 'yes') or (args.first_iteration == 'no'), \
        'Please specify "yes" or "no" for the first_iteration (-i) run-time argument'
    if args.time_periods == "ALL":
        time_periods = _all_periods[:]
    else:
        time_periods = args.time_periods.split(",")

    # connect to already open desktop
    try:
        desktop = connect_to_desktop(port=args.port)
    except:
        desktop = start_desktop(args.trn_path, port=args.port)
    modeller = _m.Modeller(desktop)
    emmebank = modeller.emmebank
    for period in time_periods:
        scenario_id = period_to_scenario_dict[period]
        scenario = emmebank.scenario(scenario_id)

        initialize_matrices(components=['transit_skims'], periods=[period], scenario=scenario, delete_all_existing=False)

        ctramp_output_folder = _os.path.join(_os.getcwd(), 'ctramp_output')
        if not args.skip_import_demand:
            import_demand_matrices(period, scenario, ctramp_output_folder, num_processors=args.num_processors)
        else:
            create_empty_demand_matrices(period, scenario)

        # Only run ccr assignment if not first run and period in ['AM', 'PM']
        # if args.first_iteration == 'no' and period in ['AM', 'PM']:
        #     use_ccr = True
        #     # read in demand matrices for ccr-assignment
        #     ctramp_output_folder = _os.path.join(_os.getcwd(), 'ctramp_output')
        #     import_demand_matrices(period, scenario, ctramp_output_folder, num_processors="MAX-4")
        # else:
        #     use_ccr = False
        use_ccr = False

        perform_assignment_and_skim(modeller, scenario, period=period, assignment_only=False,
                                    num_processors=args.num_processors, use_fares=True, use_ccr=use_ccr)
        output_omx_file = _os.path.join(args.skims_path, "transit_skims_{}.omx".format(period))
        export_matrices_to_omx(omx_file=output_omx_file, periods=[period], scenario=scenario,
                               big_to_zero=True, max_transfers=3)

        if use_ccr and args.save_iter_flows:
            save_per_iteration_flows(scenario)
        output_transit_boardings = False
        if output_transit_boardings:
            desktop.data_explorer().replace_primary_scenario(scenario)
            output_transit_boardings_file = _os.path.join(args.trn_path, "boardings_by_line_{}.csv".format(period))
            export_boardings_by_line(desktop, output_transit_boardings_file)
