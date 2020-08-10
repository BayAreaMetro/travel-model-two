import geopandas
import pandas as pd
import numpy as np
import csv
import os
import time
pd.set_option("display.max_columns",250)

# ------------- input files------------
cube_network_data_folder = os.path.join(os.getcwd(), "cube_network_data")
link_shapefile = os.path.join(cube_network_data_folder, "mtc_transit_network_AM_CONG.shp")
node_shapefile = os.path.join(cube_network_data_folder, "nodes_mtc_transit_network_AM_CONG.shp")
transit_modes_file = os.path.join(cube_network_data_folder, "transit_modes.csv")
# transit_lin_file = r"E:\projects\clients\marin\2015_test_2019_02_13\trn\transitLines_new_nodes.lin"
transit_lin_file = os.path.join(cube_network_data_folder, "transitLines_new_nodes.lin")

# ------------- output files------------
emme_network_transaction_folder = os.path.join(os.getcwd(),"emme_network_transaction_files")
node_id_crosswalk_file = os.path.join(emme_network_transaction_folder, "node_id_crosswalk.csv")
emme_mode_transaction_file = os.path.join(emme_network_transaction_folder, "emme_modes.txt")
emme_vehicle_transaction_file = os.path.join(emme_network_transaction_folder, "emme_vehicles.txt")
emme_network_transaction_file = os.path.join(emme_network_transaction_folder, "emme_network.txt")
extra_node_attr_file = os.path.join(emme_network_transaction_folder, "emme_extra_node_attributes.txt")
extra_link_attr_file = os.path.join(emme_network_transaction_folder, "emme_extra_link_attributes.txt")
emme_transit_network_file = os.path.join(emme_network_transaction_folder, "emme_transit_lines.txt")
extra_transit_line_attr_file = os.path.join(emme_network_transaction_folder, "emme_extra_line_attributes.txt")

# ------------- run parameters ---------
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

# maps transit 'Mode Group' defined in TM2 to Emme vehicle number
# http://bayareametro.github.io/travel-model-two/input/#transit-modes
emme_vehicle_dict = {
    'Local bus': 1,
    'Express Bus': 2,
    'Express bus': 2,
    'Ferry service': 3,
    'Light rail': 4,
    'Heavy rail': 5,
    'Commuter rail': 6,
}

# vehicle definitions: number, description, mode letter, seated capacity, and total capacity
# needs to be consistent with the above dictionaries
local_bus_veh = {'vehicle': 1, 'descr': 'local_bus', 'mode': 'b', 'caps': 30, 'capt': 50}
exp_bus_veh = {'vehicle': 2, 'descr': 'exp_bus', 'mode': 'x', 'caps': 30, 'capt': 50}
ferry_veh = {'vehicle': 3, 'descr': 'ferry', 'mode': 'f', 'caps': 75, 'capt': 150}
light_rail_veh = {'vehicle': 4, 'descr': 'light_rail', 'mode': 'l', 'caps': 50, 'capt': 75}
heavy_rail_veh = {'vehicle': 5, 'descr': 'heavy_rail', 'mode': 'h', 'caps': 100, 'capt': 150}
comm_rail_veh = {'vehicle': 6, 'descr': 'comm_rail', 'mode': 'r', 'caps': 100, 'capt': 150}

# extra attributes from cube script that should be included in the Emme network
extra_node_attributes = ['COUNTY', 'MODE', 'OLD_NODE', 'TAPSEQ']
extra_link_attributes = ['KPH', 'MINUTES', 'LANES', 'RAMP', 'SPEEDCAT', 'FEET',
    'ASSIGNABLE', 'TRANSIT', 'USECLASS', 'FT', 'FFS', 'TRANTIME', 'WALKDIST','WALKTIME',
    'OLD_A', 'OLD_B', 'CTIM']
extra_transit_line_attributes = ['HEADWAY[1]','HEADWAY[2]','HEADWAY[3]','HEADWAY[4]',
    'HEADWAY[5]']

