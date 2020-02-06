; alter network for bicycle/street network intersections

RUN PGM=NETWORK
    NETI = "tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_split_bikesub2.net"
    NODEI[2] = "new_nodes_bike.csv" VAR=N,X,Y
    LINKI[2] = "link_split_bike.csv" VAR=A,B,F_JNCTID,T_JNCTID,FRC,NAME(C),FREEWAY,TOLLRD(C),ONEWAY(C),KPH,MINUTES,CARRIAGE(C),LANES,RAMP,SPEEDCAT,FEET,ASSIGNABLE,CNTYPE(C),TRANSIT,USECLASS,TOLLBOOTH,FT,FFS,NUMLANES,HIGHWAYT(C),B_CLASS,REPRIORITIZE,GRADE_CAT,PED_FLAG(C)
    LINKI[3] = "link_delete_bike.csv" VAR=A,B,CNTYPE(C)
    NETO = "tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_bike.net"
    MERGE RECORD=TRUE LAST=CNTYPE
    PHASE=LINKMERGE
        If (CNTYPE = 'DELETE')
            DELETE
        ELSE
            ;Keep record
        ENDIF
    ENDPHASE
ENDRUN
