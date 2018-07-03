
COMP countyNodesOffset = 100000             ; each county is reserved a sequential block of node numbers for MAZs and TAZs only
COMP mazNodesOffset = 10000                 ; MAZs begin at this offset within each county's block of node numbers
COMP tanaNodesOffset = 3000000              ; TANA node numbers begin here

;drop connectors
RUN PGM=NETWORK
  NETI = mtc_final_network.net
  NETO = mtc_final_network2.net

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

  NETI = mtc_final_network2.net
  LINKI[2] = finalConnectorsOldNumbers.txt VAR=A,B,FEET
  NETO = mtc_final_network3.net
  
  PHASE=LINKMERGE
	; Set the connector type field on the and make the connectors assignable.
	IF ((A < @tanaNodesOffset@ & (A % @countyNodesOffset@ < @mazNodesOffset@)) | (B < @tanaNodesOffset@ & (B % @countyNodesOffset@ < @mazNodesOffset@)))
      CNTYPE = 'TAZ'
	  ASSIGNABLE = 1
	ENDIF
  ENDPHASE
ENDRUN
