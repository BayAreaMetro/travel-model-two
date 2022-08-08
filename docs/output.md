# Outputs
Most outputs are stored within the *project directory* under "ctramp_output", "skims", "trn", and "other" folders, each with its respective files.  

## Skims

TM2 produces multiple types of network LOS indicators, often called skim matrices. The following skims are output and generated for each of the five time periods.  

### Highway Skim Matrices - skims\HWYSKM[TimePeriod]_taz.tpp

| Skim Name | Description |
|-----------|-------------|
| TIME[DA,S2,S3] | No value toll path, travel time (minutes) |
| DIST[DA,S2,S3] | No value toll path, distance (miles) |
| BTOLL[DA,S2,S3] | No value toll path, bridge toll (year 2000 cents) |
| FFT[DA,S2,S3] | No value toll path, free flow time (minutes) |
| HOVDIST[DA,S2,S3] | No value toll path, distance on HOV facilities (miles) |
| TOLLTIME[DA,S2,S3] | Toll path, travel time (minutes) |
| TOLLDIST[DA,S2,S3] | Toll path, distance (miles) |
| TOLLBTOLL[DA,S2,S3] | Toll path, bridge toll (year 2000 cents) |
| TOLLVTOLL[DA,S2,S3] | Toll path, value toll (year 2000 cents) |
| TOLLFFT[DA,S2,S3] | Toll path, free flow time (minutes) |
| TOLLHOVDIST[DA,S2,S3] | Toll path, distance on HOV facilities (miles) |
| TOLLTOLLDIST[DA,S2,S3] | Toll path, distance on toll facilities (miles) |
| RLBTY[DA,S2,S3] | No value toll path, link reliability |
| RLBTYTOLL[DA,S2,S3] | Toll path, link reliability |


### MAZ TO MAZ Distances (Bike and Walk) - skims\[bike|ped]_distance_maz_maz.txt

| Field | Description |
|-------|-------------|
| from_zone | Origin MAZ |
| to_zone | Destination MAZ |
| to_zone | Destination MAZ (written twice) |
| shortest_path_cost | Travel Cost |
| skim_value | Travel Distance |


### MAZ to TAP Distances (Bike and Walk) - skims\[bike|ped]_distance_maz_tap.txt

| Field | Description |
|-------|-------------|
| from_zone | Origin MAZ |
| to_zone | Destination TAP |
| to_zone | Destination TAP (written twice) |
| shortest_path_cost | Travel Cost |
| skim_value | Travel Distance |


### TAZ to TAZ Bike Distances - skims\bike_distance_taz_taz.txt

| Field | Description |
|-------|-------------|
| from_zone | Origin TAZ |
| to_zone | Destination TAZ |
| to_zone | Destination TAZ (written twice) |
| shortest_path_cost | Travel Cost |
| skim_value | Bike Distance |


### TAP to TAP Walk Distances - skims\ped_distance_tap_tap.txt

| Field | Description |
|-------|-------------|
| from_zone | Origin TAP |
| to_zone | Destination TAP |
| to_zone | Destination TAP (written twice) |
| shortest_path_cost | Travel Cost |
| skim_value | Walk Distance |


### Transit Skims - skims\transit_skims_[TimePeriod]\_[Iteration]_[Inner Iteration].omx

| Table Name | Description |
|------------|-------------|
| [TimePeriod]_[Set]_LBIVTT | Local bus travel time |
| [TimePeriod]_[Set]_EBIVTT | Express bus travel time |
| [TimePeriod]_[Set]_FRIVTT | Ferry travel time |
| [TimePeriod]_[Set]_LRIVTT | Light rail travel time |
| [TimePeriod]_[Set]_HRIVTT | Heavy rail travel time |
| [TimePeriod]_[Set]_CRIVTT | Commuter rail travel time |
| [TimePeriod]_[Set]_TOTALIVTT | Total travel time |
| [TimePeriod]_[Set]_FIRSTWAIT | The first wait time |
| [TimePeriod]_[Set]_XFERWAIT | The transfer wait time |
| [TimePeriod]_[Set]_EAWT | Extra added wait time due to full capacity vehicles |
| [TimePeriod]_[Set]_TOTALWAIT | Total wait time |
| [TimePeriod]_[Set]_XFERS | Total number of transfers |
| [TimePeriod]_[Set]_XFERWALK | Walk time between transfers |
| [TimePeriod]_[Set]_TOTALWALK | Total time involved walking |
| [TimePeriod]_[Set]_IN_VEHICLE_COST | In vehicle cost |
| [TimePeriod]_[Set]_CAPPEN | Capacity penalty |
| [TimePeriod]_[Set]_CROWD | Crowding penalty |
| [TimePeriod]_[Set]_FARE | The total fare |
| [TimePeriod]_[Set]_LINKREL | Link reliability |




