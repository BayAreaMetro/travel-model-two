
COMP countyNodesOffset = 100000             ; each county is reserved a sequential block of node numbers for MAZs and TAZs only
COMP mazNodesOffset = 10000                 ; MAZs begin at this offset within each county's block of node numbers
COMP tanaNodesOffset = 3000000              ; TANA node numbers begin here

;add new ones
RUN PGM=NETWORK

  PAR  NODES=10000000

  NETI = tana_sp_with_maz_taz_tap_centroids_connectors_routes_2.net ;taz connectors already dropped
  LINKI[2] = connectorsTAZFinal.txt VAR=TEMP_A,TEMP_B,FEET,A,B ;switch sequential A and B for county A and B
  NETO = tana_sp_with_maz_taz_tap_centroids_connectors_routes_final.net
  
  PHASE=LINKMERGE
	; Set the connector type field on the and make the connectors assignable.
	IF ((A < @tanaNodesOffset@ & (A % @countyNodesOffset@ < @mazNodesOffset@)) | (B < @tanaNodesOffset@ & (B % @countyNodesOffset@ < @mazNodesOffset@)))
      CNTYPE = 'TAZ'
	  ASSIGNABLE = 1
	ENDIF
  ENDPHASE
ENDRUN

;drop computer generated Alameda county connectors
RUN PGM=NETWORK
  NETI = tana_sp_with_maz_taz_tap_centroids_connectors_routes_final.net
  NETO = tana_sp_with_maz_taz_tap_centroids_connectors_routes_final2.net

  PHASE=LINKMERGE
    If (CNTYPE = 'TAZ' & A < 10000 | B < 10000) ;Alameda County
      DELETE
    ELSE
      ;Keep record
    ENDIF
  ENDPHASE 
ENDRUN

;add Rupinder's Alameda county connectors
RUN PGM=NETWORK

  PAR  NODES=10000000

  NETI = tana_sp_with_maz_taz_tap_centroids_connectors_routes_final2.net
  LINKI[2] = AlamedaConnectors.txt VAR=A,B,FEET
  NETO =tana_sp_with_maz_taz_tap_centroids_connectors_routes_final3.net
  
  PHASE=LINKMERGE
	; Set the connector type field on the and make the connectors assignable.
	IF ((A < @tanaNodesOffset@ & (A % @countyNodesOffset@ < @mazNodesOffset@)) | (B < @tanaNodesOffset@ & (B % @countyNodesOffset@ < @mazNodesOffset@)))
      CNTYPE = 'TAZ'
	  ASSIGNABLE = 1
	ENDIF
  ENDPHASE
ENDRUN

;export final connectors
RUN PGM=NETWORK
  NETI = tana_sp_with_maz_taz_tap_centroids_connectors_routes_final3.net

  PAR  NODES=10000000
  
  PHASE=LINKMERGE
    IF (CNTYPE = 'TAZ')
      print form=8.0, file=finalConnectorsOldNumbers.txt, list=A,B,FEET
    ENDIF
    
  ENDPHASE 
ENDRUN





