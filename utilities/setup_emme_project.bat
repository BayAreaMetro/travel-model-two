::~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:: Create the MTC Toolbox and Initialize the EMME Project
:: The user needs to specify the following paths -
::		PYTHON_PATH - the path to the python directory inside the EMME installation
::		PROJECT_PATH - the path to the current model directory
::~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SET PYTHON_PATH="C:\Program Files\INRO\Emme\Emme 4\Emme-4.4.2\Python27"
REM SET PROJECT_PATH="F:\Projects\Clients\mtc\TO13_emme_network"
SET PROJECT_PATH="F:\Projects\Clients\mtc\TO13_emme_network"

python cube_to_emme_network_conversion.py
IF ERRORLEVEL 1 goto done
%PYTHON_PATH%\python %PROJECT_PATH%\create_emme_network.py -r %PROJECT_PATH% -n "mtc_emme"
IF ERRORLEVEL 1 goto done
%PYTHON_PATH%\python %PROJECT_PATH%\skim_transit_network.py -r %PROJECT_PATH% -n "mtc_emme"
IF ERRORLEVEL 1 goto done

PAUSE