## CTRAMP Output

TM2 produces the following tour and trip microsimulation trip lists for both individual and joint travel. The files output are listed below. The modes are defined in [Tour and Trip Modes](#tour-and-trip-modes-codes) below.  

* Accessibilities - ctramp_output/accessibilities.csv
* PreAutoOwnership - ctramp_output/aoResults_pre.csv
* AutoOwnership - ctramp_output/aoResults.csv
* Household Data - ctramp_output/householdData_[iteration].csv
* Person Data - ctramp_output/personData_[iteration].csv
* Work and School Location Choice - ctramp_output/wsLocResults_[iteration].csv
* Shadow Pricing - ctramp_output/ShadowPricingOutput_[work/school]_0.csv
* Individual Tours - ctramp_output/indivTourData_[iteration].csv
* Individual Trips - ctramp_output/indivTripData_[iteration].csv
* Joint Tours – ctramp_output/jointTourData_[iteration].csv
* Joint Trips - ctramp_output/jointTripData_[iteration].csv
* Resimulated Transit Trips - ctramp_output/indivTripDataResim_[iteration]_[inner_iteration].csv
* Unconstrained Parking Demand - ctramp_output/unconstrainedPNRDemand_[iteration]0.csv
* Constrained Parking Demand - ctramp_output/constrainedPNRDemand_[iteration]1.csv

It is important to consider occupancy when reviewing these tables. The model generates person trips. A mode is chosen for each person trip, for personal vehicle travel this could be SOV, HOV2, or HOV3+. At an aggregate level, 100 HOV2 person trips must result in 50 vehicle trips. While this is true at an aggregate level, it may not be possible to pair up all HOV2 person trips produced in the model. But the model produces enough HOV2 person trips to match the target mode share. When reviewing the joint table remember that these records include all travelers.  So only one row per trip, as opposed to one row per person or traveler.


### Individual Tours File - indivTourData_[iteration].csv

| Field | Description |
|-------|-------------|
| hh_id | Household ID |
| person_id | Person ID |
| person_num | Person number in HH |
| person_type | Person type |
| tour_id | Tour ID |
| tour_category | Tour category: |
|  | INDIVIDUAL_NON_MANDATORY |
|  | MANDATORY |
|  | AT_WORK |
| tour_purpose | Tour purpose: |
|  | Discretionary |
|  | Eating Out |
|  | Escort |
|  | Maintenance |
|  | School |
|  | Shop |
|  | University |
|  | Visiting |
|  | Work |
|  | Work-Based |
| orig_mgra | Origin MAZ |
| dest_mgra | Destination MAZ |
| start_period | Tour start period (30 min periods starting at 03:00 AM, see [Time Period Codes](#time-period-codes)) |
| end_period | Tour end period (30 min periods starting at 03:00 AM, see [Time Period Codes](#time-period-codes)) |
| tour_mode | Tour mode (see [Tour and Trip Modes Codes](#tour-and-trip-modes-codes)) |
| tour_distance | Tour distance |
| tour_time | Tour time |
| atWork_freq | At work stop frequency |
| num_ob_stops | Number of outbound stops |
| num_ib_stops | Number of inbound stops |
| out_btap | Outbound boarding tap |
| out_atap | Outbound alighting tap |
| in_btap | Inbound boarding tap |
| in_atap | Inbound alighting tap |
| out_set | Outbound transit set |
| in_set | Inbound transit set |
| sampleRate | Iteration sample rate |
| dcLogsum | Destination choice logsum |
| util_[1-17] | Utility for each tour mode (see [Tour and Trip Modes Codes](#tour-and-trip-modes-codes)) |
| prob_[1-17] | Probabilities for each tour mode  (see [Tour and Trip Modes Codes](#tour-and-trip-modes-codes)) |


### Individual Trips File - indivTripData_[iteration].csv

| Field | Description |
|-------|-------------|
| hh_id | Household ID |
| person_id | Person ID |
| person_num | Person number in HH |
| tour_id | Tour ID |
| stop_id | Trip ID |
| inbound | Inbound or outbound trip |
| tour_purpose | Tour purpose: |
|  | Discretionary |
|  | Eating Out |
|  | Escort |
|  | Maintenance |
|  | School |
|  | Shop |
|  | University |
|  | Visiting |
|  | Work |
|  | Work-Based |
| orig_purpose | Trip origin purpose: |
|  | Discretionary |
|  | Eating Out |
|  | Escort |
|  | Home |
|  | Maintenance |
|  | School |
|  | Shop |
|  | University |
|  | Visiting |
|  | Work |
|  | Work related |
|  | Work-Based |
| dest_purpose | Trip destination purpose: |
|  | Discretionary |
|  | Eating Out |
|  | Escort |
|  | Home |
|  | Maintenance |
|  | School |
|  | Shop |
|  | University |
|  | Visiting |
|  | Work |
|  | Work related |
|  | Work-Based |
| orig_mgra | Origin MAZ |
| dest_mgra | Destination MAZ |
| parking_mgra | Parking MAZ |
| stop_period | Trip period (30min periods see [Table](#time-period-codes)) |
| trip_mode | Trip mode (see [Table](#tour-and-trip-modes-codes)) |
| trip_board_tap | Trip boarding tap |
| trip_alight_tap | Trip alighting tap |
| tour_mode | Tour mode (see [Table](#tour-and-trip-modes-codes)) |
| set | Transit set |
| sampleRate | Iteration sample rate |
| TRIP_TIME | Trip time |
| TRIP_DISTANCE | Trip distance |
| TRIP_COST | Trip cost |


### Joint Tours File - jointTourData_[iteration].csv

| Field | Description |
|-------|-------------|
| hh_id | Hosehold ID |
| tour_id | Tour ID |
| tour_category | Tour category |
| tour_purpose | Tour purpose |
| tour_composition | Tour composition code |
| tour_participants | Household person numbers |
| orig_mgra | Origin MAZ |
| dest_mgra | Destination MAZ |
| start_period | Tour start period (30min periods see [Table](#time-period-codes)) |
| end_period | Tour end period (30min periods see [Table](#time-period-codes)) |
| tour_mode | Tour mode (see [Table](#tour-and-trip-modes-codes)) |
| tour_distance | Tour distance |
| tour_time | Tour time |
| num_ob_stops | Number of outbound stops |
| num_ib_stops | Number of inbound stops |
| out_btap | Outbound boarding tap |
| out_atap | Outbound alighting tap |
| in_btap | Inbound boarding tap |
| in_atap | Inbound alighting tap |
| out_set | Outbound transit set |
| in_set | Inbound transit set |
| sampleRate | Iteration sample rate |
| dcLogsum | Destination choice logsum |
| util_[1-17] | Utility for each mode |
| prob_[1-17] | Probabilities for each mode |


### Joint Trips File - jointTripData_[iteration].csv

| Field | Description |
|-------|-------------|
| hh_id | Household ID |
| tour_id | Tour ID |
| stop_id | Stop ID |
| inbound | Inbound or outbound trip |
| tour_purpose | Tour purpose |
| orig_purpose | Trip origin purpose |
| dest_purpose | Trip destination purpose |
| orig_mgra | Origin MAZ |
| dest_mgra | Destination MAZ |
| parking_mgra | Parking MAZ |
| stop_period | Trip period (30min periods see [Table](#time-period-codes)) |
| trip_mode | Trip mode (see [Table](#tour-and-trip-modes-codes)) |
| num_participants | Number of participants |
| trip_board_tap | Trip boarding tap |
| trip_alight_tap | Trip alighting tap |
| tour_mode | Tour mode (see [Table](#tour-and-trip-modes-codes)) |
| set | Transit set |
| sampleRate | Iteration sample rate |
| TRIP_TIME | Trip Time |
| TRIP_DISTANCE | Trip Distance |
| TRIP_COST | Trip Cost |


### Resimulated Transit Trips File - ctramp_output/indivTripDataResim_[iteration]_[inner_iteration].csv

| Field | Description |
|-------|-------------|
| hh_id | Household ID |
| person_id | Person ID |
| person_num | Person number in HH |
| tour_id | Tour ID |
| stop_id | Stop ID |
| inbound | Inbound or outbound trip |
| tour_purpose | Tour purpose: |
|  | Discretionary |
|  | Eating Out |
|  | Escort |
|  | Maintenance |
|  | School |
|  | Shop |
|  | University |
|  | Visiting |
|  | Work |
|  | Work-Based |
| orig_purpose | Trip origin purpose: |
|  | Discretionary |
|  | Eating Out |
|  | Escort |
|  | Home |
|  | Maintenance |
|  | School |
|  | Shop |
|  | University |
|  | Visiting |
|  | Work |
|  | Work related |
|  | Work-Based |
| dest_purpose | Trip destination purpose: |
|  | Discretionary |
|  | Eating Out |
|  | Escort |
|  | Home |
|  | Maintenance |
|  | School |
|  | Shop |
|  | University |
|  | Visiting |
|  | Work |
|  | Work related |
|  | Work-Based |
| orig_mgra | Origin MAZ |
| dest_mgra | Destination MAZ |
| parking_mgra | Parking MAZ |
| stop_period | Trip period (30min periods see [Table](#time-period-codes)) |
| trip_mode | Trip mode (see [Table](#tour-and-trip-modes-codes)) |
| trip_board_tap | Trip boarding tap |
| trip_alight_tap | Trip alighting tap |
| tour_mode | Tour mode (see [Table](#tour-and-trip-modes-codes)) |
| set | Transit set |
| sampleRate | Iteration sample rate |
| resimulatedTrip | If 1, trip is selected for resimulation |
| TRIP_TIME | Trip time |
| TRIP_DISTANCE | Trip distance |
| TRIP_COST | Trip cost |


### Unconstrained Parking Demand File - ctramp_output/unconstrainedPNRDemand_[iteration]0.csv

| Field | Description |
|-------|-------------|
| TAP | TAP ID |
| CAPACITY | Parking Capacity |
| TOT_ARRIVALS | Total arrivals in a day |
| 3:15 AM, 3:30 AM,...., 3:00 AM | Arrivals in every 15 minutes |


### Constrained Parking Demand File - ctramp_output/constrainedPNRDemand_[iteration]1.csv

| Field | Description |
|-------|-------------|
| TAP | TAP ID |
| CAPACITY | Parking Capacity |
| TOT_ARRIVALS | Total arrivals in a day |
| 3:15 AM, 3:30 AM,...., 3:00 AM | Arrivals in every 15 minutes |


### Tour and Trip Modes Codes

| Code | Mode | Description |
|------|------|-------------|
| 1 | DRIVEALONEFREE | Drive alone free (non-toll) |
| 2 | DRIVEALONEPAY | Drive alone pay (toll eligible) |
| 3 | SHARED2GP | Shared-2 general purpose lanes (non-toll, non-HOV) |
| 4 | SHARED2HOV | Shared-2 HOV-eligible (non-toll) |
| 5 | SHARED2PAY | Shared-2 pay (HOV and toll eligible) |
| 6 | SHARED3GP | Shared 3+ general purpose lanes (non-toll, non-HOV) |
| 7 | SHARED3HOV | Shared 3+ HOV-eligible (non-toll) |
| 8 | SHARED3PAY | Shared 3+ pay (HOV and toll eligible) |
| 9 | WALK | Walk |
| 10 | BIKE | Bike |
| 11 | WALK_SET | Walk-transit tour, or walk-transit-walk trip |
| 12 | PNR_SET | Park and Ride transit tour, or PNR-transit-walk if outbound trip, walk-transit-PNR if inbound trip |
| 13 | KNR_PERS | Kiss and Ride transit tour, or KNR-transit-walk if outbound trip, walk-transit-KNR if inbound trip |
| 14 | KNR_TNC | KNR tour or trip like above using TNC |
| 15 | TAXI | Taxi  |
| 16 | TNC | Riding using services like Uber or Lyft |
| 17 | SCHBUS | School bus |


### Time Period Codes

**TM2 Time Period**|**Time Period Definition**
:-----:|:-----:
1|03:00 AM to 05:00 AM
2|05:00 AM to 05:30 AM
3|05:30 AM to 06:00 AM
4|06:00 AM to 06:30 AM
5|06:30 AM to 07:00 AM
6|07:00 AM to 07:30 AM
7|07:30 AM to 08:00 AM
8|08:00 AM to 08:30 AM
9|08:30 AM to 09:00 AM
10|09:00 AM to 09:30 AM
11|09:30 AM to 10:00 AM
12|10:00 AM to 10:30 AM
13|10:30 AM to 11:00 AM
14|11:00 AM to 11:30 AM
15|11:30 AM to 12:00 PM
16|12:00 PM to 12:30 PM
17|12:30 PM to 01:00 PM
18|01:00 PM to 01:30 PM
19|01:30 PM to 02:00 PM
20|02:00 PM to 02:30 PM
21|02:30 PM to 03:00 PM
22|03:00 PM to 03:30 PM
23|03:30 PM to 04:00 PM
24|04:00 PM to 04:30 PM
25|04:30 PM to 05:00 PM
26|05:00 PM to 05:30 PM
27|05:30 PM to 06:00 PM
28|06:00 PM to 06:30 PM
29|06:30 PM to 07:00 PM
30|07:00 PM to 07:30 PM
31|07:30 PM to 08:00 PM
32|08:00 PM to 08:30 PM
33|08:30 PM to 09:00 PM
34|09:00 PM to 09:30 PM
35|09:30 PM to 10:00 PM
36|10:00 PM to 10:30 PM
37|10:30 PM to 11:00 PM
38|11:00 PM to 11:30 PM
39|11:30 PM to 12:00 AM
40|12:00 AM to 03:00 AM


## Other CTRAMP Outputs

Other CTRAMP outputs, including key fields, are described below:

* Various accessibility measures by microzone - ctramp_output/accessibilities.csv
* Household auto ownership before and after usual work and school location choice - ctramp_output/aoResults_pre.csv (before) and ctramp_output/aoResults.csv (after)
* Household level model results – ctramp_output/householdData_[iteration].csv
    * transponder – transponder ownership model result
    * cdap_pattern – CDAP model result
    * jtf_choice – joint tour frequency model result
* Person level model results – ctramp_output/personData_[iteration].csv
    * value_of_time – value of time
    * transitSubsidy_choice - chooses to use transit subsidy or not
    * transitSubsidy_percent - percentage of discount in transit subsidy
    * transitPass_choice - chooses to use transit pass or not
    * activity_pattern – CDAP model result
    * imf_choice – individual mandatory tour frequency model result
    * inmf_choice – individual non-mandatory tour frequency model result
    * fp_choice – free parking model result
    * reimb_pct – parking reimbursement percent
    * workDCLogsum - work destination choice logsum
    * schoolDCLogsum - school destination choice logsum
* Work and school location choice - ctramp_output/wsLocResults_[iteration].csv
    * EmploymentCategory – employment category
        * 1: employed FT
        * 2: employed PT
        * 3: not employed
        * 4: under age 16
    * StudentCategory – student category
        * 1: student in grade or high school
        * 2: student in college or higher
        * 3: not a student
    * WorkSegment – work segment
        * -1: Not a worker
        * 0 : Management
        * 1 : White Collar
        * 2 : Blue Collar
        * 3 : Sales
        * 4 : Natural
        * 5: Production
        * 99999: Works from home
    * SchoolSegment – school segment
        * -1: non-student
        * 0: pre-schooler
        * 1-8: grade school school district
        * 9-16: high school districts
        * 17-18: typical and non-typical university student
        * 88888: home-schooled
    * WorkLocation – work location zone
    * WorkLocationDistance – work location distance
    * WorkLocationLogsum – work location logsum
    * SchoolLocation – school location zone
    * SchoolLocationDistance – school location distance
    * SchoolLocationLogsum – school location logsum
* Shadow price by microzone, market segment, and iteration – ctramp_output/ShadowPricingOutput_school_0.csv and ctramp_output/ShadowPricingOutput_work_0.csv

## Assignment Outputs
TM2 produces multiple types of assigned network skims, often called loaded networks. The following files are output and some are generated for each of the five time periods.  

### Highway Assignment Networks

### hwy\maz_preload_[TimePeriod].net
With a MAZMAZVOL link attribute providing MAZ to MAZ lik volumes after highway assignment.

### hwy\load[TimePeriod].net
Five loaded highway networks, one for each time period, containing the following attributes for each link:

| Attribute Name | Description |
|----------------|-------------|
| V_1  | volume, in passenger car equivalents (if assigned again, volume would be labeled V_2) |
| TIME_1  | congested time, in minutes |
| VC_1  | volume to capacity ratio |
| CSPD_1  | congested speed, in miles per hour |
| VDT_1  | vehicle distance traveled, in vehicle miles |
| VHT_1  | vehicle hours traveled |
| V1_1   | volume of vehicles in assigment class one: drive alone, no value toll |
| V2_1   | volume of vehicles in assigment class two: two-occupant vehicles, no value toll |
| V3_1   | volume of vehicles in assigment class three: three-or-more-occupant vehicles, no value toll |
| V4_1   | volume of vehicles in assigment class four: very small, small, and medium trucks, no value toll |
| V5_1   | volume of vehicles in assigment class five: combination trucks, no value toll |
| V6_1   | volume of vehicles in assigment class six: drive alone, value toll |
| V7_1   | volume of vehicles in assigment class seven: two-occupant vehicles, value toll |
| V8_1   | volume of vehicles in assigment class eight: three-or-more-occupant vehicles, value toll |
| V9_1   | volume of vehicles in assigment class nine: very small, small, and medium trucks, value toll |
| V10_1  | volume of vehicles in assigment class ten: combination trucks, value toll |
| VT_1 and VXT_1 | where X is 1 through 10, are the b-to-a volumes |

### hwy\msaload[TimePeriod]_taz.net
Five highway networks with the averaged volume, one for each time period, stored in the same variables as the input variables.

### hwy\msaspeed[TimePeriod].net
Five time-period specific loaded highway networks with the following link specific variables which represent the composite roadway conditions of all previous model iterations:

| Attribute Name | Description |
|----------------|-------------|
| CTIM  | congested travel time (minutes) |
| VC  | volume-to-capacity ratio |
| CSPD  | congested travel speed (miles per hour) |
| VDT  | vehicle-distance traveled on each link (in vehicle times miles) |
| VHT  | vehicle hours traveled on each link |

### hwy\msamerge[ITERATION]_[TimePeriod].net and
Highway networks loaded with core variables mentioned below:

| Attribute Name | Description |
|----------------|-------------|
| CTIM  | congested travel time (minutes) |
| TSIN  | if 1, indicating that the link is immune to congestion and has a fixed travel time |
| DISTANCE  | link distance (miles) |
| VX_1  | corresponding to the ten vehicle classes, where X takes on the integers one through ten |
| LANES  | number of travel lanes |
| GL  | county code |
| USE  | link use code |
| FT  | facility type |
| AT  | area type |
| CAP  | link capacity in vehicles per hour per lane |
| FFS  | link free-flow speed (miles per hour) |
| FFT  | link free-flow travel time (minutes) |

### hwy\msamerge[ITERATION].csv
The loaded highway network in CSV format with some core variables noted above as well as the following output variables:

| Attribute Name | Description |
|----------------|-------------|
| ctimXX  | congested travel time (minutes), where XX indicates time-of-day |
| cspdXX  | congested travel speed (miles per hour) |
| volXX_YYY  | daily volume, where YYY indicates assigned vehicle class |
| delayXX  | link delay, calculated as the difference between the congested time and the free-flow travel time |
| vmtXX  | link vehicle-miles traveled |
| vhtXX | link vehicle-hours traveled |

### Transit Assignment Tables

### trn\boardings_by_line_[TimePeriod].txt

| Field | Description |
|-------|-------------|
| line_name | Line Name |
| description | Description of line |
| total_boardings | Total daily boardings in line |
| mode | Transit mode |
| line_mode | Line mode |

### trn\boardings_by_segment_[TimePeriod].txt

| Field | Description |
|-------|-------------|
| i_node | Start node |
| j_node | End node |
| line_name | Line name |
| description | Description |
| volume | Volume |
| boardings | Boardings |
| alightings | Alightings |
| mode | Transit mode |
| line_mode | Line mode |
| total_cap_of_line_per_hr | Total capacity per hour |
| seated_cap_of_line_per_hr | Seated capacity per hour |
| i_node_x | Start node - X coordinate |
| i_node_y | Start node - Y coordinate |
| j_node_x | End node - X coordinate |
| j_node_y | End node - Y coordinate |
| total_capacity | Total capacity |
| seated_capacity | Seated capacity |
| capacity_penalty | Capacity penalty |
| tot_vcr | Total volume-to-capacity ratio |
| seated_vcr | Seated volume-to-capacity ratio |
| ccost | Congenstion cost |
| eawt | Extra added weight time |
| seg_rel | Segment Reliability |
