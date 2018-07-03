; Code bike and ped ok on bridges
; Ben Stabler, stabler@pbworld.com, 07/17/13

RUN PGM=NETWORK
  PAR  NODES=10000000
  NETI = mtc_final_network.net  
  LINKI[2] = bikepedok.csv VAR=A,B,BIKEPEDOK
  NETO = mtc_final_network2.net
ENDRUN

*copy mtc_final_network2.net  mtc_final_network.net  
*del mtc_final_network2.net  