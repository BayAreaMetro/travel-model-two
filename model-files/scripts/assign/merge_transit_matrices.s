; ----------------------------------------------------------------------------------------------------------------
; merge_demand_matrices.s
;
; TP+ script to merge the transit trip matrix outputs from the CTRAMP model into TAP (transit)
; demand matrices for assignment.
;
; Input:  Demand matrices output by CTRAMP:
;            transit_set@set@_@p@_KNRTNC_SET_@p@.mat
;            transit_set@set@_@p@_KNRPRV_SET_@p@.mat
;            transit_set@set@_@p@_PNR_SET_@p@.mat
;            transit_set@set@_@p@_WLK_SET_@p@.mat
;
;         where @p@ is one of the five time periods (EA,AM,MD,PM,EV)
;         where @set@ is one of the transit skim sets (1,2,3)
;
; Output: TAP level demand matrices:
;            TAP_Demand_set@set@_@p@.mat
;
;         where @p@ is one of the five time periods (EA,AM,MD,PM,EV)
;         where @set@ is one of the transit skim sets (1,2,3)
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


  ; creat set matrices
  loop set = 1, 3

  ;convert from open matrix to cube
  loop files = 1, 4

    if (files = 1)
      fmode = 'ctramp_output\Transit_'
      fclass = '_WLK_TRN_'
    elseif (files = 2)
       fmode = 'ctramp_output\Transit_'
       fclass = '_PNR_TRN_'
    elseif (files = 3)
      fmode = 'ctramp_output\Transit_'
      fclass = '_KNRPRV_TRN_'
    elseif (files = 4)
      fmode = 'ctramp_output\Transit_'
      fclass = '_KNRTNC_TRN_'
    endif

    ;write Cube script since cant pass tokens to RUN PGM = CUBE
    RUN PGM=MATRIX
     ZONES=1
     FILEO PRINTO[1] = convert_omx_tpp.s
     PRINT LIST="CONVERTMAT FROM=@fmode@@p@@fclass@set@set@_@p@.omx TO=@fmode@@p@@fclass@set@set@_@p@.mat FORMAT='TPP' COMPRESSION=0" PRINTO=1
    ENDRUN

   ;run script
    *Voyager.exe convert_omx_tpp.s /Start

  endloop ;files

    ;Merge TAP demand matrices for assignment
    RUN PGM=MATRIX

      ZONES=%TAP_COUNT%

      MATI[1]="ctramp_output\Transit_@p@_WLK_TRN_set@set@_@p@.mat"
      MATI[2]="ctramp_output\Transit_@p@_PNR_TRN_set@set@_@p@.mat"
      MATI[3]="ctramp_output\Transit_@p@_KNRPRV_TRN_set@set@_@p@.mat"
      MATI[4]="ctramp_output\Transit_@p@_KNRTNC_TRN_set@set@_@p@.mat"

      MATO[1]="ctramp_output\TAP_Demand_set@set@_@p@.mat", MO=1-3, Name=WLK_SET_@p@, PNR_SET_@p@, KNR_SET_@p@

      FILLMW MW[1]=MI.1.1
      FILLMW MW[2]=MI.2.1
      FILLMW MW[3]=MI.3.1 + MI.4.1

    ENDRUN

  ;  *del "ctramp_output\Transit_set@set@_@p@_KNR_TRN_@p@.mat"
  ;  *del "ctramp_output\Transit_set@set@_@p@_PNR_TRN_@p@.mat"
  ;  *del "ctramp_output\Transit_set@set@_@p@_WLK_TRN_@p@.mat"

  endloop ; set

endloop ; period
