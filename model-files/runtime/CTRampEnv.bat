:: This file sets up environment variables for CT-RAMP batch files
::
::   JAVA_PATH: location of the 64-bit java development kit or runtime environment
::    TPP_PATH: location of the RUNTPP and VOYAGER executables from Citilabs
::   CUBE_PATH: location of the Cube executable from Citilabs
:: PYTHON_PATH: location of the Python executable
::     RUNTIME: location of the main JAR file

IF %ENVTYPE%==RSG (
  set "JAVA_PATH=C:\Program Files\Java\jre1.8.0_131"
  set "TPP_PATH=C:\Program Files\Citilabs\CubeVoyager"
  set "CUBE_PATH=C:\Program Files (x86)\Citilabs\Cube"
  set "CUBE_DLL_PATH=C:\Program Files\Citilabs\VoyagerFileAPI"
  set "PYTHON_PATH=C:\Program Files\anaconda2"
)
IF %ENVTYPE%==MTC (
  set "JAVA_PATH=C:\Program Files\Java\jdk1.8.0_181"
  set "TPP_PATH=C:\Program Files\Citilabs\CubeVoyager;C:\Program Files (x86)\Citilabs\CubeVoyager"
  set "CUBE_PATH=C:\Program Files (x86)\Citilabs\Cube"
  set "CUBE_DLL_PATH=C:\Program Files\Citilabs\VoyagerFileAPI"
  set "PYTHON_PATH=C:\Python27"
)

set RUNTIME=CTRAMP/runtime

rem set ports
set JAVA_32_PORT=1190
set MATRIX_MANAGER_PORT=1191
set HH_MANAGER_PORT=1129

rem set machine names
SET MAIN=model2-b
SET MTC02=model2-b

SET node_runner_MTC02=runMtc02
rem set IP addresses
:: get the ipaddress of this machine
FOR /F "TOKENS=1* DELIMS= " %%A IN ('IPCONFIG') DO (
  IF "%%A"=="IPv4" SET IP=%%B
)
FOR %%A IN (%IP%) DO SET IPADDRESS=%%A

::  Set the IP address of the host machine which sends tasks to the client machines 
::set HOST_IP_ADDRESS=10.70.192.64
SET HOST_IP_ADDRESS=%IPADDRESS%

set HHMGR_IP=192.168.1.206

:: Machine running matrix data manager. Set to localhost if running on this machine.
SET MATRIX_SERVER=localhost
SET MATRIX_SERVER_BASE_DIR=\\model2-a\Model2a-Share\Projects_TM2\%SCEN%
SET MATRIX_SERVER_ABSOLUTE_BASE_DIR=X:\Projects_TM2\%SCEN%
SET MATRIX_SERVER_JAVA_PATH=%JAVA_PATH%

:: Machine running household data manager. Set to localhost if running on this machine.
SET HH_SERVER=localhost
SET HH_SERVER_BASE_DIR=\\model2-a\Model2a-Share\Projects_TM2\%SCEN%
SET HH_SERVER_ABSOLUTE_BASE_DIR=X:\Projects_TM2\%SCEN%
SET HH_SERVER_JAVA_PATH=%JAVA_PATH%

rem set main property file name
set PROPERTIES_NAME=sandag_abm

rem all nodes need to map the scenario drive, currently mapped as Q:
set MAPDRIVE=X:
rem uncomment next line if use T drive as data folder.  
rem !!!Note: much slower than a local data folder!!!
set MAPDRIVEFOLDER=\\%MAIN%\projects_tm2\%SCEN%

rem location of mapThenRun.bat on remote machines
set MAPANDRUN=CTRAMP\runtime\mapThenRunNew.bat

rem account settings for remote access using psexec
SET USERNAME=redacted
SET PASSWORD=redacted
