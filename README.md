travel-model-two
================

Currently in development.

## Relevant Repositories
The software needed to implement TM2.2 and above is spread across multiple repositories. The organization is as follows:

1. `tm2py`: A Python package that implements TM2. Please see this repository for installation instructions and usage.
2. `travel-model-two`: This repository. It contains the Java software and compilation instructions for implementing the resident passenger component of the TM2.2 system. 
3. `travel-model-two-configs`: A repository to house specific configurations of the TM2.2 system. For example, the configurations needed to simulate the 2015 base year will live in this repository. 

## Compilation Instructions

TODO -- update (using Maven?)

To build, install apache ant (https://ant.apache.org/)

Set the `REPOSITORY_DIR` environment variable to this directory, and run `ant all`.
This will read the build configuration in `build.xml`.

