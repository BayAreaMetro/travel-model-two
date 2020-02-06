; Merge Use Links and Use Link Connectors
; Code Tollbooths, facility type, speeds, lanes
; Ben Stabler, stabler@pbworld.com, 03/07/13

;add new A nodes
RUN PGM=NETWORK
   neti = "tana_sp_with_maz_taz_tap_centroids_connectors_routes.net"
   ;NEWA,NEWB,OFFAX,OFFAY,OFFBX,OFFBY,USECLASS,FRC,NEWLANES,FEET,SPEEDCAT,KPH
   nodei[2] = "use_links_cube.csv" VAR=N,TEMP1,X,Y,TEMP2,TEMP3,TEMP4,TEMP5,TEMP6,TEMP7,TEMP8,TEMP9
   neto = "temp.net" EXCLUDE=TEMP1,TEMP2,TEMP3,TEMP4,TEMP5,TEMP6,TEMP7,TEMP8,TEMP9
ENDRUN

;add new B nodes
RUN PGM=NETWORK
   neti = "temp.net"
   ;NEWA,NEWB,OFFAX,OFFAY,OFFBX,OFFBY,USECLASS,FRC,NEWLANES,FEET,SPEEDCAT,KPH
   nodei[2] = "use_links_cube.csv" VAR=TEMP1,N,TEMP2,TEMP3,X,Y,TEMP4,TEMP5,TEMP6,TEMP7,TEMP8,TEMP9
   neto = "temp2.net" EXCLUDE=TEMP1,TEMP2,TEMP3,TEMP4,TEMP5,TEMP6,TEMP7,TEMP8,TEMP9
ENDRUN

;add new use links
RUN PGM=NETWORK
  NETI = "temp2.net"
  ;NEWA,NEWB,OFFAX,OFFAY,OFFBX,OFFBY,USECLASS,FRC,NEWLANES,FEET,SPEEDCAT,KPH ;renamed NEWLANES to LANES
  LINKI[2] = "use_links_cube.csv" VAR=A,B,TEMP1,TEMP2,TEMP3,TEMP4,USECLASS,FRC,LANES,FEET,SPEEDCAT,KPH
  NETO = "temp3.net" EXCLUDE=TEMP1,TEMP2,TEMP3,TEMP4
  
  PHASE=LINKMERGE
    IF (A >= 5000000 & B >= 5000000)
      CNTYPE = 'TANA'
      ASSIGNABLE = 1
    ENDIF 
  ENDPHASE
  
ENDRUN

;add new use link connectors
RUN PGM=NETWORK
  NETI = "temp3.net"
  ;CONNECTORA,CONNECTORB,CONNECTORA_REV,CONNECTORB_REV,USECLASS,FRC,NEWLANES,FEET,SPEEDCAT,KPH ;renamed NEWLANES to LANES
  LINKI[2] = "use_links_connectors_cube.csv" VAR=A,B,TEMP1,TEMP2,USECLASS,FRC,LANES,FEET,SPEEDCAT,KPH
  NETO = "temp4.net" EXCLUDE=TEMP1,TEMP2
  
  PHASE=LINKMERGE
    IF ((A >= 5000000 | B >= 5000000) & (A < 5000000 | B < 5000000))
      CNTYPE = 'USE'
      ASSIGNABLE = 1
    ENDIF 
  ENDPHASE
  
ENDRUN

;add new use link connectors reverse
RUN PGM=NETWORK
  NETI = "temp4.net"
  ;CONNECTORA,CONNECTORB,CONNECTORA_REV,CONNECTORB_REV,USECLASS,FRC,NEWLANES,FEET,SPEEDCAT,KPH ;renamed NEWLANES to LANES
  LINKI[2] = "use_links_connectors_cube.csv" VAR=TEMP1,TEMP2,A,B,USECLASS,FRC,LANES,FEET,SPEEDCAT,KPH
  NETO = "temp5.net" EXCLUDE=TEMP1,TEMP2
  
  PHASE=LINKMERGE
    IF ((A >= 5000000 | B >= 5000000) & (A < 5000000 | B < 5000000))
      CNTYPE = 'USE'
      ASSIGNABLE = 1
    ENDIF 
  ENDPHASE
  
ENDRUN

