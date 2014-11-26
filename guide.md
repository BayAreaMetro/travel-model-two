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

* Run `VoyagerFileAPIInstaller.msi`, which is included in the `CTRAMP\runtime` folder
* Ensure `VoyagerFileAccess.dll` is in the `CTRAMP\runtime` folder
* Ensure the Microsoft Visual C++ 2012 redistributable is installed on the matrix server machine.  Make sure to get version “110” DLLs (`MSVCR110.dll` and `MSVCP110.dll`).  These files can be obtained from the [Microsoft](http://www.microsoft.com/en-us/default.aspx). Download and install `vcredist_x64.exe`.

#### Citilabs Cube Cluster
The Cube Cluster software allows Cube scripts to be multi-threaded. In the current approach, the travel model uses 64 computing nodes across four machines. The Cube scripts can be manipulated to use any number of computing nodes across any number of machines, provided each machine has, at a minimum, a Cube Voyager node license (for the time being, MTC has found 64 nodes on a single machine to be the most effective -- in terms of reliability and run time -- approach). Cube Cluster is not strictly necessary, as the Cube scripts can be modified to use only a single computing node. Such an approach would dramatically increase run times.

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
3.  a client, the CT-RAMP software in this case.

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

* model -- contains all of the [Utility Expression Calculators](http://analytics.mtc.ca.gov/foswiki/Main/UtilityExpressionCalculator) files that specify the choice models;
* runtime -- contains all of the Java configuration and `JAR` (executable) files, as well as the files necessary for Java to communicate with Cube;
* scripts -- contains all of the Cube scripts and associated helper files.

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
The CT-RAMP software is controlled by a standard Java properties file.  The table below identifies, describes, and provides on example of, each of the variables CT-RAMP expects to be in the properties file.  After the initial configuration, only a handful of these properties willl be modified in a typical application of the travel model.  The primary use for many of teh variables is to facilitate model calibration and/or debugging.  Comments in the properties file preceeded with a pound (#) are ignored.

| **Property** | **Data Type** | **Example** | **Purpose** |
|--------------|---------------|-------------|-------------|
| Trace | Boolean | false | True or False whether to trace zones |
| Trace.otaz | Integer | 1638 | Specify which origin taz to trace |
| Trace.dtaz | Integer | 2447 | Specify which destination taz to trace |
| Seek | Boolean | false | True or False whether to seek households |
| Process.Debug.HHs.Only | Boolean | false | True of False whether to debug households |
| Debug.Trace.HouseholdIdList | String | 566425 | Specify which household IDs to trace |
| run.this.household.only | String | 566425 | Specify that this household ID only will be run through the model |
| Project.Directory | String | %project.folder% | File locations specified in the properties file as well as the UEC DataSheet pages are expressed as relative to this location.  %project.folder% is set by RunModel.bat. |
| Model.Random.Seed | Integer | 1 | Starting value for model random seed number (added to household IDs to create unique random number for each household) |
| RunModel.MatrixServerAddress | String | 156.75.49.78 | matrix server address |
| RunModel.MatrixServerPort | Integer | 1191 | matrix server port number |
| RunModel.HouseholdServerAddress | String | 156.75.49.78 | household server address |
| RunModel.HouseholdServerPort | Integer | 1117 | household server port number |
| generic.path | String | %project.folder%/input/ | Inputs folder |
| scenario.path | String | %project.folder%/ | scenario folder |
| skims.path | String | %project.folder%/skims/ | Skim matrix files folder |
| uec.path | String | %project.folder%/ctramp/model | UEC folder |
|   |   |   |   |
| acc.jppf | Boolean |  true | Run accessibility calculation with JPPF |
| acc.without.jppf.numThreads |  Integer | 20 |  Num threads for local threaded (but not distributed JPPF) setup |
| acc.destination.sampleRate | Float |  0.05 | Percent of destinations to calculate accessibility measures for in order to speed up the model |
| acc.uec.file | String | %project.folder%/ctramp/model/Accessibilities.xls | Accessibilities.xls location |
| acc.data.page | Integer | 0 | Accessibilities data page |
| acc.transit.offpeak.page | Integer | 1 | Accessibilities offpeak page |
| acc.transit.peak.page | Integer | 2 | Accessibilities peak page |
| acc.transit.walkaccess.page | Integer | 3 | Accessibilities walk access page |
| acc.transit.driveaccess.page | Integer | 4 | Accessibilities drive access page |
| acc.sov.offpeak.page | Integer | 5 | Accessibilities SOV offpeak |
| acc.sov.peak.page | Integer | 6 | Accessibilities SOV peak |
| acc.hov.offpeak.page | Integer | 7 | Accessibilities HOV offpeak |
| acc.hov.peak.page | Integer | 8 | Accessibilities HOV peak |
| acc.nonmotorized.page | Integer | 9 | Accessibilities non-motorized |
| acc.constants.page | Integer | 10 | Accessibilities constants |
| acc.sizeTerm.page | Integer | 11 | Accessibilities size terms |
| acc.schoolSizeTerm.page | Integer | 12 | Accessibilities school size terms |
| acc.workerSizeTerm.page | Integer | 13 | Accessibilities worker size terms |
| acc.dcUtility.uec.file | String | %project.folder%/ctramp/model/Accessibilities_DC.xls | Accessibilities_DC.xls location |
| acc.dcUtility.data.page | Integer | 0 | DC Accessibilities data page |
| acc.dcUtility.page | Integer | 1 | DC Accessibilities utility page |
| accessibility.alts.file | String | Acc_alts.csv | Accessibilities alternatives |
| acc.output.file | String | /ctramp_output/accessibilities.csv | Accessibilities.csv location |
| acc.read.input.file | Boolean | false | Read the accessibilities as input instead of running the module |
| acc.mandatory.uec.file | String | %project.folder%/ctramp/model/MandatoryAccess.xls | MandatoryAccess.xls location |
| acc.mandatory.data.page | Integer | 0 | Mandatory Access data page |
| acc.mandatory.auto.page | Integer | 1 | Mandatory Access auto page |
| acc.mandatory.autoLogsum.page | Integer | 2 | Mandatory Access autoLogsum page |
| acc.mandatory.bestWalkTransit.page | Integer | 3 | Mandatory Access best Walk Transit page |
| acc.mandatory.bestDriveTransit.page | Integer | 4 | Mandatory Access best Drive Transit page |
| acc.mandatory.transitLogsum.page | Integer | 5 | Mandatory Access transit logsum page |
|   |   |   |   |
| PopulationSynthesizer.InputToCTRAMP.HouseholdFile | String | popsyn/HHFile_2000_MAZ.csv | location of popsyn households file |
| PopulationSynthesizer.InputToCTRAMP.PersonFile | String | popsyn/PersonFile.2000.csv | location of popsyn persons file |
| PopulationSynthesizer.OccupCodes | String | popsyn/pecas_occ_occsoc.csv | location of popsyn pecas_occ_occsoc.csv file |
| PopulationSynthesizer.IndustryCodes | String | popsyn/activity_code_indcen.csv | location of popsyn activity_code_indcen.csv file |
|   |   |   |   |
| maz.tap.tapLines | String |  trn/tapLines.csv | TAP lines for trimming MAZ to TAP set to include only further away TAPs if they serve new lines |
| maz.tap.distance.file | String | skims/ped_distance_maz_tap.txt | location of the MAZ TAP distance file |
| maz.maz.distance.file | String | skims/ped_distance_maz_maz.txt | location of the MAZ MAZ ped distance file |
| maz.maz.bike.distance.file | String | skims/bike_distance_maz_maz.txt | location of the MAZ MAZ bike distance file |
| mgra.walkdistance.file | String | input/mgrataz.walk | location of MAZ walk distance file |
| tap.data.file | String | hwy/tap_data.csv | location of TAP data file |
| tap.data.tap.column | String | tap | tap id key field |
| tap.data.taz.column | String | taz | taz field |
| tap.data.lotid.column | String | lotid | lotid field |
| tap.data.capacity.column | String | capacity | capacity field |
| mgra.socec.file | String | /landuse/maz_data.csv | [[MAZData]] |
| network.node.seq.mapping.file | String | /hwy/mtc_final_network_zone_seq.csv | Node re-numbering file for sequential zone numbers in CT-RAMP |
| taz.data.file | String | /landuse/taz_data.csv | [[TAZData]] |
| taz.tap.access.file | String | /skims/drive_maz_taz_tap.csv | MAZ to TAP drive impedance data |
|   |   |   |   |
| Results.WriteDataToFiles | Boolean | true | write data to files? |
| Results.HouseholdDataFile | String | ctramp_output/householdData.csv | output name of household data file |
| Results.PersonDataFile | String | ctramp_output/personData.csv | output name of person data file |
| Results.IndivTourDataFile | String | ctramp_output/indivTourData.csv | output name of individual tour data file |
| Results.JointTourDataFile | String | ctramp_output/jointTourData.csv | output name of joint tour data file |
| Results.IndivTripDataFile | String | ctramp_output/indivTripData.csv | output name of individual trip data file |
| Results.JointTripDataFile | String | ctramp_output/jointTripData.csv | output name of joint trip data file |
| Results.CBDFile | String | ctramp_output/cbdParking.csv | output name of CBD parking file |
| Results.PNRFile | String | ctramp_output/pnrParking.csv | output name of PNR parking file |
| Results.WriteDataToDatabase | Boolean | false | write data to a database? |
| Results.HouseholdTable | String | household_data | output name of household data file in database |
| Results.PersonTable | String | person_data | output name of person data file in database |
| Results.IndivTourTable | String | indiv_tour_data | output name of individual tour data file in database |
| Results.JointTourTable | String | joint_tour_data | output name of joint tour data file in database |
| Results.IndivTripTable | String | indiv_trip_data | output name of individual trip data file in database |
| Results.JointTripTable | String | joint_trip_data | output name of joint trip data file in database |
| Results.AutoTripMatrix | String | ctramp_output/autoTrips | output name of auto trip matrix |
| Results.TranTripMatrix | String | ctramp_output/tranTrips | output name of transit trip matrix |
| Results.NMotTripMatrix | String | ctramp_output/nmotTrips | output name of non-motorized trip matrix |
| Results.OthrTripMatrix | String | ctramp_output/othrTrips | output name of other modes trip matrix |
| Results.PNRFile | String | ctramp_output/PNRByTAP_Vehicles.csv | output name of PNR by TAP Vehicle Trip file |
| Results.CBDFile | String | ctramp_output/CBDByMGRA_Vehicles.csv | output name of CBD by MGRA Vehicle Trip file |
| Results.MAZAutoTripMatrix.TripMaxDistance |  Float |  1.5 | Max trip distance for MAZ to MAZ auto trip assignment |
| Results.MAZAutoTripMatrix.MaxSeqMazSet1 |  Integer |  25218 | MAZ to MAZ set 1 range |
| Results.MAZAutoTripMatrix.MaxSeqMazSet2 |  Integer |  51661 | MAZ to MAZ set 2 range |
| Results.MAZAutoTripMatrix.MaxSeqMazSet3 |  Integer |  66235 | MAZ to MAZ set 3 range |
|   |   |   |   |
| TourModeChoice.Save.UtilsAndProbs | Boolean | true | Save utilities and probabilities in tour mode choice output files |
| distributed.task.packet.size | Integer | 500 | JPPF distributed task packet size (i.e. number of households per thread) |
|   |   |   |   |
| RunModel.RestartWithHhServer | String | none | model can be restarted with certain files already generated;values include 'none' (run whole model), 'uwsl', 'ao', 'stf' |
| RunModel.PreAutoOwnership | Boolean | true | True or False whether to run this model component |
| RunModel.UsualWorkAndSchoolLocationChoice | Boolean | true | True or False whether to run this model component |
| RunModel.AutoOwnership | Boolean | true | True or False whether to run this model component |
| RunModel.TransponderChoice | Boolean | true | True or False whether to run this model component |
| RunModel.FreeParking | Boolean | true | True or False whether to run this model component |
| RunModel.CoordinatedDailyActivityPattern | Boolean | true | True or False whether to run this model component |
| RunModel.IndividualMandatoryTourFrequency | Boolean | true | True or False whether to run this model component |
| RunModel.MandatoryTourModeChoice | Boolean | true | True or False whether to run this model component |
| RunModel.MandatoryTourDepartureTimeAndDuration | Boolean | true | True or False whether to run this model component |
| RunModel.JointTourFrequency | Boolean | true | True or False whether to run this model component |
| RunModel.JointTourLocationChoice | Boolean | true | True or False whether to run this model component |
| RunModel.JointTourDepartureTimeAndDuration | Boolean | true | True or False whether to run this model component |
| RunModel.JointTourModeChoice | Boolean | true | True or False whether to run this model component |
| RunModel.IndividualNonMandatoryTourFrequency | Boolean | true | True or False whether to run this model component |
| RunModel.IndividualNonMandatoryTourLocationChoice | Boolean | true | True or False whether to run this model component |
| RunModel.IndividualNonMandatoryTourDepartureTimeAndDuration | Boolean | true | True or False whether to run this model component |
| RunModel.IndividualNonMandatoryTourModeChoice | Boolean | true | True or False whether to run this model component |
| RunModel.AtWorkSubTourFrequency | Boolean | true | True or False whether to run this model component |
| RunModel.AtWorkSubTourLocationChoice | Boolean | true | True or False whether to run this model component |
| RunModel.AtWorkSubTourDepartureTimeAndDuration | Boolean | true | True or False whether to run this model component |
| RunModel.AtWorkSubTourModeChoice | Boolean | true | True or False whether to run this model component |
| RunModel.StopFrequency | Boolean | true | True or False whether to run this model component |
| RunModel.StopLocation | Boolean | true | True or False whether to run this model component |
|   |   |   |   |
| uwsl.use.new.soa | Boolean | false | true or false whether to use new soa for the work/school DC model |
| nmdc.use.new.soa | Boolean | false | true or false whether to use new soa for the non-mandatory DC models |
| slc.use.new.soa | Boolean | false | true or false whether to use new soa for the stop location chocie models |
| Results.AutoOwnership | String | ctramp_output/aoResults.csv | auto ownership output file name and location |
| read.pre.ao.results | Boolean | false | read in the old pre-auto ownership results file |
| read.pre.ao.filename | String | ctramp_output/aoResults_pre.csv | pre auto ownership output file nAme and location |
| Results.UsualWorkAndSchoolLocationChoice | String | ctramp_output/wsLocResults.csv | usual work and school location output file name and location |
| read.uwsl.results | Boolean | false | Read in the old uwsl results? |
| read.uwsl.filename | String | ctramp_output/wsLocResults_1.csv | old uwsl result file name and location to read in |
| uwsl.run.workLocChoice | Boolean | true | True or False whether to run this model component |
| uwsl.run.schoolLocChoice | Boolean | true | True or False whether to run this model component |
| uwsl.write.results | Boolean | true | True of False whether to write out usual work and school location results |
|   |   |   |   |
| ao.uec.file | String | AutoOwnership.xls | File name of auto ownership UEC |
| ao.data.page | Integer | 0 | Auto ownership UEC data page |
| ao.model.page | Integer | 1 | Auto ownership UEC utility page |
| uwsl.dc.uec.file | String | TourDestinationChoice.xls | File Name of Tour Destination Choice UEC |
| uwsl.dc2.uec.file | String | TourDestinationChoice2.xls | File Name of Tour Destination Choice 2 UEC |
| uwsl.soa.uec.file | String | DestinationChoiceAlternativeSample.xls | File Name of Destination Choice Alternative Sample UEC |
| uwsl.soa.alts.file | String | DestinationChoiceAlternatives.csv | File name of the alternatives (MGRAs) available to the destination choice models (part of the model design; this should not be changed) |
| uwsl.work.soa.SampleSize | Integer | 30 | Sample size of Work Destination Choice |
| uwsl.school.soa.SampleSize | Integer | 30 | Sample size of School Destination Choice |
| work.soa.uec.file | String | TourDcSoaDistance.xls | File Name of Tour Distance DC SOA UEC for Work Purpose, includes TAZ Size in the expressions |
| work.soa.uec.data | Integer | 0 | Work Tour Distance SOA UEC data page |
| work.soa.uec.model | Integer | 1 | Work Tour Distance SOA UEC utility page |
| univ.soa.uec.file | String | TourDcSoaDistanceNoSchoolSize.xls | File Name of Tour Distance DC SOA UEC for School Purpose; school purposes do not include TAZ Size in the expressions so that the utilities can be stored as exponentiated distance utility matrices for university, and then multiplied by the university segment size terms |
| univ.soa.uec.data | Integer | 0 | University Tour Distance SOA UEC data page |
| univ.soa.uec.model | Integer | 1 | University Tour Distance SOA UEC utility page |
| hs.soa.uec.file | String | TourDcSoaDistanceNoSchoolSize.xls | File Name of Tour Distance DC SOA UEC for School Purpose; school purposes do not include TAZ Size in the expressions so that the utilities can be stored as exponentiated distance utility matrices for high school, and then multiplied by the high school segment size terms |
| hs.soa.uec.data | Integer | 0 | High School Tour Distance SOA UEC data page |
| hs.soa.uec.model | Integer | 2 | High School Tour Distance SOA UEC utility page |
| gs.soa.uec.file | String | TourDcSoaDistanceNoSchoolSize.xls | File Name of Tour Distance DC SOA UEC for School Purpose; school purposes do not include TAZ Size in the expressions so that the utilities can be stored as exponentiated distance utility matrices for grade school, and then multiplied by the grade school segment size terms |
| gs.soa.uec.data | Integer | 0 | Grade School Tour Distance SOA UEC data page |
| gs.soa.uec.model | Integer | 3 | Grade School Tour Distance SOA UEC utility page |
| ps.soa.uec.file | String | TourDcSoaDistanceNoSchoolSize.xls | File Name of Tour Distance DC SOA UEC for School Purpose; school purposes do not include TAZ Size in the expressions so that the utilities can be stored as exponentiated distance utility matrices for preschool, and then multiplied by the preschool segment size terms |
| ps.soa.uec.data | Integer | 0 | Preschool Tour Distance SOA UEC data page |
| ps.soa.uec.model | Integer | 4 | Prescehool Tour Distance SOA UEC utility page |
|   |   |   |   |
| UsualWorkLocationChoice.ShadowPrice.Input.File | String | input/ShadowPricingOutput_work_39.csv | File Name Work Location shadow price |
| UsualSchoolLocationChoice.ShadowPrice.Input.File | String | input/ShadowPricingOutput_school_19.csv | File Name School Location shadow price |
| uwsl.ShadowPricing.Work.MaximumIterations | Integer | 1 | maximum number of iterations for work shadow price |
| uwsl.ShadowPricing.School.MaximumIterations | Integer | 1 | maximum number of iterations for school shadow price |
| uwsl.ShadowPricing.OutputFile | String | ctramp_output/ShadowPricingOutput.csv | output file name for shadow price |
|   |   |   |   |
| tc.choice.avgtts.file | String | ctramp_output/tc_avgtt.csv | File name of average travel times for transponder ownership calculated by CT-RAMP and read in later |
| tc.uec.file | String | TransponderOwnership.xls | File name of transponder ownership UEC |
| tc.data.page | Integer | 0 | Transponder ownership UEC data page |
| tc.model.page | Integer | 1 | Transponder ownership UEC utility page |
|   |   |   |   |
| fp.uec.file | String | ParkingProvision.xls | File name of parking provision UEC |
| fp.data.page | Integer | 0 | Parking Provision UEC data page |
| fp.model.page | Integer | 1 | Parking Provision UEC utility page |
|   |   |   |   |
| cdap.uec.file | String | CoordinatedDailyActivityPattern.xls | File name of CDAP UEC |
| cdap.data.page | Integer | 0 | CDAP UEC data page |
| cdap.one.person.page | Integer | 1 | CDAP UEC utility for one person page |
| cdap.two.person.page | Integer | 2 | CDAP UEC utility for 2 persons page |
| cdap.three.person.page | Integer | 3 | CDAP UEC utility for 3 persons page |
| cdap.all.person.page | Integer | 4 | CDAP UEC utility for All member interation page |
| cdap.joint.page | Integer | 5 | CDAP UEC utility for joint tours page |
| imtf.uec.file | String | MandatoryTourFrequency.xls | File name of Mandatory tour frequency UEC |
| imtf.data.page | Integer | 0 | Mandatory tour frequency UEC data page |
| imtf.model.page | Integer | 1 | mandatory tour frequency UEC utility page |
| nonSchool.soa.uec.file | String | TourDcSoaDistance.xls | File Name of Tour Distance DC SOA UEC for Non Work/School Purposes, includes TAZ Size in the expressions |
| escort.soa.uec.data | Integer | 0 | Escort Tour Distance SOA UEC data page |
| escort.soa.uec.model | Integer | 2 | Escort Tour Distance SOA UEC utility page |
| other.nonman.soa.uec.data | Integer | 0 | Other Non-mandatory Tour Distance SOA UEC data page |
| other.nonman.soa.uec.model | Integer | 3 | Other Non-mandatory Tour Distance SOA UEC utility page |
| atwork.soa.uec.data | Integer | 0 | At-Work Sub-Tour Distance SOA UEC data page |
| atwork.soa.uec.model | Integer | 4 | At-Work Sub-Tour Distance SOA UEC utility page |
| soa.taz.dist.alts.file | String | SoaTazDistAlts.csv | File name of Sample of Alternatives of TAZs |
|   |   |   |   |
| nmdc.dist.alts.file | String | NonMandatoryTlcAlternatives.csv | File name of non-mandatory tour alternatives |
| nmdc.soa.alts.file | String | DestinationChoiceAlternatives.csv | File name of the alternatives (MGRAs) available to the destination choice models (part of the model design; this should not be changed) |
| nmdc.soa.SampleSize | Integer | 30 | Sample size of non-mandatory Destination choice |
| nmdc.uec.file2 | String | TourDestinationChoice2.xls | File Name of Tour Destination Choice 2 UEC |
| nmdc.uec.file | String | TourDestinationChoice.xls | File Name of Tour Destination Choice UEC |
| nmdc.data.page | Integer | 0 | Non-mandatory Tour DC UEC data page |
| nmdc.escort.model.page | Integer | 7 | Escort Tour Destination Choice UEC utility page |
| nmdc.shop.model.page | Integer | 8 | Shop Tour Destination Choice UEC utility page |
| nmdc.maint.model.page | Integer | 9 | Maintenance Tour Destination Choice UEC utility page |
| nmdc.eat.model.page | Integer | 10 | Eating Out Tour Destination Choice UEC utility page |
| nmdc.visit.model.page | Integer | 11 | Visiting Tour Destination Choice UEC utility page |
| nmdc.discr.model.page | Integer | 12 | Discretionary Tour Destination Choice UEC utility page |
| nmdc.atwork.model.page | Integer | 13 | At-Work Sub-Tour Destination Choice UEC utility page |
| nmdc.soa.uec.file | String | DestinationChoiceAlternativeSample.xls | File Name of Destination Choice Alternative Sample UEC |
| nmdc.soa.data.page | Integer | 0 | Non-mandatory TOUR SOA UEC data page |
| nmdc.soa.escort.model.page | Integer | 6 | Escort TOUR SOA UEC utility page |
| nmdc.soa.shop.model.page | Integer | 7 | Shop TOUR SOA UEC utility page |
| nmdc.soa.maint.model.page | Integer | 7 | Maintenance TOUR SOA UEC utility page |
| nmdc.soa.eat.model.page | Integer | 7 | Eating Out TOUR SOA UEC utility page |
| nmdc.soa.visit.model.page | Integer | 7 | Visiting TOUR SOA UEC utility page |
| nmdc.soa.discr.model.page | Integer | 7 | Discretionary TOUR SOA UEC utility page |
| nmdc.soa.atwork.model.page | Integer | 8 | At-Work Sub-Tour SOA UEC utility page |
|   |   |   |   |
| tourModeChoice.uec.file | String | TourModeChoice.xls | File name of Tour Mode choice UEC |
| tourModeChoice.maint.model.page | Integer | 4 | Maintenance Tour Mode Choice UEC utility page |
| tourModeChoice.discr.model.page | Integer | 5 | Discretionary Tour Mode Choice UEC utility page |
| tourModeChoice.atwork.model.page | Integer | 6 | At-Work Sub-Tour Mode Choice UEC utility page |
|   |   |   |   |
| departTime.uec.file | String | TourDepartureAndDuration.xls | File name of Tour TOD Choice UEC |
| departTime.data.page | Integer | 0 | Tour TOD Choice UEC data page |
| departTime.work.page | Integer | 1 | Work Tour TOD Choice UEC utility page |
| departTime.univ.page | Integer | 2 | University Tour TOD Choice UEC utility page |
| departTime.school.page | Integer | 3 | School Tour TOD Choice UEC utility page |
| departTime.escort.page | Integer | 4 | Escort Tour TOD Choice UEC utility page |
| departTime.shop.page | Integer | 5 | Shop Tour TOD Choice UEC utility page |
| departTime.maint.page | Integer | 6 | Maintenance Tour TOD Choice UEC utility page |
| departTime.eat.page | Integer | 7 | Eating Out Tour TOD Choice UEC utility page |
| departTime.visit.page | Integer | 8 | Visiting Tour TOD Choice UEC utility page |
| departTime.discr.page | Integer | 9 | Discretionary Tour TOD Choice UEC utility page |
| departTime.atwork.page | Integer | 10 | At-Work Sub-Tour TOD Choice UEC utility page |
| departTime.alts.file | String | DepartureTimeAndDurationAlternatives.csv | File name of Departure time and duration alternatives |
|   |   |   |   |
| jtfcp.uec.file | String | JointTourFrequency.xls | File name of Joint Tour Frequency UEC |
| jtfcp.alternatives.file | String | JointAlternatives.csv | File name of joint tour alternatives by purpose and party composition combinations |
| jtfcp.data.page | Integer | 0 | Joint Tour Frequency UEC data page |
| jtfcp.freq.comp.page | Integer | 1 | Joint Tour Frequency UEC utility composition page |
| jtfcp.participate.page | Integer | 2 | Joint Tour Frequency UEC utility participation page |
| inmtf.uec.file | String | NonMandatoryIndividualTourFrequency.xls | File name of Individual non-mandatory tour frequency UEC |
| inmtf.FrequencyExtension.ProbabilityFile | String | IndividualNonMandatoryTourFrequencyExtensionProbabilities _p1.csv | File name of Individual non-mandatory tour frequency extension probabilities |
| IndividualNonMandatoryTourFrequency.AlternativesList.InputFile | String | IndividualNonMandatoryTourFrequencyAlternatives.csv | File name of individual non-mandatory tour frequency alternatives (combinations) |
| inmtf.data.page | Integer | 0 | Individual Non-mandatory tour frequency UEC data page |
| inmtf.perstype1.page | Integer | 1 | Individual Non-mandatory tour frequency UEC utility for Full time workers page |
| inmtf.perstype2.page | Integer | 2 | Individual Non-mandatory tour frequency UEC utility for Part time workers page |
| inmtf.perstype3.page | Integer | 3 | Individual Non-mandatory tour frequency UEC utility for University students page |
| inmtf.perstype4.page | Integer | 4 | Individual Non-mandatory tour frequency UEC utility for Non-workers page |
| inmtf.perstype5.page | Integer | 5 | Individual Non-mandatory tour frequency UEC utility for Retirees page |
| inmtf.perstype6.page | Integer | 6 | Individual Non-mandatory tour frequency UEC utility for Driving students page |
| inmtf.perstype7.page | Integer | 7 | Individual Non-mandatory tour frequency UEC utility for Pre-driving students page |
| inmtf.perstype8.page | Integer | 8 | Individual Non-mandatory tour frequency UEC utility for Preschool students page |
|   |   |   |   |
| awtf.uec.file |   | AtWorkSubtourFrequency.xls | File name of at-work sub-tour frequency UEC |
| awtf.data.page | Integer | 0 | At-Work Sub-Tour Frequency UEC Data page |
| awtf.model.page | Integer | 1 | At-Work Sub-Tour Frequency UEC Utility page |
|   |   |   |   |
| stf.uec.file | String | StopFrequency.xls | File name of Stop Frequency UEC |
| stf.purposeLookup.proportions | String | StopPurposeLookupProportions.csv | File name of Stop Purpose Lookup proportions |
| stf.data.page | Integer | 0 | Stop Frequency UEC data page |
| stf.work.page | Integer | 1 | Stop Frequency for Work Tour UEC utility page |
| stf.univ.page | Integer | 2 | Stop Frequency for University Tour UEC utility page |
| stf.school.page | Integer | 3 | Stop Frequency for School Tour UEC utility page |
| stf.escort.page | Integer | 4 | Stop Frequency for Escort Tour UEC utility page |
| stf.shop.page | Integer | 5 | Stop Frequency for Shop Tour UEC utility page |
| stf.maint.page | Integer | 6 | Stop Frequency for Maintenance Tour UEC utility page |
| stf.eat.page | Integer | 7 | Stop Frequency for Eating Out Tour UEC utility page |
| stf.visit.page | Integer | 8 | Stop Frequency for Visiting Tour UEC utility page |
| stf.discr.page | Integer | 9 | Stop Frequency for Discretionary Tour UEC utility page |
| stf.subtour.page | Integer | 10 | Stop Frequency for At-Work Sub-Tour UEC utility page |
|   |   |   |   |
| slc.uec.file | String | StopLocationChoice.xls | File Name of Stop Location Choice UEC |
| slc.uec.data.page | Integer | 0 | Stop Location Choice UEC data page |
| slc.mandatory.uec.model.page | Integer | 1 | Stop Location Choice for Mandatory Tours UEC utility page |
| slc.maintenance.uec.model.page | Integer | 2 | Stop Location Choice for Maintenance Tours UEC utility page |
| slc.discretionary.uec.model.page | Integer | 3 | Stop Location Choice for Discretionary Tours UEC utility page |
| slc.alts.file | String | SlcAlternatives.csv | File name of stop location choice alternatives |
| slc.soa.alts.file | String | DestinationChoiceAlternatives.csv | File name of the alternatives (MGRAs) available to the destination choice models (part of the model design; this should not be changed) |
| auto.slc.soa.distance.uec.file | String | SlcSoaDistanceUtility.xls | File name of Stop Location Sample of Alternatives Choice UEC for tourmodes other than walk or bike - for transit, availability of stop for transit is set in java code |
| auto.slc.soa.distance.data.page | Integer | 0 | Stop Location SOA Choice UEC data page |
| auto.slc.soa.distance.model.page | Integer | 1 | Stop Location SOA Choice UEC utility page |
| slc.soa.size.uec.file | String | SlcSoaSize.xls | File Name of Stop Location Choice Size Terms UEC |
| slc.soa.size.uec.data.page | Integer | 0 | Stop Location Choice Size terms UEC data page |
| slc.soa.size.uec.model.page | Integer | 1 | Stop Location Choice Size terms UEC utility page |
| stop.depart.arrive.proportions | String | StopDepartArriveProportions.csv | File name of Stop Location Time of Day proportions |
| tripModeChoice.uec.file | String | TripModeChoice.xls | File name of Trip mode choice UEC |
|   |   |   |   |
| plc.uec.file | String | ParkLocationChoice.xls | File name of Parking Location Choice UEC |
| plc.uec.data.page | Integer | 0 | Parking Location Choice UEC data page |
| plc.uec.model.page | Integer | 1 | Parking Location Choice UEC utility page |
| plc.alts.corresp.file | String | ParkLocationAlts.csv | File name of parking location alternatives (MAZs) |
| plc.alts.file | String | ParkLocationSampleAlts.csv | File name of parking location sample of alternatives |
|   |   |   |   |
| mgra.avg.cost.output.file | String | ctramp_output/mgraParkingCost.csv | File name of average parking costs by MAZ |
| mgra.avg.cost.trace.zone | Integer | 1814 | MAZ parking cost trace zone |
| mgra.max.parking.distance | Integer | 0.75 | Max parking walk distance |
| mgra.avg.cost.dist.coeff.work | Float | -8.6 | Parking location model coefficient for walking distance to destination for Work purpose |
| mgra.avg.cost.dist.coeff.other | Float | -4.9 | Parking location model coefficient for walking distance to destination for other purposes |
| park.cost.reimb.mean | Float | -0.05 | Parking location model mean parking cost reimbursement |
| park.cost.reimb.std.dev | Float | 0.54 | Parking location model standard deviation for parking cost reimbursement |
|   |   |   |   |
| utility.bestTransitPath.uec.file | String | BestTransitPathUtility.xls | File name of best transit path UEC |
| utility.bestTransitPath.data.page | Integer | 0 | Best Transit Path UEC data page |
| utility.bestTransitPath.tapToTap.ea.page | Integer | 1 | Best Transit Path UEC for TAP to TAP Early AM utility page |
| utility.bestTransitPath.tapToTap.am.page | Integer | 2 | Best Transit Path UEC for TAP to TAP AM utility page |
| utility.bestTransitPath.tapToTap.md.page | Integer | 3 | Best Transit Path UEC for TAP to TAP MD utility page |
| utility.bestTransitPath.tapToTap.pm.page | Integer | 4 | Best Transit Path UEC for TAP to TAP PM utility page |
| utility.bestTransitPath.tapToTap.ev.page | Integer | 5 | Best Transit Path UEC for TAP to TAP Evening utility page |
| utility.bestTransitPath.walkAccess.page | Integer | 6 | Best Transit Path UEC for Walk Access to Transit utility page |
| utility.bestTransitPath.driveAccess.page | Integer | 7 | Best Transit Path UEC for Drive Access to Transit utility page |
| utility.bestTransitPath.walkEgress.page | Integer | 8 | Best Transit Path UEC for Walk Egress to Transit utility page |
| utility.bestTransitPath.driveEgress.page | Integer | 9 | Best Transit Path UEC for Drive Egress to Transit utility page |
|   |   |   |   |
| skims.auto.uec.file | String | AutoSkims.xls | File name of Auto Skims UEC |
| skims.auto.data.page | Integer | 0 | Auto Skims data page |
| skims.auto.ea.page | Integer | 1 | Auto skims Early AM utility page |
| skims.auto.am.page | Integer | 2 | Auto skims AM utility page |
| skims.auto.md.page | Integer | 3 | Auto skims MD utility page |
| skims.auto.pm.page | Integer | 4 | Auto skims PM utility page |
| skims.auto.ev.page | Integer | 5 | Auto skims Evening utility page |
|   |   |   |   |
| taz.distance.uec.file | String | tazDistance.xls | File name of TAZ Distance UEC |
| taz.distance.data.page | Integer | 0 | TAZ Distance UEC data page |
| taz.od.distance.ea.page | Integer | 1 | TAZ Distance UEC Early AM utility page |
| taz.od.distance.am.page | Integer | 2 | TAZ Distance UEC AM utility page |
| taz.od.distance.md.page | Integer | 3 | TAZ Distance UEC MD utility page |
| taz.od.distance.pm.page | Integer | 4 | TAZ Distance UEC PM utility page |
| taz.od.distance.ev.page | Integer | 5 | TAZ Distance UEC Evening utility page |
|   |   |   |   |
| skim.walk.transit.walk.uec.file | String | WalkTransitWalkSkims.xls | File name of Walk Transit Walk Skims UEC |
| skim.walk.transit.walk.data.page | Integer | 0 | Walk Transit Walk Skims UEC data page |
| skim.walk.local.walk.ea.page | Integer | 1 | Walk Local Walk Early AM Skims UEC utility page |
| skim.walk.local.walk.am.page | Integer | 3 | Walk Local Walk AM Skims UEC utility page |
| skim.walk.local.walk.md.page | Integer | 5 | Walk Local Walk MD Skims UEC utility page |
| skim.walk.local.walk.pm.page | Integer | 7 | Walk Local Walk PM Skims UEC utility page |
| skim.walk.local.walk.ev.page | Integer | 9 | Walk Local Walk Evening Skims UEC utility page |
| skim.walk.premium.walk.ea.page | Integer | 2 | Walk Premium Walk Early AM Skims UEC utility page |
| skim.walk.premium.walk.am.page | Integer | 4 | Walk Premium Walk AM Skims UEC utility page |
| skim.walk.premium.walk.md.page | Integer | 6 | Walk Premium Walk MD Skims UEC utility page |
| skim.walk.premium.walk.pm.page | Integer | 8 | Walk Premium Walk PM Skims UEC utility page |
| skim.walk.premium.walk.ev.page | Integer | 10 | Walk Premium Walk Evening Skims UEC utility page |
| skim.walk.transit.drive.uec.file | String | WalkTransitDriveSkims.xls | File name of Walk Transit Drive Skims UEC |
| skim.walk.transit.drive.data.page | Integer | 0 | Walk Transit Drive Skims UEC data page |
| skim.walk.local.drive.ea.page | Integer | 1 | Walk Local Drive Early AM Skims UEC utility page |
| skim.walk.local.drive.am.page | Integer | 3 | Walk Local Drive AM Skims UEC utility page |
| skim.walk.local.drive.md.page | Integer | 5 | Walk Local Drive MD Skims UEC utility page |
| skim.walk.local.drive.pm.page | Integer | 7 | Walk Local Drive PM Skims UEC utility page |
| skim.walk.local.drive.ev.page | Integer | 9 | Walk Local Drive Evening Skims UEC utility page |
| skim.walk.premium.drive.ea.page | Integer | 2 | Walk Premium Drive Early AM Skims UEC utility page |
| skim.walk.premium.drive.am.page | Integer | 4 | Walk Premium Drive AM Skims UEC utility page |
| skim.walk.premium.drive.md.page | Integer | 6 | Walk Premium Drive MD Skims UEC utility page |
| skim.walk.premium.drive.pm.page | Integer | 8 | Walk Premium Drive PM Skims UEC utility page |
| skim.walk.premium.drive.ev.page | Integer | 10 | Walk Premium Drive Evening Skims UEC utility page |
| skim.drive.transit.walk.uec.file | String | DriveTransitWalkSkims.xls | File name of Drive Transit Walk Skims UEC |
| skim.drive.transit.walk.data.page | Integer | 0 | Drive Transit Walk Skims UEC data page |
| skim.drive.local.walk.ea.page | Integer | 1 | Drive Local Walk Early AM Skims UEC utility page |
| skim.drive.local.walk.am.page | Integer | 3 | Drive Local Walk AM Skims UEC utility page |
| skim.drive.local.walk.md.page | Integer | 5 | Drive Local Walk MD Skims UEC utility page |
| skim.drive.local.walk.pm.page | Integer | 7 | Drive Local Walk PM Skims UEC utility page |
| skim.drive.local.walk.ev.page | Integer | 9 | Drive Local Walk Evening Skims UEC utility page |
| skim.drive.premium.walk.ea.page | Integer | 2 | Drive Premium Walk Early AM Skims UEC utility page |
| skim.drive.premium.walk.am.page | Integer | 4 | Drive Premium Walk AM Skims UEC utility page |
| skim.drive.premium.walk.md.page | Integer | 6 | Drive Premium Walk MD Skims UEC utility page |
| skim.drive.premium.walk.pm.page | Integer | 8 | Drive Premium Walk PM Skims UEC utility page |
| skim.drive.premium.walk.ev.page | Integer | 10 | Drive Premium Walk Evening Skims UEC utility page |
|   |   |   |   |
| summit.output.directory | String | ctramp_output/ | File location for Summit output |
| summit.purpose.Work | Integer | 1 | Specify code for Work Purpose |
| summit.purpose.University | Integer | 2 | Specify code for University Purpose |
| summit.purpose.School | Integer | 3 | Specify code for School Purpose |
| summit.purpose.Escort | Integer | 4 | Specify code for Escort Purpose |
| summit.purpose.Shop | Integer | 4 | Specify code for Shop Purpose |
| summit.purpose.Maintenance | Integer | 4 | Specify code for Maintenance Purpose |
| summit.purpose.EatingOut | Integer | 5 | Specify code for Eating out Purpose |
| summit.purpose.Visiting | Integer | 5 | Specify code for Visiting Purpose |
| summit.purpose.Discretionary | Integer | 5 | Specify code for Discretionary Purpose |
| summit.purpose.WorkBased | Integer | 6 | Specify code for At-Work Sub Tour Purpose |
| summit.filename.1 | String | Work | Specify file name for Work Purpose |
| summit.filename.2 | String | University | Specify file name for University Purpose |
| summit.filename.3 | String | School | Specify file name for School Purpose |
| summit.filename.4 | String | Maintenance | Specify file name for Maintenance Purpose |
| summit.filename.5 | String | Discretionary | Specify file name for Discretionary Purpose |
| summit.filename.6 | String | Workbased | Specify file name for At-Work Sub tour Purpose |
| summit.ivt.file.1 | Float | -0.016 | Specify in-vehicle time coefficient for Work Purpose |
| summit.ivt.file.2 | Float | -0.016 | Specify in-vehicle time coefficient for University Purpose |
| summit.ivt.file.3 | Float | -0.01 | Specify in-vehicle time coefficient for School Purpose |
| summit.ivt.file.4 | Float | -0.017 | Specify in-vehicle time coefficient for Maintenance Purpose |
| summit.ivt.file.5 | Float | -0.015 | Specify in-vehicle time coefficient for Discretionary Purpose |
| summit.ivt.file.6 | Float | -0.032 | Specify in-vehicle time coefficient for At-work Sub tour Purpose |
| summit.modes | Integer | 26 | Specify number of modes in the model |
| summit.mode.array | String | 0,0,0,0,0,0,0,0,0, 0, 1, 1,1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0 | Specify mode array; 0 for auto modes/school bus mode, 1 for walk transit, 2 for drive transit modes |
| summit.upperEA | Integer | 3 | Specify upper limit code for Early AM time period |
| summit.upperAM | Integer | 9 | Specify upper limit code for AM time period |
| summit.upperMD | Integer | 22 | Specify upper limit code for Midday time period |
| summit.upperPM | Integer | 29 | Specify upper limit code for PM time period |
|   |   |   |   |
| occ3plus.purpose.Work | Float | 3.5 | Specify 3+ occupancy multiplier for trip table creation for Work Purpose |
| occ3plus.purpose.University | Float | 3.5 | Specify 3+ occupancy multiplier for trip table creation for University Purpose |
| occ3plus.purpose.School | Float | 3.5 | Specify 3+ occupancy multiplier for trip table creation for School Purpose |
| occ3plus.purpose.Escort | Float | 3.5 | Specify 3+ occupancy multiplier for trip table creation for Escort Purpose |
| occ3plus.purpose.Shop | Float | 3.5 | Specify 3+ occupancy multiplier for trip table creation for Shop Purpose |
| occ3plus.purpose.Maintenance | Float | 3.5 | Specify 3+ occupancy multiplier for trip table creation for Maintenance Purpose |
| occ3plus.purpose.EatingOut | Float | 3.5 | Specify 3+ occupancy multiplier for trip table creation for Eating Out Purpose |
| occ3plus.purpose.Visiting | Float | 3.5 | Specify 3+ occupancy multiplier for trip table creation for Visiting Purpose |
| occ3plus.purpose.Discretionary | Float | 3.5 | Specify 3+ occupancy multiplier for trip table creation for Discretionary Purpose |
| occ3plus.purpose.WorkBased | Float | 3.5 | Specify 3+ occupancy multiplier for trip table creation for At-Work Sub Tour Purpose |
| workSchoolSegments.definitions | String | ctramp_output/workSchoolSegments.definitions | Work school segment definitions file |
|   |   |   |   |
| HouseholdManager.MinValueOfTime | Float | 1.0 | Distributed person VOT settings |
| HouseholdManager.MaxValueOfTime | Float | 50 | Distributed person VOT settings |
| HouseholdManager.MeanValueOfTime.Values | String | 6.01, 8.81, 10.44,12.86 | Distributed person VOT settings |
| HouseholdManager.MeanValueOfTime.Income.Limits | String | 30000, 60000, 100000 | Distributed person VOT settings |
| HouseholdManager.Mean.ValueOfTime.Multiplier.Mu | Float | 0.684 | Distributed person VOT settings |
| HouseholdManager.ValueOfTime.Lognormal.Sigma | Float | 0.87 | Distributed person VOT settings |
| HouseholdManager.HH.ValueOfTime.Multiplier.Under18 | Float |  0.66667 | Distributed person VOT settings |
| HouseholdManager.MinValueOfTime | Float | 1 | Distributed person VOT settings |

## Input Files
The table below contains brief descriptions of the input files required to execute the travel model. 

| **File name** | **Purpose** | **Folder location** | **File type** | **File format** |
|---------------|-------------|---------------------|---------------|-----------------|
| mtc_final_network.net | Highway, bike, walk network | hwy\ | [Citilabs Cube](http://citilabs.com/products/cube)| Networks |
| mazData.csv | Micro zone data  | landuse\ | CSV | MazData |
| tazData.csv | Travel analysis zone data | landuse\ | CSV | TazData |
| truckFF.dat | Friction factors for the commercial vehicle distribution models | nonres\ | ASCII | TruckDistribution |
| truckkfact.k22.z1454.mat | "K-factors" for the commercial vehicle distribution models | nonres\ | [Citilabs Cube](http://citilabs.com/products/cube) | TruckDistribution |
| truck_kfactors_taz.csv | "K-factors" for the commercial vehicle distribution models | nonres\ | CSV | TruckDistribution |
| ixDailyYYYY.tpp | Internal-external fixed trip table for year YYYY | nonres\ | [Citilabs Cube](http://citilabs.com/products/cube) | FixedDemand |
| IXDaily2006x4.may2208.new | Internal-external input fixed trip table | nonres\ | [Citilabs Cube](http://citilabs.com/products/cube) | FixedDemand |
|  YYYY_fromtoAAA.csv |  Airport passenger fixed trips for year YYYY and airport AAA  | nonres\ | CSV | FixedDemand |
| hhFile_YYYY_MAZ.csv | Synthetic population household file at the MAZ level for year YYYY | popsyn\ | CSV | PopSynHousehold |
| personFile.YYYY.csv | Synthetic population person file for year YYYY | popsyn\ | CSV |   |
| activity_code_indcen.csv | Census occupation to activity coding | popsyn\ | CSV |   |
| pecas_occ_occcen1.csv | Census occupation to work occupation coding | popsyn\ | CSV |   |
| transitLines.lin | Transit lines | trn\transit_lines | [Citilabs Cube](http://citilabs.com/products/cube)| TransitNetwork  |
| transitFactors_MMMM.fac | Cube Public Transport (PT) factor files by transit line haul mode MMMM | trn\transit_support | [Citilabs Cube](http://citilabs.com/products/cube) | TransitNetwork |

## Output Files

## Model Schematic

## Level of Service Information

## Networks

