---
layout: page
title: Guide
---

*Work in Progress*

# Users' Guide

*Model Version 1.0*

** CONTENTS **

1. [Computing Environment](#Computing-Environment) 
2. [System Design](#System-Design) 


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

## Model Execution

## CT-RAMP Properties File

## Input Files

## Output Files

## Model Schematic

## Level of Service Information

## Networks

