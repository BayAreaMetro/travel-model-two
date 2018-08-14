;osm network -> shapefile
; this is needed to to the final step of building the bike network (intersecting with highway network)

;add in bridge hov bypass links
RUN PGM=NETWORK 
  PAR  NODES=10000000
  NETI = "D:\Projects\MTC\networks\MAZs\TAZUpdate\mtc_with_new_taz.net"
  LINKI[2] = bridge_hov_bypass.csv VAR=A,B,F_JNCTID,T_JNCTID,FRC,NAME(C),FREEWAY,TOLLRD(C),ONEWAY(C),KPH,MINUTES,CARRIAGE(C),LANES,RAMP,SPEEDCAT,FEET,ASSIGNABLE,CNTYPE(C),TRANSIT,USECLASS,TOLLBOOTH,FT,FFS,NUMLANES,HIGHWAYT(C),B_CLASS,REPRIORITIZE,GRADE_CAT,PED_FLAG(C)
  NETO = mtc_pre_final_network.net
ENDRUN

;add bike/ped ok identifiers for bridges
RUN PGM=NETWORK 
  PAR  NODES=10000000
  NETI = mtc_pre_final_network.net
  LINKI[2] = bikepedok.csv VAR=A,B,BIKEPEDOK
  NETO = mtc_pre_final_network2.net
ENDRUN

*copy mtc_pre_final_network2.net  mtc_pre_final_network.net  
*del mtc_pre_final_network2.net 

;export network to shapefiles  
RUN PGM = NETWORK
;    NETI = "D:\Projects\MTC\networks\transit\tana_sp_with_maz_taz_tap_centroids_connectors_osm_bike_routes.net"
    NETI= mtc_pre_final_network.net
    FILEO LINKO = "postprocess_temp_link.shp" FORMAT=SHP
    FILEO NODEO = "postprocess_temp_node.shp" FORMAT=SHP
ENDRUN

;have to create a prj file because Cube doesn't
*"COPY D:\Projects\MTC\networks\osm\tana_mtc_nodes.prj postprocess_temp_link.prj /Y"
*"COPY D:\Projects\MTC\networks\osm\tana_mtc_nodes.prj postprocess_temp_node.prj /Y"