# --------------------------------------------- Methods --------------------------------------------
def load_input_data():
    print("Loading input data")
    # node_gdf = pd.DataFrame()
    # link_gdf = pd.DataFrame()
    node_gdf = geopandas.read_file(node_shapefile)
    link_gdf = geopandas.read_file(link_shapefile)
    transit_modes_df = pd.read_csv(transit_modes_file)
    transit_modes_df['emme_mode'] = transit_modes_df['mode_group'].apply(lambda x: emme_transit_modes_dict[x])
    transit_modes_df['vehicle'] = transit_modes_df['mode_group'].apply(lambda x: emme_vehicle_dict[x])

    for attr in extra_node_attributes:
        assert attr in node_gdf.columns, "extra_node_attribute " + attr + " is not in the node input file"
    for attr in extra_link_attributes:
        assert attr in link_gdf.columns, "extra_link_attribute " + attr + " is not in the link input file"

    return node_gdf, link_gdf, transit_modes_df


def determine_centroid_nodes(node_gdf):
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
    num_centroids_needed = num_tazs + num_taps

    print("Total number of nodes:", num_nodes)
    print("Number of TAZ centroid nodes:", num_tazs)
    print("Number of External TAZ centroid nodes:", num_ext_tazs)
    print("Number of TAP centroid nodes:", num_taps)
    print("Number of MAZ centroid nodes:", num_mazs)
    print("Number of Centroids needed (TAZ + TAP): ", num_centroids_needed)
    return node_gdf


def renumber_nodes_for_emme(node_gdf, link_gdf):
    # NOTE: Node ID's need to be less than 1,000,000 for import into Emme
    node_gdf['node_id'] = pd.Series(range(1,len(node_gdf)+1))

    # merging new node_ids to the link and nodes files
    link_gdf = pd.merge(
        link_gdf,
        node_gdf[['N','node_id', 'is_tap']],
        how='left',
        left_on='A',
        right_on='N'
    )
    link_gdf.drop(columns='N', inplace=True)
    link_gdf.rename(columns={'node_id': 'A_node_id', 'is_tap': 'A_is_tap'}, inplace=True)

    link_gdf = pd.merge(
        link_gdf,
        node_gdf[['N','node_id', 'is_tap']],
        how='left',
        left_on='B',
        right_on='N'
    )
    link_gdf.drop(columns='N', inplace=True)
    link_gdf.rename(columns={'node_id': 'B_node_id', 'is_tap': 'B_is_tap'}, inplace=True)

    # writing node crosswalk table for reference if needed
    node_gdf[['OLD_NODE', 'N', 'node_id']].to_csv(node_id_crosswalk_file, index=False, header=True)
    return node_gdf, link_gdf


def create_and_write_mode_transaction_file():
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
    mode_transaction_df['ctc'] = pd.NA  # operating cost/hour. Only needed for mode type 2 and 3
    mode_transaction_df.loc[mode_transaction_df['type'].isin([1,3]), 'ctc'] = 0
    mode_transaction_df['cdc'] = pd.NA  # operating cost/unit length. Only needed for mode type 2 and 3
    mode_transaction_df.loc[mode_transaction_df['type'].isin([1,3]), 'cdc'] = 0
    mode_transaction_df['etc'] = pd.NA  # energy consumption/hour. Only needed for mode type 2 and 3
    mode_transaction_df.loc[mode_transaction_df['type'].isin([1,3]), 'etc'] = 0
    mode_transaction_df['edc'] = pd.NA  # energy consumption/length. Only needed for mode type 2 and 3
    mode_transaction_df.loc[mode_transaction_df['type'].isin([1,3]), 'edc'] = 0
    mode_transaction_df['speed'] = pd.NA  # speed, only for type = 3 (aux transit mode speed)
    mode_transaction_df.loc[mode_transaction_df['type'] == 3, 'speed'] = 5
    mode_transaction_df

    assert all(pd.Series(emme_transit_modes_dict).isin(mode_transaction_df['mode'].values)), \
        "Mode in the emme_transit_modes_dict is not listed in  the mode transaction file"

    with open(emme_mode_transaction_file, 'w') as file:
        file.write('t modes init\n')
        mode_transaction_df.to_csv(file, mode='a', sep=' ', index=False, header=False)
    file.close()
    return mode_transaction_df


