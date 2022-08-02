# User Guide

*Work in Progress*

*Model Version TM2.1 - transit-ccr*

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
The travel model currently uses version 6.4.2 of [Citilabs Cube](http://www.citilabs.com/) software. The Cube software is used to build skims, manipulate networks, manipulate matrices, and perform assignments.

#### Citilabs Cube Voyager 64bit Matrix I/O DLL
The CT-RAMP software, as discussed below, needs to access data stored in a format dictated by Cube. This is accomplished through a 64-bit DLL library specifically for matrix I/O,which must be accessible through the `PATH` environment variable.  To install the DLL:

* Run `VoyagerFileAPIInstaller.msi`, which is included in the [`CTRAMP\runtime`](https://github.com/MetropolitanTransportationCommission/travel-model-two/tree/master/model-files/runtime) folder
* Ensure `VoyagerFileAccess.dll` is in the [`CTRAMP\runtime`](https://github.com/MetropolitanTransportationCommission/travel-model-two/tree/master/model-files/runtime) folder
* Ensure the Microsoft Visual C++ 2012 redistributable is installed on the matrix server machine.  Make sure to get version “110” DLLs (`MSVCR110.dll` and `MSVCP110.dll`).  These files can be obtained from the [Microsoft](http://www.microsoft.com/en-us/default.aspx). Download and install `vcredist_x64.exe`.

#### Citilabs Cube Cluster
The [Cube Cluster software](http://citilabs.com/software/products/cube/cube-cluster) allows Cube scripts to be multi-threaded. In the current approach, the travel model uses 64 computing nodes across four machines. The Cube scripts can be manipulated to use any number of computing nodes across any number of machines, provided each machine has, at a minimum, a Cube Voyager node license (for the time being, MTC has found 64 nodes on a single machine to be the most effective approach -- in terms of reliability and run time). Cube Cluster is not strictly necessary, as the Cube scripts can be modified to use only a single computing node. Such an approach would dramatically increase run times.

#### Java and CT-RAMP
MTC's travel model operates on the open-source Coordinated Travel - Regional Activity-based Modeling Platform (or CT-RAMP) developed by [Parsons Brinckerhoff](pbworld.com). The software is written in the [Java](http://java.com/en) programming language.  CT-RAMP requires the 64-bit Java Development Kit version 1.8 or later to be installed on each computer running the CT-RAMP software. The Java Development Kit includes the Java Runtime Environment. The 64-bit version of the software allows CT-RAMP to take advantage of larger memory addresses. The details of setting up and configuring the software are presented in the [Setup and Configuration section](#setup-and-configuration) of this guide.

#### Python
Certain network processing programs are written in [Python](https://www.python.org/). Python must be installed on the computer executing the Cube scripts -- `mainmodel` in MTC's configuration.

#### Python Rtree library
The open source [Python `rtree` library](http://www.lfd.uci.edu/~gohlke/pythonlibs/#rtree) is required for a script that dynamically codes link area type based on land use data.  The `rtree` library provides an efficient spatial index for looking up all spatial units within a buffered distance from each spatial unit. To install, open a dos prompt, navigate to the directory and type: pip install Rtree-0.8.2-cp27-cp27m-win_amd64.whl

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

* Intra-step threading: The `DistributeINTRAStep` keyword allows calculations that are performed across a matrix of data to be performed in blocks -- specifically rows of data -- across multiple threads. MTC uses intra-step threading in highway assignment, allowing shortest paths to be constructed for more than one origin at a time. Complex matrix calculations can also benefit from intra-step threading.
* Multi-step threading: The `DistributeMULTIStep` keyword allows blocks of code to be distributed across multiple threads. For example, if the same calculations are being performed for five different time periods, the same block of code (with variables) can be distributed across computers for parallel processing. This type of Cube multi-threading is a bit less flexible than the intra-step threading as it requires threads to be identified *a priori* (e.g., thread one will do the calculations for time period A), where the intra-step threading can be given a list of available processes and use what is available. MTC uses multi-step threading for highway skimming, transit skimming, highway assignment, the conversion of trip lists to trip matrices, highway assignment, and transit assignment.

As noted in the [Computing Environment](#computing-environment) section, the MTC travel model specifies the Cube scripts to take advantage of 64 threads. A knowledgeable user can easily adjust the necessary scripts to take advantage of more or fewer processors.

#### CT-RAMP
The CT-RAMP software allows for the choice models to be distributed across threads and machines. The MTC application currently uses four machines, but the CT-RAMP software can be configured fairly easy to utilize fewer or more machines. CT-RAMP uses the [Java Parallel Processing Framework](http://www.jppf.org/), or JPPF, to manage the distribution of tasks. JPPF is an open-source Java package. The JPPF framework consists of three main parts as follows:

1. a driver, also referred to as the JPPF server;
2. one or more nodes, typically one node is established on each machine; and,
3. a client, the CT-RAMP software in this case.

As noted on the [Computing Environment](#computing-environment) section, MTC uses four computers with the names `mainmodel`, `satmodel`, `satmodel2`, and `satmodel3`. The JPPF driver process is executed on `mainmodel` and acts like a traffic cop by acquiring tasks from the client and distributing those tasks to the node processes. When the node processes complete tasks, the results are returned back to the client via the JPPF driver. Three nodes are used in the MTC application, one each on `satmodel`, `satmodel2`, and `satmodel3` (each node runs 12 processes). These three nodes are created prior to executing a model run. After being created, each node listens for tasks from the JPPF driver.

Node processes receive tasks, perform those tasks, and return the results. Nodes are configured to communicate with the driver process when they are started. MTC configures the nodes to use 90 GB of memory and 12 threads (see the [Setup and Configuration](#setup-and-configuration) section for details on where these parameters are specified). The JPPF driver attempts to balance computational loads across available nodes. The driver also retrieves class files, i.e. sets of Java code, from the client application and passes those to the nodes as needed.

The CT-RAMP software, which serves as the client, is responsible for creating task objects that can be run in parallel and submitting those to the driver. Because the MTC travel model simulates households, the CT-RAMP software creates packets of `N` (a user-configurable quantity, e.g. 500) households and sends those packets to the nodes for processing. As the nodes complete tasks and return them to the driver, the driver gives the nodes new tasks, attempting to keep each node uniformly busy.

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
The MTC travel model folder structure is shown below. Typically the parent directory will be named for the scenario to be run (e.g. '2010_base'). The parent directory contains two subfolders `ctramp` and `input`, and one MS-DOS batch file, `RunModel.bat`. This folder can be placed in any directory on a computer designated as the main controller of the program flow. On MTC's set up, these files are placed on the `mainmodel` computer (see [System Design](#system-design) section for more details).

* \Scenario_Folder
    - \ct-ramp
    - \input
    - RunModel.bat

The `CTRAMP` directory contains all of the model configuration files, Java instructions, Cube, EMME, EMME and Python scripts required to run the travel model, organized in the following three folders:

* [model](https://github.com/MetropolitanTransportationCommission/travel-model-two/tree/master/model-files/model) -- contains all of the [Utility Expression Calculators](http://analytics.mtc.ca.gov/foswiki/Main/UtilityExpressionCalculator) files that specify the choice models; [CHECK_DAVID: should the links be for master branch or transit-ccr?]
* [runtime](https://github.com/MetropolitanTransportationCommission/travel-model-two/tree/master/model-files/runtime) -- contains all of the Java configuration and `JAR` (executable) files, as well as the files necessary for Java to communicate with Cube; [CHECK_DAVID: should the links be for master branch or transit-ccr?]
* [scripts](https://github.com/MetropolitanTransportationCommission/travel-model-two/tree/master/model-files/scripts) -- contains all of the Cube, EMME, and Python scripts along with associated helper files. [CHECK_DAVID: should the links be for master branch or transit-ccr?]

The `INPUT` directory contains all of the input files (see the [Input Files](#input-files) section) required to run a specific scenario. All the input files are available on [Box](https://mtcdrive.box.com/s/7fpzlg3vmtk5x65r7lp4q3k5kvp1v3p4). MTC will deliver the model with a set of scenario-specific set of inputs. When configuring the model on a new computing system, one should make sure that the results from an established scenario can be recreated before developing and analyzing a new scenario. The `INPUT` directory contains the following folders:

* `hwy` -- contains the input master network with all zone centroids as well (TAZ, MAZ, and TAP) (see the [Networks](#networks) section);
* `trn` -- contains all of the input transit network files (see the [Networks](#networks) section);
* `landuse` -- contains the MAZ and TAZ level socio-economic input land use files;
* `nonres` -- contains the fixed, year-specific internal/external trip tables, the fixed, year-specific air passenger trip tables, and files used to support the commercial vehicle model;
* `popsyn` -- contains the synthetic population files;
* `visualizer` -- contains the survey data and other helper files needed for the visualizer;

The `RunModel.bat` script contains a list of MS-DOS instructions that control model flow.

### Step 2: Map a network drive to share across computers
As noted in the previous section, the MTC model files can be placed within any directory. After establishing this location, the user must map a network drive to a shared folder to allow other computers access. On MTC's machine, the directory `E:\MainModelShare` is first mapped to the letter drive `M:\` and this directory is then shared across on the network (`M:\ = \\MainModel\MainModelShare\`).

Satellite computers should also map the letter drive `M:\` to this network location.

Please note that the model components running on the main machine should use the local version of the directory (i.e. `M:\Projects\`) rather than the network version (i.e. `\\MainModel\MainModelShare\Projects\`).

MTC has created scenarios for 2000, 2005, 2010 and 2015. The model is calibrated and validated to 2010 observed data.

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

A file that needs to be edited prior to executing a model run is the `mtctm2.properties` file located in `CTRAMP\runtime\`. This file serves as the general control module for the entire CT-RAMP application. At this stage, the following variables need to be modified for the software to execute the model properly.

| **Statement**                                     | **Purpose**                                                                                           |
|---------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| `RunModel.MatrixServerAddress = 192.168.1.200`    | The IP address of the machine upon which the Matrix Manager is being executed (`satmodel1` at MTC)    |
| `RunModel.HouseholdServerAddress = 192.168.1.200` | The IP address of the machine upon which the Household Manager is being executed (`satmodel1` at MTC) |

### Step 4: Configure `RunModel.bat` and `CTRampEnv.bat`
The file `RunModel.bat` MS-DOS batch file that executes the model stream needs to be consistent with the network and if a specialized model run is being executed, the model flow logic and/or sample rates may need to be adjusted. The following statements may need to be configured within this file:

| **Statement**                                                                | **Purpose** |
|:------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| `set SAMPLERATE_ITERATION{iteration}=0.2`                                    | Set choice model household sample rate by iteration |
model run |
| `set MODEL_YEAR=2015`                                                        | Set model year |
| `set BASE_SCRIPTS=CTRAMP\scripts`                                            | Set scripts folder |
| `set /A MAX_ITERATION=3`                                                     | Set the model feedback iterations |
| `set /A MAX_INNER_ITERATION=2`                                                     | Set the inner transit capacity restraint iterations |

The file `CTRampEnv.bat` MS-DOS batch file points to locations of executables and contains some additional information on machine configuration. The following statements may need to be configured within this file:

| **Statement**                                                                | **Purpose** |
|:------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| `set JAVA_PATH=C:\Program Files\Java\jre1.8.0_301`                           | Specify the 64-bit Java path; version 1.8.0+ |
| `set TPP_PATH=C:\Progam Files\Citilabs\CubeVoyager`                          | Specify the Cube Voyager path |
| `set CUBE_PATH=C:\Progam Files (x86)\Citilabs\Cube`                          | Specify the Cube path |
| `set PYTHON_PATH=D:\Anaconda2`                                 | Specify the Python path |
| `set RUNTIME=CTRAMP\runtime`                                                 | Specify the location of the CT-RAMP software (relative to the project directory) |
|`set JAVA_32_PORT=1190`                                                       | Specify the port for Java 32 bit matrix reader\writer (not currently used) |
|`set MATRIX_MANAGER_PORT=1191`                                                | Specify the port for the matrix manager |
|`set HH_MANAGER_PORT=1129`                                                    | Specify the port for the household manager |
| `SET MAIN=WRJMDLPPW08` | Set machine name mainmodel |
| `SET MTC0{1,2,3}=WRJMDLPPW08` | Set machine names for satmodels |
|`set HHMGR_IP=172.24.0.100`                                                   | Specify IP address of household manager |
| `set MATRIX_SERVER=\\%MTC02%`                                        | Machine running matrix data manager |
| `set MATRIX_SERVER_BASE_DIR=%MATRIX_SERVER%\e$\projects\clients\MTC\%SCEN%`          | Machine running matrix data manager base directory |
| `set MATRIX_SERVER_ABSOLUTE_BASE_DIR=e:\projects\clients\MTC\%SCEN%`                 | Machine running matrix data manager absolute directory |
| `set MATRIX_SERVER_JAVA_PATH=C:\Program Files\Java\jre1.8.0_261`              | Machine running matrix data manager Java install |
| `set HH_SERVER=\\%MTC02%`                                            | Machine running household data manager |
| `set HH_SERVER_BASE_DIR=%HH_SERVER%\e$\projects\clients\MTC\%SCEN%`                  | Machine running household data manager base directory |
| `set HH_SERVER_ABSOLUTE_BASE_DIR=e:\projects\clients\MTC\%SCEN%`                     | Machine running household data manager absolute directory |
| `set HH_SERVER_JAVA_PATH=C:\Program Files\Java\jre1.8.0_261`                  | Machine running household data manager Java install |
| `set USERNAME=`                                                                    | Username for remote access using psexec |
| `set PASSWORD=`                                                                   | Password for remote access using psexec |


Now that the model is configured, the user can run the model, as described in the [Model Execution](#model-execution) section.

## Model Execution

This page describes how `RunModel.bat` executes the travel model. For:

* a description of the underlying computing environment, see [Computing Environment](#computing-environment);
* a general description of the underlying system design, see [System Design](#system-design);
* a description of the configuration files that may need to be modified before executing the model, see [Setup and Configuration](#setup-and-configuration).

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
copy INPUT\hwy\                 hwy\       /Y
copy INPUT\trn\                 trn\       /Y
copy INPUT\landuse\             landuse\   /Y
copy INPUT\popsyn\              popsyn\    /Y
copy INPUT\nonres\              nonres\    /Y
copy INPUT\warmstart\main\      main\      /Y
copy INPUT\warmstart\nonres\    nonres\    /Y
```
After the directories are created, copies are made to the remote machines for access by the household and matrix servers.

```dosbatch
SET HH_DEPENDENCIES=(hwy popsyn landuse skims trn CTRAMP logs)
IF NOT EXIST "%HH_SERVER_BASE_DIR%" MKDIR "%HH_SERVER_BASE_DIR%"
FOR %%A IN %HH_DEPENDENCIES% DO (
  IF NOT EXIST "%HH_SERVER_BASE_DIR%\%%A" MKDIR "%HH_SERVER_BASE_DIR%\%%A"
)
ROBOCOPY CTRAMP %HH_SERVER_BASE_DIR%\CTRAMP *.* /E /NDL /NFL

:: Create necessary directory structure for matrix data server
SET MATRIX_DEPENDENCIES=(skims CTRAMP logs ctramp_output)
IF NOT EXIST "%MATRIX_SERVER_BASE_DIR%" MKDIR "%MATRIX_SERVER_BASE_DIR%"
FOR %%A IN %MATRIX_DEPENDENCIES% DO (
    IF NOT EXIST "%MATRIX_SERVER_BASE_DIR%\%%A" MKDIR "%MATRIX_SERVER_BASE_DIR%\%%A"
)
ROBOCOPY CTRAMP "%MATRIX_SERVER_BASE_DIR%\CTRAMP" *.* /E /NDL /NFL
```

### Step 4: Pre-process steps
Several steps are needed to prepare the inputs for use in the model.  The following Cube scripts are executed to perform the following:

* `preprocess_input_net.job` -- preprocessing input network to add a Feet field for distance and fix space issue in CNTYPE field
* `writeZoneSystems.job` -- write a batch file with number of tazs, taps, and mazs
* `zone_seq_net_builder.job` -- build an internal numbering scheme for the network nodes to play nice with Cube
* `zone_seq_disseminator.py` -- creates all necessary input files based on updated sequential zone numbering
* `renumber.py` -- renumber the TAZs and MAZs in the households data file
* `maz_densities.job` -- writes out the intersection and MAZ XYs
* `createMazDensityFile.py` -- calculates density fields and append those to MAZ file
* `CreateNonMotorizedNetwork.job` -- convert the roadway network into bike and ped networks
* `tap_to_taz_for_parking.job` -- builds a shortest path tree from taps to tazs based on walk distance
* `tap_data_builder.py` -- this script builds the tap csv data file which maps all TAPs to the closest TAZ for that TAP
* `SetTolls.job` -- set network prices (i.e., bridge tolls, express lane tolls) in the roadway network
* `SetHovXferPenalties.job` -- add a penalty of X seconds for dummy links connecting HOV/express lanes and general purpose lanes
* `SetCapClass.job` -- compute area type and populate the `CAPCLASS` network variable
* `setInterchangeDistance.job` -- preprocess freeway link distances to nearest major interchange
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

* `HwySkims.job` -- build the roadway skims
* `BuildTransitNetworks.job` -- build the transit networks using the congested roadway times
* `TransitSkimsPrep.job` -- build the transit skims for five time periods
* `cube_to_emme_network_conversion.py` -- read in a Cube network shapefile and output EMME transaction files to load the network and attributes into EMME for first model iteration
* `create_emme_network.py` -- creates an EMME project folder, database, and a scenario for each time period for first model iteration
* `skim_transit_network.py` -- performs transit skimming and assignment for TM2
* Set the sampling rate based on `SAMPLERATE_ITERATION<iteration>` global variable
* Copy the skims and related files to the remote household and matrix data manager machines

### Step 8:  Execute the CT-RAMP models
The core passenger travel demand models are executed via the CT-RAMP Java code via the following steps:

*  Remote household and matrix servers are started using `psexec`
*  JPPF driver, as needed, is started via `CTRAMP/runtime/runDriver.cmd`
*  JPPF worker nodes, as specified, are started via `CTRAMP\runtime\runNode0.cmd`
*  CT-RAMP models are executed via `CTRAMP/runMTCTM2ABM.cmd`
*  Stops remote servers using `pskill`
*  Copies output matrices from the matrix manager machine back to the main machine
*  `merge_auto_matrices.s` --  merge non-transit trip matrices from the CTRAMP model outputs

### Step 9:  Execute the internal/external and commercial vehicle models
These ancillary demand models are executed via a series of Cube scripts as follows:

* `IxForecasts.job` -- create the internal/external demand matrices forecast
* `IxTimeOfDay.job` -- apply diurnal factors to the daily fixed internal/external demand matrices
* `IxTollChoice.job` -- apply a toll choice model for express lanes to the internal/external demand
* `TruckTripGeneration.job` -- apply the commercial vehicle generation models
* `TruckTripDistribution.job` -- apply the commercial vehicle distribution models
* `TruckTimeOfDay.job` -- apply the commercial vehicle diurnal factors
* `TruckTollChoice.job` -- apply a toll choice model for express lanes with eligible commercial demand

### Step 10: Network Assignment
Demand is located on mode-specific paths through the networks in the assignment step via the following steps:

* `build_and_assign_maz_to_maz_auto.job` -- nearby automobile demand assigned to best path on MAZ-scale network
* `HwyAssign.job` -- using nearby demand as background demand, demand assigned to TAZ-scale network
* `AverageNetworkVolumes.job` -- method of successive averages (MSA) applied across overall model iterations
* `CalculateAverageSpeed.job` -- using the averaged volumes, compute speeds
* `MergeNetworks.job` -- merge time-of-day-specific networks into a single network
* `IF` additional `ITERATION`s are needed, run `HwySkims.job`
* `BuildTransitNetworks.job` -- creates the transit network used for skimming/assignment
* `TransitSkimsPrep.job` -- compute transit skims for five time periods
* `cube_to_emme_network_conversion.py` -- updates the transaction files and attributes in EMME for second model iteration
* `create_emme_network.py` -- updates the congested link times in EMME for second model iteration
* `IF INNER_ITERATION == 1`, `skim_transit_network_py2.py` script resimulates the congested transit assignment for all time periods
* `IF INNER_ITERATION > 1`, `skim_transit_network_py2.py` script resimulates the congested transit assignment only for AM and PM periods
* Start remote matrix server using `psexec`
* Recalculate transit best path via running `CTRAMP\runtime\runTransitPathRecalculator.cmd`

### Step 11: Clean up
The next step of the model run moves all the TP+ printouts to the `/logs` folder and deletes all the temporary TP+ printouts and cluster files.

### Step 12: visualizer
The final step of the model run creates an html visualizer that helps comparing CHTS survey data to current run model outputs. The visualizer is created via `CTRAMP\scripts\visualizer\generateDashboard.bat`


## CT-RAMP Properties File
The CT-RAMP software is controlled by a standard Java [properties file](https://github.com/MetropolitanTransportationCommission/travel-model-two/blob/master/model-files/runtime/mtctm2.properties).  The _forthcoming_ {table, link} below identifies, describes, and provides on example of, each of the variables CT-RAMP expects to be in the properties file.  After the initial configuration, only a handful of these properties willl be modified in a typical application of the travel model.  The primary use for many of the variables is to facilitate model calibration and/or debugging.  Comments in the properties file preceeded with a pound (#) are ignored.


<table>
    <tr>
        <th>Purpose</th>
        <th>Expected Data Type</th>
        <th>Example Value</th>
        <th>Purpose</th>
    </tr>
    <tr>
        <td colspan="4"><a id="cluster_properties"><b>Cluster Properties</b><br><i>Modify when changing cluster configuration or moving to new cluster</i> (properties for java processes) </a></td>
    </tr>
    <tr>
        <td>RunModel.MatrixServerAddress</td>
        <td>String</td>
        <td>10.0.1.46</td>
        <td>Matrix server address</td>
    </tr>
    <tr>
        <td>RunModel.MatrixServerPort</td>
        <td>Integer</td>
        <td>1191</td>
        <td>Matrix server port number</td>
    </tr>
    <tr>
        <td>RunModel.HouseholdServerAddress</td>
        <td>String</td>
        <td>10.0.1.46</td>
        <td>Household server address</td>
    </tr>
    <tr>
        <td>RunModel.HouseholdServerPort</td>
        <td>Integer</td>
        <td>1129</td>
        <td>Household server port number</td>
    </tr>
    <tr>
        <td colspan="4"><a id="logging_properties"><b>Logging and Debugging Properties</b><br><i>Use for tracing households or agents through simulation</i></b></a></td>
    </tr>
    <tr>
        <td>Trace</td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to trace zones</td>
    </tr>
    <tr>
        <td>Trace.otaz </td>
        <td>Integer</td>
        <td>0</td>
        <td>Specify which origin taz to trace</td>
    </tr>
    <tr>
        <td>Trace.dtaz </td>
        <td>Integer</td>
        <td>0</td>
        <td>Specify which destination taz to trace</td>
    </tr>
    <tr>
        <td>Seek </td>
        <td>Boolean</td>
        <td>false</td>
        <td>True or False whether to seek households</td>
    </tr>
    <tr>
        <td>Process.Debug.HHs.Only </td>
        <td>Boolean</td>
        <td>false</td>
        <td>True of False whether to debug households</td>
    </tr>
    <tr>
        <td>Debug.Trace.HouseholdIdList </td>
        <td>Integer</td>
        <td>13748</td>
        <td>Specify which Household ID to trace</td>
    </tr>
    <tr>
        <td>TourModeChoice.Save.UtilsAndProbs </td>
        <td>Boolean</td>
        <td>true</td>
        <td>Save tour mode choice utilities and probabilities for debugging</td>
    </tr>
    <tr>
        <td colspan="4"><a id="path_properties"><b>Path Properties</b><br><i>Modify as needed when copy release to a local run folder</i></b></a></td>
    </tr>
    <tr>
        <td>Project.Directory</td>
        <td>String</td>
        <td>%project.folder%/</td>
        <td>Project.Directory</td>
    </tr>
    <tr>
        <td>generic.path </td>
        <td>String</td>
        <td>%project.folder%/INPUT/</td>
        <td>Inputs folder</td>
    </tr>
    <tr>
        <td>scenario.path </td>
        <td>String</td>
        <td>%project.folder%/</td>
        <td>Scenario folder</td>
    </tr>
    <tr>
        <td>skims.path </td>
        <td>String</td>
        <td>%project.folder%/skims/</td>
        <td>Outputs folder</td>
    </tr>
    <tr>
        <td>uec.path </td>
        <td>String</td>
        <td>%project.folder%/CTRAMP/model/</td>
        <td>UEC folder</td>
    </tr>
    <tr>
        <td colspan="4"><a id="scenario_properties"><b>Scenario Properties</b><br><i>Modify when running new scenario, if necessary</i></a></td>
    </tr>
    <tr>
        <td>mgra.socec.file </td>
        <td>String</td>
        <td>/landuse/maz_data_withDensity.csv</td>
        <td>Location of mgra land use file</td>
    </tr>
    <tr>
        <td>network.node.seq.mapping.file </td>
        <td>String</td>
        <td>/hwy/mtc_final_network_zone_seq.csv</td>
        <td>Location of mapping between Nodes, MAZs, TAZs and TAPs</td>
    </tr>
    <tr>
        <td>aoc.fuel </td>
        <td>Float</td>
        <td>10.99</td>
        <td>Auto operating costs: Fuel cost</td>
    </tr>
    <tr>
        <td>aoc.maintenance </td>
        <td>Float</td>
        <td>6.24</td>
        <td>Auto operating costs: Maintenance cost</td>
    </tr>
    <tr>
        <td>HouseholdManager.MinValueOfTime </td>
        <td>Float</td>
        <td>1.0</td>
        <td>Household Value of Time Distribution: Minimum</td>
    </tr>
    <tr>
        <td>HouseholdManager.MaxValueOfTime </td>
        <td>Float</td>
        <td>50.0</td>
        <td>Household Value of Time Distribution: Maximum</td>
    </tr>
    <tr>
        <td>HouseholdManager.MeanValueOfTime.Values </td>
        <td>String</td>
        <td>6.01, 8.81, 10.44, 12.86</td>
        <td>Household Value of Time Distribution: Mean values for income groups</td>
    </tr>
    <tr>
        <td>HouseholdManager.MeanValueOfTime.Income.Limits </td>
        <td>String</td>
        <td>30000, 60000, 100000</td>
        <td>Household Value of Time Distribution: Income Limits</td>
    </tr>
    <tr>
        <td>HouseholdManager.Mean.ValueOfTime.Multiplier.Mu </td>
        <td>Float</td>
        <td>0.684</td>
        <td>Household Value of Time Distribution: Mean Multiplier</td>
    </tr>
    <tr>
        <td>HouseholdManager.ValueOfTime.Lognormal.Sigma </td>
        <td>Float</td>
        <td>0.87</td>
        <td>Household Value of Time Distribution: Lognormal Sigma</td>
    </tr>
    <tr>
        <td>HouseholdManager.HH.ValueOfTime.Multiplier.Under18 </td>
        <td>Float</td>
        <td>0.66667</td>
        <td>Household Value of Time Distribution: Under 18 multiplier</td>
    </tr>
    <tr>
        <td colspan="4"><a id="av_mobility"><b>AV Mobility Scenario Parameters</b></a></td>
    </tr>
    <tr>
        <td>Mobility.AV.Share </td>
        <td>Float</td>
        <td>0.0</td>
        <td>Specifies the share of vehicles assumed to be AVs in the vehicle fleet</td>
    </tr>
    <tr>
        <td>Mobility.AV.ProbabilityBoost.AutosLTDrivers </td>
        <td>Float</td>
        <td>1.2</td>
        <td>The increased probability for using AVs for tours by LT drivers.</td>
    </tr>
    <tr>
        <td>Mobility.AV.ProbabilityBoost.AutosGEDrivers </td>
        <td>Float</td>
        <td>1.1</td>
        <td>The increased probability for using AVs for tours by GE drivers.</td>
    </tr>
    <tr>
        <td>Mobility.AV.IVTFactor </td>
        <td>Float</td>
        <td>0.5</td>
        <td>The auto in-vehicle time factor to apply to AVs</td>
    </tr>
    <tr>
        <td>Mobility.AV.ParkingCostFactor </td>
        <td>Float</td>
        <td>0.0</td>
        <td>The auto parking cost factor to apply to AVs</td>
    </tr>
    <tr>
        <td>Mobility.AV.CostPerMileFactor </td>
        <td>Float</td>
        <td>0.5</td>
        <td>Cost to travel per mile to apply to AVs</td>
    </tr>
    <tr>
        <td>Mobility.AV.TerminalTimeFactor </td>
        <td>Float</td>
        <td>0.0</td>
        <td>Terminal Time Factor to apply to AVs</td>
    </tr>
    <tr>
        <td colspan="4"><a id="taxi_tnc_cost"><b>Taxi and TNC Cost and Wait Time Parameters</b></a></td>
    </tr>
    <tr>
        <td>taxi.basefare </td>
        <td>Float</td>
        <td>2.2</td>
        <td>Basefare for taxi</td>
    </tr>
    <tr>
        <td>taxi.costPerMile </td>
        <td>Float</td>
        <td>2.3</td>
        <td>Cost per mile for taxi</td>
    </tr>
    <tr>
        <td>taxi.costPerMinute </td>
        <td>Float</td>
        <td>0.1</td>
        <td>Cost per minute for taxi</td>
    </tr>
    <tr>
        <td>TNC.basefare </td>
        <td>Float</td>
        <td>2.2</td>
        <td>Basefare for TNC</td>
    </tr>
    <tr>
        <td>TNC.costPerMile </td>
        <td>Float</td>
        <td>1.33</td>
        <td>cost per mile  for TNC</td>
    </tr>
    <tr>
        <td>TNC.costPerMinute </td>
        <td>Float</td>
        <td>0.24</td>
        <td>Cost per minute for TNC</td>
    </tr>
    <tr>
        <td>TNC.costMinimum </td>
        <td>Float</td>
        <td>7.2</td>
        <td>Minimum cost to ride using TNC</td>
    </tr>
    <tr>
        <td>TNC.waitTime.mean </td>
        <td>String</td>
        <td>10.3, 8.5,  8.4, 6.3, 4.7</td>
        <td>Mean for TNC wait time distribution</td>
    </tr>
    <tr>
        <td>TNC.waitTime.sd </td>
        <td>String</td>
        <td>2.1, 2.1,  2.1, 2.1, 2.1</td>
        <td>Standard deviation for TNC wait time distribution</td>
    </tr>
    <tr>
        <td>Taxi.waitTime.mean </td>
        <td>String</td>
        <td>26.5, 17.3,13.3, 9.5, 5.5</td>
        <td>Mean for taxi wait time distribution</td>
    </tr>
    <tr>
        <td>Taxi.waitTime.sd </td>
        <td>String</td>
        <td>3.2,  3.2, 3.2, 3.2, 3.2</td>
        <td>Standard deviation for taxi wait time distribution</td>
    </tr>
    <tr>
        <td>WaitTimeDistribution.EndPopEmpPerSqMi </td>
        <td>String</td>
        <td>500,2000,5000,15000,9999999999</td>
        <td>Population employment per square mile for wait time distribution</td>
    </tr>
    <tr>
        <td colspan="4"><a id="transit_assignment_parameters"><b>Transit Assignment Parameters</b><br><i>Toggle and controls for managing Cube PT transit crowding assignments</i></a></td>
    </tr>
    <tr>
        <td>transit.crowding </td>
        <td>Boolean</td>
        <td>True</td>
        <td>Master toggle to enable adjustlink and adjustwait.</td>
    </tr>
    <tr>
        <td>transit.crowding.adjustlink </td>
        <td>Boolean</td>
        <td>False</td>
        <td>Toggle to enable link travel-time adjustment based on crowding</td>
    </tr>
    <tr>
        <td>transit.crowding.adjustwait </td>
        <td>Boolean</td>
        <td>False</td>
        <td>Toggle to enable wait adjusted travel times and bump boardings from crowding</td>
    </tr>
    <tr>
        <td>transit.crowding.advance_support </td>
        <td>Boolean</td>
        <td>False</td>
        <td>Toggle if Cube version is > 6.4.4 and supports advanced convergence and dampening factors (df)</td>
    </tr>
    <tr>
        <td>transit.crowding.convergence </td>
        <td>Float</td>
        <td>0.01</td>
        <td>Cube PT crowding RMSE congervence criteria</td>
    </tr>
    <tr>
        <td>transit.crowding.linkdf </td>
        <td>Float</td>
        <td>0.4</td>
        <td>Cube PT link dampening factor</td>
    </tr>
    <tr>
        <td>transit.crowding.voldf </td>
        <td>Float</td>
        <td>0.4</td>
        <td>Cube PT volume dampening factor</td>
    </tr>
    <tr>
        <td>transit.crowding.waitdf </td>
        <td>Float</td>
        <td>0.4</td>
        <td>Cube PT wait dampening factor</td>
    </tr>
    <tr>
        <td>transit.crowding.iterations </td>
        <td>Integer</td>
        <td>1</td>
        <td>Number of iterations for transit crowding assignments</td>
    </tr>
    <tr>
        <td colspan="4"><a id="parking_restraint_parameters"><b>Parking Capacity Restraint Parameters</b><br><i>For managing CT-RAMP parking capacity restraint algorithm</i></a></td>
    </tr>
    <tr>
        <td>ParkingCapacityRestraint.spacesForMissingLots </td>
        <td>Integer</td>
        <td>20</td>
        <td>The number of spaces to use for any TAP not listed in the station attribute file (local stops, missing express bus stops, etc.)</td>
    </tr>
    <tr>
        <td>ParkingCapacityRestraint.minutesPerSimulationPeriod </td>
        <td>Integer</td>
        <td>15</td>
        <td>The size of the simulation period used for capacity calculations in the parking capacity restraint model. The smaller the simulation period, the more iterations may be required to constrain to total available parking</td>
    </tr>
    <tr>
        <td>ParkingCapacityRestraint.maxIterations </td>
        <td>Integer</td>
        <td>10</td>
        <td>Maximum number of times to iterate between parking constraint and re-running CT-RAMP for households with PNR tours arriving at full lots</td>
    </tr>
    <tr>
        <td>ParkingCapacityRestraint.lumpinessFactor </td>
        <td>Integer</td>
        <td>2</td>
        <td>The factor used to scale the inverse of sample rate to calculate a buffer for parking capacity (buffer = 1.0f/sampleRate * lumpiness_factor)</td>
    </tr>
    <tr>
        <td>ParkingCapacityRestraint.parkAndHideFactor </td>
        <td>Float</td>
        <td>1.15</td>
        <td>A factor on parking capacity to account for cars that "hide" and walk to station from non-designated parking</td>
    </tr>
    <tr>
        <td>ParkingCapacityRestraint.occupancyFactor </td>
        <td>Float</td>
        <td>1.05</td>
        <td>The average number of transit riders who drive together in the same car and park, to convert person trips to vehicles</td>
    </tr>
    <tr>
        <td colspan="4"><a id="avg_veh_occupancy_3_plus"><b>Average vehicle occupancy for 3 plus by purpose</b><br><i>Used for generating trip tables for assignment</i></a></td>
    </tr>
    <tr>
        <td>occ3plus.purpose.Work </td>
        <td>Float</td>
        <td>3.33</td>
        <td></td>
    </tr>
    <tr>
        <td>occ3plus.purpose.University </td>
        <td>Float</td>
        <td>3.33</td>
        <td></td>
    </tr>
    <tr>
        <td>occ3plus.purpose.School </td>
        <td>Float</td>
        <td>3.33</td>
        <td></td>
    </tr>
    <tr>
        <td>occ3plus.purpose.Escort </td>
        <td>Float</td>
        <td>3.33</td>
        <td></td>
    </tr>
    <tr>
        <td>occ3plus.purpose.Shop </td>
        <td>Float</td>
        <td>3.33</td>
        <td></td>
    </tr>
    <tr>
        <td>occ3plus.purpose.Maintenance </td>
        <td>Float</td>
        <td>3.33</td>
        <td></td>
    </tr>
    <tr>
        <td>occ3plus.purpose.EatingOut </td>
        <td>Float</td>
        <td>3.33</td>
        <td></td>
    </tr>
    <tr>
        <td>occ3plus.purpose.Visiting </td>
        <td>Float</td>
        <td>3.33</td>
        <td></td>
    </tr>
    <tr>
        <td>occ3plus.purpose.Discretionary </td>
        <td>Float</td>
        <td>3.33</td>
        <td></td>
    </tr>
    <tr>
        <td>occ3plus.purpose.WorkBased </td>
        <td>Float</td>
        <td>3.33</td>
        <td></td>
    </tr>
    <tr>
        <td colspan="4"><a id="core_model"><b>Core Model Run Properties</b><br><i>Control Steps Run in Core Model</i></a></td>
    </tr>
    <tr>
        <td>Model.Random.Seed </td>
        <td>Integer</td>
        <td>1</td>
        <td>Starting value for model random seed number (added to household IDs to create unique random number for each household)</td>
    </tr>
    <tr>
        <td>acc.read.input.file</td>
        <td>Boolean</td>
        <td>false</td>
        <td>Set to true if read the accessibilities from an input file instead of calculating them prior to running CTRAMP</td>
    </tr>
    <tr>
        <td>uwsl.ShadowPricing.Work.MaximumIterations </td>
        <td>Integer</td>
        <td>1</td>
        <td>maximum number of iterations for work shadow price</td>
    </tr>
    <tr>
        <td>uwsl.ShadowPricing.School.MaximumIterations </td>
        <td>Integer</td>
        <td>1</td>
        <td>maximum number of iterations for school shadow price</td>
    </tr>
    <tr>
        <td>uwsl.ShadowPricing.OutputFile </td>
        <td>String</td>
        <td>/ctramp_output/ShadowPricingOutput.csv</td>
        <td>output file name and location for shadow price</td>
    </tr>
    <tr>
        <td>uwsl.run.workLocChoice </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component</td>
    </tr>
    <tr>
        <td>uwsl.run.schoolLocChoice </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component</td>
    </tr>
    <tr>
        <td>uwsl.write.results </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True of False whether to write out usual work and school location results</td>
    </tr>
    <tr>
        <td>uwsl.use.new.soa </td>
        <td>Boolean</td>
        <td>false</td>
        <td>true or false whether to use new soa for the work/school DC model</td>
    </tr>
    <tr>
        <td>nmdc.use.new.soa </td>
        <td>Boolean</td>
        <td>false</td>
        <td>true or false whether to use new soa for the non-mandatory DC models</td>
    </tr>
    <tr>
        <td>slc.use.new.soa </td>
        <td>Boolean</td>
        <td>false</td>
        <td>true or false whether to use new soa for the stop location choice models</td>
    </tr>
    <tr>
        <td>distributed.task.packet.size </td>
        <td>Integer</td>
        <td>500</td>
        <td>Distributed task packet size</td>
    </tr>
    <tr>
        <td>RunModel.PreAutoOwnership </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component </td>
    </tr>
    <tr>
        <td>RunModel.UsualWorkAndSchoolLocationChoice </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component </td>
    </tr>
    <tr>
        <td>RunModel.AutoOwnership </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component </td>
    </tr>
    <tr>
        <td>RunModel.TransponderChoice </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component</td>
    </tr>
    <tr>
        <td>RunModel.FreeParking </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component</td>
    </tr>
    <tr>
        <td>RunModel.CoordinatedDailyActivityPattern </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component</td>
    </tr>
    <tr>
        <td>RunModel.IndividualMandatoryTourFrequency </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component</td>
    </tr>
    <tr>
        <td>RunModel.MandatoryTourModeChoice </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component</td>
    </tr>
    <tr>
        <td>RunModel.MandatoryTourDepartureTimeAndDuration </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component</td>
    </tr>
    <tr>
        <td>RunModel.JointTourFrequency </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component </td>
    </tr>
    <tr>
        <td>RunModel.JointTourLocationChoice </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component </td>
    </tr>
    <tr>
        <td>RunModel.JointTourDepartureTimeAndDuration </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component </td>
    </tr>
    <tr>
        <td>RunModel.JointTourModeChoice </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component </td>
    </tr>
    <tr>
        <td>RunModel.IndividualNonMandatoryTourFrequency </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component </td>
    </tr>
    <tr>
        <td>RunModel.IndividualNonMandatoryTourLocationChoice </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component </td>
    </tr>
    <tr>
        <td>RunModel.IndividualNonMandatoryTourDepartureTimeAndDuration </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component </td>
    </tr>
    <tr>
        <td>RunModel.IndividualNonMandatoryTourModeChoice </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component </td>
    </tr>
    <tr>
        <td>RunModel.AtWorkSubTourFrequency </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component </td>
    </tr>
    <tr>
        <td>RunModel.AtWorkSubTourLocationChoice </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component </td>
    </tr>
    <tr>
        <td>RunModel.AtWorkSubTourDepartureTimeAndDuration </td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component </td>
    </tr>
    <tr>
        <td>RunModel.AtWorkSubTourModeChoice</td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component </td>
    </tr>
    <tr>
        <td>RunModel.StopFrequency</td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component </td>
    </tr>
    <tr>
        <td>RunModel.StopLocation</td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to run this model component </td>
    </tr>
    <tr>
        <td colspan="4"><a id="input_properties"><b>Input Properties</b></a></td>
    </tr>
    <tr>
        <td>PopulationSynthesizer.InputToCTRAMP.HouseholdFile </td>
        <td>String</td>
        <td>popsyn/households.csv</td>
        <td>Location of popsyn households.csv file</td>
    </tr>
    <tr>
        <td>PopulationSynthesizer.InputToCTRAMP.PersonFile </td>
        <td>String</td>
        <td>popsyn/persons.csv</td>
        <td>Location of popsyn persons.csv file</td>
    </tr>
    <tr>
        <td>maz.tap.tapLines</td>
        <td>String</td>
        <td>trn/tapLines.csv</td>
        <td>Location of tap lines file</td>
    </tr>
    <tr>
        <td>maz.tap. </td>
        <td>String</td>
        <td>skims/ped_distance_maz_tap.txt</td>
        <td>Location of MAZ to TAP pedestrian distances file</td>
    </tr>
    <tr>
        <td>maz.maz.distance.file </td>
        <td>String</td>
        <td>skims/ped_distance_maz_maz.txt</td>
        <td>Location of MAZ to MAZ pedestrian distances file</td>
    </tr>
    <tr>
        <td>maz.maz.bike.distance.file </td>
        <td>String</td>
        <td>skims/bike_distance_maz_maz.txt</td>
        <td>Location of MAZ to MAZ bike distances file</td>
    </tr>
    <tr>
        <td>maz.tap.trimTapSet</td>
        <td>Boolean</td>
        <td>true</td>
        <td>True or False whether to trim tap set or not</td>
    </tr>
    <tr>
        <td>maz.tap.maxWalkTapDistInMiles </td>
        <td>Integer</td>
        <td>1.2</td>
        <td>Maximum walk distance allowed between any MAZ and TAP</td>
    </tr>
    <tr>
        <td>transit.fareDiscount.file</td>
        <td>String</td>
        <td>trn/transitFareDiscounts.csv</td>
        <td>Location of transit fare discounts file</td>
    </tr>
    <tr>
        <td colspan="4"><a id="output_properties"><b>Output Properties</b></a></td>
    </tr>
    <tr>
        <td>Results.WriteDataToFiles</td>
        <td>Boolean</td>
        <td>true</td>
        <td>Write data to files</td>
    </tr>
    <tr>
        <td>Results.HouseholdDataFile </td>
        <td>String</td>
        <td>/ctramp_output/householdData.csv</td>
        <td>Output name of household data file</td>
    </tr>
    <tr>
        <td>Results.PersonDataFile </td>
        <td>String</td>
        <td>/ctramp_output/personData.csv</td>
        <td>Output name of person data file</td>
    </tr>
    <tr>
        <td>Results.IndivTourDataFile </td>
        <td>String</td>
        <td>/ctramp_output/indivTourData.csv</td>
        <td>Output name of individual tour data file</td>
    </tr>
    <tr>
        <td>Results.JointTourDataFile </td>
        <td>String</td>
        <td>/ctramp_output/jointTourData.csv</td>
        <td>Output name of joint tour data file</td>
    </tr>
    <tr>
        <td>Results.IndivTripDataFile </td>
        <td>String</td>
        <td>/ctramp_output/indivTripData.csv</td>
        <td>Output name of individual trip data file</td>
    </tr>
    <tr>
        <td>Results.JointTripDataFile </td>
        <td>String</td>
        <td>/ctramp_output/jointTripData.csv</td>
        <td>Output name of joint trip data file</td>
    </tr>
    <tr>
        <td>Results.WriteDataToDatabase </td>
        <td>Boolean</td>
        <td>false</td>
        <td>Write data to a database</td>
    </tr>
    <tr>
        <td>Results.HouseholdTable </td>
        <td>String</td>
        <td>household_data</td>
        <td>Output name of household data file in database</td>
    </tr>
    <tr>
        <td>Results.PersonTable </td>
        <td>String</td>
        <td>person_data</td>
        <td>Output name of person data file in database</td>
    </tr>
    <tr>
        <td>Results.IndivTourTable </td>
        <td>String</td>
        <td>indiv_tour_data</td>
        <td>Output name of individual tour data file in database</td>
    </tr>
    <tr>
        <td>Results.JointTourTable </td>
        <td>String</td>
        <td>joint_tour_data</td>
        <td>Output name of joint tour data file in database</td>
    </tr>
    <tr>
        <td>Results.IndivTripTable </td>
        <td>String</td>
        <td>indiv_trip_data</td>
        <td>Output name of individual trip data file in database</td>
    </tr>
    <tr>
        <td>Results.JointTripTable </td>
        <td>String</td>
        <td>joint_trip_data</td>
        <td>Output name of joint trip data file in database</td>
    </tr>
    <tr>
        <td>Results.CBDFile </td>
        <td>String</td>
        <td>/ctramp_output/cbdParking.csv</td>
        <td>Output name of CBD by MGRA Vehicle Trip file</td>
    </tr>
    <tr>
        <td>Results.PNRFile </td>
        <td>String</td>
        <td>/ctramp_output/pnrParking.csv</td>
        <td>Output name of PNR by TAP Vehicle Trip file</td>
    </tr>
    <tr>
        <td>Results.AutoTripMatrix </td>
        <td>String</td>
        <td>/ctramp_output/auto</td>
        <td>Output name of auto trip matrix</td>
    </tr>
    <tr>
        <td>Results.TranTripMatrix </td>
        <td>String</td>
        <td>/ctramp_output/transit</td>
        <td>Output name of transit trip matrix</td>
    </tr>
    <tr>
        <td>Results.NMotTripMatrix </td>
        <td>String</td>
        <td>/ctramp_output/nonmotor</td>
        <td>Output name of non-motorized trip matrix</td>
    </tr>
    <tr>
        <td>Results.OthrTripMatrix </td>
        <td>String</td>
        <td>/ctramp_output/other</td>
        <td>Output name of other modes trip matrix</td>
    </tr>
    <tr>
        <td>Results.AutoAVTripMatrix  </td>
        <td>String</td>
        <td>/ctramp_output/autoAV</td>
        <td>Output name of AV modes trip matrix</td>
    </tr>
    <tr>
        <td>Results.MatrixType </td>
        <td>String</td>
        <td>OMX</td>
        <td>Matrix type for trip tables</td>
    </tr>
    <tr>
        <td>Results.MAZAutoTripMatrix.IntrazonalOnly </td>
        <td>Boolean</td>
        <td>False</td>
        <td>If True, then intrazonal trips get put into one of the three County Sets based on the origin MAZ county code. If False, then both intrazonal trips and trips whose distance is less than TripMaxDistance get put into one of the CountySets based on the origin MAZ county code</td>
    </tr>
    <tr>
        <td>Results.AutoOwnership</td>
        <td>String</td>
        <td>/ctramp_output/aoResults.csv</td>
        <td>Auto ownership output file name and location</td>
    </tr>
    <tr>
        <td>read.pre.ao.results</td>
        <td>Boolean</td>
        <td>false</td>
        <td>Read in the old pre-auto ownership results file</td>
    </tr>
    <tr>
        <td>read.pre.ao.filename</td>
        <td>String</td>
        <td>/ctramp_output/aoResults_pre.csv</td>
        <td>Pre auto ownership output file name and location</td>
    </tr>
    <tr>
        <td>Results.UsualWorkAndSchoolLocationChoice</td>
        <td>String</td>
        <td>/ctramp_output/wsLocResults.csv</td>
        <td>Usual work and school location output file name and location</td>
    </tr>
    <tr>
        <td>read.uwsl.results</td>
        <td>Boolean</td>
        <td>false</td>
        <td>Read in the old uwsl results</td>
    </tr>
    <tr>
        <td>read.uwsl.filename</td>
        <td>String</td>
        <td>/ctramp_output/wsLocResults_1.csv</td>
        <td>Old uwsl result file name and location to read in</td>
    </tr>
    <tr>
        <td>workSchoolSegments.definitions </td>
        <td>String</td>
        <td>/ctramp_output/workSchoolSegments.definitions</td>
        <td>Correspondence table for work location segment indices and work location segment names</td>
    </tr>
    <tr>
        <td colspan="4"><a id="core_model_uec"><b>Core Model UECs</b></a></td>
    </tr>
    <tr>
        <td>acc.jppf </td>
        <td>Boolean</td>
        <td>true</td>
        <td>Accessibilities to be assigned to a JPPF node</td>
    </tr>
    <tr>
        <td>acc.without.jppf.numThreads </td>
        <td>Integer</td>
        <td>30</td>
        <td>Number of threads for accessibilities without JPPF</td>
    </tr>
    <tr>
        <td>acc.destination.sampleRate </td>
        <td>Float</td>
        <td>0.05</td>
        <td>Sample rate for accessibilities</td>
    </tr>
    <tr>
        <td>acc.uec.file </td>
        <td>String</td>
        <td>%project.folder%/uec/Accessibilities.xls</td>
        <td>Accessibilities.xls location</td>
    </tr>
    <tr>
        <td>acc.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Accessibilities data page</td>
    </tr>
    <tr>
        <td>acc.sov.offpeak.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Accessibilities SOV offpeak</td>
    </tr>
    <tr>
        <td>acc.sov.peak.page </td>
        <td>Integer</td>
        <td>2</td>
        <td>Accessibilities SOV peak</td>
    </tr>
    <tr>
        <td>acc.hov.offpeak.page </td>
        <td>Integer</td>
        <td>3</td>
        <td>Accessibilities HOV offpeak</td>
    </tr>
    <tr>
        <td>acc.hov.peak.page </td>
        <td>Integer</td>
        <td>4</td>
        <td>Accessibilities HOV peak</td>
    </tr>
    <tr>
        <td>acc.nonmotorized.page </td>
        <td>Integer</td>
        <td>5</td>
        <td>Accessibilities non-motorized</td>
    </tr>
    <tr>
        <td>acc.constants.page </td>
        <td>Integer</td>
        <td>6</td>
        <td>Accessibilities constants</td>
    </tr>
    <tr>
        <td>acc.sizeTerm.page </td>
        <td>Integer</td>
        <td>7</td>
        <td>Accessibilities size terms</td>
    </tr>
    <tr>
        <td>acc.schoolSizeTerm.page </td>
        <td>Integer</td>
        <td>8</td>
        <td>Accessibilities school size terms</td>
    </tr>
    <tr>
        <td>acc.workerSizeTerm.page </td>
        <td>Integer</td>
        <td>9</td>
        <td>Accessibilities worker size terms</td>
    </tr>
    <tr>
        <td>acc.dcUtility.uec.file </td>
        <td>String</td>
        <td>%project.folder%/CTRAMP/model/Accessibilities_DC.xls</td>
        <td>Accessibilities_DC.xls location</td>
    </tr>
    <tr>
        <td>acc.dcUtility.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>DC Accessibilities data page</td>
    </tr>
    <tr>
        <td>acc.dcUtility.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>DC Accessibilities utility page</td>
    </tr>
    <tr>
        <td>acc.output.file </td>
        <td>String</td>
        <td>/ctramp_output/accessibilities.csv</td>
        <td>accessibilities.csv location</td>
    </tr>
    <tr>
        <td>accessibility.alts.file </td>
        <td>String</td>
        <td>Acc_alts.csv</td>
        <td>Accessibilities alternatives</td>
    </tr>
    <tr>
        <td>acc.mandatory.uec.file </td>
        <td>String</td>
        <td>%project.folder%/CTRAMP/model/MandatoryAccess.xls</td>
        <td>MandatoryAccess.xls location</td>
    </tr>
    <tr>
        <td>acc.mandatory.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Mandatory Access data page</td>
    </tr>
    <tr>
        <td>acc.mandatory.auto.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Mandatory Access auto page</td>
    </tr>
    <tr>
        <td>acc.mandatory.autoLogsum.page </td>
        <td>Integer</td>
        <td>2</td>
        <td>Mandatory Access autoLogsum page</td>
    </tr>
    <tr>
        <td>acc.mandatory.bestWalkTransit.page </td>
        <td>Integer</td>
        <td>3</td>
        <td>Mandatory Access best Walk Transit page</td>
    </tr>
    <tr>
        <td>acc.mandatory.bestDriveTransit.page </td>
        <td>Integer</td>
        <td>4</td>
        <td>Mandatory Access best Drive Transit page</td>
    </tr>
    <tr>
        <td>acc.mandatory.transitLogsum.page </td>
        <td>Integer</td>
        <td>5</td>
        <td>Mandatory Access transit logsum page</td>
    </tr>
    <tr>
        <td>ao.uec.file </td>
        <td>String</td>
        <td>AutoOwnership.xls</td>
        <td>File name of auto ownership UEC</td>
    </tr>
    <tr>
        <td>ao.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Auto ownership UEC data page</td>
    </tr>
    <tr>
        <td>ao.model.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Auto ownership UEC utility page</td>
    </tr>
    <tr>
        <td>tt.uec.file </td>
        <td>String</td>
        <td>TransitSubsidyAndPass.xls</td>
        <td>File name of transit subsidy UEC</td>
    </tr>
    <tr>
        <td>tt.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Transit Subsidy UEC data page</td>
    </tr>
    <tr>
        <td>tt.subsidyModel.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Transit subsidy model page</td>
    </tr>
    <tr>
        <td>tt.passModel.page </td>
        <td>Integer</td>
        <td>2</td>
        <td>Transit pass model page</td>
    </tr>
    <tr>
        <td>tt.autoGenTime.page </td>
        <td>Integer</td>
        <td>3</td>
        <td>Transit auto time page</td>
    </tr>
    <tr>
        <td>tt.subsidyPercent.file </td>
        <td>String</td>
        <td>transitSubsidyDistribution.csv</td>
        <td>File name of transit subsidy distribution</td>
    </tr>
    <tr>
        <td>tt.naics.20 </td>
        <td>String</td>
        <td>constr,util,natres</td>
        <td></td>
    </tr>
    <tr>
        <td>tt.naics.30 </td>
        <td>String</td>
        <td>man_bio,man_lgt,man_hvy,man_tech</td>
        <td></td>
    </tr>
    <tr>
        <td>tt.naics.40 </td>
        <td>String</td>
        <td>logis,ret_loc,ret_reg,transp</td>
        <td></td>
    </tr>
    <tr>
        <td>tt.naics.50 </td>
        <td>String</td>
        <td>info,lease,prof,fire,serv_bus</td>
        <td></td>
    </tr>
    <tr>
        <td>tt.naics.70 </td>
        <td>String</td>
        <td>art_rec,eat,hotel</td>
        <td></td>
    </tr>
    <tr>
        <td>tt.naics.80 </td>
        <td>String</td>
        <td>serv_pers</td>
        <td></td>
    </tr>
    <tr>
        <td>tt.naics.90 </td>
        <td>String</td>
        <td>gov</td>
        <td></td>
    </tr>
    <tr>
        <td>uwsl.dc.uec.file </td>
        <td>String</td>
        <td>TourDestinationChoice.xls</td>
        <td>File Name of Tour Destination Choice UEC</td>
    </tr>
    <tr>
        <td>uwsl.dc2.uec.file </td>
        <td>String</td>
        <td>TourDestinationChoice2.xls</td>
        <td>File Name of Tour Destination Choice 2 UEC</td>
    </tr>
    <tr>
        <td>uwsl.soa.uec.file </td>
        <td>String</td>
        <td>DestinationChoiceAlternativeSample.xls</td>
        <td>File Name of Destination Choice Alternative Sample UEC</td>
    </tr>
    <tr>
        <td>uwsl.soa.alts.file </td>
        <td>String</td>
        <td>DestinationChoiceAlternatives.csv</td>
        <td>File name of the alternatives (MGRAs) available to the destination choice models (part of the model design; this should not be changed)</td>
    </tr>
    <tr>
        <td>uwsl.work.soa.SampleSize </td>
        <td>Integer</td>
        <td>30</td>
        <td>Sample size of Work Destination Choice</td>
    </tr>
    <tr>
        <td>uwsl.school.soa.SampleSize </td>
        <td>Integer</td>
        <td>30</td>
        <td>Sample size of School Destination Choice</td>
    </tr>
    <tr>
        <td>work.soa.uec.file </td>
        <td>String</td>
        <td>TourDcSoaDistance.xls</td>
        <td>File Name of Tour Distance DC SOA UEC for Work Purpose includes TAZ Size in the expressions</td>
    </tr>
    <tr>
        <td>work.soa.uec.data </td>
        <td>Integer</td>
        <td>0</td>
        <td>Work Tour Distance SOA UEC data page</td>
    </tr>
    <tr>
        <td>work.soa.uec.model </td>
        <td>Integer</td>
        <td>1</td>
        <td>Work Tour Distance SOA UEC utility page</td>
    </tr>
    <tr>
        <td>univ.soa.uec.file </td>
        <td>String</td>
        <td>TourDcSoaDistanceNoSchoolSize.xls</td>
        <td>File Name of Tour Distance DC SOA UEC for School Purpose; school purposes do not include TAZ Size in the expressions so that the utilities can be stored as exponentiated distance utility matrices for university and then multiplied by the university segment size terms</td>
    </tr>
    <tr>
        <td>univ.soa.uec.data </td>
        <td>Integer</td>
        <td>0</td>
        <td>University Tour Distance SOA UEC data page</td>
    </tr>
    <tr>
        <td>univ.soa.uec.model </td>
        <td>Integer</td>
        <td>1</td>
        <td>University Tour Distance SOA UEC utility page</td>
    </tr>
    <tr>
        <td>hs.soa.uec.file </td>
        <td>String</td>
        <td>TourDcSoaDistanceNoSchoolSize.xls</td>
        <td>File Name of Tour Distance DC SOA UEC for School Purpose; school purposes do not include TAZ Size in the expressions so that the utilities can be stored as exponentiated distance utility matrices for high school and then multiplied by the high school segment size terms</td>
    </tr>
    <tr>
        <td>hs.soa.uec.data </td>
        <td>Integer</td>
        <td>0</td>
        <td>High School Tour Distance SOA UEC data page</td>
    </tr>
    <tr>
        <td>hs.soa.uec.model </td>
        <td>Integer</td>
        <td>2</td>
        <td>High School Tour Distance SOA UEC utility page</td>
    </tr>
    <tr>
        <td>gs.soa.uec.file </td>
        <td>String</td>
        <td>TourDcSoaDistanceNoSchoolSize.xls</td>
        <td>File Name of Tour Distance DC SOA UEC for School Purpose; school purposes do not include TAZ Size in the expressions so that the utilities can be stored as exponentiated distance utility matrices for grade school and then multiplied by the grade school segment size terms</td>
    </tr>
    <tr>
        <td>gs.soa.uec.data </td>
        <td>Integer</td>
        <td>0</td>
        <td>Grade School Tour Distance SOA UEC data page</td>
    </tr>
    <tr>
        <td>gs.soa.uec.model </td>
        <td>Integer</td>
        <td>3</td>
        <td>Grade School Tour Distance SOA UEC utility page</td>
    </tr>
    <tr>
        <td>ps.soa.uec.file </td>
        <td>String</td>
        <td>TourDcSoaDistanceNoSchoolSize.xls</td>
        <td>File Name of Tour Distance DC SOA UEC for School Purpose; school purposes do not include TAZ Size in the expressions so that the utilities can be stored as exponentiated distance utility matrices for preschool and then multiplied by the preschool segment size terms</td>
    </tr>
    <tr>
        <td>ps.soa.uec.data </td>
        <td>Integer</td>
        <td>0</td>
        <td>Preschool Tour Distance SOA UEC data page</td>
    </tr>
    <tr>
        <td>ps.soa.uec.model </td>
        <td>Integer</td>
        <td>4</td>
        <td>Preschool Tour Distance SOA UEC utility page</td>
    </tr>
    <tr>
        <td>tc.choice.avgtts.file </td>
        <td>String</td>
        <td>/../input/ABMTEMP/ctramp/tc_avgtt.csv</td>
        <td>File name of average travel times for transponder ownership</td>
    </tr>
    <tr>
        <td>tc.uec.file </td>
        <td>String</td>
        <td>TransponderOwnership.xls</td>
        <td>File name of transponder ownership UEC</td>
    </tr>
    <tr>
        <td>tc.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Transponder ownership UEC data page</td>
    </tr>
    <tr>
        <td>tc.model.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Transponder ownership UEC utility page</td>
    </tr>
    <tr>
        <td>fp.uec.file </td>
        <td>String</td>
        <td>ParkingProvision.xls</td>
        <td>File name of parking provision UEC</td>
    </tr>
    <tr>
        <td>fp.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Parking Provision UEC data page</td>
    </tr>
    <tr>
        <td>fp.model.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Parking Provision UEC utility page</td>
    </tr>
    <tr>
        <td>cdap.uec.file </td>
        <td>String</td>
        <td>CoordinatedDailyActivityPattern.xls</td>
        <td>File name of CDAP UEC</td>
    </tr>
    <tr>
        <td>cdap.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>CDAP UEC data page</td>
    </tr>
    <tr>
        <td>cdap.one.person.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>CDAP UEC utility for one person page</td>
    </tr>
    <tr>
        <td>cdap.two.person.page </td>
        <td>Integer</td>
        <td>2</td>
        <td>CDAP UEC utility for 2 persons page</td>
    </tr>
    <tr>
        <td>cdap.three.person.page </td>
        <td>Integer</td>
        <td>3</td>
        <td>CDAP UEC utility for 3 persons page</td>
    </tr>
    <tr>
        <td>cdap.all.person.page </td>
        <td>Integer</td>
        <td>4</td>
        <td>CDAP UEC utility for All member interation page</td>
    </tr>
    <tr>
        <td>cdap.joint.page </td>
        <td>Integer</td>
        <td>5</td>
        <td>CDAP UEC utility for joint tours page</td>
    </tr>
    <tr>
        <td>imtf.uec.file </td>
        <td>String</td>
        <td>MandatoryTourFrequency.xls</td>
        <td>File name of Mandatory tour frequency UEC</td>
    </tr>
    <tr>
        <td>imtf.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Mandatory tour frequency UEC data page</td>
    </tr>
    <tr>
        <td>imtf.model.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>mandatory tour frequency UEC utility page</td>
    </tr>
    <tr>
        <td>nonSchool.soa.uec.file </td>
        <td>String</td>
        <td>TourDcSoaDistance.xls</td>
        <td>File Name of Tour Distance DC SOA UEC for Non Work/School Purposes includes TAZ Size in the expressions</td>
    </tr>
    <tr>
        <td>escort.soa.uec.data </td>
        <td>Integer</td>
        <td>0</td>
        <td>Escort Tour Distance SOA UEC data page</td>
    </tr>
    <tr>
        <td>escort.soa.uec.model </td>
        <td>Integer</td>
        <td>2</td>
        <td>Escort Tour Distance SOA UEC utility page</td>
    </tr>
    <tr>
        <td>other.nonman.soa.uec.data </td>
        <td>Integer</td>
        <td>0</td>
        <td>Other Non-mandatory Tour Distance SOA UEC data page</td>
    </tr>
    <tr>
        <td>other.nonman.soa.uec.model </td>
        <td>Integer</td>
        <td>3</td>
        <td>Other Non-mandatory Tour Distance SOA UEC utility page</td>
    </tr>
    <tr>
        <td>atwork.soa.uec.data </td>
        <td>Integer</td>
        <td>0</td>
        <td>At-Work Sub-Tour Distance SOA UEC data page</td>
    </tr>
    <tr>
        <td>atwork.soa.uec.model </td>
        <td>Integer</td>
        <td>4</td>
        <td>At-Work Sub-Tour Distance SOA UEC utility page</td>
    </tr>
    <tr>
        <td>soa.taz.dist.alts.file </td>
        <td>String</td>
        <td>SoaTazDistAlternatives.csv</td>
        <td>File name of Sample of Alternatives of TAZs</td>
    </tr>
    <tr>
        <td>nmdc.dist.alts.file </td>
        <td>String</td>
        <td>NonMandatoryTlcAlternatives.csv</td>
        <td>File name of non-mandatory tour alternatives</td>
    </tr>
    <tr>
        <td>nmdc.soa.alts.file </td>
        <td>String</td>
        <td>DestinationChoiceAlternatives.csv</td>
        <td>File name of the alternatives (MGRAs) available to the destination choice models (part of the model design; this should not be changed)</td>
    </tr>
    <tr>
        <td>nmdc.soa.SampleSize </td>
        <td>Integer</td>
        <td>30</td>
        <td>Sample size of non-mandatory Destination choice</td>
    </tr>
    <tr>
        <td>nmdc.uec.file2 </td>
        <td>String</td>
        <td>TourDestinationChoice2.xls</td>
        <td>File Name of Tour Destination Choice 2 UEC</td>
    </tr>
    <tr>
        <td>nmdc.uec.file </td>
        <td>String</td>
        <td>TourDestinationChoice.xls</td>
        <td>File Name of Tour Destination Choice UEC</td>
    </tr>
    <tr>
        <td>nmdc.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Non-mandatory Tour DC UEC data page</td>
    </tr>
    <tr>
        <td>nmdc.escort.model.page </td>
        <td>Integer</td>
        <td>7</td>
        <td>Escort Tour Destination Choice UEC utility page</td>
    </tr>
    <tr>
        <td>nmdc.shop.model.page </td>
        <td>Integer</td>
        <td>8</td>
        <td>Shop Tour Destination Choice UEC utility page</td>
    </tr>
    <tr>
        <td>nmdc.maint.model.page </td>
        <td>Integer</td>
        <td>9</td>
        <td>Maintenance Tour Destination Choice UEC utility page</td>
    </tr>
    <tr>
        <td>nmdc.eat.model.page </td>
        <td>Integer</td>
        <td>10</td>
        <td>Eating Out Tour Destination Choice UEC utility page</td>
    </tr>
    <tr>
        <td>nmdc.visit.model.page </td>
        <td>Integer</td>
        <td>11</td>
        <td>Visiting Tour Destination Choice UEC utility page</td>
    </tr>
    <tr>
        <td>nmdc.discr.model.page </td>
        <td>Integer</td>
        <td>12</td>
        <td>Discretionary Tour Destination Choice UEC utility page</td>
    </tr>
    <tr>
        <td>nmdc.atwork.model.page </td>
        <td>Integer</td>
        <td>13</td>
        <td>At-Work Sub-Tour Destination Choice UEC utility page</td>
    </tr>
    <tr>
        <td>nmdc.soa.uec.file </td>
        <td>String</td>
        <td>DestinationChoiceAlternativeSample.xls</td>
        <td>File Name of Destination Choice Alternative Sample UEC</td>
    </tr>
    <tr>
        <td>nmdc.soa.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Non-mandatory TOUR SOA UEC data page</td>
    </tr>
    <tr>
        <td>nmdc.soa.escort.model.page </td>
        <td>Integer</td>
        <td>6</td>
        <td>Escort TOUR SOA UEC utility page</td>
    </tr>
    <tr>
        <td>nmdc.soa.shop.model.page </td>
        <td>Integer</td>
        <td>7</td>
        <td>Shop TOUR SOA UEC utility page</td>
    </tr>
    <tr>
        <td>nmdc.soa.maint.model.page </td>
        <td>Integer</td>
        <td>7</td>
        <td>Maintenance TOUR SOA UEC utility page</td>
    </tr>
    <tr>
        <td>nmdc.soa.eat.model.page </td>
        <td>Integer</td>
        <td>7</td>
        <td>Eating Out TOUR SOA UEC utility page</td>
    </tr>
    <tr>
        <td>nmdc.soa.visit.model.page </td>
        <td>Integer</td>
        <td>7</td>
        <td>Visiting TOUR SOA UEC utility page</td>
    </tr>
    <tr>
        <td>nmdc.soa.discr.model.page </td>
        <td>Integer</td>
        <td>7</td>
        <td>Discretionary TOUR SOA UEC utility page</td>
    </tr>
    <tr>
        <td>nmdc.soa.atwork.model.page </td>
        <td>Integer</td>
        <td>8</td>
        <td>At-Work Sub-Tour SOA UEC utility page</td>
    </tr>
    <tr>
        <td>tourModeChoice.uec.file </td>
        <td>String</td>
        <td>TourModeChoice.xls</td>
        <td>File name of Tour Mode choice UEC</td>
    </tr>
    <tr>
        <td>tourModeChoice.maint.model.page </td>
        <td>Integer</td>
        <td>4</td>
        <td>Maintenance Tour Mode Choice UEC utility page</td>
    </tr>
    <tr>
        <td>tourModeChoice.discr.model.page </td>
        <td>Integer</td>
        <td>5</td>
        <td>Discretionary Tour Mode Choice UEC utility page</td>
    </tr>
    <tr>
        <td>tourModeChoice.atwork.model.page </td>
        <td>Integer</td>
        <td>6</td>
        <td>At-Work Sub-Tour Mode Choice UEC utility page</td>
    </tr>
    <tr>
        <td>departTime.uec.file </td>
        <td>String</td>
        <td>TourDepartureAndDuration.xls</td>
        <td>File name of Tour TOD Choice UEC</td>
    </tr>
    <tr>
        <td>departTime.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Tour TOD Choice UEC data page</td>
    </tr>
    <tr>
        <td>departTime.work.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Work Tour TOD Choice UEC utility page</td>
    </tr>
    <tr>
        <td>departTime.univ.page </td>
        <td>Integer</td>
        <td>2</td>
        <td>University Tour TOD Choice UEC utility page</td>
    </tr>
    <tr>
        <td>departTime.school.page </td>
        <td>Integer</td>
        <td>3</td>
        <td>School Tour TOD Choice UEC utility page</td>
    </tr>
    <tr>
        <td>departTime.escort.page </td>
        <td>Integer</td>
        <td>4</td>
        <td>Escort Tour TOD Choice UEC utility page</td>
    </tr>
    <tr>
        <td>departTime.shop.page </td>
        <td>Integer</td>
        <td>5</td>
        <td>Shop Tour TOD Choice UEC utility page</td>
    </tr>
    <tr>
        <td>departTime.maint.page </td>
        <td>Integer</td>
        <td>6</td>
        <td>Maintenance Tour TOD Choice UEC utility page</td>
    </tr>
    <tr>
        <td>departTime.eat.page </td>
        <td>Integer</td>
        <td>7</td>
        <td>Eating Out Tour TOD Choice UEC utility page</td>
    </tr>
    <tr>
        <td>departTime.visit.page </td>
        <td>Integer</td>
        <td>8</td>
        <td>Visiting Tour TOD Choice UEC utility page</td>
    </tr>
    <tr>
        <td>departTime.discr.page </td>
        <td>Integer</td>
        <td>9</td>
        <td>Discretionary Tour TOD Choice UEC utility page</td>
    </tr>
    <tr>
        <td>departTime.atwork.page </td>
        <td>Integer</td>
        <td>10</td>
        <td>At-Work Sub-Tour TOD Choice UEC utility page</td>
    </tr>
    <tr>
        <td>departTime.alts.file </td>
        <td>String</td>
        <td>DepartureTimeAndDurationAlternatives.csv</td>
        <td>File name of Departure time and duration alternatives</td>
    </tr>
    <tr>
        <td>jtfcp.uec.file </td>
        <td>String</td>
        <td>JointTourFrequency.xls</td>
        <td>File name of Joint Tour Frequency UEC</td>
    </tr>
    <tr>
        <td>jtfcp.alternatives.file </td>
        <td>String</td>
        <td>JointAlternatives.csv</td>
        <td>File name of joint tour alternatives by purpose and party composition combinations</td>
    </tr>
    <tr>
        <td>jtfcp.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Joint Tour Frequency UEC data page</td>
    </tr>
    <tr>
        <td>jtfcp.freq.comp.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Joint Tour Frequency UEC utility composition page</td>
    </tr>
    <tr>
        <td>jtfcp.participate.page </td>
        <td>Integer</td>
        <td>2</td>
        <td>Joint Tour Frequency UEC utility participation page</td>
    </tr>
    <tr>
        <td>inmtf.uec.file </td>
        <td>String</td>
        <td>NonMandatoryIndividualTourFrequency.xls</td>
        <td>File name of Individual non-mandatory tour frequency UEC</td>
    </tr>
    <tr>
        <td>inmtf.FrequencyExtension.ProbabilityFile </td>
        <td>String</td>
        <td>IndividualNonMandatoryTourFrequencyExtensionProbabilities_p1.csv</td>
        <td>File name of Individual non-mandatory tour frequency extension probabilities</td>
    </tr>
    <tr>
        <td>IndividualNonMandatoryTourFrequency.AlternativesList.InputFile </td>
        <td>String</td>
        <td>IndividualNonMandatoryTourFrequencyAlternatives.csv</td>
        <td>File name of individual non-mandatory tour frequency alternatives (combinations)</td>
    </tr>
    <tr>
        <td>inmtf.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Individual Non-mandatory tour frequency UEC data page</td>
    </tr>
    <tr>
        <td>inmtf.perstype1.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Individual Non-mandatory tour frequency UEC utility for Full time workers page</td>
    </tr>
    <tr>
        <td>inmtf.perstype2.page </td>
        <td>Integer</td>
        <td>2</td>
        <td>Individual Non-mandatory tour frequency UEC utility for Part time workers page</td>
    </tr>
    <tr>
        <td>inmtf.perstype3.page </td>
        <td>Integer</td>
        <td>3</td>
        <td>Individual Non-mandatory tour frequency UEC utility for University students page</td>
    </tr>
    <tr>
        <td>inmtf.perstype4.page </td>
        <td>Integer</td>
        <td>4</td>
        <td>Individual Non-mandatory tour frequency UEC utility for Non-workers page</td>
    </tr>
    <tr>
        <td>inmtf.perstype5.page </td>
        <td>Integer</td>
        <td>5</td>
        <td>Individual Non-mandatory tour frequency UEC utility for Retirees page</td>
    </tr>
    <tr>
        <td>inmtf.perstype6.page </td>
        <td>Integer</td>
        <td>6</td>
        <td>Individual Non-mandatory tour frequency UEC utility for Driving students page</td>
    </tr>
    <tr>
        <td>inmtf.perstype7.page </td>
        <td>Integer</td>
        <td>7</td>
        <td>Individual Non-mandatory tour frequency UEC utility for Pre-driving students page</td>
    </tr>
    <tr>
        <td>inmtf.perstype8.page </td>
        <td>Integer</td>
        <td>8</td>
        <td>Individual Non-mandatory tour frequency UEC utility for Preschool students page</td>
    </tr>
    <tr>
        <td>awtf.uec.file </td>
        <td></td>
        <td>AtWorkSubtourFrequency.xls</td>
        <td>File name of at-work sub-tour frequency UEC</td>
    </tr>
    <tr>
        <td>awtf.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>At-Work Sub-Tour Frequency UEC Data page</td>
    </tr>
    <tr>
        <td>awtf.model.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>At-Work Sub-Tour Frequency UEC Utility page</td>
    </tr>
    <tr>
        <td>stf.uec.file </td>
        <td>String</td>
        <td>StopFrequency.xls</td>
        <td>File name of Stop Frequency UEC</td>
    </tr>
    <tr>
        <td>stf.purposeLookup.proportions </td>
        <td>String</td>
        <td>StopPurposeLookupProportions.csv</td>
        <td>File name of Stop Purpose Lookup proportions</td>
    </tr>
    <tr>
        <td>stf.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Stop Frequency UEC data page</td>
    </tr>
    <tr>
        <td>stf.work.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Stop Frequency for Work Tour UEC utility page</td>
    </tr>
    <tr>
        <td>stf.univ.page </td>
        <td>Integer</td>
        <td>2</td>
        <td>Stop Frequency for University Tour UEC utility page</td>
    </tr>
    <tr>
        <td>stf.school.page </td>
        <td>Integer</td>
        <td>3</td>
        <td>Stop Frequency for School Tour UEC utility page</td>
    </tr>
    <tr>
        <td>stf.escort.page </td>
        <td>Integer</td>
        <td>4</td>
        <td>Stop Frequency for Escort Tour UEC utility page</td>
    </tr>
    <tr>
        <td>stf.shop.page </td>
        <td>Integer</td>
        <td>5</td>
        <td>Stop Frequency for Shop Tour UEC utility page</td>
    </tr>
    <tr>
        <td>stf.maint.page </td>
        <td>Integer</td>
        <td>6</td>
        <td>Stop Frequency for Maintenance Tour UEC utility page</td>
    </tr>
    <tr>
        <td>stf.eat.page </td>
        <td>Integer</td>
        <td>7</td>
        <td>Stop Frequency for Eating Out Tour UEC utility page</td>
    </tr>
    <tr>
        <td>stf.visit.page </td>
        <td>Integer</td>
        <td>8</td>
        <td>Stop Frequency for Visiting Tour UEC utility page</td>
    </tr>
    <tr>
        <td>stf.discr.page </td>
        <td>Integer</td>
        <td>9</td>
        <td>Stop Frequency for Discretionary Tour UEC utility page</td>
    </tr>
    <tr>
        <td>stf.subtour.page </td>
        <td>Integer</td>
        <td>10</td>
        <td>Stop Frequency for At-Work Sub-Tour UEC utility page</td>
    </tr>
    <tr>
        <td>slc.uec.file </td>
        <td>String</td>
        <td>StopLocationChoice.xls</td>
        <td>File Name of Stop Location Choice UEC</td>
    </tr>
    <tr>
        <td>slc.uec.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Stop Location Choice UEC data page</td>
    </tr>
    <tr>
        <td>slc.mandatory.uec.model.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Stop Location Choice for Mandatory Tours UEC utility page</td>
    </tr>
    <tr>
        <td>slc.maintenance.uec.model.page </td>
        <td>Integer</td>
        <td>2</td>
        <td>Stop Location Choice for Maintenance Tours UEC utility page</td>
    </tr>
    <tr>
        <td>slc.discretionary.uec.model.page </td>
        <td>Integer</td>
        <td>3</td>
        <td>Stop Location Choice for Discretionary Tours UEC utility page</td>
    </tr>
    <tr>
        <td>slc.alts.file </td>
        <td>String</td>
        <td>SlcAlternatives.csv</td>
        <td>File name of stop location choice alternatives</td>
    </tr>
    <tr>
        <td>slc.soa.uec.file </td>
        <td>String</td>
        <td>SlcSoaSize.xls</td>
        <td>File name of SOA UEC to the stop location choice </td>
    </tr>
    <tr>
        <td>slc.soa.alts.file </td>
        <td>String</td>
        <td>DestinationChoiceAlternatives.csv</td>
        <td>File name of the alternatives (MGRAs) available to the destination choice models (part of the model design; this should not be changed)</td>
    </tr>
    <tr>
        <td>auto.slc.soa.distance.uec.file </td>
        <td>String</td>
        <td>SlcSoaDistanceUtility.xls</td>
        <td>File name of Stop Location Sample of Alternatives Choice UEC for tour modes other than walk or bike - for transit, availability of stop for transit is set in java code</td>
    </tr>
    <tr>
        <td>auto.slc.soa.distance.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Stop Location SOA Choice UEC data page</td>
    </tr>
    <tr>
        <td>auto.slc.soa.distance.model.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Stop Location SOA Choice UEC utility page</td>
    </tr>
    <tr>
        <td>slc.soa.size.uec.file </td>
        <td>String</td>
        <td>SlcSoaSize.xls</td>
        <td>File Name of Stop Location Choice Size Terms UEC</td>
    </tr>
    <tr>
        <td>slc.soa.size.uec.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Stop Location Choice Size terms UEC data page</td>
    </tr>
    <tr>
        <td>slc.soa.size.uec.model.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Stop Location Choice Size terms UEC utility page</td>
    </tr>
    <tr>
        <td>stop.depart.arrive.proportions </td>
        <td>String</td>
        <td>StopDepartArriveProportions.csv</td>
        <td>File name of Stop Location Time of Day proportions</td>
    </tr>
    <tr>
        <td>tripModeChoice.uec.file </td>
        <td>String</td>
        <td>TripModeChoice.xls</td>
        <td>File name of Trip mode choice UEC</td>
    </tr>
    <tr>
        <td>plc.uec.file </td>
        <td>String</td>
        <td>ParkLocationChoice.xls</td>
        <td>File name of Parking Location Choice UEC</td>
    </tr>
    <tr>
        <td>plc.uec.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Parking Location Choice UEC data page</td>
    </tr>
    <tr>
        <td>plc.uec.model.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Parking Location Choice UEC utility page</td>
    </tr>
    <tr>
        <td>plc.alts.corresp.file </td>
        <td>String</td>
        <td>ParkLocationAlts.csv</td>
        <td>File name of parking location alternatives (MGRAs)</td>
    </tr>
    <tr>
        <td>plc.alts.file </td>
        <td>String</td>
        <td>ParkLocationSampleAlts.csv</td>
        <td>File name of parking location sample of alternatives</td>
    </tr>
    <tr>
        <td>mgra.avg.cost.output.file </td>
        <td>String</td>
        <td>/ctramp_output/mgraParkingCost.csv</td>
        <td>File name of average parking costs by MGRA</td>
    </tr>
    <tr>
        <td>mgra.avg.cost.trace.zone </td>
        <td>Integer</td>
        <td>2141</td>
        <td>Zone ID where parking cost to be traced</td>
    </tr>
    <tr>
        <td>mgra.max.parking.distance </td>
        <td>Float</td>
        <td>0.75</td>
        <td>Maximum parking distance</td>
    </tr>
    <tr>
        <td>mgra.avg.cost.dist.coeff.work </td>
        <td>Float</td>
        <td>-8.6</td>
        <td>Parking location model coefficient for walking distance to destination for Work purpose</td>
    </tr>
    <tr>
        <td>mgra.avg.cost.dist.coeff.other </td>
        <td>Float</td>
        <td>-4.9</td>
        <td>Parking location model coefficient for walking distance to destination for other purposes</td>
    </tr>
    <tr>
        <td>park.cost.reimb.mean </td>
        <td>Float</td>
        <td>-0.05</td>
        <td>Parking location model mean parking cost reimbursement</td>
    </tr>
    <tr>
        <td>park.cost.reimb.std.dev </td>
        <td>Float</td>
        <td>0.54</td>
        <td>Parking location model standard deviation for parking cost reimbursement</td>
    </tr>
    <tr>
        <td>utility.bestTransitPath.uec.file </td>
        <td>String</td>
        <td>BestTransitPathUtility.xls</td>
        <td>File name of best transit path UEC</td>
    </tr>
    <tr>
        <td>utility.bestTransitPath.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Best Transit Path UEC data page</td>
    </tr>
    <tr>
        <td>utility.bestTransitPath.tapToTap.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Best Transit Path UEC for TAP to TAP utility page</td>
    </tr>
    <tr>
        <td>utility.bestTransitPath.walkAccess.page </td>
        <td>Integer</td>
        <td>2</td>
        <td>Best Transit Path UEC for walk access utility page</td>
    </tr>
    <tr>
        <td>utility.bestTransitPath.driveAccess.page</td>
        <td>Integer</td>
        <td>3</td>
        <td>Best Transit Path UEC for drive access utility page</td>
    </tr>
    <tr>
        <td>utility.bestTransitPath.walkEgress.page</td>
        <td>Integer</td>
        <td>4</td>
        <td>Best Transit Path UEC for walk egress utility page</td>
    </tr>
    <tr>
        <td>utility.bestTransitPath.driveEgress.page</td>
        <td>Integer</td>
        <td>5</td>
        <td>Best Transit Path UEC for drive egress utility page</td>
    </tr>
    <tr>
        <td>utility.bestTransitPath.driveAccDisutility.page </td>
        <td>Integer</td>
        <td>6</td>
        <td>Best Transit Path UEC for drive access disutility page</td>
    </tr>
    <tr>
        <td>utility.bestTransitPath.driveEgrDisutility.page </td>
        <td>Integer</td>
        <td>7</td>
        <td>Best Transit Path UEC for drive egress disutility page</td>
    </tr>
    <tr>
        <td>utility.bestTransitPath.skim.sets</td>
        <td>Integer</td>
        <td>3</td>
        <td>Number of skim sets in best transit path </td>
    </tr>
    <tr>
        <td>utility.bestTransitPath.alts </td>
        <td>Integer</td>
        <td>4</td>
        <td>Number of alternatives in best transit path</td>
    </tr>
    <tr>
        <td>utility.bestTransitPath.maxPathsPerSkimSetForLogsum</td>
        <td>String</td>
        <td>1, 1, 1</td>
        <td>Maximum number of paths per skims set to use for logsum (by iteration?)</td>
    </tr>
    <tr>
        <td>utility.bestTransitPath.nesting.coeff</td>
        <td>Float</td>
        <td>0.24</td>
        <td>Nesting coefficient</td>
    </tr>
    <tr>
        <td>ResimulateTransitPath.uec.file </td>
        <td>String</td>
        <td>BestTransitPathUtility.xls</td>
        <td>File name of transit capacity restraint resimulation</td>
    </tr>
    <tr>
        <td>ResimulateTransitPath.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Transit capacity restraint data page</td>
    </tr>
    <tr>
        <td>ResimulateTransitPath.identifyTripToResimulate.page </td>
        <td>Integer</td>
        <td>8</td>
        <td>Transit capacity restraint utility page</td>
    </tr>
    <tr>
        <td>ResimulateTransitPath.results.IndivTripDataFile </td>
        <td>String</td>
        <td>/ctramp_output/indivTripDataResim.csv</td>
        <td>File name of resimulated individual trips data</td>
    </tr>
    <tr>
        <td>ResimulateTransitPath.results.JointTripDataFile </td>
        <td>String</td>
        <td>/ctramp_output/jointTripDataResim.csv</td>
        <td>File name of resimulated joint trips data</td>
    </tr>
    <tr>
        <td>skims.auto.uec.file </td>
        <td>String</td>
        <td>AutoSkims.xls</td>
        <td>File name of Auto Skims UEC</td>
    </tr>
    <tr>
        <td>skims.auto.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Auto Skims data page</td>
    </tr>
    <tr>
        <td>skims.auto.ea.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Auto skims Early AM utility page</td>
    </tr>
    <tr>
        <td>skims.auto.am.page </td>
        <td>Integer</td>
        <td>2</td>
        <td>Auto skims AM utility page</td>
    </tr>
    <tr>
        <td>skims.auto.md.page </td>
        <td>Integer</td>
        <td>3</td>
        <td>Auto skims MD utility page</td>
    </tr>
    <tr>
        <td>skims.auto.pm.page </td>
        <td>Integer</td>
        <td>4</td>
        <td>Auto skims PM utility page</td>
    </tr>
    <tr>
        <td>skims.auto.ev.page </td>
        <td>Integer</td>
        <td>5</td>
        <td>Auto skims Evening utility page</td>
    </tr>
    <tr>
        <td>taz.distance.uec.file </td>
        <td>String</td>
        <td>tazDistance.xls</td>
        <td>File name of TAZ Distance UEC</td>
    </tr>
    <tr>
        <td>taz.distance.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>TAZ Distance UEC data page</td>
    </tr>
    <tr>
        <td>taz.od.distance.ea.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>TAZ Distance UEC Early AM utility page</td>
    </tr>
    <tr>
        <td>taz.od.distance.am.page </td>
        <td>Integer</td>
        <td>2</td>
        <td>TAZ Distance UEC AM utility page</td>
    </tr>
    <tr>
        <td>taz.od.distance.md.page </td>
        <td>Integer</td>
        <td>3</td>
        <td>TAZ Distance UEC MD utility page</td>
    </tr>
    <tr>
        <td>taz.od.distance.pm.page </td>
        <td>Integer</td>
        <td>4</td>
        <td>TAZ Distance UEC PM utility page</td>
    </tr>
    <tr>
        <td>taz.od.distance.ev.page </td>
        <td>Integer</td>
        <td>5</td>
        <td>TAZ Distance UEC Evening utility page</td>
    </tr>
    <tr>
        <td>skim.walk.transit.walk.uec.file </td>
        <td>String</td>
        <td>WalkTransitWalkSkims.xls</td>
        <td>File name of Walk Transit Walk Skims UEC</td>
    </tr>
    <tr>
        <td>skim.walk.transit.walk.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Walk Transit Walk Skims UEC data page</td>
    </tr>
    <tr>
        <td>skim.walk.transit.walk.skim.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Walk Transit Walk Skims UEC skim page</td>
    </tr>
    <tr>
        <td>skim.walk.transit.walk.sets </td>
        <td>Integer</td>
        <td>3</td>
        <td></td>
    </tr>
    <tr>
        <td>skim.walk.transit.walk.skims </td>
        <td>Integer</td>
        <td>12</td>
        <td></td>
    </tr>
    <tr>
        <td>skim.walk.transit.drive.uec.file </td>
        <td>String</td>
        <td>WalkTransitDriveSkims.xls</td>
        <td>File name of Walk Transit Drive Skims UEC</td>
    </tr>
    <tr>
        <td>skim.walk.transit.drive.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Walk Transit Drive Skims UEC data page</td>
    </tr>
    <tr>
        <td>skim.walk.transit.drive.skim.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Walk Transit Drive Skims UEC skim page</td>
    </tr>
    <tr>
        <td>skim.walk.transit.drive.sets </td>
        <td>Integer</td>
        <td>3</td>
        <td></td>
    </tr>
    <tr>
        <td>skim.walk.transit.drive.skims </td>
        <td>Integer</td>
        <td>12</td>
        <td></td>
    </tr>
    <tr>
        <td>skim.drive.transit.walk.uec.file </td>
        <td>String</td>
        <td>DriveTransitWalkSkims.xls</td>
        <td>File name of Drive Transit Walk Skims UEC</td>
    </tr>
    <tr>
        <td>skim.drive.transit.walk.data.page </td>
        <td>Integer</td>
        <td>0</td>
        <td>Drive Transit Walk Skims UEC data page</td>
    </tr>
    <tr>
        <td>skim.drive.transit.walk.skim.page </td>
        <td>Integer</td>
        <td>1</td>
        <td>Drive Transit Walk Skims UEC skim page</td>
    </tr>
    <tr>
        <td>skim.drive.transit.walk.sets </td>
        <td>Integer</td>
        <td>3</td>
        <td></td>
    </tr>
    <tr>
        <td>skim.drive.transit.walk.skims </td>
        <td>Integer</td>
        <td>12</td>
        <td></td>
    </tr>
    <tr>
        <td colspan="4"><a id="transit_path_data"><b>Best Transit Path Data Files</b></a></td>
    </tr>
    <tr>
        <td>tap.data.file </td>
        <td>String</td>
        <td>hwy/tap_data.csv</td>
        <td>Location of the file having information about parking lot capacity for TAPS</td>
    </tr>
    <tr>
        <td>tap.data.tap.column </td>
        <td>String</td>
        <td>tap</td>
        <td>Column name for TAP IDs</td>
    </tr>
    <tr>
        <td>tap.data.taz.column </td>
        <td>String</td>
        <td>taz</td>
        <td>Column name TAZ IDs</td>
    </tr>
    <tr>
        <td>tap.data.lotid.column </td>
        <td>String</td>
        <td>lotid</td>
        <td>Column name for parking lot IDs</td>
    </tr>
    <tr>
        <td>tap.data.capacity.column </td>
        <td>String</td>
        <td>capacity</td>
        <td>Column name for parking lot capacity</td>
    </tr>
    <tr>
        <td>tap.station.attribute.file </td>
        <td>String</td>
        <td>trn/emme_network_transaction_files_AM/station_attributes/station_tap_attributes.csv</td>
        <td>Location of station attribute data</td>
    </tr>
    <tr>
        <td>tap.pnr.default.share </td>
        <td>Integer</td>
        <td>0.5</td>
        <td>PNR share value</td>
    </tr>
    <tr>
        <td>taz.tap.access.file </td>
        <td>String</td>
        <td>/skims/drive_maz_taz_tap.csv</td>
        <td>Location of file having cost information related drive access between TAZ-TAP pairs</td>
    </tr>
    <tr>
        <td>taz.tap.access.ftaz.column </td>
        <td>String</td>
        <td>FTAZ</td>
        <td>Column containing start TAZ</td>
    </tr>
    <tr>
        <td>taz.tap.access.mode.column </td>
        <td>String</td>
        <td>MODE</td>
        <td>Column containing mode</td>
    </tr>
    <tr>
        <td>taz.tap.access.period.column </td>
        <td>String</td>
        <td>PERIOD</td>
        <td>Column containing time periods</td>
    </tr>
    <tr>
        <td>taz.tap.access.ttap.column </td>
        <td>String</td>
        <td>TTAP</td>
        <td>Column containing transit TAPs</td>
    </tr>
    <tr>
        <td>taz.tap.access.tmaz.column </td>
        <td>String</td>
        <td>TMAZ</td>
        <td>Column containing transit MAZs</td>
    </tr>
    <tr>
        <td>taz.tap.access.ttaz.column </td>
        <td>String</td>
        <td>TTAZ</td>
        <td>Column containing transit TAZs</td>
    </tr>
    <tr>
        <td>taz.tap.access.dtime.column </td>
        <td>String</td>
        <td>DTIME</td>
        <td>Column containing drive times</td>
    </tr>
    <tr>
        <td>taz.tap.access.ddist.column </td>
        <td>String</td>
        <td>DDIST</td>
        <td>Column containing drive distances</td>
    </tr>
    <tr>
        <td>taz.tap.access.dtoll.column </td>
        <td>String</td>
        <td>DTOLL</td>
        <td>Column containing drive tolls</td>
    </tr>
    <tr>
        <td>taz.tap.access.wdist.column </td>
        <td>String</td>
        <td>WDIST</td>
        <td>Column containing walk distances</td>
    </tr>
    <tr>
        <td colspan="4"><a id="misc"><b>Miscellaneous: Place Holders for Future Enhancements</b></a></td>
    </tr>
    <tr>
        <td>taz.data.file </td>
        <td>String</td>
        <td>/landuse/taz_data.csv</td>
        <td>location of TAZ landuse file</td>
    </tr>
    <tr>
        <td>taz.data.taz.column </td>
        <td>String</td>
        <td>TAZ</td>
        <td>Column containing TAZ IDs</td>
    </tr>
    <tr>
        <td>taz.data.avgttd.column </td>
        <td>String</td>
        <td>AVGTTS</td>
        <td>Column containing </td>
    </tr>
    <tr>
        <td>taz.data.dist.column </td>
        <td>String</td>
        <td>DIST</td>
        <td>Column containing distances</td>
    </tr>
    <tr>
        <td>taz.data.pctdetour.column </td>
        <td>String</td>
        <td>PCTDETOUR</td>
        <td>Column containing </td>
    </tr>
    <tr>
        <td>taz.data.terminal.column </td>
        <td>String</td>
        <td>TERMINALTIME</td>
        <td>Column containing terminal times</td>
    </tr>
</table>
