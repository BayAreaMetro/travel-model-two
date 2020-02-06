; Merge MTC MAZ and TAZ Centroids with TeleAtlas Network

RUN PGM=NETWORK
   neti = "..\..\shapefiles\tana_sp.net"
   nodei[2] = "..\..\shapefiles\maz_taz_centroids.dbf" RENAME=POINT_X-X, POINT_Y-Y
   neto = "..\..\shapefiles\tana_sp_with_maz_taz_centroids.net"
   linko = "..\..\shapefiles\tana_sp_with_maz_taz_links.dbf" INCLUDE = A, B, FRC, FT, FREEWAY, ASSIGNABLE
   nodeo = "..\..\shapefiles\tana_sp_with_maz_taz_nodes.dbf"
ENDRUN


