RUN PGM=CUBE Parameters ='/Command /CloseWhenDone /Minimize /NoSplash'
	
	function = SHAPE2NETWORK
		shpi="..\shapefiles\ca_jc_relevant_sp.shp"
		shpi="..\shapefiles\ca_nw_Intersect_sp.shp"
		neto="..\shapefiles\tana_sp.net"
		PointNodeNumField="ID_hash"
		AnodeField="F_JNCTID_h"
		BnodeField="T_JNCTID_h"
		
		;required defaults
		LevelField=""
		DirectionOption=3 ;1 for one-way, 2 for two-way, 3 for use field to specify
		DirectionField="oneway_rec"
		AddDistanceField=N
		DistanceScale=1
		NodeGroupingLimit=0.0001
		StartingNewNode=1
		HighestZone=1
	endfunction
	
ENDRUN