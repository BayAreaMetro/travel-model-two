# Outputs
Most outputs are stored within the *project directory* under "ctramp_output", "skims", "trn", and "other" folders, each with its respective files.  

## Skims

TM2 produces multiple types of network LOS indicators, often called skim matrices. The following skims are output.  

### TAP Skim Matrices - skims\tap_skim_[TOD]_set[SETID].omx

| Skim    | Description    | Skim Number    |
|--------------------|-----------------------------------|----------------|
| IVT    | In-Vehicle Time    | 1    |
| OWT    | Origin Wait Time    | 2    |
| TWT    | Transfer Wait Time    | 3    |
| WKT    | Walk Time    | 4    |
| NTR    | Transfers (Boardings-1)    | 5    |
| FAR    | Fare    | 6    |
| IVTT(Bus)    | In-Vehicle Time Tsys Bus    | 7    |
| IVTT(ComRail)    | In-Vehicle Time Tsys ComRail    | 8    |
| IVTT(ExpBus)    | In-Vehicle Time Tsys ExpBus    | 9    |
| IVTT(LightRail)    | In-Vehicle Time Tsys LightRail    | 10    |
| Demand    | The OD matrix for the TOD and SETID   | 107    |


### TAP to TAP Fare Matrix - skims\fare.omx

| Skim    | Description    | Skim Number    |
|--------------------|-----------------------------------|----------------|
| fare   | TAP-TAP fare in cents    | fare    |


### MAZ TO MAZ Distances (Bike and Walk) - skims\maz2maz_[Bike|Walk].csv


| Name    | Units/Description    |
|--------------|------------------------------|
| OMAZ    | Origin MAZ    |
| DMAZ    | Destination MAZ    |
| DISTMILES    | Network distance in miles    |

### TAP to MAZ Distances (Bike and Walk) - skims\tap2maz_[Bike|Walk].CSV

| Name    | Units/Description    |
|--------------|------------------------------|
| TAP    | TAP ID    |
| MAZ    | MAZ ID    |
| DISTMILES    | Network distance in miles    |

### TAZ to NEAR TAPS Impedances for Drive Transit - skims\drive_taz_tap.csv

| Field    | Description    |
|-----------|-------------------|
| FTAZ    | From TAZ    |
| MODE    | Transit mode    |
| PERIOD    | Time period    |
| TTAP    | To TAP    |
| TMAZ    | To TAP’s MAZ    |
| TTAZ    | To TAP’s TAZ    |
| DTIME    | Drive time    |
| DDIST    | Drive distance    |
| DTOLL    | Drive toll    |
| WDIST    | Walk distance    |

### TAZ Skim Matrices - skims\taz_skim_[DSEG]_[TOD].omx

| Transport Systems    | Demand Segment    | Skims    | Skim Numbers    |
|----------------------|-------------------|----------------------------|----------------------|
| SOV    | SOV    | TTO,TTC,DIS,Demand    | 1,2,3,100    |
| SOVToll    | SOVToll    | TTO,TTC,DIS,AD1,TOL,Demand    | 4,5,6,7,8,104    |
| HOV2    | HOV2    | TTO,TTC,DIS,AD2,Demand    | 9,10,11,12,101    |
| HOV2Toll    | HOV2Toll    | TTO,TTC,DIS,AD1,AD2,TOL,Demand    | 13,14,15,16,17,18,105    |
| HOV3    | HOV3    | TTO,TTC,DIS,AD3,Demand    | 19,20,21,22,102    |
| HOV3Toll    | HOV3Toll    | TTO,TTC,DIS,AD1,AD3,TOL,Demand    | 23,24,25,26,27,28,106    |
| Truck    | Truck    | TTO,TTC,DIS,Demand    | 29,30,31,103    |
| TruckToll    | TruckToll    | TTO,TTC,DIS,AD1,TOL    | 32,33,34,35,36    |

### TAZ Skim Definitions

