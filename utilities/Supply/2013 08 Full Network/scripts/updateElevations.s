; Updates node elevations 
; Ben Stabler, stabler@pbworld.com, 05/22/13
; "C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" updateElevations.s /Start
 
RUN PGM=NETWORK
  NETI = "tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_bike.net"
  NODEI[2] = "nodeElevations.csv" VAR=N,TEMP_X,TEMP_Y,TEMP_Z
  NETO = "temp.net" EXCLUDE=TEMP_X,TEMP_Y,TEMP_Z
  
  PHASE=NODEMERGE
    Z=TEMP_Z
  ENDPHASE
  
ENDRUN

;rename output file
*copy temp.net tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_bike.net

;remove temp network files
*del temp.net