---
layout: page
title: Network Building Guide
---

# Network Building Guide

This is a step-by-step guide for Travel Model Two users who want to build or modify the roadway and transit networks using the tool [NetworkWrangler](https://github.com/BayAreaMetro/NetworkWrangler).

These instructions are written assuming installation on Windows (tested on Windows 10).

---
CONTENTS

1. [Setting it up for the first time](#Setting-it-up-for-the-first-time)
   1. [Software requirements](#software-requirements)
   1. [Using the command line, python interpreter, and the NetworkWrangler Python module](#using-the-command-line-python-interpreter-and-the-networkwrangler-python-module)
1. [Build a network](#build-a-network)
   1. [Build a Future](#build-a-future)
   1. [Build a Test Network](#build-a-test-network)
1. [Coding a project](#Coding-a-project)

---

## Setting it up for the first time

### Software requirements
To build model networks, the following software needs to be installed on your computer.

* **Install [Python](https://www.python.org/downloads/)** if you don't already have it. [NetworkWrangler](https://github.com/BayAreaMetro/NetworkWrangler) should work with either Python 2 or Python 3.  You'll also need [pip](https://pypi.org/project/pip/) to help you to install python modules, but this should be [included](https://pip.pypa.io/en/stable/installing/) with Python 2 if your version is >= 2.7.9 and with Python 3 if your version >= 3.4.  We typically install the 64-bit version of python (not the 32-bit version) and install it in the root level (e.g. `C:\Python27` or `C:\Python35`). **Be sure to note where your Python is installed.**   Python is a fairly easy language to learn and there are some nice tutorials for Python online ([Python 2 tutorial](https://docs.python.org/2/tutorial/), [Python 3 tutorial](https://docs.python.org/3/tutorial/)) if you're unfamiliar with it.
*	**Install [Citilabs Cube 6.4.4 or newer](http://www.citilabs.com/support/downloads/).** After installing when you run the application, you'll be asked where the license server is located -- there is a note in Lisa's office with this information.  Cube is typically installed in `C:\Program Files (x86)\Citilabs`, and `RUNTPP.EXE` is typically found in `C:\Program Files (x86)\Citilabs\CubeVoyager`.
* **Install [Github Desktop](https://desktop.github.com/).**  You can use this for the next step, cloning *NetworkWrangler* from Github, and also for committing changes to the *NetworkWrangler* network configuration back to github.
* **Clone [NetworkWrangler from Github](https://github.com/BayAreaMetro/NetworkWrangler)** and keep track of where you cloned it.  We typically clone it into our personal `Documents` folder or `Documents\GitHub`.  For example, Flavia's installation is in `C:\Users\ftsang\Documents\GitHub\NetworkWrangler`.
* **Install [Git](https://git-scm.com/downloads).**  This is related to, but not the same as the [GitHub Desktop application](https://desktop.github.com/); we'll need it because projects are coded as local git repositories (that are not on Github).  This is typically installed in `C:\Program Files\Git`.
* **Install [Box Drive](https://www.box.com/resources/downloads/drive).**  This is because our 2015 base networks are in Box and using Box Drive ensures you're testing with the most recent versions.  If you don't have access to the [2015 base network inputs here](https://mtcdrive.box.com/s/qbkhr1y6gedifou5i84nm41frtrsco5k), contact a member of the modeling team.  Take note of where Box Drive syncs this folder to your local disk since you'll need that to [Build a network](#build-a-network) below.


### Using the command line, python interpreter, and the NetworkWrangler Python module

The next step is to test if you can import Wrangler. Open a command window, and type in the following DOS commands:

#### Stop 0: Open a Command Prompt window.

To open a command prompt window, open `cmd.exe`, which comes with Windows.  

I suggest right clicking the top bar of the window and selecting *Properties*, and updating the fonts and colors of the window since the defaults are hideous and hard to read.  *Lucida Console* is a much easier font to read.  You can also change the *Screen Buffer Size* (the Height will control how many lines you can scroll back and see as you do you work, so I usually make this large: 5000) and the *Window Size* here.  Changes you make here will be applied to subsequent command prompt windows you open, so these customizations will last.  See also: [How to make the command prompt look & work better](https://www.digitalcitizen.life/how-customize-command-prompt)

#### Step 1: Add the location of `python.exe` and `pip.exe` to your system's `PATH` environment variable.

This is so that Windows will know where Python is when you try to run it. To do so, you’ll need to know where your `python.exe` is installed.  For example, if your `python.exe` is installed in `C:\Python27`, type the command as below into your command prompt. If your `python.exe` is installed elsewhere, replace `C:\Python27` with your `python.exe` location.  It's also helpful to include the `Scripts` subdirectory of your python installation, since that's where [`pip.exe`](https://pypi.org/project/pip/) is located, which is used for installing python modules.

```dosbatch
C:\>set PATH=%PATH%;C:\Python27;C:\Python27\Scripts
```

#### Step 2: Add the location of Citilabs Cube's `RUNTPP.EXE` to your system's `PATH` environment variable.

This is so that Windows will know where this executable is when *NetworkWrangler* tries to run it in order to build networks.  Again, you’ll need to know where Cube's `RUNTPP.EXE` is installed. Below is an example command assuming `RUNTPP.EXE` is installed in `C:\Program Files (x86)\Citilabs\CubeVoyager`. Adjust the command according to the location of your `RUNTPP.EXE`.

```dosbatch
C:\>set PATH=%PATH%;C:\Program Files (x86)\Citilabs\CubeVoyager
```

#### Step 3: Add the location of *NetworkWrangler* to your system's `PYTHONPATH` environment variable.

This is required so python will know where *NetworkWrangler* is so that it can be imported.  This is necessary for this module but not modules installed by *pip* because *NetworkWrangler* is not installed in the typical location for standard python modules (since it's our own custom python code rather than a module that has been released to the [Python Package Index](https://pypi.org/)). You’ll need to include both the root directory, `NetworkWrangler`, as well as the `_static_` subdirectory of `NetworkWrangler`. The examples below assume that GitHub repository is cloned into `C:\Users\ftsang\Documents\GitHub`; modify the path as appropriate for your installation of *NetworkWrangler*.

```dosbatch
C:\>set PYTHONPATH=%PYTHONPATH%;C:\Users\ftsang\Documents\GitHub\NetworkWrangler;C:\Users\ftsang\Documents\GitHub\NetworkWrangler\_static
```

### Step 4: Run the python interpreter

In your command prompt window, when you run the command of `python`, you'll enter into the *python interpreter*.  This means that subsequent commands are interpretted as lines of Python rather than as Windows DOS commands.  When you enter into the *python interpreter*, the command window should display a message about the version of your python and the prompt will change to be `>>>` instead of `[your current working directory]>`.

To exit the python interpreter, type the python command, `quit()`.

**Note that python, unlike Windows DOS, is case-sensitive.**

```dosbatch
C:\>python
Python 2.7.8 (default, Jun 30 2014, 16:08:48) [MSC v.1500 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> print("This is a python print command")
This is a python print command
>>> print("Type quit() to exit the python interpreter")
Type quit() to exit the python interpreter
>>> quit()

C:\>
```

### Step 5: Import the NetworkWrangler module into python.

While in the python interpreter, try to import NetworkWrangler.  A successful import will look like the following.

```dosbatch
C:\>python
Python 2.7.8 (default, Jun 30 2014, 16:08:48) [MSC v.1500 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> import Wrangler
('Importing ', 'C:\\Users\\lzorn\\Documents\\NetworkWrangler\\_static\\dataTable.pyc')
('Importing ', 'C:\\Users\\lzorn\\Documents\\NetworkWrangler\\Wrangler\\TransitAssignmentData.pyc')
>>>
```

The most likely type of error you'll get here is an import error if a module required to *NetworkWrangler* fails to load.  For example, if the required module, *xlrd*, is not installed, it'll look like this:

```dosbatch
C:\>python
Python 2.7.8 (default, Jun 30 2014, 16:08:48) [MSC v.1500 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> import Wrangler
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "C:\Users\lzorn\Documents\NetworkWrangler\Wrangler\__init__.py", line 9, in <module>
    from .TransitAssignmentData import TransitAssignmentData ##
  File "C:\Users\lzorn\Documents\NetworkWrangler\Wrangler\TransitAssignmentData.py", line 5, in <module>
    import csv,os,logging,string,sys,xlrd
ImportError: No module named xlrd
>>>
```

To resolve, quit the python interpreter and install the missing python module using *pip*.  Then try again:

```dosbatch
C:\>python
Python 2.7.8 (default, Jun 30 2014, 16:08:48) [MSC v.1500 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> import Wrangler
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "C:\Users\lzorn\Documents\NetworkWrangler\Wrangler\__init__.py", line 9, in <module>
    from .TransitAssignmentData import TransitAssignmentData ##
  File "C:\Users\lzorn\Documents\NetworkWrangler\Wrangler\TransitAssignmentData.py", line 5, in <module>
    import csv,os,logging,string,sys,xlrd
ImportError: No module named xlrd
>>> quit()

C:\>pip install xlrd
Collecting xlrd
  Downloading https://files.pythonhosted.org/packages/07/e6/e95c4eec6221bfd8528bcc4ea252a850bffcc4be88ebc367e23a1a84b0bb/xlrd-1.1.0-py2.py3-none-any.whl (108kB)
    100% |UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU| 112kB 656kB/s
Installing collected packages: xlrd
Successfully installed xlrd-1.1.0

C:\>python
Python 2.7.8 (default, Jun 30 2014, 16:08:48) [MSC v.1500 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> import Wrangler
('Importing ', 'C:\\Users\\lzorn\\Documents\\NetworkWrangler\\_static\\dataTable.pyc')
('Importing ', 'C:\\Users\\lzorn\\Documents\\NetworkWrangler\\Wrangler\\TransitAssignmentData.pyc')
>>>
```
For most current python users, the required modules are:
* [xlrd](https://pypi.org/project/xlrd/)
* [SimpleParse](https://pypi.org/project/SimpleParse/)
* [numpy](https://pypi.org/project/numpy/)

If you are using python 3, you may need [pywin32](https://pypi.org/project/pywin32/) as well.

## Build a Network

Now that we can import *NetworkWrangler*, it's time to build a network!

There are two network building scripts and they each have their own configuration.  The following documentation assumes you'll use your local [NetworkWrangler\scripts](https://github.com/BayAreaMetro/NetworkWrangler/tree/master/scripts) as your working directory, so navigate there in the command prompt:

```dosbatch
C:\>cd Users\lzorn\Documents\NetworkWrangler\scripts

C:\Users\lzorn\Documents\NetworkWrangler\scripts>
```

### Build a Future

The futures network script and configuration exists to build the networks for each of the [three Horizon futures](https://mtc.ca.gov/sites/default/files/Horizon-Futures_Shortlist.pdf).  The network building script is [build_network_mtc_futures.py](https://github.com/BayAreaMetro/NetworkWrangler/blob/master/scripts/build_network_mtc_futures.py) and its configuration is [net_spec_futures_round1.py](https://github.com/BayAreaMetro/NetworkWrangler/blob/master/scripts/net_spec_futures_round1.py).

In order to use the script, you will need to set the `PIVOT_DIR` (which is the base network dir) to point to the location of the 2015 base network inputs which should be available via Box Drive.  For example, the location of my inputs are [committed into the network config](https://github.com/BayAreaMetro/NetworkWrangler/blob/master/scripts/net_spec_futures_round1.py#L14), but yours may vary depending on which directory is at your top Box level.
```python
PIVOT_DIR = os.path.join(os.environ["USERPROFILE"], "Box","Modeling and Surveys","Development","Travel Model Two Development","Model Inputs","2015_revised_mazs")
```

To build a Futures network series, run:

```dosbatch
C:\Users\lzorn\Documents\NetworkWrangler\scripts>python build_network_mtc_futures.py net_spec_futures_round1.py CleanAndGreen
('Importing ', 'C:\\Users\\lzorn\\Documents\\NetworkWrangler\\_static\\dataTable.pyc')
('Importing ', 'C:\\Users\\lzorn\\Documents\\NetworkWrangler\\Wrangler\\TransitAssignmentData.pyc')
Network Specification: build_network_mtc_futures.py
WranglerLogger: DEBUG    Using tier network C:\Users\lzorn\Box\Modeling and Surveys\Development\Travel Model Two Development\Model Inputs\2015_revised_mazs\hwy\FREEFLOW.net
WranglerLogger: DEBUG    convertLineData: PROGRAM: PT

[lots of output omitted]

WranglerLogger: DEBUG    Successfully completed running C:\Users\lzorn\Documents\NetworkWrangler\scripts\scratch\build_network_mtc_futures.py

C:\Users\lzorn\Documents\NetworkWrangler\scripts>dir CleanAndGreen
 Volume in drive C has no label.
 Volume Serial Number is E89B-14C9

 Directory of C:\Users\lzorn\Documents\NetworkWrangler\scripts\CleanAndGreen

09/18/2018  06:40 PM    <DIR>          .
09/18/2018  06:40 PM    <DIR>          ..
09/18/2018  06:40 PM    <DIR>          network_2015
09/18/2018  06:40 PM    <DIR>          network_2045
               0 File(s)              0 bytes
               4 Dir(s)  104,776,904,704 bytes free
```

This creates the 2015 network (really just a copy of the base) and the 2045 network, which has 1 foot of Sea Level Rise.  As we create projects, those will get added to the [network configuration's `NETWORK_PROJECTS`](https://github.com/BayAreaMetro/NetworkWrangler/blob/master/scripts/net_spec_futures_round1.py#L29) based on the project's opening year, and more intermediate year networks will get created; the script does not create an intermediate year network unless a project has been applied.

### Build a Test Network

The test network script and configuration are very similar, but they exist as a convenience to test the project coding that you're working on.  As the network projects get coded and the Futures network configuration becomes more filled out, building a full network series for each future will become slower.  To make project coding easier, the test network script and configuration exist to build a bare-bones network so you can add only the project you're working on (and it's required projects, if any) for testing.

The network building script is [build_network_mtc.py](https://github.com/BayAreaMetro/NetworkWrangler/blob/master/scripts/build_network_mtc.py) and its configuration is [net_spec_test.py](https://github.com/BayAreaMetro/NetworkWrangler/blob/master/scripts/net_spec_test.py).

Similar to above, in order to use the script, you will need to set the [`PIVOT_DIR` location](https://github.com/BayAreaMetro/NetworkWrangler/blob/master/scripts/net_spec_test.py#L18) to point to the location of the 2015 base network inputs which should be available via Box Drive. 

```dosbatch
C:\Users\lzorn\Documents\NetworkWrangler\scripts>python build_network_mtc.py net_spec_test.py
('Importing ', 'C:\\Users\\lzorn\\Documents\\NetworkWrangler\\_static\\dataTable.pyc')
('Importing ', 'C:\\Users\\lzorn\\Documents\\NetworkWrangler\\Wrangler\\TransitAssignmentData.pyc')
Network Specification: build_network_mtc.py
WranglerLogger: DEBUG    Using tier network C:\Users\lzorn\Box\Modeling and Surveys\Development\Travel Model Two Development\Model Inputs\2015_revised_mazs\hwy\FREEFLOW.net
WranglerLogger: DEBUG    convertLineData: PROGRAM: PT

[lots of output omitted]

WranglerLogger: DEBUG    Successfully completed running C:\Users\lzorn\Documents\NetworkWrangler\scripts\scratch\build_network_mtc.py

C:\Users\lzorn\Documents\NetworkWrangler\scripts>dir Test_Scenario_network*
 Volume in drive C has no label.
 Volume Serial Number is E89B-14C9

 Directory of C:\Users\lzorn\Documents\NetworkWrangler\scripts

08/22/2018  03:32 PM    <DIR>          Test_Scenario_network_2020
               0 File(s)              0 bytes
               1 Dir(s)  104,662,265,856 bytes free
```

### Congratulations!  This is the checkpoint for our **NetworkWrangler Workshop Part 2**!

![Woot](https://media.giphy.com/media/JzvALW6b4Plss/giphy.gif)

## Coding a Project

Network projects are coded as folders within **`M:\Application\Model Two\NetworkProjects`**.  Each project or folder is a local Git repository.  To code a project, you'll likely want to start with a similar seed project (more on that below) and create a new folder, name it appropriately and copy the contents of the seed project into your folder to start.  Make sure you do not copy the `.git` folder, as that is the git version history of the seed project, and your project will have its own git version history.

The basic files required in a project are:
* `README.txt` - While not technically *required*, it's good practice to keep basic documentation and notes here.  Since we plan to keep much of our notes/conversations on Asana, assuming we continue that practice, a link the relevant Asana task is sufficient.
* `__init__.py` - This makes the project serve as a python module, so that *NetworkWrangler* can import it.  
   * The `desc()` method should return a short string description of the project
   * The `year()` method should return the project's opening year
   * For transit projects, the `applyEdits()` method will be meaningful; more on that later.
* `apply.s` - This Cube script is run for roadway projects.  More on that below.
* data files - These names can vary depending on what the project does to the network, although it'd be nice for them to have intuitive names.

### Coding a Roadway Project

Roadway projects can take basically (one or more of) six actions:

| Action | Example Project |
|--------|-----------------|
| Create new nodes | *SMART* |
| Modify attributes for nodes | To be created. |
| Delete nodes | None yet and this may not ever be necessary |
| Create new links | To be created |
| Modify attributes for links | *ALA050014_SR84_Livermore* |
| Delete links | *SeaLevelRise_1foot* |


### Specifying the network changes
Step 1: Create a new directory for the set of network changes in here: M:\Application\Model Two\NetworkProjects. (This location is hard-coded in the script build_network_mtc.py)

Step 2: Copy apply.s, mod.dat, del.dat, __init__.py and README.txt from a previous project to this new directory

Step 3: Specify links to be modified or deleted in mod.dat and del.dat

Step 4: Edit __init__.py as appropriate (in most cases, I only have to edit the description text field e.g. d="Test SLR 1"); Also enter information in readme.txt as appropriate

Step 5: Create a new Git repository here
-	Right click in the blank space of this folder
-	Choose “Git GUI here”
-	Choose “Create New Repository”
-	Select the current folder and click “Create”
-	On the top left quadrant, click on each file to move the files from “unstaged” to “staged”
-	Supply a commit message
-	Click “Commit”

### Getting ready to run Wrangler
Step 1: Go into or create a directory for the scenario. This is where the specification file (network_test_specification.py) will be saved

Step 2: Modify network_test_specification.py in a text editor. Remember to:
•	Go through all the mandatory fields
•	make sure the piv_directory is correct
•	make sure the directory where the network changes are specified is named here
o	e.g. 'hwy':['test_SLR1']
o	e.g. 'trn':[], # 'test_trn_proj'
(note: the hwy directory should include: turnsam.pen, turnsop.pen, turnspm.pen)

### Run Wrangler
Step 1: Open a command window

Step 2: “cd” into the directory for the scenario. This is where the specification file (network_test_specification.py) is saved.

Step 3: run the DOS commands  below

```
REM Set the path DOS environment variable and python path
set PATH= %PATH%;C:\Python27
set PYTHONPATH=%PYTHONPATH%;C:\Python27

REM Set the Cube Voyager path
set PATH= %PATH%;C:\Program Files (x86)\Citilabs\CubeVoyager

REM Set the pythonpath to point to wrangler
set PYTHONPATH=%PYTHONPATH%;C:\Users\ftsang\Documents\GitHub\NetworkWrangler\
set PYTHONPATH=%PYTHONPATH%;C:\Users\ftsang\Documents\GitHub\NetworkWrangler\_static

REM run wrangler
REM cd into the folder where the specification file (network_test_specification.py) is stored, if you haven't
python C:\Users\ftsang\Documents\GitHub\NetworkWrangler\scripts\build_network_mtc.py network_test_specification.py
```

Users will be asked about pre-requisite, co-requisite and conflicting projects. In most MTC applications, just answer “y”for yes  to these.

The output .net file would be in \scratch\[name you chose in the specification file]\hwy, inside the current working directory

### Checks
The script currently doesn’t check whether Cube successfully runs. But users can check the .prn file in the subdirectory Wrangler_tmp_ xxxxx\[test name] to confirm this.
(this check perhaps be incorporated the script in the future)
