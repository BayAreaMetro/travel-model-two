The files in this directory were used to develop micro-analysis zones (MAZs) and
travel analysis zones (TAZs) for Travel Model Two.

[Internal asana link](https://app.asana.com/0/inbox/15119358130896/626340099942965/653367336829779)

MAZs and TAZs are defined by the correspondence in blocks_mazs_tazs.csv so they are a union
of [2010 vintage Census 2010 Blocks](https://www.census.gov/cgi-bin/geo/shapefiles/index.php?year=2010&layergroup=Blocks)

The [R script](csv_to_dbf.R) converts the csv to dbf (and forces the GEOID10 to be text) and the
python script [maz_taz_checker.py](maz_taz_checker.py) does a number of checks on the MAZs and TAZs and fixes,
and creates the shapefiles.

Major changes from v2.1:
- v2.1.1 has a bunch of manual fixes
- maz_taz_checker.py fixes a bunch of problems (moving blocks to neighboring mazs,
  splitting tazs -- see the script for more detail)
- maz_taz_checker.bat is used to iterate, producing the v2.1.X files
- the final v2.1.X file is the v2.2 file

The resulting shapefile has the following fields for QA/QC in the resulting maz and taz files:
- *ALAND10*, *AWATER10* - the land and water area (summed from the census blocks, in square meters)
- *GEOID10* - the count of census blocks in the maz/taz
- *partcount* - the number of disjoint parts
- *PERIM_GEO* - the perimeter around the maz/taz, in meters
- *psq_overa* - the perimeter squared divided by the area; the bigger this is, the less round/square the maz/taz.