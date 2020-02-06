rem # create MTC area network shapefiles to load into Cube and re-project
CALL runCreateShapefiles.bat

rem # create Cube network files
CALL runBuildNetwork.bat

rem # merge in taz and maz centroids and re-number network nodes
CALL runMergeTazMaz.bat

rem # merge in transit network, bike, walk

rem # build taz and maz connectors using just the 1 merged file
CALL runBuildConnectors.bat