def create_and_write_vehicle_transaction_file():
    print("Writing vehicle transaction file")
    columns=['vehicle', 'descr', 'mode', 'caps', 'capt']
    veh_transaction_df = pd.DataFrame(columns=columns)

    veh_transaction_df  = veh_transaction_df.append(local_bus_veh, ignore_index=True)
    veh_transaction_df  = veh_transaction_df.append(exp_bus_veh, ignore_index=True)
    veh_transaction_df  = veh_transaction_df.append(ferry_veh, ignore_index=True)
    veh_transaction_df  = veh_transaction_df.append(light_rail_veh, ignore_index=True)
    veh_transaction_df  = veh_transaction_df.append(heavy_rail_veh, ignore_index=True)
    veh_transaction_df  = veh_transaction_df.append(comm_rail_veh, ignore_index=True)
    veh_transaction_df['transaction'] = 'a'
    veh_transaction_df['ctc'] = 0  # operating cost/hr
    veh_transaction_df['cdc'] = 0  # operating cost/unit length
    veh_transaction_df['etc'] = 0  # operating energy/hr
    veh_transaction_df['edc'] = 0  # operating energy/unit length
    veh_transaction_df['auto'] = 2  # auto equivalent of the vehicle
    veh_transaction_df['fleet'] = 1 # not actually used, included for backwards compatibility
    veh_transaction_df

    # required order for vehicle transaction file
    veh_output_cols = ['transaction', 'vehicle', 'descr', 'mode', 'fleet', 'caps',
                       'capt', 'ctc', 'cdc', 'etc', 'edc', 'auto']

    with open(emme_vehicle_transaction_file, 'w') as file:
        file.write('t vehicles init\n')
        veh_transaction_df[veh_output_cols].to_csv(file, mode='a', sep=' ', index=False, header=False)
    file.close()
    return veh_transaction_df


def create_emme_nodes_input(node_gdf):
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


def create_emme_links_input(link_gdf, mode_transaction_df):
    all_modes_str = ''
    for mode in mode_transaction_df['mode'].values:
        all_modes_str = all_modes_str + mode

    # adding required fields for the node transaction file
    link_gdf['transaction'] = 'a'
    link_gdf['i_node'] = link_gdf['A_node_id']
    link_gdf['j_node'] = link_gdf['B_node_id']
    link_gdf['length_ft'] = link_gdf['FEET']
    link_gdf['modes'] = all_modes_str
    link_gdf.loc[link_gdf['A_is_tap'] == 1, 'modes'] = 'a'  # access
    link_gdf.loc[link_gdf['B_is_tap'] == 1, 'modes'] = 'e'  # eggress
    link_gdf.loc[link_gdf['FREEWAY'] == 1, 'modes'] = link_gdf[  # remove walk from freeways
        link_gdf['FREEWAY'] == 1]['modes'].apply(lambda x: x.replace('w', ''))
    link_gdf['type'] = 1
    link_gdf['lanes'] = link_gdf['LANES']
    # NOTE: lanes can't be larger than 9 (there are two links with 16 lanes!)
    link_gdf.loc[link_gdf['lanes'] > 9, 'lanes'] = 9
    link_gdf['volume_delay_function'] = 1
    link_gdf['user1'] = 0
    link_gdf['user2'] = 0
    link_gdf['user3'] = 0

    # required order for link transaction file
    link_transaction_cols = ['transaction', 'i_node', 'j_node', 'length_ft', 'modes', 'type', 'lanes',
                             'volume_delay_function', 'user1', 'user2', 'user3']
    return link_gdf, link_transaction_cols