;remove lanes from gp links
RUN PGM=NETWORK
  NETI = "temp5.net"
  ;A,B,LANES
  LINKI[2] = "use_links_cube_gp.csv" VAR=A,B,NEWLANES
  NETO = "temp6.net" EXCLUDE=NEWLANES
  
  PHASE=LINKMERGE
    IF(NEWLANES>0)
      LANES = NEWLANES
    ENDIF
  ENDPHASE
  
ENDRUN

;add in model lanes 
RUN PGM=NETWORK
  NETI = "temp6.net"
  ;A,B,LANES
  LINKI[2] = "num_lanes.csv" VAR=A,B,NEWLANES
  NETO = "temp7.net" EXCLUDE=NEWLANES
  
  PHASE=LINKMERGE
    IF(NEWLANES>0)
      LANES = NEWLANES
    ENDIF
  ENDPHASE
  
ENDRUN

;tag toll booth links and remove not used attributes
RUN PGM=NETWORK
  NETI = "temp7.net"
  NETO = "temp8.net" EXCLUDE=FID_CA_NW,ID,FEATTYP,FT,F_JNCTTYP,T_JNCTTYP,PJ,
												METERS,NETCLASS,NETBCLASS,NET2CLASS,NAMELC,SOL,NAMETYP,
												CHARGE,SHIELDNUM,RTETYP,RTEDIR,RTEDIRVD,PROCSTAT,FOW,
												SLIPRD,BACKRD,RDCOND,STUBBLE,PRIVATERD,CONSTATUS,F_BP,
												T_BP,F_ELEV,T_ELEV,POSACCUR,ADAS,TRANS,DYNSPEED,NTHRUTRAF,
												ROUGHRD,PARTSTRUC,FID_ABAG_B,SHAPE_LENG,ONEWAY_REC
  PHASE=LINKMERGE
    IF (A = 3042897 & B = 3050038 )
      TOLLBOOTH=1
    ENDIF 
    IF (A = 3657327 & B = 3038784 )
      TOLLBOOTH=2
    ENDIF 
    IF (A = 3081419 & B = 4110624 )
      TOLLBOOTH=3
    ENDIF 
    IF (A = 3066674 & B = 3040885 )
      TOLLBOOTH=4
    ENDIF 
    IF (A = 3074082 & B = 3976545 )
      TOLLBOOTH=5
    ENDIF 
    IF (A = 3015082 & B = 3921250 )
      TOLLBOOTH=6
    ENDIF 
    IF (A = 3032066 & B = 3887868 )
      TOLLBOOTH=7
    ENDIF 
    IF (A = 3019551 & B = 4065913 )
      TOLLBOOTH=8
    ENDIF 
  ENDPHASE
  
ENDRUN

;code FT, FFS, and NUMLANES
RUN PGM=NETWORK
  NETI = "temp8.net"
  NETO = "temp9.net" 
  PHASE=LINKMERGE
  
    ;calculate TANA link attributes
    IF(CNTYPE='TANA')
    
      ;freeway-to-freeway
	    IF ((FRC=0 | FRC=1 | FRC=2) & RAMP=1)
	      FT=1
      ;freeway
	    ELSEIF ((FRC=0 | FRC=1 | FRC=2) & RAMP=0)
	      FT=2
	    ;ramp
	    ELSEIF (FRC>2 & RAMP=1)
	      FT=5
	    ENDIF 
	    ;expressway
	    IF (FRC=3 & RAMP=0)
	      FT=3
	    ENDIF 
	    ;major arterial
	    IF ((FRC=4 | FRC=5) & RAMP=0)
	      FT=7
	    ENDIF
	    ;collector
	    IF ((FRC=6 | FRC=7 | FRC=8) & RAMP=0)
	      FT=4
	    ENDIF 
	    	    
	    ;free flow speed
	    FFS = KPH * 0.625
      
      ;fill in NUMLANES attribute
      NUMLANES = LANES
      IF (NUMLANES=0)
        NUMLANES=1
      ENDIF 
	    
	  ENDIF
    
  ENDPHASE
ENDRUN

;rename output file
*copy temp9.net tana_sp_with_maz_taz_tap_centroids_connectors_routes_uselinks.net

;remove temp network files
*del temp*.net