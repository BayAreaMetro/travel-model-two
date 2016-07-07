; ----------------------------------------------------------------------------------------------------------------
; merge_demand_matrices.s
;
; TP+ script to merge the trip matrix outputs from the CTRAMP model into TAZ (non-transit) and TAP (transit)
; demand matrices. The CTRAMP output matrices are individually segmented by mode, and this script combines
; all of the individual mode matrices into a single matrix file (each mode is kept separate, but they are
; all combined into a single file).
;
; Input:  Demand matrices output by CTRAMP:
;            auto_@p@_SOV_GP_@p@.mat
;            auto_@p@_SOV_PAY_@p@.mat
;            auto_@p@_SR2_GP_@p@.mat
;            auto_@p@_SR2_HOV_@p@.mat
;            auto_@p@_SR2_PAY_@p@.mat
;            auto_@p@_SR3_GP_@p@.mat
;            auto_@p@_SR3_HOV_@p@.mat
;            auto_@p@_SR3_PAY_@p@.mat
;            nonmotor_@p@_BIKE_@p@.mat
;            nonmotor_@p@_WALK_@p@.mat
;            other_@p@_SCHLBUS_@p@.mat
;            transit_set@set@_@p@_KNR_SET_@p@.mat
;            transit_set@set@_@p@_PNR_SET_@p@.mat
;            transit_set@set@_@p@_WLK_SET_@p@.mat
;
;         where @p@ is one of the five time periods (EA,AM,MD,PM,EV)
;         where @set@ is one of the transit skim sets (1,2,3)
;
; Output: TAZ and TAP level demand matrices:
;            TAZ_Demand_@p@.mat
;            TAP_Demand_set@set@_@p@.mat
;
;         where @p@ is one of the five time periods (EA,AM,MD,PM,EV)
;         where @set@ is one of the transit skim sets (1,2,3)
;
; version:  Travel Model Zed
; authors:  Ben Stabler (2013); crf (2014)
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
    
    MATI[9]="ctramp_output\nonmotor_@p@_BIKE_@p@.mat"
    MATI[10]="ctramp_output\nonmotor_@p@_WALK_@p@.mat"
    
    MATI[11]="ctramp_output\other_@p@_SCHLBUS_@p@.mat"
    
    MATO[1]="ctramp_output\TAZ_Demand_@p@.mat", MO=1-11, Name=SOV_GP_@p@, SOV_PAY_@p@, SR2_GP_@p@, SR2_HOV_@p@, SR2_PAY_@p@, SR3_GP_@p@, SR3_HOV_@p@, SR3_PAY_@p@, BIKE_@p@, WALK_@p@, SCHLBUS_@p@
    
    FILLMW MW[1]=MI.1.1
    FILLMW MW[2]=MI.2.1
    FILLMW MW[3]=MI.3.1 
    FILLMW MW[4]=MI.4.1 
    FILLMW MW[5]=MI.5.1 
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
;  *del "ctramp_output\nonmotor_@p@_BIKE_@p@.mat"
;  *del "ctramp_output\nonmotor_@p@_WALK_@p@.mat"
;  *del "ctramp_output\other_@p@_SCHLBUS_@p@.mat"
  
  ; creat set matrices
  loop set = 1, 3
  
    ;Merge TAP demand matrices for assignment
    RUN PGM=MATRIX
      
      ZONES=%TAP_COUNT%
      
      MATI[1]="ctramp_output\transit_set@set@_@p@_KNR_SET_@p@.mat"
      MATI[2]="ctramp_output\transit_set@set@_@p@_PNR_SET_@p@.mat"
      MATI[3]="ctramp_output\transit_set@set@_@p@_WLK_SET_@p@.mat"
      
      MATO[1]="ctramp_output\TAP_Demand_set@set@_@p@.mat", MO=1-3, Name=WLK_SET_@p@, PNR_SET_@p@, KNR_SET_@p@
      
      FILLMW MW[1]=MI.1.1
      FILLMW MW[2]=MI.2.1
      FILLMW MW[3]=MI.3.1 
      
    ENDRUN
    
  ;  *del "ctramp_output\transit_set@set@_@p@_KNR_SET_@p@.mat"
  ;  *del "ctramp_output\transit_set@set@_@p@_PNR_SET_@p@.mat"
  ;  *del "ctramp_output\transit_set@set@_@p@_WLK_SET_@p@.mat"

  endloop ; set

endloop ; period
