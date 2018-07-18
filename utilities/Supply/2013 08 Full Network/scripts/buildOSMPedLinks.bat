
rem # Download SF area OSM file - http://metro.teczno.com - sf-bay-area bzipped OSM file

"C:\Python26\P64\python.exe" osm_mtc.py

"C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" buildOSM.s /Start

rem # save Cube OSM to shapefile and re-project OSM from WGS84 to MTC SP and add SP X and Y coord fields to DBF

rem # export new MTC nodes and links to shapefile

"C:\Python26\ArcGIS10.0\python.exe" osm_ped.py

"C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" mergeOSM.s /Start

"C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" osmToShapefile.s /Start

"C:\Python26\ArcGIS10.0\python.exe" intersectPedWithStreets.py

"C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" mergeOSMSplitLinks.s /Start
