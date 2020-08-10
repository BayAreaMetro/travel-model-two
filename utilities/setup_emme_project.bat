::~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:: Create the Oregon Metro Toolbox and Initialize the EMME Project
:: The user needs to specify the following paths -
::		PYTHON_PATH - the path to the python directory inside the EMME installation
::		PROJECT_PATH - the path to the current model directory
::~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SET PYTHON_PATH="C:\Program Files\INRO\Emme\Emme 4\Emme-4.4.2\Python27"
SET PROJECT_PATH="E:\projects\clients\mtc\Tasks\TO13_emme_network"

%PYTHON_PATH%\python %PROJECT_PATH%\create_emme_network.py -r %PROJECT_PATH% -t "MTC_Emme"

PAUSE
