@ECHO OFF
"C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" netToShapefileForBike.s /Start
"c:\Python26\ArcGIS10.0\python.exe" bicycle_network.py
"C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" addBikeData.s /Start
"c:\Python26\ArcGIS10.0\python.exe" add_bike_links.py
"C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" addNewBikeTrailData.s /Start
"c:\Python26\ArcGIS10.0\python.exe" intersect_non_street_with_streets.py
"C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" merge_split_bike_links.s /Start
"C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" addBikePedOk.s /Start
