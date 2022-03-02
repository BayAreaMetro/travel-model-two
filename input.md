---
layout: page
title: Input
---

# Input Files

---
CONTENTS

1. [Input File List](#input-file-list)
1. [Time Periods](#time-periods)
1. [Roadway Network](#roadway-network)
   - [County Node Numbering System](#county-node-numbering-system)
   - [Node Attributes](#node-attributes)
   - [Link Attributes](#link-attributes)
      - [TOLLBOOTH & TOLLSEG](#tollbooth--tollseg)
1. [Transit Network](#transit-network)
   - [Line Attributes](#line-attributes)
   - [Transit Modes](#transit-modes)
   - [Transit Fares](#transit-fares)
1. [Micro Zonal Data](#micro-zonal-data)
1. [Zonal Data](#zonal-data)
1. [Synthetic Population](#synthetic-population)
   - [Households](#households)
   - [Persons](#persons)
1. [Truck Distribution](#truck-distribution)
   - [Friction Factors](#friction-factors)
   - [K-Factors](#k-factors)
1. [Fixed Demand](#fixed-demand)
   - [Internal/External](#internalexternal)
   - [Air Passenger](#air-passenger)

---

## Input File List

The table below contains brief descriptions of the input files required to execute the travel model.

| **File name** | **Purpose** | **Folder location** | **File type** | **File format** |
|---------------|-------------|---------------------|---------------|-----------------|
| `mtc_final_network.net` | Highway, bike, walk network | hwy\ | [Citilabs Cube](http://citilabs.com/products/cube)| [Roadway Network](#roadway-network) |
| `mazData.csv` | Micro zone data  | landuse\ | CSV | [Micro Zonal Data](#micro-zonal-data) |
| `tazData.csv` | Travel analysis zone data | landuse\ | CSV | [Zonal Data](#zonal-data) |
| `truckFF.dat` | Friction factors for the commercial vehicle distribution models | nonres\ | ASCII | [Truck Distribution](#truck-distribution) |
| `truckkfact.k22.z1454.mat` | "K-factors" for the commercial vehicle distribution models | nonres\ | [Citilabs Cube](http://citilabs.com/products/cube) | [Truck Distribution](#truck-distribution) |
| `truck_kfactors_taz.csv` | "K-factors" for the commercial vehicle distribution models | nonres\ | CSV | [Truck Distribution](#truck-distribution) |
| `ixDailyYYYY.tpp` | Internal-external fixed trip table for year YYYY | nonres\ | [Citilabs Cube](http://citilabs.com/products/cube) | [Fixed Demand](#fixed-demand) |
| `IXDaily2006x4.may2208.new` | Internal-external input fixed trip table | nonres\ | [Citilabs Cube](http://citilabs.com/products/cube) | [Fixed Demand](#fixed-demand) |
|  `YYYY_fromtoAAA.csv` |  Airport passenger fixed trips for year YYYY and airport AAA  | nonres\ | CSV | [Fixed Demand](#fixed-demand) |
| `households.csv` | Synthetic population household file | popsyn\ | CSV | PopSynHousehold |
| `persons.csv` | Synthetic population person file | popsyn\ | CSV |   |
| `transitLines.lin` | Transit lines | trn\transit_lines | [Citilabs Cube](http://citilabs.com/products/cube)| TransitNetwork  |
| `transitFactors_MMMM.fac` | Cube Public Transport (PT) factor files by transit line haul mode MMMM | trn\transit_support | [Citilabs Cube](http://citilabs.com/products/cube) | TransitNetwork |

## Time Periods

Time periods in Travel Model Two are consistent with Travel Model One:

| **Time Period** | **Times** | **Duration** |
|-----------------|-----------|--------------|
| EA (early AM) | 3 am to 6 am | 3 hours |
| AM (AM peak period) | 6 am to 10 am | 4 hours |
| MD (midday) | 10 am to 3 pm | 5 hours |
| PM (PM peak period) | 3 pm to 7 pm | 4 hours |
| EV (evening) | 7 pm to 3 am | 8 hours |

## Roadway Network

The all streets highway network, walk network, and bicycle network were developed from [OpenStreetMap](http://www.openstreetmap.org/).  The *projection* is [**NAD 1983 StatePlane California VI FIPS 0406 Feet**](https://epsg.io/102646).

### County Node Numbering System

The highway network uses a numbering system whereby each county has a reserved block of nodes. Within each county’s block, nodes 1 through 9,999 are reserved for TAZs, 10,001 through 89,999 are for MAZs, and 90,001 through 99,999 for transit access points or TAPs. The blocks are assigned to the nine counties per MTC’s numbering scheme, as shown in the table below.

Roadway, walk, bicycle, and transit network nodes are numbered by county as well and range from 1,000,000 to 10,000,000 as shown below.

Code  | County | TAZs | MAZs |  TAPs | Network Node |
|:---:|:-------|:-----|:-----|:------|:-------------|
1 | San Francisco |	1 - 9,999 |	10,001 – 89,999 |	90,001 – 99,999 |	1,000,000 – 1,500,000 |
2 |	San Mateo |	100,001 – 109,999 |	110,001 – 189,999 |	190,001 – 199,999 |	1,500,000 – 2,000,000 |
3 |	Santa Clara |	200,001 – 209,999 |	210,001 – 289,999 |	290,001 – 299,999 |	2,000,000 – 2,500,000 |
4 |	Alameda |	300,001 – 309,999 |	310,001 – 389,999 |	390,001 – 399,999 |	2,500,000 – 3,000,000 |
5 |	Contra Costa |	400,001 – 409,999 |	410,001 – 489,999 |	490,001 – 499,999 |	3,000,000 – 3,500,000 |
6 |	Solano |	500,001 – 509,999 |	510,001 – 589,999 |	590,001 – 599,999 |	3,500,000 – 4,000,000 |
7 |	Napa |	600,001 – 609,999 |	610,001 – 689,999 |	690,001 – 699,999 |	4,000,000 – 4,500,000 |
8 |	Sonoma |	700,001 – 709,999 |	710,001 – 789,999 |	790,001 – 799,999 |	4,500,000 – 5,000,000 |
9 |	Marin |	800,001 – 809,999 |	810,001 – 889,999 |	890,001 – 899,999 |	5,000,000 – 5,500,000 |
  | External | 900,001 - 999,999

### Node Attributes

The following node attributes are included in the master network.

|*Field* | *Description* | *Data Type*
|--------|-------------|----------
|*N* | Node Number | Integer (see [Node Numbering](#county-node-numbering-system))
|*X* | X coordinate (feet) | Float
|*Y* | Y coordinate (feet) | Float
|*OSM_NODE_ID* | OpenStreetMap node identifier | Integer
|*COUNTY* | County Name | String
|*DRIVE_ACCESS* | Node is used by automobile and/or bus links | Boolean
|*WALK_ACCESS* | Node is used by pedestrian links | Boolean
|*BIKE_ACCESS* | Node is used by bicycle links | Boolean
|*RAIL_ACCESS* | Node is used by rail links | Boolean
|*FAREZONE* | Unique sequential fare zone ID for transit skimming and assignment | Integer
|*TAP_ID* | Transit access point (TAP) associated connected to this node | Integer

### Link Attributes

The following link attributes are included on the master network.

| *Field* | *Description* | *Data Type* | *Source* |
|-------|---------------|-------------|----------|
| *A* | from node | Integer (see [Node Numbering](#county-node-numbering-system)) |
| *B* | to node | Integer (see [Node Numbering](#county-node-numbering-system)) |
| *MODEL_LINK_ID* | Unique link identifier | Integer |   |
| *SHSTGEOMERTRYID* | Unique link shape identifier per SharedStreets approach | String |   |
| *ASSIGNABLE* | Is link used for assignment (1=True, 0=False) | Integer |   |
| *DRIVE_ACCESS* | Link is used by automobiles and/or buses (1=True, 0=False) | Integer |   |
| *BIKE_ACCESS* | Link is used by bicycles (1=True, 0=False) | Integer |   |
| *WALK_ACCESS* | Link is used by pedestrians (1=True, 0=False) | Integer |   |
| *BUS_ONLY* | Link is used by buses, but not automobiles (1=True, 0=False) | Integer |   |
| *RAIL_ONLY* | Link is used by rail vehicles (1=True, 0=False) | Integer |   |
| *DRIVE_ACCESS* | Link is used by automobiles and/or buses (1=True, 0=False) | Integer |   |
| *MANAGED* | Link has a parallel managed lane (1=True, 0=False) | Integer |   |
| *SEGMENT_ID* | Parallel managed lane unique segment identifier (on managed and general purpose lanes) | Integer |   |
| *COUNTY* | County name | String |   |
| *CNTYPE* | Link connector type{::nomarkdown}<br /><ul> <li>BIKE - bike link</li> <li>CRAIL - commuter rail</li> <li>FERRY- ferry link</li> <li>HRAIL - heavy rail link</li> <li>LRAIL- light rail link</li> <li>MAZ - MAZ connector link</li> <li>PED - ped link</li> <li>TANA - regular network link</li> <li>TAP - TAP link</li> <li>TAZ - TAZ connector link</li> <li>USE - HOV (user class) link</li> </ul>{:/} | String |   |
| *TRANSIT* | Is Transit link | Integer |   |
| *TOLLBOOTH* | Toll link.  See [TOLLBOOTH & TOLLSEG table below](#tollbooth--tollseg). Links with values [less than 11](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/block/hwyParam.block) are _bridge tolls_; 11 or above are _value tolls_. | Integer |   |
| *TOLLSEG* | See [TOLLBOOTH & TOLLSEG table below](#tollbooth--tollseg). | Integer |   |
| *FT* | Facility type{::nomarkdown}<br /> <ul><li>1: Freeway</li> <li>2: Expressway</li> <li>3: Ramp</li> <li>4:  Divided Arterial</li> <li>5: Undivided Arterial</li> <li>6: Collector</li> <li>7: Local</li> <li>8: Connector (MAZ, TAZ, TAP)</li></ul>{:/} | Integer |   |
| *LANES_[EA,AM,MD,PM,EV]* | Model number of lanes by time period | Integer |   |
| *USECLASS_[EA,AM,MD,PM,EV]* | Link user class by time period{::nomarkdown}<br /> <ul><li>0 - NA; link open to everyone</li> <li>2 - HOV 2+</li> <li>3 - HOV 3+</li> <li>4 - No combination trucks</li></ul>{:/} | Integer |   |

#### TOLLBOOTH & TOLLSEG

| *TOLLBOOTH* | *TOLLSEG* | *Definition* | *Opening Year (or anticipated) for Toll Collection* | *Project Card* |
|-------------|-----------|--------------|-----------------------------------------------------|----------|
| 1 | | Benicia-Martinez Bridge | [1962](https://en.wikipedia.org/wiki/Benicia%E2%80%93Martinez_Bridge#Historical_toll_rates) | [`year_2015_hov_lane_benicia_bridge_toll_plaza.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2015_hov_lane_benicia_bridge_toll_plaza.yml) |
| 2 | | Carquinez Bridge | [1958](https://en.wikipedia.org/wiki/Carquinez_Bridge#Historical_toll_rates) | [`year_2015_carquinez_bridge_toll_plaza.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2015_carquinez_bridge_toll_plaza.yml) |
| 3 | | Richmond Bridge | [1956](https://en.wikipedia.org/wiki/Richmond%E2%80%93San_Rafael_Bridge#Historical_toll_rates) | [`year_2015_richmond_bridge_toll_plaza.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2015_richmond_bridge_toll_plaza.yml) |
| 4 | | Golden Gate Bridge | [1937](https://en.wikipedia.org/wiki/Golden_Gate_Bridge#Tolls) | [`year_2015_golden_gate_bridge_toll_plaza.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2015_golden_gate_bridge_toll_plaza.yml) |
| 5 | | San Francisco/Oakland Bay Bridge | [1936](https://en.wikipedia.org/wiki/San_Francisco%E2%80%93Oakland_Bay_Bridge#Financing_and_tolls) | [`year_2015_hov_lane_bay_bridge_toll_plaza_segment_02.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2015_hov_lane_bay_bridge_toll_plaza_segment_02.yml), [`year_2015_hov_lane_bay_bridge_toll_plaza_segment_03.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2015_hov_lane_bay_bridge_toll_plaza_segment_03.yml) |
| 6 | | San Mateo Bridge | [1929](https://en.wikipedia.org/wiki/San_Mateo%E2%80%93Hayward_Bridge#Historical_toll_rates) | [`year_2015_san_mateo_bridge_toll_plaza.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2015_san_mateo_bridge_toll_plaza.yml) |
| 7 | | Dumbarton Bridge | [1927](https://en.wikipedia.org/wiki/Dumbarton_Bridge_(California)#Historical_toll_rates) | [`year_2015_dumbarton_bridge_toll_plaza.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2015_dumbarton_bridge_toll_plaza.yml) |
| 8 | | Antioch Bridge | [1989](https://en.wikipedia.org/wiki/Antioch_Bridge#Historical_toll_rates) | [`year_2015_antioch_bridge.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2015_antioch_bridge.yml) |
| 25 | | [I-680 Sunol Express Lanes Phase 1](https://511.org/driving/express-lanes/i-680-sunol-express-lane) *Southbound* | | |
| 25 | 1 | Andrade Rd to Washington Blvd | September 2010 | |
| 25 | 2 | Washington Blvd to Mission Blvd | September 2010 | |
| 25 | 3 | Mission Blvd to SR 237 | September 2010 | |
| 28 | | [I-580 Express Lanes](https://www.alamedactc.org/programs-projects/expresslanesops/580expresslanes/) *Eastbound* | | |
| 28 | 1 | Hacienda Dr to Airway Blvd | February 2016 | [`year_2016_managed_lane_i580e_segment_01_hacienda_drive_to_airway_blvd.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2016_managed_lane_i580e_segment_01_hacienda_drive_to_airway_blvd.yml), [`year_2016_managed_lane_i580e_segment_02_hacienda_drive_to_airway_blvd.yml`](year_2016_managed_lane_i580e_segment_02_hacienda_drive_to_airway_blvd.yml) |
| 28 | 2 | Airway Blvd to Livermore Ave | February 2016 | [`year_2016_managed_lane_i580e_airway_blvd_to_livermore_ave.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2016_managed_lane_i580e_airway_blvd_to_livermore_ave.yml) |
| 28 | 3 | Livermore Ave to Vasco Rd | February 2016 | [`year_2016_managed_lane_i580e_segment_01_livermore_ave_to_vasco_road.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2016_managed_lane_i580e_segment_01_livermore_ave_to_vasco_road.yml), [`year_2016_managed_lane_i580e_segment_02_livermore_ave_to_vasco_road.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2016_managed_lane_i580e_segment_02_livermore_ave_to_vasco_road.yml) |
| 28 | 4 | Vasco Rd to Greenville Rd | February 2016 | [`year_2016_managed_lane_i580e_vasco_road_to_greenville_road.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2016_managed_lane_i580e_vasco_road_to_greenville_road.yml) |
| 29 | | [I-580 Express Lanes](https://www.alamedactc.org/programs-projects/expresslanesops/580expresslanes/) *Westbound* | | |
| 29 | 1 | Greenville Rd to Springtown Blvd | February 2016 | [`year_2016_managed_lane_i580w_greenville_road_to_springtown_blvd.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2016_managed_lane_i580w_greenville_road_to_springtown_blvd.yml) |
| 29 | 2 | Springtown to Isabel Ave | February 2016 | [`year_2016_managed_lane_i580w_springtown_blvd_to_isabel_ave.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2016_managed_lane_i580w_springtown_blvd_to_isabel_ave.yml) |
| 29 | 3 | Isabel Ave to Fallon Rd | February 2016 | [`year_2016_managed_lane_i580w_isabel_ave_to_fallon_road.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2016_managed_lane_i580w_isabel_ave_to_fallon_road.yml) |
| 29 | 4 | Fallon Rd to Hacienda Dr | February 2016 | [`year_2016_managed_lane_i580w_fallon_road_to_hacienda_drive.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2016_managed_lane_i580w_fallon_road_to_hacienda_drive.yml) |
| 29 | 5 | Hacienda Dr to San Ramon Rd | February 2016 | [`year_2016_managed_lane_i580w_hacienda_drive_to_san_ramon_road.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2016_managed_lane_i580w_hacienda_drive_to_san_ramon_road.yml) |
| 31 | | [SR-237 Express Lanes Phase 1](https://511.org/driving/express-lanes/b-sr-237-express-lanes) *Southbound* | | |
| 31 | 1 | Dixon Landing Rd to N First Ave (Westbound) | March 2012 | |
| 32 | | [SR-237 Express Lanes Phase 1](https://511.org/driving/express-lanes/b-sr-237-express-lanes) *Northbound* | | |
| 32 | 1 | N First Ave to Dixon Landing Rd (Eastbound) | March 2012 | |
| 33 | | [I-680 Contra Costa Express Lanes](https://511.org/driving/express-lanes/i-680-contra-costa-express-lanes) *Southbound* | | |
| 33 | 1 | Rudgear to Crow Canyon (Crow Canyon SB pricing zone) | October 2017 | [`year_2017_managed_lane_i680n_acosta_blvd_to_livorna_road.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2017_managed_lane_i680n_acosta_blvd_to_livorna_road.yml)|
| 33 | 2 | Crow Canyon to Alcosta (Alcosta pricing zone) | October 2017 | |
| 34 | | [I-680 Contra Costa Express Lanes](https://511.org/driving/express-lanes/i-680-contra-costa-express-lanes) *Northbound* | October 2017 | |
| 34 | 1 | Alcosta to Crow Canyon (Crow Canyon NB pricing zone) | October 2017 | [`year_2017_managed_lane_i680s_benicia_bridge_to_acosta_blvd.yml`](https://github.com/BayAreaMetro/travel-model-two-networks/blob/develop/project_cards/year_2017_managed_lane_i680s_benicia_bridge_to_acosta_blvd.yml) |
| 34 | 2 | Crow Canyon to Livorna (Livorna pricing zone) | October 2017 | |

## Transit Network

The transit network is made up of three core components: transit lines, transit modes, and transit fares.  The transit lines were built GTFS feeds from raound 2015.  The lines are coded with a mode (see below) and serve a series of stop nodes.  Transit fares are coded according to Cube's Public Transport program (see below).

Transit trips are assigned between transit access points (TAPs), which represent individual or collections of transit stops for transit access/egress.  TAPs are essentially transit specific TAZs that are automatically coded based on the transit network.  See the [Level of Service Information](#level-of-service-information).

### Link Attributes

|Field                |Description                                                                             |Data Type|
|---------------------|----------------------------------------------------------------------------------------|---------|
|trip_id              |unique identifier for each trip                                                         |Integer  |
|is_stop_A            |if node A is a transit stop                                                             |boolean  |
|access_A             |                                                                                        |         |
|stop_sequence_A      |stop sequence of node A, if node A is a stop                                            |Integer  |
|shape_pt_sequence_B  |sequence of node A in the route                                                         |Integer  |
|shape_model_node_id_B|model_node_id of node B                                                                 |Integer  |
|NAME                 |name of route with TOD                                                                  |string   |
|agency_id            |transit agency id                                                                       |string   |
|TM2_line_haul_name   |'Commuter rail', 'Express bus', 'Local bus', 'Light rail', 'Ferry service', 'Heavy rail'|string   |
|TM2_mode             |see mode dictionary                                                                     |Integer  |
|faresystem           |faresystem (1-50)                                                                       |Integer  |
|tod                  |time of day (1, 2, 3, 4, 5)                                                             |Integer  |
|HEADWAY              |transit service headway in minute                                                       |Integer  |
|A                    |A of link                                                                               |Integer  |
|B                    |B of link                                                                               |Integer  |
|model_link_id        |model_link_id                                                                           |Integer  |
|shstGeometryId       |the shstGeometryId of the link                                                          |Integer  |


### Transit Modes

The following transit modes are defined based on the [Open511](https://511.org/developers/list/apis/) attributes (but not completely, since they came from the GTFS database predecessor, the Regional Transit Database).  These modes represent combinations of operators and technology.

|TM2_operator|agency_name|TM2_mode                                     |TM2_line_haul_name|faresystem   |
|------------|-----------|---------------------------------------------|------------------|-------------|
|30          |AC Transit |84                                           |Express bus       |9            |
|30          |AC Transit |30                                           |Local bus         |9            |
|30          |AC Transit |30                                           |Local bus         |11           |
|5           |ACE Altamont Corridor Express|133                                          |Commuter rail     |1            |
|26          |Bay Area Rapid Transit|120                                          |Heavy rail        |2            |
|3           |Blue & Gold Fleet|103                                          |Ferry service     |13           |
|3           |Blue & Gold Fleet|103                                          |Ferry service     |14           |
|3           |Blue & Gold Fleet|103                                          |Ferry service     |12           |
|17          |Caltrain   |130                                          |Commuter rail     |3            |
|23          |Capitol Corridor|131                                          |Commuter rail     |4            |
|19          |Cloverdale Transit|63                                           |Local bus         |7            |
|17          |Commute.org Shuttle|14                                           |Local bus         |46           |
|15          |County Connection|86                                           |Express bus       |16           |
|15          |County Connection|42                                           |Local bus         |15           |
|15          |County Connection|42                                           |Local bus         |17           |
|10          |Emery Go-Round|12                                           |Local bus         |18           |
|28          |Fairfield and Suisun Transit|92                                           |Express bus       |10           |
|28          |Fairfield and Suisun Transit|52                                           |Local bus         |10           |
|35          |Golden Gate Transit|87                                           |Express bus       |8            |
|20          |Golden Gate Transit|101                                          |Ferry service     |19           |
|20          |Golden Gate Transit|101                                          |Ferry service     |20           |
|35          |Golden Gate Transit|70                                           |Local bus         |8            |
|99          |MVgo Mountain View|16                                           |Local bus         |21           |
|39          |Marin Transit|71                                           |Local bus         |23           |
|39          |Marin Transit|71                                           |Local bus         |24           |
|21          |Petaluma Transit|68                                           |Local bus         |47           |
|13          |Rio Vista Delta Breeze|52                                           |Local bus         |5            |
|6           |SamTrans   |80                                           |Express bus       |6            |
|6           |SamTrans   |24                                           |Local bus         |6            |
|25          |San Francisco Bay Ferry|101                                          |Ferry service     |28           |
|25          |San Francisco Bay Ferry|101                                          |Ferry service     |30           |
|25          |San Francisco Bay Ferry|101                                          |Ferry service     |31           |
|25          |San Francisco Bay Ferry|101                                          |Ferry service     |32           |
|25          |San Francisco Bay Ferry|101                                          |Ferry service     |29           |
|22          |San Francisco Municipal Transportation Agency|110                                          |Light rail        |25           |
|22          |San Francisco Municipal Transportation Agency|20                                           |Local bus         |25           |
|22          |San Francisco Municipal Transportation Agency|21                                           |Local bus         |26           |
|1           |Santa Rosa CityBus|66                                           |Local bus         |33           |
|12          |SolTrans   |91                                           |Express bus       |35           |
|12          |SolTrans   |49                                           |Local bus         |34           |
|12          |SolTrans   |49                                           |Local bus         |35           |
|19          |Sonoma County Transit|63                                           |Local bus         |7            |
|7           |Stanford Marguerite Shuttle|13                                           |Local bus         |22           |
|4           |Tri Delta Transit|95                                           |Express bus       |36           |
|4           |Tri Delta Transit|44                                           |Local bus         |37           |
|4           |Tri Delta Transit|44                                           |Local bus         |36           |
|36          |Union City Transit|38                                           |Local bus         |38           |
|31          |VTA        |81                                           |Express bus       |40           |
|31          |VTA        |81                                           |Express bus       |41           |
|31          |VTA        |111                                          |Light rail        |41           |
|31          |VTA        |28                                           |Local bus         |41           |
|31          |VTA        |28                                           |Local bus         |39           |
|14          |Vacaville City Coach|56                                           |Local bus         |48           |
|38          |Vine (Napa County)|94                                           |Express bus       |43           |
|38          |Vine (Napa County)|60                                           |Local bus         |42           |
|38          |Vine (Napa County)|60                                           |Local bus         |44           |
|37          |WestCat (Western Contra Costa)|90                                           |Express bus       |49           |
|37          |WestCat (Western Contra Costa)|90                                           |Express bus       |50           |
|37          |WestCat (Western Contra Costa)|46                                           |Local bus         |49           |
|24          |Wheels Bus |17                                           |Local bus         |45           |


### Transit Fares

Transit fares are modeled in Cube's Public Transport (PT) program as follows:
  1. Each transit mode is assigned a fare system in the Cube factor files
  1. Each fare system is defined in the fares.far fare file
  1. Each fare system is either FROMTO (fare zone based) or FLAT (initial + transfer in fare)
  1. For FROMTO fare systems:
    1. Each stop node is assigned a FAREZONE ID in the master network
    1. The fare is looked up from the fare matrix (fareMatrix.txt), which is a text file with the following columns: MATRIX ZONE_I ZONE_J VALUE
    1. The fare to transfer in from other modes is defined via the FAREFROMFS array (of modes) in the fares.far file
  1. For FLAT fare systems:
    1. The initial fare is defined via the IBOARDFARE in the fares.far file
    1. The fare to transfer in from other modes is defined via the FAREFROMFS array (of modes) in the fares.far file

## Micro Zonal Data

| *Column Name* | *Description* | *Used by* | *Source* |
|---------------|---------------|-----------|----------|
| *MAZ_ORIGINAL* | Original micro zone number. It's original because these will get renumbered during the model run assuming [the node numbering conventions](#county-node-numbering-system) | |
| *TAZ_ORIGINAL* | Original TAZ number. It's original because these will get renumbered during the model run assuming [the node numbering conventions](#county-node-numbering-system)  | |
| *CountyID* | County ID Number | MAZAutoTripMatrix via [MgraDataManager] | |
| *CountyName* | County name string | | |
| *DistID* | District ID Number (TODO: link district map) | [TourModeChoice.xls] | District system definition |
| *DistName* | District Name (TODO: link district map) | | District system definition |
| *ACRES* | MAZ acres | [createMazDensityFile.py] | Calculated from shapefile |
| *HH* | Total number of households | [MgraDataManager] | |
| *POP* | Total population | [MgraDataManager] | |
| **Employment Industry Categories** |||
| *ag* | Employment in agriculture: [NAICS] 11 | [Accessibilities] |
| *art_rec* | Employment in arts, entertainment and recreation: [NAICS] 71 | [Accessibilities] |
| *const* | Employment in construction: [NAICS] 23 | [Accessibilities] |
| *eat* | Employment in food services and drinking places: [NAICS] 722 | [Accessibilities] |
| *ed_high* | Employment in junior colleges, colleges, universities: [NAICS] 6112, 6113, 6114, 6115 | [Accessibilities] |
| *ed_k12* | Employment in K-12 schools: [NAICS] 6111 | [Accessibilities] |
| *ed_oth* | Employment in other schools, libraries and educational services: [NAICS] 6116, 6117 | [Accessibilities] |
| *fire* | Employment in FIRE (finance, insurance and real estate): NAICS 52, 53 not in leasing | [Accessibilities] |
| *gov* | Employment in government: [NAICS] 92 | [Accessibilities] |
| *health* | Employment in health care: [NAICS] 62 except those in *serv_soc* | [Accessibilities] |
| *hotel* | Employment in hotels and other accomodations: [NAICS] 721 | [Accessibilities] |
| *info* | Employment in information-based services: [NAICS] 51 | [Accessibilities] |
| *lease* | Employment in leasing: [NAICS] 532 | [Accessibilities] |
| *logis* | Employment in logistics/warehousing and distribution: [NAICS] 42, 493 | [Accessibilities] |
| *man_bio* | Employment in biological/drug manufacturing: [NAICS] 325411, 325412, 325313, 325414 | [Accessibilities] |
| *man_hvy* | Employment in heavy manufacturing: [NAICS] 31-33 subset | [Accessibilities] |
| *man_lgt* | Employment in light manufacturing: [NAICS] 31-33 subset | [Accessibilities] |
| *man_tech* | Employment in high-tech manufacturing: [NAICS] 334 | [Accessibilities] |
| *natres* | Employment in mining and resource extraction: [NAICS] 21 | [Accessibilities] |
| *prof* | Employment in professional and technical services: [NAICS] 54 | [Accessibilities] |
| *ret_loc* | Employment in local-serving retail: [NAICS] 444130, 444190, 444210, 444220, 445110, 445120, 445210, 445220, 445230, 445291, 445292, 445299, 445310, 446110, 446120, 446130, 446191, 446199, 447110, 447190, 448110, 448120, 448130, 448140, 448150, 448190, 448210, 448310, 448320, 451110, 451120, 451130, 451140, 451211, 451212, 452910, 452990, 453110, 453220, 453310, 453910, 453920, 453930, 453991, 453998, 454111, 454112, 454113 | [Accessibilities] |
| *ret_reg* | Employment in regional retail: [NAICS] 441110, 441120, 441210, 441222, 441228, 441310, 441320, 442110, 442210, 442291, 442299, 443141, 443142, 444110, 444120, 452111, 452112, 453210, 454210, 454310, 454390 | [Accessibilities] |
| *serv_bus* | Employment in managerial services, administrative and business services: [NAICS] 55,56 | [Accessibilities] |
| *serv_pers* | Employment in personal and other services: [NAICS] 53, 81 | [Accessibilities] |
| *serv_soc* | Employment in social services and childcare: [NAICS] 624 | [Accessibilities] |
| *transp* | Employment in transportation: [NAICS] 48 (most of it), 49 (not in *logis*) | [Accessibilities] |
| *util* | Employment in utilities: [NAICS] 22, 56 | [Accessibilities] |
| *unclass* | Employment not classified | is this used? |
| *emp_total* | Total employment | [Accessibilities] |
| **School Enrollment Categories** |||
| *publicenrollgradekto8* | Public school grade K-8 enrollment | [Accessibilities] |
| *privateenrollgradekto8* | Private school grade K-8 enrollment | [Accessibilities] |
| *publicenrollgrade9to12* | Public high school grade 9-12 enrollment | [Accessibilities] |
| *privateenrollgrade9to12* | Private high school grade 9-12 enrollment | [Accessibilities] |
| *comm_coll_enroll* | Community college enrollment | [Accessibilities] |
| *EnrollGradeKto8* | Total high school grade 9-12 enrollment | [MgraDataManager] |
| *EnrollGrade9to12* | Total high school grade 9-12 enrollment | [MgraDataManager] |
| *collegeEnroll* | Major College enrollment | [MgraDataManager] |
| *otherCollegeEnroll* | Other College enrollment | [MgraDataManager] |
| *AdultSchEnrl* | Adult School enrollment | [MgraDataManager] |
| *ech_dist* | Elementary school district | [MgraDataManager] |
| *hch_dist* | High school district | [MgraDataManager] |
| **Parking** |||
| *parkarea* | {::nomarkdown}<ul><li>1: Trips with destinations in this MAZ may choose to park in a different MAZ, parking charges apply (downtown)</li> <li>2: Trips with destinations in parkarea 1 may choose to park in this MAZ, parking charges might apply (quarter mile buffer around downtown)</li> <li>3: Only trips with destinations in this MAZ may park here, parking charges apply (outside downtown paid parking, only show cost no capacity issue)</li> <li>4: Only trips with destinations in this MAZ may park here, parking charges do not apply (outside downtown, free parking)</li> </ul>{:/} | [MgraDataManager] |
| *hstallsoth* | Number of stalls allowing hourly parking for trips with destinations in other MAZs | [MgraDataManager] |
| *hstallssam* | Number of stalls allowing hourly parking for trips with destinations in the same MAZ | [MgraDataManager] |
| *hparkcost* | Average cost of parking for one hour in hourly stalls in this MAZ, dollars | [MgraDataManager] |
| *numfreehrs* | Number of hours of free parking allowed before parking charges begin in hourly stalls | [MgraDataManager] |
| *dstallsoth* | Stalls allowing daily parking for trips with destinations in other MAZs | [MgraDataManager] |
| *dstallssam* | Stalls allowing daily parking for trips with destinations in the same MAZ | [MgraDataManager] |
| *dparkcost* | Average cost of parking for one day in daily stalls, dollars | [MgraDataManager] |
| *mstallsoth* | Stalls allowing monthly parking for trips with destinations in other MAZs | [MgraDataManager] |
| *mstallssam* | Stalls allowing monthly parking for trips with destinations in the same MAZ | [MgraDataManager] |
| *mparkcost* | Average cost of parking for one day in monthly stalls, amortized over 22 workdays, dollars | [MgraDataManager] |
| **Other** |||
| *park_area* | Area of park space, in square meters | [Accessibilities] |
| **Calculated land use measures** |||
| *TotInt* | Total intersections | [MgraDataManager], [AutoOwnership] | [createMazDensityFile.py] |
| *DUDen* | Dwelling unit density | [MgraDataManager] | [createMazDensityFile.py] |
| *EmpDen* | Employment density | [MgraDataManager] | [createMazDensityFile.py] |
| *PopDen* | Population density | [AutoOwnership] | [createMazDensityFile.py] |
| *RetEmpDen* | Retail employment density | [AutoOwnership] | [createMazDensityFile.py] |
| *TotIntBin* | Total intersection bin | is this used? | [createMazDensityFile.py] |
| *EmpDenBin* | Employment density bin | [AtWorkSubtourFrequency] | [createMazDensityFile.py] |
| *DuDenBin* | Dwelling unit density bin | [AtWorkSubtourFrequency] | [createMazDensityFile.py] |


## Zonal Data

| *Field* | *Description* | *Used by* |
|---------|---------------|-----------|
| *TAZ_ORIGINAL* | Original TAZ number. It's original because these will get renumbered during the model run assuming [the node numbering conventions](#county-node-numbering-system)  |
| *AVGTTS* | Average travel time savings for transponder ownership model | [TazDataManager] |
| *DIST* | Distance for transponder ownership model | [TazDataManager] |
| *PCTDETOUR* | Percent detour for transponder ownership model | [TazDataManager] |
| *TERMINALTIME* | Terminal time | [TazDataManager] |

## Synthetic Population

The synethic population is generated by [popsyn3](https://github.com/BayAreaMetro/popsyn3) or [populationsim](https://github.com/BayAreaMetro/populationsim) (TBD).

### Households

| *Column Name* | *Description* | *Used by* |
|---------------|---------------|-----------|
| *HHID* | Unique household ID | [HouseholdDataManager] |
| *TAZ* | TAZ of residence | [HouseholdDataManager] |
| *MAZ* | MAZ of residence | [HouseholdDataManager] |
| *MTCCountyID* | County of residence | [HouseholdDataManager] |
| *HHINCADJ* | Household income in 2010 dollars | [HouseholdDataManager] |
| *NWRKRS_ESR* | Number of workers.  A count of *EMPLOYED* persons in the household, ranges from 0 to 20. | [HouseholdDataManager] |
| *VEH* | Number of vehicles owned by the household. From [PUMS], ranges from 0 (no vehicles) to 6 (6 or more vehicles), with N/A recoded as -9 for group quarters | [HouseholdDataManager] |
| *NP* | Number of persons in household. From [PUMS].  Ranges from 1 to 20 | [HouseholdDataManager] |
| *HHT* | Household type. From [PUMS]. {::nomarkdown}<br /> <ul><li>1=Married-couple family household</li><li>2=Other family household, Male householder, no wife present</li><li>3=Other family household, Female householder, no husband present</li><li>4=Nonfamily household, Male householder, Living alone</li><li>5=Nonfamily household, Male householder, Not living alone</li><li>6=Nonfamily household, Female householder, Living alone</li><li>7=Nonfamily household, Female householder, Not living alone</li><li>-9=N/A recoded for group quarters</li></ul>{:/} | [HouseholdDataManager] |
| *BLD* | Units in structure. From [PUMS]. {::nomarkdown}<br /> <ul><li>1=Mobile home or trailer</li><li>2=One-family house detached</li><li>3=One-family house attached</li><li>4=2 Apartments</li><li>5=3-4 Apartments</li><li>6=5-9 Apartments</li><li>7=10-19 Apartments</li><li>8=20-49 Apartments</li><li>9=50 or more apartments</li><li>10=Boat, RV, van, etc.</li><li>-9=N/A recoded for group quarters</li></ul>{:/} | [HouseholdDataManager] |
| *TYPE* | Type of unit (housing, institutional or noninstitutional group quarters). From [PUMS]. 1=Housing unit, 2=Institutional group quarters (shouldn't be included in this input data set), 3=Noninstitutional group quarters. | [HouseholdDataManager] |

### Persons

| *Column Name* | *Description* | *Used by* |
|---------------|---------------|-----------|
| *HHID* | Unique household ID | [HouseholdDataManager] |
| *PERID* | Unique person ID | [HouseholdDataManager] |
| *AGEP* | Age of person. From [PUMS], ranges from 0 to 99. | [HouseholdDataManager] |
| *SEX* | Sex of person. From [PUMS]. 1=Male, 2=Female | [HouseholdDataManager] |
| *SCHL* | Education attainment of person. From [PUMS]. {::nomarkdown}<br /> <ul><li>-9=N/A recoded for less than 3 years old</li><li>1=No schooling completed</li><li>2=Nursery school to grade 4</li><li>3=Grade 5 or grade 6</li><li>4=Grade 7 or grade 8</li><li>5=Grade 9</li><li>6=Grade 10</li><li>7=Grade 11</li><li>8=12th grade, no diploma</li><li>9=High school graduate</li><li>10=Some college, but less than 1 year</li><li>11=One or more years of college, no degree</li><li>12=Associate's degree</li><li>13=Bachelor's degree</li><li>14=Master's degree</li><li>15=Professional school degree</li><li>16=Doctorate degree</li><ul>{:/} | [HouseholdDataManager] |
| *OCCP* | Occupation, based on recoding of *SOCP00* or *SOCP10* from [PUMS]. Recoding done in [create_seed_population.py] {::nomarkdown}<br /> <ul><li>-999 is N/A recode (less than 16 years old/Not in labor force who last worked more than 5 years ago or never worked)</li><li>1=Management</li><li>2=Professional</li><li>3=Services</li><li>4=Retail</li><li>5=Manual</li><li>6=Military</li></ul>{:/} [HouseholdDataManager] |
| *WKHP* | Usual hours worked per week past 12 months. From [PUMS]. -9=N/A recoded for persons less than 16 years old or who did not work during the past 12 months. Otherwise ranges from 1 to 99. | [HouseholdDataManager] |
| *WKW* | Weeks worked during past 12 months. From [PUMS].  {::nomarkdown}<br /> <ul><li>-9=N/A recoded for persons less than 16 years old or who did not work during the past 12 months</li><li>1=50 to 52 weeks</li><li>2=48 to 49 weeks</li><li>3=40 to 47 weeks</li><li>4= 27 to 39 weeks</li><li>5=14 to 26 weeks</li><li>6=13 weeks or less</li></ul>{:/} | [HouseholdDataManager] |
| *EMPLOYED* | Based on *ESR* below. 1=Employed, set if *ESR* is one of [1,2,4,5]. 0=Unemployed. | [HouseholdDataManager] |
| *ESR* | Employment status recode. From [PUMS] {::nomarkdown}<br /> <ul><li>0=N/A recoded for persons less than 16 years old</li><li>1=Civilian employed, at work</li><li>2=Civilian employed, with a job but not at work</li><li>3=Unemployed</li><li>4=Armed forces, at work</li><li>5=Armed forces, with a job but not at work</li><li>6=Not in labor force</li></ul>{:/} | [HouseholdDataManager] |
| *SCHG* | Grade level attending. From [PUMS] {::nomarkdown}<br /> <ul><li>-9=N/A (not attending school) recoded</li><li>1=Nursery schoo./preschool</li><li>2=Kindergarten</li><li>3=Grade 1 to grade 4</li><li>4=Grade 5 to grade 8</li><li>5=Grade 9 to grade 12</li><li>6=College undergraduate</li><li>7=Graduate or professional school</li></ul>{:/} | [HouseholdDataManager] |



## Truck Distribution

MTC uses a simple three-step (generation, distribution, and assignment) commercial vehicle model to generate estimates of four types of commercial vehicles. The four vehicle types are very small (two-axle, four-tire), small (two-axle, six-tire), medium (three-axle), and large or combination trucks (four-or-more-axle).

### Friction Factors

The trip distribution step uses a standard gravity model with a blended travel time impedance measure. This file sets the friction factors, which are vehicle type specific, using an ASCII fixed format text file with the following data:

 * Travel time in minutes (integer, starting in column 1, left justified);
 * Friction factors for very small trucks (integer, starting in column 9, left justified);
 * Friction factors for small trucks (integer, starting in column 17, left justified);
 * Friction factors for medium trucks (integer, starting in column 25, left justified); and,
 * Friction factors for large trucks (integer, starting in column 33, left justified).

### K-Factors

The trip distribution step also uses a matrix of K-factors to adjust the distribution results to better match observed data. This matrix contains a unit-less adjustment value; the higher the number, the more attractive the production/attraction pair.

## Fixed Demand

MTC uses representations of internal/external and air passenger demand that is year-, but not scenario-, specific -- meaning simple sketch methods are used to estimate this demand from past trends. This demand is then fixed for each forecast year and does not respond to changes in land use or the transport network.

### Internal/External

So-called internal/external demand is travel that either begins or ends in the nine county Bay Area. This demand is based on Census journey-to-work data and captures all passenger (i.e. non-commercial) vehicle demand. This demand is introduced to the model via a matrix that contains the following four demand tables in production-attraction format:

 * Daily single-occupant vehicle flows;
 * Daily two-occupant vehicle flows;
 * Daily three-or-more occupant vehicle flows; and,
 * Daily vehicle flows, which is the sum of the first three tables and not used by the travel model.

### Air Passenger

Air passenger demand is based on surveys of air passenger and captures demand from the following travel modes: passenger vehicles, rental cars, taxis, limousines, shared ride vans, hotel shuttles, and charter buses. This demand is introduced to the model via Main.TimePeriods specific matrices that contain the following six flow tables:

 * Single-occupant vehicles;
 * Two-occupant vehicles;
 * Three-occupant vehicles;
 * Single-occupant vehicles that are willing to pay a high-occupancy toll lane fee;
 * Two-occupant vehicles that are willing to pay a high-occupancy toll lane fee; and,
 * Three-occupant vehicles that are willing to pay a high-occupancy toll lane fee.

[Accessibilities]: https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/model/Accessibilities.xls
[AtWorkSubtourFrequency]: https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/model/AtWorkSubtourFrequency.xls
[AutoOwnership]: https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/model/AutoOwnership.xls
[createMazDensityFile.py]: https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/scripts/preprocess/createMazDensityFile.py
[create_seed_population.py]: https://github.com/BayAreaMetro/populationsim/blob/master/bay_area/create_seed_population.py
[MgraDataManager]: https://github.com/BayAreaMetro/travel-model-two/blob/master/core/src/java/com/pb/mtctm2/abm/ctramp/MgraDataManager.java#L47
[NAICS]: https://www.census.gov/eos/www/naics/
[TazDataManager]: https://github.com/BayAreaMetro/travel-model-two/blob/master/core/src/java/com/pb/mtctm2/abm/ctramp/TazDataManager.java#L37
[TourModeChoice.xls]: https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/model/TourModeChoice.xls
[HouseholdDataManager]: https://github.com/BayAreaMetro/travel-model-two/blob/master/core/src/java/com/pb/mtctm2/abm/ctramp/HouseholdDataManager.java#L44
[PUMS]: https://www2.census.gov/programs-surveys/acs/tech_docs/pums/data_dict/PUMS_Data_Dictionary_2007-2011.pdf
