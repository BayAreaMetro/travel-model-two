; append bicycle data to existing network
; bike_links.csv has the a/b nodes of the links, and the bike data
; links not listed in the file are just given empty bike data

RUN PGM=NETWORK
  NETI = "D:\Projects\MTC\networks\osm\tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split.net"
  LINKI[2] = "bike_links.csv" VAR=A,B,B_CLASS,REPRIORITIZE,GRADE_CAT,PED_FLAG(C)
  LINKI[3] = "missing_links.csv" VAR=A,B,B_CLASS,REPRIORITIZE,GRADE_CAT,PED_FLAG(C)
  LINKI[4] = "bike_trail_links.csv" VAR=A,B,B_CLASS,REPRIORITIZE,GRADE_CAT,PED_FLAG(C)
  NETO = "tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split_bikesub.net"
ENDRUN

RUN PGM = NETWORK
    NETI = "tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split_bikesub.net"
    FILEO LINKO = "tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split_bikesub.shp" FORMAT=SHP
ENDRUN

;have to create a prj file because Cube doesn't
*"COPY tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split.prj tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split_bikesub.prj /Y"

