;get node sets for use link corridors

RUN PGM = CUBE Parameters ='/Command /CloseWhenDone /Minimize /NoSplash'
  FUNCTION = BUILDPATH
    neti="tana_sp_with_maz_taz_tap_centroids_connectors_routes.net"
    pathprinto="use_links_nodes.csv"
    CostSpec="FEET" ;impedance
    fileformat=txt
    LinkSelection="A >= 3000000 & B >= 3000000 & FRC < 4"

; Set the OD Pairs
Origin=3060215 Destination=3699224
Origin=3046551 Destination=3048925
Origin=3649848 Destination=3642690
Origin=3026114 Destination=3644294
Origin=3074470 Destination=3074523
Origin=3171702 Destination=3154643
Origin=4106402 Destination=3075007
Origin=4105760 Destination=3015790
Origin=4098917 Destination=4108032
Origin=3081159 Destination=3080750
Origin=3639758 Destination=3080750
Origin=3049506 Destination=3657327
Origin=3976465 Destination=4116354
Origin=3842982 Destination=4052437
Origin=4070310 Destination=3055095
Origin=3026338 Destination=4003602
Origin=4004244 Destination=3646870
Origin=3978117 Destination=3981883
Origin=3983418 Destination=3982228
Origin=4025351 Destination=3040857
Origin=3027891 Destination=3016921
Origin=3031122 Destination=3045885
Origin=3012819 Destination=3885673
Origin=3847688 Destination=3919546
Origin=3922350 Destination=3034360
Origin=3885673 Destination=3032066
Origin=3885673 Destination=3015339
Origin=3946587 Destination=3840381
Origin=3418322 Destination=3813236
Origin=3816052 Destination=3423602
Origin=3583189 Destination=3052466
Origin=3534605 Destination=3533190
Origin=3541689 Destination=3537555
Origin=3813236 Destination=3782109
Origin=3765374 Destination=3816052
Origin=3782109 Destination=3541689
Origin=3533190 Destination=3765374
Origin=3052319 Destination=3768867
Origin=3048770 Destination=3049077
Origin=3781363 Destination=3052099
Origin=3067375 Destination=3035960
Origin=3546374 Destination=3056969
Origin=3041027 Destination=3543927
Origin=3811052 Destination=3847688
Origin=3015339 Destination=3021608
Origin=3534380 Destination=3546100
Origin=3533190 Destination=3816052
Origin=3813236 Destination=3541689
    CLOSE
  ENDFUNCTION
ENDRUN