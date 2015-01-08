"""
    truck_taz_data.py model_dir input_maz_file output_taz_file taz_count

    This script aggregates the maz data to taz level, aggregating and retaining variables needed
    for the commercial truck model. The (column) aggregation is as follows:

    +---------------------------------+--------------------------------+
    | maz data file columns           | truck taz data file columns    |
    +---------------------------------+--------------------------------+
    | emp_ag                          | AGREMPN                        |
    |                                 |                                |
    | emp_retail                      | RETEMPN                        |
    |                                 |                                |
    | emp_prof_bus_svcs               | FPSEMPN                        |
    | emp_prof_bus_svcs_bldg_maint    |                                |
    | emp_personal_svcs_office        |                                |
    |                                 |                                |
    | emp_pvt_ed_k12                  | HEREMPN                        |
    | emp_pvt_ed_post_k12_oth         |                                |
    | emp_health                      |                                |
    | emp_public_ed                   |                                |
    | emp_amusement                   |                                |
    | emp_personal_svcs_retail        |                                |
    | emp_hotel                       |                                |
    | emp_restaurant_bar              |                                |
    | emp_pvt_hh                      |                                |
    |                                 |                                |
    | emp_mfg_prod                    | MWTEMPN                        |
    | emp_mfg_office                  |                                |
    | emp_whsle_whs                   |                                |
    | emp_trans                       |                                |
    | emp_utilities_prod              |                                |
    | emp_utilities_office            |                                |
    |                                 |                                |
    | emp_const_non_bldg_prod         | OTHEMPN                        |
    | emp_const_non_bldg_office       |                                |
    | emp_const_bldg_prod             |                                |
    | emp_const_bldg_office           |                                |
    | emp_religious                   |                                |
    | emp_state_local_gov_ent         |                                |
    | emp_fed_non_mil                 |                                |
    | emp_fed_mil                     |                                |
    | emp_state_local_gov_blue        |                                |
    | emp_state_local_gov_white       |                                |
    |                                 |                                |
    | emp_total                       | TOTEMP                         |
    |                                 |                                |
    | HH                              | TOTHH                          |
    |                                 |                                |
    | emp_self                        | PE*                            |
    | emp_own_occ_dwell_mgmt          |                                |
    |                                 |                                |
    | emp_cap_accts                   | ***not used***                 |
    | emp_scrap_other                 |                                |
    | emp_fed_gov_accts               |                                |
    | emp_st_lcl_gov_accts            |                                |
    +---------------------------------+--------------------------------+

    The PE* class is reallocated to all other employment classes (proportional to their
    pre-reallocation counts), as these categories do not neatly fit into any single category.
    Additionally, the ***not used*** classes are ignored, as these represent dollar counts,
    not employment

    Inputs: maz_data.csv - the input maz data file

    Outputs: truck_taz_data.csv - the output truck taz data file

    version:  Travel Model Zed
    authors:  crf (2014 2 7)
"""

import sys,os,csv

base_dir = sys.argv[1]
maz_data_file = os.path.join(base_dir,sys.argv[2])
taz_data_file = os.path.join(base_dir,sys.argv[3])
taz_count = int(sys.argv[4])

#need these here for correct ordering
taz_columns = ['TAZ','AGREMPN','RETEMPN','FPSEMPN','HEREMPN','MWTEMPN','OTHEMPN','TOTEMP','TOTHH']
allocation_columns = ['AGREMPN','RETEMPN','FPSEMPN','HEREMPN','MWTEMPN','OTHEMPN']
#set emplolyment category mappings
data_map = {}
data_map['AGREMPN'] = ['emp_ag']
data_map['RETEMPN'] =        ['emp_retail']
data_map['FPSEMPN'] =        ['emp_prof_bus_svcs',
                              'emp_prof_bus_svcs_bldg_maint',
                              'emp_personal_svcs_office']
data_map['HEREMPN'] =        ['emp_pvt_ed_k12',
                              'emp_pvt_ed_post_k12_oth',
                              'emp_health',
                              'emp_public_ed',
                              'emp_amusement',
                              'emp_personal_svcs_retail',
                              'emp_hotel',
                              'emp_restaurant_bar',
                              'emp_pvt_hh']
data_map['MWTEMPN'] =        ['emp_mfg_prod',
                              'emp_mfg_office',
                              'emp_whsle_whs',
                              'emp_trans',
                              'emp_utilities_prod',
                              'emp_utilities_office']
data_map['OTHEMPN'] =        ['emp_const_non_bldg_prod',
                              'emp_const_non_bldg_office',
                              'emp_const_bldg_prod',
                              'emp_const_bldg_office',
                              'emp_religious',
                              'emp_state_local_gov_ent',
                              'emp_fed_non_mil',
                              'emp_fed_mil',
                              'emp_state_local_gov_blue',
                              'emp_state_local_gov_white']
data_map['TOTEMP'] =         ['emp_total']
data_map['TOTHH'] =          ['HH']
data_map['***not used***'] = ['emp_scrap_other',
                              'emp_cap_accts',
                              'emp_fed_gov_accts',
                              'emp_st_lcl_gov_accts']
data_map['PE'] =             ['emp_self',
                              'emp_own_occ_dwell_mgmt']

#read in maz-level employment data, and aggregate it to taz-level
taz_data = {}
taz_data[0] = {} #for default
for column in data_map:
    taz_data[0][column] = 0.0
with open(maz_data_file) as f:
    for row in csv.DictReader(f,skipinitialspace=True):
        taz = int(row['TAZ'])
        if not taz in taz_data:
            taz_data[taz] = {}
            for column in data_map:
                taz_data[taz][column] = 0.0
        for column in data_map:
            for maz_column in data_map[column]:
                taz_data[taz][column] += float(row[maz_column])

#reallocate PE
default_fraction = 1 / float(len(allocation_columns))
for taz in taz_data:
    emps = taz_data[taz]
    emp_sum = 0.0
    max_column = None #max column gets remainder
    for column in allocation_columns:
        emp_sum += emps[column]
        if max_column is None:
            max_column = column
        elif emps[column] > emps[max_column]:
            max_column = column

    allocations_fractions = {}
    for column in allocation_columns:
        if emp_sum == 0:
            allocations_fractions[column] = default_fraction
        else:
            allocations_fractions[column] = emps[column] / emp_sum

    allocated_total = 0
    for column in allocation_columns:
        if column == max_column:
            continue
        allocation_emp = round(allocations_fractions[column] * emps['PE'])
        emps[column] += allocation_emp
        allocated_total += allocation_emp
    emps[max_column] += max(0,emps['PE'] - allocated_total)

#write out data, with emplyment-type aggregation
with open(taz_data_file,'wb') as f:
    f.write(','.join(taz_columns) + os.linesep)
    for taz in range(1,taz_count+1):
        if taz in taz_data:
            data = taz_data[taz]
        else:
            data = taz_data[0]
        line = [taz]
        for column in taz_columns:
            if column != 'TAZ':
                line.append(data[column])
        f.write(','.join(map(str,line)) + os.linesep)
