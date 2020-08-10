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

import inro.emme.desktop.app as _app
import inro.emme.desktop.types as _ws_types
import inro.emme.database.emmebank as _eb
import inro.modeller as _m
import argparse
import os

# ------------- input files------------
emme_network_transaction_folder = os.path.join(os.getcwd(),"emme_network_transaction_files")
emme_mode_transaction_file = os.path.join(emme_network_transaction_folder, "emme_modes.txt")
emme_vehicle_transaction_file = os.path.join(emme_network_transaction_folder, "emme_vehicles.txt")
emme_network_transaction_file = os.path.join(emme_network_transaction_folder, "emme_network.txt")
extra_node_attr_file = os.path.join(emme_network_transaction_folder, "emme_extra_node_attributes.txt")
extra_link_attr_file = os.path.join(emme_network_transaction_folder, "emme_extra_link_attributes.txt")
emme_transit_network_file = os.path.join(emme_network_transaction_folder, "emme_transit_lines.txt")
extra_transit_line_attr_file = os.path.join(emme_network_transaction_folder, "emme_extra_line_attributes.txt")
# ------------- output files------------
# name of folder for emme project
emme_project_folder = "mtc_emme"

# modeller = _m.Modeller()
# ------------- run parameters ---------
WKT_PROJECTION = 'PROJCS["NAD_1983_StatePlane_California_VI_FIPS_0406_Feet",GEOGCS["GCS_North_American_1983",DATUM["North_American_Datum_1983",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Lambert_Conformal_Conic_2SP"],PARAMETER["False_Easting",6561666.666666666],PARAMETER["False_Northing",1640416.666666667],PARAMETER["Central_Meridian",-116.25],PARAMETER["Standard_Parallel_1",32.78333333333333],PARAMETER["Standard_Parallel_2",33.88333333333333],PARAMETER["Latitude_Of_Origin",32.16666666666666],UNIT["Foot_US",0.30480060960121924],AUTHORITY["EPSG","102646"]]'

def init_emme_project(root, title, emmeversion, port=59673):
    project_path = _app.create_project(root, emme_project_folder)
    desktop = _app.start(  # will not close desktop when program ends
        project=project_path, user_initials="PB", visible=True, port=port)
    # desktop = _app.start_dedicated(
        # project=project_path, user_initials="PB", visible=True)
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
        'full_matrices': 300,

        'scenarios': 7,
        'centroids': 10000,
        'regular_nodes': 600000,
        'links': 1000000,
        'turn_entries': 1900000,
        'transit_vehicles': 200,
        'transit_lines': 40000,
        'transit_segments': 2000000,
        'extra_attribute_values': 30000000,

        'functions': 99,
        'operators': 5000
    }

    # for Emme version > 4.3.7, add the sola_analyses dimension
    if emmeversion != '4.4.2':
        dimensions['sola_analyses'] = 240

    os.mkdir(os.path.join(project_root, "Database"))
    emmebank = _eb.create(os.path.join(project_root, "Database", "emmebank"), dimensions)
    emmebank.title = title
    emmebank.coord_unit_length = 0.000189394  # feet to miles
    emmebank.unit_of_length = "mi"
    emmebank.unit_of_cost = "$"
    emmebank.unit_of_energy = "MJ"
    emmebank.node_number_digits = 6
    emmebank.use_engineering_notation = True
    scenario = emmebank.create_scenario(1000)
    scenario.title = "Initial Scenario"
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


def import_modes(input_dir):
    print "importing modes"
    process_modes_tool_path = "inro.emme.data.network.mode.mode_transaction"
    process_modes_tool = modeller.tool(process_modes_tool_path)
    input_file = os.path.join(input_dir, emme_mode_transaction_file).replace("\\","/")
    process_modes_tool(transaction_file=input_file,
        revert_on_error=True,
        scenario=modeller.scenario)


