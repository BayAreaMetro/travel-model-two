"""
cube_to_emme_network_conversion.py

 Script to read in a Cube network shapefile and output Emme transaction files to
 load the network and attributes into Emme.

 inputs:
    - congested network files from Cube in DBF format
    - Cube transit.lin file with updated numbering
    - vehtype.pts file for vehicle types
    - Station attribute csv file

 Outputs:
    - A folder for each time of day period containing all of the emme transaction files
    - Node crosswalk files and station attribute files for debugging between cube and emme

 Specific input and output file location and names are listed in the __init__ method
 of the emme_network_conversion class

 Usage: python cube_to_emme_network_conversion.py
 Run Options:
        ['-p', '--trn_path'], path to the trn folder, default is the current_working_folder\trn
        ['-i', '--first_iteration'], Is this the first iteration? yes or no, default is yes.
            There is currently no difference between first_iteration yes and no, but future
            improvements could speed up run time by only updating the network attributes that change
            after the first iteration.

 Date: Oct, 2021
 Contacts: david.hensle@rsginc.com
"""

import geopandas
import shapely
import pandas as pd
import numpy as np
import shlex
import csv
import os
import argparse
import time
import re
pd.set_option("display.max_columns",250)
cal_state_plane_VI_crs = '+proj=lcc +lat_1=32.78333333333333 +lat_2=33.88333333333333 +lat_0=32.16666666666666 +lon_0=-116.25 +x_0=2000000 +y_0=500000.0000000002 +ellps=GRS80 +datum=NAD83 +to_meter=0.3048006096012192 +no_defs'


# ------------- run parameters ---------
_all_periods = ['EA', 'AM', 'MD', 'PM', 'EV']
# _all_periods = ['AM']

# maps time of day period to correct headway variable
period_to_headway_dict = {
    'EA': 'HEADWAY[1]',
    'AM': 'HEADWAY[2]',
    'MD': 'HEADWAY[3]',
    'PM': 'HEADWAY[4]',
    'EV': 'HEADWAY[5]',
}


# maps transit 'Mode Group' defined in TM2 to a single character required by Emme
emme_transit_modes_dict = {
    'Local bus': 'b',
    'Express Bus': 'x',
    'Express bus': 'x',
    'Ferry service': 'f',
    'Light rail': 'l',
    'Heavy rail': 'h',
    'Commuter rail': 'r'
}

# station attributes are only applied to taps that service the corresponding mode
station_type_to_emme_mode_dict = {
    'H': ['h'],
    'C': ['r'],
    'F': ['f'],
    'L': ['l'],
    'B': ['b', 'x']
}
station_attribute_use_flags=[2015]
# stations that match to taps farther than a mile away are not included
station_to_tap_max_dist = 5280  # feet

# extra attributes from cube script that should be included in the Emme network
extra_node_attributes = ['OLD_NODE', 'TAPSEQ', 'FAREZONE']
extra_link_attributes = ['SPEED', 'FEET',
    'LANES_EA', 'LANES_AM', 'LANES_MD', 'LANES_PM', 'LANES_EV',
    'USECLASS_EA', 'USECLASS_AM', 'USECLASS_MD', 'USECLASS_PM', 'USECLASS_EV',
    'ASSIGNABLE', 'TRANSIT', 'FT', 'FFS', 'TRANTIME', 'WALKDIST','WALKTIME',
    'WALK_ACCESS', 'BIKE_ACCESS', 'DRIVE_ACCES', 'BUS_ONLY', 'RAIL_ONLY',
    'OLD_A', 'OLD_B', 'CTIM', 'NTL_MODE']
extra_transit_line_attributes = ['HEADWAY[1]','HEADWAY[2]','HEADWAY[3]','HEADWAY[4]',
    'HEADWAY[5]', 'MODE', 'FARESYSTEM', 'uses_NNTIME']
# name is from the raodway attribute names file
extra_link_network_fields = ['COUNTY', 'CNTYPE', 'modes', 'name']

# station attributes
station_extra_attributes = ['stBikeWalk', 'stBusWalkTime', 'stPNRWalkTime', 'stKNRWalkTime', 'stPNRDriveTime',
                            'stKNRDriveTime', 'stPlatformTime', 'stFreeSpaces', 'stPaidSpaces', 'stPermitSpaces',
                            'stPrivateSpaces', 'stDailyCost', 'stMonthlyCost', 'stPrivateCost', 'stPNRSplit']
station_network_field_attributes = ['stName', 'stType', 'stParkType']

