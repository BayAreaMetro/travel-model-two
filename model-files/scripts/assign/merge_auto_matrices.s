; ----------------------------------------------------------------------------------------------------------------
; merge_auto_matrices.s
;
; TP+ script to merge the trip matrix outputs from the CTRAMP model into TAZ (non-transit)
; The CTRAMP output matrices are individually segmented by mode, and this script combines
; all of the individual mode matrices into a single matrix file (each mode is kept separate, but they are
; all combined into a single file).
;
; Input:  Demand omxrices output by CTRAMP:
;            auto_@p@_SOV_GP_@p@.omx
;            auto_@p@_SOV_PAY_@p@.omx
;            auto_@p@_SR2_GP_@p@.omx
;            auto_@p@_SR2_HOV_@p@.omx
;            auto_@p@_SR2_PAY_@p@.omx
;            auto_@p@_SR3_GP_@p@.omx
;            auto_@p@_SR3_HOV_@p@.omx
;            auto_@p@_SR3_PAY_@p@.omx
;            nonmotor_@p@_BIKE_@p@.omx
;            nonmotor_@p@_WALK_@p@.omx
;            other_@p@_SCHLBUS_@p@.omx
;
;         where @p@ is one of the five time periods (EA,AM,MD,PM,EV)
;         where @set@ is one of the transit skim sets (1,2,3)
;
; Output: TAZ level demand matrices:
;            TAZ_Demand_@p@.mat
;
;         where @p@ is one of the five time periods (EA,AM,MD,PM,EV)
;
; version:  Travel Model Zed
; authors:  Ben Stabler (2013); crf (2014);
;           Joel Freedman (2018) - to handle Taxi, TNCs, TNC-access to transit. TODO:Handle CAVs
;                                  Note: TNCs added to S2 HOV mode if AV_SCENARIO=0, else added to DA mode
;
; ----------------------------------------------------------------------------------------------------------------

