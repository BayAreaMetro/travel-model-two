; Determines all of the TAPs within a specified max distance using
; the shortest path program. Makes use of PRINTMODE = SUMMARY option so that
; only the final node is written (origin, destination, cumulative cost).

RUN PGM = CUBE Parameters ='/Command /CloseWhenDone /Minimize /NoSplash'
  FUNCTION = BUILDPATH
    neti="tana_sp_with_maz_taz_tap_centroids_connectors_routes.net"
    pathprinto="mazShortestPathsMAZ2TAP.txt"
    CostSpec="FEET" ;impedance
    fileformat=txt
    MaxPathCost = 7290   ; 1.5 mile max distance
    PRINTMODE=SUMMARY

    ; Set the origin to MAZs and destination to TAPs.
    Origin="(N%100000 > 10000) & (N%100000 < 90000) & (N<3000000)"
    Destination="(N%100000 > 90000) & (N<3000000)"
    CLOSE
  ENDFUNCTION
ENDRUN