def write_links_and_nodes_tranaction_file(node_gdf, link_gdf, mode_transaction_df):
    print("Writing emme network file")

    node_gdf, node_transaction_cols = create_emme_nodes_input(node_gdf)
    link_gdf, link_transaction_cols = create_emme_links_input(link_gdf, mode_transaction_df)

    with open(emme_network_transaction_file, 'w') as file:
        file.write('t nodes init\n')
        node_gdf[node_transaction_cols].to_csv(file, mode='a', sep=' ', index=False, header=False)
        file.write('t links init\n')
        link_gdf[link_transaction_cols].to_csv(file, mode='a', sep=' ', index=False, header=False)
    file.close()
    return node_gdf, link_gdf


def write_extra_attributes_header(file, extra_attrib_cols, attribute_type):
    file.write('t extra_attributes\n')
    assert attribute_type in ['NODE', 'LINK', 'TRANSIT_LINE'], "invalid attribute_type"
    col_names_string = ''
    if attribute_type == 'NODE':
        col_names_string = 'inode'
    elif attribute_type == 'LINK':
        col_names_string = 'inode,jnode'
    elif attribute_type == 'TRANSIT_LINE':
        col_names_string = 'line'

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


def write_extra_links_and_nodes_attribute_files(node_gdf, link_gdf):
    print("Writing extra link and node attributes file")

    # writing node file
    with open(extra_node_attr_file, 'w') as file:
        write_extra_attributes_header(file, extra_node_attributes, 'NODE')
        cols = ['node_id'] + extra_node_attributes
        # Emme does not accept null values in extra attributes
        node_gdf[cols].fillna('NA').to_csv(
            file, mode='a', sep=',', quoting=csv.QUOTE_NONNUMERIC, header=False, index=False, line_terminator='\n')
    file.close()

    # writing link file
    with open(extra_link_attr_file, 'w') as file:
        write_extra_attributes_header(file, extra_link_attributes, 'LINK')
        cols = ['A_node_id', 'B_node_id'] + extra_link_attributes
        link_gdf[cols].fillna('NA').to_csv(
            file, mode='a', sep=',', quoting=csv.QUOTE_NONNUMERIC, header=False, index=False, line_terminator='\n')
    file.close()
    pass


def parse_transit_line_file():
    # initializing variables
    line_data = []
    stop_data =[]
    line_id = -1

    # looping through each line in transit file.
    # Each line in file is expected to correspond to a single transit Line
    with open(transit_lin_file, 'r') as file:
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

    stop_df = pd.DataFrame(stop_data)
    transit_line_df = pd.DataFrame(line_data)

    return transit_line_df, stop_df


def create_stop_transaction_variables(stop_df, node_gdf):
    stop_df['N'] = stop_df['stop'].abs()
    # negative stop numbers from cube transit line file denote no boarding or alighting
    stop_df['can_board'] = 1
    stop_df.loc[stop_df['stop'] < 0, 'can_board'] = 0

    stop_df = pd.merge(
        stop_df,
        node_gdf[['N', 'node_id', 'is_tap']],
        how='left',
        on='N'
    )
    stop_df['dwt'] = 'dwt=0'  # dwell time per line segment (mins)
    stop_df.loc[stop_df['can_board'] == 0, 'dwt'] = 'dwt=#0'  # cannot board or alight at this stop
    stop_df['ttf'] = 'ttf=0'  # transit time function

    # NOTE: there are a couple cases where a stop node is repeated in the input file
    #   (see e.g. GG_049_SB node 1469206)
    # Emme crashes when trying to route from a node to the same node, so one node is removed
    stop_df = stop_df[~((stop_df['LINE'] == stop_df['LINE'].shift(-1))
                      & (stop_df['node_id'] == stop_df['node_id'].shift(-1)))]

    # file needs an indent when specifying nodes
    stop_df['initial_separator'] = ' '
    # stop variables output to file
    stop_transaction_cols = ['initial_separator', 'node_id', 'dwt', 'ttf']

    return stop_df, stop_transaction_cols


