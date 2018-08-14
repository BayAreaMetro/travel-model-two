; Build connectors for the MAZ nodes in the input network. Set the connector type field (CNTYPE) to either MAZ, TAZ, or TANA,
; and make the connectors assignable.
; Read in network with MAZ centroids and text file with (origin, destination, distance) for the connectors and merges them. 

COMP countyNodesOffset = 100000             ; each county is reserved a sequential block of node numbers for MAZs and TAZs only
COMP mazNodesOffset = 10000                 ; MAZs begin at this offset within each county's block of node numbers
COMP tanaNodesOffset = 3000000              ; TANA node numbers begin here

RUN PGM=NETWORK
  NETI = "C:/projects/mtc/tana_sp_with_maz_taz_centroids.net"
  LINKI[2] = "C:/projects/mtc/connectorsMAZ.txt" VAR=A,B,FEET
  NETO = "C:/projects/mtc/tana_sp_with_maz_taz_centroids_connectors.net"
    
  PHASE=LINKMERGE
	; Set the connector type field on the and make the connectors assignable.
	IF ((A < @tanaNodesOffset@ & (A % @countyNodesOffset@ < @mazNodesOffset@)) | (B < @tanaNodesOffset@ & (B % @countyNodesOffset@ < @mazNodesOffset@)))
      CNTYPE = 'TAZ'
	  ASSIGNABLE = 1
	ELSEIF ((A < @tanaNodesOffset@ & (A % @countyNodesOffset@ > @mazNodesOffset@)) | (B < @tanaNodesOffset@ & (B % @countyNodesOffset@ > @mazNodesOffset@)))
      CNTYPE = 'MAZ'
	  ASSIGNABLE = 1
	ELSE
	  CNTYPE = 'TANA'
	ENDIF
  ENDPHASE
ENDRUN
