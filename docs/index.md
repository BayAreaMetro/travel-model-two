# Travel Model Two

Travel Model Two, currently under development, is an important extension of Travel Model One. Fundamental to the foundation of Travel Model Two is the use of a wide ranging set of on-board transit rider surveys as well as the California Household travel survey, which obtained a statistical larger sample in the nine-county Bay Area.

## Changes from Travel Model One
Important travel behavior enhancements in Travel Model Two include:

*	A much more detailed spatial representation of transportation system supply including an accurate all-streets network for entire 9-county Bay Area, pedestrian paths\sidewalks from OpenStreetMap, bicycle facilities from MTC’s BikeMapper, and transit networks from MTC’s RTD network
*	Land-use and demographic forecast integration with [Bay Area UrbanSim Two](https://github.com/BayAreaMetro/bayarea_urbansim) represented at a 40,000 micro-analysis zone (MAZ) level
*	Detailed transit access/egress based on actual origin/destinations at the MAZ level considering boarding and alighting at specific transit stops allowing for a more accurate representation of walk times
*	More detailed temporal resolution using half-hourly time windows compared to hourly time windows in Travel Model One
* The effects of transit capacity and crowding
*	More detailed auto assignments, most notably with the loading of short trips to local streets
* The inclusion of Taxis and Transportation Network Companies (TNCs) such as Uber and Lyft as a mode choice option
* Representation of Automated Vehicles

## Versions

* TM2.0: Initial TM2 with Cube, CTRAMP core, 3-zone system. In use by TAM (Marin)
* TM2.1: TM2 with transit CCR implemented in Emme (uses Cube and Emme), CTRAMP core. Anticipated release: Summer 2022. This work is being performed in the branch [transit-ccr](https://github.com/BayAreaMetro/travel-model-two/tree/transit-ccr) -- **these docs are for this version**
* TM2.2: TM2 with Emme only (No Cube), CTRAMP core. This work is being performed in the [tm2py repository](https://github.com/BayAreaMetro/tm2py)
* TM2.3: TM2 with Emme only and ActivitySim core.

## References
* [Travel Model One documentation wiki](https://github.com/BayAreaMetro/modeling-website/wiki/TravelModel)
* [Travel Model One github repo](https://github.com/BayAreaMetro/travel-model-one)
