; MAZ to MAZ bike impedances
; Ben Stabler, stabler@pbworld.com, 04/17/13
; Chris Frazier, frazierc@pbworld.com, 04/13
; "C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" shortestPathBike.s /Start

RUN PGM = CUBE Parameters ='/Command /CloseWhenDone /Minimize /NoSplash'
  FUNCTION = BUILDPATH
    neti="tana_sp_with_maz_taz_tap_centroids_connectors_routes_osm_bicycle.net"
    pathprinto="maz_bike_costs.csv"
    CostSpec="FEET" ;impedance
    fileformat=txt
    LinkSelection="(FT=0 | FT=3 | FT=4 | FT=7 | BIKEPEDOK=1) & (CNTYPE='TANA' | CNTYPE='MAZ')"
    MaxPathCost = 63360   ; 12 mile max distance
    PRINTMODE=SUMMARY

    ; Set the origin and destination to the set of MAZs.
    Origin="(N%100000 > 10000) & (N<3000000)"
    Destination="(N%100000 > 10000) & (N<3000000)"
    CLOSE
  ENDFUNCTION
ENDRUN