import geopandas
import pandas as pd
import numpy as np
import shlex
import csv
import os
import argparse
import time
import re
pd.set_option("display.max_columns",250)

# ------------- run parameters ---------
# _all_periods = ['EA', 'AM', 'MD', 'PM', 'EV']
_all_periods = ['AM']


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

veh_dict = {
    'Local bus': '5', # GGT Bus
    'Express bus': '6',  # generic express bus
    'Ferry service': '60', # alameda/oakland ferry
    'Light rail': '38',  # VTA LRT 2-car train
    'Heavy rail': '41',  # BART 9-car train
    'Commuter rail': '50'  # caltrain 6-car
}

# maps time of day period to correct headway variable
period_to_headway_dict = {
    'EA': 'HEADWAY[1]',
    'AM': 'HEADWAY[2]',
    'MD': 'HEADWAY[3]',
    'PM': 'HEADWAY[4]',
    'EV': 'HEADWAY[5]',
}

# extra attributes from cube script that should be included in the Emme network
extra_node_attributes = ['OLD_NODE', 'TAPSEQ', 'FAREZONE']
extra_link_attributes = ['SPEED', 'FEET',
    'LANES_EA', 'LANES_AM', 'LANES_MD', 'LANES_PM', 'LANES_EV',
    'ML_LANES_EA', 'ML_LANES_AM', 'ML_LANES_MD', 'ML_LANES_PM', 'ML_LANES_EV',
    'USECLASS_EA', 'USECLASS_AM', 'USECLASS_MD', 'USECLASS_PM', 'USECLASS_EV',
    'ASSIGNABLE', 'TRANSIT', 'FT', 'FFS', 'TRANTIME', 'WALKDIST','WALKTIME',
    'WALK_ACCESS', 'BIKE_ACCESS', 'DRIVE_ACCES', 'BUS_ONLY', 'RAIL_ONLY',
    'OLD_A', 'OLD_B', 'CTIM', 'NTL_MODE']
extra_transit_line_attributes = ['HEADWAY[1]','HEADWAY[2]','HEADWAY[3]','HEADWAY[4]',
    'HEADWAY[5]', 'MODE', 'FARESYSTEM', 'uses_NNTIME']

# old network attributes
# extra_node_attributes = ['COUNTY', 'MODE', 'OLD_NODE', 'TAPSEQ', 'FAREZONE']
# extra_link_attributes = ['KPH', 'MINUTES', 'LANES', 'RAMP', 'SPEEDCAT', 'FEET',
#     'ASSIGNABLE', 'TRANSIT', 'USECLASS', 'FT', 'FFS', 'TRANTIME', 'WALKDIST','WALKTIME',
#     'OLD_A', 'OLD_B', 'CTIM', 'NTL_MODE']
# extra_transit_line_attributes = ['HEADWAY[1]','HEADWAY[2]','HEADWAY[3]','HEADWAY[4]',
#     'HEADWAY[5]', 'MODE', 'FARESYSTEM', 'uses_NNTIME']

