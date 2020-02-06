"C:\Python26\ArcGIS10.0\python.exe" getTAZVertices.py
"C:\Python26\ArcGIS10.0\python.exe" buildConnectorsMAZ.py
"C:\Python26\ArcGIS10.0\python.exe" buildConnectorsTAZAll.py
"C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" buildConnectorsTAZ_Part1.s /Start
"C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" taz_usage.s /Start
"C:\Python26\ArcGIS10.0\python.exe" finalConnectors.py
"C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" buildConnectorsTAZ_Part2.s /Start

"C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" buildConnectors.s /Start

