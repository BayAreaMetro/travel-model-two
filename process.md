---
layout: page
title: Modeling Process
---

*Work in Progress*

# Modeling Process

1. [`preprocess\zone_seq_net_builder.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/zone_seq_net_builder.job)
   * Summary: Builds a sequential zone numbering system for TAZs, MAZs, TAPs and Externals 
     given the [node number conventions](/travel-model-two/guide/#County-Node-Numbering-System).
   * Input: `hwy\mtc_final_network_base.net`, the roadway network
   * Output:
     1. `hwy\mtc_final_network.net` with additional link attributes, _TAZSEQ_, _MAZSEQ_, _TAPSEQ_ and _EXTSEQ_
     2. `hwy\mtc_final_network_zone_seq.csv` with columns _N_, _TAZSEQ_, _MAZSEQ_, _TAPSEQ_ and _EXTSEQ_
     
1. [`preprocess\zone_seq_disseminator.py`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/zone_seq_disseminator.py)
   * Summary: Builds other files with zone numbers
   * Input: 
     1. `hwy\mtc_final_network_zone_seq.csv`
     2. `landuse\taz_data.csv` - [Zonal Data](/travel-model-two/guide/#Zonal-Data)
     3. `landuse\maz_data.csv` - [Micro Zonal Data](/travel-model-two/guide/#Micro-Zonal-Data)
   * Output:
     1. `landuse\taz_data.csv` - Adds (or rewrites) column **TAZ** (renumbered version of **TAZ_ORIGINAL**)
     2. `landuse\maz_data.csv` - Adds (or rewrites) columns **TAZ** and **MTAZ** (renumbered versions of **TAZ_ORIGINAL** and **MTAZ_ORIGINAL**)
     3. `CTRAMP\model\ParkLocationAlts.csv` - park location alternatives,  **TODO**: What are these? Move this from _CTRAMP_
     4. `CTRAMP\model\DestinationChoiceAlternatives.csv` - destination choice alternatives. *TODO*: what are these?  Move this from _CTRAMP_
     5. `CTRAMP\model\SoaTazDistAlternatives.csv`  **TODO**: what are these?  Move this from _CTRAMP_
     6. `CTRAMP\model\ParkLocationSampleAlts.csv`  **TODO**: what are these?  Move this from _CTRAMP_

1. [`preprocess\CreateNonMotorizedNetwork.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/CreateNonMotorizedNetwork.job)
   * Summary: Create pedestrian, bicycle and pedestrian TAP (Transit Access Point) to TAP networks.  The procedure to create the non-motorized networks (walk and bike) extracts the links from the network which have **CNTYPE** equal to TANA, PED/BIKE, MAZ, TAZ, or TAP and which are not freeways, or which have the BIKEPEDOK flag set to true (1). For the pedestrian network, any link that is one-way has an opposite direction link generated. 
   * Input: 
     1. `CTRAMP\scripts\block\maxCosts.block` - sets maximum pedestrian distance, maximum bike distances, maximum driving generalized cost, maximum tap-tap pedestrian distance
     2. `hwy\mtc_final_network.net`, the roadway network
   * Output:
     1. `hwy\mtc_ped_network.net`, the pedestrian network.  Link attributes are the same as the roadway network, plus **SP_DISTANCE** (? What is this?)
     2. `hwy\mtc_tap_ped_network.net`, the tap-tap pedestrian network.  This is the same as the pedestrian network but with **SP_DISTANCE** for TAP links modified to max tap ped distance.  (?)
     3. `hwy\mtc_bike_network.net`, the bike network.  This is extracted in a similar fashion as the pedestrian network, but **CNTYPE** = 'BIKE' links are included instead of **CNTYPE** = 'PED'.
