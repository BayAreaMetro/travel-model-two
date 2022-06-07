# TM2 Network QA

## 2015 Networks

* Geodatabase - Includes all counties. Right click on model_net.gdb and select 'Download'
  * [2022 02 01 release](https://mtcdrive.box.com/s/j0gd3suiefdlebkn6v2jpws87aq3cmec) - Includes only the 2015 roadway network
  * [2022 03 01 release](https://mtcdrive.box.com/s/y0p4twyu3nkm1rg4u6vk6miksvzduhuf) - Includes the 2015 roadway network, nodes and transit links; also included a [managed lane correction](https://github.com/BayAreaMetro/travel-model-two-networks/issues/53)

* [Travel Analysis Zones (TAZ) and Micro-Analysis Zones (MAZ)](https://mtcdrive.app.box.com/folder/157365053902?s=xpwx5kl55acdceha9ol7vhhrqlyjlsx6) - Helpful for reviewing centroid connectors

* ArcGIS Online web maps - available upon request:  

  * [Alameda](https://mtc.maps.arcgis.com/home/webmap/viewer.html?webmap=d21c975d3b384e2c8a8e3ee6b4a4fd52)
  * Contra Costa
  * Marin
  * Napa
  * San Francisco
  * San Mateo
  * Santa Clara
  * Solano
  * Sonoma

## Resources

* [Roadway Network Documentation](../input/#roadway-network) including node and link attributes
* [Network Rebuild Requirements](https://mtcdrive.box.com/s/mrunshse2ygf7sfvkt695gzshfpascz5) - pdf document on Box
* GitHub repositories related to network tools:
  * [BayAreaMetro/travel-model-two-networks](https://github.com/BayAreaMetro/travel-model-two-networks/tree/develop)
  * [BayAreaMetro/network_wrangler](https://github.com/BayAreaMetro/network_wrangler/tree/generic_agency)
  * [BayAreaMetro/Lasso](https://github.com/BayAreaMetro/Lasso/tree/mtc_parameters)

## Known Issues

* [Managed Lane offset rendering problem](https://github.com/BayAreaMetro/travel-model-two-networks/issues/57)
* [Link shapes do not represent direction in point order of polyline](https://github.com/BayAreaMetro/travel-model-two-networks/issues/56)
* [Roadway links missing names (and freeway links missing route direction)](https://github.com/BayAreaMetro/travel-model-two-networks/issues/58)
* [Freeway names are not useful, missing route num](https://github.com/BayAreaMetro/travel-model-two-networks/issues/55)
* [num_lanes comprises of GP,HOV,ML,etc](https://github.com/BayAreaMetro/travel-model-two-networks/issues/62)

## Frequently Asked Questions (FAQs)

TBD.  Please email [Flavia](mailto:ftsang@bayareametro.gov) with any questions you encounter while reviewing networks.
