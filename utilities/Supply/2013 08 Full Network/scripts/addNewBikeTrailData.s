; append new bicycle trail data to existing network

RUN PGM=NETWORK
  NETI = "tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split_bikesub.net"
  NODEI[2] = "missing_bike_trail_nodes.csv" VAR=N,X,Y,Type,ID
  LINKI[2] = "missing_bike_trail_links.csv" VAR=A,B,CNTYPE(C),B_CLASS,REPRIORITIZE,GRADE_CAT,PED_FLAG(C),FEET
  NETO = "tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split_bikesub2.net"
ENDRUN

RUN PGM = NETWORK
    NETI = "tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split_bikesub2.net"
    FILEO LINKO = "tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split_bikesub2.shp" FORMAT=SHP
ENDRUN

;have to create a prj file because Cube doesn't
*"COPY tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split.prj tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split_bikesub2.prj /Y"
