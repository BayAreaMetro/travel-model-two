; MAZ to MAZ ped impedances
; Ben Stabler, stabler@pbworld.com, 04/17/13
; "C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" shortestPathPed.s /Start

;create temporary network with one-way links allowing walking in both directions
;write network link dbf
RUN PGM = NETWORK
    NETI="tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm.net"
    LINKO="tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm__links.dbf"
ENDRUN
;swap and and b links
RUN PGM=MATRIX
    FILEI RECI="tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm__links.dbf"
    FILEO RECO[1]="tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm__links_flipped.dbf", FIELDS=A,B,RECI.ALLFIELDS,EXCLUDERECI=A,B
    RO.A=RI.B
    RO.B=RI.A
    IF (RI.ONEWAY == 'TF')
        RO.ONEWAY = 'FT'
    ELSEIF (RI.ONEWAY == 'FT') 
        RO.ONEWAY = 'TF'
    ELSE
        CONTINUE
    ENDIF
    WRITE RECO=1
ENDRUN
;merge networks
RUN PGM=NETWORK
    NETI="tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm.net"
    LINKI[2]="tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm__links_flipped.dbf"
    NETO="tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_ped.net"
ENDRUN

*"IF EXIST tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm__links.dbf DEL /S /Q tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm__links.dbf"
*"IF EXIST tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm__links_flipped.dbf DEL /S /Q tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm__links_flipped.dbf"

RUN PGM = CUBE Parameters ='/Command /CloseWhenDone /Minimize /NoSplash'
  FUNCTION = BUILDPATH
    neti="tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_ped.net"
    pathprinto="maz_ped_costs.txt"
    CostSpec="FEET" ;impedance
    fileformat=txt
    LinkSelection="(FT=0 | FT=4 | FT=7 | BIKEPEDOK=1) & (CNTYPE='TANA' | CNTYPE='PED' | CNTYPE='MAZ')"
    MaxPathCost = 15840   ; 3 mile max distance
    PRINTMODE=SUMMARY

    ; Set the origin and destination to the set of MAZs.
    Origin="(N%100000 > 10000) & (N<3000000)"
    Destination="(N%100000 > 10000) & (N<3000000)"
    CLOSE
  ENDFUNCTION
ENDRUN

*"IF EXIST tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_ped.net DEL /S /Q tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_ped.net"