# --------------------------------------------- Methods --------------------------------------------
class emme_network_conversion:
    def __init__(self, cube_network_folder, period):
        """
        Sets the time of day period, and input and output file locations that are
        used when creating emme transaction files.  The purpose of the class is to keep
        better track of the specific files for each time period.

        Parameters:
            - cube_network_folder: folder containing the cube network and transit data.
                                Is typtically the "trn" folder in the base model directory
            - period: str to denote the time of day period.
        """
        self.period = period
        # input data
        self.link_shapefile = os.path.join(cube_network_folder, "mtc_transit_network_{}_CONG_links.DBF".format(period))
        self.node_shapefile = os.path.join(cube_network_folder, "mtc_transit_network_{}_CONG_nodes.DBF".format(period))
        self.transit_lin_file = os.path.join(cube_network_folder, "transitLines_new_nodes.lin")
        self.vehtype_pts_file = os.path.join(cube_network_folder, "vehtype.pts")
        self.link_names_file = os.path.join(cube_network_folder, "roadway-assignment-names-helper.csv")
        self.station_attributes_input_file = os.path.join(cube_network_folder, 'station_attribute_data_input.csv')
        # output data
        self.emme_network_transaction_folder = os.path.join(
            cube_network_folder,"emme_network_transaction_files_{}".format(period))
        self.station_attributes_folder = os.path.join(self.emme_network_transaction_folder, 'station_attributes')
        self.node_id_crosswalk_file = os.path.join(self.emme_network_transaction_folder, "node_id_crosswalk.csv")
        self.emme_mode_transaction_file = os.path.join(self.emme_network_transaction_folder, "emme_modes.txt")
        self.emme_vehicle_transaction_file = os.path.join(self.emme_network_transaction_folder, "emme_vehicles.txt")
        self.emme_network_transaction_file = os.path.join(self.emme_network_transaction_folder, "emme_network.txt")
        self.extra_node_attr_file = os.path.join(self.emme_network_transaction_folder, "emme_extra_node_attributes.txt")
        self.extra_link_attr_file = os.path.join(self.emme_network_transaction_folder, "emme_extra_link_attributes.txt")
        self.extra_link_network_fields_file = os.path.join(self.emme_network_transaction_folder, "emme_extra_link_network_fields.txt")
        self.update_extra_link_attr_file = os.path.join(self.emme_network_transaction_folder, "emme_update_extra_link_attributes.txt")
        self.emme_transit_network_file = os.path.join(self.emme_network_transaction_folder, "emme_transit_lines.txt")
        self.extra_transit_line_attr_file = os.path.join(self.emme_network_transaction_folder, "emme_extra_line_attributes.txt")
        self.extra_transit_segment_attr_file = os.path.join(self.emme_network_transaction_folder, "emme_extra_segment_attributes.txt")
        self.emme_transit_time_function_file = os.path.join(self.emme_network_transaction_folder, "emme_transit_time_function.txt")
        self.all_stop_attributes_file = os.path.join(self.emme_network_transaction_folder, "all_stop_attributes.csv")
        self.all_transit_lines_file = os.path.join(self.emme_network_transaction_folder, "all_transit_lines.csv")
        self.station_extra_attributes_file = os.path.join(self.emme_network_transaction_folder, "station_extra_attributes.txt")
        self.station_network_fields_file = os.path.join(self.emme_network_transaction_folder, "station_network_fields.txt")

    def load_input_data(self):
        """
        Loads in the links and nodes from the Cube network.  Trims all MAZ and TAZ
        connectors and pedestrian links to reduce network size.

        Returns:
            - node_gdf: GeoDataFrame containing node information
            - link_gdf: GeoDataFrame containing link information
        """
        print("Loading input data for", self.period, "period")
        node_gdf = geopandas.read_file(self.node_shapefile)
        link_gdf = geopandas.read_file(self.link_shapefile)

        # remove all MAZ, TAZ, and PED links.
        link_gdf = link_gdf[link_gdf['CNTYPE'].isin(['TANA', 'TAP', 'CRAIL', 'TRWALK'])]

        print("node columns: ", node_gdf.columns)
        print("link columns: ", link_gdf.columns)

        for attr in extra_node_attributes:
            assert attr in node_gdf.columns, "extra_node_attribute " + attr + " is not in the node input file"
        for attr in extra_link_attributes:
            assert attr in link_gdf.columns, "extra_link_attribute " + attr + " is not in the link input file"

        return node_gdf, link_gdf


    def determine_centroid_nodes(self, node_gdf):
        """
        Determines the centroid nodes using the following table:
        http://bayareametro.github.io/travel-model-two/input/#county-node-numbering-system

        Parameters:
            - node_gdf: GeoDataFrame of node attributes

        Returns:
            - node_gdf with centroid node flags
        """
        node_gdf['is_taz'] = 0
        node_gdf.loc[(node_gdf.OLD_NODE <= 9999)
                        | ((node_gdf.OLD_NODE >= 100001) & (node_gdf.OLD_NODE <= 109999))
                        | ((node_gdf.OLD_NODE >= 200001) & (node_gdf.OLD_NODE <= 209999))
                        | ((node_gdf.OLD_NODE >= 300001) & (node_gdf.OLD_NODE <= 309999))
                        | ((node_gdf.OLD_NODE >= 400001) & (node_gdf.OLD_NODE <= 409999))
                        | ((node_gdf.OLD_NODE >= 500001) & (node_gdf.OLD_NODE <= 509999))
                        | ((node_gdf.OLD_NODE >= 600001) & (node_gdf.OLD_NODE <= 609999))
                        | ((node_gdf.OLD_NODE >= 700001) & (node_gdf.OLD_NODE <= 709999))
                        | ((node_gdf.OLD_NODE >= 800001) & (node_gdf.OLD_NODE <= 809999)),
                       'is_taz'] = 1

        node_gdf['is_taz_exts'] = 0
        node_gdf.loc[((node_gdf.OLD_NODE >= 900001) & (node_gdf.OLD_NODE <= 999999)),
                       'is_taz_exts'] = 1

        node_gdf['is_maz'] = 0
        node_gdf.loc[((node_gdf.OLD_NODE >= 10001) & (node_gdf.OLD_NODE <= 89999))
                        | ((node_gdf.OLD_NODE >= 110001) & (node_gdf.OLD_NODE <= 189999))
                        | ((node_gdf.OLD_NODE >= 210001) & (node_gdf.OLD_NODE <= 289999))
                        | ((node_gdf.OLD_NODE >= 310001) & (node_gdf.OLD_NODE <= 389999))
                        | ((node_gdf.OLD_NODE >= 410001) & (node_gdf.OLD_NODE <= 489999))
                        | ((node_gdf.OLD_NODE >= 510001) & (node_gdf.OLD_NODE <= 589999))
                        | ((node_gdf.OLD_NODE >= 610001) & (node_gdf.OLD_NODE <= 689999))
                        | ((node_gdf.OLD_NODE >= 710001) & (node_gdf.OLD_NODE <= 789999))
                        | ((node_gdf.OLD_NODE >= 810001) & (node_gdf.OLD_NODE <= 889999)),
                       'is_maz'] = 1

        node_gdf['is_tap'] = 0
        node_gdf.loc[((node_gdf.OLD_NODE >= 90001) & (node_gdf.OLD_NODE <= 99999))
                        | ((node_gdf.OLD_NODE >= 190001) & (node_gdf.OLD_NODE <= 199999))
                        | ((node_gdf.OLD_NODE >= 290001) & (node_gdf.OLD_NODE <= 299999))
                        | ((node_gdf.OLD_NODE >= 390001) & (node_gdf.OLD_NODE <= 399999))
                        | ((node_gdf.OLD_NODE >= 490001) & (node_gdf.OLD_NODE <= 499999))
                        | ((node_gdf.OLD_NODE >= 590001) & (node_gdf.OLD_NODE <= 599999))
                        | ((node_gdf.OLD_NODE >= 690001) & (node_gdf.OLD_NODE <= 699999))
                        | ((node_gdf.OLD_NODE >= 790001) & (node_gdf.OLD_NODE <= 799999))
                        | ((node_gdf.OLD_NODE >= 890001) & (node_gdf.OLD_NODE <= 899999)),
                       'is_tap'] = 1
        num_nodes = len(node_gdf)
        num_tazs = node_gdf['is_taz'].sum()
        num_ext_tazs = node_gdf['is_taz_exts'].sum()
        num_taps = node_gdf['is_tap'].sum()
        num_mazs = node_gdf['is_maz'].sum()

        print("Total number of nodes:", num_nodes)
        print("Number of TAZ centroid nodes:", num_tazs)
        print("Number of External TAZ centroid nodes:", num_ext_tazs)
        print("Number of TAP centroid nodes:", num_taps)
        print("Number of MAZ centroid nodes:", num_mazs)
        return node_gdf


    def renumber_nodes_for_emme(self, node_gdf, link_gdf):
        """
        Renumbers node id's for use in Emme.
        Nodes are numbered starting at one to avoid the node id cap in Emme.
        Sets new i and j node id's for links to match renumbered nodes.

        Writes the crosswalk file to the output folder.

        Parameters:
            - node_gdf: GeoDataFrame of node data
            - link_gdf: GeoDataFrame of link data

        Returns:
            - node_gdf with renumbered nodes
            - link_gdf with renumbered links
        """
        # NOTE: Node ID's need to be less than 1,000,000 for import into Emme
        node_gdf['node_id'] = pd.Series(range(1,len(node_gdf)+1))

        # merging new node_ids to the link and nodes files
        node_cols = ['N','node_id', 'is_tap', 'X', 'Y']
        link_gdf = pd.merge(
            link_gdf,
            node_gdf[node_cols],
            how='left',
            left_on='A',
            right_on='N'
        )
        link_gdf.drop(columns='N', inplace=True)
        column_rename_dict = {
            'node_id': 'A_node_id',
            'is_tap': 'A_is_tap',
            'X': 'A_node_X',
            'Y': 'A_node_Y'
        }
        link_gdf.rename(columns=column_rename_dict, inplace=True)

        link_gdf = pd.merge(
            link_gdf,
            node_gdf[node_cols],
            how='left',
            left_on='B',
            right_on='N'
        )
        link_gdf.drop(columns='N', inplace=True)
        column_rename_dict = {
            'node_id': 'B_node_id',
            'is_tap': 'B_is_tap',
            'X': 'B_node_X',
            'Y': 'B_node_Y'
        }
        link_gdf.rename(columns=column_rename_dict, inplace=True)

        # writing node crosswalk table for reference if needed
        node_gdf[['OLD_NODE', 'N', 'node_id']].to_csv(self.node_id_crosswalk_file, index=False, header=True)

        # calculating link distance between nodes
        link_gdf['dist_between_nodes_ft'] = np.sqrt(
            np.power(link_gdf['A_node_X'] - link_gdf['B_node_X'], 2)
            + np.power(link_gdf['A_node_Y'] - link_gdf['B_node_Y'], 2))
        link_gdf['dist_between_nodes_mi'] = link_gdf['dist_between_nodes_ft'] / 5280

        return node_gdf, link_gdf


    def parse_vehtype_pts_file(self):
        """
        Parses the vehicle type information from vehtype.pts

        Returns:
            - vehicletype_df: pandas datafrane of vehicle type data
        """

        vehicletype_data = []
        # looping through each line in vehicle type pts file.
        with open(self.vehtype_pts_file, 'r') as file:
            line = file.readline()
            while line:
                data_dict = {}
                # parsing vehicletype data
                if 'VEHICLETYPE NUMBER' in line:
                    line = line.replace('VEHICLETYPE NUMBER', 'NUMBER')
                    # replace spaces with comma unless inside quote, then remove quotes
                    line_segs = ','.join(shlex.split(line)).split(',')
                    for line_seg in line_segs:
                        key = line_seg.split('=')[0]
                        value = line_seg.split('=')[1]
                        data_dict.update({key:value})
                    vehicletype_data.append(data_dict)

                # read next line
                line = file.readline()

        vehicletype_df = pd.DataFrame(vehicletype_data)
        vehicletype_df.rename(columns={'NUMBER': 'VEHICLETYPE'}, inplace=True)

        return vehicletype_df


    def create_and_write_mode_transaction_file(self, write_file=True):
        """
        Creates and writes the emme mode transaction file.  Modes definitions are hard coded here.

        Parameters:
            - write_file: Boolean on whether to write the Emme transaction file. default True
        Returns:
            - mode_transaction_df: dataframe of mode Emme mode definitions

        """
        print("Writing mode transaction file")
        # type options: 1:auto, 2:transit, 3:auxiliary transit or 4:auxiliary auto
        columns=['transaction', 'mode', 'descr', 'type']
        mode_transaction_df = pd.DataFrame(columns=columns)
        mode_transaction_df = mode_transaction_df.append({'transaction': 'a', 'mode': 'c', 'descr': 'car', 'type':1 }, ignore_index=True)
        mode_transaction_df = mode_transaction_df.append({'transaction': 'a', 'mode': 'w', 'descr': 'walk', 'type':3 }, ignore_index=True)
        mode_transaction_df = mode_transaction_df.append({'transaction': 'a', 'mode': 'a', 'descr': 'access', 'type':3 }, ignore_index=True)
        mode_transaction_df = mode_transaction_df.append({'transaction': 'a', 'mode': 'e', 'descr': 'egress', 'type':3 }, ignore_index=True)
        mode_transaction_df = mode_transaction_df.append({'transaction': 'a', 'mode': 'b', 'descr': 'local_bus', 'type':2 }, ignore_index=True)
        mode_transaction_df = mode_transaction_df.append({'transaction': 'a', 'mode': 'x', 'descr': 'exp_bus', 'type':2 }, ignore_index=True)
        mode_transaction_df = mode_transaction_df.append({'transaction': 'a', 'mode': 'f', 'descr': 'ferry', 'type':2 }, ignore_index=True)
        mode_transaction_df = mode_transaction_df.append({'transaction': 'a', 'mode': 'l', 'descr': 'light_rail', 'type':2 }, ignore_index=True)
        mode_transaction_df = mode_transaction_df.append({'transaction': 'a', 'mode': 'h', 'descr': 'heavy_rail', 'type':2 }, ignore_index=True)
        mode_transaction_df = mode_transaction_df.append({'transaction': 'a', 'mode': 'r', 'descr': 'comm_rail', 'type':2 }, ignore_index=True)
        mode_transaction_df['plot'] = 1  # deprecated but needed
        mode_transaction_df['ctc'] = 0  # operating cost/hour. Only needed for mode type 2 and 3
        mode_transaction_df.loc[mode_transaction_df['type'].isin([1,3]), 'ctc'] = 0
        mode_transaction_df['cdc'] = 0  # operating cost/unit length. Only needed for mode type 2 and 3
        mode_transaction_df.loc[mode_transaction_df['type'].isin([1,3]), 'cdc'] = 0
        mode_transaction_df['etc'] = 0  # energy consumption/hour. Only needed for mode type 2 and 3
        mode_transaction_df.loc[mode_transaction_df['type'].isin([1,3]), 'etc'] = 0
        mode_transaction_df['edc'] = 0    # energy consumption/length. Only needed for mode type 2 and 3
        mode_transaction_df.loc[mode_transaction_df['type'].isin([1,3]), 'edc'] = 0
        mode_transaction_df['speed'] = 0  # speed only needed for type = 3 (aux transit mode speed)
        # walk speed set to 3 mph
        # mode_transaction_df.loc[mode_transaction_df['mode'] == 'w', 'speed'] = 3
        # mode_transaction_df.loc[mode_transaction_df['mode'] == 'a', 'speed'] = 3
        # mode_transaction_df.loc[mode_transaction_df['mode'] == 'e', 'speed'] = 3
        # access and egress times set to user link field 2 to grab WALKTIME variable
        mode_transaction_df.loc[mode_transaction_df['mode'] == 'w', 'speed'] = "ul2*1"
        mode_transaction_df.loc[mode_transaction_df['mode'] == 'a', 'speed'] = "ul2*1"
        mode_transaction_df.loc[mode_transaction_df['mode'] == 'e', 'speed'] = "ul2*1"


        assert all(pd.Series(emme_transit_modes_dict).isin(mode_transaction_df['mode'].values)), \
            "Mode in the emme_transit_modes_dict is not listed in  the mode transaction file"

        if write_file == False:
            return mode_transaction_df

        with open(self.emme_mode_transaction_file, 'w') as file:
            file.write('t modes init\n')
            mode_transaction_df.to_csv(file, mode='a', sep=' ', index=False, header=False)
        file.close()
        return mode_transaction_df


    def create_and_write_vehicle_transaction_file(self, vehicletype_df, transit_line_df):
        """
        Creates and writes vehicle information to the Emme transaction file

        Parameters:
            - vehicletype_df: dataframe of vehicle type data from vehtype.pts file
            - transit_line_df: dataframe of transit line dataframe matching lines to vehicles
        Returns:
            - mode_vehtype_xwalk: dataframe relating vehicle type to the transit line mode
        """
        print("Writing vehicle transaction file")
        # need to generate crosswalk between vehicletype, mode code, and emme mode
        mode_vehtype_xwalk = transit_line_df.groupby(
            ['MODE', 'VEHICLETYPE', 'emme_mode']).count().reset_index()[['MODE', 'VEHICLETYPE', 'emme_mode']]

        # not a one-to-one correspondence between vehicletype and emme_mode.
        # Emme requires a vehicle to belong to only one mode.
        # recoding emme_vehicle_num to satisfy this condition
        mode_vehtype_xwalk = mode_vehtype_xwalk.groupby(['VEHICLETYPE', 'emme_mode'])['MODE'].count().reset_index()
        mode_vehtype_xwalk.rename(columns={'MODE': 'MODE_count'}, inplace=True)
        mode_vehtype_xwalk['emme_vehicle_num'] = mode_vehtype_xwalk.index + 1

        vehicletype_df = pd.merge(vehicletype_df, mode_vehtype_xwalk, how='right', on='VEHICLETYPE')
        vehicletype_df = vehicletype_df.loc[pd.notna(vehicletype_df['NAME'])]

        # creating transaction file
        veh_transaction_df = vehicletype_df.copy()
        veh_transaction_df['transaction'] = 'a'
        veh_transaction_df['vehicle'] = veh_transaction_df['emme_vehicle_num']
        # vehicle description only allows 10 characters. removing non-alphanumeric chars
        veh_transaction_df['descr'] = veh_transaction_df['NAME'].apply(
            lambda x: re.sub(r'\W+', '', str(x))[:10])
        veh_transaction_df['mode'] = veh_transaction_df['emme_mode']
        veh_transaction_df['fleet'] = 1 # not actually used, included for backwards compatibility
        veh_transaction_df['caps'] = veh_transaction_df['SEATCAP']  # seated capacity
        veh_transaction_df['capt'] = veh_transaction_df['CRUSHCAP']  # total capacity
        veh_transaction_df['ctc'] = 0  # operating cost/hr
        veh_transaction_df['cdc'] = 0  # operating cost/unit length
        veh_transaction_df['etc'] = 0  # operating energy/hr
        veh_transaction_df['edc'] = 0  # operating energy/unit length
        veh_transaction_df['auto'] = 2  # auto equivalent of the vehicle

        # required order for vehicle transaction file
        veh_output_cols = ['transaction', 'vehicle', 'descr', 'mode', 'fleet', 'caps',
                           'capt', 'ctc', 'cdc', 'etc', 'edc', 'auto']

        with open(self.emme_vehicle_transaction_file, 'w') as file:
            file.write('t vehicles init\n')
            veh_transaction_df[veh_output_cols].to_csv(file, mode='a', sep=' ', index=False, header=False)
        file.close()

        return mode_vehtype_xwalk


    def create_emme_nodes_input(self, node_gdf):
        """
        Creates the variables required for the node transaction into Emme

        Parameters:
            - node_gdf: GeoDataFrame of node information
        Returns:
            - node_gdf with Emme specific columns
            - node_transaction_cols: list of columns to be written to transaction file
        """
        # adding required fields for the node transaction file
        node_gdf['i_node'] = node_gdf['node_id']
        node_gdf['transaction'] = 'a'
        # taps are denoted as centroid nodes
        node_gdf.loc[node_gdf['is_tap'] == 1, 'transaction'] = 'a*'
        node_gdf['x_cord'] = node_gdf['X']
        node_gdf['y_cord'] = node_gdf['Y']
        # unused fields required by Emme
        node_gdf['user1'] = 0
        node_gdf['user2'] = 0
        node_gdf['user3'] = 0
        node_gdf['node_label'] = '0000'

        # required order for node transaction file
        node_transaction_cols = ['transaction', 'i_node', 'x_cord', 'y_cord',
                                 'user1', 'user2', 'user3', 'node_label']
        return node_gdf, node_transaction_cols


    def create_emme_links_input(self, link_gdf, mode_transaction_df):
        """
        Creates the variables required for the link transaction into Emme

        Parameters:
            - linke_gdf: GeoDataFrame of linke information
        Returns:
            - linke_gdf with Emme specific columns
            - linke_transaction_cols: list of columns to be written to transaction file
        """
        non_walk_modes = ''
        for mode in mode_transaction_df['mode'].values:
            if mode in ['a', 'e', 'w']:
                # don't want to include access or egress modes on all links
                continue
            non_walk_modes = non_walk_modes + mode

        # adding required fields for the node transaction file
        link_gdf['transaction'] = 'a'
        link_gdf['i_node'] = link_gdf['A_node_id']
        link_gdf['j_node'] = link_gdf['B_node_id']
        link_gdf['length_ft'] = link_gdf['FEET']
        link_gdf['length_mi'] = link_gdf['FEET'] / 5280
        link_gdf['length_mi'] = link_gdf['length_mi'].round(4)
        link_gdf['length_mi'] = np.where(link_gdf['length_mi'] == 0, .0001, link_gdf['length_mi'])
        link_gdf['modes'] = non_walk_modes
        link_gdf.loc[link_gdf['CNTYPE'] == 'CRAIL']
        link_gdf.loc[link_gdf['A_is_tap'] == 1, 'modes'] = 'a'  # access
        link_gdf.loc[link_gdf['B_is_tap'] == 1, 'modes'] = 'e'  # eggress

        # TRWALK links are TAP-TAP psuedo links created during BuildTransitNetworks.job
        # We are using these as tansfer walk links to avoid walking along entire network
        # this will help runtime and remain consistent with previous TM2 version
        link_gdf.loc[link_gdf['CNTYPE'] == 'TRWALK', 'modes'] = 'w'  # walk links
        link_gdf['type'] = 1
        # network can have different number of lanes for each time period
        link_gdf['lanes'] = link_gdf['LANES_' + self.period]
        # NOTE: lanes can't be larger than 9 in Emme
        link_gdf.loc[link_gdf['lanes'] > 9, 'lanes'] = 9
        link_gdf['volume_delay_function'] = 1
        link_gdf['user1'] = link_gdf['TRANTIME'].round(4)  # set trantime for transit time function to access

        # walktime set in BuildTransitNetworks.job.  999 for non-TRWALK links.
        link_gdf['user2'] = link_gdf['WALKTIME']  # auxiliariy transit walktime
        link_gdf['user3'] = 0

        # required order for link transaction file
        link_transaction_cols = ['transaction', 'i_node', 'j_node', 'length_mi', 'modes', 'type', 'lanes',
                                 'volume_delay_function', 'user1', 'user2', 'user3']
        return link_gdf, link_transaction_cols


    def remove_long_walk_links(self, link_gdf, max_length_mi):
        """
        Utility function to remove long walk links from network

        Parameters:
            - link_gdf: GeoDataFrame of links
            - max_length_mi: float that specifies the max allowed walk link length in miles

        Returns:
            - link_gdf with no more walk links
        """
        long_walk_links = ((link_gdf['dist_between_nodes_mi'] > max_length_mi) & (link_gdf['NTL_MODE'] == 2))
        print("Total number of walk links: ", len(link_gdf[link_gdf['NTL_MODE'] == 2]))
        print("Number of long walk links removed: ", long_walk_links.sum())
        link_gdf = link_gdf[~long_walk_links]
        print("Walk links remaining: ", len(link_gdf[link_gdf['NTL_MODE'] == 2]))
        return link_gdf


    def write_links_and_nodes_transaction_file(self, node_gdf, link_gdf, mode_transaction_df):
        """
        Writes the Emme network transaction file

        Parameters:
            - node_gdf: GeoDataFrame of node information to be written to transaction file
            - link_gdf: GeoDataFrame of link information to be written to transaction file
            - mode_transaction_df: dataframe of Emme transit mode data
        Returns:
            - node_gdf with additional Emme variables
            - link_gdf with additional Emme variables
        """

        print("Writing emme network file")

        node_gdf, node_transaction_cols = self.create_emme_nodes_input(node_gdf)
        link_gdf, link_transaction_cols = self.create_emme_links_input(link_gdf, mode_transaction_df)

        # link_gdf = self.remove_long_walk_links(link_gdf, max_length_mi=.25)

        with open(self.emme_network_transaction_file, 'w') as file:
            file.write('t nodes init\n')
            node_gdf[node_transaction_cols].to_csv(file, mode='a', sep=' ', index=False, header=False)
            file.write('t links init\n')
            link_gdf[link_transaction_cols].to_csv(file, mode='a', sep=' ', index=False, header=False)
        file.close()
        return node_gdf, link_gdf


    def write_extra_attributes_header(self, file, extra_attrib_cols, attribute_type, network_fields=False):
        """
        Writes the header for network attribute and network field transaction files

        Parameters:
            - file: an open file to write the header to
            - extra_attrib_cols: The column names of the extra attributes
            - attribute_type: string that denotes the type of network object the attribute is for.
                             allowed values are NODE, LINK, TRANSIT_LINE, and TRANSIT_SEGMENT
            - network_fields: Boolean to determine if you are writing network fields (strings) or network attributes (numbers)
        Returns:
            - None
        """
        if network_fields:
            parameter_type = 'network_fields'
            default_value = 'STRING'
            prefix='#'
        else:
            parameter_type = 'extra_attributes'
            default_value = '0.0'
            prefix='@'
        file.write(f't {parameter_type}\n')
        assert attribute_type in ['NODE', 'LINK', 'TRANSIT_LINE', 'TRANSIT_SEGMENT'], "invalid attribute_type"
        col_names_string = ''
        if attribute_type == 'NODE':
            col_names_string = 'inode'
        elif attribute_type == 'LINK':
            col_names_string = 'inode,jnode'
        elif attribute_type == 'TRANSIT_LINE':
            col_names_string = 'line'
        elif attribute_type =='TRANSIT_SEGMENT':
            col_names_string = 'line,inode,jnode'

        for attr in extra_attrib_cols:
            # attribute names in EMME need to be lower case: COUNTY -> @county
            # attribute name also can't have brackets: HEADWAY[1] -> @headway1
            emme_attr = attr.replace('[','').replace(']','').lower()
            attr_string = prefix + emme_attr + ',' + attribute_type + ","+ default_value + ",'" + attr + "'\n"
            file.write(attr_string)
            col_names_string = col_names_string + ', ' + prefix + emme_attr
        file.write(f'end {parameter_type}\n')
        col_names_string += '\n'
        # column names are written before data and after header
        file.write(col_names_string)
        pass


    def write_extra_links_and_nodes_attribute_files(self, node_gdf, link_gdf):
        """
        Writes the specified extra link and node attributes to the extra link and node
        attribute transaction files.  This is necessary because the base network transaction file
        cannot include all of these extra data fields

        Extra attribute files are specifically for numbers, and network fields are for string values

        Input:
            - node_gdf: GeoDataFrame with node information
            - link_gdf: GeoDataFrame with link information
        Returns:
            - None
        """
        print("Writing extra link and node attributes file")

        # writing node file
        with open(self.extra_node_attr_file, 'w') as file:
            self.write_extra_attributes_header(file, extra_node_attributes, 'NODE')
            cols = ['node_id'] + extra_node_attributes
            # Emme does not accept null values in extra attributes
            node_gdf[cols].fillna('NA').to_csv(
                file, mode='a', sep=',', quoting=csv.QUOTE_NONNUMERIC, header=False, index=False, line_terminator='\n')
        file.close()

        # writing link file
        with open(self.extra_link_attr_file, 'w') as file:
            self.write_extra_attributes_header(file, extra_link_attributes, 'LINK')
            cols = ['A_node_id', 'B_node_id'] + extra_link_attributes
            link_gdf[cols].fillna('NA').to_csv(
                file, mode='a', sep=',', quoting=csv.QUOTE_NONNUMERIC, header=False, index=False, line_terminator='\n')
        file.close()

        # extra link attributes including link names
        roadway_names = pd.read_csv(self.link_names_file, encoding="ISO-8859-1")
        link_gdf_with_names = pd.merge(
            link_gdf,
            roadway_names,
            how='left',
            left_on='MODEL_LINK_',
            right_on='model_link_id'
        )

        for col in extra_link_network_fields:
            link_gdf_with_names[col] = link_gdf_with_names[col].str.replace('"', '').replace("'", '')

        extra_link_network_fields_file = os.path.join(self.emme_network_transaction_folder, "emme_extra_link_network_fields.txt")
        with open(self.extra_link_network_fields_file, 'w', encoding='utf-8') as file:
            self.write_extra_attributes_header(file, extra_link_network_fields, 'LINK', network_fields=True)
            cols = ['A_node_id', 'B_node_id'] + extra_link_network_fields
            link_gdf_with_names[cols].fillna('NA').to_csv(
                file, mode='a', sep=',', quoting=csv.QUOTE_NONNUMERIC, quotechar="'",
                header=False, index=False, line_terminator='\n', encoding='utf-8')
        file.close()
        pass


    def parse_transit_line_file(self):
        """
        Parses the transit.lin file output by build_new_transit_line.py file

        Returns:
            - transit_line_df: pandas dataframe with transit line data
            - stop_df: pandas dataframe with sequential stops for each transit line
        """
        # initializing variables
        line_data = []
        stop_data =[]
        line_id = -1

        # looping through each line in transit line file.
        # Each line in file is expected to correspond to a single transit Line
        with open(self.transit_lin_file, 'r') as file:
            line = file.readline()
            while line:
        #         print(line)
                # splitting line by comma and removing double quotes and new line symbols
                processed_line = line.replace('"', '').replace(', ', ',').replace('\n','')
                # need to insert comma betwen LINE and NAME before splitting by comma
                processed_line = processed_line.replace('LINE NAME', 'LINE,NAME').split(',')

                # e.g. line: LINE NAME="name", HEADWAY[0]=0,... N=1, 2, 3....
                # processed_line: ['LINE', 'NAME=name', 'HEADWAY[0]=0',... 'N=1', '2', '3'...]
                # transit_lines_df: LINE: line_id, NAME: name, HEADWAY[0]: 0,....
                # stop_df: LINE: line_id, N: 1; LINE:line_id, N: 2 ....
                data_dict = {}
                for seg in processed_line:
                    # new Transit line
                    if seg == "LINE":
                        line_id += 1
                        data_dict = {'LINE': line_id}
                    elif '=' in seg:
                        key = seg.split('=')[0].replace(' ','')
                        value = seg.split('=')[1].replace("'", '')

                        if key == 'N':
                            # stop data gets put to stop_df
                            stop_data.append({'LINE': line_id, 'stop': int(value)})
                        elif key == 'NNTIME' or key == 'ACCESS_C' or key == 'ACCESS':
                            stop_data[len(stop_data) - 1][key] = value
                        else:
                            data_dict.update({key:value})
                    # if no '=' and is a number, add that stop to stop_df
                    elif seg.replace('-','').isdigit():
                        stop_data.append({'LINE': line_id, 'stop': int(seg)})
                    else:
                        continue
                if data_dict != {}:
                    line_data.append(data_dict)
                line = file.readline()

        transit_line_df = pd.DataFrame(line_data)
        stop_df = pd.DataFrame(stop_data)
        # ACCESS_C specifies whether a mode is for access and exit (0-default), access only (1), or exit only (2)
        #  for all subsequent nodes on the line unitl the line ends or ACCESS_C is specified again
        # ACCESS can also be specified for individual stops
        if 'ACCESS_C' in stop_df.columns:
            stop_df['ACCESS'] = stop_df.groupby('LINE')['ACCESS_C'].ffill().fillna(0).astype(int)
        # If ACCESS not set in transit network, set to default value of 0
        if 'ACCESS' not in stop_df.columns:
            stop_df['ACCESS'] = 0
        stop_df['ACCESS'].fillna(0, inplace=True)
        stop_df['ACCESS'] = stop_df['ACCESS'].astype(int)
        stop_df['N'] = stop_df['stop'].abs()

        transit_line_df['emme_mode'] = transit_line_df['USERA2'].map(emme_transit_modes_dict)

        assert all(transit_line_df['emme_mode'].notna()), 'Emme Mode missing for: \n{}'.format(
            transit_line_df[transit_line_df['emme_mode'].isna()])

        lines_with_nntime_df = stop_df.groupby('LINE').count().reset_index()
        lines_with_nntime_df['uses_NNTIME'] = np.where(lines_with_nntime_df['NNTIME'] > 0, 1, 0)

        transit_line_df = pd.merge(transit_line_df, lines_with_nntime_df[['LINE', 'uses_NNTIME']], how='left', on='LINE')
        transit_line_df['keep_line'] = 1

        return transit_line_df, stop_df


    def setup_NNTIIME_variables(self, stop_df, link_gdf):
        """
        Initialize the NNTIME variables to set station-to-station time.
        (NNTIME is the Cube variable name).
        Actual station to station time is done in the create_emme_network.py script
        where actual link distances can be used when there are intermediary stops.

        TODO: Is this really necessary now that we have the NNTIME set in network import?

        Parameters:
            - stop_df: dataframe of transit stops for each transit line
            - link_gdf:
        Returns:
            - stop_link_df: stop_df with link lengths merged and NNTIME setup
        """
        # backfilling NNTIME to all nodes involved with each NNTIME
        # stop_df['NNTIME_fill'] = stop_df.groupby('LINE')['NNTIME'].bfill().astype(float)

        # merging link length
        stop_df['next_node_id'] = stop_df.groupby('LINE')['node_id'].shift(-1)
        link_cols = ['i_node', 'j_node', 'length_mi', 'TRANTIME']
        stop_link_df = pd.merge(
            stop_df,
            link_gdf[link_cols],
            how='left',
            left_on=['node_id', 'next_node_id'],
            right_on=['i_node', 'j_node'],
            validate='m:1')

        # these are set in the create_emme_network.py script
        stop_link_df['nn_trantime'] = 0
        stop_link_df['tot_nntime'] = 0

        # legacy code for NNTIME distribution. NOT VERIFIED
        # finding total length of links for NNTIME segments
        # stop_link_df['nn_tot_length'] = stop_link_df.groupby(
        #     ['LINE', 'NNTIME_fill'])['length_mi'].transform('sum')
        # # calculating the portion of each segment compared to total length
        # stop_link_df['nn_time_portion'] = stop_link_df['length_mi'] / stop_link_df['nn_tot_length']
        # # new trantime is the NNTIME * portion of total length
        # stop_link_df['nn_trantime'] = stop_link_df['nn_time_portion'] * stop_link_df['NNTIME_fill']
        # # checking to make sure all nn_trantime's sum to the total NNTIME
        # stop_link_df['nn_tot_trantime'] = stop_link_df.groupby(
        #     ['LINE', 'NNTIME_fill'])['nn_trantime'].transform('sum')
        # stop_link_df['nn_check'] = ((stop_link_df['nn_tot_trantime'] - stop_link_df['NNTIME_fill']) < .01)
        # assert all(stop_link_df[stop_link_df['NNTIME_fill'].notna()]['nn_check']), "nn_trantimes do not sum to NNTIME!!"
        #
        # # final transit skim time is set to nn_trantime if NNTIME was set, otherwise it is the link TRANTIME
        # stop_link_df['trantime_final'] = np.where(
        #     stop_link_df['nn_trantime'].isna(), stop_link_df['TRANTIME'], stop_link_df['nn_trantime'])
        return stop_link_df


    def trim_network(self,link_gdf, node_gdf, transit_line_df, stop_df):
        """
        Removes links and nodes that are not needed in the network.
        Local rodes without a transit line on them are removed.
        Nodes that do not belong to any link are removed
        Additional code exists for debugging routing issues between Cube and Emme.

        This is required to get under the Emme limit for the max number of nodes and links

        Inputs:
            - link_gdf: GeoDataFrame of link data
            - node_gdf: GeoDataFrame of node data
            - transit_line_df: dataframe of transit line data
            - stop_df: dataframe of stops for each transit line
        Returns:
            - The input dataframes trimmed of unnessesary links and nodes
        """
        # remove links that do not have any transit lines and are local roads
        link_gdf_trimmed = link_gdf[
            link_gdf['A'].isin(stop_df['N'])
            | link_gdf['B'].isin(stop_df['N'])
            | (link_gdf['FT'] != 7)] # local roads

        # remove nodes that are not on any links or transit stops
        node_gdf_trimmed = node_gdf[
            node_gdf['N'].isin(link_gdf_trimmed['A'])
            | node_gdf['N'].isin(link_gdf_trimmed['B'])]

        # remove stops that do not have links connected
        in_network = (stop_df['N'].isin(link_gdf_trimmed['A'])
                      | stop_df['N'].isin(link_gdf_trimmed['B']))
        stops_missing_links = stop_df[~in_network]

        # remove transit lines that are missing stops
        lines_missing_stops = transit_line_df[transit_line_df['LINE'].isin(stops_missing_links['LINE'])]

        # can uncomment if you do not want emme to crash on these lines
        transit_line_df_trimmed = transit_line_df
        stop_df_trimmed = stop_df
        # transit_line_df_trimmed = transit_line_df[~transit_line_df['LINE'].isin(lines_missing_stops['LINE'])]
        # stop_df_trimmed = stop_df[stop_df['LINE'].isin(transit_line_df_trimmed['LINE'])]

        if len(stops_missing_links > 0):
            stops_missing_links.to_csv(os.path.join(
                self.emme_network_transaction_folder, 'stops_without_links.csv'), index=False)
            lines_missing_stops.to_csv(os.path.join(
                self.emme_network_transaction_folder, 'lines_missing_stops_from_network.csv'), index=False)

            stop_nodes_without_links = node_gdf[node_gdf['N'].isin(stops_missing_links['N'])]
            stop_nodes_without_links.to_csv(os.path.join(
                self.emme_network_transaction_folder, 'stop_nodes_without_links.csv'), index=False)

            print("\nWARNING: stops specified in transit line file are missing from network")
            print("Stops missing links: ", stops_missing_links['N'].unique())
            print("Lines Removed: ", lines_missing_stops['NAME'], '\n')

        print("number of links after trimming: ", len(link_gdf))
        print("number of nodes after trimming: ", len(node_gdf))

        return link_gdf_trimmed, node_gdf_trimmed, transit_line_df_trimmed, stop_df_trimmed


    def create_stop_transaction_variables(self, stop_df, node_gdf, link_gdf):
        """
        Create the transit stop variables needed for the Emme transit network transaction file.
        Includes the call to setup NNTIME (station-to-station time) variables

        Parameters:
            - stop_df: dataframe of transit stops for each transit line
            - node_gdf: GeoDataFrame containing node information
            - link_gdf: GeoDataFrame containing link information
        Returns:
            - stop_df with variables for the transaction file
            - stop_transaction_cols: list of stop_df columns that need to be included in the transaction file
        """
        # negative stop numbers from cube transit line file denote no boarding or alighting
        stop_df['can_board'] = 1
        stop_df.loc[stop_df['stop'] < 0, 'can_board'] = 0

        stop_df = pd.merge(
            stop_df,
            node_gdf[['N', 'node_id', 'is_tap']],
            how='left',
            on='N'
        )

        stop_df = self.setup_NNTIIME_variables(stop_df, link_gdf)

        stop_df['dwt'] = 'dwt=+0'  # dwell time per line segment (mins), can board or alight
        stop_df.loc[stop_df['can_board'] == 0, 'dwt'] = 'dwt=#0'  # cannot board or alight at this stop
        stop_df.loc[stop_df['ACCESS'] == 1, 'dwt'] = 'dwt=<0'  # boarding only
        stop_df.loc[stop_df['ACCESS'] == 2, 'dwt'] = 'dwt=>0'  # alighting only
        stop_df['ttf'] = 'ttf=2'  # transit time function, set to ft2 = us1 which is trantime
        stop_df['us1'] = stop_df['TRANTIME'].apply(
            lambda x: 'us1=0' if pd.isna(x) else 'us1=' + str(round(x, 3)))

        # end of line conditions:
        # stop_df.loc[stop_df['next_node_id'].isna(), 'dwt'] = ''
        stop_df.loc[stop_df['next_node_id'].isna(), 'ttf'] = ''
        stop_df.loc[stop_df['next_node_id'].isna(), 'us1'] = ''

        # NOTE: there are a couple cases where a stop node is repeated in the input file
        #   (see e.g. GG_049_SB node 1469206)
        # Emme crashes when trying to route from a node to the same node, so one node is removed
        stop_df = stop_df[~((stop_df['LINE'] == stop_df['LINE'].shift(-1))
                          & (stop_df['node_id'] == stop_df['node_id'].shift(-1)))]

        # indent line when specifying nodes... this may or may not be necessary....
        stop_df['initial_separator'] = ' '
        # stop variables output to file
        # stop_transaction_cols = ['initial_separator', 'node_id', 'dwt', 'ttf', 'us1']
        # dwt applies to j node of line segment, so it needs to be written before node_id
        stop_transaction_cols = ['initial_separator', 'dwt', 'node_id', 'ttf', 'us1']

        return stop_df, stop_transaction_cols


    def create_transit_line_transaction_variables(self, transit_line_df, mode_vehtype_xwalk, headway_var):
        """
        Create the transit line variables needed for the Emme transit network transaction file.
        Includes a check to make sure every line has a headway and vehicle type

        Parameters:
            - transit_line_df: dataframe of transit lines
            - mode_vehtype_xwalk: dataframe containing map between transit mode and vehicle type
            - headway_var: column name of transit_line_df containing the headway
                        (headways change by time of day, so the right one needs to be selected)
        Returns:
            - transit_line_df with the transaction variables set
        """
        # need to assign emme_vehicle for each transit line
        # this comes from mode_vehtype_xwalk generated during vehicle transaction file creation
        transit_line_df = pd.merge(
            transit_line_df,
            mode_vehtype_xwalk[['VEHICLETYPE', 'emme_mode', 'emme_vehicle_num']],
            how='left',
            on=['emme_mode', 'VEHICLETYPE'],
            validate='many_to_one'
        )

        transit_line_df['transaction'] = 'a'
        transit_line_df['line_name'] = transit_line_df['NAME']
        transit_line_df['vehicle'] = transit_line_df['emme_vehicle_num']
        transit_line_df['headway'] = transit_line_df[headway_var].astype(float).fillna(0)
        transit_line_df['speed'] = 15  # most common XYSPEED in old network used to set default speed
        transit_line_df['descr'] = transit_line_df['LONGNAME'].apply(lambda x: "'" + x + "'")
        transit_line_df['ut1'] = 0
        transit_line_df['ut2'] = 0
        transit_line_df['ut3'] = 0

        assert all(transit_line_df['vehicle'].notna()), 'Vehicle type missing for: \n{}'.format(
            transit_line_df[transit_line_df['vehicle'].isna()])
        assert all(transit_line_df['headway'].notna()), 'Headway missing for: \n{}'.format(
            transit_line_df[transit_line_df['headway'].isna()])
        # transit_line_df.loc[transit_line_df['headway'] == '0', 'headway'] = 999  # no headway not allowed, so using max
        # Elimate transit lines from dataframe if headway = 0
        transit_line_df.loc[transit_line_df['headway'] == 0, 'keep_line'] = 0

        return transit_line_df


    def write_transit_route_to_file(self, row, file, stop_transaction_cols):
        """
        Writes a transit stop and it's required data to the transit line transaction file

        Parameters:
            - row: A row of the stop_df dataframe with the column information
            - file: transit network transaction file to write data to
            - stop_transaction_cols: list of columns in the row that should be included
        Returns:
            - None
        """
        route_string = '\n  '
        for col in stop_transaction_cols:
            route_string = route_string + ' ' + str(row[col])
        file.write(route_string)
        pass


    def write_transit_line_to_file(self, row, stop_df, file, stop_transaction_cols):
        """
        Writes a single transit line to the transit line transaction file including all stops

        Parameters:
            - row: a row of the transit_line_df dataframe
            - stop_df: dataframe of stops for each transit line
            - file: transaction file that the output should be written to
            - stop_transaction_cols: list of stop variables to write to file
        Returns:
            - None
        """
        line_string = '{transaction} {line_name} {mode} {vehicle} {headway} {speed} {descr} {ut1} {ut2} {ut3}\n'
        line_string = line_string.format(
            transaction=row['transaction'],
            line_name=row['line_name'],
            mode=row['emme_mode'],
            vehicle=row['vehicle'],
            headway=row['headway'],
            speed=row['speed'],
            descr=row['descr'],
            ut1=row['ut1'],
            ut2=row['ut2'],
            ut3=row['ut3']
        )
        file.write(line_string)

        # Not every single node has to be specified if path=yes
        # Emme says there is non-routable paths if path=no...
        file.write(' path=yes ')

        stops_for_current_line_df = stop_df.loc[stop_df['LINE'] == row['LINE']]
        stops_for_current_line_df.apply(lambda row:
            self.write_transit_route_to_file(row, file, stop_transaction_cols), axis=1)
        file.write('\n')
        # stops_for_current_line_df[stop_transaction_cols].to_csv(
        #     file, mode='a', sep=' ', header=False, index=False, quoting=csv.QUOTE_NONE, line_terminator='\n')

        pass


    def find_lines_with_created_segments(self, transit_line_df, stop_df):
        # if no link exists between stops, segments are created based on shortest path when importing into emme
        #  finding lines that have segments created
        lines_with_missing_segments = stop_df[
            stop_df['next_node_id'].notna() & stop_df['i_node'].isna()]['LINE'].unique()
        transit_line_df['has_missing_segments'] = np.where(
            transit_line_df['LINE'].isin(lines_with_missing_segments), 1, 0)

        # Writing out fixed path lines that need segments created after initial network import
        # lines_need_links_created_df = transit_line_df[
        #     (transit_line_df['has_missing_segments'] == 1) & (transit_line_df['uses_NNTIME'] == 1)]
        lines_need_links_created_df = transit_line_df[
            (transit_line_df['has_missing_segments'] == 1)
            & (transit_line_df['emme_mode'].isin(['l', 'h', 'r', 'f']))]
        lines_need_links_created_path = os.path.join(
            self.emme_network_transaction_folder, 'lines_that_need_links_created.csv')
        lines_need_links_created_df.to_csv(lines_need_links_created_path, index=False)

        lines_missing_seg_and_no_nntime_df = transit_line_df[
            (transit_line_df['has_missing_segments'] == 1)
            & (transit_line_df['uses_NNTIME'] == 0)
            & (transit_line_df['emme_mode'].isin(['l', 'h', 'r', 'f']))]

        lines_missing_seg_and_no_nntime_path = os.path.join(
            self.emme_network_transaction_folder, 'lines_missing_seg_and_no_nntime.csv')
        lines_missing_seg_and_no_nntime_df.to_csv(lines_missing_seg_and_no_nntime_path, index=False)

        # lines that need links created will be added in the create_emme_network script using the Emme API
        transit_line_df.loc[transit_line_df['LINE'].isin(lines_need_links_created_df['LINE']), 'keep_line'] = 0

        return transit_line_df, stop_df


    def write_transit_line_transaction_file(self, node_gdf, link_gdf, transit_line_df, stop_df, mode_vehtype_xwalk, headway_var):
        """
        Writing the tranist line Emme transaction file.  Includes calls to create the necessary variables
        in the transit line and stops data.

        Parameters:
            - node_gdf: GeoDataFrame with node info
            - link_gdf: GeoDataFrame with link info
            - transit_line_df: dataframe with transit line info
            - stop_df: dataframe with stop sequence for each transit line
            - mode_vehtype_xwalk: dataframe containing map between transit mode and vehicle type
            - headway_var: str containing the column in the transit_line_df that should be used for setting transit line headways

        Returns:
            - transit_line_df with transaction varibles set
            - stop_df with transaction variables set
        """
        print("Parsing input transit line file")

        stop_df, stop_transaction_cols  = self.create_stop_transaction_variables(stop_df, node_gdf, link_gdf)
        transit_line_df = self.create_transit_line_transaction_variables(
            transit_line_df, mode_vehtype_xwalk, headway_var)

        # transit_line_df, stop_df = self.find_lines_with_created_segments(transit_line_df, stop_df)

        with open(self.emme_transit_network_file, 'w') as file:
            file.write('t lines init\n')
            transit_line_df[transit_line_df['keep_line'] == 1].apply(
                lambda row:
                    self.write_transit_line_to_file(row, stop_df, file, stop_transaction_cols),
                axis=1)
        file.close()

        return transit_line_df, stop_df


    def create_transit_time_functon_transaction_file(self):
        """
        Write the transit time function transaction file.
        There are two transit time functions, ft1 set to 0 for the zero function,
        and ft2 = trantime_final * (1 + link_unreliability)

        Parameters:
            - None
        Returns:
            - None
        """
        with open(self.emme_transit_time_function_file, 'w') as file:
            file.write('t functions init\n')
            file.write('c Transit time functions (TTF)\n')
            # set transit time function to first user link field which is set to trantime_final
            file.write('a  ft1 = 0\n')
            file.write('a  ft2 = us1*(1+ul3)\n')  # link unreliability stored in ul3 / link.data3
        file.close()
        pass


    def prepare_transit_line_extra_attributes(self, transit_line_df, extra_attrib_cols):
        """
        Some fields in the transit line file can be the same as node or link attributes.
        This is not allowed an so the names of the columns need to be updated.

        Parameters:
            - transit_line_df: transit dataframe with the extra attributes
            - extra_attrib_cols: list of extra transit line attributes to be included in emme network
        Returns:
            - transit_line_df with NA's filled (Emme doesn't accept missing values)
            - output_col_type_dict: dictionary of update column names and their data type
                (data type is not currently used, could be removed in later versions)
        """
        # Creating dictionary with attr_column_name: is_float
        output_col_type_dict = {}
        for col in extra_attrib_cols:
            # Convert to float if it can so no quotes are put in transaction file around numbers
            try:
                transit_line_df[col] = transit_line_df[col].fillna(0).astype(float)
                is_float=True
            except:
                print("Could not convert", col)
                is_float=False
                pass

            # can't have same column name in nodes/links as lines
            if (col in extra_node_attributes) or (col in extra_link_attributes):
                new_col_name = 'line_' + col
                transit_line_df[new_col_name] = transit_line_df[col]
                output_col_type_dict.update({new_col_name: is_float})
            else:
                output_col_type_dict.update({col: is_float})
        return transit_line_df, output_col_type_dict


    def write_extra_transit_line_attributes_file(self, transit_line_df):
        """
        Writes extra attribute transaction file for transit lines

        Paramters:
            - transit_line_df: dataframe of transit line data
        Returns:
            - None
        """
        print("Writing transit line extra attributes file")

        # writing transit line file for output checking
        transit_line_df, output_col_type_dict = self.prepare_transit_line_extra_attributes(transit_line_df, extra_transit_line_attributes)
        transit_line_df.to_csv(self.all_transit_lines_file, index=False)

        with open(self.extra_transit_line_attr_file, 'w') as file:
            self.write_extra_attributes_header(file, list(output_col_type_dict.keys()), 'TRANSIT_LINE')
            # Emme does not accept null values in extra attributes
    #         cols = ['line_name'] + extra_transit_line_attributes
            cols = ['line_name'] + list(output_col_type_dict.keys())
            transit_line_df[transit_line_df['keep_line'] == 1][cols].fillna(0).to_csv(
                file, mode='a', sep=',', quoting=csv.QUOTE_NONNUMERIC, header=False, index=False, line_terminator='\n')
        file.close()
        pass


    def write_extra_transit_segment_attributes_file(self, stop_df, transit_line_df):
        """
        Writes the extra attributes transaction file for transit segments

        Parameters:
            - stop_df: dataframe of transit stops containing the segment information
            - transit_line_df: dataframe of transit lines needed to match stop with line
        Returns:
            - stop_attributes_df: stop_df with the extra attributes appended
        """
        print("Writing transit segment extra attributes file")

        stop_attributes_df = pd.merge(stop_df, transit_line_df[['LINE', 'NAME', 'keep_line']], how='left', on='LINE')
        # stop_attributes_df['has_nntime'] = np.where(stop_attributes_df['NNTIME_fill'].notna(), 1, 0)
        # stop_attributes_df['tot_nntime'] = stop_attributes_df['NNTIME_fill'].fillna(0)
        # stop_attributes_df['nn_trantime'] = stop_attributes_df['nn_trantime'].fillna(0)
        stop_attributes_df['link_trantime'] = stop_attributes_df['TRANTIME'].fillna(0)
        # trantime_final is currently set to link_trantime, but NNTIME will replace later if applicable
        stop_attributes_df['trantime_final'] = stop_attributes_df['TRANTIME'].fillna(0)
        stop_attributes_df.to_csv(self.all_stop_attributes_file, index=False)

        # filtering out segments that do not match to a link or a transit line (due to line being filtered out)
        stop_attributes_df = stop_attributes_df[stop_attributes_df['j_node'].notna()
                                                & stop_attributes_df['NAME'].notna()
                                                & (stop_attributes_df['keep_line'] == 1)]
        stop_attributes_df['next_node_id'] = stop_attributes_df['next_node_id'].astype(int)
        stop_attributes_df['node_id'] = stop_attributes_df['node_id'].astype(int)

        # extra_transit_segment_attributes = ['trantime_final', 'link_trantime', 'has_nntime', 'tot_nntime', 'nn_trantime']
        extra_transit_segment_attributes = ['trantime_final', 'link_trantime', 'tot_nntime', 'nn_trantime']

        with open(self.extra_transit_segment_attr_file, 'w') as file:
            self.write_extra_attributes_header(file, extra_transit_segment_attributes, 'TRANSIT_SEGMENT')
            cols = ['NAME', 'node_id', 'next_node_id'] + extra_transit_segment_attributes
            stop_attributes_df[cols].fillna('NA').to_csv(
                file, mode='a', sep=',', quoting=csv.QUOTE_NONNUMERIC, header=False, index=False, line_terminator='\n')
        file.close()

        return stop_attributes_df


    def match_station_to_tap(self, sa_gdf, node_gdf, link_gdf, stop_df, transit_line_df):
        """
        Matches stations to the most appropriate tap through the following steps:
        For each station type / mode:
            1. Find taps that connect to lines that have the same mode as the station
            2. Select the tap closest to each station for that given station type

        Creates a station attributes folder containing crosswalks between stations and taps
        and shape files for validation

        Parameters:
            - sa_gdf: GeoDataFrame of station attributes
            - node_gdf: GeoDataFrame of node data
            - link_gdf: GeoDataFrame of link data
            - stop_df: dataframe of transit stop data
            - transit_line_df: dataframe of transit lines
        Returns:
            - Dataframe with station attributes matched to taps
        """
        sa_with_taps = []
        sa_to_tap_connections = []

        for station_type in sa_gdf['Station Type'].unique():
            # print('Station attributes for Station Type: ', station_type)
            # find transit lines that have mode of station
            emme_mode = station_type_to_emme_mode_dict[station_type]
            mode_lines = transit_line_df.loc[transit_line_df['emme_mode'].isin(emme_mode), 'LINE']
            # find stops of those transit lines
            mode_stops = stop_df.loc[stop_df['LINE'].isin(mode_lines), 'node_id'].unique()

            # get the links that service the stops
            mode_tap_connectors = link_gdf[
                ((link_gdf['A_is_tap'] == 1) & (link_gdf['j_node'].isin(mode_stops)))
                | ((link_gdf['B_is_tap'] == 1) & (link_gdf['i_node'].isin(mode_stops)))]

            # get the taps at the end of the links that service the stops
            mode_taps_df = node_gdf.loc[
                node_gdf['i_node'].isin(mode_tap_connectors.loc[mode_tap_connectors['A_is_tap'] == 1, 'i_node'])
                | node_gdf['i_node'].isin(mode_tap_connectors.loc[mode_tap_connectors['B_is_tap'] == 1, 'j_node'])
            ]

            # select the stations for this mode:
            mode_sa_gdf = sa_gdf[((sa_gdf['Station Type'] == station_type)
                                 &  (sa_gdf['Use Flag'].isin(station_attribute_use_flags)))]

            def get_nearest_tap(row, taps_df):
                taps_df['sa_x'] = row.X
                taps_df['sa_y'] = row.Y
                taps_df['dist'] = np.sqrt((taps_df['sa_x'] - taps_df['X'])**2
                                          + (taps_df['sa_y'] - taps_df['Y'])**2)
                row['tap'] = taps_df.loc[taps_df['dist'].idxmin(), 'i_node']
                row['tap_dist'] = taps_df['dist'].min()
                return row

            # append closet tap id and distance to tap to the station attributes data
            mode_sa_gdf = mode_sa_gdf.apply(
                lambda row: get_nearest_tap(row, mode_taps_df), axis=1)
            mode_sa_gdf['keep_station'] = True
            mode_sa_gdf.loc[mode_sa_gdf['tap_dist'] > station_to_tap_max_dist, 'keep_station'] = False
            mode_sa_gdf.crs = sa_gdf.crs
            sa_with_taps.append(mode_sa_gdf)

            # ------- outputting validation shape files ------
            sa_filename = os.path.join(self.station_attributes_folder, 'stations_' + station_type + '.shp')
            mode_sa_gdf.to_file(sa_filename)

            mode_taps_gdf =  geopandas.GeoDataFrame(mode_taps_df,
                                                    geometry=geopandas.points_from_xy(mode_taps_df.X, mode_taps_df.Y))
            mode_taps_gdf.crs = mode_sa_gdf.crs
            taps_filename = os.path.join(self.station_attributes_folder, 'taps_' + station_type + '.shp')
            mode_taps_gdf.to_file(taps_filename)

            # creating shape file that draws a line from the station to it's matched tap
            sa_to_tap_connections_mode = pd.merge(
                mode_sa_gdf.drop(columns='geometry'),
                mode_taps_gdf.drop(columns='geometry'),
                how='left',
                left_on='tap',
                right_on='node_id',
                suffixes=('_sa', '_tap'),
            )

            sa_to_tap_connections_mode['geometry'] = sa_to_tap_connections_mode.apply(
                lambda row: shapely.geometry.LineString([(row['X_sa'], row['Y_sa']), (row['X_tap'], row['Y_tap'])]),
                axis=1)
            sa_to_tap_connections.append(sa_to_tap_connections_mode)


        sa_to_tap_connections = pd.concat(sa_to_tap_connections)
        sa_to_tap_connections.crs = cal_state_plane_VI_crs
        sa_to_tap_filename = os.path.join(self.station_attributes_folder, 'station_to_tap_connections.csv')
        sa_to_tap_connections.to_file(sa_to_tap_filename)

        return pd.concat(sa_with_taps)


    def prepare_tap_station_attributes(self, sa_with_taps):
        """
        Creates the attirbutes that will be written to the transaction file for station attributes.
        Since multiple stations can match to a single tap, different functions are needed to combine
        the station attributes for a single network entry.

        Parameters:
            - sa_with_taps: dataframe of station attributes matched to taps
        Returns:
            - station_tap_attributes: dataframe of taps with station attributes
        """
        # ---- functions used to aggregate accross stations attached to the same tap  ----
        def join_strings(x):
            x_join = '; '.join(x.fillna('').unique())
            return (x_join)

        def average_station_attributes(x):
            return round(x.dropna().mean(), 2)

        def sum_station_attributes(x):
            return x.dropna().sum()

        def average_costs(x):
            costs_to_float = x.str.replace('$','').astype(float)
            return costs_to_float.dropna().mean()

        def waited_average_costs(x, weights):
            costs_to_float = x.dropna().str.replace('$','').astype(float)
            if len(costs_to_float) <= 1:
                return costs_to_float.mean()
            weights = weights.loc[x.dropna().index]
            if weights.sum() == 0:
                return round(costs_to_float.mean(), 2)
            else:
                return round(np.average(costs_to_float, weights=weights.loc[x.dropna().index]), 2)

        tap_agg_dict = {
            'Station Name': lambda x:  join_strings(x),
            'Station Type': lambda x: join_strings(x),
            'Bike Walk': lambda x: average_station_attributes(x),
            'Bus Walk': lambda x: average_station_attributes(x),
            'PNR Walk': lambda x: average_station_attributes(x),
            'KNR Walk': lambda x: average_station_attributes(x),
            'PNR IVT': lambda x: average_station_attributes(x),
            'KNR IVT': lambda x: average_station_attributes(x),
            'Station Platform': lambda x: average_station_attributes(x),
            'Park Type': lambda x: join_strings(x),
            'Operator Parking Spaces Free': lambda x: sum_station_attributes(x),
            'Operator Parking Spaces Paid': lambda x: sum_station_attributes(x),
            'Operator Parking Spaces Permit': lambda x: sum_station_attributes(x),
            'Private Spaces': lambda x: sum_station_attributes(x),
            'Parking Cost Daily': lambda x: waited_average_costs(x, weights=sa_with_taps['Operator Parking Spaces Paid']),
            'Parking Cost Monthly': lambda x: waited_average_costs(x, weights=sa_with_taps['Operator Parking Spaces Paid']),
            'Private Cost': lambda x: waited_average_costs(x, weights=sa_with_taps['Private Spaces']),
            'PNR Split': lambda x: average_station_attributes(x),
        }

        # station names need to be under 20 characters to fit in Emme
        station_attributes_rename_dict = {
            'Station Name': 'stName',
            'Station Type': 'stType',
            'Bike Walk': 'stBikeWalk',
            'Bus Walk': 'stBusWalkTime',
            'PNR Walk': 'stPNRWalkTime',
            'KNR Walk': 'stKNRWalkTime',
            'PNR IVT': 'stPNRDriveTime',
            'KNR IVT': 'stKNRDriveTime',
            'Station Platform': 'stPlatformTime',
            'Park Type': 'stParkType',
            'Operator Parking Spaces Free': 'stFreeSpaces',
            'Operator Parking Spaces Paid': 'stPaidSpaces',
            'Operator Parking Spaces Permit': 'stPermitSpaces',
            'Private Spaces': 'stPrivateSpaces',
            'Parking Cost Daily': 'stDailyCost',
            'Parking Cost Monthly': 'stMonthlyCost',
            'Private Cost': 'stPrivateCost',
            'PNR Split': 'stPNRSplit',
        }
        # writing all stations merged to taps file
        sa_with_taps.to_csv(
            os.path.join(self.station_attributes_folder, 'all_stations.csv'),
            index=False)
        # writing stations are are removed
        sa_with_taps[sa_with_taps['keep_station'] == False].to_csv(
            os.path.join(self.station_attributes_folder, 'stations_not_included.csv'),
            index=False)
        #writing stations that are matched to the same tap
        sa_with_taps[sa_with_taps['tap'].duplicated(keep=False)].sort_values('tap').to_csv(
            os.path.join(self.station_attributes_folder, 'duplicate_taps.csv'),
            index=False)

        # removing the stations that were matched to taps farther than threshold
        sa_with_taps = sa_with_taps[sa_with_taps['keep_station']]

        station_tap_attributes = sa_with_taps.groupby('tap').agg(tap_agg_dict).rename(columns=station_attributes_rename_dict).fillna(0)
        station_tap_attributes.to_csv(os.path.join(self.station_attributes_folder, 'station_tap_attributes.csv'))
        station_tap_attributes.reset_index(inplace=True)
        return station_tap_attributes


    def write_station_attributes_transaction_files(self, station_tap_attributes):
        """
        Writes the station attributes transaction file which specifies the station
        data that should be included in each tap matched to a station.

        Parameters:
            - station_tap_attributes: dataframe of taps and their station data
        Returns:
            - None
        """

        with open(self.station_extra_attributes_file, 'w') as file:
            self.write_extra_attributes_header(file, station_extra_attributes, 'NODE')
            cols = ['tap'] + station_extra_attributes
            # Emme does not accept null values in extra attributes
            station_tap_attributes[cols].fillna('NA').to_csv(
                file, mode='a', sep=',', quoting=csv.QUOTE_NONNUMERIC, header=False, index=False, line_terminator='\n')
        file.close()

        with open(self.station_network_fields_file, 'w') as file:
            self.write_extra_attributes_header(file, station_network_field_attributes, 'NODE', network_fields=True)
            cols = ['tap'] + station_network_field_attributes
            # Emme does not accept null values in extra attributes
            station_tap_attributes[cols].fillna('NA').to_csv(
                file, mode='a', sep=',', quoting=csv.QUOTE_NONNUMERIC, header=False, index=False, line_terminator='\n')
        file.close()


    def write_station_attributes_files(self, node_gdf, link_gdf, stop_df, transit_line_df):
        """
        Reads in the station attribute data, and calls functions that match stations to taps,
        prepare the station attribute data, and writes output to the transaction file.

        Parameters:
            - node_gdf: GeoDataFrame of node data
            - link_gdf: GeoDataFrame of link data
            - stop_df: dataframe of transit stop data
            - transit_line_df: dataframe of transit lines
        Returns:
            - None
        """
        print("writing station attribute transaction files")
        if not os.path.exists(self.station_attributes_folder):
            os.mkdir(self.station_attributes_folder)

        # reading station attribute data
        sa_data = pd.read_csv(self.station_attributes_input_file)
        sa_gdf = geopandas.GeoDataFrame(sa_data, geometry=geopandas.points_from_xy(sa_data.X, sa_data.Y))
        sa_gdf.crs = cal_state_plane_VI_crs

        sa_gdf['unique_station_id'] = sa_gdf.index + 1

        sa_with_taps = self.match_station_to_tap(sa_gdf, node_gdf, link_gdf, stop_df, transit_line_df)

        sa_tap_attributes = self.prepare_tap_station_attributes(sa_with_taps)

        self.write_station_attributes_transaction_files(sa_tap_attributes)


    def make_all_emme_transaction_files(self):
        """
        Main driver calling all other methods to get transaction files created from cube data.

        Starts by loading in the input data, trimming the network to get under the Emme link and node limits,
        and then prepares and writes out all of the necessary transaction files
        """

        if not os.path.exists(self.emme_network_transaction_folder):
            os.mkdir(self.emme_network_transaction_folder)

        # ------ reading and processing input -----
        node_gdf, link_gdf = self.load_input_data()
        node_gdf = self.determine_centroid_nodes(node_gdf)
        node_gdf, link_gdf = self.renumber_nodes_for_emme(node_gdf, link_gdf)

        vehicletype_df = self.parse_vehtype_pts_file()
        transit_line_df, stop_df = self.parse_transit_line_file()

        # removing links and nodes that are not needed
        link_gdf, node_gdf, transit_line_df, stop_df = self.trim_network(
            link_gdf, node_gdf, transit_line_df, stop_df)

        # ----- writing emme transaction files -----
        # modes and vehicles
        mode_transaction_df = self.create_and_write_mode_transaction_file()
        mode_vehtype_xwalk = self.create_and_write_vehicle_transaction_file(
            vehicletype_df, transit_line_df)

        # network
        node_gdf, link_gdf = self.write_links_and_nodes_transaction_file(node_gdf, link_gdf, mode_transaction_df)
        self.write_extra_links_and_nodes_attribute_files(node_gdf, link_gdf)

        # transit network
        self.create_transit_time_functon_transaction_file()
        transit_line_df, stop_df = self.write_transit_line_transaction_file(
            node_gdf, link_gdf, transit_line_df, stop_df, mode_vehtype_xwalk, headway_var=period_to_headway_dict[self.period])
        self.write_extra_transit_line_attributes_file(transit_line_df)
        self.write_extra_transit_segment_attributes_file(stop_df, transit_line_df)
        self.write_station_attributes_files(node_gdf, link_gdf, stop_df, transit_line_df)


    def make_updated_link_attributes_file(self):
        """
        Potential improvement to just update link attributes instead of creating the whole network.
        With the newly created all streets network, there are too many links for Emme to handle,
        so the network needs to be trimmed.  This network trimming code is only implemented for the full setup.

        This method is currently not being used
        """

        node_gdf, link_gdf = self.load_input_data()
        node_gdf = self.determine_centroid_nodes(node_gdf)
        node_gdf, link_gdf = self.renumber_nodes_for_emme(node_gdf, link_gdf)

        # link_gdf = self.remove_long_walk_links(link_gdf, max_length_mi=.25)

        # writing link file
        link_attributes_to_update = ['TRANTIME', 'CTIM']
        with open(self.update_extra_link_attr_file, 'w') as file:
            self.write_extra_attributes_header(file, link_attributes_to_update, 'LINK')
            cols = ['A_node_id', 'B_node_id'] + link_attributes_to_update
            link_gdf[cols].fillna('NA').to_csv(
                file, mode='a', sep=',', quoting=csv.QUOTE_NONNUMERIC, header=False, index=False, line_terminator='\n')
        file.close()