; create time period matrices
loop period = 1, 5

   ; a two letter token is used for each time period
   if (period = 1)
      p = 'EA'
   elseif (period = 2)
      p = 'AM'
   elseif (period = 3)
      p = 'MD'
   elseif (period = 4)
      p = 'PM'
   elseif (period = 5)
      p = 'EV'
   endif

   ;convert from open matrix to cube
   loop files = 1, 16

     if (files = 1)
		fmode = 'ctramp_output\auto_'
		fclass = '_SOV_GP_'
	 elseif (files = 2)
        fmode = 'ctramp_output\auto_'
		fclass = '_SOV_PAY_'
	 elseif (files = 3)
		fmode = 'ctramp_output\auto_'
		fclass = '_SR2_GP_'
	 elseif (files = 4)
		fmode = 'ctramp_output\auto_'
		fclass = '_SR2_HOV_'
	 elseif (files = 5)
		fmode = 'ctramp_output\auto_'
		fclass = '_SR2_PAY_'
	 elseif (files = 6)
		fmode = 'ctramp_output\auto_'
		fclass = '_SR3_GP_'
	 elseif (files = 7)
		fmode = 'ctramp_output\auto_'
		fclass = '_SR3_HOV_'
	 elseif (files = 8)
		fmode = 'ctramp_output\auto_'
		fclass = '_SR3_PAY_'
	 elseif (files = 9)
		fmode = 'ctramp_output\Nonmotor_'
		fclass = '_BIKE_'
	 elseif (files = 10)
		fmode = 'ctramp_output\Nonmotor_'
		fclass = '_WALK_'
	 elseif (files = 11)
		fmode = 'ctramp_output\other_'
		fclass = '_SCHLBUS_'
	 elseif (files = 12)
		fmode = 'ctramp_output\other_'
		fclass = '_TAXI_'
	 elseif (files = 13)
		fmode = 'ctramp_output\other_'
		fclass = '_TNC_'
	 elseif (files = 14)
		fmode = 'ctramp_output\auto_'
		fclass = '_MAZ_AUTO_1_'
	 elseif (files = 15)
		fmode = 'ctramp_output\auto_'
		fclass = '_MAZ_AUTO_2_'
	 elseif (files = 16)
		fmode = 'ctramp_output\auto_'
		fclass = '_MAZ_AUTO_3_'
	 endif

     ;write Cube script since cant pass tokens to RUN PGM = CUBE
     RUN PGM=MATRIX
      ZONES=1
      FILEO PRINTO[1] = convert_omx_tpp.s
      PRINT LIST="CONVERTMAT FROM=@fmode@@p@@fclass@@p@.omx TO=@fmode@@p@@fclass@@p@.mat FORMAT='TPP' COMPRESSION=0" PRINTO=1
     ENDRUN

    ;run script
     *Voyager.exe convert_omx_tpp.s /Start

   endloop ;files


  ;Merge TAZ demand matrices for assignment
  RUN PGM=MATRIX

    ZONES=%TAZ_COUNT%

    MATI[1]="ctramp_output\auto_@p@_SOV_GP_@p@.mat"
    MATI[2]="ctramp_output\auto_@p@_SOV_PAY_@p@.mat"
    MATI[3]="ctramp_output\auto_@p@_SR2_GP_@p@.mat"
    MATI[4]="ctramp_output\auto_@p@_SR2_HOV_@p@.mat"
    MATI[5]="ctramp_output\auto_@p@_SR2_PAY_@p@.mat"
    MATI[6]="ctramp_output\auto_@p@_SR3_GP_@p@.mat"
    MATI[7]="ctramp_output\auto_@p@_SR3_HOV_@p@.mat"
    MATI[8]="ctramp_output\auto_@p@_SR3_PAY_@p@.mat"

    MATI[9]="ctramp_output\Nonmotor_@p@_BIKE_@p@.mat"
    MATI[10]="ctramp_output\Nonmotor_@p@_WALK_@p@.mat"

    MATI[11]="ctramp_output\other_@p@_SCHLBUS_@p@.mat"

    ;added 2018-07-18 JEF
    MATI[12]="ctramp_output\other_@p@_TAXI_@p@.mat"
    MATI[13]="ctramp_output\other_@p@_TNC_@p@.mat"

    MATO[1]="ctramp_output\TAZ_Demand_@p@.mat", MO=1-11, Name=SOV_GP_@p@, SOV_PAY_@p@, SR2_GP_@p@, SR2_HOV_@p@, SR2_PAY_@p@, SR3_GP_@p@, SR3_HOV_@p@, SR3_PAY_@p@, BIKE_@p@, WALK_@p@, SCHLBUS_@p@

    FILLMW MW[1]=MI.1.1 ;sov-nt

    if(%AV_SCENARIO%=0)
      FILLMW MW[2]=MI.2.1 ; sov-toll
    else
      FILLMW MW[2]=MI.2.1 + MI.13.1 ;sov-toll + TNC
    endif

    FILLMW MW[3]=MI.3.1 ; sr2
    FILLMW MW[2]=MI.4.1 ; sr2-hov

    if(%AV_SCENARIO%=0)
      FILLMW MW[5]=MI.5.1 + MI.12.1 + MI.13.1; sr2-toll + taxi + TNC
    else
      FILLMW MW[5]=MI.5.1 + MI.12.1 ; sr2-toll + taxi
    endif

    FILLMW MW[6]=MI.6.1
    FILLMW MW[7]=MI.7.1
    FILLMW MW[8]=MI.8.1
    FILLMW MW[9]=MI.9.1
    FILLMW MW[10]=MI.10.1
    FILLMW MW[11]=MI.11.1

  ENDRUN

;  *del "ctramp_output\auto_@p@_SOV_GP_@p@.mat"
;  *del "ctramp_output\auto_@p@_SOV_PAY_@p@.mat"
;  *del "ctramp_output\auto_@p@_SR2_GP_@p@.mat"
;  *del "ctramp_output\auto_@p@_SR2_HOV_@p@.mat"
;  *del "ctramp_output\auto_@p@_SR2_PAY_@p@.mat"
;  *del "ctramp_output\auto_@p@_SR3_GP_@p@.mat"
;  *del "ctramp_output\auto_@p@_SR3_HOV_@p@.mat"
;  *del "ctramp_output\auto_@p@_SR3_PAY_@p@.mat"
;  *del "ctramp_output\Nonmotor_@p@_BIKE_@p@.mat"
;  *del "ctramp_output\Nonmotor_@p@_WALK_@p@.mat"
;  *del "ctramp_output\other_@p@_SCHLBUS_@p@.mat"

     *copy ctramp_output\TAZ_Demand_@p@.mat ctramp_output\TAZ_Demand_@p@_%ITERATION%.mat

endloop ; period
