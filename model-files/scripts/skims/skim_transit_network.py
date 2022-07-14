"""
skim_transit_network.py

This script performs transit skimming and assignment for MTC TM2.  Output skims
are in OMX format and are used as input into the CT-RAMP model.  Skimming and assignment
is done with the Emme networks created in create_emme_network.py with options to include
demand matrices from prior CT-RAMP runs.

Usage: %EMME_PYTHON_PATH%\python skim_transit_network.py
    Note that the Emme python must be used to have access to the Emme API

    [-p, --trn_path]: path to the trn folder, default is the
        current_working_folder\trn
    [-s, --skims_path]: path to the skims folder, default is the
        current_working_folder\skims
    [-c, --ccr_periods]: List of time periods to run CCR as EA,AM,MD,PM,EV or ALL
    [--save_iter_flows]: Save per-iteration flows in scenario
    [-t, --time_periods]: List of time periods as EA,AM,MD,PM,EV or
        ALL, default is ALL
    [-o, --port]: Port to connect to Emme desktop session, default
        is 59673
    [-d, --skip_import_demand]: Skip import of CT-RAMP demand
    [-b, --output_transit_boardings]: Output transit boardings from assignment
    [-n, --num_processor]: Number of processors to use, can specify MAX-#, default
        is MAX-4

Date: Oct, 2021
Contacts: david.hensle@rsginc.com, kevin@inrosoftware.com
"""
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
except Exception as e:
    import omx as _omx
    def open_file(file_path, mode):
        return OmxMatrix(_omx.openFile(file_path, mode))

# _all_periods = ['AM']
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
    'AM': 4,  # 6:00 to 10:00 AM
    'MD': 5,  # 10:00 AM to 3:00 PM
    'PM': 4,  # 3:00 PM to 7:00 PM
    'EV': 8,  # 7:00 PM to 3:00 AM
}

