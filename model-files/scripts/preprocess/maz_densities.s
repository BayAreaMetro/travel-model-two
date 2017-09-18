;---------------------------------------------------------------------------
; 
; maz_densities.job
;
; This script creates the land-use density fields required by CT-RAMP.
;
; inputs
;
;
; outputs

;---------------------------------------------------------------------------

;COMP numMAZs = %MAZ_COUNT%

;create intersections node file with x and y coordinate
RUN PGM=NETWORK
	neti="hwy\mtc_final_network_base.net"
  
	array _noden = 10000000
	array _nodex = 10000000
	array _nodey = 10000000
  
	phase=nodemerge
		_noden[N] = 0
		_nodex[N] = X
		_nodey[N] = Y
	
		IF ((N < 900000) & (N % 100000 > 10000) & (N % 100000 < 90000))
			print CSV=T form=8.0, file="hwy\maz_nodes.csv",list=N, X, Y
		ENDIF
	endphase
  
	;count nodes
	phase=linkmerge
    
		;count non-freeway, non-connector nodes
		IF (FRC > 0 & CNTYPE='')
			_noden[A] = _noden[A] + 1
			_noden[B] = _noden[B] + 1
		ENDIF
	  
	endphase
	
	phase=summary
		loop _n2=1,10000000
			if(_noden[_n2] > 4) ;atleast 5 links to be an intersection
				;node, x, y
				print CSV=T form=8.0, file="hwy\intersection_nodes.csv",list=_n2, _nodex[_n2],  _nodey[_n2]
			endif
		endloop
	endphase
	
ENDRUN

