;osm network -> shapefile
; this is needed to to the final step of building the ped network (intersecting with highway network)

RUN PGM = NETWORK
    NETI = "tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm.net"
    FILEO LINKO = "tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm.shp" FORMAT=SHP
ENDRUN

;have to create a prj file because Cube doesn't
*"COPY tana_mtc_nodes.prj tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm.prj /Y"