# number of trips in the peak hour / avg number of trips per hour in period
# factor of 1 means no adjustment
_vcr_adjustment_factor = {
    'EA': 1,
    'AM': 1.219,
    'MD': 1,
    'PM': 1.262,
    'EV': 1,
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
values = scenario.get_attribute_values("TRANSIT_VEHICLE", ["seated_capacity"])
network.set_attribute_values("TRANSIT_VEHICLE", ["seated_capacity"], values)

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
    # capacity adjusted for full time period
    seated_capacity = line.vehicle.seated_capacity * {0} * 60 / line.headway
    # volume is adjusted to reflect peak period
    adj_transit_volume = transit_volume * {1}
    num_seated = min(adj_transit_volume, seated_capacity)
    num_standing = max(adj_transit_volume - seated_capacity, 0)

    # adjusting transit volume to account for peak period spreading
    vcr = adj_transit_volume / capacity
    crowded_factor = (((
           (min_seat_weight+(max_seat_weight-min_seat_weight)*(vcr)**power_seat_weight)*num_seated
           +(min_stand_weight+(max_stand_weight-min_stand_weight)*(vcr)**power_stand_weight)*num_standing
           )/(adj_transit_volume+0.01)))

    # Toronto implementation limited factor between 1.0 and 10.0

    # subtracting 1 from factor since new transit times are calculated as:
    #  trtime_new = trtime_old * (1 + crowded_factor), but Toronto was derived
    #  using trtime_new = trtime_old * (crowded_factor)
    #  (see https://app.asana.com/0/0/1185777482487173/1202006990557038/f)
    crowded_factor = max(crowded_factor - 1, 0)
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
    # multipying vcr by peak period factor
    vcr = transit_volume / capacity * {1}
    eawt = calc_eawt(segment, vcr, segment.line.headway)
    adj_hdwy = calc_adj_headway(transit_volume, transit_boardings, headway, capacity, segment)
    return adj_hdwy + eawt

"""


def connect_to_desktop(port=59673):
    """
    Fetches the Emme desktop object for an already open project. This is a useful
    method when testing a single step or two and you don't want to re-create the entire project.

    Parameters:
        - port: int of the Emme port.  You can find it in Emme under
            tools -> Model Applications -> Advanced
    Returns:
        - Emme desktop object from the specified port
    """
    print("connecting to Emme desktop via port:", port)
    desktop = _app.connect(port=port)
    return desktop


def start_desktop(root, title="emme_full_run", port=59673):
    """
    Open an emme desktop from the specified emme project folder location

    Parameters:
        - root: str folder location of Emme project
        - title: str name of Emme project folder
        - port: int port number to open the desktop on
    Returns:
        - Emme desktop object
    """
    emme_project = _os.path.join(root, title, title + ".emp")
    print("emme_project: {}".format(emme_project))
    desktop = _app.start(  # will not close desktop when program ends
        project=emme_project, user_initials="RSG", visible=True, port=port)
    return desktop


# ------------------------------------ Initialize matrices -----------------------------------------

# @_m.logbook_trace("Create and initialize matrices", save_arguments=True)
def initialize_matrices(components, periods, scenario, delete_all_existing=False):
    """
    Determines all necessary matrix names and creates them in emme database

    Parameters:
        - components: list of str, components to create matrices for
        - periods: list of str, time of day periods to create matrices for
        - scenario: emme scenario to create matrices in
        - delete_all_existing: boolean, if True will delete all existing matrices
            before initializing new matrices
    Returns:
        - list of Emme matrices created
    """
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
    """
    Creates the matrices in the emme databank for the given scenario

    Parameters:
        - component: str component label for matrix list
        - periods: list of str, time of day periods to create matrices for
        - scenario: emme scenario to create matrices in
        - create_matrix_tool: instance of the emme create_matrix modeller tool
    Returns:
        - list of Emme matrix names created
    """
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
    """
    creates a list of matrix names that need to be initialized in the current scenario

    Parameters:
        - scenario: Emme scenario to create the matrices in
    Returns:
        - Dictionary of matrix names and options to be passed to emme create_matrix tool
    """
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
    """
    Returns a list of emme matrix names created for given scenario

    Parameters:
        - component: str component label for matrix list
        - periods: list of str of time of day periods
        - scenario: active Emme scenario objct
    """
    generate_matrix_list(scenario)
    matrices = []
    for period in periods:
        matrices.extend([m[1] for m in _matrices[component][period]])
    return matrices


def add_matrices(component, period, matrices):
    """
    Fills the maxtrix names and count global variables specifying the created matrices

    Parameters:
        - component: str component label for matrix list
        - period: str of time of day period
        - matrices: list of matrix types, names, and descriptions
    Returns:
        - None
    """
    for ident, name, desc in matrices:
        _matrices[component][period].append([ident+str(_matrix_count[ident]), name, desc])
        _matrix_count[ident] += 1


def get_transit_skims():
    """
    List of transit matrices that will be filled when performing transit skimming

    Parameters:
        - None
    Returns:
        - multi-dimensional list of matrix names and options for creation
    """
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
        # ("STPLATTIME",  "Station platform time"),
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
    """
    Creates one full Emme matrix in the current scenario

    Parameters:
        - matrix_name: str name of Emme matrix that will be created
        - matrix_description: str description of matrix
        - scenario: Emme scenario to create matrix in
    Returns:
        - None
    """
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
    """
    Creates demand matrices that have zero in all fields that are used in assignment
    when no demand matrices yet exist or you do not want to use them.

    Parameters:
        - period: str of time-of-day period
        - scenario: Emme scenario to create empty matrices in
    """
    summed_matrix_name_template = "TRN_{set}_{period}"
    with _m.logbook_trace("Create empty demand matrices for period %s" % period):
        for set_num in _all_sets:
            summed_matrix_name = summed_matrix_name_template.format(period=period, set=set_num)
            create_full_matrix(summed_matrix_name, 'demand summed across access modes', scenario)


def import_demand_matrices(period, scenario, ctramp_output_folder, num_processors="MAX-1", msa_iteration=1):
    """
    Imports the TAP-to-TAP transit demand matrices created from CT-RAMP by time of day,
    access mode, and transit set type (local, premium, local+premium).  Demand matrices
    are then assigned to transit network

    Parameters:
        - period: str denoting time of day period
        - scenario: Emme scenario object to import demand matrices into
        - ctramp_output_folder: str folder location containing demand matrices
        - num_processors: Number of processors that can be used in matrix calculations
    Returns:
        - None
    """
    omx_filename_template = "transit_{period}_{access_mode}_TRN_{set}_{period}.omx"
    matrix_name_template = "{access_mode}_TRN_{set}_{period}"
    summed_matrix_name_template = "TRN_{set}_{period}"
    num_processors = parse_num_processors(num_processors)
    import_from_omx_tool = _m.Modeller().tool("inro.emme.data.matrix.import_from_omx")
    matrix_calc_tool = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

    with _m.logbook_trace("Importing demand matrices for period %s" % period):
        for set_num in _all_sets:
            matrix_names = []
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
                matrix_names.append(matrix_name)
            sum_expression =  ' + mf'.join(matrix_names)

            # Sum demand accross access modes:
            summed_matrix_name = summed_matrix_name_template.format(period=period, set=set_num)
            if msa_iteration == 1:
                create_full_matrix(summed_matrix_name, 'demand summed across access modes', scenario)
            else:
                sum_expression = "{prev_demand} + (1.0 / {msa}) * (({demand}) - ({prev_demand}))".format(
                    prev_demand=summed_matrix_name, msa=msa_iteration, demand=sum_expression)
            spec = {
                "type": "MATRIX_CALCULATION",
                "constraint": None,
                "result": 'mf' + summed_matrix_name,
                "expression": sum_expression,
            }
            matrix_calc_tool(spec, scenario=scenario, num_processors=num_processors)


def parse_num_processors(value):
    """
    Return an int for the number of processors to use for a given task. Input value
    can include the MAX keywork for number of processors and an expression to use a
    certain number less than the MAX.  For example, if on a mahcine with 24 cores,
    a value of "MAX-4" would return 20 processors.

    Parameters:
        - value: str or int of processors to use
    Returns:
        - int for number of processors to use
    """
    max_processors = _multiprocessing.cpu_count()
    if isinstance(value, int):
        return value
    if isinstance(value, str):
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
    """
    Calls methods to perform transit assignment and transit skimming for network
    created in the create_emme_network.py script.

    Parameters:
        - modeller: emme modeller instance
        - scenario: Emme scenario containing network to assign and skim and
            matrices to fill
        - period: str of time of day period
        - assignment_only: boolean, if True, no skimming will be performed
        - num_processor: str or int to define number of processors to use
        - use_fars: boolean, if True will create journey levels to handle transfers
            and skim fares
        - use_ccr: boolean, if True will use transit crowding and capacity restraint
            penalties in assignemnt
    Returns:
        - None
    """
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
        # run_assignment(modeller, scenario, period, params, network, num_processors, use_fares, use_ccr)
        network = scenario.get_network()

        if not assignment_only:
            with _m.logbook_trace("Skims for Local-only (set1)"):
                run_skims(modeller, scenario, "BUS", period, _local_modes, params, num_processors, network, use_fares, use_ccr)
            with _m.logbook_trace("Skims for Premium-only (set2)"):
                run_skims(modeller, scenario, "PREM", period, _premium_modes, params, num_processors, network, use_fares, use_ccr)
            with _m.logbook_trace("Skims for Local+Premium (set3)"):
                run_skims(modeller, scenario, "ALLPEN", period, _local_modes + _premium_modes, params, num_processors, network, use_fares, use_ccr)
                mask_allpen(scenario, period)
            #report(scenario, period)


def get_perception_parameters(period):
    """
    Perception parameters to calculate assignment variables and utilities.
    Parameters can differ by time of day

    Parameters:
        - period: str time of day period to get perception parameters for
    Returns:
        - dict of perception parameters for selected period
    """
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
    """
    Assigns demand to the transit network. Has the option to use fares and/or
    transit crowding and capacity restraint.  Assignment is split into three sets:
    local (bus), premium (express bus, rail, ferry), and local+premium with a transfer.

    Parameters:
        - modeller: emme modeller instance
        - scenario: Emme scenario containing network to assign and skim and
            matrices to fill
        - period: str of time of day period
        - params: dict of perception parameter names and values
        - network: emme network object to assign demand to
        - num_processor: str or int to define number of processors to use
        - use_fars: boolean, if True will create journey levels to handle transfers
            and skim fares
        - use_ccr: boolean, if True will use transit crowding and capacity restraint
            penalties in assignemnt
    Returns:
        - None
    """
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
        for (mode_name, parameters) in skim_parameters.items():
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
                "python_function": _segment_cost_function.format(_hours_in_period[period], _vcr_adjustment_factor[period]),
                "congestion_attribute": "us3",
                "orig_func": False
            },
            "headway": {
                "type": "CUSTOM",
                "python_function": _headway_cost_function.format(mode_attr, _vcr_adjustment_factor[period]),
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
        for (mode_name, parameters) in skim_parameters.items():
            spec = _copy(base_spec)
            name = "%s_%s" % (period, mode_name)
            spec["modes"] = parameters["modes"]
            #spec["demand"] = 'ms1' # zero demand matrix
            spec["demand"] = "mfTRN_{set}_{period}".format(set=_set_dict[mode_name], period=period)
            # spec['od_results'] = {'total_impedance': 'mf{}_{}_IMPED'.format(period, mode_name)}
            spec["journey_levels"] = parameters["journey_levels"]
            print("Running assign_transit with spec={} class_name={} add_volumes={} scenario={}".format(spec, name, add_volumes, scenario))
            assign_transit(spec, class_name=name, add_volumes=add_volumes, scenario=scenario)
            add_volumes = True


def get_strat_spec(components, matrix_name):
    """
    Retrieve the default specification template for strategy analysis in Emme.

    Parameters:
        - components: trip components to skim and the variable to sum. trip component
            options are: "boading", "in-vehicle", "alighting", and "aux_transit"
        - matrix_name: name of the matrix that should contain the skim
    Returns:
        - dictionary of the strategy specification
    """
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
    """
    Performs the transit skimming from the transit assignment results

    Parameters:
        - modeller: emme modeller instance
        - scenario: Emme scenario containing network to assign and skim and
            matrices to fill
        - name: str of assignment set type. Options are local: "BUS", premium: "PREM",
            and local+premium: "ALLPEN"
        - period: str of time of day period
        - valid_modes: list of emme modes that are allowed in the set type
        - params: dict of perception parameter names and values
        - network: emme network object to assign demand to
        - num_processor: str or int to define number of processors to use
        - use_fars: boolean, if True will skim transit fare attributes
        - use_ccr: boolean, if True will add crowding penalty to in vehicle times
    Returns:
        - None
    """
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
                                # segment["@mode_timtr"] = segment['transit_time']
                                segment["@mode_timtr"] = segment['transit_time'] - segment['@ccost']
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
            {   # transfer walk time = total - access - egress,
                # no longer correct if station attributes are included!  access / egress time at station != 0.66
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
            create_extra("TRANSIT_SEGMENT", "@seg_rel", "link reliability on transit segment", overwrite=True, scenario=scenario)
            # create_extra("TRANSIT_SEGMENT", "@crowding_factor", "crowding factor along segments", overwrite=True, scenario=scenario)
            create_extra("TRANSIT_SEGMENT", "@capacity_penalty", "capacity penalty at boarding", overwrite=True, scenario=scenario)
            create_extra("TRANSIT_SEGMENT", "@tot_capacity", "total capacity", overwrite=True, scenario=scenario)
            create_extra("TRANSIT_SEGMENT", "@seated_capacity", "seated capacity", overwrite=True, scenario=scenario)
            create_extra("TRANSIT_SEGMENT", "@tot_vcr", "volume to total capacity ratio", overwrite=True, scenario=scenario)
            create_extra("TRANSIT_SEGMENT", "@seated_vcr", "volume to seated capacity ratio", overwrite=True, scenario=scenario)
            create_extra("TRANSIT_SEGMENT", "@ccost_skim", "copy of ccost used for skimming", overwrite=True, scenario=scenario)
            network = scenario.get_partial_network(["TRANSIT_LINE", "TRANSIT_SEGMENT"], include_attributes=True)
            attr_map = {
                "TRANSIT_SEGMENT": ["@phdwy", "transit_volume", "transit_boardings", "@capacity_penalty",
                                    "@tot_capacity", "@seated_capacity", "@tot_vcr", "@seated_vcr", '@seg_rel',
                                    "@base_timtr", "@eawt", "@ccost_skim"],
                "TRANSIT_VEHICLE": ["seated_capacity", "total_capacity"],
                "TRANSIT_LINE": ["headway"],
                "LINK": ["data3"],
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
            code = compile(_headway_cost_function.format(mode_name, _vcr_adjustment_factor[period]), "headway_cost_function", "exec")
            exec(code, enclosing_scope)
            calc_eawt = enclosing_scope["calc_eawt"]
            hdwy_fraction = 0.5 # fixed in assignment spec

            for segment in network.transit_segments():
                line = segment.line
                headway = line.headway
                veh_cap = line.vehicle.total_capacity
                seated_veh_cap = line.vehicle.seated_capacity
                # capacity = 60.0 * veh_cap / line.headway
                capacity = 60.0 * _hours_in_period[period] * veh_cap / line.headway
                seated_capacity = 60.0 * _hours_in_period[period] * seated_veh_cap / line.headway
                transit_volume = segment.transit_volume
                vcr = transit_volume / capacity * _vcr_adjustment_factor[period]
                seated_vcr = transit_volume / seated_capacity * _vcr_adjustment_factor[period]
                segment["@tot_capacity"] = capacity
                segment["@seated_capacity"] = seated_capacity
                segment["@tot_vcr"] = vcr
                segment["@seated_vcr"] = seated_vcr
                # link reliability is calculated as link_rel_factor * base (non-crowded) transit time
                if segment.link is None:
                    # sometimes segment.link returns None. Is this due to hidden segments??
                    segment['@seg_rel'] = 0
                else:
                    segment["@seg_rel"] = segment.link.data3 * segment['@base_timtr']
                segment["@eawt"] = calc_eawt(segment, vcr, headway)
                segment["@capacity_penalty"] = max(segment["@phdwy"] - segment["@eawt"] - headway, 0) * hdwy_fraction
                segment['@ccost_skim'] = segment['@ccost']

            additional_attribs = ["@eawt", "@capacity_penalty", "@tot_vcr", "@seated_vcr", "@tot_capacity", "@seated_capacity", "@seg_rel", "@ccost_skim"]
            values = network.get_attribute_values('TRANSIT_SEGMENT', additional_attribs)
            scenario.set_attribute_values('TRANSIT_SEGMENT', additional_attribs, values)

            # # Link unreliability
            spec = get_strat_spec({"in_vehicle": "@seg_rel"}, "%s_LINKREL" % skim_name)
            strategy_analysis(spec, class_name=class_name, scenario=scenario, num_processors=num_processors)

            # Crowding penalty
            # for some unknown reason, just using ccost here will produce an all 0 matrix...
            # spec = get_strat_spec({"in_vehicle": "@ccost"}, "%s_CROWD" % skim_name)
            # hack to get around this was to create a new variable that is a copy of ccost and use it to skim
            spec = get_strat_spec({"in_vehicle": "@ccost_skim"}, "%s_CROWD" % skim_name)
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
            print(strat.name)
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
    """
    Sets the local+premium skim matrices to zero if path does not include both
    local and premium service.

    Parameters:
        - scenario: emme scenario object containing local+premium skims
        - period: str of period name
    Returns:
        - None
    """
    # Reset skims to 0 if not both local and premium
    skims = [
        "FIRSTWAIT", "TOTALWAIT", "XFERS", "TOTALWALK",
        "LBIVTT", "EBIVTT", "LRIVTT", "HRIVTT", "CRIVTT", "FRIVTT",
        "XFERWAIT", "FARE", "IN_VEHICLE_COST",
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
    """
    Sets all transit matrix cells to zero if path includes more than the specified
    number of transfers.

    Parameters:
        - scenario: emme scenario object containing local+premium skims
        - period: str of period name
        - max_transfers: max number of transfers to allow between any two TAPs
    Returns:
        - None
    """
    # Reset skims to 0 if number of transfers is greater than max_transfers
    skims = [
        "FIRSTWAIT", "TOTALWAIT", "XFERS", "TOTALWALK",
        "LBIVTT", "EBIVTT", "LRIVTT", "HRIVTT", "CRIVTT", "FRIVTT",
        "XFERWAIT", "FARE", "IN_VEHICLE_COST",
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
    """
    Gets the data stored in a matrix

    Parameters:
        - scenario: emme scenario that contains the matrix
        - name: str of matrix name to get data from
    Returns:
        - numpy array of matrix data
    """
    # data = _matrix_cache.get(name)
    # if data is None:
    matrix = scenario.emmebank.matrix(name)
    if matrix is None:
        raise Exception("No matrix with name %s" % name)
    return matrix.get_numpy_data(scenario.id)
    #_matrix_cache[name] = data
    # return data


def set_matrix_data(scenario, name, data):
    """
    Sets the data stored in a matrix

    Parameters:
        - scenario: emme scenario that contains the matrix
        - name: str of matrix name to store data in
        - data: numpy array of matrix data
    Returns:
        - None
    """
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
        except Exception as e:
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
        except Exception as e:
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
    """
    Helper class used to better handle omx specific data when writing
    out transit skims in omx form.
    """
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
            for (key, matrix) in matrices.items():
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
    """
    Export all created matrices in the scenario to the specified omx_file

    Parameters:
        - omx_file: str of omx_file name and location
        - periods: time of day periods to write out matrices for
        - scenario: emme scenario containing the matrices to write out
        - big_to_zero: boolean, if true will set all cells with value above 10E6 to zero
        - max_transfer: If a tap pair has more than three transfers, set all matrix
            values to zero for that tap pair.  If None, will not set any values to 0.
    Returns:
        - None
    """
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
    """
    Writes out csv file containing the transit boardings by line  for use in
    validation summaries

    Parameters:
        - desktop: emme desktop object with an primary scenario that has transit
            boardings assigned
        - output_transit_boardings_file: str of file to write transit boardings to
    """
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

    column.expression = "@mode"
    column.name = "line_mode"
    table.add_column(4, column)

    table.export(output_transit_boardings_file)
    table.close()


def export_boardings_by_segment(desktop, output_transit_boardings_file):
    """
    Writes out csv file containing the transit boardings by segment for use in
    validation summaries

    Parameters:
        - desktop: emme desktop object with an primary scenario that has transit
            boardings assigned
        - output_transit_boardings_file: str of file to write transit boardings to
    """
    project = desktop.project
    table = project.new_network_table("TRANSIT_SEGMENT")
    column = _worksheet.Column()

    col_name_dict = {
        "i": "i_node",
        "j": "j_node",
        "line": "line_name",
        "description": "description",
        "voltr": "volume",
        "board": "boardings",
        "alight": "alightings",
        "#src_mode": "mode",
        "@mode": "line_mode",
        "capt": "total_cap_of_line_per_hr",
        "caps": "seated_cap_of_line_per_hr",
        "xi": "i_node_x",
        "yi": "i_node_y",
        "xj": "j_node_x",
        "yj": "j_node_y",
        "@tot_capacity": "total_capacity",
        "@seated_capacity": "seated_capacity",
        "@capacity_penalty": "capacity_penalty",
        "@tot_vcr": "tot_vcr",
        "@seated_vcr": "seated_vcr",
        "@ccost": "ccost",
        "@eawt": "eawt",
        "@seg_rel": "seg_rel",
    }

    col_num = 0
    for expression, name in col_name_dict.items():
        column.expression = expression
        column.name = name
        table.add_column(col_num, column)
        col_num += 1

    table.export(output_transit_boardings_file)
    table.close()


def export_boardings_by_station(modeller, output_folder, period):
    sta2sta = modeller.tool(
        "inro.emme.transit_assignment.extended.station_to_station_analysis")
    sta2sta_spec = {
        "type": "EXTENDED_TRANSIT_STATION_TO_STATION_ANALYSIS",
        "transit_line_selections": {
            "first_boarding": "mod=h",
            "last_alighting": "mod=h"
        },
        "analyzed_demand": None,
    }

    # FIXME these expressions need to be more flexible if fares are applied
    operator_dict = {
    # mode: network_selection
        'bart': "mode=h",
        'caltrain': "mode=i"
    }

    # no station to station attributes for local buses
    sets = ["PREM", "ALLPEN"]

    with _m.logbook_trace("Writing station-to-station summaries for period %s" % period):
        for set in sets:
            for op, cut in operator_dict.iteritems():
                class_name = "%s_%s" % (period, set)
                demand_matrix = "mfTRN_%s_%s" % (_set_dict[set], period)
                output_file_name = "%s_station_to_station_%s_%s.txt" % (op, set, period)
                print(class_name, demand_matrix, output_file_name)

                sta2sta_spec['transit_line_selections']['first_boarding'] = cut
                sta2sta_spec['transit_line_selections']['last_alighting'] = cut
                sta2sta_spec['analyzed_demand'] = demand_matrix

                output_path = _os.path.join(output_folder, output_file_name)
                sta2sta(specification=sta2sta_spec,
                        output_file=output_path,
                        append_to_output_file=False,
                        class_name=class_name)


def output_transit_boardings(desktop, output_location, period):
    desktop.data_explorer().replace_primary_scenario(scenario)
    output_transit_boardings_file = _os.path.join(_os.getcwd(), output_location, "boardings_by_line_{}.csv".format(period))
    export_boardings_by_line(desktop, output_transit_boardings_file)

    output_transit_segments_file = _os.path.join(_os.getcwd(), output_location, "boardings_by_segment_{}.csv".format(period))
    export_boardings_by_segment(desktop, output_transit_segments_file)

    # output_station_to_station_folder = _os.path.join(_os.getcwd(), output_location)
    # export_boardings_by_station(modeller, output_station_to_station_folder, period)


# --------------------------------------------- Entry Point ---------------------------------------
if __name__ == "__main__":
    parser = _argparse.ArgumentParser(description="Skim an already created Emme transit network.")
    parser.add_argument('-p', '--trn_path', help=r"path to the trn folder, default is the current_working_folder\trn",
                        default=_os.path.join(_os.getcwd(), 'trn'))
    parser.add_argument('-s', '--skims_path', help=r"path to the skims folder, default is the current_working_folder\skims",
                        default=_os.path.join(_os.getcwd(), 'skims'))
    parser.add_argument('-i', '--iteration', help='Current inner loop iteration number for MSA averaging', type=int)
    parser.add_argument('-c', '--ccr_periods', help='List of time periods to run CCR as EA,AM,MD,PM,EV or ALL', default='AM,PM')
    parser.add_argument('--save_iter_flows', action="store_true", help='Save per-iteration flows in scenarios', default=False)
    parser.add_argument('-t', '--time_periods', help='List of time periods as EA,AM,MD,PM,EV or ALL', default='ALL')
    parser.add_argument('-o', '--port', help='Port to connect to Emme desktop session', default=59673, type=int)
    parser.add_argument('-d', '--skip_import_demand', action="store_true", help='Skip import of CT-RAMP demand')
    parser.add_argument('-b', '--output_transit_boardings', action="store_true", help='Output transit boardings from assignment')
    parser.add_argument('-n', '--num_processors', help='Number of processors to use, can specify MAX-#', default='MAX-4')

    args = parser.parse_args()
    if args.time_periods == "ALL":
        time_periods = _all_periods[:]
    else:
        time_periods = args.time_periods.split(",")

    # connect to already created Emme project
    try:
        desktop = connect_to_desktop(port=args.port)
    except:
        desktop = start_desktop(args.trn_path, port=args.port)
    modeller = _m.Modeller(desktop)
    emmebank = modeller.emmebank

    # perform skimming and assignment for each period
    for period in time_periods:
        scenario_id = period_to_scenario_dict[period]
        scenario = emmebank.scenario(scenario_id)

        initialize_matrices(components=['transit_skims'], periods=[period], scenario=scenario, delete_all_existing=False)

        ctramp_output_folder = _os.path.join(_os.getcwd(), 'ctramp_output')
        if not args.skip_import_demand:
            import_demand_matrices(period, scenario, ctramp_output_folder, num_processors=args.num_processors, msa_iteration=args.iteration)
        else:
            create_empty_demand_matrices(period, scenario)

        if (not args.skip_import_demand) and (period in args.ccr_periods.split(",") or (args.ccr_periods == 'ALL')):
            use_ccr = True
        else:
            use_ccr = False

        perform_assignment_and_skim(modeller, scenario, period=period, assignment_only=False,
                                    num_processors=args.num_processors, use_fares=True, use_ccr=use_ccr)
        output_omx_file = _os.path.join(args.skims_path, "transit_skims_{}.omx".format(period))
        export_matrices_to_omx(omx_file=output_omx_file, periods=[period], scenario=scenario,
                               big_to_zero=True, max_transfers=3)

        if use_ccr and args.save_iter_flows:
            save_per_iteration_flows(scenario)

        if args.output_transit_boardings:
            output_transit_boardings(desktop, output_location=args.trn_path, period=period)