# --------------------------------------------- Entry Point ---------------------------------------
if __name__ == "__main__":
    start_time = time.time()
    parser = argparse.ArgumentParser(description="Create a new Emme project and database with MTC defaults.")
    parser.add_argument('-p', '--trn_path', help=r"path to the trn folder, default is the current_working_folder\trn",
                        default=os.path.join(os.getcwd(), 'trn'))
    parser.add_argument('-i', '--first_iteration', help='Is this the first iteration? yes or no, default is yes', default='yes')
    args = parser.parse_args()
    assert (args.first_iteration == 'yes') or (args.first_iteration == 'no'), \
        'Please specify "yes" or "no" for the first_iteration (-i) run-time argument'

    for period in _all_periods:
        # create a class for each period
        period_emme_transaction = emme_network_conversion(args.trn_path, period)
        if args.first_iteration == 'yes':
            # create all transaction files for the time period
            period_emme_transaction.make_all_emme_transaction_files()
        else:
            period_emme_transaction.make_all_emme_transaction_files()
            # TODO: could improve run time by including network trimming code in update only link attributes
            #  also would need to change the update=False to True in import_extra_link_attributes
            #  in update_congested_link_times in create_emme_network.py
            # period_emme_transaction.make_updated_link_attributes_file()

    run_time = round(time.time() - start_time, 2)
    print("Run Time: ", run_time, "secs = ", run_time/60, " mins")
