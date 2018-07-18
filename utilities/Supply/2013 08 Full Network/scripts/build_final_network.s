; alter network for bicycle/street network intersections

RUN PGM=NETWORK
    ZONES=1
    NODEI[1] = "postprocess_node.csv" VAR=N,X,Y,COUNTY,MODE,TYPE,ID
    LINKI[1] = "postprocess_link.csv" VAR=A,B,F_JNCTID,T_JNCTID,FRC,NAME(C),FREEWAY,TOLLRD(C),ONEWAY(C),KPH,MINUTES,CARRIAGE(C),LANES,RAMP,SPEEDCAT,FEET,ASSIGNABLE,CNTYPE(C),TRANSIT,USECLASS,TOLLBOOTH,FT,FFS,NUMLANES,HIGHWAYT(C),B_CLASS,REPRIORITIZE,GRADE_CAT,PED_FLAG(C),BIKEPEDOK,REV
    NETO = "mtc_final_network.net"
ENDRUN

RUN PGM=NETWORK
    NETI = "mtc_final_network.net"
    NETO = "mtc_final_network_temp.net"
    
    PHASE=LINKMERGE
        IF ((NAME = 'Oakland - San Francisco') | (NAME = 'San Francisco - Alameda') | (NAME = 'San Francisco - Alcatraz') | (NAME = 'San Francisco - Angel Is') | (NAME = 'San Francisco - Sausalito') | (NAME = 'San Francisco - Tiburon') | (NAME = 'San Francisco - Vallejo') | (NAME = 'Tiburon - Angel'))
            DELETE
        ELSE
            ;Keep record
        ENDIF
    ENDPHASE
ENDRUN

*"COPY mtc_final_network_temp.net mtc_final_network.net /Y"
*"DEL /Q /F mtc_final_network_temp.net"

RUN PGM = PUBLIC TRANSPORT
    FILEO NETO = "mtc_final_network.net"
    FILEI LINEI[1] = "transitLines.lin"
    FILEI NETI = "mtc_final_network.net"
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
; network -> shapefile

RUN PGM = NETWORK
    NETI = "mtc_final_network.net"
    FILEO LINKO = "mtc_final_network_links.shp" FORMAT=SHP
    FILEO NODEO = "mtc_final_network_nodes.shp" FORMAT=SHP
ENDRUN

;have to create a prj file because Cube doesn't
*"COPY postprocess_temp_link.prj mtc_final_network_links.prj /Y"
*"COPY postprocess_temp_link.prj mtc_final_network_nodes.prj /Y"

