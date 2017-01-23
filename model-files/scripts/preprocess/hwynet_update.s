;delete collectors from time-period assignment networks

loop period = 1,5
    ; a two letter token is used for each time period
    if (period = 1)   
      token_period = 'EA'   
    elseif (period = 2)   
      token_period = 'AM'    
    elseif (period = 3)   
      token_period = 'MD'    
    elseif (period = 4)   
      token_period = 'PM'
    elseif (period = 5)   
      token_period = 'EV'
    endif

    run pgm = network
        PAR NODES=10000000
        NETI = .\..\..\..\hwy\avgload@token_period@_taz.net
        NETO = .\..\..\..\hwy\avgload@token_period@_taz_temp1.net
		
        PHASE=LINKMERGE
			    IF(LI.1.FRC = 7 || LI.1.FRC = 8) DELETE
        ENDPHASE
    ENDRUN
    
*DEL .\..\..\..\hwy\avgload@token_period@_taz.net
*REN .\..\..\..\hwy\avgload@token_period@_taz_temp1.net .\..\..\..\hwy\avgload@token_period@_taz.net

endloop