def create_transit_line_transaction_variables(transit_line_df, transit_modes_df, headway_var):
    transit_line_df['mode'] = transit_line_df['MODE'].astype(int)
    transit_line_df = pd.merge(
        transit_line_df,
        transit_modes_df[['mode', 'emme_mode', 'vehicle']].drop_duplicates('mode'),
        how='left',
        on='mode',
        validate='many_to_one'
    )
    # mode 88 missing from table pulled from TM2 github
    transit_line_df.loc[transit_line_df['MODE'] == '88',
        'vehicle'] = emme_vehicle_dict['Express Bus']
    transit_line_df.loc[transit_line_df['MODE'] == '88',
        'emme_mode'] = emme_transit_modes_dict['Express Bus']


    transit_line_df['transaction'] = 'a'
    transit_line_df['line_name'] = transit_line_df['NAME']
    transit_line_df['headway'] = transit_line_df[headway_var]
    # FIXME: Elimate transit lines from dataframe if headway = 0?
    transit_line_df.loc[transit_line_df['headway'] == '0', 'headway'] = 999  # no headway not allowed, so using max
    transit_line_df['speed'] = 50  # NOTE: default speed
    transit_line_df['descr'] = transit_line_df['USERA1'].apply(lambda x: "'" + x + "'")
    transit_line_df['ut1'] = 0
    transit_line_df['ut2'] = 0
    transit_line_df['ut3'] = 0
    return transit_line_df


def trim_bad_transit_lines(transit_line_df, stop_df):
    print("WARNING: removing transit lines!")
    # no route from node 155433 to 153756 (looks like a network error -- missing tiny link)
    bad_lines = stop_df[stop_df['node_id'] == 153756]['LINE'].unique()
    print(len(bad_lines), " transit routes go through node_id 153756 and were removed")
    transit_line_df = transit_line_df[~transit_line_df['LINE'].isin(bad_lines)]

    # two one-way streets meet facing eachother at node 347877
    bad_lines = stop_df[stop_df['node_id'] == 347877]['LINE'].unique()
    print(len(bad_lines), " transit routes go through node_id 347877 and were removed")
    transit_line_df = transit_line_df[~transit_line_df['LINE'].isin(bad_lines)]

    # two one-way streets depart from node 400225, so that node is not routeable
    bad_lines = stop_df[stop_df['node_id'] == 400225]['LINE'].unique()
    print(len(bad_lines), " transit routes go through node_id 400225 and were removed")
    transit_line_df = transit_line_df[~transit_line_df['LINE'].isin(bad_lines)]

    # two one-way streets depart from node 83668, so that node is not routeable
    bad_lines = stop_df[stop_df['node_id'] == 83668]['LINE'].unique()
    print(len(bad_lines), " transit routes go through node_id 83668 and were removed")
    transit_line_df = transit_line_df[~transit_line_df['LINE'].isin(bad_lines)]

    # centroid nodes are not allowed on route in Emme
    bad_lines = stop_df[stop_df['is_tap'] == 1]['LINE'].unique()
    print(len(bad_lines), " transit routes going through centroid nodes were removed")
    transit_line_df = transit_line_df[~transit_line_df['LINE'].isin(bad_lines)]

    return transit_line_df


def write_transit_route_to_file(row, file, stop_transaction_cols):
    route_string = '\n  '
    for col in stop_transaction_cols:
        route_string = route_string + ' ' + str(row[col])
    file.write(route_string)
    pass


def write_transit_line_to_file(row, stop_df, file, stop_transaction_cols):
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
        write_transit_route_to_file(row, file, stop_transaction_cols), axis=1)
    file.write('\n')
    # stops_for_current_line_df[stop_transaction_cols].to_csv(
    #     file, mode='a', sep=' ', header=False, index=False, quoting=csv.QUOTE_NONE, line_terminator='\n')

    pass


