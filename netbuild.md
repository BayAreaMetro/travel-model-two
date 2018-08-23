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

Before using network wrangler, you’ll need to:

•	install Cube 6.4.4 or newer (http://www.citilabs.com). Cube is a proprietary software and a license will be required.

•	clone network wrangler from GitHub (https://github.com/BayAreaMetro/NetworkWrangler). When it's cloned, you should see this python script in your local GitHub directory: C:\Users\ftsang\Documents\GitHub\NetworkWrangler\scripts\build_network_mtc.py

•	install various python modules that network wrangler uses. (For most current python users, the required modules are xlrd, simpleparse, and numpy. If you are using python 3, you may need win32 as well. If additional module is needed for your specific set up, you’ll get error messages on screen to indicating which python module is needed.

•	 install Git (https://git-scm.com/downloads)

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
