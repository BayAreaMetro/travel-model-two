https://app.asana.com/0/inbox/15119358130896/626340099942965/653367336829779

MAZs and TAZs are defined by the blocks_mazs_tazs.csv

I use the R script to convert to dbf (and force the GEOID10 to be text)
and then use the python script
https://github.com/BayAreaMetro/travel-model-two/blob/master/utilities/maz_taz_checker.py
to create the shapefiles.

Major changes from v2.1:
- v2.1.1 has a bunch of manual fixes
- maz_taz_checker.py fixes a bunch of problems (moving blocks to neighboring mazs,
  splitting tazs -- see the script for more detail)
- maz_taz_checker.bat is used to iterate, producing the v2.1.X files
- the final v2.1.X file will be v2.2