def write_transit_line_transaction_file(node_gdf, transit_modes_df):
    print("Parsing input transit line file")

    transit_line_df, stop_df = parse_transit_line_file()
    stop_df, stop_transaction_cols  = create_stop_transaction_variables(stop_df, node_gdf)
    transit_line_df = create_transit_line_transaction_variables(
        transit_line_df, transit_modes_df, 'HEADWAY[2]')

    transit_line_df = trim_bad_transit_lines(transit_line_df, stop_df)

    with open(emme_transit_network_file, 'w') as file:
        file.write('t lines init\n')
        transit_line_df.apply(
            lambda row:
                write_transit_line_to_file(row, stop_df, file, stop_transaction_cols),
            axis=1)
    file.close()

    return transit_line_df, stop_df


def prepare_transit_link_extra_attributes(transit_line_df, extra_attrib_cols):
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


def write_extra_attributes_header_dict(file, output_col_type_dict, attribute_type):
    file.write('t extra_attributes\n')
    assert attribute_type in ['NODE', 'LINK', 'TRANSIT_LINE'], "invalid attribute_type"
    col_names_string = ''
    if attribute_type == 'NODE':
        col_names_string = 'inode'
    elif attribute_type == 'LINK':
        col_names_string = 'inode,jnode'
    elif attribute_type == 'TRANSIT_LINE':
        col_names_string = 'line'

    for attr, is_float in output_col_type_dict.items():
        if is_float:
            default_value = str(0.0)
        else:
            default_value = "'NA'"

        # attribute names in EMME need to be lower case: COUNTY -> @county
        # attribute name also can't have brackets: HEADWAY[1] -> @headway1
        emme_attr = attr.replace('[','').replace(']','').lower()
        attr_string = '@' + emme_attr + ',' + attribute_type + "," + default_value + ",'" + attr + "'\n"
        file.write(attr_string)
        col_names_string = col_names_string + ', @' + emme_attr
    file.write('end extra_attributes\n')
    col_names_string += '\n'
    # column names are written before data and after header
    file.write(col_names_string)
    pass


def write_extra_transit_link_attributes_file(transit_line_df):
    print("Writing transit link extra attributes file")

    # cols = ['line_name'] + extra_transit_line_attributes
    # transit_line_df, output_col_type_dict = prepare_transit_link_extra_attributes(transit_line_df, cols)


    with open(extra_transit_line_attr_file, 'w') as file:
        write_extra_attributes_header(file, extra_transit_line_attributes, 'TRANSIT_LINE')
        # write_extra_attributes_header_dict(file, output_col_type_dict, 'TRANSIT_LINE')
        # Emme does not accept null values in extra attributes
        cols = ['line_name'] + extra_transit_line_attributes
        transit_line_df[cols].fillna(0).to_csv(
            file, mode='a', sep=',', quoting=csv.QUOTE_NONNUMERIC, header=False, index=False, line_terminator='\n')
    file.close()
    pass


# --------------------------------------------- Entry Point ---------------------------------------
if __name__ == "__main__":
    start_time = time.time()

    # reading and processing input
    node_gdf, link_gdf, transit_modes_df = load_input_data()
    node_gdf = determine_centroid_nodes(node_gdf)
    node_gdf, link_gdf = renumber_nodes_for_emme(node_gdf, link_gdf)

    # writing emme transaction files
    mode_transaction_df = create_and_write_mode_transaction_file()
    veh_transaction_df = create_and_write_vehicle_transaction_file()
    node_gdf, link_gdf = write_links_and_nodes_tranaction_file(node_gdf, link_gdf, mode_transaction_df)
    write_extra_links_and_nodes_attribute_files(node_gdf, link_gdf)
    transit_line_df, stop_df = write_transit_line_transaction_file(node_gdf, transit_modes_df)
    write_extra_transit_link_attributes_file(transit_line_df)

    run_time = round(time.time() - start_time, 2)
    print("Run Time: ", run_time, "secs = ", run_time/60, " mins")
