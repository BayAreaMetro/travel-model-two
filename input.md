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

The *all streets highway network* was developed from the [TomTom](http://www.tomtom.com/en_gb/licensing/) (previously TeleAtlas) North America routable network database.  The *projection* is [**NAD 1983 StatePlane California VI FIPS 0406 Feet**](https://epsg.io/102646).

The *bike network* was built from the highway network and the [MTC Bike Mapper](http://gis.mtc.ca.gov/btp/) network. The Bike Mapper network is a framework in which local cities update a master database of bicycle infrastructure and bicycle lane attributes, from which MTC has built and now maintains a trip planner application. 

The *walk network* was built from the highway network and the open source [Open Street Map](http://www.openstreetmap.org/) (OSM) network. 

### County Node Numbering System

The highway network uses a numbering system whereby each county has a reserved block of nodes. Within each county’s block, nodes 1 through 9,999 are reserved for TAZs, 10,001 through 89,999 are for MAZs, and 90,001 through 99,999 for transit access points or TAPs. The blocks are assigned to the nine counties per MTC’s numbering scheme, as shown in the table below.

TeleAtlas network nodes are numbered by county as well and range from 1,000,000 to 10,000,000 as shown below. HOV lane nodes are those nodes corresponding to general purpose lane nodes.   

Code  | County | TAZs | MAZs |  TAPs | Network Node | HOV Lane Node
|:---:|:-------|:-----|:-----|:------|:-------------|:-------------
1 | San Francisco |	1 - 9,999 |	10,001 – 89,999 |	90,001 – 99,999 |	1,000,000 – 1,500,000 |	5,500,000 – 6,000,000
2 |	San Mateo |	100,001 – 109,999 |	110,001 – 189,999 |	190,001 – 199,999 |	1,500,000 – 2,000,000 |	6,000,000 – 6,500,000
3 |	Santa Clara |	200,001 – 209,999 |	210,001 – 289,999 |	290,001 – 299,999 |	2,000,000 – 2,500,000 |	6,500,000 – 7,000,000
4 |	Alameda |	300,001 – 309,999 |	310,001 – 389,999 |	390,001 – 399,999 |	2,500,000 – 3,000,000 | 7,000,000 – 7,500,000
5 |	Contra Costa |	400,001 – 409,999 |	410,001 – 489,999 |	490,001 – 499,999 |	3,000,000 – 3,500,000 |	7,500,000 – 8,000,000
6 |	Solano |	500,001 – 509,999 |	510,001 – 589,999 |	590,001 – 599,999 |	3,500,000 – 4,000,000 |	8,000,000 – 8,500,000
7 |	Napa |	600,001 – 609,999 |	610,001 – 689,999 |	690,001 – 699,999 |	4,000,000 – 4,500,000 |	8,500,000 – 9,000,000
8 |	Sonoma |	700,001 – 709,999 |	710,001 – 789,999 |	790,001 – 799,999 |	4,500,000 – 5,000,000 |	9,000,000 – 9,000,000
9 |	Marin |	800,001 – 809,999 |	810,001 – 889,999 |	890,001 – 899,999 |	5,000,000 – 5,500,000 |	9,500,000 – 9,999,999 
  | External | 900,001 - 999,999

### Node Attributes

The following node attributes are included in the master network.

|*Field* | *Description* | *Data Type*
|--------|-------------|----------
|*N* | Node Number | Integer (see [Node Numbering](#county-node-numbering-system))
|*X* | X coordinate (feet) | Float
|*Y* | Y coordinate (feet) | Float
|*COUNTY* | County Code | Integer
|*MODE* | Best transit mode served. {::nomarkdown}<br /><ul><li>1: Local bus</li> <li>2: Express bus</li> <li>3: Ferry</li> <li>4: Light rail</li> <li>5: Heavy rail</li> <li>6: Commuter rail</li> </ul>{:/} Appears to be set for TAPs and nodes with **STOP** set.| Integer
|*STOP* | Transit stop or terminal name of the node | String
|*PNR_CAP* |  Number of parking spaces at the stop or terminal if a parking facility is available | Integer
|*PNR[1-5]* | Is parking available at the stop or terminal by time period? | Integer (1=available)
|*PNR_FEE[1-5]* | Parking fee at the stop by time period | Float
|*FAREZONE* | Unique sequential fare zone ID for transit skimming and assignment | Integer

### Link Attributes

The following link attributes are included on the master network.

| *Field* | *Description* | *Data Type* | *Source* |
|-------|---------------|-------------|----------|
| *A* | from node | Integer (see [Node Numbering](#county-node-numbering-system)) |
| *B* | to node | Integer (see [Node Numbering](#county-node-numbering-system)) |
| *F_JNCTID* | TomTom from node | Long integer | TomTom |
| *T_JNCTID* | TomTom to node | Long integer | TomTom |
| *FRC* | Functional Road Class{::nomarkdown}<br /> <ul><li>-1: Not Applicable</li> <li>0: Motorway, Freeway, or Other Major Road</li>  <li>1: a Major Road Less Important than a Motorway</li> <li>2: Other Major Road</li> <li>3: Secondary Road</li> <li>4: Local Connecting Road</li> <li>5: Local Road of High Importance</li> <li>6: Local Road</li> <li>7: Local Road of Minor Importance</li> <li>8: Other Road</li> </ul>{:/} | Float | TomTom |
| *NAME* | Road name | String | TomTom |
| *FREEWAY* | Freeway{::nomarkdown}<br /> <ul><li>0: No Part of Freeway (default)</li> <li>1: Part of Freeway</li> </ul>{:/} | Integer | TomTom |
| *TOLLRD* | Toll Road{::nomarkdown}<br /> <ul> <li>Blank: No Toll Road (default)</li> <li>B: Toll Road in Both Directions</li> <li>FT: Toll Road in Positive Direction</li> <li>TF: Toll Road in Negative Direction</li> </ul>{:/} | String | TomTom |
| *ONEWAY* |  Direction of Traffic Flow{::nomarkdown}<br /> <ul><li>Blank: Open in Both Directions (default)</li> <li>FT: Open in Positive Direction</li> <li>N: Closed in Both Directions</li> <li>TF: Open in Negative Direction</li></ul>{:/} | String | TomTom |
| *KPH* | Calculated Average Speed (kilometers per hour) | Integer | TomTom |
| *MINUTES* | Travel Time (minutes) | Integer | TomTom |
| *CARRIAGE* | Carriageway Type{::nomarkdown}<br /> <ul><li>Blank: Not Applicable</li> <li>1: Car Pool</li> <li>2: Express</li> <li>3: Local</li></ul>{:/} | Integer | TomTom |
| *LANES* | TomTom Number of lanes | Integer | TomTom |
| *RAMP* | Exit / Entrance Ramp{::nomarkdown}<br /> <ul><li>0: No Exit/Entrance Ramp - Default</li> <li>1: Exit</li> <li>2: Entrance</li></ul>{:/} | Integer | TomTom |
| *SPEEDCAT* | Speed Category{::nomarkdown}<br /><ul><li>1: &gt; 130 km/h</li> <li>2: 101 - 130 km/h</li> <li>3: 91 - 100 km/h</li> <li>4: 71 - 90 km/h</li> <li>5: 51 - 70 km/h</li> <li>6: 31 - 50 km/h</li> <li>7: 11 - 30 km/h</li><li>8: &lt; 11 km/h</li></ul>{:/} | Integer | TomTom |
| *FEET* | Calculated from TomTom Meters field | Integer | TomTom |
| *RTEDIR* | Route Directional{::nomarkdown}<br /><ul><li>Blank: Not Applicable (default)</li> <li>N: Northbound</li> <li>E: Eastbound</li> <li>S: Southbound</li> <li>O / W: Westbound</li></ul>{:/} | String | TomTom |
| *ASSIGNABLE* | Is link used for assignment (1=True, 0=False) | Integer |   |
| *CNTYPE* | Link connector type{::nomarkdown}<br /><ul> <li>BIKE - bike link</li> <li>CRAIL - commuter rail</li> <li>FERRY- ferry link</li> <li>HRAIL - heavy rail link</li> <li>LRAIL- light rail link</li> <li>MAZ - MAZ connector link</li> <li>PED - ped link</li> <li>TANA - regular network link</li> <li>TAP - TAP link</li> <li>TAZ - TAZ connector link</li> <li>USE - HOV (user class) link</li> </ul>{:/} | String |   |
| *TRANSIT* | Is Transit link | Integer |   |
| *USECLASS* | Link user class{::nomarkdown}<br /> <ul><li>0 - NA; link open to everyone</li> <li>2 - HOV 2+</li> <li>3 - HOV 3+</li> <li>4 - No combination trucks</li></ul>{:/} | Integer |   |
| *TOLLBOOTH* | Toll link.  Links with values [less than 11](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/block/hwyParam.block) are _bridge tolls_; 11 or above are _value tolls_. {::nomarkdown}<br /> <ul><li>1: Benicia-Martinez Bridge</li> <li>2: Carquinez Bridge</li> <li>3: Richmond Bridge</li> <li>4: Golden Gate Bridge</li> <li>5: San Francisco/Oakland Bay Bridge</li> <li>6: San Mateo Bridge</li> <li>7: Dumbarton Bridge</li> <li>8: Antioch Bridge</li> <li>25: I-680 Sunol Express Lanes</li> <li>28: I-580 Express Lanes EB</li> <li>29: I-580 Express Lanes WB</li> <li>31: SR-237 Express Lanes SB</li> <li>32: SR-237 Express Lanes NB</li> <li>33: I-680 Contra Costa Express Lanes SB</li> <li>34: I-680 Contra Costa Express Lanes NB</li></ul>{:/} | Integer |   |
| *TOLLSEG* | Toll segments{::nomarkdown}<br /> <ul></ul> <li>For I-680 Sunol Express Lanes SB (TOLLBOOTH=25): <ul><li>1: Andrade Rd to Washington Blvd</li> <li>2: Washington Blvd to Mission Blvd</li> <li>3: Mission Blvd to SR 237</li></ul></li> <li>I-580 Express Lanes EB (TOLLBOOTH=28): <ul><li>1: Hacienda Dr to Airway Blvd</li> <li>2: Airway Blvd to Livermore Ave</li> <li>3: Livermore Ave to Vasco Rd</li> <li>4: Vasco Rd to Greenville Rd	</li></ul>  <li>I-580 Express Lanes WB (TOLLBOOTH=29): <ul><li>1: Greenville Rd to Springtown Blvd</li> <li>2: Springtown to Isabel Ave</li> <li>3: Isabel Ave to Fallon Rd</li> <li>4: Fallon Rd to Hacienda Dr	</li> <li>5: Hacienda Dr to San Ramon Rd</li></ul> <ul></ul> <li>SR-237 Express Lanes SB (TOLLBOOTH=31): <ul><li>1: Dixon Landing Rd to N First Ave (Westbound)</li></ul>  <ul></ul> <li>SR-237 Express Lanes NB (TOLLBOOTH=32): <ul><li>1: N First Ave to Dixon Landing Rd (Eastbound)</li></ul> <ul></ul> <li>I-680 Contra Costa Express Lanes SB (TOLLBOOTH=33): <ul><li>1: Rudgear to Crow Canyon (Crow Canyon SB pricing zone)</li> <li>2: Crow Canyon to Alcosta (Alcosta pricing zone)</li></ul>   <ul></ul> <li>I-680 Contra Costa Express Lanes NB (TOLLBOOTH=34): <ul><li>1: Alcosta to Crow Canyon (Crow Canyon NB pricing zone)</li> <li>2: Crow Canyon to Livorna (Livorna pricing zone)</li> {:/} | Integer |   |
| *FT* | Facility type{::nomarkdown}<br /> <ul><li>0: Connector</li> <li>1: Freeway to Freeway</li> <li>2: Freeway</li> <li>3:  Expressway</li> <li>4: Collector</li> <li>5: Ramp</li> <li>6: Special Facility</li> <li>7: Major Arterial</li></ul>{:/} | Integer |   |
| *FFS* | Free flow speed calculated from TomTom KPH | Integer |   |
| *NUMLANES* | Model number of lanes | Integer |   |
| *HIGHWAYT* | Highway type{::nomarkdown}<br /> <ul> <li>footway</li> <li>footway_unconstructed</li> <li>pedestrian</li> <li>steps</li> </ul>{:/} | String | Open Street Map |
| *B_CLASS* | Bike Class{::nomarkdown}<br /> <ul><li>0 - Unclassified Street</li> <li>1 - Class I Trail</li> <li>2 - Class II Route</li> <li>3 - Class III Route</li></ul>{:/} | Integer | BikeMapper |
| *REPRIORITIZE* | Priority{::nomarkdown}<br/> <ul><li>2 - Highly Desirable</li> <li>1 - Desirable</li> <li>0 - No Preference</li> <li>-1 - Undesirable</li> <li>-2 - Highly Undesirable</li></ul>{:/} | Integer | BikeMapper |
| *GRADE_CAT* | Grade class{::nomarkdown}<br /> <ul><li>4 - 18% or High Grade</li> <li>3 - 10-18% Grade</li> <li>2 - 5-10% Grade</li> <li>1 - 0-5% Grade</li></ul>{:/} | Integer | BikeMapper |
| *PED_FLAG* | Pedestrian access (Y=yes; blank=no) | String | BikeMapper |
| *BIKEPEDOK* | Bridge that allows bike and peds (1=true, 0=false) | Integer | BikeMapper |
| *PEMSID* | PEMS ID | Integer | PEMS |
| *PEMSLANES* | PEMS number of lanes | Integer | PEMS |
| *PEMSDIST* | Distance from link to PEMS station | Float | PEMS |
| *TAP_DRIVE* | TAP link to parking lot (1=true) | Int | MTC |

## Transit Network

The transit network is made up of three core components: transit lines, transit modes, and transit fares.  The transit lines were built from MTC’s regional transit database (or RTD).  The lines are coded with a mode (see below) and serve a series of stop nodes.  Transit fares are coded according to Cube's Public Transport program (see below).

Transit trips are assigned between transit access points (TAPs), which represent individual or collections of transit stops for transit access/egress.  TAPs are essentially transit specific TAZs that are automatically coded based on the transit network.  See the [Level of Service Information](#level-of-service-information). 

### Line Attributes

| *Field* | *Description* | *Data Type* |
|---------|---------------|-------------|
| *NAME* | RTD CPT_AGENCYID and SCH_ROUTEDESIGNATOR | String |
| *USERA1* | Transit operator | String |
| *USERA2* | Line haul mode, one of {::nomarkdown}<br/><ul><li>`Local bus`</li> <li>`Express bus`</li> <li>`Ferry service`</li> <li>`Light rail`</li> <li>`Heavy rail`</li> <li>`Commuter rail`</li></ul>{:/} | String |
| *MODE* | Mode code | Integer |
| *FARESYSTEM* | Faresystem code. Not necessary if *MODE* corresponds to *FARESYSTEM* in the factors file. | Integer |
| *OPERATOR* | Operator code | Integer |
| *ONEWAY* | set to TRUE since each route is coded by direction | Character |
| *XYSPEED* | set to 15 by default (not used) | Integer |
| *HEADWAY[1]* | early AM headway (3AM to 6AM) | Float |
| *HEADWAY[2]* | AM peak headway (6AM to 10AM) | Float |
| *HEADWAY[3]* | Midday headway (10AM to 3PM) | Float |
| *HEADWAY[4]* | PM peak headway (3PM to 7PM) | Float |
| *HEADWAY[5]* | Evening headway (7PM to 3AM) | Float |
| *N* | List of stops served.  Lines are coded through stops, not TAPs (which are like transit TAZs).  A negative stop is not served. | List of Integers |

### Transit Modes

The following transit modes are defined based on the [Open511](https://511.org/developers/list/apis/) attributes (but not completely, since they came from the GTFS database predecessor, the Regional Transit Database).  These modes represent combinations of operators and technology. 

| *Operator/Agency ID* | *Agency Name* | *Mode* | *Mode Group* | *Farezones* |
|----------------------|---------------|--------|--------------|-------------|
| 3D | TriDelta Transit | 44 | Local bus | |
| AB | AirBART | 40 | Local bus | |
| AC | AC Transit | 30 | Local bus | |
| AD | AC Transbay | 84 | Express Bus | 1-5 |
| AM | Amtrak Capitol Cor. & Reg. Svc | 131 | Commuter rail | 25-36 |
| AO | Alameda/Oakland Ferry | 100 | Ferry service | 120-121, 123-124 |
| AT | Angel Island - Tiburon Ferry | 103 | Ferry service | 130-132 |
| AY | American Canyon Transit | 55 | Local bus | |
| BA | BART | 120 | Heavy rail | 40-85 |
| BG | Blue and Gold | 103 | Ferry service | 128-132 |
| BT | Benicia Transit | 58 | Local bus | |
| CC | The County Connection | 86 | Express Bus | |
| CC | The County Connection | 42 | Local bus | |
| CE | ACE | 133 | Commuter rail | 20-22 |
| CT | Caltrain | 130 | Commuter rail | 105-110 |
| DE | Dumbarton Express | 82 | Express Bus | 2, 4 |
| EM | Emery Go-Round | 12 | Local bus | |
| FS | Fairfield-Suisun Transit | 92 | Express Bus | 5, 150-152, 154 |
| FS | Fairfield-Suisun Transit | 52 | Local bus | |
| GF | Golden Gate Ferry | 101 | Ferry service | 115-117 |
| GG | Golden Gate Transit | 87 | Express Bus | 1, 5, 12-16, 201, 204 |
| GG | Golden Gate Transit | 70 | Local bus | 1, 5, 12-16, 201, 204 |
| HB | Alameda Harbor Bay Ferry | 100 | Ferry service | 122-124 |
| MA | [Marin Transit](https://marintransit.org/) | 70 | Local bus | |
| MS | Stanford Marguerite Shuttle | 13 | Local bus | |
| PE | Petaluma Transit | 68 | Local bus | |
| RV | Rio Vista Delta Breeze | 52 | Local bus | 150, 170 |
| SA | [Sonoma Marin Area Rail Transit (SMART)](https://sonomamarintrain.org/) | 134 | Commuter rail | 97-101 |
| SC | Santa Clara VTA | 81 | Express Bus | |
| SC | Santa Clara VTA | 28 | Local bus | |
| SC | Santa Clara VTA | 111 | Light rail | |
| SF | San Francisco MUNI | 21 | Local bus | |
| SF | San Francisco MUNI | 110 | Light rail | |
| SF | San Francisco MUNI | 20 | Local bus | |
| SM | SamTrans | 80 | Express Bus | |
| SM | SamTrans | 24 | Local bus | 1-3 |
| SO | Sonoma County Transit | 63 | Local bus | 201-208 |
| SR | Santa Rosa CityBus | 66 | Local bus | |
| SV | St. Helena VINE | 60 | Local bus | |
| UC | [Union City Transit](https://www.unioncity.org/170/Union-City-Transit) | 38 | Local bus | |
| VB | [Vallejo Baylink Ferry](https://www.vallejobayferry.com/) | 93 | Express bus | |
| VB | [Vallejo Baylink Ferry](https://www.vallejobayferry.com/) | 104 | Ferry service | 125-127 |
| VC | Vacaville City Coach | 56 | Local bus | |
| VN | [Napa VINE](http://www.ridethevine.com/vine) | 60 | Local bus | 5, 160-161 |
| VT | Vallejo Transit | 91 | Express Bus | |
| VT | Vallejo Transit | 49 | Local bus | |
| WC | [WestCAT](https://www.westcat.org/) | 90 | Express Bus | |
| WC | [WestCAT](https://www.westcat.org/) | 46 | Local bus | |
| WH | [Livermore Amador Valley Transit Authority (LAVTA)](https://www.wheelsbus.com/) | 17 | Local bus | |
| YV | Yountville Shuttle | 60 | Local bus | |

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
| *NWRKRS_ESR* | Number of workers | [HouseholdDataManager] |
| *VEH* | Number of vehicles owned by the household. From [PUMS] | [HouseholdDataManager] |
| *NP* | Number of persons in household. From [PUMS] | [HouseholdDataManager] |
| *HHT* | Household type. From [PUMS] | [HouseholdDataManager] |
| *BLD* | Units in structure. From [PUMS] | [HouseholdDataManager] |
| *TYPE* | Type of unit (housing, institutional or noninstitutional group quarters). From [PUMS] | [HouseholdDataManager] |

### Persons

| *Column Name* | *Description* | *Used by* |
|---------------|---------------|-----------|
| *HHID* | Unique household ID | [HouseholdDataManager] |
| *PERID* | Unique person ID | [HouseholdDataManager] |
| *AGEP* | Age of person. From [PUMS] | [HouseholdDataManager] |
| *SEX* | Sex of person. From [PUMS] | [HouseholdDataManager] |
| *SCHL* | Education attainment of person. From [PUMS] | [HouseholdDataManager] |
| *OCCP* | Occupation. [?] | [HouseholdDataManager] |
| *WKHP* | Usual hours worked per week past 12 months. From [PUMS] | [HouseholdDataManager] |
| *WKW* | Weeks worked during past 12 months. From [PUMS] | [HouseholdDataManager] |
| *EMPLOYED* | TBD. | [HouseholdDataManager] |
| *ESR* | Employment status recode. From [PUMS] | [HouseholdDataManager] |
| *SCHG* | Grade level attending. From [PUMS] | [HouseholdDataManager] |



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
[MgraDataManager]: https://github.com/BayAreaMetro/travel-model-two/blob/master/core/src/java/com/pb/mtctm2/abm/ctramp/MgraDataManager.java#L47
[NAICS]: https://www.census.gov/eos/www/naics/
[TazDataManager]: https://github.com/BayAreaMetro/travel-model-two/blob/master/core/src/java/com/pb/mtctm2/abm/ctramp/TazDataManager.java#L37
[TourModeChoice.xls]: https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/model/TourModeChoice.xls
[HouseholdDataManager]: https://github.com/BayAreaMetro/travel-model-two/blob/master/core/src/java/com/pb/mtctm2/abm/ctramp/HouseholdDataManager.java#L44
[PUMS]: https://www2.census.gov/programs-surveys/acs/tech_docs/pums/data_dict/PUMS_Data_Dictionary_2007-2011.pdf
