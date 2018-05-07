# MAZs and TAZs for Travel Model Two

The files in this directory were used to develop micro-analysis zones (MAZs) and
travel analysis zones (TAZs) for Travel Model Two (TM2).

See [web map](https://arcg.is/aLz8f) with Version 2.2 and 1.0 of TM2 MAZs and TAZs, along with TrCensus 2010 places, tracts, block groups.

## Axioms
* MAZs and TAZs are *defined* as a union of [2010 vintage Census 2010 Blocks](https://www.census.gov/cgi-bin/geo/shapefiles/index.php?year=2010&layergroup=Blocks).  The shapefiles are dissolved from this definition.
* There is one 2010 vintage Census 2010 Block Group (and therefore Tract and County) per MAZ
* There is one 2010 vintage Census 2010 Tract (and therefore County) per TAZ
* 2010 vintage Census 2010 Blocks with zero land area (ALAND10) are not assigned a MAZ or TAZ
* 2010 vintage Census 2010 Blocks with nonzero land area (ALAND10) are assigned a MAZ and TAZ

### Axiom Exceptions

There are a handful of exceptions to the above axioms.

* Blocks "06 075 980401 100[1,2,3]" (maz 16084, taz 287) are the Farallon Islands.  It's a standalone maz but the
  taz spans tracts because it's not worth it's own taz.
* Block "06 081 608002 2004" (maz 112279, taz 100178) spans a block group boundary but not doing so would split up
  and island with two blocks.
* Blocks "06 075 017902 10[05,80]" (maz 16495, taz 312) is a tiny sliver that's barely land so not worth
  making a new maz, so that maz includes a second tract (mostly water)
* Blocks "06 041 104300 10[17,18,19]" (maz 810745, taz 800095) spans a block group/tract boundary but the're a
  tiny bit on the water's edge and moving them would separate them from the rest of the maz/taz
* Blocks "06 041 122000 100[0,1,2]" (maz 813480, taz 800203) are a tract that is inside another tract so keeping
  as is so as not to create a donut hole maz
* Block "06 013 301000 3000" (maz 410304, taz 400507) is a block that Census 2010 claims has no land area ("Webb Tract")
  but appears to be a delta island so it's an exception to the zero-land/non-zero water blocks having a maz/taz

### Notes
* Block "06 075 017902 1009" (maz 10186, taz 592) is the little piece of Alameda island that the Census 2010
  calls San Francisco.  Left in SF as its own maz.

The [R script](csv_to_dbf.R) converts the csv to dbf (and forces the GEOID10 to be text) and the
python script [maz_taz_checker.py](maz_taz_checker.py) does a number of checks on the MAZs and TAZs and fixes,
and creates the shapefiles and geoJSON files.

## GeoJSON and Shapefiles

The resulting shapefiles (produced by the correspondence csv via the python script) have the following fields:

* *maz*, *taz* - The MAZ and TAZ ids.  These are [numeric and grouped by county](http://bayareametro.github.io/travel-model-two/input/#county-node-numbering-system).  Note *maz* isn't specified in the TAZ shapefile.
* *ALAND10*, *AWATER10* - the land and water area (summed from the census 2010 blocks, in square meters)
* *blockcount* - the count of census 2010 blocks in the MAZ/MAZ
* *partcount* - the number of disjoint parts
* *PERIM_GEO* - the perimeter around the MAZ/TAZ, in meters
* *psq_overa* - the perimeter squared divided by the area; the bigger this is, the less round/square the MAZ/TAZ
* *mazcount* - for TAZs only, this is the count of MAZs in the TAZ

## Revision History

### Version 2.2

* Manual fixes incorporated into [blocks_mazs_tazs_v2.1.1.csv](blocks_mazs_tazs_v2.1.1.csv)
* Updated [maz_taz_checker.py](maz_taz_checker.py) to fix problems (moving blocks to neighboring mazs,
  splitting tazs -- see the script for more detail)
* [maz_taz_checker.bat](maz_taz_checker.bat) is used to iterate, producing the v2.1.X files
* The final v2.1.X file is the v2.2 file
* [(Internal) Asana Task](https://app.asana.com/0/610230255351992/626340099942965/f)
* Work performed in M:\Data\GIS layers\TM2_maz_taz_v2.2

### Version 2.1
* Started development of [maz_taz_checker.py](maz_taz_checker.py) to automatically generate shapefiles
* Using 2010 vintage of Census 2010 blocks because the 2017 vintage had problems
* All blocks with nonzero land area (ALAND10) are assigned to a maz/taz
* All blocks with zero land area (ALAND10) are not assigned a maz/taz
* Work performed in M:\Data\GIS layers\TM2_maz_taz_v2.1

### Version 2.0
* Required to fix some problems where some MAZs were mistakenly part of TAZs for which the other MAZs were far away
* We also decided not to break up Census 2010 blocks into pieces, so we defined MAZs (and TAZs) as a union of Census 2010 blocks (2017 vintage) and that
  TAZs should nest within counties
* [(Internal) Asana Task](https://app.asana.com/0/610230255351992/578257153057158/f)
* Work performed in M:\Data\GIS layers\TM2_maz_taz_v2.0

### Version 1.0
* [Map](http://www.arcgis.com/apps/OnePane/basicviewer/index.html?appid=4ca5bf25e2ed46ebb7c25796b29c33d1)
* [Revised Travel Analysis and Micro-Analysis Zone Boundaries](https://mtcdrive.box.com/travel-model-two-revised-space) - May 22, 2014
* [Initial Draft Travel Analysis and Micro-Analysis Zone Boundaries](https://mtcdrive.box.com/travel-model-two-first-space) - Jan 17, 2013