# --------------------------------------------- Methods --------------------------------------------
class emme_network_conversion:
    def __init__(self, cube_network_folder, period):
        self.period = period
        self.emme_network_transaction_folder = os.path.join(
            cube_network_folder,"emme_network_transaction_files_{}".format(period))
        self.link_shapefile = os.path.join(cube_network_folder, "mtc_transit_network_{}_CONG_links.DBF".format(period))
        self.node_shapefile = os.path.join(cube_network_folder, "mtc_transit_network_{}_CONG_nodes.DBF".format(period))
        # transit_lin_file = r"E:\projects\clients\marin\2015_test_2019_02_13\trn\transitLines_new_nodes.lin"
        self.transit_lin_file = os.path.join(cube_network_folder, "transitLines_new_nodes.lin")
        self.transit_system_file = os.path.join(cube_network_folder, "transitSystem.PTS")
        self.transit_SET3_file =  os.path.join(cube_network_folder, "transitFactors_SET3.fac")
        self.node_id_crosswalk_file = os.path.join(self.emme_network_transaction_folder, "node_id_crosswalk.csv")
        self.emme_mode_transaction_file = os.path.join(self.emme_network_transaction_folder, "emme_modes.txt")
        self.emme_vehicle_transaction_file = os.path.join(self.emme_network_transaction_folder, "emme_vehicles.txt")
        self.emme_network_transaction_file = os.path.join(self.emme_network_transaction_folder, "emme_network.txt")
        self.extra_node_attr_file = os.path.join(self.emme_network_transaction_folder, "emme_extra_node_attributes.txt")
        self.extra_link_attr_file = os.path.join(self.emme_network_transaction_folder, "emme_extra_link_attributes.txt")
        self.update_extra_link_attr_file = os.path.join(self.emme_network_transaction_folder, "emme_update_extra_link_attributes.txt")
        self.emme_transit_network_file = os.path.join(self.emme_network_transaction_folder, "emme_transit_lines.txt")
        self.extra_transit_line_attr_file = os.path.join(self.emme_network_transaction_folder, "emme_extra_line_attributes.txt")
        self.extra_transit_segment_attr_file = os.path.join(self.emme_network_transaction_folder, "emme_extra_segment_attributes.txt")
        self.emme_transit_time_function_file = os.path.join(self.emme_network_transaction_folder, "emme_transit_time_function.txt")
        self.all_stop_attributes_file = os.path.join(self.emme_network_transaction_folder, "all_stop_attributes.csv")
        self.all_transit_lines_file = os.path.join(self.emme_network_transaction_folder, "all_transit_lines.csv")

    def load_input_data(self):
        print("Loading input data for", self.period, "period")
        node_gdf = geopandas.read_file(self.node_shapefile)
        link_gdf = geopandas.read_file(self.link_shapefile)

        # remove all MAZ, TAZ, and PED links.  are CRAIL links needed?
        link_gdf = link_gdf[link_gdf['CNTYPE'].isin(['TANA', 'TAP', 'CRAIL'])
                            | (link_gdf['BUS_ONLY'] == 1)]

        print("node columns: ", node_gdf.columns)
        print("link columns: ", link_gdf.columns)

        for attr in extra_node_attributes:
            assert attr in node_gdf.columns, "extra_node_attribute " + attr + " is not in the node input file"
        for attr in extra_link_attributes:
            assert attr in link_gdf.columns, "extra_link_attribute " + attr + " is not in the link input file"

        return node_gdf, link_gdf


    def determine_centroid_nodes(self, node_gdf):
        # finding centroids using information on wiki:
        # http://bayareametro.github.io/travel-model-two/input/#county-node-numbering-system
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


    def parse_transit_system_file(self):
        operator_data = []
        mode_data = []
        vehicletype_data = []
        # looping through each line in transit system file.
        with open(self.transit_system_file, 'r') as file:
            line = file.readline()
            while line:
                data_dict = {}

                # parsing operator data
                if 'OPERATOR NUMBER' in line:
                    line = line.replace('OPERATOR ', '')
                    # replace spaces with comma unless inside quote, then remove quotes
                    line_segs = ','.join(shlex.split(line)).split(',')
                    for line_seg in line_segs:
                        key = line_seg.split('=')[0]
                        value = line_seg.split('=')[1]
                        data_dict.update({key:value})
                    operator_data.append(data_dict)

                # parsing mode data
                if 'MODE NUMBER' in line:
                    line = line.replace('MODE NUMBER', 'NUMBER')
                    # replace spaces with comma unless inside quote, then remove quotes
                    line_segs = ','.join(shlex.split(line)).split(',')
                    for line_seg in line_segs:
                        key = line_seg.split('=')[0]
                        value = line_seg.split('=')[1]
                        data_dict.update({key:value})
                    mode_data.append(data_dict)

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

        operator_df = pd.DataFrame(operator_data)
        vehicletype_df = pd.DataFrame(vehicletype_data)
        vehicletype_df.rename(columns={'NUMBER': 'VEHICLETYPE'}, inplace=True)

        transit_system_mode_df = pd.DataFrame(mode_data)
        # metching NAME to emme_mode.  e.g. Local Bus -> b
        lower_emme_transit_modes_dict = dict((k.lower(), v) for k, v in emme_transit_modes_dict.items())
        transit_system_mode_df['emme_mode'] = transit_system_mode_df['NAME'].apply(
            lambda x: lower_emme_transit_modes_dict[x.lower()])
        transit_system_mode_df.rename(columns={'NUMBER': 'MODE'}, inplace=True)

        return operator_df, transit_system_mode_df, vehicletype_df


    def parse_transit_SET_file(self):
        faresystem_df = pd.DataFrame(columns=['FARESYSTEM', 'MODE'])
        # looping through each line in transit system file.
        with open(self.transit_SET3_file, 'r') as file:
            line = file.readline()
            while line:
                data_dict = {}

                # parsing faresystem data from file
                if 'FARESYSTEM=' in line:
                    # FARESYSTEM=1, MODE=12-13\n -> FARESYSTEM: 1, MODE: 12;  FARESYSTEM 1, MODE: 13
                    line_segs = line.replace(' ','').replace('\n', '').split(',')
                    faresystem = line_segs[0].split('=')[1]
                    mode = line_segs[1].split('=')[1]
                    if '-' in mode:
                        first_mode_num = mode.split('-')[0]
                        last_mode_num = mode.split('-')[1]
                        for mode_num in range(int(first_mode_num), int(last_mode_num) + 1):
                            faresystem_df.loc[len(faresystem_df)] = [faresystem, str(mode_num)]
                    else:
                        faresystem_df.loc[len(faresystem_df)] = [faresystem, mode]
                # read next line
                line = file.readline()
        return faresystem_df


    def create_and_write_mode_transaction_file(self, write_file=True):
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


    def create_and_write_vehicle_transaction_file(self, vehicletype_df, transit_line_df, transit_system_mode_df):
        print("Writing vehicle transaction file")
        # need to generate crosswalk between vehicletype, mode code, and emme mode
        mode_vehtype_xwalk = transit_line_df.groupby(
            ['MODE', 'VEHICLETYPE']).count().reset_index()[['MODE', 'VEHICLETYPE']]
        # emme mode is already in transit_system_mode_df
        mode_vehtype_xwalk = pd.merge(mode_vehtype_xwalk, transit_system_mode_df, how='left', on='MODE')

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
        # NTL_MODE no longer uniquely identifies walk links
        # link_gdf.loc[link_gdf['NTL_MODE'] == 2, 'modes'] = 'w'  # walk links
        # link_gdf.loc[link_gdf['FREEWAY'] == 1, 'modes'] = link_gdf[  # remove walk from freeways
        #     link_gdf['FREEWAY'] == 1]['modes'].apply(lambda x: x.replace('w', ''))
        link_gdf['type'] = 1
        # network can have different number of lanes for each time period
        link_gdf['lanes'] = link_gdf['LANES_' + self.period]
        # NOTE: lanes can't be larger than 9 (there are two links with 16 lanes!)
        link_gdf.loc[link_gdf['lanes'] > 9, 'lanes'] = 9
        link_gdf['volume_delay_function'] = 1
        link_gdf['user1'] = link_gdf['TRANTIME'].round(4)  # set trantime for transit time function to access
        link_gdf['user2'] = link_gdf['WALKTIME']  # auxiliariy transit walktime
        link_gdf['user3'] = 0

        # required order for link transaction file
        link_transaction_cols = ['transaction', 'i_node', 'j_node', 'length_mi', 'modes', 'type', 'lanes',
                                 'volume_delay_function', 'user1', 'user2', 'user3']
        return link_gdf, link_transaction_cols


    def remove_long_walk_links(self, link_gdf, max_length_mi):
        long_walk_links = ((link_gdf['dist_between_nodes_mi'] > max_length_mi) & (link_gdf['NTL_MODE'] == 2))
        print("Total number of walk links: ", len(link_gdf[link_gdf['NTL_MODE'] == 2]))
        print("Number of long walk links removed: ", long_walk_links.sum())
        link_gdf = link_gdf[~long_walk_links]
        print("Walk links remaining: ", len(link_gdf[link_gdf['NTL_MODE'] == 2]))
        return link_gdf


    def write_links_and_nodes_transaction_file(self, node_gdf, link_gdf, mode_transaction_df):
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


    def write_extra_attributes_header(self, file, extra_attrib_cols, attribute_type):
        file.write('t extra_attributes\n')
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
            attr_string = '@' + emme_attr + ',' + attribute_type + ",0.0,'" + attr + "'\n"
            file.write(attr_string)
            col_names_string = col_names_string + ', @' + emme_attr
        file.write('end extra_attributes\n')
        col_names_string += '\n'
        # column names are written before data and after header
        file.write(col_names_string)
        pass


    def write_extra_links_and_nodes_attribute_files(self, node_gdf, link_gdf):
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
        pass


    def parse_transit_line_file(self):
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
                        value = seg.split('=')[1]

                        if key == 'N':
                            # stop data gets put to stop_df
                            stop_data.append({'LINE': line_id, 'stop': int(value)})
                        elif key == 'NNTIME' or key == 'ACCESS_C':
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
        # Filling ACCESS explicitly
        # stop_df['ACCESS'] = stop_df.groupby('LINE')['ACCESS_C'].ffill().fillna(0).astype(int)
        # Is not set in updated network.  setting ACCESS to default value of 0
        stop_df['ACCESS'] = 0
        stop_df['N'] = stop_df['stop'].abs()

        transit_line_df['VEHICLETYPE'] = transit_line_df['USERA2'].map(veh_dict)
        transit_line_df['emme_mode'] = transit_line_df['USERA2'].map(emme_transit_modes_dict)

        assert all(transit_line_df['emme_mode'].notna()), 'Emme Mode missing for: \n{}'.format(
            transit_line_df[transit_line_df['emme_mode'].isna()])

        lines_with_nntime_df = stop_df.groupby('LINE').count().reset_index()
        lines_with_nntime_df['uses_NNTIME'] = np.where(lines_with_nntime_df['NNTIME'] > 0, 1, 0)

        transit_line_df = pd.merge(transit_line_df, lines_with_nntime_df[['LINE', 'uses_NNTIME']], how='left', on='LINE')
        transit_line_df['keep_line'] = 1

        return transit_line_df, stop_df


    def setup_NNTIIME_variables(self, stop_df, link_gdf):
        # NNTIME is the Cube variable containing station-to-station time
        # It is set after the network import, but we initialize the variables used here

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


    def create_stop_transaction_variables(self, stop_df, node_gdf, link_gdf):
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


    def create_transit_line_transaction_variables(self, transit_line_df, transit_system_mode_df, mode_vehtype_xwalk, headway_var):
        # transit_line_df['mode'] = transit_line_df['MODE'].astype(int)
        # need to assign emme_mode for each transit line. this comes from transitSystem.PTS file
        #    new network has it in transit line file
        # transit_line_df = pd.merge(
        #     transit_line_df,
        #     transit_system_mode_df[['MODE', 'emme_mode']],
        #     how='left',
        #     on='MODE',
        #     validate='many_to_one'
        # )
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
        route_string = '\n  '
        for col in stop_transaction_cols:
            route_string = route_string + ' ' + str(row[col])
        file.write(route_string)
        pass


    def write_transit_line_to_file(self, row, stop_df, file, stop_transaction_cols):
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


    def write_transit_line_transaction_file(self, node_gdf, link_gdf, transit_line_df, stop_df, transit_system_mode_df, mode_vehtype_xwalk, headway_var):
        print("Parsing input transit line file")

        stop_df, stop_transaction_cols  = self.create_stop_transaction_variables(stop_df, node_gdf, link_gdf)
        transit_line_df = self.create_transit_line_transaction_variables(
            transit_line_df, transit_system_mode_df, mode_vehtype_xwalk, headway_var)

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
        with open(self.emme_transit_time_function_file, 'w') as file:
            file.write('t functions init\n')
            file.write('c Transit time functions (TTF)\n')
            # set transit time function to first user link field which is set to trantime_final
            file.write('a  ft1 = 0\n')
            file.write('a  ft2 = us1*(1+ul3)\n')  # link unreliability stored in ul3 / link.data3
        file.close()
        pass


    def prepare_transit_line_extra_attributes(self, transit_line_df, extra_attrib_cols):
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
        print("Writing transit line extra attributes file")

        # cols = ['line_name'] + extra_transit_line_attributes
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

        # extra_transit_segment_attributes = ['trantime_final', 'link_trantime', 'has_nntime', 'tot_nntime', 'nn_trantime']
        extra_transit_segment_attributes = ['trantime_final', 'link_trantime', 'tot_nntime', 'nn_trantime']

        with open(self.extra_transit_segment_attr_file, 'w') as file:
            self.write_extra_attributes_header(file, extra_transit_segment_attributes, 'TRANSIT_SEGMENT')
            cols = ['NAME', 'node_id', 'next_node_id'] + extra_transit_segment_attributes
            stop_attributes_df[cols].fillna('NA').to_csv(
                file, mode='a', sep=',', quoting=csv.QUOTE_NONNUMERIC, header=False, index=False, line_terminator='\n')
        file.close()


        return stop_attributes_df


    def make_all_emme_transaction_files(self):
        if not os.path.exists(self.emme_network_transaction_folder):
            os.mkdir(self.emme_network_transaction_folder)

        # ------ reading and processing input -----
        node_gdf, link_gdf = self.load_input_data()
        node_gdf = self.determine_centroid_nodes(node_gdf)
        node_gdf, link_gdf = self.renumber_nodes_for_emme(node_gdf, link_gdf)

        operator_df, transit_system_mode_df, vehicletype_df = self.parse_transit_system_file()
        transit_line_df, stop_df = self.parse_transit_line_file()
        # merge FARESYSTEM to transit_lines
        # faresystem is already included in new transitline file
        # faresystem_df = self.parse_transit_SET_file()
        # transit_line_df = pd.merge(transit_line_df, faresystem_df, how='left', on='MODE')

        # remove links that do not have any transit lines and are local roads
        link_gdf = link_gdf[
            link_gdf['A'].isin(stop_df['N'])
            | link_gdf['B'].isin(stop_df['N'])
            | (link_gdf['FT'] != 7)] # local roads

        # remove nodes that are not on any links or transit stops
        node_gdf = node_gdf[node_gdf['N'].isin(link_gdf['A'])
                            | node_gdf['N'].isin(link_gdf['B'])
                            | node_gdf['N'].isin(stop_df['N'])]

        print("number of links: ", len(link_gdf))
        print("number of nodes: ", len(node_gdf))

        # ----- writing emme transaction files -----
        # modes and vehicles
        mode_transaction_df = self.create_and_write_mode_transaction_file()
        mode_vehtype_xwalk = self.create_and_write_vehicle_transaction_file(
            vehicletype_df, transit_line_df, transit_system_mode_df)

        # network
        node_gdf, link_gdf = self.write_links_and_nodes_transaction_file(node_gdf, link_gdf, mode_transaction_df)
        self.write_extra_links_and_nodes_attribute_files(node_gdf, link_gdf)

        # transit network
        self.create_transit_time_functon_transaction_file()
        transit_line_df, stop_df = self.write_transit_line_transaction_file(
            node_gdf, link_gdf, transit_line_df, stop_df, transit_system_mode_df, mode_vehtype_xwalk, headway_var=period_to_headway_dict[self.period])
        self.write_extra_transit_line_attributes_file(transit_line_df)
        self.write_extra_transit_segment_attributes_file(stop_df, transit_line_df)


    def make_updated_link_attributes_file(self):

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
        period_emme_transaction = emme_network_conversion(args.trn_path, period)
        if args.first_iteration == 'yes':
            period_emme_transaction.make_all_emme_transaction_files()
        else:
            period_emme_transaction.make_updated_link_attributes_file()

    run_time = round(time.time() - start_time, 2)
    print("Run Time: ", run_time, "secs = ", run_time/60, " mins")
