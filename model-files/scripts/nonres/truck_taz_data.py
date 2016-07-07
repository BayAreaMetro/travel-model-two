USAGE = r"""
    
    Usage: python truck_taz_data.py

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

    Inputs:  landuse\maz_data.csv - the maz data file

    Outputs: nonres\truck_taz_data.csv - the truck taz data file with columns
             'TAZ','AGREMPN','RETEMPN','FPSEMPN','HEREMPN','MWTEMPN','OTHEMPN','TOTEMP','TOTHH'

    version:  Travel Model Zed
    authors:  crf (2014 2 7)
"""

import collections,sys,os,csv
import numpy, pandas

# employment category mappings
CATEGORY_MAP = collections.OrderedDict([
  ('AGREMPN',   ['emp_ag'                      ]),
  ('RETEMPN',   ['emp_retail'                  ]),
  ('FPSEMPN',   ['emp_prof_bus_svcs'           ,
                 'emp_prof_bus_svcs_bldg_maint',
                 'emp_personal_svcs_office'    ]),
  ('HEREMPN',   ['emp_pvt_ed_k12'              ,
                 'emp_pvt_ed_post_k12_oth'     ,
                 'emp_health'                  ,
                 'emp_public_ed'               ,
                 'emp_amusement'               ,
                 'emp_personal_svcs_retail'    ,
                 'emp_hotel'                   ,
                 'emp_restaurant_bar'          ,
                 'emp_pvt_hh'                  ]),
  ('MWTEMPN',   ['emp_mfg_prod'                ,
                 'emp_mfg_office'              ,
                 'emp_whsle_whs'               ,
                 'emp_trans'                   ,
                 'emp_utilities_prod'          ,
                 'emp_utilities_office'        ]),
  ('OTHEMPN',   ['emp_const_non_bldg_prod'     ,
                 'emp_const_non_bldg_office'   ,
                 'emp_const_bldg_prod'         ,
                 'emp_const_bldg_office'       ,
                 'emp_religious'               ,
                 'emp_state_local_gov_ent'     ,
                 'emp_fed_non_mil'             ,
                 'emp_fed_mil'                 ,
                 'emp_state_local_gov_blue'    ,
                 'emp_state_local_gov_white'   ]),
  ('TOTEMP',    ['emp_total'                   ]),
  ('TOTHH',     ['HH'                          ]),
  ('*not used*',['emp_scrap_other'             ,
                 'emp_cap_accts'               ,
                 'emp_fed_gov_accts'           ,
                 'emp_st_lcl_gov_accts'        ]),
  ('PE',        ['emp_self'                    ,
                 'emp_own_occ_dwell_mgmt'      ])
  ])

ALLOCATION_COLUMNS = ['AGREMPN','RETEMPN','FPSEMPN','HEREMPN','MWTEMPN','OTHEMPN']

if __name__ == '__main__':
  maz_data_file = os.path.join("landuse",  "maz_data.csv")
  taz_data_file = os.path.join("nonres",   "truck_taz_data.csv")

  maz_data = pandas.DataFrame.from_csv(maz_data_file)
  taz_data = maz_data.groupby(['TAZ']).sum()

  # combine categories
  for newcol in CATEGORY_MAP.keys():
    taz_data[newcol] = 0
    for origcat in CATEGORY_MAP[newcol]:
      taz_data[newcol] += taz_data[origcat]

  # Reallocate PE
  if taz_data.PE.sum() > 0:
    pe_alloc = taz_data.loc[:,ALLOCATION_COLUMNS]
    pe_alloc['totemp'] =  pe_alloc.sum(axis=1)
  
    # We'll proportion the PE amounts proportionally to existing
    pe_alloc.loc[pe_alloc.totemp >0,ALLOCATION_COLUMNS] = pe_alloc.loc[pe_alloc.totemp>0,ALLOCATION_COLUMNS].div(pe_alloc['totemp'], axis=0)
    # If no existing, just evenly
    pe_alloc.loc[pe_alloc.totemp==0,ALLOCATION_COLUMNS] = 1.0/len(ALLOCATION_COLUMNS)
  
    # Multiply by the PE we want and round it
    pe_new = numpy.round(pe_alloc.loc[:,ALLOCATION_COLUMNS].mul(taz_data.PE, axis=0))
  
    # Rounding will make us slightly off -- fix the largest column
    pe_new['pe_sum' ] = pe_new.sum(axis=1)  # this is what we got
    pe_new['pe_goal'] = taz_data.PE         # but this is what we want
    pe_new['max_col'] = pe_alloc.loc[:,ALLOCATION_COLUMNS].idxmax(axis=1)  # adjust this column to get what we want
    for taz in pe_new.index:
      pe_new.loc[taz, pe_new.loc[taz,'max_col']] += pe_new.loc[taz,'pe_goal'] - pe_new.loc[taz,'pe_sum']
  
    # add to our taz_data
    for newcol in ALLOCATION_COLUMNS:
      taz_data[newcol] = taz_data[newcol] + pe_new[newcol].astype(numpy.int64)

  taz_data = taz_data.loc[:,ALLOCATION_COLUMNS+['TOTEMP','TOTHH']]
  taz_data.reset_index(inplace=True)
  taz_data.to_csv(taz_data_file, index=False)