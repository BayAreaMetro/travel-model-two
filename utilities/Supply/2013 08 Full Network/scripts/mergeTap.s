; Merge MTC TAP centroids with existing network

RUN PGM=NETWORK
   neti = "D:\Projects\MTC\frazier_testbed\tana_sp_with_maz_taz_centroids_connectors.net"
   nodei[2] = "D:\Projects\MTC\frazier_testbed\outputs\taps.txt" VAR=X,Y,COUNTY,N,MODE
   neto = "D:\Projects\MTC\frazier_testbed\outputs\tana_sp_with_maz_taz_tap_centroids.net"
ENDRUN


