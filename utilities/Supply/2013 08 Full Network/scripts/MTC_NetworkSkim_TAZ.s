
;check MTC TAZ network
;Ben Stabler, stabler@pbworld.com, 12/20/12
;Erin Wardell, wardell@pbworld.com, 12/20/12

;global parameters
numTAZs=4509
TANA_OFFSET = 3000000
COUNTY_OFFSET = 100000
MAZ_OFFSET = 10000

;create sequential taz numbers
RUN PGM=NETWORK
  NETI = "tana_sp_with_maz_taz_centroids_connectors.net" 
  NETO = "temp.net"

  PHASE = NODEMERGE
    
    IF (N < @TANA_OFFSET@ && N % @COUNTY_OFFSET@ < @MAZ_OFFSET@)
      _i = _i + 1     
      TAZ_NODE = _i
    ENDIF
    
  ENDPHASE
  
  PHASE = LINKMERGE
    IF (A < @TANA_OFFSET@ && A % @COUNTY_OFFSET@ < @MAZ_OFFSET@)
      A_TAZ_NODE = A.TAZ_NODE
    ENDIF
    
    IF (B < @TANA_OFFSET@ && B % @COUNTY_OFFSET@ < @MAZ_OFFSET@)
      B_TAZ_NODE = B.TAZ_NODE
    ENDIF
  
  ENDPHASE
  
ENDRUN
  
RUN PGM=NETWORK
  NETI = "temp.net" 
  NETO = "temp2.net"

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

;taz to taz straight line distance
RUN PGM=NETWORK
  nodei[1]="temp2.net"

	;put TAZ centroid number and coordinates into arrays for later
  array _tazn=@numTAZs@
  array _tazx=@numTAZs@
  array _tazy=@numTAZs@
  
	phase=input filei=ni.1
     IF (N <= @numTAZs@)
        _i=_i+1
	    	_tazn[_i]=N
		    _tazx[_i]=X
		    _tazy[_i]=Y
     ENDIF 
  endphase
  
  ;loop through tazs
  phase=nodemerge
    IF (N <= @numTAZs@)  
      LOOP _index=1,@numTAZs@
				     
        ;calculate distance
        _dist = sqrt((X-_tazx[_index])^2 +(Y-_tazy[_index])^2)
           			    	
        ;from, to, distance
        print file="taz_dist.csv", csv=T, list=N, _tazn[_index], _dist
            
      ENDLOOP
    ENDIF
    
  endphase
 
ENDRUN

; Create taz to taz network distance skim
RUN PGM=HIGHWAY

  NETI="temp2.net"
  MATO[1]=dist.skm,MO=1,NAME=DISTANCE

	ZONES=@numTAZs@

  PHASE=linkread
    IF (li.ASSIGNABLE=0) ADDTOGROUP=1
  ENDPHASE

  PHASE=ILOOP  
    ;choose path based on link FEET attribute and skim (trace) link FEET attribute
    path=li.FEET, excludegroup=1, mw[1]=pathtrace(li.FEET)
    
  ENDPHASE
  
ENDRUN

;create table version of distance skim
RUN PGM=MATRIX

  MATI[1]=dist.skm
  zones=@numTAZs@
  
  IF(I=1)
   PRINT LIST="I,J,DISTANCE" FILE="taz_skim_dist.csv"
  ENDIF
  
  JLOOP
    PRINT LIST=INT(I)(L), INT(J)(L), mi.1.1[J](L), CSV=T FILE="taz_skim_dist.csv" APPEND=T
  ENDJLOOP

ENDRUN

;delete temp files
*del temp.net
*del temp2.net

