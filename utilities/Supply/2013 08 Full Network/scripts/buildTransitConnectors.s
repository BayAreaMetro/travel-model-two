; Build connectors for the TAP nodes in the input network. Set the connector type field (CNTYPE) to TAP,
; and make the connectors non-assignable.
; Read in network with TAP centroids and text file with (origin, destination, distance) for
; the connectors and merges them.
; Sets connector length to 1 foot so MAZ to TAP shortest path is just MAZ to stop (not also stop to TAP node)


COMP countyNodesOffset = 100000             ; each county is reserved a sequential block of node numbers for MAZs and TAZs only
COMP mazNodesOffset = 10000                 ; MAZs begin at this offset within each county's block of node numbers
COMP tapNodesOffset = 90000                 ; TAPs begin here
COMP tanaNodesOffset = 3000000              ; TANA node numbers begin here

RUN PGM=NETWORK
  NETI = "D:\Projects\MTC\frazier_testbed\outputs\tana_sp_with_maz_taz_tap_centroids.net"
  LINKI[3] = "D:\Projects\MTC\frazier_testbed\outputs\nodes_to_taps.txt" VAR=A,B,FEET,TRANSIT
  NETO = "D:\Projects\MTC\frazier_testbed\outputs\tana_sp_with_maz_taz_tap_centroids_connectors.net"
  
  PHASE=LINKMERGE
	; Set the connector type field on the and make the connectors non-assignable.
	IF ((A < @tanaNodesOffset@ & (A % @countyNodesOffset@ > @tapNodesOffset@)) | (B < @tanaNodesOffset@ & (B % @countyNodesOffset@ > @tapNodesOffset@)))
    FEET = 1 ;set connector length to 1 foot so MAZ to TAP shortest path is just MAZ to stop (not also stop to TAP node)
    CNTYPE = 'TAP'
	  ASSIGNABLE = 0
	ENDIF
  ENDPHASE
ENDRUN