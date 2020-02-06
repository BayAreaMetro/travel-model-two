; Merge OSM ped links
; Ben Stabler, stabler@pbworld.com, 04/17/13
; "C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" mergeOSM.s /Start

;add new nodes
RUN PGM=NETWORK
  NETI = "tana_sp_with_maz_taz_tap_centroids_connectors_routes.net"
  NODEI[2] = "osm_nodes.txt" VAR=N,X,Y
  NETO = "temp.net"
ENDRUN

;add new links
RUN PGM=NETWORK
  NETI = "temp.net"
  LINKI[2] = "osm_links.txt" VAR=A,B,FEET,OSM,HighwayT(C)
  NETO = "tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm.net" EXCLUDE=OSM
  
  PHASE=LINKMERGE
    IF (OSM=1)
      CNTYPE = 'PED'
    ENDIF 
  ENDPHASE
  
ENDRUN

;remove temp network files
*del temp*.net