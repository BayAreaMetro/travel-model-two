## ACS Household Block Group to MAZ and TAZ2 Crosswalks

American Community Survey (ACS) data are available at block group and above geographies. However, TM2 geographies (MAZ/TAZ2) are 
built on clusters of blocks. The script in this folder creates a block-group-to-MAZ and block-group-to-TAZ2 crosswalks.
This README describes the process for creating a crosswalk to use with household-level variables, though in the future
other types of crosswalks may be developed. For the HH-level crosswalk files, 2010 decennial census household data at 
the block level are used to develop the share of households by block group. The block group shares are generated as a 
simple calculation of block HHs/block group HHs. That share can then be applied to any household-level distribution for 
TM2 MAZ/TAZ2 data development. 

The [script](https://github.com/BayAreaMetro/travel-model-two/blob/master/maz_taz/crosswalks/Create%20Census%202010%20MAZ%20and%20TAZ%20shares%20of%20blockgroups.R) also checks ACS year blockgroups against 2010 blockgroups to see if any of the ACS block groups have a non-zero household count 
where Census 2010 had zero households. Addressing this is important to ensure full apportionment of ACS data. In cases 
that ACS block groups are >0 while Census 2010 values were zero, a straight apportionment to blocks is done
by the number of blocks in that block group. For example, if the block group has 10 blocks, each block is 
apportioned a share of 0.1.

### Steps

* Data for 2010 total households is downloaded using the [Census API](https://api.census.gov/data/2010.html) with [R's TidyCensus Package](https://walker-data.com/tidycensus/articles/basic-usage.html)
* Sum block group total households and calculate block shares
* Bring in ACS five-year data with the [ACS API](https://www.census.gov/data/developers/data-sets/acs-5year.2017.html) for the relevant year and determine if block group totals are non-zero where they were zero in 2010.
  + If no block groups fit this criterion, make no changes to the block-level shares
  + For block group that do fit the above description, divide 1/number of blocks to get the respective block shares.
* Sum block shares for each block group/MAZ and block group/TAZ2 combination to produce final crosswalk files.
* Output crosswalks for [MAZ](https://github.com/BayAreaMetro/travel-model-two/blob/master/maz_taz/crosswalks/Census%202010%20hhs%20maz%20share%20of%20blockgroups.csv) and [TAZ2](https://github.com/BayAreaMetro/travel-model-two/blob/master/maz_taz/crosswalks/Census%202010%20hhs%20taz2%20share%20of%20blockgroups.csv).
* A log file for the appropriate ACS year is produced to document block groups fitting the above condtions (log not included in the GitHub repository)
