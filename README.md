travel-model-two
================

Development plan:

* [**TM2.0**](https://github.com/BayAreaMetro/travel-model-two/releases/tag/TM2.0): Initial TM2 with Cube, CTRAMP core, 3-zone system. In use by TAM.
* [**TM2.1**](https://github.com/BayAreaMetro/travel-model-two/tree/TM2.1): TM2 with transit CCR (capacity, crowding, reliability) implemented in Emme (uses Cube _and_ Emme), CTRAMP core. This version was never used due to the complexity involved 
* **TM2.2**: TM2 with Emme only (not Cube). CTRAMP core.  This work is being performed in [the tm2py repository](https://github.com/BayAreaMetro/tm2py) so files outside of the CTRAMP core have been removed from this repo. This work is being done in [**master**](https://github.com/BayAreaMetro/travel-model-two)
* **TM2.3**: TM2 with Emme only and ActivitySim core. This work is also in progress in [ActivitySim / BayDAG](https://github.com/BayAreaMetro/activitysim/tree/BayDAG)
Currently in development.

## Relevant Repositories
The software needed to implement TM2.2 and above is spread across multiple repositories. The organization is as follows:

1. `tm2py`: A Python package that implements TM2. Please see this repository for installation instructions and usage.
2. `travel-model-two`: This repository. It contains the Java software and compilation instructions for implementing the resident passenger component of the TM2.2 system. 
3. `travel-model-two-configs`: A repository to house specific configurations of the TM2.2 system. For example, the configurations needed to simulate the 2015 base year will live in this repository. 

## Compilation Instructions

To build, install apache ant (https://ant.apache.org/)

Set the `REPOSITORY_DIR` environment variable to this directory, and run `ant all`.
This will read the build configuration in `build.xml`.

VV: Edit the batch file (compile_jar.bat) to have correct ant-installation and java installation, and run then run it to create jar.
