---
layout: page
title: Input
---

# Input Files

---
CONTENTS

1. [Roadway Network](#roadway-network)
2. [Transit Network](#transit-network)
2. [Micro Zonal Data](#micro-zonal-data)
3. [Zonal Data](#zonal-data)
4. [Fixed Demand](#fixed-demand)

---

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

## Roadway Network

The *all streets highway network* was developed from the [TomTom](http://www.tomtom.com/en_gb/licensing/) (previously TeleAtlas) North America routable network database.  The *projection* is NAD83 California State Plane FIPS VI.

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
|:---:|-------------|----------
|**N** | Node Number | Integer (see [Node Numbering](#county-node-numbering-system))
|**X** | X coordinate (feet) | Float
|**Y** | Y coordinate (feet) | Float
|**COUNTY** | County Code | Integer
|**MODE** | Best transit mode served. {::nomarkdown}<br /><ul><li>1: Local bus</li> <li>2: Express bus</li> <li>3: Ferry</li> <li>4: Light rail</li> <li>5: Heavy rail</li> <li>6: Commuter rail</li> </ul>{:/} Appears to be set for TAPs and nodes with **STOP** set.| Integer
|**STOP** | Transit stop or terminal name of the node | String
|**PNR_CAP** |  Number of parking spaces at the stop or terminal if a parking facility is available | Integer
|**PNR&lt;TimePeriod&gt;** | Is parking available at the stop or terminal by time period? | Integer (1=available)
|**PNR_Fee&lt;Timeperiod&gt;** | Parking fee at the stop by time period | Float
|**FAREZONE** | Unique sequential fare zone ID for transit skimming and assignment | Integer

### Link Attributes

The following link attributes are included on the master network.

| *Field* | *Description* | *Data Type* | *Source* |
|:-------:|---------------|-------------|----------|
| **A** | from node | Integer (see [Node Numbering](#county-node-numbering-system)) |
| **B** | to node | Integer (see [Node Numbering](#county-node-numbering-system)) |
| **F_JNCTID** | TomTom from node | Long integer | TomTom |
| **T_JNCTID** | TomTom to node | Long integer | TomTom |
| **FRC** | Functional Road Class<br /> <ul><li>-1: Not Applicable</li> <li>0: Motorway, Freeway, or Other Major Road</li>  <li>1: a Major Road Less Important than a Motorway</li> <li>2: Other Major Road</li> <li>3: Secondary Road</li> <li>4: Local Connecting Road</li> <li>5: Local Road of High Importance</li> <li>6: Local Road</li> <li>7: Local Road of Minor Importance</li> <li>8: Other Road</li> </ul> | Float | TomTom |
| **NAME** | Road name | String | TomTom |
| **FREEWAY** | Freeway<br /> <ul><li>0: No Part of Freeway (default)</li> <li>1: Part of Freeway</li> </ul> | Integer | TomTom |
| **TOLLRD** | Toll Road<br /> <ul> <li>Blank: No Toll Road (default)</li> <li>B: Toll Road in Both Directions</li> <li>FT: Toll Road in Positive Direction</li> <li>TF: Toll Road in Negative Direction</li> </ul> | String | TomTom |
| **ONEWAY** |  Direction of Traffic Flow<br /> <ul><li>Blank: Open in Both Directions (default)</li> <li>FT: Open in Positive Direction</li> <li>N: Closed in Both Directions</li> <li>TF: Open in Negative Direction</li></ul> | String | TomTom |
| **KPH** | Calculated Average Speed (kilometers per hour) | Integer | TomTom |
| **MINUTES** | Travel Time (minutes) | Integer | TomTom |
| **CARRIAGE** | Carriageway Type<br /> <ul><li>Blank: Not Applicable</li> <li>1: Car Pool</li> <li>2: Express</li> <li>3: Local</li></ul> | Integer | TomTom |
| **LANES** | TomTom Number of lanes | Integer | TomTom |
| **RAMP** | Exit / Entrance Ramp<br /> <ul><li>0: No Exit/Entrance Ramp - Default</li> <li>1: Exit</li> <li>2: Entrance</li></ul> | Integer | TomTom |
| **SPEEDCAT** | Speed Category<br /><ul><li>1: &gt; 130 km/h</li> <li>2: 101 - 130 km/h</li> <li>3: 91 - 100 km/h</li> <li>4: 71 - 90 km/h</li> <li>5: 51 - 70 km/h</li> <li>6: 31 - 50 km/h</li> <li>7: 11 - 30 km/h</li><li>8: &lt; 11 km/h</li></ul> | Integer | TomTom |
| **FEET** | Calculated from TomTom Meters field | Integer | TomTom |
| **RTEDIR** | Route Directional<br /><ul><li>Blank: Not Applicable (default)</li> <li>N: Northbound</li> <li>E: Eastbound</li> <li>S: Southbound</li> <li>O / W: Westbound</li></ul> | String | TomTom |
| **ASSIGNABLE** | Is link used for assignment (1=True, 0=False) | Integer |   |
| **CNTYPE** | Link connector type<br /><ul> <li>BIKE - bike link</li> <li>CRAIL - commuter rail</li> <li>FERRY- ferry link</li> <li>HRAIL - heavy rail link</li> <li>LRAIL- light rail link</li> <li>MAZ - MAZ connector link</li> <li>PED - ped link</li> <li>TANA - regular network link</li> <li>TAP - TAP link</li> <li>TAZ - TAZ connector link</li> <li>USE - HOV (user class) link</li> </ul> | String |   |
| **TRANSIT** | Is Transit link | Integer |   |
| **USECLASS** | Link user class<br /> <ul><li>0 - NA; link open to everyone</li> <li>2 - HOV 2+</li> <li>3 - HOV 3+</li> <li>4 - No combination trucks</li></ul> | Integer |   |
| **TOLLBOOTH** | Toll link.  Links with values [less than 11](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/block/hwyParam.block) are _bridge tolls_; 11 or above are _value tolls_. <br /> <ul><li>1: Benicia-Martinez Bridge</li> <li>2: Carquinez Bridge</li> <li>3: Richmond Bridge</li> <li>4: Golden Gate Bridge</li> <li>5: San Francisco/Oakland Bay Bridge</li> <li>6: San Mateo Bridge</li> <li>7: Dumbarton Bridge</li> <li>8: Antioch Bridge</li> <li>12: I-680 express lane</li></ul> | Integer |   |
| **FT** | Facility type<br /> <ul><li>0: Connector</li> <li>1: Freeway to Freeway</li> <li>2: Freeway</li> <li>3:  Expressway</li> <li>4: Collector</li> <li>5: Ramp</li> <li>6: Special Facility</li> <li>7: Major Arterial</li></ul> | Integer |   |
| **FFS** | Free flow speed calculated from TomTom KPH | Integer |   |
| **NUMLANES** | Model number of lanes | Integer |   |
| **HIGHWAYT** | Highway type<br /> <ul> <li>footway</li> <li>footway_unconstructed</li> <li>pedestrian</li> <li>steps</li> </ul> | String | Open Street Map |
| **B_CLASS** | Bike Class<br /> <ul><li>0 - Unclassified Street</li> <li>1 - Class I Trail</li> <li>2 - Class II Route</li> <li>3 - Class III Route</li></ul> | Integer | BikeMapper |
| **REPRIORITIZE** | Priority<br/> <ul><li>2 - Highly Desirable</li> <li>1 - Desirable</li> <li>0 - No Preference</li> <li>-1 - Undesirable</li> <li>-2 - Highly Undesirable</li></ul> | Integer | BikeMapper |
| **GRADE_CAT** | Grade class<br /> <ul><li>4 - 18% or High Grade</li> <li>3 - 10-18% Grade</li> <li>2 - 5-10% Grade</li> <li>1 - 0-5% Grade</li></ul> | Integer | BikeMapper |
| **PED_FLAG** | Pedestrian access (Y=yes; blank=no) | String | BikeMapper |
| **BIKEPEDOK** | Bridge that allows bike and peds (1=true, 0=false) | Integer | BikeMapper |
| **PEMSID** | PEMS ID | Integer | PEMS |
| **PEMSLANES** | PEMS number of lanes | Integer | PEMS |
| **PEMSDIST** | Distance from link to PEMS station | Float | PEMS |
| **TAP_DRIVE** | TAP link to parking lot (1=true) | Int | MTC |

## Transit Network

The transit network is made up of three core components: transit lines, transit modes, and transit fares.  The transit lines were built from MTC’s regional transit database (or RTD).  The lines are coded with a mode (see below) and serve a series of stop nodes.  Transit fares are coded according to Cube's Public Transport program (see below).

Transit trips are assigned between transit access points (TAPs), which represent individual or collections of transit stops for transit access/egress.  TAPs are essentially transit specific TAZs that are automatically coded based on the transit network.  See the [Level of Service Information](#level-of-service-information). 

### Line Attributes

| *Field* | *Description* | *Data Type* |
|:-------:|---------------|-------------|
| **NAME** | RTD CPT_AGENCYID and SCH_ROUTEDESIGNATOR | String |
| **USERA1** | Transit operator | String |
| **USERA2** | Line haul mode, one of <ul> <li>Local bus (LB)</li> <li>Express Bus (EB)</li> <li>Ferry service (FY)</li> <li>Light rail (LR)</li> <li>Heavy rail (HR)</li> <li>Commuter rail (CR)</li> </ul> | String |
| **MODE** | Mode code | Integer |
| **ONEWAY** | set to TRUE since each route is coded by direction | Character |
| **XYSPEED** | set to 15 by default (not used) | Integer |
| **HEADWAY[1]** | early AM headway (3AM to 6AM) | Float |
| **HEADWAY[2]** | AM peak headway (6AM to 10AM) | Float |
| **HEADWAY[3]** | Midday headway (10AM to 3PM) | Float |
| **HEADWAY[4]** | PM peak headway (3PM to 7PM) | Float |
| **HEADWAY[5]** | Evening headway (7PM to 3AM) | Float |
| **N** | List of stops served.  Lines are coded through stops, not TAPs (which are like transit TAZs).  A negative stop is not served. | List of Integers |

### Transit Modes

The following transit modes are defined based on the RTD database attributes `CPT_AGENCYID`, `CPT_MODE`, and `SCH_ROUTEDESIGNATOR`.  These modes represent combinations of operators and technology. 

| *CPT_AGENCYID* | *AGENCYNAME* | *CPT_MODE* | *SCH_ROUTEDESIGNATOR* | *MODECODE* | *MODEGROUP* |
|----------------|--------------|------------|-----------------------|------------|-------------|
| 3D | TriDelta Transit | B | NA | 44 | Local bus |
| AB | AirBART | B | NA | 40 | Local bus |
| AC | AC Transit | B | NA | 30 | Local bus |
| AD | AC Transbay | B | NA | 84 | Express Bus |
| AM | Amtrak Capitol Cor. & Reg. Svc | T | NA | 131 | Commuter rail |
| AO | Alameda/Oakland Ferry | F | NA | 100 | Ferry service |
| AT | Angel Island - Tiburon Ferry | F | NA | 103 | Ferry service |
| AY | American Canyon Transit | B | NA | 55 | Local bus |
| BA | BART | T | NA | 120 | Heavy rail |
| BG | Blue and Gold | F | NA | 103 | Ferry service |
| BT | Benicia Transit | B | NA | 58 | Local bus |
| CC | The County Connection | B | 91X | 86 | Express Bus |
| CC | The County Connection | B | 92X | 86 | Express Bus |
| CC | The County Connection | B | 93X | 86 | Express Bus |
| CC | The County Connection | B | 95X | 86 | Express Bus |
| CC | The County Connection | B | 96X | 86 | Express Bus |
| CC | The County Connection | B | 97X | 86 | Express Bus |
| CC | The County Connection | B | 98X | 86 | Express Bus |
| CC | The County Connection | B | NA | 42 | Local bus |
| CE | ACE | T | NA | 133 | Commuter rail |
| CT | Caltrain | T | NA | 130 | Commuter rail |
| DE | Dumbarton Express | B | NA | 82 | Express Bus |
| EM | Emery Go-Round | B | NA | 12 | Local bus |
| FS | Fairfield-Suisun Transit | B | 40 | 92 | Express Bus |
| FS | Fairfield-Suisun Transit | B | NA | 52 | Local bus |
| GF | Golden Gate Ferry | F | NA | 101 | Ferry service |
| GG | Golden Gate Transit | B | 22 | 87 | Express Bus |
| GG | Golden Gate Transit | B | 23 | 87 | Express Bus |
| GG | Golden Gate Transit | B | 29 | 87 | Express Bus |
| GG | Golden Gate Transit | B | 35 | 87 | Express Bus |
| GG | Golden Gate Transit | B | 36 | 87 | Express Bus |
| GG | Golden Gate Transit | B | 71 | 88 | Express Bus |
| GG | Golden Gate Transit | B | NA | 70 | Local bus |
| HB | Alameda Harbor Bay Ferry | F | NA | 100 | Ferry service |
| MS | Stanford Marguerite Shuttle | B | NA | 13 | Local bus |
| PE | Petaluma Transit | B | NA | 68 | Local bus |
| RV | Rio Vista Delta Breeze | B | NA | 52 | Local bus |
| SC | Santa Clara VTA | B | 101 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 102 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 103 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 104 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 120 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 121 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 122 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 140 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 168 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 180 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 181 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 182 | 81 | Express Bus |
| SC | Santa Clara VTA | B | NA | 28 | Local bus |
| SC | Santa Clara VTA | LR | NA | 111 | Light rail |
| SF | San Francisco MUNI | B | NA | 21 | Local bus |
| SF | San Francisco MUNI | LR | NA | 110 | Light rail |
| SF | San Francisco MUNI | CC | NA | 20 | Local bus |
| SM | samTrans | B | KX | 80 | Express Bus |
| SM | samTrans | B | NA | 24 | Local bus |
| SO | Sonoma County Transit | B | NA | 63 | Local bus |
| SR | Santa Rosa CityBus | B | NA | 66 | Local bus |
| SV | St. Helena VINE | B | NA | 60 | Local bus |
| UC | Union City Transit | B | NA | 38 | Local bus |
| VB | Vallejo Baylink Ferry | B | NA | 93 | Express bus |
| VB | Vallejo Baylink Ferry | F | NA | 104 | Ferry service |
| VC | Vacaville City Coach | B | NA | 56 | Local bus |
| VN | Napa VINE | B | NA | 60 | Local bus |
| VT | Vallejo Transit | B | 80 | 91 | Express Bus |
| VT | Vallejo Transit | B | 85 | 91 | Express Bus |
| VT | Vallejo Transit | B | NA | 49 | Local bus |
| WC | WestCAT | B | JL | 90 | Express Bus |
| WC | WestCAT | B | JPX | 90 | Express Bus |
| WC | WestCAT | B | JR | 90 | Express Bus |
| WC | WestCAT | B | JX | 90 | Express Bus |
| WC | WestCAT | B | LYNX | 90 | Express Bus |
| WC | WestCAT | B | NA | 46 | Local bus |
| WH | WHEELS | B | NA | 17 | Local bus |
| YV | Yountville Shuttle | B | NA | 60 | Local bus |

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

| *Column Name* | *Description* |
|:-------------:|---------------|
| **MAZ_ORIGINAL** | Original micro zone number. It's original because these will get renumbered during the model run assuming [the node numbering conventions](#county-node-numbering-system) |
| **TAZ_ORIGINAL** | Original TAZ number. It's original because these will get renumbered during the model run assuming [the node numbering conventions](#county-node-numbering-system)  |
| **hh** | Total number of households |
| **pop** | Total population |
| **emp_self** | Self-employed |
| **emp_ag** | Agriculture employment |
| **emp_const_non_bldg_prod** | Construction Non-Building production (including mining) employment |
| **emp_const_non_bldg_office** | Construction Non-Building office support (including mining) employment |
| **emp_utilities_prod** | Utilities production employment |
| **emp_utilities_office** | Utilities office support employment |
| **emp_const_bldg_prod** | Construction of Buildings production employment |
| **emp_const_bldg_office** | Construction of Buildings office support employment |
| **emp_mfg_prod** | Manufacturing production employment |
| **emp_mfg_office** | Manufacturing office support employment |
| **emp_whsle_whs** | Wholesale and Warehousing employment |
| **emp_trans** | Transportation Activity employment |
| **emp_retail** | Retail Activity employment |
| **emp_prof_bus_svcs** | Professional and Business Services employment |
| **emp_prof_bus_svcs_bldg_maint** | Professional and Business Services (Building Maintenance) employment |
| **emp_pvt_ed_k12** | Private Education K-12 employment |
| **emp_pvt_ed_post_k12_oth** | Private Education Post-Secondary (Post K-12) and Other employment |
| **emp_health** | Health Services employment |
| **emp_personal_svcs_office** | Personal Services Office Based employment |
| **emp_amusement** | Amusement Services employment |
| **emp_hotel** | Hotels and Motels employment |
| **emp_restaurant_bar** | Restaurants and Bars employment |
| **emp_personal_svcs_retail** | Personal Services Retail Based employment |
| **emp_religious** | Religious Activity employment |
| **emp_pvt_hh** | Private Households employment |
| **emp_state_local_gov_ent** | State and Local Government Enterprises Activity employment |
| **emp_scrap_other** | Scrap other employment |
| **emp_fed_non_mil** | Federal Non-Military Activity employment |
| **emp_fed_mil** | Federal Military Activity employment |
| **emp_state_local_gov_blue** | State and Local Government Non-Education Activity production employment |
| **emp_state_local_gov_white** | State and Local Government Non-Education Activity office support employment |
| **emp_public_ed** | Public Education K-12 and other employment |
| **emp_own_occ_dwell_mgmt** | Owner-Occupied Dwellings Management and Maintenance Activity employment |
| **emp_fed_gov_accts** | Federal Government Accounts employment |
| **emp_st_lcl_gov_accts** | State and Local Government Accounts employment |
| **emp_cap_accts** | Capital Accounts employment |
| **emp_total** | Total employment |
| **EnrollGradeKto8** | Grade School K-8 enrollment |
| **EnrollGrade9to12** | Grade School 9-12 enrollment |
| **collegeEnroll** | Major College enrollment |
| **otherCollegeEnroll** | Other College enrollment |
| **AdultSchEnrl** | Adult School enrollment |
| **ech_dist** | Elementary school district |
| **hch_dist** | High school district |
| **parkarea** | <ul><li>1: Trips with destinations in this MAZ may choose to park in a different MAZ, parking charges apply (downtown)</li> <li>2: Trips with destinations in parkarea 1 may choose to park in this MAZ, parking charges might apply (quarter mile buffer around downtown)</li> <li>3: Only trips with destinations in this MAZ may park here, parking charges apply (outside downtown paid parking, only show cost no capacity issue)</li> <li>4: Only trips with destinations in this MAZ may park here, parking charges do not apply (outside downtown, free parking)</li> </ul> |
| **hstallsoth** | Number of stalls allowing hourly parking for trips with destinations in other MAZs |
| **hstallssam** | Number of stalls allowing hourly parking for trips with destinations in the same MAZ |
| **hparkcost** | Average cost of parking for one hour in hourly stalls in this MAZ, dollars |
| **numfreehrs** | Number of hours of free parking allowed before parking charges begin in hourly stalls |
| **dstallsoth** | Stalls allowing daily parking for trips with destinations in other MAZs |
| **dstallssam** | Stalls allowing daily parking for trips with destinations in the same MAZ |
| **dparkcost** | Average cost of parking for one day in daily stalls, dollars |
| **mstallsoth** | Stalls allowing monthly parking for trips with destinations in other MAZs |
| **mstallssam** | Stalls allowing monthly parking for trips with destinations in the same MAZ |
| **mparkcost** | Average cost of parking for one day in monthly stalls, amortized over 22 workdays, dollars |
| **TotInt** | Total intersections |
| **DUDen** | Dwelling unit density |
| **EmpDen** | Employment density |
| **PopDen** | Population density |
| **RetEmpDen** | Retail employment density |
| **TotIntBin** | Total intersection bin |
| **EmpDenBin** | Employment density bin |
| **DuDenBin** | Dwelling unit density bin |
| **ACRES** | MAZ acres |

## Zonal Data

| *Field* | *Description* |
|:-------:|---------------|
| **TAZ_ORIGINAL** | Original TAZ number. It's original because these will get renumbered during the model run assuming [the node numbering conventions](#county-node-numbering-system)  |
| **AVGTTS** | Average travel time savings for transponder ownership model |
| **DIST** | Distance for transponder ownership model |
| **PCTDETOUR** | Percent detour for transponder ownership model |
| **TERMINALTIME** | Terminal time |

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

### Internal/external

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