def import_network(input_dir):
    print "importing network"
    process_network_tool_path = "inro.emme.data.network.base.base_network_transaction"
    process_network_tool = modeller.tool(process_network_tool_path)
    input_file = os.path.join(input_dir, emme_network_transaction_file).replace("\\","/")
    process_network_tool(transaction_file=input_file,
        revert_on_error=True,
        scenario=modeller.scenario)


def import_extra_node_attributes(input_dir):
    print "importing extra node attributes"
    import_extra_attributes_tool_path = "inro.emme.data.extra_attribute.import_extra_attributes"
    import_extra_attributes_tool = modeller.tool(import_extra_attributes_tool_path)
    input_file = os.path.join(input_dir, extra_node_attr_file)
    import_extra_attributes_tool(
        file_path=input_file,
        scenario=modeller.scenario,
        field_separator=",",
        has_header=True,
        column_labels="FROM_HEADER",
        import_definitions=True,
        revert_on_error=True
    )


def import_extra_link_attributes(input_dir):
    print "importing extra link attributes"
    import_extra_attributes_tool_path = "inro.emme.data.extra_attribute.import_extra_attributes"
    import_extra_attributes_tool = modeller.tool(import_extra_attributes_tool_path)
    input_file = os.path.join(input_dir, extra_link_attr_file)
    import_extra_attributes_tool(
        file_path=input_file,
        scenario=modeller.scenario,
        field_separator=",",
        has_header=True,
        column_labels="FROM_HEADER",
        import_definitions=True,
        revert_on_error=True
    )


def import_vehicles(input_dir):
    print "importing transit vehicles"
    process_vehicles_tool_path = "inro.emme.data.network.transit.vehicle_transaction"
    process_vehicles_tool = modeller.tool(process_vehicles_tool_path)
    input_file = os.path.join(input_dir, emme_vehicle_transaction_file).replace("\\","/")
    process_vehicles_tool(transaction_file=input_file,
        revert_on_error=True,
        scenario=modeller.scenario)


def import_transit_lines(input_dir):
    print "importing transit network"
    process_transit_lines_tool_path = "inro.emme.data.network.transit.transit_line_transaction"
    process_transit_lines_tool = modeller.tool(process_transit_lines_tool_path)
    input_file = os.path.join(input_dir, emme_transit_network_file).replace("\\","/")
    process_transit_lines_tool(transaction_file=input_file,
        revert_on_error=True,
        scenario=modeller.scenario)


def import_extra_transit_line_attributes(input_dir):
    print "importing extra transit line attributes"
    import_extra_attributes_tool_path = "inro.emme.data.extra_attribute.import_extra_attributes"
    import_extra_attributes_tool = modeller.tool(import_extra_attributes_tool_path)
    input_file = os.path.join(input_dir, extra_transit_line_attr_file)
    import_extra_attributes_tool(
        file_path=input_file,
        scenario=modeller.scenario,
        field_separator=",",
        has_header=True,
        column_labels="FROM_HEADER",
        import_definitions=True,
        revert_on_error=True
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new Emme project and database with MTC defaults.")
    parser.add_argument('-r', '--root', help="path to the root ABM folder, default is the working folder",
                        default=os.path.abspath(os.getcwd()))
    parser.add_argument('-t', '--title', help="the Emmebank title",
                        default="MTC Initial Database")
    parser.add_argument('-v', '--emmeversion', help='the Emme version', default='4.4.2')
    args = parser.parse_args()

    # create emme project
    # desktop = init_emme_project(args.root, args.title, args.emmeversion)
    # or connect to already open desktop for debugging
    desktop = connect_to_running_desktop(port=59673)

    # create modeller instance used to import data to project database
    modeller = _m.Modeller(desktop)

    # import_modes(input_dir=args.root)
    # import_network(input_dir=args.root)
    # import_extra_node_attributes(input_dir=args.root)
    # import_extra_link_attributes(input_dir=args.root)
    # import_vehicles(input_dir=args.root)
    import_transit_lines(input_dir=args.root)
    import_extra_transit_line_attributes(input_dir=args.root)

    # emmebank.dispose()
