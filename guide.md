---
layout: page
title: Guide
---

*Work in Progress*

# Users' Guide

*Model Version 1.0*

---
CONTENTS

1. [Computing Environment](#Computing-Environment) 
2. [System Design](#System-Design) 
3. [Setup and Configuration](#Setup-and-Configuration)
4. [Model Execution](#Model-Execution) 
5. [CT-RAMP Properties File](#CT-RAMP-Properties-File)
6. [Input Files](#Input-Files)

---

## Computing Environment

The hardware and software MTC uses to execute Travel Model Two are described on this page. To date, MTC has not experimented enough with the model to define the minimum or ideal hardware configuration. As such, the description here is for a hardware set up that is sufficient -- not optimal. It is important to note that both the software and model structure are highly configurable and flexible; depending on the analysis needs, the required computing power could vary dramatically.

### Hardware
MTC uses four identical servers with the following characteristics:

* Operating system: Microsoft Windows Server 2007 with Service Pack 2, 64-bit edition;
* Processors: Two Intel Xeon X5570 @ 2.93 GHz (i.e., two quad-core processors with hyper-threading capability);
* Memory (RAM): 96.0 GB

As discussed in the [System Design](#System-Design) section, these four computers can act in different roles, each requiring different amounts of memory and computing power. The four computers are named as follows: `mainmodel`, `satmodel` (for satellite), `satmodel2`, and `satmodel3`. As discussed in the [System Design](##System Design) section, the `mainmodel` computer plays a specialized role in the system design; the satellite machines each play identical and completely interchangeable roles.

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
MTC's travel model operates on the open-source Coordinated Travel - Regional Activity-based Modeling Platform (or CT-RAMP) developed by [Parsons Brinckerhoff](pbworld.com). The software is written in the [Java](http://java.com/en) programming language.  CT-RAMP requires the 64-bit Java Development Kit version 1.6 or later to be installed on each computer running the CT-RAMP software. The Java Development Kit includes the Java Runtime Environment. The 64-bit version of the software allows CT-RAMP to take advantage of larger memory addresses. The details of setting up and configuring the software are presented in the [Setup and Configuration section](#Setup-and-Configuration) of this guide.

#### Python
Certain network processing programs are written in [Python](https://www.python.org/). Python must be installed on the computer executing the Cube scripts -- `mainmodel` in MTC's configuration.

#### Python Rtree library
The open source [Python `rtree` library](https://pypi.python.org/pypi/Rtree/) is required for a script that dynamically codes link area type based on land use data.  The `rtree` library provides an efficient spatial index for looking up all spatial units within a buffered distance from each spatial unit.

#### Microsoft Excel
The CT-RAMP software allows discrete choice models to be specified via so-called [Utility Expression Calculators](http://analytics.mtc.ca.gov/foswiki/Main/UtilityExpressionCalculator). These files are Excel-based.

#### Remote Execution and Stop Utilities
The Microsoft [`PsKill`](http://technet.microsoft.com/en-us/sysinternals/bb896683.aspx) and [`PsExec`](http://technet.microsoft.com/en-us/sysinternals/bb897553.aspx) programs are used to remotely kill programs and execute programs.

## System Design

Here, we describe the manner in which the software is configured to take advantage of the available hardware (see the [Computing Environment](#Computing-Environment) section for details on the hardware and software used in the travel model; see the [Setup and Configuration](#Setup-and-Configuration) section for details on setting up and configuring the MTC to run on a given set of hardware).

### Distributed Computing
The MTC travel model uses two types of distributed applications. The first is facilitated by the Cube Cluster software and allows the skim building and assignment steps to utilize multiple threads. The second is faciltated by the CT-RAMP software, which allows the choice models to be distributed across multiple threads and multiple computers. A brief overview of both of these applications is provided below.

#### Cube Cluster
Citilabs Cube scripts facilitate two types of distribution, both of which are highly configurable through the Cube scripting language and the Cube Cluster thread management system; the two distinct types of multi-threading are as follows:

* Intra-step threading: The `DistributeINTRAStep` keyword keyword allows calculations that are performed across a matrix of data to be performed in blocks -- specifically rows of data -- across multiple threads. MTC uses intra-step threading in highway assignment, allowing shortest paths to be constructed for more than one origin at a time. Complex matrix calculations can also benefit from intra-step threading.
* Multi-step threading: The `DistributeMULTIStep` keyword allows blocks of code to be distributed across multiple threads. For example, if the same calculations are being performed for five different time periods, the same block of code (with variables) can be distributed across computers for parallel processing. This type of Cube multi-threading is a bit less flexible than the intra-step threading as it requires threads to be identified *a priori* (e.g., thread one will do the calculations for time period A), where the intra-step threading can be given a list of available processes and use what is available. MTC uses multi-step threading for highwway skimming, transit skimming, highway assignment, the conversion of trip lists to trip matrices, highway assignment, and transit assignment.

As noted in the [Computing Environment](#Computing-Environment) section, the MTC travel model specifies the Cube scripts to take advantage of 64 threads. A knowledgeable user can easily adjust the necessary scripts to take advantage of more or fewer processors.

#### CT-RAMP
The CT-RAMP software allows for the choice models to be distributed across threads and machines. The MTC application currently uses four machines, but the CT-RAMP software can be configured fairly easy to utilize fewer or more machines. CT-RAMP uses the [Java Parallel Processing Framework](http://www.jppf.org/), or JPPF, to manage the distribution of tasks. JPPF is an open-source Java package. The JPPF framework consists of three main parts as follows: 

1. a driver, also referred to as the JPPF server; 
2. one or more nodes, typically one node is established on each machine; and,
3. a client, the CT-RAMP software in this case.

As noted on the [Computing Environment](#Computing-Environment) section, MTC uses four computers with the names `mainmodel`, `satmodel`, `satmodel2`, and `satmodel3`. The JPPF driver process is executed on `mainmodel` and acts like a traffic cop by acquiring tasks from the client and distributing those tasks to the node processes. When the node processes complete tasks, the results are returned back to the client via the JPPF driver. Three nodes are used in the MTC application, one each on `satmodel`, `satmodel2`, and `satmodel3` (each node runs 12 processes). These three nodes are created prior to executing a model run. After being created, each node listens for tasks from the JPPF driver.
 
Node processes receive tasks, perform those tasks, and return the results. Nodes are configured to communicate with the driver process when they are started. MTC configures the nodes to use 90 GB of memory and 12 threads (see the [Setup and Configuration](#Setup-and-Configuration) section for details on where these parameters are specified). The JPPF driver attempts to balance computational loads across available nodes. The driver also retrieves class files, i.e. sets of Java code, from the client application and passes those to the nodes as needed.

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
The MTC travel model is delivered as a compressed folder containing two directories, `CTRAMP` and `INPUT` and one MS-DOS batch file, `RunModel.bat`. These files can be placed in any directory on a computer designated as the main controller of the program flow. On MTC's set up, these files are placed on the `mainmodel` computer (see [System Design](#System-Design) section for more details).

The `CTRAMP` directory contains all of the model configuration files, Java instructions, and Cube scripts required to run the travel model, organized in the following three folders:

* [model](https://github.com/MetropolitanTransportationCommission/travel-model-two/tree/master/model-files/model) -- contains all of the [Utility Expression Calculators](http://analytics.mtc.ca.gov/foswiki/Main/UtilityExpressionCalculator) files that specify the choice models;
* [runtime](https://github.com/MetropolitanTransportationCommission/travel-model-two/tree/master/model-files/runtime) -- contains all of the Java configuration and `JAR` (executable) files, as well as the files necessary for Java to communicate with Cube;
* [scripts](https://github.com/MetropolitanTransportationCommission/travel-model-two/tree/master/model-files/scripts) -- contains all of the Cube scripts and associated helper files.

The `INPUT` directory contains all of the input files (see the [Input Files](#Input-Files) section) required to run a specific scenario. MTC will deliver the model with a set of scenario-specific set of inputs. When configuring the model on a new computing system, one should make sure that the results from an established scenario can be recreated before developing and analyzing a new scenario. The `INPUT` directory contains the following folders:

* `hwy` -- contains the input master network with all zone centroids as well (TAZ, MAZ, and TAP) (see the [Networks](#Networks) section);
* `trn` -- contains all of the input transit network files (see the [Networks](#Networks) section);
* `landuse` -- contains the MAZ and TAZ level socio-economic input land use files;
* `nonres` -- contains the fixed, year-specific internal/external trip tables, the fixed, year-specific air passenger trip tables, and files used to support the commercial vehicle model;
* `popsyn` -- contains the synthetic population files.

The `RunModel.bat` script contains a list of MS-DOS instructions that control model flow.

### Step 2: Map a network drive to share across computers
As noted in the previous section, the MTC model files can be placed within any directory. After establishing this location, the user must map a network drive to a shared folder to allow other computers access. On MTC's machine, the directory `E:\MainModelShare` is first mapped to the letter drive `M:\` and this directory is then shared across on the network (`M:\ = \\MainModel\MainModelShare\`).

Satellite computers should also map the letter drive `M:\` to this network location.

Please note that the model components running on the main machine should use the local version of the directory (i.e. `M:\Projects\`) rather than the network version (i.e. `\\MainModel\MainModelShare\Projects\`).

### Step 3: Configure the CT-RAMP and JPPF Services
Much of the configuration of the CT-RAMP software is done automatically by the `RunModel.bat` batch file.  However, prior to executing a model run, the files controlling the CT-RAMP and JPPF services may need to be configured. Please see the [System Design](#System-Design) section for a broad overview of these services. When executing the travel model, the following start-up scripts need to be run separately on each computer. Each script specifies the tasks assigned to each computer and need not be configured exactly as described on the [System Design](#System-Design) section (we describe MTC's setup; numerous other configurations are possible). In the MTC setup, the following commands are executed:

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

Now that the model is configured, the user can run the model, as described in the [Model Execution](#Model-Execution) section.

## Model Execution

This page describes how `RunModel.bat` executes the travel model. For: 

* a description of the underlying computing environment, see [Computing Environment](#Computing-Environment); 
* for a general description of the underlying system design, see [System Design](#System-Design); 
* for a description of the configuration files that may need to be modified before executing the model, see [Setup and Configuration](#Setup-and-Configuration).

### Step 1: Set globally-available environmental variables

See  [Setup and Configuration](#Setup-and-Configuration) for complete details.

### Step 2: Set relevant paths to access software

See  [Setup and Configuration](#Setup-and-Configuration) for complete details.

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
* `IF` additional `ITERATION`s are needed, `GOTO` [Step 7: Build highway and transit skims](#Step-7:-Build-highway-and-transit-skims)
* `ELSE` perform transit assignment with `TransitAssign.job`

### Step 11: Clean up
The final step of the model run moves all the TP+ printouts to the `/logs` folder and deletes all the temporary Cube printouts and cluster files. 


## CT-RAMP Properties File
The CT-RAMP software is controlled by a standard Java properties file.  The _forthcoming_ {table, link} below identifies, describes, and provides on example of, each of the variables CT-RAMP expects to be in the properties file.  After the initial configuration, only a handful of these properties willl be modified in a typical application of the travel model.  The primary use for many of the variables is to facilitate model calibration and/or debugging.  Comments in the properties file preceeded with a pound (#) are ignored.


## Input Files
The table below contains brief descriptions of the input files required to execute the travel model. 

| **File name** | **Purpose** | **Folder location** | **File type** | **File format** |
|---------------|-------------|---------------------|---------------|-----------------|
| `mtc_final_network.net` | Highway, bike, walk network | hwy\ | [Citilabs Cube](http://citilabs.com/products/cube)| Networks |
| `mazData.csv` | Micro zone data  | landuse\ | CSV | MazData |
| `tazData.csv` | Travel analysis zone data | landuse\ | CSV | TazData |
| `truckFF.dat` | Friction factors for the commercial vehicle distribution models | nonres\ | ASCII | TruckDistribution |
| `truckkfact.k22.z1454.mat` | "K-factors" for the commercial vehicle distribution models | nonres\ | [Citilabs Cube](http://citilabs.com/products/cube) | TruckDistribution |
| `truck_kfactors_taz.csv` | "K-factors" for the commercial vehicle distribution models | nonres\ | CSV | TruckDistribution |
| `ixDailyYYYY.tpp` | Internal-external fixed trip table for year YYYY | nonres\ | [Citilabs Cube](http://citilabs.com/products/cube) | FixedDemand |
| `IXDaily2006x4.may2208.new` | Internal-external input fixed trip table | nonres\ | [Citilabs Cube](http://citilabs.com/products/cube) | FixedDemand |
|  `YYYY_fromtoAAA.csv` |  Airport passenger fixed trips for year YYYY and airport AAA  | nonres\ | CSV | FixedDemand |
| `hhFile_YYYY_MAZ.csv` | Synthetic population household file at the MAZ level for year YYYY | popsyn\ | CSV | PopSynHousehold |
| `personFile.YYYY.csv` | Synthetic population person file for year YYYY | popsyn\ | CSV |   |
| `activity_code_indcen.csv` | Census occupation to activity coding | popsyn\ | CSV |   |
| `pecasvocc_occcen1.csv` | Census occupation to work occupation coding | popsyn\ | CSV |   |
| `transitLines.lin` | Transit lines | trn\transit_lines | [Citilabs Cube](http://citilabs.com/products/cube)| TransitNetwork  |
| `transitFactors_MMMM.fac` | Cube Public Transport (PT) factor files by transit line haul mode MMMM | trn\transit_support | [Citilabs Cube](http://citilabs.com/products/cube) | TransitNetwork |

### Highway Network

The all streets highway network was developed from the [TomTom](http://www.tomtom.com/en_gb/licensing/) (previously TeleAtlas) North America routable network database.  The *projection* is NAD83 California State Plane FIPS VI.

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

Field | Description | Data Type
------|-------------|----------
N | Node Number | Integer (see [Node Numbering](#County-Node-Numbering-System))
X | X coordinate (feet) | Float
Y | Y coordinate (feet) | Float
COUNTY | County Code | Integer
MODE | Best transit ode served | Integer
STOP | Transit stop or terminal name of the node | String
PNR_CAP |  Number of parking spaces at the stop or terminal if a parking facility is available | Integer
PNR&lt;TimePeriod&gt; | Is parking available at the stop or terminal by time period? | Integer (1=available)
PNR_Fee&lt;Timeperiod&gt; | Parking fee at the stop by time period | Float
FAREZONE | Unique sequential fare zone ID for transit skimming and assignment | Integer

#### Link Attributes

The following link attributes are included on the master network.

| Field | Description | Data Type | Source |
| A | from node | Integer (see [Node Numbering](#County-Node-Numbering-System)) |
| B | to node | Integer (see [Node Numbering](#County-Node-Numbering-System)) |
| F_JNCTID | TomTom from node | Long integer | TomTom |
| T_JNCTID | TomTom to node | Long integer | TomTom |
| FRC | Functional Road Class<br />&bull; -1: Not Applicable<br />&bull; 0: Motorway, Freeway, or Other Major Road<br />&bull; 1: a Major Road Less Important than a Motorway<br />&bull; 2: Other Major Road<br />&bull; 3: Secondary Road<br />&bull; 4: Local Connecting Road<br />&bull; 5: Local Road of High Importance<br />&bull; 6: Local Road<br />&bull; 7: Local Road of Minor Importance<br />&bull; 8: Other Road | Float | TomTom |
| NAME | Road name | String | TomTom |
| FREEWAY | Freeway<br />&bull; 0: No Part of Freeway (default)<br />&bull; 1: Part of Freeway | Integer | TomTom |
| TOLLRD | Toll Road<br />&bull; Blank: No Toll Road (default)<br />&bull; B: Toll Road in Both Directions<br />&bull; FT: Toll Road in Positive Direction<br />&bull; TF: Toll Road in Negative Direction | String | TomTom |
| ONEWAY |  Direction of Traffic Flow<br />&bull; Blank: Open in Both Directions (default)<br />&bull; FT: Open in Positive Direction<br />&bull; N: Closed in Both Directions<br />&bull; TF: Open in Negative Direction | String | TomTom |
| KPH | Calculated Average Speed (kilometers per hour) | Integer | TomTom |
| MINUTES | Travel Time (minutes) | Integer | TomTom |
| CARRIAGE | Carriageway Type<br />&bull; Blank: Not Applicable<br />&bull; 1: Car Pool<br />&bull; 2: Express<br />&bull; 3: Local | Integer | TomTom |
| LANES | TANA Number of lanes | Integer | TomTom |
| RAMP | Exit / Entrance Ramp<br />&bull; 0: No Exit/Entrance Ramp - Default<br />&bull; 1: Exit<br />&bull; 2: Entrance | Integer | TomTom |
| SPEEDCAT | Speed Category<br />&bull; 1: &gt; 130 km/h<br />&bull; 2: 101 - 130 km/h<br />&bull; 3: 91 - 100 km/h<br />&bull; 4: 71 - 90 km/h<br />&bull; 5: 51 - 70 km/h<br />&bull; 6: 31 - 50 km/h<br />&bull; 7: 11 - 30 km/h<br />&bull; 8: &lt; 11 km/h | Integer | TomTom |
| FEET | Calculated from TANA Meters field | Integer | TomTom |
| RTEDIR | Route Directional<br />&bull; Blank: Not Applicable (default)<br />&bull; N: Northbound<br />&bull; E: Eastbound<br />&bull; S: Southbound<br />&bull; O / W: Westbound | String | TomTom |
| ASSIGNABLE | Is link used for assignment (1=True, 0=False) | Integer |   |
| CNTYPE | <p>Link connector type<br /><br /></p> <ul> <li>BIKE - bike link</li> <li>CRAIL - commuter rail</li> <li>FERRY- ferry link</li> <li>HRAIL - heavy rail link</li> <li>LRAIL- light rail link</li> <li>MAZ - MAZ connector link</li> <li>PED - ped link</li> <li>TANA - regular network link</li> <li>TAP - TAP link</li> <li>TAZ - TAZ connector link</li> <li>USE - HOV (user class) link</li> </ul> | String |   |
| TRANSIT | Is Transit link | Integer |   |
| USECLASS | <p>Link user class</p> <p>0 - NA; link open to everyone<br />2 - HOV 2+<br />3 - HOV 3+<br />4 - No combination trucks</p> | Integer |   |
| TOLLBOOTH | <p>Toll link</p> <p>1 - Benicia-Martinez Bridge<br />2 - Carquinez Bridge<br />3 - Richmond Bridge<br />4 - Golden Gate Bridge<br />5 - San Francisco/Oakland Bay Bridge<br />6 - San Mateo Bridge<br />7 - Dumbarton Bridge<br />8 - Antioch Bridge<br />12 - I-680 express lane</p> | Integer |   |
| FT | <p>Facility type</p> <p>0 - Connector<br />1 - Freeway to Freeway<br />2 - Freeway<br />3 - Expressway<br />4 - Collector<br />5 - Ramp<br />7 - Major Arterial</p> | Integer |   |
| FFS | Free flow speed calculated from TANA KPH | Integer |   |
| NUMLANES | Model number of lanes | Integer |   |
| HIGHWAYT | <p>Highway type</p> <ul> <li>footway</li> <li>footway_unconstructed</li> <li>pedestrian</li> <li>steps</li> </ul> | String | Open Street Map |
| B_CLASS | <p>Bike Class</p> <p>0 - Unclassified Street<br />1 - Class I Trail<br />2 - Class II Route<br />3 - Class III Route</p> | Integer | BikeMapper |
| REPRIOR | <p>Priority</p> <p>2 - Highly Desirable<br />1 - Desirable<br />0 - No Preference<br />-1 - Undesirable<br />-2 - Highly Undesirable</p> | Integer | BikeMapper |
| GRADE_CAT | <p>Grade class</p> <p>4 - 18% or High Grade<br />3 - 10-18% Grade<br />2 - 5-10% Grade<br />1 - 0-5% Grade</p> | Integer | BikeMapper |
| PED_FLAG | Pedestrian access (Y=yes; blank=no) | String | BikeMapper |
| BIKEPEDOK | Bridge that allows bike and peds (1=true, 0=false) | Integer | BikeMapper |
| PEMSID | PEMS ID | Integer | PEMS |
| PEMSLANES | PEMS number of lanes | Integer | PEMS |
| PEMSDIST | Distance from link to PEMS station | Float | PEMS |
| TAP_DRIVE | TAP link to parking lot (1=true) | Int | MTC |
   


## Output Files

## Model Schematic

## Level of Service Information

## Networks

