;build the transit routes for MTC and put them into the network
;the non-transit leg mode is a placeholder and needs to be set

RUN PGM = PUBLIC TRANSPORT

    FILEO NETO = "tana_sp_with_maz_taz_tap_centroids_connectors_osm_bike_routes.net"
    
    FILEI LINEI[1] = "transitLines.lin"
    FILEI NETI = "..\bike\tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_bike.net"
    FILEI FACTORI[1] = "transitFactors.fac"
    
    PARAMETERS HDWAYPERIOD=5
    
    PHASE=DATAPREP
        LINKLOOP
            LW.DISTANCE = LI.FEET/5280
            PARAMETERS TRANTIME=(LW.DISTANCE*60/15)
        ENDLINKLOOP
        GENERATE,
            COST=LW.DISTANCE/3.0*60,
            MAXCOST[1]=120,
            NTLEGMODE=50
    ENDPHASE
ENDRUN
