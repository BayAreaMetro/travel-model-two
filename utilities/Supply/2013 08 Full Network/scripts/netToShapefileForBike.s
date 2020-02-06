;osm network -> shapefile
; this is needed to to the final step of building the bike network (intersecting with highway network)

RUN PGM = NETWORK
    NETI = "D:\Projects\MTC\networks\osm\tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split.net"
    FILEO LINKO = "tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split.shp" FORMAT=SHP
ENDRUN

;have to create a prj file because Cube doesn't
*"COPY D:\Projects\MTC\networks\osm\tana_mtc_nodes.prj tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split.prj /Y"
