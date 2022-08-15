# Modeling Process

## Preprocessing

1. [`preprocess\preprocess_input_net.job`](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/scripts/preprocess/preprocess_input_net.job)
    * Summary: preprocesses input network to fix some existing attributes and add a new one.
    * Input:
        1. `hwy\complete_network.net` - the roadway network
        2. `hwy\interchange_nodes.csv` - the list of freeway links with distances
    * Output: `hwy\mtc_final_network_base.net`, the updated roadway network with a new DISTANCE attribute, fixed CNTYPE and FT attributes.

1. [`preprocess\writeZoneSystems.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/writeZoneSystems.job)
    * Summary: Counts tazs, mazs, taps and external zones based on [node number conventions](/travel-model-two/input/#county-node-numbering-system)
    * Input: `hwy\mtc_final_network_base.net`, the roadway network
    * Output: `zoneSystem.bat`, a local batch file that defines `TAZ_COUNT`, `TAZ_EXTS_COUNT`, `TAP_COUNT`, and `MAZ_COUNT` environment variables

1. [`preprocess\zone_seq_net_builder.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/zone_seq_net_builder.job)
    * Summary: Builds a sequential zone numbering system for TAZs, MAZs, TAPs and Externals
     given the [node number conventions](/travel-model-two/input/#county-node-numbering-system).
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

1. [`preprocess\renumber.py`](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/scripts/preprocess/renumber.py)
    * Summary: Renumbers the TAZ and MAZ labels in the households file.
    * Input:
        1. `popsyn\households.csv` - Households file input for renumbering
    * Output:
        1. `popsyn\households_renum.csv` - Output households file with renumbering

1. [`preprocessing\maz_densities.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/maz_densities.job)
    * Summary: Creates intermediate files for calculating maz densities: maz centroid location file and intersection location file.
    * Input: `hwy\mtc_final_network_base.net`, the roadway network
    * Output:
        1. `hwy\maz_nodes.csv`, the maz centroids and their coordinates
        2. `hwy\intersection_nodes.csv`, intersection nodes and their coordinates, where intersections are defined by having 5 non-freeway, non-connector links attached

1. [`preprocessing\createMazDensityFile.py`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/createMazDensityFile.py)
    * Summary: Calculates density-related columns to add to [Micro Zonal Data](/travel-model-two/guide/#micro-zonal-data)
    * Input:
        1. `hwy\maz_nodes.csv`, the maz centroids and their coordinates
        2. `hwy\intersection_nodes.csv`, intersection nodes and their coordinates
        3. `landuse\maz_data.csv` - [Micro Zonal Data](/travel-model-two/guide/#micro-zonal-data)
    * Output:
        1. `landuse\maz_density.csv` - Density measures for MAZs (TotInt, EmpDen, RetDen, DUDen, PopDen, intDenBin, empDenBin, duDenBin)
        2. `landuse\maz_data_withDensity.csv` - [Micro Zonal Data](/travel-model-two/guide/#micro-zonal-data) joined with density measures

1. [`preprocess\CreateNonMotorizedNetwork.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/preprocess/CreateNonMotorizedNetwork.job)
    * Summary: Create pedestrian, bicycle and pedestrian TAP (Transit Access Point) to TAP networks.  The procedure to create the non-motorized networks (walk and bike) extracts the links from the network which have **CNTYPE** equal to TANA, PED/BIKE, MAZ, TAZ, or TAP and which are not freeways, or which have the BIKEPEDOK flag set to true (1). For the pedestrian network, any link that is one-way has an opposite direction link generated.
    * Input:
        1. [`CTRAMP\scripts\block\maxCosts.block`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/block/maxCosts.block) - sets maximum pedestrian distance, maximum bike distances, maximum driving generalized cost, maximum tap-tap pedestrian distance
        2. `hwy\mtc_final_network.net`, the roadway network
    * Output:
        1. `hwy\mtc_ped_network.net`, the pedestrian network.  Link attributes are the same as the roadway network, plus **SP_DISTANCE**, or Shortest Path Distance.  This is set to:
            - `@max_ped_distance@` for **CNTYPE**=_MAZ_ links and **CNTYPE**=_TAP_ links with a TAZ/MAZ/TAP origin or destination,
            - `@nomax_bike_distance@` for _TAZ_ links
            - **FEET** otherwise
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
        - 0: regional core
        - 1: central business district
        - 2: urban business
        - 3: urban
        - 4: suburban
        - 5: rural

1. [`preprocess\setInterchangeDistance.job`](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/scripts/preprocess/setInterchangeDistance.job)
    * Summary: Preprocesses freeway link distances to add nearest major interchange distances. This script runs interchangeDistance.py script to calculate distances, write distances to CSV, convert to DBF, and merge into Cube network.
    * Input: `hwy\mtc_final_network_with_tolls.net` - roadway network with toll values
    * Output: `hwy\mtc_final_network_with_tolls.net` - Input network with added variables UPDIST and DOWNDIST in miles

1. [`preprocess\interchangeDistance.py`](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/scripts/preprocess/interchangeDistance.py)
    * Summary: Cube script are provides the interchange nodes and links. This script loops through links to determine shortest paths and calculate distances to interchanges.
    * Input: `hwy\fwy_links.csv` - Lists freeway links with their nodes, distance and FT attributes.
    * Output:`hwy\fwy_interchange_dist.csv`, a CSV file with columns
        1. A - Upstream node
        2. B - Downstream node
        3. FT - Facility type
        4. DISTANCE - Link distance
        5. INTXA - If 1, A is far node
        6. INTXB - If 1, B is far node
        7. downdist - Downstream distance
        8. updist - Upstream distance

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
    * **TODO**: This creates uses cube to create a bunch of cube scripts which I find pretty awkward. It also could do more parallelizing and is limited to 9 (one per county) at present. Use python to create the cubescript?  It would be easier to make flexible and run the pieces on an arbitrary number of nodes.
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
        2. `skims\ped_distance_tap_tap.txt`, the pedestrian TAP to TAP skims
        3. `hwy\avgload[EA,AM,MD,PM,EV].net`, the congested network (**TODO**: Is this generated with real congested times?  Currently, it's not, I don't think.)
    * Output:
        1. `hwy\mtc_transit_network_tap_to_node.txt`, mapping of renumbered nodes.
        2. `hwy\mtc_transit_network_[EA,AM,MD,PM,EV].net`, transit network with renumbered nodes, TAP first pseudo TAP nodes and links, and *TRANTIME* attribute from congested roadway link time.

1. [`skims\build_drive_access_skims.py`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/build_drive_access_skims.py)
    * Summary: Called by [`skims\TransitSkimsPrep.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/TransitSkims.job), below, this script creates drive access links from TAZs to TAPs.  This process involves:
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
    * Summary: Called by [`skims\TransitSkimsPrep.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/TransitSkims.job), below, this script outputs a list of TAPs and the lines that serve that TAP
    * Input:
        1. `trn\transitLines.lin`, the transit lines
        2. `hwy\mtc_final_network_tap_links.csv`, the TAP to node connectors
        3. `hwy\mtc_final_network_zone_seq.csv`, for translating between TAPs, MAZs, TAZs and their renumbered versions
    * Output: `trn\tapLines.csv` with the following columns:
        1. TAP: TAP (sequential numbering)
        2. LINES: space-delimited list of names of lines serving the TAP

1. [`skims\TransitSkimsPrep.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/TransitSkims.job)
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
            - COMPCOST: composite cost, including walk, wait, boarding transfer and in-vehicle time, and fares
            - IWAIT: average wait time incurred at the start of the trip for all attractive routes between zones
            - XWAIT: average actual wait incurred at the transfer points of all attractive routes between zones
            - XPEN: average actual transfer penalty for all attractive routes between zones
            - BRDPEN: the boarding penalties associated with transit legs of the trip
            - XFERS: the average number of transfers used by the attractive routes between zone pairs
            - FARE: the average fare, in monetary units, for all attractive routes between zones
            - XWTIME: transfer walk time
            - AEWTIME: acess/egress walk time
            - LB_TIME: local bus time
            - EB_TIME: express bus time
            - LR_TIME: light rail time
            - HR_TIME: heavy rail time
            - CR_TIME: commuter rail time
            - BEST_MODE: the "highest" mode with positive time, where commuter rail=5, heavy rail=4, light rail=3, express bus=2, local bus=1
        3. `trn\mtc_transit_lines_[EA,AM,MD,PM,EV]_SET[1,2,3]_with_transit.lin`
        4. `trn\mtc_transit_ntlegs_[EA,AM,MD,PM,EV]_SET[1,2,3]_with_transit.ntl`, nontransit legs file
        5. `trn\mtc_transit_ntlegs_[EA,AM,MD,PM,EV]_SET[1,2,3]_with_transit.rte`, enumerated routes
        6. `trn\mtc_transit_report_[EA,AM,MD,PM,EV]_SET[1,2,3]_with_transit.rpt`, reports from the route-enumeration and route-evaluation processes

1. [`skims\cube_to_emme_network_conversion.py`](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/scripts/skims/cube_to_emme_network_conversion.py)
    * Summary: Script to read in a Cube network shapefile and output EMME transaction files to load the network and attributes into EMME.
    * Input:
        1. `mtc_transit_network_[EA,AM,MD,PM,EV]_CONG_links.dbf` - congested network files from Cube in DBF format
        2. `transitLines.lin` - Cube's transit lines file with updated node numbering
        3. `vehtype.pts` - File providing vehicle types and their capacities
        4. `station_attribute_data_input.csv` - CSV file providing station attributes
    * Output:
        1. `emme_network_transaction_files_[EA,AM,MD,PM,EV]` - A folder for each time of day period containing all of the EMME transaction files
        2. `emme_network_transaction_files_[EA,AM,MD,PM,EV]\node_id_crosswalk.csv` - Node crosswalk files used for debugging between Cube and EMME
        3. `emme_network_transaction_files_[EA,AM,MD,PM,EV]\station_attributes` - Folder with station attribute files used for the parking capacity restraint model

1. [`skims\create_emme_network.py`](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/scripts/skims/create_emme_network.py)
    * Summary: Creates an EMME project folder and database, and creates a scenario for each time period. In each scenario, a network is created in accordance with the EMME transaction files generated by the cube_to_emme_network_conversion.py script.
    * Input:
        1. List of transaction files used from `emme_network_transaction_files_[EA,AM,MD,PM,EV]` folder:
            + `emme_modes.txt`
            + `emme_vehicles.txt`
            + `emme_network.txt`
            + `emme_extra_node_attributes.txt`
            + `emme_extra_link_attributes.txt`
            + `emme_transit_lines.txt`
            + `emme_extra_line_attributes.txt`
            + `emme_extra_segment_attributes.txt`
            + `emme_transit_time_function.txt`
            + `emme_extra_node_network_fields.txt`
            + `emme_extra_link_network_fields.txt`
            + `station_extra_attributes.txt`
            + `station_network_fields.txt`
            + `node_id_crosswalk.csv`
            + `station_attributes\station_tap_attributes.csv`
        2. `hwy\tap_to_pseudo_tap_xwalk.csv` - a crosswalk between TAPs and walk transfer nodes
    * Output:
        1. `mtc_emme` - EMME project folder with all time period scenarios

1. [`skims\skim_transit_network.py`](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/scripts/skims/skim_transit_network.py)
    * Summary: This script performs transit skimming and assignment for MTC TM2. Output skims are in OMX format and are used as input into the CT-RAMP model. Skimming and assignment is done with the EMME networks created in create_emme_network.py.
    * Input: `trn\mtc_emme` - EMME project and scenarios created by create_emme_network.py script
    * Output: `transit_skims_[EA,AM,MD,PM,EV].omx` - Transit skims created by EMME for each time period

## Core
* Summary: The series of behavioral models where households and persons make decisions that ultimately result in daily trips.
* Configuration:
        1. [`mtctm2.properties`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/runtime/mtctm2.properties) is the primary configuration file for all models

### [Accessibilities](https://github.com/BayAreaMetro/travel-model-two/blob/master/core/src/java/com/pb/mtctm2/abm/accessibilities/BuildAccessibilities.java)
Summary: All accessibility measures for are calculated at the MAZ level. The auto travel times and cost are TAZ-based and the size variables are MAZ-based. This necessitates that auto accessibilities be calculated at the MAZ level.
* UEC: [Accessibilities.xls](https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/model/Accessibilities.xls)
* Output: ```acc.output.file = /ctramp_output/accessibilities.csv```

### [Pre-Auto Ownership](https://github.com/BayAreaMetro/travel-model-two/blob/master/core/src/java/com/pb/mtctm2/abm/ctramp/HouseholdAutoOwnershipModel.java)

This step selects the preliminary auto ownership level for the household, based upon household demographic variables, household ‘4D’ variables, and destination-choice accessibility terms created in the *Accessibilities* sub-model (see above). This auto ownership level is used to create mode choice logsums for workers and students in the household, which are then used to select work and school locations in model **UsualWorkAndSchoolLocationChoice**. The auto ownership model is re-run (*AutoOwnership*) in order to select the actual auto ownership for the household, but this subsequent version is informed by the work and school locations chosen by the **UsualWorkAndSchoolLocationChoice** model. All other variables and coefficients are held constant between the two models, except for alternativespecific constants.

* UEC: [AutoOwnership.xls](https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/model/AutoOwnership.xls)
* Logfile: *event-ao.log*
* Output: ```read.pre.ao.filename = /ctramp_output/aoResults_pre.csv```

### [Work From Home Choice](https://github.com/BayAreaMetro/travel-model-two/blob/master/core/src/java/com/pb/mtctm2/abm/ctramp/MandatoryDestChoiceModel.java#L496)
Summary: The work from home choice model determines whether each worker works from home or not. It is a binary logit model.

* UEC: [TourDestinationChoice.xls](https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/model/TourDestinationChoice.xls), worksheet *workfromhome*
* Logfile: *event-tourDcMan.log*
* See: [WorkLocationChoiceModel.java](https://github.com/BayAreaMetro/travel-model-two/blob/master/core/src/java/com/pb/mtctm2/abm/ctramp/WorkLocationChoiceModel.java#L459)

### [Usual Work And School Location Choice](https://github.com/BayAreaMetro/travel-model-two/blob/master/core/src/java/com/pb/mtctm2/abm/ctramp/MandatoryDestChoiceModel.java#L129)

A workplace location choice model assigns a workplace MAZ for every employed person in the synthetic population who does not choose ‘works at home’ from the previous model. Every worker is assigned a regular work location zone (TAZ) and MAZ according to a multinomial logit destination choice model. Size terms in the model vary according to worker occupation, to reflect the different types of jobs that are likely to attract different workers. Each occupation category utilizes different coefficients for categories of employment by industry, to reflect the different likelihood of workers by occupation to work in each industry. Accessibility from the workers home to the alternative workplace is measured by a mode choice logsum taken directly from the tour mode choice model, based on peak period travel (A.M. departure and P.M. return). Various distance terms are also used.

Since mode choice logsums are required for each destination, a two-stage procedure is used for all destination choice models in the CT-RAMP system in order to reduce computational time (it would be computationally prohibitive to compute a mode choice logsum for over 40,000 MAZs and every tour). In the first stage, a simplified destination choice model is applied in which all TAZs are alternatives. The only variables in this model are the size term (accumulated from all MAZs in the TAZ) and distance. This model creates a probability distribution for all possible alternative TAZs (TAZs with no employment are not sampled). A set of alternatives are sampled from the probability distribution and, for each TAZ, a MAZ is chosen according to its size relative to the sum of all MAZs within the TAZ. These sampled alternatives constitute the choice set in the full destination choice model. Mode choice logsums are computed for these alternatives and the destination choice model is applied. A discrete choice of MAZ is made for each worker from this more limited set of alternatives. In the case of the work location choice model, a set of 30 alternatives is sampled.

The application procedure utilizes an iterative shadow pricing mechanism in order to match workers to input employment totals. The shadow pricing process compares the share of workers who choose each MAZ by occupation to the relative size of the MAZ compared to all MAZ. A shadow prices is computed which scales the size of the MAZ based on the ratio of the observed share to the estimated share. The model is re-run until the estimated and observed shares are within a reasonable tolerance. The shadow prices are written to a file and can be used in subsequent model runs to cut down computational time.

* UEC: [TourDestinationChoice.xls](https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/model/TourDestinationChoice.xls), worksheet *workLocation*
* ```uwsl.soa.uec.file = DestinationChoiceAlternativeSample.xls```
* ```work.soa.uec.file = TourDcSoaDistance.xls```
* ```univ.soa.uec.file = TourDcSoaDistanceNoSchoolSize.xls```
* ```hs.soa.uec.file = TourDcSoaDistanceNoSchoolSize.xls```
* ```gs.soa.uec.file = TourDcSoaDistanceNoSchoolSize.xls```
* ```ps.soa.uec.file = TourDcSoaDistanceNoSchoolSize.xls```
* Logfile: *event-tourDcMan.log*
* Output: ```Results.UsualWorkAndSchoolLocationChoice = /ctramp_output/wsLocResults.csv```


### [Transit Subsidy Model](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/TransitSubsidyAndPassModel.java)

The transit subsidy model determines whether a worker or student has their transit costs subsidized by their employer. This model was estimated using the MTC 2011 household travel survey and the coefficients for this model are shown in it's UEC file. Explanatory variables for this model include person type, industry code, and accessibility.

Once the transit subsidy model is run, if the worker or student has transit subsidized, it samples the percentage of the transit fare that is subsidized, and this percentage is used to factor the skimmed transit fare in the transit virtual path-builder.

* UEC: [TransitSubsidyAndPass.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/TransitSubsidyAndPass.xls), worksheet *Transit_subsidy*
* ```tt.subsidyPercent.file = transitSubsidyDistribution.csv```

### [Transit Pass Ownership Model](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/TransitSubsidyAndPassModel.java)

The transit pass ownership model is used to determines whether or not a person owns a transit pass. Unlike the transit subsidy model, it is applied to all persons. It predicts the probability of owning a transit pass with longer term length than one day. The model coefficients are provided in it's UEC file. Adults are more likely to own transit passes than children, and transit pass ownership is inversely related to household income. Workers who work in zones with better transit access compared to auto time and who have subsidized transit are more likely to own a transit pass. Workers in resource extraction, manufacturing, and other services are less likely to own a transit pass.

* UEC: [TransitSubsidyAndPass.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/TransitSubsidyAndPass.xls), worksheet *Transit_pass*

### [Post-Mandatory Car Ownership and Vehicle Type Choice Model](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/HouseholdAutoOwnershipModel.java)

The pre-mandatory car ownership model is described above. The model is re-run after work/school location choice, so that auto ownership can be influenced by the actual work and school location choices. The explanatory variables in the post-mandatory car ownership model include the ones listed above, with the addition of the following:
1. A variable measuring auto dependency for workers in the household based upon their home to work tour mode choice logsum
1. A variable measuring auto dependency for students in the household based upon their home to school tour mode choice logsum
1. A variable measuring the time on rail transit as a proportion of total transit time to work for workers in the household
1. A variable measuring the time on rail transit as a proportion of total transit time to school for students in the household

* UEC: [AutoOwnership.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/AutoOwnership.xls)
* Logfile: *event-ao.log*
* Output: ```Results.AutoOwnership = /ctramp_output/aoResults.csv```
* See: [HouseholdAutoOwnershipModel.java](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/HouseholdAutoOwnershipModel.java)

### [Transponder Ownership](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/TransponderChoiceModel.java)

The transponder ownership model predicts whether each household owns a toll transponder unit or not. It was originally estimated using aggregate transponder ownership data for San Diego. Although the model is implemented in Travel Model Two, transponder ownership is not currently used in any downstream models. If data becomes available to calibrate the model, and/or it is found that demand on managed lanes is over-estimated, transponder ownership can be introduced in mode choice to reduce or restrict access to managed lanes if a transponder is not available. Coefficients for the transponder ownership model are provided in it's UEC file.

* UEC: [TransponderOwnership.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/TransponderOwnership.xls)
* ```tc.choice.avgtts.file = /../input/ABMTEMP/ctramp/tc_avgtt.csv```
* Logfile: *event-tp.log*

### [Parking Provision Model](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/ParkingProvisionModel.java)

The parking provision model model predicts for each worker whose work MAZ is in a parking constrained area (PARKAREA 4) whether their parking is fully paid by their employer, partially subsidized, or not free/subsidized. The model coefficients are provided in it's UEC file. If the model predicts that the worker’s parking is partially subsidized, the percent subsidy is sampled from a lognormal distribution with mean -0.05 and standard deviation 0.54, capped at 1.0. The results from the model are used in the tour and trip mode choice utility calculations for work tours, where the parking cost in the destination MAZ is multiplied by 1-the reimbursement percentage or 0 if parking is fully provided.

* UEC: [ParkingProvision.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/ParkingProvision.xls)
* ```tc.choice.avgtts.file = /../input/ABMTEMP/ctramp/tc_avgtt.csv```
* Logfile: *event-fp.log*

### [Coordinated Daily Activity Pattern (CDAP) Model](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/HouseholdCoordinatedDailyActivityPatternModel.java)

This model predicts the main daily activity pattern (DAP) type for each household member. The activity types that the model considers are:
1. **Mandatory pattern (M)** that includes at least one of the three mandatory activities – work, university or school. This constitutes either a workday or a university/school day, and may include additional non-mandatory activities such as separate home-based tours or intermediate stops on the mandatory tours.
1. **Non-mandatory pattern (N)** that includes only maintenance and discretionary tours. Note that the way in which tours are defined, maintenance and discretionary tours cannot include travel for mandatory activities.
1. **At-home pattern (H)** that includes only in-home activities. At-home patterns are not distinguished by any specific activity (e.g., work at home, take care of child, being sick, etc.). Cases where someone is not in town (e.g., business travel) are also combined with this category.

The model also simultaneously predicts the presence of fully-joint tours for the household. Fully-joint tours are tours in which two or more household members travel together for all stops on the tour. Joint tours are only a possible alternative at the household level when two or more household members have an active (M or N) travel day.

* UEC: [CoordinatedDailyActivityPattern.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/CoordinatedDailyActivityPattern.xls)
* Logfile: *event-cdap.log, event-cdap-logsum.log, event-cdap-uec.log*

### [Individual Mandatory Tour Frequency](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/HouseholdIndividualMandatoryTourFrequencyModel.java)

Based on the DAP chosen for each person, individual mandatory tours, such as work, school and university tours are generated at person level. The model predicts the exact number and purpose of mandatory tours for each person who chose the mandatory DAP type at the previous decision-making stage. Since the DAP type model at the household level determines which household members engage in mandatory tours, all persons subjected to the individual mandatory tour model implement at least one mandatory tour. The model has the following five alternatives:
1. One work tour
1. One school tour
1. Two or more work tours
1. Two or more school tours
1. One work tour plus one school tour

Alternatives with work tours are only available to workers, while alternatives with school tours are only available to students.

DAPs and subsequent behavioral models of travel generation include various explanatory variables that relate to household composition, income, car ownership, location of work and school activities, land-use development, residential and employment density, and accessibility factors.

* UEC: [MandatoryTourFrequency.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/MandatoryTourFrequency.xls)
* Logfile: *event-TourFreq.log*

### [Individual Mandatory Tour Time of Day Choice](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/HouseholdIndividualMandatoryTourDepartureAndDurationTime.java)

After individual mandatory tours have been generated, the tour departure time from home and arrival time back at home is chosen simultaneously. The model is a discrete-choice construct that operates with tour departure-from-home and arrival-back-home time combinations as alternatives. The model has a temporal resolution of 30 minutes, but the first two hours (from 3 A.M. to 5 A.M.) and the last three hours (from 12 A.M. to 3 A.M.) are collapsed into one period each.

The model utilizes direct availability rules for each subsequently scheduled tour, to be placed in the residual time window left after scheduling tours of higher priority. This conditionality ensures a full consistency for the individual entire-day activity and travel schedule as an outcome of the model. The model utilizes household, person, and zonal characteristics, most of which are generic across time alternatives. However, network level-of-service (LOS) variables vary by time of day and are specified as alternative-specific based on each alternative’s departure and arrival time. Other explanatory variables used in mandatory tour scheduling models include:
1. Distance between home and the mandatory activity location
1. Person type
1. Household income
1. Gender
1. Age
1. Presence of other person types in household (beside the traveler)
1. Tour sequence information

* UEC: [TourDepartureAndDuration.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/TourDepartureAndDuration.xls)
* ```departTime.alts.file = DepartureTimeAndDurationAlternatives.csv```
* Logfile: *event-tod.log*

### [Generation of Joint Household Tours](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/JointTourModels.java)

In the CT-RAMP structure, joint travel for non-mandatory activities is modeled explicitly in the form of fully joint tours. Each fully joint tour is considered a modeling unit with a group-wise decision-making process for the primary destination, mode, frequency and location of stops.

A tour generation and composition stage that generates the number of joint tours by purpose/activity type made by the entire household. This is the joint tour frequency model. A tour participation stage at which the decision whether to participate or not in each joint tour is made for each household member and tour. Joint tour party composition is modeled for each tour. Travel party composition is defined in terms of person categories participating in each tour. Person participation choice is then modeled for each person sequentially

* UEC: [JointTourFrequency.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/JointTourFrequency.xls), worksheet *31_Frequency_Party_Composition*
* ```jtfcp.alternatives.file = JointAlternatives.csv```

### [Joint Tour Participation](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/JointTourModels.java)

Joint tour participation is modeled for each person and each joint tour. If the person does not correspond to the composition of the tour determined in the joint tour composition model, they are ineligible to participate in the tour. Persons whose daily activity pattern type is home are excluded from participating. A tour starts with no participants. After all persons in the household have made their participation choice, the software checks to see whether the party type constraint is met. For example, on an adults-only tour, at least two household adults must participate. On a children-only tour, at least two children must participate. On mixed tour, at least one household child and one household adult must participate. Explanatory variables include the person type of the decision-maker, the maximum pair-wise overlaps between the decision-maker and other household members of the same person type (adults or children), household and person variables, and urban form variables.

* UEC: [JointTourFrequency.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/JointTourFrequency.xls), worksheet *32_Person_participation*
* ```jtfcp.alternatives.file = JointAlternatives.csv```

### [Joint Tour Primary Destination Choice](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/JointTourModels.java)

The joint tour primary destination choice model determines the location of the tour primary destination. The destination is chosen for the tour and assigned to all tour participants. The model works at a microzone level, and sampling of destination alternatives is implemented in order to reduce computation time.    Explanatory variables include household and person characteristics, the tour purpose, logged size variables, round-trip mode choice logsum, distance, and other variables. There are no separate destination choice models for joint tours, it is done under Individual Non-Mandatory Tour Destination Choice, below.

### [Joint Tour Time of Day Choice](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/JointTourModels.java)

After joint tours have been generated and assigned a primary location, the tour departure time from home and arrival time back at home is chosen simultaneously. A unique condition applies when applying the time-of-day choice model to joint tours. That is, the tour departure and arrival period combinations are restricted to only those available for each participant on the tour, after scheduling mandatory activities. Once the tour departure/arrival time combination is chosen, it is applied to all participants on the tour. The joint tour time-of-day choice models use the same coefficients as individual non-mandatory tour time of day choice models.

### [Individual Non-Mandatory Tour Frequency](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/HouseholdIndividualNonMandatoryTourFrequencyModel.java)

Individual non-mandatory tours include escort, shopping, other maintenance, eat out, visit, and other discretionary tours. The choices include the number (0-2+) and type of tours generated by each of the non-mandatory tour purposes. The explanatory variables include:
1. Auto sufficiency
1. Household income
1. Dwelling type
1. Number of full time workers in household
1. Number of part time workers in household
1. Number of university students in household
1. Number of non-workers in household
1. Number of retirees in household
1. Number of driving age school children in household
1. Number pre-driving age school children in household
1. Number of preschool children in household
1. Number of adults in household not staying home
1. Number of children in household not staying home
1. Gender
1. Age
1. Education level
1. Indicator variable for whether person works at home regularly
1. Number of individual/joint tours per person by tour purpose
1. Population density at the origin
1. Work Accessibility from household MAZ to employment
1. School Accessibility from household MAZ to employment
1. Escorting HOV Accessibility from household MAZ to employment
1. Shopping SOV/HOV Accessibility from household MAZ to employment
1. Maintenance SOV/HOV Accessibility from household MAZ to employment
1. Eating Out SOV/HOV Accessibility from household MAZ to employment
1. Walk Accessibility from household MAZ to non-mandatory activities



* UEC: [NonMandatoryIndividualTourFrequency.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/NonMandatoryIndividualTourFrequency.xls)
* ```inmtf.FrequencyExtension.ProbabilityFile = IndividualNonMandatoryTourFrequencyExtensionProbabilities_p1.csv```
* ```IndividualNonMandatoryTourFrequency.AlternativesList.InputFile = IndividualNonMandatoryTourFrequencyAlternatives.csv```
* Logfile: *event-TourFreq.log*

### [Individual Non-Mandatory Tour Primary Destination Choice](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/NonMandatoryDestChoiceModel.java)

The individual non-mandatory tour primary destination choice model determines the location of the tour primary destination. The model works at a zone level, and sampling of destination alternatives is implemented in order to reduce computation time. Explanatory variables include household and person characteristics, the tour purpose, logged size (i.e. attraction) variables, round-trip mode choice logsum, distance, and other variables.  

* UEC: [TourDestinationChoice.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/TourDestinationChoice.xls)
* ```nmdc.soa.uec.file = DestinationChoiceAlternativeSample.xls```
* Logfile: *event-tourDcNonMan.log*

### [Individual Non-Mandatory Tour Time of Day Choice](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/NonMandatoryTourDepartureAndDurationTime.java)

After individual non-mandatory tours have been generated and assigned a primary location, the tour departure time from home and arrival time back at home is chosen simultaneously. The tour departure and arrival period combinations are restricted to only those available, after scheduling individual mandatory tours and joint tours. Joint tour availability windows consider available time windows for all tour participants. Individual non-mandatory tour time-of-day choice coefficients are stratified by the specific tour purpose.

* UEC: [TourDepartureAndDuration.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/TourDepartureAndDuration.xls)
* ```departTime.alts.file = DepartureTimeAndDurationAlternatives.csv```

### [At-Work Sub-Tour Frequency](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/HouseholdAtWorkSubtourFrequencyModel.java)

Work-based sub-tours are modeled last and are relevant only for those persons who implement at least one work tour. These underlying activities are mostly individual (e.g., business-related and dining-out purposes), but may include some household maintenance functions as well as person and household maintenance tasks. There are six alternatives in the model, corresponding to the most frequently observed patterns of at-work sub-tours. The alternatives are:
1. One eat-out
1. One business
1. One maintenance
1. Two business
1. Two maintenance
1. One eat-out and one business

The alternatives define both the number of at-work sub-tours and their purpose. Explanatory variables include household and person attributes, duration of the parent work tour, the number of joint and individual non-mandatory tours already generated in the day, and accessibility and urban form variables.

* UEC: [AtWorkSubtourFrequency.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/AtWorkSubtourFrequency.xls)
* Logfile: *event-TourFreq.log*

### [At-Work Sub-Tour Primary Destination Choice](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/SubtourDestChoiceModel.java)

The at-work sub-tour primary destination choice model determines the location of the tour primary destination. The model works at a microzone level, and sampling of destination alternatives is implemented in order to reduce computation time.    Explanatory variables include household and person characteristics, the tour purpose, logged size variables, round-trip mode choice logsum, distance, and other variables.

* UEC: [TourDestinationChoice.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/TourDestinationChoice.xls)
* ```nmdc.soa.uec.file = DestinationChoiceAlternativeSample.xls```
* Logfile: *event-tourDcNonMan.log*

### [At-Work Sub-Tour Time of Day Choice](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/SubtourDepartureAndDurationTime.java)

After at-work sub-tours have been generated and assigned a primary location, the tour departure time from workplace and arrival time back at the workplace is chosen simultaneously. The tour departure and arrival period combinations are restricted to only those available based on the time window of the parent tour.

* UEC: [TourDepartureAndDuration.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/TourDepartureAndDuration.xls)
* ```departTime.alts.file = DepartureTimeAndDurationAlternatives.csv```

### [Vehicle Type Choice Model](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/TourVehicleTypeChoiceModel.java)

Prior to running tour mode choice, this model is run which determines whether the auto that would be used for the tour is either a human-driven vehicle or an autonomous vehicle. This model is only relevant for households that chose one of the auto ownership alternatives with both a human-driven and an autonomous vehicle sub-option. The model was asserted such that the probability of using an autonomous vehicle is equal to the share of autonomous to human-driven vehicles in the household, multiplied by a “probability boost” of 1.2 under the assumption that all else being equal, a household member would prefer to use the autonomous vehicle 20% more than a human-driven vehicle. If an autonomous vehicle is assumed to be used for the tour, than the autonomous vehicle variables and coefficients are applied at the tour and trip mode choice level for this tour.

### [Tour Mode Choice Model](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/TourModeChoiceModel.java)

This model determines the “main tour mode” used to get from the origin to the primary destination and back to origin. The tour-based modeling approach requires a certain reconsideration of the conventional mode choice structure. Instead of a single mode choice model pertinent to a four-step structure, there are two different levels where the mode choice decision is modeled: Tour mode level and Trip mode level.

The tour mode level can be thought of as a mode preference model, while the trip mode choice model can be thought of as a mode switching model. Tour mode choice is used to constrain stop location choice as well as trip mode choice. The modes for both models are the same, but the higher level of the nesting structure constrains lower level decisions.

The tour mode choice model is based on the round-trip level-of-service (LOS) between the tour anchor location (home for home-based tours and work for at-work sub-tours) and the tour primary destination. The tour mode is chosen based on LOS variables for both directions according to the time periods for the tour departure from the anchor and the arrival back at the anchor. This is one of the fundamental advantages of the tour-based approach. The appropriate skim values for the tour mode choice are a function of the MAZ of the tour origin and MAZ of the tour primary destination. The primary drivers are in-vehicle time, other travel times, cost, characteristics of the destination zone such as CBD, demographics, and the household’s level of auto ownership compared to number of workers in the household. Transit utilities are treated specially in Travel Model Two, as described below. The wait time for taxi and TNC is sampled from a distribution whose mean and standard deviation varies according to density.

* UEC: [TourModeChoice.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/TourModeChoice.xls)
* Logfile: *event-tourMcMan.log*

### [Intermediate Stop Frequency Model](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/StopFrequencyModel.java)

The stop frequency choice model determines the number of intermediate stops on the way to/from the primary destination up to a maximum of 3 per direction, for a total of 8 trips per tour (four on each tour leg). However, for many tour purposes, the number of intermediate stops observed in the data is significantly less than 3 per direction.  

Stop frequency is based on a number of explanatory variables, including household and person attributes, the duration of the tour, the distance from the tour anchor to the primary destination, and accessibility and urban form variables.

Once the number of intermediate stops is determined, each intermediate stop is assigned a purpose based on a frequency distribution created from observed data.  The distribution is segmented by tour purpose, tour direction, and person type and is based on survey data summaries. Work tours are also segmented by departure or arrival time period.  

* UEC: [StopFrequency.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/StopFrequency.xls)
* ```stf.purposeLookup.proportions = StopPurposeLookupProportions.csv```
* Logfile: *event-StopFreq.log*

### [Intermediate Stop Location Choice Model](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/IntermediateStopChoiceModels.java)

The stop location choice model predicts the location of stops along the tour other than the primary destination. The stop-location model is structured as a multinomial logit model using a zone attraction size variable and route deviation measure as impedance. The alternatives are sampled from the full set of zones, subject to availability of a zonal attraction size term. The sampling mechanism is also based on accessibility between tour origin and primary destination and is subject to certain rules based on tour mode. All destinations are available for auto tour modes, so long as there is a positive size term for the zone.

The intermediate stop location choice model works by cycling through stops on tours. The level-of-service variables are calculated as the additional utility between the last location and the next known location on the tour. Intermediate stop location choice model parameters, segmented by tour purpose. Stop location choice model size terms are segmented by the purpose of the stop. They are consistent with size terms by purpose used for tour destination choice.


* UEC: [StopLocationChoice.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/StopLocationChoice.xls)
* ```slc.alts.file = SlcAlternatives.csv```
* ```slc.soa.uec.file = SlcSoaSize.xls```
* Logfile: *event-StopLoc.log*

### [Trip Departure Time Model]()

The stop departure time model simulates the half-hour departure time for each outbound trip on a tour, or the half-hour arrival time for each inbound trip on a tour, based on a lookup of probabilities by tour purpose, inbound versus outbound indicator, tour departure hour, and stop index. These probabilities are created from survey data.

### [Trip Mode Choice Model](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/core/src/java/com/pb/mtctm2/abm/ctramp/TripModeChoiceDMU.java)

The trip mode choice model determines the mode for each trip along the tour. Trip modes are constrained by the main tour mode. The linkage between tour and trip levels is implemented through correspondence rules between tour and trip modes. The model can incorporate asymmetric mode combinations, but in reality, there is a great deal of symmetry between outbound and inbound modes used for the same tour.

In the trip mode choice model, the trip modes are exactly the same as the modes in the tour mode choice model. The correspondence rules depend on a kind of hierarchy, which is similar to that used for the definition of transit modes. The hierarchy is based on the following principles:
1. The auto occupancy of the tour mode is determined by the maximum occupancy across all auto trips that make up the tour. Therefore, the auto occupancy for the tour mode is the maximum auto occupancy for any trip on the tour.
1. Transit tours can include auto shared-ride trips for particular legs.  Therefore, ‘casual carpool’, wherein travelers share a ride to work and take transit back to the tour origin, is explicitly allowed in the tour/trip mode choice model structure.
1. The walk mode is allowed for any trip on a tour except for drive-alone, wherein the driver must use the vehicle for all trips on the tour.
1. The transit mode of the tour is determined by the highest transit mode used for any trip in the tour according to the transit mode hierarchy.
1. Shared-ride modes are also available in transit tours, albeit with a low probability.

The trip mode choice models explanatory variables include household and person variables, level-of-service between the trip origin and destination according to the time period for the tour leg, urban form variables, and alternative-specific constants segmented by tour mode.  

* UEC: [TripModeChoice.xls](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/model/TripModeChoice.xls)
* Logfile: *event-tripMc.log*


### Merge Auto Demand Matrices

1. [`assign\merge_auto_matrices.s`](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/scripts/assign/merge_auto_matrices.s)
    * Summary: This script combines the trip matrices from CTRAMP that are segmented by individual mode into a single matrix file while keeping each mode separate.
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
    * Output:
        1. `ctramp_output\TAZ_Demand_[EA,AM,MD,PM,EV].mat`, TAZ-to-TAZ demand matrices for the time period with matrices 1-11 direct from input files.


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
    * Output: `nonres\tripsIx[EA,AM,MD,PM,EV].tpp`, the internal/external trips for the given time period.  Tables are *DA*, *S2*, *S3*

1. [`nonres\IxTollChoice.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/nonres/IxTollChoice.job)
    * Summary: Applies a binomial choice model to drive alone, shared ride 2 and shared ride 3+ internal/external travel to determine of the traveler chooses the tolled path (if available) or non-tolled path.
    * Input:
        1. `nonres\tripsIx[EA,AM,MD,PM,EV]x.tpp`, the internal/external trips for the given time period, with no distinction between toll/notoll trips
        2. `skims\HWYSKM[EA,AM,MD,PM,EV]_taz.tpp`, level of service matrices for autos
        3. `ctramp\scripts\block\hwyparam.block` for *SR2COSTSHARE* and *SR3COSTSHARE*
        4. `hwy\autoopcost.properties` for auto operating cost
    * Output:
        1. `nonres\tripIx[EA,AM,MD,PM,EV].tpp`, the internal/external trips for the given time period.  Tables are *DA*, *SR2*, *SR3*, *DATOLL*, *SR2TOLL*, *SR3TOLL*

## Assignment

1. [`assign\build_and_assign_maz_to_maz_auto.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/assign/build_and_assign_maz_to_maz_auto.job)
    * Summary: Assigns short auto trips to highway network using MAZ centroids based on shortest paths.
    * Input:  
        1. `hwy\avgload@token_period@.net`, TAZ output network for skimming by time period
        2. [`hwy\hwyParam.block`](https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/scripts/block/hwyParam.block), highway assignment generalized cost parameters
        3. `MAZ_Demand_[MAZSET]_[EA,AM,MD,PM,EV].mat`, MAZ to MAZ auto demand for each local network
    * Output:
        1. `maz_preload_[EA,AM,MD,PM,EV].net`, Network by time period with link attribute MAZMAZVOL for copying over to the TAZ to TAZ highway assignment    

2. [`scripts\assign\HwyAssign.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/assign/hwyassign.job)
    * Summary: Assigns trips to highway network using TAZ centroids and equilibrium capacity restraint assignment. Uses trimmed highway network which excludes lower-functional class links to improve runtime.
    * Input:
        1. [`block\hwyParam.block`](https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/scripts/block/hwyParam.block), highway assignment generalized cost parameters
        2. [`block\SpeedCapacity_1hour.block`](https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/scripts/block/SpeedCapacity_1hour.block), speed-capacity table
        3. [`block\FreeFlowSpeed.block`](https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/scripts/block/FreeFlowSpeed.block), free-flow speed table
        4. [`block\SpeedFlowCurve.block`](https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/scripts/block/SpeedFlowCurve.block), volume-delay functions
        5. `hwy\avgload[EA,AM,MD,PM,EV]_taz.net`, highway network for assignment
        6. `ctramp_output\TAZ_Demand_[EA,AM,MD,PM,EV].mat`, household travel demand
        7. `nonres\tripsIx[EA,AM,MD,PM,EV].tpp`, internal-external travel demand
        8. `nonres\tripsTrk[EA,AM,MD,PM,EV].tpp`, commercial vehicle travel demand
        9. `nonres\tripsAirPax[EA,AM,MD,PM,EV].mtx`, airport travel demand
    * Output:
        1. `hwy\load[EA,AM,MD,PM,EV].net`, loaded highway network

3. [`scripts\assign\AverageNetworkVolumes.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/assign/averagenetworkvolumes.job)
    * Summary: Compute the weighted average of roadway volumes for successive iterations of the entire model stream.  The iteration weights are set in the primary model stream file, RunModel. This script averages the volumes from the current iteration with the averaged volumes for ALL previous iterations. This method of successive averages "forces" model convergence.
    * Input:
        1. `hwy\msaload[EA,AM,MD,PM,EV]_taz.net`, an MSA network used to store averaged volumes for all previous iterations
        2. `hwy\load[EA,AM,MD,PM,EV].net`, the loaded highway network from the current iteration
    * Output:
        1. `hwy\msaload[EA,AM,MD,PM,EV]_taz.net`, the new MSA network with averaged volumes for all iterations including the current iteration

4. [`scripts\assign\CalculateAverageSpeed.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/assign/calculateaveragespeed.job)
    * Summary: Computes the speeds from a highway network with successively averaged roadway volumes.
    * Input:
        1. [`block\hwyParam.block`](https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/scripts/block/hwyParam.block), highway assignment generalized cost parameters
        2. [`block\SpeedCapacity_1hour.block`](https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/scripts/block/SpeedCapacity_1hour.block), speed-capacity table
        3. [`block\FreeFlowSpeed.block`](https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/scripts/block/FreeFlowSpeed.block), free-flow speed table
        4. [`block\SpeedFlowCurve.block`](https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/scripts/block/SpeedFlowCurve.block), volume-delay functions
        5. `hwy\msaload[EA,AM,MD,PM,EV]_taz.net`, the new MSA network with averaged volumes for all iterations including the current iteration
    * Output:
        1. `hwy\avgload[EA,AM,MD,PM,EV]_taz.net`, a highway network with congested speeds according to MSA volumes by period

5. [`scripts\assign\MergeNetworks.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/assign/mergenetworks.job)
    * Summary: Merges time-period-specific assignment results into a single TP+ and CSV network. The combined network is not used by the model stream. Variables are first given time-period-specific names in the first step of the script and then the five networks are merged. Daily volumes, delay, vehicle-miles traveled, and vehicle-hours traveled calculations are performed. Note that delay is computed as the difference between congested time and free-flow time.
    * Input:
        1. `hwy\msaload[EA,AM,MD,PM,EV]_taz.net`, highway networks with congested speeds according to MSA volumes by period
        2. `hwy\msa[EA,AM,MD,PM,EV]_speeds.csv`, a comma-separated value file of speeds
    * Output:
        1. `hwy\msamerge[ITERATION].net`, a merged network with assignment data for all time periods
        2. `hwy\msamerge[ITERATION].csv`, a comma-separated value dump of the above network

6. [`skims\HwySkims.job`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/skims/HwySkims.job)
    * Summary: If another iteration is to be run, this script creates new roadway skims.
    * Input:
        1. [`CTRAMP\scripts\block\hwyparam.block`](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/block/hwyparam.block) for value of time
        2. `hwy\autoopcost.properties`, auto and truck operating costs
        3. `hwy\avgload[EA,AM,MD,PM,EV]_taz.net`, the per-timeperiod roadway networks with renumbered nodes
    * Output:
        1. `skims\HWYSKM[EA,AM,MD,PM,EV]_taz.tpp`, level of service matrices for autos
        2. `skims\COM_HWYSKIM[EA,AM,MD,PM,EV]_taz.tpp`, level of service matrices for commercial vehicles
        3. `logs\HwySkims.debug`, a debug log file for a trace origin/destination


7. [`skims\cube_to_emme_network_conversion.py`](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/scripts/skims/cube_to_emme_network_conversion.py)
    * Summary: Script to read in a Cube network shapefile and output updated EMME transaction files to load the network and attributes into EMME.
    * Input:
        1. `mtc_transit_network_[EA,AM,MD,PM,EV]_CONG_links.dbf` - congested network files from Cube in DBF format
        2. `transitLines.lin` - Cube's transit lines file with updated node numbering
        3. `vehtype.pts` - File providing vehicle types and their capacities
        4. `station_attribute_data_input.csv` - CSV file providing station attributes
    * Output:
        1. `emme_network_transaction_files_[EA,AM,MD,PM,EV]` - A folder for each time of day period containing all of the EMME transaction files
        2. `emme_network_transaction_files_[EA,AM,MD,PM,EV]\node_id_crosswalk.csv` - Node crosswalk files used for debugging between Cube and EMME
        3. `emme_network_transaction_files_[EA,AM,MD,PM,EV]\station_attributes` - Folder with station attribute files used for the parking capacity restraint model

8. [`skims\create_emme_network.py`](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/scripts/skims/create_emme_network.py)
    * Summary: Updates the EMME project folder and database with congested links times. In each scenario, a the network is updated in accordance with the updated EMME transaction files generated by the cube_to_emme_network_conversion.py script.
    * Input:
        1. List of transaction files used from `emme_network_transaction_files_[EA,AM,MD,PM,EV]` folder:
            + `emme_extra_link_attributes.txt`
            + `emme_extra_segment_attributes.txt`
        2. `hwy\tap_to_pseudo_tap_xwalk.csv` - a crosswalk between TAPs and walk transfer nodes
    * Output:
        1. `mtc_emme` - EMME project folder with all time period scenarios

9. [`skims\skim_transit_network.py`](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/scripts/skims/skim_transit_network.py)
    * Summary: This script performs transit skimming and assignment for MTC TM2. Skimming and assignment is done with the EMME networks created in create_emme_network.py while including demand matrices from prior CT-RAMP runs. Output skims are in OMX format and are used as input into the next iteration of CT-RAMP model. For first inner iteration, the skimming and assignment is done for all time periods, otherwise it is only done for AM and PM periods.
    * Input:
        1. `trn\mtc_emme` - EMME project and scenarios created by create_emme_network.py script
        2. `ctramp_output\transit_[EA,AM,MD,PM,EV]_[WLK,PNR,KNRPRV,KNRTNC]_TRN_set[1,2,3]_[EA,AM,MD,PM,EV].omx` -
    * Output:
        1. `skims\transit_skims_[EA,AM,MD,PM,EV].omx` -
        2. `boardings_by_line_[EA,AM,MD,PM,EV].csv` - Transit skims created by EMME for each time period
        3. `boardings_by_segment_[EA,AM,MD,PM,EV].csv` -

10. [`CTRAMP\runtime\runTransitPathRecalculator.cmd`](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/runtime/runTransitPathRecalculator.cmd): Run the best transit path recalculator considering the transit capacity constraints and congested link times from prior skimming. After recalculating transit paths, the model runs skim_transit_network.py script one more time to resimulate the transit skimming and assignment over congested network.

## Cleaning & Generating Visualizer

1. Move all TP+ printouts to `\logs` folder and delete all temporary TP+ printouts and cluster files
2. [`CTRAMP\scripts\visualizer\generateDashboard.bat`](https://github.com/BayAreaMetro/travel-model-two/blob/transit-ccr/model-files/scripts/visualizer/generateDashboard.bat) - Batch file to generate the visualizer with data from final iteration