| Skim    | Description    | Intrazonal    |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------|-------------------------|
| TT0    | Free flow travel time    | 0.5 * mean nearest 3    |
| TTC    | Congested travel time    | 0.5 * mean nearest 3    |
| DIS    | Trip distance    | 0.5 * mean nearest 3    |
| AD1    | Toll only distance*    | 0.5 * mean nearest 3    |
| AD2    | HOV2 only distance*    | 0.5 * mean nearest 3    |
| AD3    | HOV3 only distance*    | 0.5 * mean nearest 3    |
| TOL    | Toll    | 0.5 * mean nearest 3    |
| *Before skimming each demand segment
AddVal1 = Length * (Toll_PrTSys([DSEG]) > 0)
AddVal2 = Length * (T0_PrTSys(HOV2/HOV2Toll) < 99999 & T0_PrTSys(SOV) >= 99999)
AddVal3 = Length * (T0_PrTSys(HOV3/HOV3Toll) < 99999 & T0_PrTSys(SOV) >= 99999)
Note AddVal1,2,3 are used for internal calculations and should not be used by the user    |

[Go to Top](output)





## CTRAMP Output

TM2 produces the following tour and trip microsimulation trip lists for both individual and joint travel. The files output are listed below. The modes are defined in [Tour and Trip Modes](Model-Outputs#tour-and-trip-modes-codes) below.  

* Individual tours - outputs/other/indivTourData_[iteration].csv
* Individual trips - outputs/other/indivTripData_[iteration].csv
* Joint tours – outputs/other/jointTourData_[iteration].csv
* Joint trips - outputs/other/jointTripData_[iteration].csv

It is important to consider occupancy when reviewing these tables. The model generates person trips. A mode is chosen for each person trip, for personal vehicle travel this could be SOV, HOV2, or HOV3+. At an aggregate level, 100 HOV2 person trips must result in 50 vehicle trips. While this is true at an aggregate level, it may not be possible to pair up all HOV2 person trips produced in the model. But the model produces enough HOV2 person trips to match the target mode share. When reviewing the joint table remember that these records include all travelers.  So only one row per trip, as opposed to one row per person or traveler.


### Individual Tours File - INDIVTOURDATA_[ITERATION].CSV

| Field           | Description                                                                                    |
|-----------------|------------------------------------------------------------------------------------------------|
| hh_id           | Household ID                                                                                   |
| person_id       | Person ID                                                                                      |
| person_num      | Person number in HH                                                                            |
| person_type     | Person type                                                                                    |
| tour_id         | Tour ID                                                                                        |
| tour_category   | Tour category:                                                                                 |
|                 | INDIVIDUAL_NON_MANDATORY                                                                       |
|                 | MANDATORY                                                                                      |
|                 | AT_WORK                                                                                        |
| tour_purpose    | Tour purpose:                                                                                  |
|                 | Discretionary                                                                                  |
|                 | Eating Out                                                                                     |
|                 | Escort                                                                                         |
|                 | Maintenance                                                                                    |
|                 | School                                                                                         |
|                 | Shop                                                                                           |
|                 | University                                                                                     |
|                 | Visiting                                                                                       |
|                 | Work                                                                                           |
|                 | Work-Based                                                                                     |
| orig_maz        | Origin MAZ                                                                                     |
| dest_maz        | Destination MAZ                                                                                |
| start_period    | [Tour start period](https://github.com/RSGInc/SOABM/wiki/Model-Outputs#time-period-codes) (periods starting at 03:00 AM)                                           |
| end_period      | [Tour end period](https://github.com/RSGInc/SOABM/wiki/Model-Outputs#time-period-codes) (periods  starting at 03:00 AM)                                             |
| tour_mode       | Tour mode (see [Tour and Trip Modes Codes](Model-Outputs#tour-and-trip-modes-codes))                                                                     |
| tour_distance   | Tour distance                                                                                  |
| tour_time       | Tour time                                                                                      |
| atWork_freq     | At work stop frequency                                                                         |
| num_ob_stops    | Number of outbound stops                                                                       |
| num_ib_stops    | Number of inbound stops                                                                        |
| escort_type_out | Escort type outbound (0 = no   escorting; 1 = ride-share, 2 = pure escort)                     |
| escort_type_in  | Escort type inbound (0 = no   escorting; 1 = ride-share, 2 = pure escort)                      |
| driver_num_out  | Escort driver number outbound   (person number of driver on outbound direction if escort tour) |
| driver_num_in   | Escort driver number inbound   (person number of driver on inbound direction if escort tour)   |
| out_btap        | Outbound boarding tap                                                                          |
| out_atap        | Outbound alighting tap                                                                         |
| in_btap         | Inbound boarding tap                                                                           |
| in_atap         | Inbound alighting tap                                                                          |
| out_set         | Outbound transit set                                                                           |
| in_set          | Inbound transit set                                                                            |
| Util_[1-14]     | Utility for each tour mode   (see [Tour and Trip Modes Codes](Model-Outputs#tour-and-trip-modes-codes))                                                  |
| Prob_[1-14]     | Probabilities for each tour   mode (see [Tour and Trip Modes Codes](Model-Outputs#tour-and-trip-modes-codes))                                            |


### Individual Trips File - INDIVTRIPDATA_[ITERATION].CSV

| Field                | Description                                                                                                                                      |
|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| hh_id                | Household ID                                                                                                                                     |
| person_id            | Person ID                                                                                                                                        |
| person_num           | Person number in HH                                                                                                                              |
| person_type          | Person type                                                                                                                                      |
| tour_id              | Tour ID                                                                                                                                          |
| Stop_id              | Trip ID                                                                                                                                          |
| Inbound              | Inbound or outbound trip                                                                                                                         |
| Tour_purpose         | Tour purpose:                                                                                                                                    |
|                      | Discretionary                                                                                                                                    |
|                      | Eating Out                                                                                                                                       |
|                      | Escort                                                                                                                                           |
|                      | Maintenance                                                                                                                                      |
|                      | School                                                                                                                                           |
|                      | Shop                                                                                                                                             |
|                      | University                                                                                                                                       |
|                      | Visiting                                                                                                                                         |
|                      | Work                                                                                                                                             |
|                      | Work-Based                                                                                                                                       |
| orig_purpose         | Trip origin purpose:                                                                                                                             |
|                      | Discretionary                                                                                                                                    |
|                      | Eating Out                                                                                                                                       |
|                      | Escort                                                                                                                                           |
|                      | Home                                                                                                                                             |
|                      | Maintenance                                                                                                                                      |
|                      | School                                                                                                                                           |
|                      | Shop                                                                                                                                             |
|                      | University                                                                                                                                       |
|                      | Visiting                                                                                                                                         |
|                      | Work                                                                                                                                             |
|                      | work related                                                                                                                                     |
|                      | Work-Based                                                                                                                                       |
| dest_purpose         | Trip destination purpose:                                                                                                                        |
|                      | Discretionary                                                                                                                                    |
|                      | Eating Out                                                                                                                                       |
|                      | Escort                                                                                                                                           |
|                      | Home                                                                                                                                             |
|                      | Maintenance                                                                                                                                      |
|                      | School                                                                                                                                           |
|                      | Shop                                                                                                                                             |
|                      | University                                                                                                                                       |
|                      | Visiting                                                                                                                                         |
|                      | Work                                                                                                                                             |
|                      | work related                                                                                                                                     |
|                      | Work-Based                                                                                                                                       |
| orig_maz             | Origin MAZ                                                                                                                                       |
| dest_maz             | Destination MAZ                                                                                                                                  |
| universityParking    | University parking (1 for   true)                                                                                                                |
| Parking_maz          | Parking MAZ                                                                                                                                      |
| stop_period          | Trip period (30min periods see [Table](https://github.com/RSGInc/SOABM/wiki/Model-Outputs#time-period-codes))                                                                                                   |
| trip_mode            | Trip mode (see [Table](Model-Outputs#tour-and-trip-modes-codes))                                                                                                                       |
| Trip_board_tap       | Trip boarding tap                                                                                                                                |
| Trip_alight_tap      | Trip alighting tap                                                                                                                               |
| Tour_mode            | Tour mode (see [Table](Model-Outputs#tour-and-trip-modes-codes))                                                                                                                       |
| Driver_pnum          | The person_num of the driver   if the trip origin or destination is escort; else 0 if neither end of the   trip is part of the escort model.     |
| Orig_escort_stoptype | Origin escort trip stop type   (0 = no escorting; 1 = dropped-off, 2 = picked-up)                                                                |
| orig_escortee_pnum   | The person_num of the child   being picked-up or dropped off at the origin end of the trip                                                       |
| dest_escort_stoptype | Destination escort trip stop   type (0 = no escorting; 1 = dropped-off, 2 = picked-up)                                                           |
| dest_escortee_pnum   | The person_num of the child   being picked-up or dropped off at the destination end of the trip                                                  |
| Set                  | Transit set ID                                                                                                                                   |

[Go to Top](output)


### Joint Tours File - JOINTTOURDATA_[ITERATION].CSV

| Field             | Description                                          |
|-------------------|------------------------------------------------------|
| hh_id             | Hosehold ID                                          |
| tour_id           | Tour ID                                              |
| tour_category     | Tour category                                        |
| tour_purpose      | Tour purpose                                         |
| tour_composition  | Tour composition code                                |
| tour_participants | Household person numbers                             |
| orig_maz          | Origin MAZ                                           |
| dest_maz          | Destination MAZ                                      |
| start_period      | Tour start period 30min periods see [Table](Model-Outputs#time_periodcodes))  |
| end_period        | Tour end period (30min periods see [Table](Model-Outputs#time_periodcodes))    |
| tour_mode         | Tour mode (see [Table](Model-Outputs#tour-and-trip-modes-codes))                           |
| tour_distance     | Tour distance                                        |
| tour_time         | Tour time                                            |
| num_ob_stops      | Number of outbound stops                             |
| num_ib_stops      | Number of inbound stops                              |
| out_btap          | Outbound boarding tap                                |
| out_atap          | Outbound alighting tap                               |
| in_btap           | Inbound boarding tap                                 |
| in_atap           | Inbound alighting tap                                |
| out_set           | Outbound transit set                                 |
| in_set            | Inbound transit set                                  |
| Util_[1-14]       | Utility for each mode                                |
| Prob_[1-14]       | Probabilities for each mode                          |


### Joint Trips File - JOINTTRIPDATA_[ITERATION].CSV

|    Field    |    Description    |
|-------------------------|------------------------------------------------------|
|    hh_id    |    Household ID    |
|    tour_id    |    Tour ID    |
|    Stop_id    |    Trip ID    |
|    Inbound    |    Inbound or outbound trip    |
|    tour_purpose    |    Tour purpose    |
|    orig_purpose    |    Trip origin purpose    |
|    dest_purpose    |    Trip destination purpose    |
|    orig_maz    |    Origin MAZ    |
|    dest_maz    |    Destination MAZ    |
|    Parking_maz    |    Parking MAZ    |
|    universityParking    |    University parking (1 for   true)    |
|    stop_period    |    Trip period (30min periods see [Table](Model-Outputs#time_periodcodes))     |
|    trip_mode    |    Trip mode (see [Table](Model-Outputs#tour-and-trip-modes-codes))    |
|    Num_participants    |    Number of participants    |
|    Trip_board_tap    |    Trip boarding tap    |
|    Trip_alight_tap    |    Trip alighting tap    |
|    Tour_mode    |    Tour mode (see [Table](Model-Outputs#tour-and-trip-modes-codes))    |
|    Set    |    Transit set ID    |

### Tour and Trip Modes Codes

| Code | Mode | Description |
|------|----------------|------------------------------------------------------------------------------------------------------|
| 1 | DRIVEALONEFREE | Drive alone free (non-toll) |
| 2 | DRIVEALONEPAY | Drive alone pay (toll   eligible) |
| 3 | SHARED2GP | Shared-2 general purpose lanes   (non-toll, non-HOV) |
| 4 | SHARED2HOV | Shared-2 HOV-eligible   (non-toll) |
| 5 | SHARED2PAY | Shared-2 pay (HOV and toll   eligible) |
| 6 | SHARED3GP | Shared 3+ general purpose   lanes (non-toll, non-HOV) |
| 7 | SHARED3HOV | Shared 3+ HOV-eligible   (non-toll) |
| 8 | SHARED3PAY | Shared 3+ pay (HOV and toll   eligible) |
| 9 | WALK | Walk |
| 10 | BIKE | Bike |
| 11 | WALK_SET | Walk-transit tour, or   walk-transit-walk trip |
| 12 | PNR_SET | Park and Ride transit tour, or   PNR-transit-walk if outbound trip, walk-transit-PNR if inbound trip |
| 13 | KNR_SET | Kiss and Ride transit tour, or   KNR-transit-walk if outbound trip, walk-transit-KNR if inbound trip |
| 14 | SCHBUS | School bus |

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

[Go to Top](output)

## Demand Matrices

The output demand matrices from a run are shown in [Demand Matrices in OMX Format](Model-Outputs#demand-matrices-in-omx-format) and listed in [Demand Matrices](Model-Outputs#demand-matrices-1) below.  


### Demand Matrices

| File | Description | Matrices |
|--------------------|-------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| ctrampTazTrips.omx | TAP level matrices by mode and   time-of-day | SOV_[TOD],   SOVToll_[TOD], HOV2_[TOD], HOV2Toll_[TOD],   HOV3_[TOD], HOV3Toll_[TOD] |
| ctrampTapTrips.omx | TAP level matrices by mode and   time-of-day | Set1_[TOD],   Set2_[TOD], Set3_[TOD] |
| ctrampNmTrips.omx | MAZ level matrices for walk and bike mode by time-of-day | Walk_[TOD],   Bike_[TOD] |
| cvmTrips.omx | CVM TAZ level matrices by mode   and time-of-day | CAR_[TOD],   SU_[TOD], MU_[TOD] |
| externalOD.omx | External model TAZ level   matrices by mode and time-of-day | [TOD]_hbw,   [TOD]_hbcoll, [TOD]_hbsch, [TOD]_hbo, [TOD]_hbr,   [TOD]_hbs, [TOD]_nhbnw, [TOD]_nhbw, [TOD]_truck |

### TAP Parks

| File | Description |
|------|-------------|
|trips\tapParks.csv | List of TAPs by number of PNR parkings. |

## Other CT-RAMP Outputs

Other CT-RAMP outputs, including key fields, are described below:

* Various accessibility measures by microzone - outputs/other/accessibilities.csv
* Household auto ownership before and after usual work and school location choice - outputs/other/aoResults_pre.csv (before) and outputs/other/aoResults.csv (after)
* Household level model results – outputs/other/householdData_[iteration].csv
  * transponder – transponder ownership model result
  * cdap_pattern – CDAP model result
  * out_escort_choice – outbound escort model result
  * inb_escort_choice – inbound escort model result
  * jtf_choice – joint tour frequency model result
* Person level model results – outputs/other/personData_[iteration].csv
  * value_of_time – value of time
  * activity_pattern – CDAP model result
  * imf_choice – individual mandatory tour frequency model result
  * inmf_choice – individual non-mandatory tour frequency model result
  * fp_choice – free parking model result
  * reimb_pct – parking reimbursement percent
* Work and school location choice - outputs/other/wsLocResults_[iteration].csv
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
* Shadow price by microzone, market segment, and iteration – outputs/other/ShadowPricingOutput_school_[iteration].csv and outputs/other/ShadowPricingOutput_work_[iteration].csv

[Go to Top](output)
