---
layout: page
title: Network QA
---
# February 2022 Network QA

## 2015 Networks

Currently, these include the 2015 roadway network, TM2 MAZs and TAZs.  The 2015 transit networks will be added soon.

* [Geodatabase on Box](https://mtcdrive.box.com/s/j0gd3suiefdlebkn6v2jpws87aq3cmec) - Right click on model_net.gdb and select 'Download'
* Alameda [web map](https://mtc.maps.arcgis.com/home/webmap/viewer.html?webmap=d21c975d3b384e2c8a8e3ee6b4a4fd52)
* Contra Costa [web map](https://arcg.is/0zy0zq)
* Marin web map
* Napa [web map](https://arcg.is/1einHf)
* San Francisco web map
* San Mateo web map
* Santa Clara: a [view-only web map](https://arcg.is/1rzbCL0) (no login required); and an [editable web map](https://arcg.is/1POXza) (login required)
* Solano web map
* Sonoma web map

## Resources

* [Roadway Network Documentation](/travel-model-two/input/#roadway-network) including node and link attributes
* [Network Rebuild Requirements](https://mtcdrive.box.com/s/mrunshse2ygf7sfvkt695gzshfpascz5) - pdf document on Box
* GitHub repositories related to network tools:
  * [BayAreaMetro/travel-model-two-networks](https://github.com/BayAreaMetro/travel-model-two-networks/tree/develop)
  * [BayAreaMetro/network_wrangler](https://github.com/BayAreaMetro/network_wrangler/tree/generic_agency)
  * [BayAreaMetro/Lasso](https://github.com/BayAreaMetro/Lasso/tree/mtc_parameters)

## Known Issues

### Managed Laned offset rendering problem.

Managed lanes are coded as a link attribute in the standard network, so when modeled networks are created, they are generated as parallel links to the mainline.  However, the process that creates the shapefile version offsets the links in a manner that is inconsistent with the generation of the nodes, resulting in a visualization of these lanes which appears to be disconnected.  However, this is a rendering problem only, and the actual modeled network does not have this issue -- just the shapefile version.

## Frequently Asked Questions (FAQs)

TBD.  Please email [Flavia](mailto:ftsang@bayareametro.gov) with any questions you encounter while reviewing networks.
