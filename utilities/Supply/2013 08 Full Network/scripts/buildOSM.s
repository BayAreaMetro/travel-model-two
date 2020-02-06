
;"C:\Program Files (x86)\Citilabs\CubeVoyager\Voyager.exe" buildOSM.s /Start
;only highway=footway | pedestrian | steps

RUN PGM=NETWORK
  NODEI = "cube_node.csv" VAR=N,X,Y,Type,ID
  LINKI = "cube_link.csv" VAR=A,VAR=B,VAR=Type,TYP=C,VAR=ID,VAR=HighwayT,TYP=C,VAR=RailwayT,TYP=C,VAR=BikewayT,TYP=C,VAR=CyclewayT,TYP=C,VAR=PedestrianT,TYP=C,VAR=ParkingT,TYP=C
  NETO  = "osm.net"
  
  ;put TAZ centroid number and coordinates into arrays for later
  array _nodes=10000000
  PHASE=INPUT FILEI=ni.1
    _nodes[N]=0
  endphase
  
  PHASE=LINKMERGE
    If (HighwayT='footway' | HighwayT='pedestrian' | HighwayT='steps') 
      ;Keep link and nodes
      _AX = A.X
      _AY = A.Y
      _BX = B.X
      _BY = B.Y
      
      IF (_nodes[A] = 0)
        print FORM=16.4LRS, file="nodes.txt", CSV=T, list=A,_AX,_AY
        _nodes[A] = 1
      ENDIF
      IF (_nodes[B] = 0)
        print FORM=16.4LRS, file="nodes.txt", CSV=T, list=B,_BX,_BY
        _nodes[B] = 1
      ENDIF
      
    ENDIF
  ENDPHASE
ENDRUN

*del osm.net

RUN PGM=NETWORK
  NODEI = "nodes.txt" VAR=N,X,Y
  LINKI = "cube_link.csv" VAR=A,VAR=B,VAR=Type,TYP=C,VAR=ID,VAR=HighwayT,TYP=C,VAR=RailwayT,TYP=C,VAR=BikewayT,TYP=C,VAR=CyclewayT,TYP=C,VAR=PedestrianT,TYP=C,VAR=ParkingT,TYP=C
  NETO  = "osm.net"
  
  PHASE=LINKMERGE
    If (HighwayT='footway' | HighwayT='pedestrian' | HighwayT='steps') 
      ;Keep record
    ELSE
      DELETE
    ENDIF
  ENDPHASE
ENDRUN

*del nodes.txt
