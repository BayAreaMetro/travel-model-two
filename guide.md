---
layout: page
title: Guide
---

*Work in Progress*

# Users' Guide

*Model Version 1.0*

---
CONTENTS

1. [Computing Environment](#computing-environment) 
2. [System Design](#system-design) 
3. [Setup and Configuration](#setup-and-configuration)
4. [Model Execution](#model-execution) 
5. [CT-RAMP Properties File](#ct-ramp-properties-File)
6. [Input Files](#input-files)
  1. [Roadway Network](#roadway-network)
  2. [Transit Network](#transit-network)
  2. [Micro Zonal Data](#micro-zonal-data)
  3. [Zonal Data](#zonal-data)
  4. [Fixed Demand](#fixed-demand)
7. [Output Files](#output-files)
8. [Model Schematic](#model-schematic)
9. [Level of Service Information](#level-of-service-information)

---

## Computing Environment

The hardware and software MTC uses to execute Travel Model Two are described on this page. To date, MTC has not experimented enough with the model to define the minimum or ideal hardware configuration. As such, the description here is for a hardware set up that is sufficient -- not optimal. It is important to note that both the software and model structure are highly configurable and flexible; depending on the analysis needs, the required computing power could vary dramatically.

### Hardware
MTC uses four identical servers with the following characteristics:

* Operating system: Microsoft Windows Server 2007 with Service Pack 2, 64-bit edition;
* Processors: Two Intel Xeon X5570 @ 2.93 GHz (i.e., two quad-core processors with hyper-threading capability);
* Memory (RAM): 96.0 GB

As discussed in the [System Design](#system-design) section, these four computers can act in different roles, each requiring different amounts of memory and computing power. The four computers are named as follows: `mainmodel`, `satmodel` (for satellite), `satmodel2`, and `satmodel3`. As discussed in the [System Design](#system-design) section, the `mainmodel` computer plays a specialized role in the system design; the satellite machines each play identical and completely interchangeable roles.

### Software
The following software are required to execute the MTC travel model.

#### Citilabs Cube Voyager
The travel model currently uses version 6.1.X of [Citilabs Cube](http://www.citilabs.com/) or software. The Cube software is used to build skims, manipulate networks, manipulate matrices, and perform assignments. A Cube license that supports up to 9,999,999 nodes is required.

#### Citilabs Cube Voyager 64bit Matrix I/O DLL
The CT-RAMP software, as discussed below, needs to access data stored in a format dictated by Cube. This is accomplished through a 64-bit DLL library specifically for matrix I/O,which must be accessible through the `PATH` environment variable.  To install the DLL:

* Run `VoyagerFileAPIInstaller.msi`, which is included in the [`CTRAMP\runtime`](https://github.com/MetropolitanTransportationCommission/travel-model-two/tree/master/model-files/runtime) folder
* Ensure `VoyagerFileAccess.dll` is in the [`CTRAMP\runtime`](https://github.com/MetropolitanTransportationCommission/travel-model-two/tree/master/model-files/runtime) folder
* Ensure the Microsoft Visual C++ 2012 redistributable is installed on the matrix server machine.  Make sure to get version “110” DLLs (`MSVCR110.dll` and `MSVCP110.dll`).  These files can be obtained from the [Microsoft](http://www.microsoft.com/en-us/default.aspx). Download and install `vcredist_x64.exe`.

#### Citilabs Cube Cluster
The [Cube Cluster software](http://citilabs.com/software/products/cube/cube-cluster) allows Cube scripts to be multi-threaded. In the current approach, the travel model uses 64 computing nodes across four machines. The Cube scripts can be manipulated to use any number of computing nodes across any number of machines, provided each machine has, at a minimum, a Cube Voyager node license (for the time being, MTC has found 64 nodes on a single machine to be the most effective approach -- in terms of reliability and run time). Cube Cluster is not strictly necessary, as the Cube scripts can be modified to use only a single computing node. Such an approach would dramatically increase run times.

#### Java and CT-RAMP
MTC's travel model operates on the open-source Coordinated Travel - Regional Activity-based Modeling Platform (or CT-RAMP) developed by [Parsons Brinckerhoff](pbworld.com). The software is written in the [Java](http://java.com/en) programming language.  CT-RAMP requires the 64-bit Java Development Kit version 1.6 or later to be installed on each computer running the CT-RAMP software. The Java Development Kit includes the Java Runtime Environment. The 64-bit version of the software allows CT-RAMP to take advantage of larger memory addresses. The details of setting up and configuring the software are presented in the [Setup and Configuration section](#setup-and-configuration) of this guide.

#### Python
Certain network processing programs are written in [Python](https://www.python.org/). Python must be installed on the computer executing the Cube scripts -- `mainmodel` in MTC's configuration.

#### Python Rtree library
The open source [Python `rtree` library](https://pypi.python.org/pypi/Rtree/) is required for a script that dynamically codes link area type based on land use data.  The `rtree` library provides an efficient spatial index for looking up all spatial units within a buffered distance from each spatial unit.

#### Microsoft Excel
The CT-RAMP software allows discrete choice models to be specified via so-called [Utility Expression Calculators](http://analytics.mtc.ca.gov/foswiki/Main/UtilityExpressionCalculator). These files are Excel-based.

#### Remote Execution and Stop Utilities
The Microsoft [`PsKill`](http://technet.microsoft.com/en-us/sysinternals/bb896683.aspx) and [`PsExec`](http://technet.microsoft.com/en-us/sysinternals/bb897553.aspx) programs are used to remotely kill programs and execute programs.

## System Design

Here, we describe the manner in which the software is configured to take advantage of the available hardware (see the [Computing Environment](#computing-environment) section for details on the hardware and software used in the travel model; see the [Setup and Configuration](#setup-and-configuration) section for details on setting up and configuring the MTC to run on a given set of hardware).

### Distributed Computing
The MTC travel model uses two types of distributed applications. The first is facilitated by the Cube Cluster software and allows the skim building and assignment steps to utilize multiple threads. The second is faciltated by the CT-RAMP software, which allows the choice models to be distributed across multiple threads and multiple computers. A brief overview of both of these applications is provided below.

#### Cube Cluster
Citilabs Cube scripts facilitate two types of distribution, both of which are highly configurable through the Cube scripting language and the Cube Cluster thread management system; the two distinct types of multi-threading are as follows:

* Intra-step threading: The `DistributeINTRAStep` keyword keyword allows calculations that are performed across a matrix of data to be performed in blocks -- specifically rows of data -- across multiple threads. MTC uses intra-step threading in highway assignment, allowing shortest paths to be constructed for more than one origin at a time. Complex matrix calculations can also benefit from intra-step threading.
* Multi-step threading: The `DistributeMULTIStep` keyword allows blocks of code to be distributed across multiple threads. For example, if the same calculations are being performed for five different time periods, the same block of code (with variables) can be distributed across computers for parallel processing. This type of Cube multi-threading is a bit less flexible than the intra-step threading as it requires threads to be identified *a priori* (e.g., thread one will do the calculations for time period A), where the intra-step threading can be given a list of available processes and use what is available. MTC uses multi-step threading for highwway skimming, transit skimming, highway assignment, the conversion of trip lists to trip matrices, highway assignment, and transit assignment.

As noted in the [Computing Environment](#computing-environment) section, the MTC travel model specifies the Cube scripts to take advantage of 64 threads. A knowledgeable user can easily adjust the necessary scripts to take advantage of more or fewer processors.

#### CT-RAMP
The CT-RAMP software allows for the choice models to be distributed across threads and machines. The MTC application currently uses four machines, but the CT-RAMP software can be configured fairly easy to utilize fewer or more machines. CT-RAMP uses the [Java Parallel Processing Framework](http://www.jppf.org/), or JPPF, to manage the distribution of tasks. JPPF is an open-source Java package. The JPPF framework consists of three main parts as follows: 

1. a driver, also referred to as the JPPF server; 
2. one or more nodes, typically one node is established on each machine; and,
3. a client, the CT-RAMP software in this case.

As noted on the [Computing Environment](#computing-environment) section, MTC uses four computers with the names `mainmodel`, `satmodel`, `satmodel2`, and `satmodel3`. The JPPF driver process is executed on `mainmodel` and acts like a traffic cop by acquiring tasks from the client and distributing those tasks to the node processes. When the node processes complete tasks, the results are returned back to the client via the JPPF driver. Three nodes are used in the MTC application, one each on `satmodel`, `satmodel2`, and `satmodel3` (each node runs 12 processes). These three nodes are created prior to executing a model run. After being created, each node listens for tasks from the JPPF driver.
 
Node processes receive tasks, perform those tasks, and return the results. Nodes are configured to communicate with the driver process when they are started. MTC configures the nodes to use 90 GB of memory and 12 threads (see the [Setup and Configuration](#setup-and-configuration) section for details on where these parameters are specified). The JPPF driver attempts to balance computational loads across available nodes. The driver also retrieves class files, i.e. sets of Java code, from the client application and passes those to the nodes as needed.

The CT-RAMP software, which serves as the client, is responsible for creating task objects that can be run in parallel and submitting those to the driver. Because the MTC travel model simulates households, the CT-RAMP software creates packets of `N` (a user-configurable quantity, e.g. 500) households and sends those packets to the nodes for processing. As the nodes complete tasks and returns them to the driver, the driver gives the nodes new tasks, attempting to keep each node uniformly busy.

##### Household Manager and Matrix Manager
Before executing a model run, the travel model requires a `Household Manager` and a `Matrix Manager` be created. In the MTC application, both the Managers reside on the `satmodel` computer during execution. The Household Manager is tasked with managing the simulated households, as well as each simulated person in each simulated household. The `Household Manager` provides the JPPF nodes with information regarding the households for which the JPPF nodes are applying choice models and stores the resulting information computed by the JPPF nodes. To help keep run time down, the synthetic population is read from disk and stored in memory at the beginning of the application and then continuously updated as choice models are completed and iterations are performed. When the last iteration is complete, the necessary information is written to disk.

The `Matrix Manager` is tasked with managing all of the skim matrices used by the choice models. When a skim is needed, a request is made to the Matrix Manager, which then reads the required skim from disk and stores it in memory. Once in memory, each matrix is available to any other JPPF node process that may need it.

Both the `Household Manager` and `Matrix Manager` have substantial memory footprints, currently 35GB and 44GB respectively.

##### TAZ, MAZ, and TAP Data Manager
The main CT-RAMP model process includes the following internal data management interfaces for managing zone-type data: 

* TAZ data manager, 
* MAZ data manager, and 
* TAP data manager.  

These data managers provide TAZ, MAZ, and TAP level data to the various sub-models.  The TAZ data manager provides TAZ attribute data.  The MAZ data manager provides MAZ attribute data, as well as MAZ to MAZ impedances.  The TAP data manager provides TAP attribute data, as well as MAZ to TAP impedances.  These data managers are copied to JPPF nodes during execution, which increases the memory required by JPPF nodes. 

## Setup and Configuration

This section provides details on setting up the travel model to run on a cluster of computers, including descriptions of the necessary configuration files.

### Step 1: Create the required folder structure
The MTC travel model is delivered as a compressed folder containing two directories, `CTRAMP` and `INPUT` and one MS-DOS batch file, `RunModel.bat`. These files can be placed in any directory on a computer designated as the main controller of the program flow. On MTC's set up, these files are placed on the `mainmodel` computer (see [System Design](#system-design) section for more details).

The `CTRAMP` directory contains all of the model configuration files, Java instructions, and Cube scripts required to run the travel model, organized in the following three folders:

* [model](https://github.com/MetropolitanTransportationCommission/travel-model-two/tree/master/model-files/model) -- contains all of the [Utility Expression Calculators](http://analytics.mtc.ca.gov/foswiki/Main/UtilityExpressionCalculator) files that specify the choice models;
* [runtime](https://github.com/MetropolitanTransportationCommission/travel-model-two/tree/master/model-files/runtime) -- contains all of the Java configuration and `JAR` (executable) files, as well as the files necessary for Java to communicate with Cube;
* [scripts](https://github.com/MetropolitanTransportationCommission/travel-model-two/tree/master/model-files/scripts) -- contains all of the Cube scripts and associated helper files.

The `INPUT` directory contains all of the input files (see the [Input Files](#input-files) section) required to run a specific scenario. MTC will deliver the model with a set of scenario-specific set of inputs. When configuring the model on a new computing system, one should make sure that the results from an established scenario can be recreated before developing and analyzing a new scenario. The `INPUT` directory contains the following folders:

* `hwy` -- contains the input master network with all zone centroids as well (TAZ, MAZ, and TAP) (see the [Networks](#networks) section);
* `trn` -- contains all of the input transit network files (see the [Networks](#networks) section);
* `landuse` -- contains the MAZ and TAZ level socio-economic input land use files;
* `nonres` -- contains the fixed, year-specific internal/external trip tables, the fixed, year-specific air passenger trip tables, and files used to support the commercial vehicle model;
* `popsyn` -- contains the synthetic population files.

The `RunModel.bat` script contains a list of MS-DOS instructions that control model flow.

### Step 2: Map a network drive to share across computers
As noted in the previous section, the MTC model files can be placed within any directory. After establishing this location, the user must map a network drive to a shared folder to allow other computers access. On MTC's machine, the directory `E:\MainModelShare` is first mapped to the letter drive `M:\` and this directory is then shared across on the network (`M:\ = \\MainModel\MainModelShare\`).

Satellite computers should also map the letter drive `M:\` to this network location.

Please note that the model components running on the main machine should use the local version of the directory (i.e. `M:\Projects\`) rather than the network version (i.e. `\\MainModel\MainModelShare\Projects\`).

### Step 3: Configure the CT-RAMP and JPPF Services
Much of the configuration of the CT-RAMP software is done automatically by the `RunModel.bat` batch file.  However, prior to executing a model run, the files controlling the CT-RAMP and JPPF services may need to be configured. Please see the [System Design](#system-design) section for a broad overview of these services. When executing the travel model, the following start-up scripts need to be run separately on each computer. Each script specifies the tasks assigned to each computer and need not be configured exactly as described on the [System Design](#system-design) section (we describe MTC's setup; numerous other configurations are possible). In the MTC setup, the following commands are executed:

1. `runDriver.cmd` starts the JPPF Driver required for distributed model running; 
2. `runHhMgr.cmd` starts the household manager on `satmodel1`;
3. `runMtxMgr.cmd` starts the matrix manager on `satmodel1`;
4. `runNode{X}.cmd` starts up JPPF worker nodes on the remaining node {X} machine(s);

The `.cmd` files are MS-DOS batch scripts and can be edited in a text editor, such as Notepad.

Each program requires an explicit amount of memory to be allocated to it.  The amount of memory allocated to each program is identified by the `-Xmx` parameter (`XXXm` allocates XXX megabytes; `Xg` allocates X gigabytes.  This may need to be adjusted depending on the model and hardware configurations.  An example is as follows:

```dosbatch
.. %JAVA_PATH%\bin\java -server -Xmx35000m ...
```

Most of the JPPF-related configuration parameters have been optimized for the MTC travel model application and, as such, need not be modified. There are, however, a handful of parameters described in the table below that may need to be modified to meet the specifications of the computing environment upon which the model is being executed. Each of the files listed below can be found in the `CTRAMP\runtime\config\` directory. 

| **File Name**                             | **File Function**               | **Statement**                                                 | **Purpose**                                          |
|:------------------------------------------|---------------------------------|---------------------------------------------------------------|------------------------------------------------------|
| `jppf-clientDistributed.properties`       | JPPF Client Driver Control file | `driver1.jppf.server.host = 192.168.1.200`                    | IP address of the main computer (`mainmodel` at MTC) |
| `jppf-clientLocal.properties`             | JPPF Client Local Control file  | `jppf.local.execution.threads = 22`                           | Number of threads to use for running the model on one machine for testing (mainly for debugging) |
| `jppf-driver.properties`                  | JPPF Driver Control file        | `jppf.server.host = 192.168.1.200`                            | IP address of the main computer (`mainmodel` at MTC) |
| `jppf-node{x}.properties`                 | Remote JPPF Node Control file   | `jppf.server.host = 192.168.1.200`                            | IP address of the main computer (`mainmodel` at MTC) |
|                                           |                                 | `processing.threads = 12`                                     | Number of computing cores on node {X} |
|                                           |                                 | `other.jvm.options = -Xms48000m -Xmx48000m -Dnode.name=node0` | Maximum amount of memory, in MB, to allocate to node {X} and node name for logging | 

The final configuration file that needs to be edited prior to executing a model run is the `mtctm2.properties` file located in `CTRAMP\runtime\`. This file serves as the general control module for the entire CT-RAMP application. At this stage, the following variables need to be modified for the software to execute the model properly.

| **Statement**                                     | **Purpose**                                                                                           |
|---------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| `RunModel.MatrixServerAddress = 192.168.1.200`    | The IP address of the machine upon which the Matrix Manager is being executed (`satmodel1` at MTC)    |
| `RunModel.HouseholdServerAddress = 192.168.1.200` | The IP address of the machine upon which the Household Manager is being executed (`satmodel1` at MTC) |

### Step 4: Configure `RunModel.bat`
The final file in need of adjustment for the computing environment is the `RunModel.bat` MS-DOS batch file that executes the model stream. The following statements need to be configured within this file:

| **Statement**                                                                | **Purpose** |
|------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| ` set JAVA_PATH=c:\program files\java\jdk1.7.0_13`                           | Specify the 64-bit Java path; version 1.7.0+ |
| `set TPP_PATH=c:\progam files(x86)\citilabs\cubevoyager`                     | Specify the Cube Voyager path |
| `set CUBE_PATH=c:\progam files(x86)\citilabs\cube`                           | Specify the Cube path |
| `set PYTHON_PATH=C:\Python27`                                                | Specify the Python path |
| `set RUNTIME=ctramp\runtime`                                                 | Specify the location of the CT-RAMP software (relative to the project directory) |
| `set SAMPLERATE_ITERATION{iteration}=0.1`                                    | Set choice model household sample rate by iteration |
| `set PATH=%RUNTIME%;%JAVA_PATH%/bin;%TPP_PATH%;%PYTHON_PATH%/bin;%OLD_PATH%` | Set the path DOS environment variable for the model run |
| `set HOST_IP_ADDRESS=%IPADDRESS%`                                            | The IP address of the host machine, `mainmodel` at MTC, is automatically calculated |
| `set MODEL_YEAR=2010`                                                        | Set model year |
| `set BASE_SCRIPTS=CTRAMP\scripts`                                            | Set scripts folder |
| `set /A MAX_ITERATION=2`                                                     | Set the model feedback iterations |
| `set TAZ_COUNT=4509`                                                         | The number of tazs |
| `set TAZ_EXTS_COUNT=4530`                                                    | The number of tazs + externals |
| `set TAP_COUNT=6172`                                                         | The number of transit access point zones |
| `set MATRIX_SERVER=\\w-ampdx-d-sag02`                                        | Machine running matrix data manager |
| `set MATRIX_SERVER_BASE_DIR=%MATRIX_SERVER%\c$\projects\mtc\%SCEN%`          | Machine running matrix data manager base directory |
| `set MATRIX_SERVER_ABSOLUTE_BASE_DIR=c:\projects\mtc\%SCEN%`                 | Machine running matrix data manager absolute directory |
| `set MATRIX_SERVER_JAVA_PATH=C:\Program Files\Java\jdk1.7.0_25`              | Machine running matrix data manager Java install |
| `set HH_SERVER=\\w-ampdx-d-sag02`                                            | Machine running household data manager |
| `set HH_SERVER_BASE_DIR=%HH_SERVER%\c$\projects\mtc\%SCEN%`                  | Machine running household data manager base directory |
| `set HH_SERVER_ABSOLUTE_BASE_DIR=c:\projects\mtc\%SCEN%`                     | Machine running household data manager absolute directory |
| `set HH_SERVER_JAVA_PATH=C:\Program Files\Java\jdk1.7.0_25`                  | Machine running household data manager Java install |
| `set UN=`                                                                    | Username for logging in to remote machines |
| `set PWD=`                                                                   | Password for logging in to remote machines |

Now that the model is configured, the user can run the model, as described in the [Model Execution](#model-execution) section.

## Model Execution

This page describes how `RunModel.bat` executes the travel model. For: 

* a description of the underlying computing environment, see [Computing Environment](#computing-environment); 
* for a general description of the underlying system design, see [System Design](#system-design); 
* for a description of the configuration files that may need to be modified before executing the model, see [Setup and Configuration](#setup-and-configuration).

### Step 1: Set globally-available environmental variables

See  [Setup and Configuration](#setup-and-configuration) for complete details.

### Step 2: Set relevant paths to access software

See  [Setup and Configuration](#setup-and-configuration) for complete details.

### Step 3: Create and populate a working directory of input files

A working directory is created and populated with the input files, leaving the input files untouched in the process.  This step also creates the necessary directory structure for the household and matrix data servers on the remote machine and copies over needed files.

```dosbatch
mkdir hwy
mkdir trn
mkdir skims
mkdir landuse
mkdir popsyn
mkdir nonres
mkdir main
mkdir logs
mkdir database
mkdir ctramp_output

:: Stamp the feedback report with the date and time of the model start
echo STARTED MODEL RUN  %DATE% %TIME% >> logs\feedback.rpt 

:: Move the input files, which are not accessed by the model, to the working directories
copy INPUT\hwy\                 hwy\
copy INPUT\trn\                 trn\
copy INPUT\trn\transit_lines\   trn\
copy INPUT\trn\transit_fares\   trn\ 
copy INPUT\trn\transit_support\ trn\
copy INPUT\landuse\             landuse\
copy INPUT\popsyn\              popsyn\
copy INPUT\nonres\              nonres\
copy INPUT\warmstart\main\      main\
copy INPUT\warmstart\nonres\    nonres\
```
After the directories are created, copies are made to the remote machines for access by the household and matrix servers.

```dosbatch
SET HH_DEPENDENCIES=(hwy popsyn landuse skims trn CTRAMP logs)
IF NOT EXIST %HH_SERVER_BASE_DIR% MKDIR %HH_SERVER_BASE_DIR%
FOR %%A IN %HH_DEPENDENCIES% DO (
    IF NOT EXIST %HH_SERVER_BASE_DIR%\%%A MKDIR %HH_SERVER_BASE_DIR%\%%A
)
ROBOCOPY CTRAMP %HH_SERVER_BASE_DIR%\CTRAMP *.* /E /NDL /NFL

SET MATRIX_DEPENDENCIES=(skims CTRAMP logs ctramp_output)
IF NOT EXIST %MATRIX_SERVER_BASE_DIR% MKDIR %MATRIX_SERVER_BASE_DIR%
FOR %%A IN %MATRIX_DEPENDENCIES% DO (
    IF NOT EXIST %MATRIX_SERVER_BASE_DIR%\%%A MKDIR %MATRIX_SERVER_BASE_DIR%\%%A
)
ROBOCOPY CTRAMP %MATRIX_SERVER_BASE_DIR%\CTRAMP *.* /E /NDL /NFL
```

### Step 4: Pre-process steps
Several steps are needed to prepare the inputs for use in the model.  The following Cube scripts are executed to perform the following:

* `zone_seq_net_builder.job` -- build an internal numbering scheme for the network nodes to play nice with Cube
* `CreateNonMotorizedNetwork.job` -- convert the roadway network into bike and ped networks
* `tap_to_taz_for_parking.job` -- create the transit access point (TAP) data
* `SetTolls.job` -- set network prices (i.e., bridge tolls, express lane tolls) in the roadway network
* `SetHovKferPenalties.job` -- add a penalty of X seconds for dummy links connecting HOV/express lanes and general purpose lanes
* `SetCapClass.job` -- compute area type and populate the `CAPCLASS` network variable
* `CreateFiveHighwayNetworks.job` -- create time-of-day-specific roadway networks
* `BuildTazNetworks.job` -- create TAZ-scale networks for TAZ-scale roadway assignment

### Step 5:  Build walk, bicycle, and nearby automobile level-of-service matrices
Two scripts create the level-of-service information for the non-motorized modes and nearby automobile skims (for which, as a simplification, congestion is constant).  The following Cube scripts do the job:

*  `NonMotorizedSkims.job` -- skim the walk and bicycle networks
*  `MazMazSkims.job` -- builds short-distance MAZ-to-MAZ automobile skims

### Step 6: Build air passenger demand matrices
The `BuildAirPax.job` Cube script creates the air passenger demand estimates.  Air passenger demand is assumed to be independent of roadway level-of-service and, as such, can be computed a single time. 

### Step 7: Build highway and transit skims
The following steps create the highway and transit level-of-service matrices:

* Copy data files to the remote househould data manager machine
* Set the sampling rate based on `SAMPLERATE_ITERATION<iteration> global variable
* `HwySkims.job` -- build the roadway skims
* `BuildTransitNetworks.job` -- build the transit networks using the congested roadway times
* `TransitSkims.job` -- build the transit skims
* Copy the skims and related files to the remote household and matrix data manager machines

### Step 8:  Execute the CT-RAMP models
The core passenger travel demand models are executed via the CT-RAMP Java code via the following steps:

*  Remote worker node(s), as specified, are started using `psexec`
*  Remote household and matrix servers are started using `psexec`
*  JPPF driver, as needed, is started via `CTRAMP/runtime/runDriver.cmd`
*  CT-RAMP models are executed via `CTRAMP/runMTCTM2ABM.cmd`
*  Stops remote servers using `pskill`
*  Copies output matrices from the matrix manager machine back to the main machine
*  `merge_demand_matrices.s` -- merges the output demand matrices

### Step 9:  Execute the internal/external and commercial vehicle models
These ancillary demand models are executed via a series of Cube scripts as follows:

* `IxForecasts.job` -- create the internal/external demand matrices
* `IxTimeOfDay.job` -- apply diurnal factors to the daily internal/external demand matrices
* `IxTollChoice.job` -- apply a toll choice model for express lanes to the internal/external demand
* `TruckTripGeneration.job` -- apply the commercial vehicle generation models
* `TruckTripDistribution.job` -- apply the commercial vehicle distribution models
* `TruckTimeOfDay.job` -- apply the commercial vehicle diurnal factors
* `TruckTollChoice.job` -- apply a toll choice model for express lanes to the commercial vehicle demand

### Step 10: Network Assignment
Demand is located on mode-specific paths through the networks in the assignement step via the following steps:

* `build_and_assign_maz_to_maz_auto.job` -- nearby automobile demand assigned to best path on MAZ-scale network
* `HwyAssign.job` -- using nearby demand as background demand, demand assigned to TAZ-scale network
* `AverageNetworkVolumes.job` -- method of successive averages (MSA) applied across overall model iterations
* `CalculateAverageSpeed.job` -- using the averaged volumes, compute speeds
* `MergeNetworks.job` -- merge time-of-day-specific networks into a single network
* `IF` additional `ITERATION`s are needed, `GOTO` [Step 7: Build highway and transit skims](#step-7:-build-highway-and-transit-skims)
* `ELSE` perform transit assignment with `TransitAssign.job`

### Step 11: Clean up
The final step of the model run moves all the TP+ printouts to the `/logs` folder and deletes all the temporary Cube printouts and cluster files. 


## CT-RAMP Properties File
The CT-RAMP software is controlled by a standard Java [properties file](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/runtime/mtctm2.properties).  The _forthcoming_ {table, link} below identifies, describes, and provides on example of, each of the variables CT-RAMP expects to be in the properties file.  After the initial configuration, only a handful of these properties willl be modified in a typical application of the travel model.  The primary use for many of the variables is to facilitate model calibration and/or debugging.  Comments in the properties file preceeded with a pound (#) are ignored.


## Input Files
The table below contains brief descriptions of the input files required to execute the travel model. 

| **File name** | **Purpose** | **Folder location** | **File type** | **File format** |
|---------------|-------------|---------------------|---------------|-----------------|
| `mtc_final_network.net` | Highway, bike, walk network | hwy\ | [Citilabs Cube](http://citilabs.com/products/cube)| [Roadway Network](#roadway-network) |
| `mazData.csv` | Micro zone data  | landuse\ | CSV | [Micro Zonal Data](#micro-zonal-data) |
| `tazData.csv` | Travel analysis zone data | landuse\ | CSV | [Zonal Data](#zonal-data) |
| `truckFF.dat` | Friction factors for the commercial vehicle distribution models | nonres\ | ASCII | [Truck Distribution](#truck-distribution) |
| `truckkfact.k22.z1454.mat` | "K-factors" for the commercial vehicle distribution models | nonres\ | [Citilabs Cube](http://citilabs.com/products/cube) | [Truck Distribution](#truck-distribution) |
| `truck_kfactors_taz.csv` | "K-factors" for the commercial vehicle distribution models | nonres\ | CSV | [Truck Distribution](#truck-distribution) |
| `ixDailyYYYY.tpp` | Internal-external fixed trip table for year YYYY | nonres\ | [Citilabs Cube](http://citilabs.com/products/cube) | [Fixed Demand](#fixed-demand) |
| `IXDaily2006x4.may2208.new` | Internal-external input fixed trip table | nonres\ | [Citilabs Cube](http://citilabs.com/products/cube) | [Fixed Demand](#fixed-demand) |
|  `YYYY_fromtoAAA.csv` |  Airport passenger fixed trips for year YYYY and airport AAA  | nonres\ | CSV | [Fixed Demand](#fixed-demand) |
| `hhFile_YYYY_MAZ.csv` | Synthetic population household file at the MAZ level for year YYYY | popsyn\ | CSV | PopSynHousehold |
| `personFile.YYYY.csv` | Synthetic population person file for year YYYY | popsyn\ | CSV |   |
| `activity_code_indcen.csv` | Census occupation to activity coding | popsyn\ | CSV |   |
| `pecasvocc_occcen1.csv` | Census occupation to work occupation coding | popsyn\ | CSV |   |
| `transitLines.lin` | Transit lines | trn\transit_lines | [Citilabs Cube](http://citilabs.com/products/cube)| TransitNetwork  |
| `transitFactors_MMMM.fac` | Cube Public Transport (PT) factor files by transit line haul mode MMMM | trn\transit_support | [Citilabs Cube](http://citilabs.com/products/cube) | TransitNetwork |

### Roadway Network

The *all streets highway network* was developed from the [TomTom](http://www.tomtom.com/en_gb/licensing/) (previously TeleAtlas) North America routable network database.  The *projection* is NAD83 California State Plane FIPS VI.

The *bike network* was built from the highway network and the [MTC Bike Mapper](http://gis.mtc.ca.gov/btp/) network. The Bike Mapper network is a framework in which local cities update a master database of bicycle infrastructure and bicycle lane attributes, from which MTC has built and now maintains a trip planner application. 

The *walk network* was built from the highway network and the open source [Open Street Map](http://www.openstreetmap.org/) (OSM) network. 

#### County Node Numbering System

The highway network uses a numbering system whereby each county has a reserved block of nodes. Within each county’s block, nodes 1 through 9,999 are reserved for TAZs, 10,001 through 89,999 are for MAZs, and 90,001 through 99,999 for transit access points or TAPs. The blocks are assigned to the nine counties per MTC’s numbering scheme, as shown in the table below.

TeleAtlas network nodes are numbered by county as well and range from 1,000,000 to 10,000,000 as shown below. HOV lane nodes are those nodes corresponding to general purpose lane nodes.   

Code  | County | TAZs | MAZs |  TAPs | Network Node | HOV Lane Node
|:---:|:-------|:-----|:-----|:------|:-------------|:-------------
1 | San Francisco |	1 - 9,999 |	10,001 – 89,999 |	90,001 – 99,999 |	1,000,000 – 1,500,000 |	5,500,000 – 6,000,000
2 |	San Mateo |	100,001 – 109,999 |	110,001 – 189,999 |	190,001 – 199,999 |	1,500,000 – 2,000,000 |	6,000,000 – 6,500,000
3 |	Santa Clara |	200,001 – 209,999 |	210,001 – 289,999 |	290,001 – 299,999 |	2,000,000 – 2,500,000 |	6,500,000 – 7,000,000
4 |	Alameda |	300,001 – 309,999 |	310,001 – 389,999 |	390,001 – 399,999 |	2,500,000 – 3,000,000 | 7,000,000 – 7,500,000
5 |	Contra Costa |	400,001 – 409,999 |	410,001 – 489,999 |	490,001 – 499,999 |	3,000,000 – 3,500,000 |	7,500,000 – 8,000,000
6 |	Solano |	500,001 – 509,999 |	510,001 – 589,999 |	590,001 – 599,999 |	3,500,000 – 4,000,000 |	8,000,000 – 8,500,000
7 |	Napa |	600,001 – 609,999 |	610,001 – 689,999 |	690,001 – 699,999 |	4,000,000 – 4,500,000 |	8,500,000 – 9,000,000
8 |	Sonoma |	700,001 – 709,999 |	710,001 – 789,999 |	790,001 – 799,999 |	4,500,000 – 5,000,000 |	9,000,000 – 9,000,000
9 |	Marin |	800,001 – 809,999 |	810,001 – 889,999 |	890,001 – 899,999 |	5,000,000 – 5,500,000 |	9,500,000 – 9,999,999 

#### Node Attributes

The following node attributes are included in the master network.

*Field* | *Description* | *Data Type*
|:---:|-------------|----------
**N** | Node Number | Integer (see [Node Numbering](#county-node-numbering-system))
**X** | X coordinate (feet) | Float
**Y** | Y coordinate (feet) | Float
**COUNTY** | County Code | Integer
**MODE** | Best transit mode served. <br /><ul><li>1: Local bus</li> <li>2: Express bus</li> <li>3: Ferry</li> <li>4: Light rail</li> <li>5: Heavy rail</li> <li>6: Commuter rail</li> </ul> Appears to be set for TAPs and nodes with **STOP** set.| Integer
**STOP** | Transit stop or terminal name of the node | String
**PNR_CAP** |  Number of parking spaces at the stop or terminal if a parking facility is available | Integer
**PNR&lt;TimePeriod&gt;** | Is parking available at the stop or terminal by time period? | Integer (1=available)
**PNR_Fee&lt;Timeperiod&gt;** | Parking fee at the stop by time period | Float
**FAREZONE** | Unique sequential fare zone ID for transit skimming and assignment | Integer

#### Link Attributes

The following link attributes are included on the master network.

| *Field* | *Description* | *Data Type* | *Source* |
|:-------:|---------------|-------------|----------|
| **A** | from node | Integer (see [Node Numbering](#county-node-numbering-system)) |
| **B** | to node | Integer (see [Node Numbering](#county-node-numbering-system)) |
| **F_JNCTID** | TomTom from node | Long integer | TomTom |
| **T_JNCTID** | TomTom to node | Long integer | TomTom |
| **FRC** | Functional Road Class<br /> <ul><li>-1: Not Applicable</li> <li>0: Motorway, Freeway, or Other Major Road</li>  <li>1: a Major Road Less Important than a Motorway</li> <li>2: Other Major Road</li> <li>3: Secondary Road</li> <li>4: Local Connecting Road</li> <li>5: Local Road of High Importance</li> <li>6: Local Road</li> <li>7: Local Road of Minor Importance</li> <li>8: Other Road</li> </ul> | Float | TomTom |
| **NAME** | Road name | String | TomTom |
| **FREEWAY** | Freeway<br /> <ul><li>0: No Part of Freeway (default)</li> <li>1: Part of Freeway</li> </ul> | Integer | TomTom |
| **TOLLRD** | Toll Road<br /> <ul> <li>Blank: No Toll Road (default)</li> <li>B: Toll Road in Both Directions</li> <li>FT: Toll Road in Positive Direction</li> <li>TF: Toll Road in Negative Direction</li> </ul> | String | TomTom |
| **ONEWAY** |  Direction of Traffic Flow<br /> <ul><li>Blank: Open in Both Directions (default)</li> <li>FT: Open in Positive Direction</li> <li>N: Closed in Both Directions</li> <li>TF: Open in Negative Direction</li></ul> | String | TomTom |
| **KPH** | Calculated Average Speed (kilometers per hour) | Integer | TomTom |
| **MINUTES** | Travel Time (minutes) | Integer | TomTom |
| **CARRIAGE** | Carriageway Type<br /> <ul><li>Blank: Not Applicable</li> <li>1: Car Pool</li> <li>2: Express</li> <li>3: Local</li></ul> | Integer | TomTom |
| **LANES** | TomTom Number of lanes | Integer | TomTom |
| **RAMP** | Exit / Entrance Ramp<br /> <ul><li>0: No Exit/Entrance Ramp - Default</li> <li>1: Exit</li> <li>2: Entrance</li></ul> | Integer | TomTom |
| **SPEEDCAT** | Speed Category<br /><ul><li>1: &gt; 130 km/h</li> <li>2: 101 - 130 km/h</li> <li>3: 91 - 100 km/h</li> <li>4: 71 - 90 km/h</li> <li>5: 51 - 70 km/h</li> <li>6: 31 - 50 km/h</li> <li>7: 11 - 30 km/h</li><li>8: &lt; 11 km/h</li></ul> | Integer | TomTom |
| **FEET** | Calculated from TomTom Meters field | Integer | TomTom |
| **RTEDIR** | Route Directional<br /><ul><li>Blank: Not Applicable (default)</li> <li>N: Northbound</li> <li>E: Eastbound</li> <li>S: Southbound</li> <li>O / W: Westbound</li></ul> | String | TomTom |
| **ASSIGNABLE** | Is link used for assignment (1=True, 0=False) | Integer |   |
| **CNTYPE** | Link connector type<br /><ul> <li>BIKE - bike link</li> <li>CRAIL - commuter rail</li> <li>FERRY- ferry link</li> <li>HRAIL - heavy rail link</li> <li>LRAIL- light rail link</li> <li>MAZ - MAZ connector link</li> <li>PED - ped link</li> <li>TANA - regular network link</li> <li>TAP - TAP link</li> <li>TAZ - TAZ connector link</li> <li>USE - HOV (user class) link</li> </ul> | String |   |
| **TRANSIT** | Is Transit link | Integer |   |
| **USECLASS** | Link user class<br /> <ul><li>0 - NA; link open to everyone</li> <li>2 - HOV 2+</li> <li>3 - HOV 3+</li> <li>4 - No combination trucks</li></ul> | Integer |   |
| **TOLLBOOTH** | Toll link.  Links with values [less than 11](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/scripts/block/hwyParam.block) are _bridge tolls_; 11 or above are _value tolls_. <br /> <ul><li>1: Benicia-Martinez Bridge</li> <li>2: Carquinez Bridge</li> <li>3: Richmond Bridge</li> <li>4: Golden Gate Bridge</li> <li>5: San Francisco/Oakland Bay Bridge</li> <li>6: San Mateo Bridge</li> <li>7: Dumbarton Bridge</li> <li>8: Antioch Bridge</li> <li>12: I-680 express lane</li></ul> | Integer |   |
| **FT** | Facility type<br /> <ul><li>0: Connector</li> <li>1: Freeway to Freeway</li> <li>2: Freeway</li> <li>3:  Expressway</li> <li>4: Collector</li> <li>5: Ramp</li> <li>6: Special Facility</li> <li>7: Major Arterial</li></ul> | Integer |   |
| **FFS** | Free flow speed calculated from TomTom KPH | Integer |   |
| **NUMLANES** | Model number of lanes | Integer |   |
| **HIGHWAYT** | Highway type<br /> <ul> <li>footway</li> <li>footway_unconstructed</li> <li>pedestrian</li> <li>steps</li> </ul> | String | Open Street Map |
| **B_CLASS** | Bike Class<br /> <ul><li>0 - Unclassified Street</li> <li>1 - Class I Trail</li> <li>2 - Class II Route</li> <li>3 - Class III Route</li></ul> | Integer | BikeMapper |
| **REPRIORITIZE** | Priority<br/> <ul><li>2 - Highly Desirable</li> <li>1 - Desirable</li> <li>0 - No Preference</li> <li>-1 - Undesirable</li> <li>-2 - Highly Undesirable</li></ul> | Integer | BikeMapper |
| **GRADE_CAT** | Grade class<br /> <ul><li>4 - 18% or High Grade</li> <li>3 - 10-18% Grade</li> <li>2 - 5-10% Grade</li> <li>1 - 0-5% Grade</li></ul> | Integer | BikeMapper |
| **PED_FLAG** | Pedestrian access (Y=yes; blank=no) | String | BikeMapper |
| **BIKEPEDOK** | Bridge that allows bike and peds (1=true, 0=false) | Integer | BikeMapper |
| **PEMSID** | PEMS ID | Integer | PEMS |
| **PEMSLANES** | PEMS number of lanes | Integer | PEMS |
| **PEMSDIST** | Distance from link to PEMS station | Float | PEMS |
| **TAP_DRIVE** | TAP link to parking lot (1=true) | Int | MTC |

### Transit Network

The transit network is made up of three core components: transit lines, transit modes, and transit fares.  The transit lines were built from MTC’s regional transit database (or RTD).  The lines are coded with a mode (see below) and serve a series of stop nodes.  Transit fares are coded according to Cube's Public Transport program (see below).

Transit trips are assigned between transit access points (TAPs), which represent individual or collections of transit stops for transit access/egress.  TAPs are essentially transit specific TAZs that are automatically coded based on the transit network.  See the [Level of Service Information](#level-of-service-information). 

#### Line Attributes

| *Field* | *Description* | *Data Type* |
|:-------:|---------------|-------------|
| **NAME** | RTD CPT_AGENCYID and SCH_ROUTEDESIGNATOR | String |
| **USERA1** | Transit operator | String |
| **USERA2** | Line haul mode, one of <ul> <li>Local bus (LB)</li> <li>Express Bus (EB)</li> <li>Ferry service (FY)</li> <li>Light rail (LR)</li> <li>Heavy rail (HR)</li> <li>Commuter rail (CR)</li> </ul> | String |
| **MODE** | Mode code | Integer |
| **ONEWAY** | set to TRUE since each route is coded by direction | Character |
| **XYSPEED** | set to 15 by default (not used) | Integer |
| **HEADWAY[1]** | early AM headway (3AM to 6AM) | Float |
| **HEADWAY[2]** | AM peak headway (6AM to 10AM) | Float |
| **HEADWAY[3]** | Midday headway (10AM to 3PM) | Float |
| **HEADWAY[4]** | PM peak headway (3PM to 7PM) | Float |
| **HEADWAY[5]** | Evening headway (7PM to 3AM) | Float |
| **N** | List of stops served.  Lines are coded through stops, not TAPs (which are like transit TAZs).  A negative stop is not served. | List of Integers |

#### Transit Modes

The following transit modes are defined based on the RTD database attributes `CPT_AGENCYID`, `CPT_MODE`, and `SCH_ROUTEDESIGNATOR`.  These modes represent combinations of operators and technology. 

| *CPT_AGENCYID* | *AGENCYNAME* | *CPT_MODE* | *SCH_ROUTEDESIGNATOR* | *MODECODE* | *MODEGROUP* |
|----------------|--------------|------------|-----------------------|------------|-------------|
| 3D | TriDelta Transit | B | NA | 44 | Local bus |
| AB | AirBART | B | NA | 40 | Local bus |
| AC | AC Transit | B | NA | 30 | Local bus |
| AD | AC Transbay | B | NA | 84 | Express Bus |
| AM | Amtrak Capitol Cor. & Reg. Svc | T | NA | 131 | Commuter rail |
| AO | Alameda/Oakland Ferry | F | NA | 100 | Ferry service |
| AT | Angel Island - Tiburon Ferry | F | NA | 103 | Ferry service |
| AY | American Canyon Transit | B | NA | 55 | Local bus |
| BA | BART | T | NA | 120 | Heavy rail |
| BG | Blue and Gold | F | NA | 103 | Ferry service |
| BT | Benicia Transit | B | NA | 58 | Local bus |
| CC | The County Connection | B | 91X | 86 | Express Bus |
| CC | The County Connection | B | 92X | 86 | Express Bus |
| CC | The County Connection | B | 93X | 86 | Express Bus |
| CC | The County Connection | B | 95X | 86 | Express Bus |
| CC | The County Connection | B | 96X | 86 | Express Bus |
| CC | The County Connection | B | 97X | 86 | Express Bus |
| CC | The County Connection | B | 98X | 86 | Express Bus |
| CC | The County Connection | B | NA | 42 | Local bus |
| CE | ACE | T | NA | 133 | Commuter rail |
| CT | Caltrain | T | NA | 130 | Commuter rail |
| DE | Dumbarton Express | B | NA | 82 | Express Bus |
| EM | Emery Go-Round | B | NA | 12 | Local bus |
| FS | Fairfield-Suisun Transit | B | 40 | 92 | Express Bus |
| FS | Fairfield-Suisun Transit | B | NA | 52 | Local bus |
| GF | Golden Gate Ferry | F | NA | 101 | Ferry service |
| GG | Golden Gate Transit | B | 22 | 87 | Express Bus |
| GG | Golden Gate Transit | B | 23 | 87 | Express Bus |
| GG | Golden Gate Transit | B | 29 | 87 | Express Bus |
| GG | Golden Gate Transit | B | 35 | 87 | Express Bus |
| GG | Golden Gate Transit | B | 36 | 87 | Express Bus |
| GG | Golden Gate Transit | B | 71 | 88 | Express Bus |
| GG | Golden Gate Transit | B | NA | 70 | Local bus |
| HB | Alameda Harbor Bay Ferry | F | NA | 100 | Ferry service |
| MS | Stanford Marguerite Shuttle | B | NA | 13 | Local bus |
| PE | Petaluma Transit | B | NA | 68 | Local bus |
| RV | Rio Vista Delta Breeze | B | NA | 52 | Local bus |
| SC | Santa Clara VTA | B | 101 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 102 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 103 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 104 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 120 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 121 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 122 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 140 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 168 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 180 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 181 | 81 | Express Bus |
| SC | Santa Clara VTA | B | 182 | 81 | Express Bus |
| SC | Santa Clara VTA | B | NA | 28 | Local bus |
| SC | Santa Clara VTA | LR | NA | 111 | Light rail |
| SF | San Francisco MUNI | B | NA | 21 | Local bus |
| SF | San Francisco MUNI | LR | NA | 110 | Light rail |
| SF | San Francisco MUNI | CC | NA | 20 | Local bus |
| SM | samTrans | B | KX | 80 | Express Bus |
| SM | samTrans | B | NA | 24 | Local bus |
| SO | Sonoma County Transit | B | NA | 63 | Local bus |
| SR | Santa Rosa CityBus | B | NA | 66 | Local bus |
| SV | St. Helena VINE | B | NA | 60 | Local bus |
| UC | Union City Transit | B | NA | 38 | Local bus |
| VB | Vallejo Baylink Ferry | B | NA | 104 | Ferry service |
| VB | Vallejo Baylink Ferry | F | NA | 104 | Ferry service |
| VC | Vacaville City Coach | B | NA | 56 | Local bus |
| VN | Napa VINE | B | NA | 60 | Local bus |
| VT | Vallejo Transit | B | 80 | 91 | Express Bus |
| VT | Vallejo Transit | B | 85 | 91 | Express Bus |
| VT | Vallejo Transit | B | NA | 49 | Local bus |
| WC | WestCAT | B | JL | 90 | Express Bus |
| WC | WestCAT | B | JPX | 90 | Express Bus |
| WC | WestCAT | B | JR | 90 | Express Bus |
| WC | WestCAT | B | JX | 90 | Express Bus |
| WC | WestCAT | B | LYNX | 90 | Express Bus |
| WC | WestCAT | B | NA | 46 | Local bus |
| WH | WHEELS | B | NA | 17 | Local bus |
| YV | Yountville Shuttle | B | NA | 60 | Local bus |

#### Transit Fares

Transit fares are modeled in Cube's Public Transport (PT) program as follows:
  1. Each transit mode is assigned a fare system in the Cube factor files
  1. Each fare system is defined in the fares.far fare file
  1. Each fare system is either FROMTO (fare zone based) or FLAT (initial + transfer in fare)
  1. For FROMTO fare systems:
    1. Each stop node is assigned a FAREZONE ID in the master network
    1. The fare is looked up from the fare matrix (fareMatrix.txt), which is a text file with the following columns: MATRIX ZONE_I ZONE_J VALUE
    1. The fare to transfer in from other modes is defined via the FAREFROMFS array (of modes) in the fares.far file
  1. For FLAT fare systems:
    1. The initial fare is defined via the IBOARDFARE in the fares.far file
    1. The fare to transfer in from other modes is defined via the FAREFROMFS array (of modes) in the fares.far file

### Micro Zonal Data

| *Column Name* | *Description* |
|:-------------:|---------------|
| **MAZ_ORIGINAL** | Original micro zone number. It's original because these will get renumbered during the model run assuming [the node numbering conventions](#county-node-numbering-system) |
| **TAZ_ORIGINAL** | Original TAZ number. It's original because these will get renumbered during the model run assuming [the node numbering conventions](#county-node-numbering-system)  |
| **hh** | Total number of households |
| **pop** | Total population |
| **emp_self** | Self-employed |
| **emp_ag** | Agriculture employment |
| **emp_const_non_bldg_prod** | Construction Non-Building production (including mining) employment |
| **emp_const_non_bldg_office** | Construction Non-Building office support (including mining) employment |
| **emp_utilities_prod** | Utilities production employment |
| **emp_utilities_office** | Utilities office support employment |
| **emp_const_bldg_prod** | Construction of Buildings production employment |
| **emp_const_bldg_office** | Construction of Buildings office support employment |
| **emp_mfg_prod** | Manufacturing production employment |
| **emp_mfg_office** | Manufacturing office support employment |
| **emp_whsle_whs** | Wholesale and Warehousing employment |
| **emp_trans** | Transportation Activity employment |
| **emp_retail** | Retail Activity employment |
| **emp_prof_bus_svcs** | Professional and Business Services employment |
| **emp_prof_bus_svcs_bldg_maint** | Professional and Business Services (Building Maintenance) employment |
| **emp_pvt_ed_k12** | Private Education K-12 employment |
| **emp_pvt_ed_post_k12_oth** | Private Education Post-Secondary (Post K-12) and Other employment |
| **emp_health** | Health Services employment |
| **emp_personal_svcs_office** | Personal Services Office Based employment |
| **emp_amusement** | Amusement Services employment |
| **emp_hotel** | Hotels and Motels employment |
| **emp_restaurant_bar** | Restaurants and Bars employment |
| **emp_personal_svcs_retail** | Personal Services Retail Based employment |
| **emp_religious** | Religious Activity employment |
| **emp_pvt_hh** | Private Households employment |
| **emp_state_local_gov_ent** | State and Local Government Enterprises Activity employment |
| **emp_scrap_other** | Scrap other employment |
| **emp_fed_non_mil** | Federal Non-Military Activity employment |
| **emp_fed_mil** | Federal Military Activity employment |
| **emp_state_local_gov_blue** | State and Local Government Non-Education Activity production employment |
| **emp_state_local_gov_white** | State and Local Government Non-Education Activity office support employment |
| **emp_public_ed** | Public Education K-12 and other employment |
| **emp_own_occ_dwell_mgmt** | Owner-Occupied Dwellings Management and Maintenance Activity employment |
| **emp_fed_gov_accts** | Federal Government Accounts employment |
| **emp_st_lcl_gov_accts** | State and Local Government Accounts employment |
| **emp_cap_accts** | Capital Accounts employment |
| **emp_total** | Total employment |
| **EnrollGradeKto8** | Grade School K-8 enrollment |
| **EnrollGrade9to12** | Grade School 9-12 enrollment |
| **collegeEnroll** | Major College enrollment |
| **otherCollegeEnroll** | Other College enrollment |
| **AdultSchEnrl** | Adult School enrollment |
| **ech_dist** | Elementary school district |
| **hch_dist** | High school district |
| **parkarea** | <ul><li>1: Trips with destinations in this MAZ may choose to park in a different MAZ, parking charges apply (downtown)</li> <li>2: Trips with destinations in parkarea 1 may choose to park in this MAZ, parking charges might apply (quarter mile buffer around downtown)</li> <li>3: Only trips with destinations in this MAZ may park here, parking charges apply (outside downtown paid parking, only show cost no capacity issue)</li> <li>4: Only trips with destinations in this MAZ may park here, parking charges do not apply (outside downtown, free parking)</li> </ul> |
| **hstallsoth** | Number of stalls allowing hourly parking for trips with destinations in other MAZs |
| **hstallssam** | Number of stalls allowing hourly parking for trips with destinations in the same MAZ |
| **hparkcost** | Average cost of parking for one hour in hourly stalls in this MAZ, dollars |
| **numfreehrs** | Number of hours of free parking allowed before parking charges begin in hourly stalls |
| **dstallsoth** | Stalls allowing daily parking for trips with destinations in other MAZs |
| **dstallssam** | Stalls allowing daily parking for trips with destinations in the same MAZ |
| **dparkcost** | Average cost of parking for one day in daily stalls, dollars |
| **mstallsoth** | Stalls allowing monthly parking for trips with destinations in other MAZs |
| **mstallssam** | Stalls allowing monthly parking for trips with destinations in the same MAZ |
| **mparkcost** | Average cost of parking for one day in monthly stalls, amortized over 22 workdays, dollars |
| **TotInt** | Total intersections |
| **DUDen** | Dwelling unit density |
| **EmpDen** | Employment density |
| **PopDen** | Population density |
| **RetEmpDen** | Retail employment density |
| **TotIntBin** | Total intersection bin |
| **EmpDenBin** | Employment density bin |
| **DuDenBin** | Dwelling unit density bin |
| **ACRES** | MAZ acres |

### Zonal Data

| *Field* | *Description* |
|:-------:|---------------|
| **TAZ_ORIGINAL** | Original TAZ number. It's original because these will get renumbered during the model run assuming [the node numbering conventions](#county-node-numbering-system)  |
| **AVGTTS** | Average travel time savings for transponder ownership model |
| **DIST** | Distance for transponder ownership model |
| **PCTDETOUR** | Percent detour for transponder ownership model |
| **TERMINALTIME** | Terminal time |

### Truck Distribution

MTC uses a simple three-step (generation, distribution, and assignment) commercial vehicle model to generate estimates of four types of commercial vehicles. The four vehicle types are very small (two-axle, four-tire), small (two-axle, six-tire), medium (three-axle), and large or combination trucks (four-or-more-axle).

#### Friction Factors

The trip distribution step uses a standard gravity model with a blended travel time impedance measure. This file sets the friction factors, which are vehicle type specific, using an ASCII fixed format text file with the following data:
 
 * Travel time in minutes (integer, starting in column 1, left justified);
 * Friction factors for very small trucks (integer, starting in column 9, left justified);
 * Friction factors for small trucks (integer, starting in column 17, left justified);
 * Friction factors for medium trucks (integer, starting in column 25, left justified); and,
 * Friction factors for large trucks (integer, starting in column 33, left justified).

#### K-Factors

The trip distribution step also uses a matrix of K-factors to adjust the distribution results to better match observed data. This matrix contains a unit-less adjustment value; the higher the number, the more attractive the production/attraction pair.

### Fixed Demand

MTC uses representations of internal/external and air passenger demand that is year-, but not scenario-, specific -- meaning simple sketch methods are used to estimate this demand from past trends. This demand is then fixed for each forecast year and does not respond to changes in land use or the transport network.

#### Internal/external

So-called internal/external demand is travel that either begins or ends in the nine county Bay Area. This demand is based on Census journey-to-work data and captures all passenger (i.e. non-commercial) vehicle demand. This demand is introduced to the model via a matrix that contains the following four demand tables in production-attraction format:

 * Daily single-occupant vehicle flows;
 * Daily two-occupant vehicle flows;
 * Daily three-or-more occupant vehicle flows; and,
 * Daily vehicle flows, which is the sum of the first three tables and not used by the travel model.

#### Air Passenger

Air passenger demand is based on surveys of air passenger and captures demand from the following travel modes: passenger vehicles, rental cars, taxis, limousines, shared ride vans, hotel shuttles, and charter buses. This demand is introduced to the model via Main.TimePeriods specific matrices that contain the following six flow tables:

 * Single-occupant vehicles;
 * Two-occupant vehicles;
 * Three-occupant vehicles;
 * Single-occupant vehicles that are willing to pay a high-occupancy toll lane fee;
 * Two-occupant vehicles that are willing to pay a high-occupancy toll lane fee; and,
 * Three-occupant vehicles that are willing to pay a high-occupancy toll lane fee.

## Output Files

## Model Schematic

## Level of Service Information

Travel Model Two employs a tiered spatial system to allow level-of-service indicators to be computed at a fine or coarser geography, as appropriate.  Two spatial systems are defined: 1) a travel analysis zone (TAZ) system and 2) a micro-analysis zone (MAZ) system.  MAZs nest within TAZs.  For travel done at a "micro" scale (in the regional context, meaning less than five miles or so), the MAZ system is used; for travel done at a larger scale, the TAZ system is used.

Further, transit travel is represented as a combination of the following three movements:

 1. Access.  An access movement from an MAZ to a so-called transit access point (or TAP), which is a single transit stop or an abstract location representing a collection of bus stops.
 2. Line haul.  A line-haul movement from a boarding TAP to an alighting TAP, which can include a transfer (moving from one TAP to another TAP) between services.
 3. Egress.  An egress movement from the alighting TAP to the destination MAZ. 

The motivation for the MAZ and TAP model design was to more precisely represent neighborhood-level travel while avoiding the steep computational price required to maintain a full set of MAZ-to-MAZ level-of-service matrices.  This design concept originated at the San Diego Association of Governments (SANDAG) and is being adopted by other planning organizations.

The MAZ and TAP model design requires transit paths be built "on the fly" (i.e. outside the commercial software used by the travel model) by intelligently building and combining the MAZ-to-TAP, TAP-to-TAP, and TAP-to-MAZ trip components into logical, efficient potential paths for evaluation in probabilistic models of mode/transit route choice. 

The table below presents the manner in which level-of-service indicators are extracted from the model network.

| **Level-of-service component** | **Separation of origin and destination** | **Geography** | **Source** |
|--------------------------------|------------------------------------------|---------------|------------|
| Automobile times, distances, and costs | Near | MAZ to MAZ | MAZ-scale single best least-cost path |
| Automobile times, distances, and costs | Far | TAZ to TAZ | TAZ-scale equilibrium assignment path |
| Transit line-haul | All | TAP to TAP | N least-cost path determination |
| Transit walk access and egress | All | MAZ to TAP | N least-cost path determination |
| Transit bicycle access and egress | All | MAZ to TAP | N least-cost path determination |
| Transit drive access and egress | All | TAZ to nearest TAP TAZ | TAZ-scale equilibrium assignment path |
| Walk | Near (assume all walk travel is near) | MAZ to MAZ | MAZ-scale single best least-cost path |
| Bicycle | Near | MAZ to MAZ | MAZ-scale single best least-cost path |
| Bicycle | Far | TAZ to TAZ | TAZ-scale single best least-cost path |

Three distinct methods of extracting times from the network are employed, as follows:

 1. Equilibrium assignment. For automobile travel, congestion effects impact path choice, so a traditional equilibrium assignment is performed at the TAZ-scale.
 2. N best least-cost paths. For transit movements, the model builds, &ldquo;on the fly&rdquo;, the N best least-cost paths between MAZ pairs. The N best least-cost paths are then evaluated in the mode/transit route choice model.
 3. Single best least-cost path. For close-proximity automobile, bicycle, and walk travel, a single best mode-specific least-cost path is computed from the MAZ level all streets network. Because the full MAZ level network is not assigned due to computational cost, the impact of congestion on MAZ level path decisions is not taken into account. As a compromise (for gaining the spatial fidelity offered by the MAZ level network), the model implicitly assumes that automobile, pedestrian, and bicycle congestion have a negligible impact on path choice decisions and assigns each MAZ-to-MAZ movement to a single best least-cost path.
   
## Networks

