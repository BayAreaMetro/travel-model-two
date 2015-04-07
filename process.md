---
layout: page
title: Modeling Process
---

*Work in Progress*

# Contents
1. [Modeling Process](#modeling-process)
  1. [Preprocessing](#preprocessing)
  2. [Shortest Path Skims](#shortest-path-skims)
  3. [Build Airport Trip Matrices](#build-airport-trip-matrices)
  4. [Highway and Transit Skims](#highway-and-transit-skims)
  5. [Core](#core)
  6. [Non Residential](#non-residential)

# Modeling Process

## Preprocessing

1. [`preprocess\zone_seq_net_builder.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/zone_seq_net_builder.job)
   * Summary: Builds a sequential zone numbering system for TAZs, MAZs, TAPs and Externals 
     given the [node number conventions](/travel-model-two/guide/#county-node-numbering-system).
   * Input: `hwy\mtc_final_network_base.net`, the roadway network
   * Output:
     1. `hwy\mtc_final_network.net` with additional nodeattributes, **TAZSEQ**, **MAZSEQ**, **TAPSEQ** and **EXTSEQ**
     2. `hwy\mtc_final_network_zone_seq.csv`, the mapping of CUBE roadway nodes to renumbered TAZs, MAZs and TAPs.  Columns are _N_, _TAZSEQ_, _MAZSEQ_, _TAPSEQ_ and _EXTSEQ_
     
1. [`preprocess\zone_seq_disseminator.py`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/zone_seq_disseminator.py)
   * Summary: Builds other files with zone numbers
   * Input: 
     1. `hwy\mtc_final_network_zone_seq.csv`, the mapping of CUBE roadway nodes to renumbered TAZs, MAZs and TAPs
     2. `landuse\taz_data.csv` - [Zonal Data](/travel-model-two/guide/#zonal-data)
     3. `landuse\maz_data.csv` - [Micro Zonal Data](/travel-model-two/guide/#micro-zonal-data)
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
     1. [`CTRAMP\scripts\block\maxCosts.block`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/block/maxCosts.block) - sets maximum pedestrian distance, maximum bike distances, maximum driving generalized cost, maximum tap-tap pedestrian distance
     2. `hwy\mtc_final_network.net`, the roadway network
   * Output:
     1. `hwy\mtc_ped_network.net`, the pedestrian network.  Link attributes are the same as the roadway network, plus **SP_DISTANCE**, or Shortest Path Distance.  This is set to:
        * `@max_ped_distance@` for **CNTYPE**=_MAZ_ links and **CNTYPE**=_TAP_ links with a TAZ/MAZ/TAP origin or destination,
        * `@nomax_bike_distance@` for _TAZ_ links
        * **FEET** otherwise
     2. `hwy\mtc_tap_ped_network.net`, the tap-tap pedestrian network.  This is the same as the pedestrian network but with **SP_DISTANCE** for TAP links modified to @max_tap_ped_distance@.  This is because the tap-to-tap ped distances are shorter (1/2 mile versus 3 miles).
     3. `hwy\mtc_bike_network.net`, the bike network.  This is extracted in a similar fashion as the pedestrian network, but **CNTYPE** = 'BIKE' links are included instead of **CNTYPE** = 'PED'.

1. [`preprocess\tap_to_taz_for_parking.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/tap_to_taz_for_parking.job)
   * Summary: Finds shortest pedestrian distance from TAP nodes to TAZ nodes.  Max cost = `@nomax_bike_distance@ + @max_ped_distance@ + @max_ped_distance@`.
   * Input: `hwy\mtc_ped_network.net`, the pedestrian network
   * Output: `hwy\tap_to_taz_for_parking.txt`, a CSV with columns
      1. origin TAP
      2. destination TAZ
      3. destination TAZ (repeated)
      4. total **SP_DISTANCE**
      5. total **FEET**

1. [`preprocess\tap_data_builder.py`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/tap_data_builder.py)
   * Summary: Maps TAPs to the closest TAZ for that TAP (via **FEET**).
   * Input:
      1. `hwy\mtc_final_network_zone_seq.csv`, the mapping of CUBE roadway nodes to renumbered TAZs, MAZs and TAPs
      2. `hwy\tap_to_taz_for_parking.txt`, listing the shortest pedestrian distance from all TAPs to all TAZs
   * Output: `hwy\tap_data.csv` (**TODO**: name this better?), a CSV with columns
      1. TAP - the tap number (in CTRAMP sequential numbering)
      2. TAP_original - the original tap number (in the CUBE network)
      3. lotid - the lot id; this is the same as TAP right now
      4. TAZ - the taz the tap is associated with (see tap_to_taz_for_parking.job)
      5. capacity - the capacity of the lot; this is set to 9999 by default, but could be changed after this process has run

1. [`preprocess\SetTolls.JOB`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/SetTolls.JOB)
   * Summary: Converts **TOLLBOOTH** attribute to toll attributes (by vehicle class and time period) on the network.
   * Input:
      1. `hwy\mtc_final_network.net`, the roadway network
      2. `hwy\bridge_tolls.csv`, maps **TOLLBOOTH** to bridge tolls.  See [hwy Readme](https://github.com/MetropolitanTransportationCommission/travel-model-two-networks/blob/master/INPUT_tm2_2000/hwy/Readme.md) for details.
      3. `hwy\value_tolls.csv`, maps **TOLLBOOTH** to value tolls, which can be distance-based.
   * Output: `hwy\mtc_final_network_with_tolls.net`, the roadway network with additional link attributes **TOLLXX_YY**, where XX is the timeperiod and YY is the vehicle class.

1. [`preprocess\SetHovXferPenalties.JOB`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/SetHovXferPenalties.JOB)
   * Summary: Adds **HovXPen** attribute to roadway network for HOV to non-HOV in theory, but actually does nothing.  **TODO** Deprecate script or make it do something.
   * Input: `hwy\mtc_final_network_with_tolls.net`, the roadway network
   * Output: same with **HovXPen** attribute added if this ever comes back.  [Travel Model One sets it to 0.5.](https://github.com/MetropolitanTransportationCommission/travel-model-one/blob/master/model-files/scripts/preprocess/SetHovXferPenalties.JOB)

1. [`preprocess\SetCapClass.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/SetCapClass.job)
   * Summary: Adds area type and capcity class to the roadway network based on the weighted population and employment density of the nearby MAZs for the link (via [`preprocess\codeLinkAreaType.py`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/codeLinkAreaType.py)
   * Input: `hwy\mtc_final_network_with_tolls.net`, the roadway network
   * Output: same with **AT** attribute added to those links with **CNTYPE** one of ("TANA","USE","TAZ","EXT"), set to -1 otherwise.  **CAPCLASS** = 10x **AT** + **FT**.  Area types are as follows:
      * 0: regional core
      * 1: central business district
      * 2: urban business
      * 3: urban
      * 4: suburban
      * 5: rural

1. [`preprocess\CreateFiveHighwayNetworks.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/CreateFiveHighwayNetworks.job)
   * Summary: Creates per-timeperiod roadway networks for assignment and skimming
      1. Deletes links with **ASSIGNABLE** = 0
      2. Deletes links with **CNTYPE** = 'TANA' and **NUMLANES** = 0
      3. Deletes links with **CNTYPE** not one of ("TANA","MAZ","TAZ","TAP","EXT")
      4. Sets freeflow time (in minutes) **FFT** based on **FEET** and **FFS**, freeflow speed.
      5. Variously deletes/changes **USECLASS**, **NUMLANES**, **FFT** or new field **CTIM** (congested time, which is set to be equal to **FFT** here) for special (mostly bridge) links. 
      6. **TODO**: **CTIM** == **FFT** so not sure why this is added here?  Also, the reversible lanes links and the shared road bypass links with their nodes are all hard-coded into the script... why not configure this?
   * Input: `hwy\mtc_final_network_with_tolls.net`, the roadway network
   * Output: `hwy\avgload[EA,AM,MD,PM,EV].net`, the per-timeperiod roadway networks

1. [`preprocess\BuildTazNetworks.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/BuildTazNetworks.job)
    * Summary: Create TAZ-based roadway networks for skimming and assignments by renumbering the nodes so TAZs (and externals TAZs) are sequential and start at 1 and the rest of the nodes are sequential and start at 1,000,001.
   * Input: `hwy\avgload[EA,AM,MD,PM,EV].net`, the per-timeperiod roadway networks
   * Output: 
      1. `hwy\avgload[EA,AM,MD,PM,EV]_taz.net`, the per-timeperiod roadway networks with renumbered nodes.  New node attribute **OLD_NODE** preserves mapping to original node number, as does new link attribues **OLD_A** and **OLD_B**.
      2. `hwy\avgload[EA,AM,MD,PM,EV]_taz_to_node.txt`, text version (**TODO**: for what?)
      3. `hwy\msaload[EA,AM,MD,PM,EV]_taz.net` is the same as `hwy\avgload[EA,AM,MD,PM,EV]_taz.net` but with new link variables **vol**, **vc**, **vol_[da,s2,s3,sm,hv][T?]**, and **volT** initialized to zero.

## Shortest Path Skims

1. [`skims\NonMotorizedSkims.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/NonMotorizedSkims.job)
    * Summary: Creates 6 types of non-motorized shortest-path skims using Cube's shortest-path utility.
    * **TODO**: This creates uses cube to create a bunch of cube scripts which I find pretty awkward.  It also could
      do more parallelizing and is limited to 9 (one per county) at present. 
      Use python to create the cubescript?  It would be easier to make flexible and run the pieces
      on an arbitrary number of nodes.
    * Input: 
      1. [`CTRAMP\scripts\block\maxCosts.block`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/block/maxCosts.block)
      2. `hwy\mtc_ped_network.net`, the pedestrian network
      3. `hwy\mtc_bike_network.net`, the bike network
      4. `hwy\mtc_tap_ped_network.net`, the tap-tap pedestrian network
      5. `hwy\mtc_final_network_zone_seq.csv`, used to [resequence columns](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/resequence_columns.py) in the skims
    * Output: 
      1. `skims\ped_distance_maz_maz.csv`, the pedestrian MAZ to MAZ skims
      2. `skims\ped_distance_maz_tap.csv`, the pedestrian MAZ to TAP skims
      3. `skims\bike_distance_maz_maz.csv`, the bicycle MAZ to MAZ skims
      4. `skims\bike_distance_maz_tap.csv`, the bicycle MAZ to TAP skims
      5. `skims\bike_distance_taz_taz.csv`, the bicycle TAZ to TAZ skims
      6. `skims\ped_distance_tap_tap.csv`, the pedestrian TAP to TAP skims

1. [`skims\MazMazSkims.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/MazMazSkims.job)
    * Summary: Creates auto shortest-path skims for MAZ-to-MAZ using Cube's shortest-paths utility.
    * **TODO**: Same note as `NonMotorizedSkims.job`.  Could share same python scripts for distributing and for creating scripts.
    * Input:
      1. [`CTRAMP\scripts\block\maxCosts.block`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/block/maxCosts.block), which limits the _max_drive_gencost_
      2. [`CTRAMP\scripts\block\hwyparam.block`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/block/hwyparam.block)
      3. `hwy\autoopcost.properties`, auto and truck operating costs
      4. `hwy\avgload[EA,AM,MD,PM,EV].net`, the per-timeperiod roadway networks with renumbered nodes
    * Output: `skims\HWYSKIM_MAZMAZ_DA.csv`, the auto MAZ to MAZ skims.  Columns are: _ORIG_MAZ_, _DEST_MAZ_, _DEST2_MAZ_, _GENCOST_, _FEET_, _BRIDGE_TOLL_

## Build Airport Trip Matrices

1. [`nonres\BuildAirPax.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/nonres/BuildAirPax.job)
    * Summary: Creates air passenger vehicle trip tables based on 2006 survey data and 2035 predictions of air travel for the three bay area airports.
    * Input: `nonres\[2007,2035]_[to,from][OAK,SFO,SJC].csv`, trip tables for TAZ origins & destinations for the airports by time-of-day and mode (escort, park, rental car, taxi, limo, shared rid van, hotel shuttle, charter bus).
    * Output: `nonres\tripsAirPax[EA,AM,MD,PM,EV].mtx`, trip tables for resequenced (consecutive) origin/destination TAZs for modes [DA,SR2,SR3][TOLL]?

## Highway and Transit Skims

1. [`skims\HwySkims.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/HwySkims.job)
    * Summary: Creates roadway skims.
    * Input:
      1. [`CTRAMP\scripts\block\hwyparam.block`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/block/hwyparam.block) for value of time
      2. `hwy\autoopcost.properties`, auto and truck operating costs
      3. `hwy\avgload[EA,AM,MD,PM,EV]_taz.net`, the per-timeperiod roadway networks with renumbered nodes
    * Output:
      1. `skims\HWYSKM[EA,AM,MD,PM,EV]_taz.tpp`, level of service matrices for autos
      2. `skims\COM_HWYSKIM[EA,AM,MD,PM,EV]_taz.tpp`, level of service matrices for commercial vehicles
      3. `logs\HwySkims.debug`, a debug log file for a trace origin/destination

1. [`skims\BuildTransitNetworks.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/BuildTransitNetworks.job)
    * Summary: First, this script runs [`build_walk_transfer_bypass_links.py`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/build_walk_transfer_bypass_links.py), which creates "pseudo TAP" nodes, which are the TAP nodes offset a small distance, and creates links for pseudo TAPs to stops and vice versa, as well as pseudo TAP to pseudo TAP links.  It then incorporates these new nodes and links (with CNTYPE=`TRWALK`), and adds new link attributes **WALKDIST**, **WALKTIME**, **NTL_MODE**, and **TRANTIME**.  The networks are renumbered so that all TAPS are sequential and first, and **CNTYPE** `MAZ`, `TAZ`, `PED`, `BIKE`, and `EXT` are dropped, and **TRANTIME** is imported from per-time period loaded roadway networks.
    * **TODO**: **TRANTIME** is based on assumed speeds by **CNTYPE** and those speeds are hardcoded into this script.
    * Input:
      1. `hwy\mtc_final_network.net`, the roadway network
      2. `skims\ped_distance_tap_tap-origN.csv`, the pedestrian TAP to TAP skims
      3. `hwy\avgload[EA,AM,MD,PM,EV].net`, the congested network (**TODO**: Is this generated with real congested times?  Currently, it's not, I don't think.)
    * Output:
      1. `hwy\mtc_transit_network_tap_to_node.txt`, mapping of renumbered nodes.
      2. `hwy\mtc_transit_network_[EA,AM,MD,PM,EV].net`, transit network with renumbered nodes, TAP first pseudo TAP nodes and links, and *TRANTIME* attribute from congested roadway link time.

1. [`skims\build_drive_access_skims.py`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/build_drive_access_skims.py)
    * Summary: Called by [`skims\TransitSkims.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/TransitSkims.job), below, this script creates drive access links from TAZs to TAPs.  This process involves:
      1. `trn\transitLines.lin` is read to determine the set of stops that are accessible for each (timeperiod, transit mode (see [network node attributes](http://metropolitantransportationcommission.github.io/travel-model-two/guide/#node-attributes) for transit modes).
      2. `hwy\mtc_final_network_tap_links.csv` is read to link those stops with their TAPs and find the set of TAPs we want to access for each (timeperiod, mode)
      3. `skims\ped_distance_maz_tap.csv` is read to find the associate the nearest MAZ to each of those TAPs (along with the walk distance)
      4. `landuse\maz_data.csv` correspondingly assocates each MAZ with its containing TAZ
      5. These are all regarded as destination TAP/MAZ/TAZs.  For each timeperiod, each origin TAZ needs a path to a TAP for each mode.  This is found by combining a generalized driving cost from the driving skim, `skims\DA_[EA,AM,MD,PM,EV]_taz_time.csv` along with the MAZ to TAP walk time to find the optimal TAZ to MAZ to TAP walk.
    * Input: Those files listed above, plus
      1. `CTRAMP\scripts\block\hwyParam.block` for value of time
      2. `hwy\autoopcost.properties` for auto operating cost, to create generalized cost for drive
      3. `hwy\mtc_final_network_zone_seq`, for translating between TAPs, MAZs, TAZs and their renumbered versions
      4. `hwy\mtc_final_network_tap_nodes.csv` for corresponding TAPs with their transit nodes
    * Output: `skims\drive_maz_taz_tap.csv` with the following columns:
      1. ORIG_TAZ   - Origin TAZ (sequential numbering)
      2. MODE       - The (transit) mode
      3. TIMEPERIOD - The time period
      4. DEST_TAP   - Destination TAP (sequential numbering)
      5. DEST_MAZ   - Destination MAZ (sequential numbering)
      6. DEST_TAZ   - Destination TAZ (sequential numbering)
      7. DRIVE_TIME - Drive time from ORIG_TAZ to DEST_TAZ (minutes)
      8. DRIVE_DIST - Drive distance from ORIG_TAZ to DEST_TAZ (miles)
      9. DRIVE_BTOLL- Drive bridge toll from ORIG_TAZ to DEST_TAZ (in year 2010 cents)
      10. WALK_DIST  - Walk access distance from the MAZ centroid to the TAP (feet)

1. [`skims\tap_lines.py`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/tap_lines.py)
    * Summary: Called by [`skims\TransitSkims.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/TransitSkims.job), below, this script outputs a list of TAPs and the lines that serve that TAP
    * Input:
      1. `trn\transitLines.lin`, the transit lines
      2. `hwy\mtc_final_network_tap_links.csv`, the TAP to node connectors
      3. `hwy\mtc_final_network_zone_seq.csv`, for translating between TAPs, MAZs, TAZs and their renumbered versions
    * Output: `trn\tapLines.csv` with the following columns:
      1. TAP: TAP (sequential numbering)
      2. LINES: space-delimited list of names of lines serving the TAP

1. [`skims\TransitSkims.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/TransitSkims.job)
    * Summary: In addition to running [`skims\build_drive_access_skims.py`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/build_drive_access_skims.py), [`skims\tap_lines.py`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/tap_lines.py), and [`skims\renumber_transit_line_nodes.py`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/renumber_transit_line_nodes.py), creates 3 sets of transit skims per time period via Citilabs Public Transport Module
    * Input:
      1. `hwy\mtc_transit_network_[EA,AM,MD,PM,EV].net`, transit network
      2. `trn\transitLines_new_nodes.lin`, the transit lines with nodes renumbered
      3. [`trn\transitSystem.PTS`](https://github.com/MetropolitanTransportationCommission/travel-model-two-networks/blob/master/INPUT_tm2_2000/trn/transit_support/transitSystem.PTS), the Public Transport System data file defines wait curve definitions
      4. [`trn\transitFactors_SET[1,2,3].fac`](https://github.com/MetropolitanTransportationCommission/travel-model-two-networks/blob/master/INPUT_tm2_2000/trn/transit_support/transitFactors_SET1.fac), factors for each skim set
      5. [`trn\fareMatrix.txt`](https://github.com/MetropolitanTransportationCommission/travel-model-two-networks/blob/master/INPUT_tm2_2000/trn/transit_fares/fareMatrix.txt), the fare matrix
      6. [`trn\fares.far`](https://github.com/MetropolitanTransportationCommission/travel-model-two-networks/blob/master/INPUT_tm2_2000/trn/transit_fares/fares.far), definitions of fare systems
    * Output:
      1. `trn\mtc_transit_network_[EA,AM,MD,PM,EV]_SET[1,2,3]_with_transit.net`, transit network (??)
      2. `skims\transit_skims_[EA,AM,MD,PM,EV]_SET[1,2,3].TPP`, the transit skims, with matrices
         1. COMPCOST: composite cost, including walk, wait, boarding transfer and in-vehicle time, and fares
         2. IWAIT: average wait time incurred at the start of the trip for all attractive routes between zones
         3. XWAIT: average actual wait incurred at the transfer points of all attractive routes between zones
         4. XPEN: average actual transfer penalty for all attractive routes between zones
         5. BRDPEN: the boarding penalties associated with transit legs of the trip
         6. XFERS: the average number of transfers used by the attractive routes between zone pairs 
         7. FARE: the average fare, in monetary units, for all attractive routes between zones
         8. XWTIME: transfer walk time
         9. AEWTIME: acess/egress walk time
         10. LB_TIME: local bus time
         11. EB_TIME: express bus time
         12. LR_TIME: light rail time
         13. HR_TIME: heavy rail time
         14. CR_TIME: commuter rail time
         15. BEST_MODE: the "highest" mode with positive time, where commuter rail=5, heavy rail=4, light rail=3, express bus=2, local bus=1
      3. `trn\mtc_transit_lines_[EA,AM,MD,PM,EV]_SET[1,2,3]_with_transit.lin`
      4. `trn\mtc_transit_ntlegs_[EA,AM,MD,PM,EV]_SET[1,2,3]_with_transit.ntl`, nontransit legs file
      5. `trn\mtc_transit_ntlegs_[EA,AM,MD,PM,EV]_SET[1,2,3]_with_transit.rte`, enumerated routes
      6. `trn\mtc_transit_report_[EA,AM,MD,PM,EV]_SET[1,2,3]_with_transit.rpt`, reports from the route-enumeration and route-evaluation processes

1. [`skims\SkimSetsAdjustment.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/SkimSetsAdjustment.job)
    * Summary: Reads the 3 transit skim sets and if any set times are the same as the times for another set for an origin/destination pair, the second set's values are updated to NA value (0).
    * Input: `skims\transit_skims_[EA,AM,MD,PM,EV]_SET[1,2,3].TPP`, the transit skims
    * Output: `skims\transit_skims_[EA,AM,MD,PM,EV]_SET[1,2,3].TPP`, the transit skims with some O/Ds removed if they're duplicates of an earlier set

## Core

* Summary:
* Input:
    1. [`mtctm2.properties`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/runtime/mtctm2.properties), the configuration for the core
* Output:
    1. `ctramp_output\wsLocResults.csv`, work and school location choice results
    2. ...

1. [`assign\merge_demand_matrices.s`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/assign/merge_demand_matrices.s)
    * Summary: Consolidates the output matrix files from the core into TAZ- and TAP-level demand matrices.
    * Input:
      1. `ctramp_output\auto_[EA,AM,MD,PM,EV]_SOV_GP_[EA,AM,MD,PM,EV].mat`, auto single occupancy vehicle general purpose lane TAZ-to-TAZ demand matrix
      2. `ctramp_output\auto_[EA,AM,MD,PM,EV]_SOV_PAY_[EA,AM,MD,PM,EV].mat`, auto single occupancy vehicle pay lane TAZ-to-TAZ demand matrix
      3. `ctramp_output\auto_[EA,AM,MD,PM,EV]_SR2_GP_[EA,AM,MD,PM,EV].mat`, auto shared ride 2 general purpose lane TAZ-to-TAZ demand matrix
      4. `ctramp_output\auto_[EA,AM,MD,PM,EV]_SR2_HOV_[EA,AM,MD,PM,EV].mat`, auto shared ride 2 HOV lane TAZ-to-TAZ demand matrix
      5. `ctramp_output\auto_[EA,AM,MD,PM,EV]_SR2_PAY_[EA,AM,MD,PM,EV].mat`, auto shared ride 2 pay lane TAZ-to-TAZ demand matrix
      6. `ctramp_output\auto_[EA,AM,MD,PM,EV]_SR3_GP_[EA,AM,MD,PM,EV].mat`, auto shared ride 3+ general purpose lane TAZ-to-TAZ demand matrix
      7. `ctramp_output\auto_[EA,AM,MD,PM,EV]_SR3_HOV_[EA,AM,MD,PM,EV].mat`, auto shared ride 3+ HOV lane TAZ-to-TAZ demand matrix
      8. `ctramp_output\auto_[EA,AM,MD,PM,EV]_SR3_PAY_[EA,AM,MD,PM,EV].mat`, auto shared ride 3+ pay lane TAZ-to-TAZ demand matrix
      9. `ctramp_output\nonmotor_[EA,AM,MD,PM,EV]_BIKE_[EA,AM,MD,PM,EV].mat`, bike TAZ-to-TAZ demand matrix
      10. `ctramp_output\nonmotor_[EA,AM,MD,PM,EV]_WALK_[EA,AM,MD,PM,EV].mat`, walk TAZ-to-TAZ demand matrix
      11. `ctramp_output\other_[EA,AM,MD,PM,EV]_SCHLBUS_[EA,AM,MD,PM,EV].mat`, school bus TAZ-to-TAZ demand matrix
      12. `ctramp_output\transit_[EA,AM,MD,PM,EV]_KNR_SET_set[1,2,3]_[EA,AM,MD,PM,EV].mat`, kiss-and-ride TAP-to-TAP transit demand matrix sets
      13. `ctramp_output\transit_[EA,AM,MD,PM,EV]_PNR_SET_set[1,2,3]_[EA,AM,MD,PM,EV].mat`, park-and-ride TAP-to-TAP transit demand matrix sets
      14. `ctramp_output\transit_[EA,AM,MD,PM,EV]_WLK_SET_set[1,2,3]_[EA,AM,MD,PM,EV].mat`, walk to transit TAP-to-TAP transit demand matrix sets
    * Output:
      1. `ctramp_output\TAZ_Demand_[EA,AM,MD,PM,EV].mat`, TAZ-to-TAZ demand matrices for the time period with matrices 1-11 direct from input files.
      2. `ctramp_output\TAP_Demand_set[1,2,3]_[EA,AM,MD,PM,EV].mat`, TAP-to-TAP demand matrices for the time period and transit set

## Non Residential

1. [`nonres\IxForecasts.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/nonres/IxForecasts.job)
    * Summary: Creates Internal/External production/attraction matrices for the model year.  Growth rates are embedded in the script.
    * Input:
      1. [`nonres\ixDaily2006x4.may2208.new.mat`](https://github.com/MetropolitanTransportationCommission/travel-model-two-networks/blob/master/INPUT_tm2_2000/nonres/IXDaily2006x4.may2208.new.mat), base production/attraction matrix from Census journey-to-work data for 2006
      2. %MODEL_YEAR% in the environment
    * Output
      1. `nonres\ixDaily[%MODEL_YEAR%].tpp`, the internal/external daily P/A matrices.  Tables are: *ix_daily_da*, *ix_daily_sr2*, *ix_daily_sr3*, *ix_daily_total*

1. [`nonres\IxTimeOfDay.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/nonres/IxTimeOfDay.job)
    * Summary: Converts Internal/External daily production/attraction matrices to origin/destination trip matrices by time period.  Time period factors are embedded in the script.
    * Input: `nonres\ixDaily[%MODEL_YEAR%].tpp`, the internal/external daily P/A matrices
    * Output: `nonres\tripsIx[EA,AM,MD,PM,EV]x.tpp`, the internal/external trips for the given time period.  Tables are *DA*, *S2*, *S3*

1. [`nonres\IxTollChoice.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/nonres/IxTollChoice.job)
    * Summary: Applies a binomial choice model to drive alone, shared ride 2 and shared ride 3+ internal/external travel to determine of the traveler chooses the tolled path (if available) or non-tolled path.
    * Input: 
      1. `nonres\tripsIx[EA,AM,MD,PM,EV]x.tpp`, the internal/external trips for the given time period, with no distinction between toll/notoll trips
      2. `skims\HWYSKM[EA,AM,MD,PM,EV]_taz.tpp`, level of service matrices for autos
      3. `ctramp\scripts\block\hwyparam.block` for *SR2COSTSHARE* and *SR3COSTSHARE*
      4. `hwy\autoopcost.properties` for auto operating cost
    * Output:
      1. `nonres\tripIx[EA,AM,MD,PM,EV].tpp`, the internal/external trips for the given time period.  Tables are *DA*, *SR2*, *SR3*, *DATOLL*, *SR2TOLL*, *SR3TOLL*
  
