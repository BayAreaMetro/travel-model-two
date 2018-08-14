USAGE = r"""
    
    Usage: python truck_taz_data.py

    This script aggregates the maz data to taz level, aggregating and retaining variables needed
    for the commercial truck model. The (column) aggregation is as follows:

    +---------------------------------+--------------------------------+
    | maz data file columns           | truck taz data file columns    |
    +---------------------------------+--------------------------------+
    | ag                              | AGREMPN                        |
    |                                 |                                |
    | ret_loc                         | RETEMPN                        |
    | ret_reg                         |                                |
    |                                 |                                |
    | fire                            | FPSEMPN                        |
    | info                            |                                |
    | lease                           |                                |
    | prof                            |                                |
    | serv_bus                        |                                |
    |                                 |                                |
    | art_rec                         | HEREMPN                        |
    | eat                             |                                |
    | ed_high                         |                                |
    | ed_k12                          |                                |
    | ed_oth                          |                                |
    | health                          |                                |
    | hotel                           |                                |
    | serv_pers                       |                                |
    | serv_soc                        |                                |
    |                                 |                                |
    | logis                           | MWTEMPN                        |
    | man_bio                         |                                |
    | man_hvy                         |                                |
    | man_lgt                         |                                |
    | man_tech                        |                                |
    | natres                          |                                |
    | transp                          |                                |
    | util                            |                                |
    |                                 |                                |
    | constr                          | OTHEMPN                        |
    | gov                             |                                |
    |                                 |                                |
    | emp_total                       | TOTEMP                         |
    |                                 |                                |
    | HH                              | TOTHH                          |
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
  ('AGREMPN',   ['ag'                      ]),
  ('RETEMPN',   ['ret_loc'                 ,
                 'ret_reg'                 ]),
  ('FPSEMPN',   ['fire'                    ,
                 'info'                    ,
                 'lease'                   ,
                 'prof'                    ,
                 'serv_bus'                ]),
  ('HEREMPN',   ['art_rec'                 ,
                 'eat'                     ,
                 'ed_high'                 ,
                 'ed_k12'                  ,
                 'ed_oth'                  ,
                 'health'                  ,
                 'hotel'                   ,
                 'serv_pers'               ,
                 'serv_soc'                ]),
  ('MWTEMPN',   ['logis'                   ,
                 'man_bio'                 ,
                 'man_hvy'                 ,
                 'man_lgt'                 ,
                 'man_tech'                ,
                 'natres'                  ,
                 'transp'                  ,
                 'util'                    ]),
  ('OTHEMPN',   ['constr'                  ,
                 'gov'                     ]),
  ('TOTEMP',    ['emp_total'               ]),
  ('TOTHH',     ['HH'                      ]),
  ])

ALLOCATION_COLUMNS = ['AGREMPN','RETEMPN','FPSEMPN','HEREMPN','MWTEMPN','OTHEMPN']

if __name__ == '__main__':
  maz_data_file = os.path.join("landuse",  "maz_data.csv")
  taz_data_file = os.path.join("nonres",   "truck_taz_data.csv")

  maz_data = pandas.read_csv(maz_data_file)
  taz_data = maz_data.groupby(['TAZ']).sum()

  # combine categories
  for newcol in CATEGORY_MAP.keys():
    taz_data[newcol] = 0
    for origcat in CATEGORY_MAP[newcol]:
      taz_data[newcol] += taz_data[origcat]


  taz_data = taz_data.loc[:,ALLOCATION_COLUMNS+['TOTEMP','TOTHH']]
  taz_data.reset_index(inplace=True)
  taz_data.to_csv(taz_data_file, index=False)