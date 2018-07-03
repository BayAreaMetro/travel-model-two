
;check taz usage
;Ben Stabler, stabler@pbworld.com, 12/20/12

;global parameters
numTAZs=4509
TANA_OFFSET = 1000000
COUNTY_OFFSET = 100000
MAZ_OFFSET = 10000

;create sequential taz numbers
RUN PGM=NETWORK
  NETI = tana_sp_with_maz_taz_tap_centroids_connectors_routes_3.net
  NETO = temp.net

  PHASE = NODEMERGE
    
    IF (N < @TANA_OFFSET@ && N % @COUNTY_OFFSET@ < @MAZ_OFFSET@)
      _i = _i + 1     
      TAZ_NODE = _i
      COUNTY_N = N
    ENDIF
    
  ENDPHASE
  
  PHASE = LINKMERGE
    IF (A < @TANA_OFFSET@ && A % @COUNTY_OFFSET@ < @MAZ_OFFSET@)
      A_TAZ_NODE = A.TAZ_NODE
      COUNTY_A = A
    ENDIF
    
    IF (B < @TANA_OFFSET@ && B % @COUNTY_OFFSET@ < @MAZ_OFFSET@)
      B_TAZ_NODE = B.TAZ_NODE
      COUNTY_B = B
    ENDIF
  
  ENDPHASE
  
ENDRUN
  
RUN PGM=NETWORK
  NETI = temp.net
  NETO = temp2.net

  PAR  NODES=10000000

  PHASE = INPUT FILEI=NI.1
    IF (N < @TANA_OFFSET@ && N % @COUNTY_OFFSET@ < @MAZ_OFFSET@)
      N = TAZ_NODE
    ENDIF
  ENDPHASE

  PHASE = INPUT FILEI=LI.1
    IF (A < @TANA_OFFSET@ && A % @COUNTY_OFFSET@ < @MAZ_OFFSET@)
      A = A_TAZ_NODE
    ENDIF
      
    IF (B < @TANA_OFFSET@ && B % @COUNTY_OFFSET@ < @MAZ_OFFSET@)
      B = B_TAZ_NODE
    ENDIF
  ENDPHASE
  
ENDRUN

RUN PGM=MATRIX
	MATO=mat1.mat,MO=1,NAME=Ones
	ZONES=@numTAZs@
	mw[1]=1
ENDRUN

RUN PGM=HIGHWAY

  NETI=temp2.net
  MATI[1]=mat1.mat
  NETO=temp3.net
  
  ZONES=@numTAZs@
  parameters maxiters=1
  
  PHASE=LINKREAD
    IF (li.ASSIGNABLE=0) ADDTOGROUP=1    
    DISTANCE=li.FEET
    SPEED=132000 ;25*5280
  ENDPHASE

  PHASE=ILOOP  
    pathload path=TIME, excludegroup=1, vol=mi.1.Ones
  ENDPHASE
  
ENDRUN

;delete un-used connectors
RUN PGM=NETWORK
    NETI = temp3.net
    NETO = temp4.net

    PHASE=LINKMERGE
        If (CNTYPE = 'TAZ' & V_1=0)
            DELETE
        ELSE
            ;Keep record
        ENDIF
    ENDPHASE
ENDRUN
