
COMP countyNodesOffset = 100000             ; each county is reserved a sequential block of node numbers for MAZs and TAZs only
COMP mazNodesOffset = 10000                 ; MAZs begin at this offset within each county's block of node numbers
COMP tanaNodesOffset = 3000000              ; TANA node numbers begin here

;drop old connectors
RUN PGM=NETWORK
  NETI = tana_sp_with_maz_taz_tap_centroids_connectors_routes.net
  NETO = tana_sp_with_maz_taz_tap_centroids_connectors_routes_2.net

  PHASE=LINKMERGE
    If (CNTYPE = 'TAZ')
      DELETE
    ELSE
      ;Keep record
    ENDIF
  ENDPHASE 
ENDRUN

;add new ones
RUN PGM=NETWORK

  PAR  NODES=10000000

  NETI = tana_sp_with_maz_taz_tap_centroids_connectors_routes_2.net
  LINKI[2] = connectorsTAZ.txt VAR=A,B,FEET
  NETO = tana_sp_with_maz_taz_tap_centroids_connectors_routes_3.net
    
  PHASE=LINKMERGE
	; Set the connector type field on the and make the connectors assignable.
	IF ((A < @tanaNodesOffset@ & (A % @countyNodesOffset@ < @mazNodesOffset@)) | (B < @tanaNodesOffset@ & (B % @countyNodesOffset@ < @mazNodesOffset@)))
      CNTYPE = 'TAZ'
	  ASSIGNABLE = 1
	ENDIF
  ENDPHASE
ENDRUN
