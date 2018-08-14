; Determines all of the MAZs within a specified max distance (3 miles) using
; the shortest path program. Makes use of PRINTMODE = SUMMARY option so that
; only the final path is written (origin, destination, cumulative cost) for
; each MAZ.

RUN PGM = CUBE Parameters ='/Command /CloseWhenDone /Minimize /NoSplash'
  FUNCTION = BUILDPATH
    neti="tana_sp_with_maz_taz_centroids_connectors.net"
    pathprinto="mazShortestPaths.txt"
    CostSpec="FEET" ;impedance
    fileformat=txt
    MaxPathCost = 15840   ; 3 mile max distance
    PRINTMODE=SUMMARY

    ; Set the origin and destination to the set of MAZs.
    Origin="(N%100000 > 10000) & (N<3000000)"
    Destination="(N%100000 > 10000) & (N<3000000)"
    CLOSE
  ENDFUNCTION
ENDRUN