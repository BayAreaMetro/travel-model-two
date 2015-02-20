"""
  Usage: python codeLinkAreaType.py base_dir

  Calculates MAZ Area Type using buffered population & employment density measure.
  That is, for every MAZ node within 1/2 mile of the the current MAZ node,
  population, employment and acres are summed.  The MAZ is then assigned an area type
  based on a stratifcation of the average weighted population + employment density:
  popemp_density = (population + 2.5xemployment)/acres.

  Area type is based on the following bands of popemp_density:
    popemp_density >= 300: 0 # regional core 
    popemp_density <  300: 1 # CBD
    popemp_density <  100: 2 # urban business
    popemp_density <   55: 3 # urban
    popemp_density <   30: 4 # suburban
    popemp_density <    6: 5 # rural

  Assigns link area type as min(area type of MAZ closest to A node, area type of MAZ closest to B node)

  Input:

     base_dir argument: the directory in which the model runs

     base_dir\hwy\mtc_final_network_with_tolls_nodes.csv: the network nodes

     base_dir\hwy\mtc_final_network_with_tolls_links.csv: the network links

     base_dir\landuse\maz_data.csv: the Micro-Zonal Data

  Output:
     base_dir\hwy\link_area_type.csv: mapping of link to area type.  Columns are A, B, Area Type

"""


import datetime, math, os, csv, sys
import pandas
import rtree

if __name__ == '__main__':
  base_dir        = sys.argv[1]
  MAZ_DATA_FILE   = os.path.join(base_dir,'landuse','maz_data.csv')
  NODE_CSV_FILE   = os.path.join(base_dir,'hwy',    'mtc_final_network_with_tolls_nodes.csv')
  LINK_CSV_FILE   = os.path.join(base_dir,'hwy',    'mtc_final_network_with_tolls_links.csv')
  AREA_TYPE_FILE  = os.path.join(base_dir,'hwy',    'link_area_type.csv')
  BUFF_DIST       = 5280 * 0.5

  print "%s Reading MAZ data" % datetime.datetime.now().strftime("%c")
  maz_df = pandas.DataFrame.from_csv(MAZ_DATA_FILE)
  maz_df.reset_index(inplace=True)

  print "%s Reading nodes" % datetime.datetime.now().strftime("%c")
  node_df = pandas.read_table(NODE_CSV_FILE, sep=',', names=['N','X','Y'])

  # join to maz_df for maz_df coords
  maz_df = pandas.merge(left=maz_df, right=node_df, how='left',
                         left_on='MAZ_ORIGINAL', right_on='N')
  maz_spatial_index = rtree.index.Index()
  for index, row in maz_df.iterrows():
    maz_spatial_index.insert( int(row['MAZ']), (row['X'], row['Y'], row['X'], row['Y']) )

  print "%s Calculate buffered MAZ measures" % datetime.datetime.now().strftime("%c")
  # Note: pandas.DataFrame.apply is too slow here, go back to dictionary form
  maz_df.set_index('MAZ', inplace=True)
  maz_dict      = maz_df.to_dict()
  popemp_den    = {}
  for maz in maz_dict['X'].keys():
    total_pop   = 0
    total_emp   = 0
    total_acres = 0
    for near_maz in maz_spatial_index.intersection((maz_dict['X'][maz]-BUFF_DIST, 
                                                    maz_dict['Y'][maz]-BUFF_DIST,
                                                    maz_dict['X'][maz]+BUFF_DIST, 
                                                    maz_dict['Y'][maz]+BUFF_DIST)):
      total_pop   += maz_dict['POP'][near_maz] 
      total_emp   += maz_dict['emp_total'][near_maz] 
      total_acres += maz_dict['ACRES'][near_maz]
    if total_acres>0:
      popemp_den[maz] = (1.0 * total_pop + 2.5 * total_emp) / total_acres
    else:
      popemp_den[maz] = 0
  maz_dict['popemp_density'] = popemp_den
  maz_df = pandas.DataFrame.from_dict(maz_dict)

  maz_df.loc[:,                           'area_type'] = 0 # regional core
  maz_df.loc[maz_df.popemp_density < 300, 'area_type'] = 1 # CBD
  maz_df.loc[maz_df.popemp_density < 100, 'area_type'] = 2 # urban business
  maz_df.loc[maz_df.popemp_density <  55, 'area_type'] = 3 # urban
  maz_df.loc[maz_df.popemp_density <  30, 'area_type'] = 4 # suburban
  maz_df.loc[maz_df.popemp_density <   6, 'area_type'] = 5 # rural
  maz_df.loc[:,                           'area_type'] = maz_df.area_type.astype(int)
  # refresh
  maz_dict = maz_df.to_dict()

  # debug
  # maz_df.loc[:,['MAZ','popemp_density','area_type']].to_csv('maz_new.csv',index=False)

  print "%s Find nearest MAZ for each link, take min area type of A or B node" % datetime.datetime.now().strftime("%c")

  link_df = pandas.read_table(LINK_CSV_FILE, sep=',', names=['A','B','CNTYPE'])
  link_df = pandas.merge(left=link_df, right=node_df, how='left', left_on='A', right_on='N')
  link_df.rename(columns={'X':'AX', 'Y':'AY'}, inplace=True)
  link_df = pandas.merge(left=link_df, right=node_df, how='left', left_on='B', right_on='N')
  link_df.rename(columns={'X':'BX', 'Y':'BY'}, inplace=True)
  link_df.drop(['N_x','N_y'], axis=1, inplace=True)  

  # Note: pandas.DataFrame.apply is too slow here, go back to dictionary form
  link_dict = link_df.to_dict(orient='list')  # preserve index ordering
  area_type = []
  for link_idx in range(len(link_dict['AX'])):
    if link_dict['CNTYPE'][link_idx] in ["TANA","USE","TAZ","EXT"]:
      aMaz = list(maz_spatial_index.nearest((link_dict['AX'][link_idx], link_dict['AY'][link_idx], 
                                             link_dict['AX'][link_idx], link_dict['AY'][link_idx]), 1))[0]
      bMaz = list(maz_spatial_index.nearest((link_dict['BX'][link_idx], link_dict['BY'][link_idx], 
                                             link_dict['BX'][link_idx], link_dict['BY'][link_idx]), 1))[0]
      area_type.append( min( maz_dict['area_type'][aMaz], maz_dict['area_type'][bMaz] ) )
    else:
      area_type.append(-1)

  link_dict['AREATYPE'] = area_type
  link_df = pandas.DataFrame.from_dict(link_dict)

  print "%s Write link area type CSV file" % datetime.datetime.now().strftime("%c")
  link_df.loc[:,['A','B','AREATYPE']].to_csv(AREA_TYPE_FILE, index=False)
