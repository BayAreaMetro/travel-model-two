@ECHO OFF
REM Run this after street network with taz/maz connectors finished
::"C:\Python26\ArcGIS10.0\python.exe" runBuildTransit.py
::"C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" mergeTap.s /Start
::"C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" buildTransitConnectors.s /Start
REM Run this after bike network created
"C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" buildTransitNetwork.s /Start
