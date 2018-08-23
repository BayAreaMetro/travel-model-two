---
layout: page
title: Network Building Guide
---

# Network Building Guide

---
CONTENTS

1. [Setting it up for the first time](#Setting-it-up-for-the-first-time)
1. [Coding a project](#Coding-a-project)

---

## Setting it up for the first time


### Software requirements
Before using network wrangler, you’ll need to:

•	install Cube 6.4.4 or newer (http://www.citilabs.com). Cube is a proprietary software and a license will be required.

•	clone network wrangler from GitHub (https://github.com/BayAreaMetro/NetworkWrangler). When it's cloned, you should see this python script in your local GitHub directory: C:\Users\ftsang\Documents\GitHub\NetworkWrangler\scripts\build_network_mtc.py

•	install various python modules that network wrangler uses. (For most current python users, the required modules are xlrd, simpleparse, and numpy. If you are using python 3, you may need win32 as well. If additional modules are needed for your specific set up, when you import NetworkWranger for the first time you’ll get error messages on screen to indicating which python module is needed.

•	 install Git (https://git-scm.com/downloads)

### Importing Wrangler

The next step is to test if you can import Wrangler. Open a command window, and type in the following DOS commands:

Step 1: Set the path to python. You’ll need to do this for two environment variables and you’ll need to know where your python.exe is installed. For example, if your python.exe is installed in C:\Python27, type the commands as below. If your python.exe is installed elsewhere, replace C:\Python27 with your path.

**C:\>set PATH= %PATH%;C:\Python27**
**C:\>set PYTHONPATH=%PYTHONPATH%;C:\Python27**

Step 2: Make sure Cube Voyager is on the path. Again, you’ll need to know where Cube Voyager (runtpp.exe) is installed. Below is an example command assuming runtpp.exe is installed in C:\Program Files (x86)\Citilabs\CubeVoyager. Adjust the command according to the location of your runtpp.exe.

**C:\>set PATH= %PATH%;C:\Program Files (x86)\Citilabs\CubeVoyager**

Step 3: Point the pythonpath to NetworkWrangler. You’ll need to do this at two levels:

**set PYTHONPATH=%PYTHONPATH%;C:\Users\ftsang\Documents\GitHub\NetworkWrangler\
**set PYTHONPATH=%PYTHONPATH%;C:\Users\ftsang\Documents\GitHub\NetworkWrangler\_static

Step 4: Open up the python interpreter by type in
C:\>Python

(After you type in “python” and hit enter, the command window should display a message about the version of your python. You should also see that the command line start with >>> instead of >. See example below.)

Python 2.7.14 (v2.7.14:84471935ed, Sep 16 2017, 20:25:58) [MSC v.1500 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>>

Step 5: Import NetworkWrangler. Type:

**>>>Import Wrangler**

(Note that this importing command is case sensitive – it only works if you type Wrangler with W in caps. After you type in the command, if the command window displays the following messages, it means you have successfully imported NetworkWrangler.)

('Importing ', 'C:\\Users\\ftsang\\Documents\\GitHub\\NetworkWrangler\\_static\\dataTable.pyc')
('Importing ', 'C:\\Users\\ftsang\\Documents\\GitHub\\NetworkWrangler\\Wrangler\\TransitAssignmentData.pyc')
>>>

(Flavia to add a bit more on pip install here)
---

## Coding a project

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

### Getting ready to run network wrangler 
Step 1: Go into or create a directory for the scenario. This is where the specification file (network_test_specification.py) will be saved

Step 2: Modify network_test_specification.py in Notepad or other text editors. Remember to:
•	Go through all the mandatory fields
•	make sure the piv_directory is correct
•	make sure the directory where the network changes are specified is named here
o	e.g. 'hwy':['test_SLR1'] 
o	e.g. 'trn':[], # 'test_trn_proj'
(note: the hwy directory should include: turnsam.pen, turnsop.pen, turnspm.pen)

### Run Network Wrangler
Step 1: Open a command window

Step 2: “cd” into the directory for the scenario. This is where the specification file (network_test_specification.py) is saved.

Step 3: run the DOS commands  below

--
REM Set the path DOS environment variable and python path
set PATH= %PATH%;C:\Python27
set PYTHONPATH=%PYTHONPATH%;C:\Python27

REM Set the Cube Voyager path
set PATH= %PATH%;C:\Program Files (x86)\Citilabs\CubeVoyager

REM Set the pythonpath to point to network wrangler 
set PYTHONPATH=%PYTHONPATH%;C:\Users\ftsang\Documents\GitHub\NetworkWrangler\
set PYTHONPATH=%PYTHONPATH%;C:\Users\ftsang\Documents\GitHub\NetworkWrangler\_static

REM run network wrangler
REM cd into the folder where the specification file (network_test_specification.py) is stored, if you haven't
python C:\Users\ftsang\Documents\GitHub\NetworkWrangler\scripts\build_network_mtc.py network_test_specification.py
	
--

Users will be asked about pre-requisite, co-requisite and conflicting projects. In most MTC applications, just answer “y”for yes  to these.

The output .net file would be in \scratch\[name you chose in the specification file]\hwy, inside the current working directory

### Checks 
The script currently doesn’t check whether Cube successfully runs. But users can check the .prn file in the subdirectory Wrangler_tmp_ xxxxx\[test name] to confirm this.
(this check perhaps be incorporated the script in the future)
