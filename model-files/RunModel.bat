rem @ECHO OFF
::~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:: RunModel.bat
::
:: MS-DOS batch file to execute the MTC travel model.  Each of the model steps are sequentially
:: called here.  
::
:: Travel Model Two
:: dto (2012 02 15) gde (2009 04 22) crf (2013 09) bts (2013 09 24) rpm (2016 06 22) jef (2017 10 26)
:: 
:: RunModel.bat > model_run_out.txt 2>&1
::~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:: ------------------------------------------------------------------------------------------------------
::
:: Step 1:  Set the necessary path and other computer/environment-specific variables
::
:: ------------------------------------------------------------------------------------------------------

:: Scenario name - the directory that this file is in
SET D=%~p0
IF %D:~-1% EQU \ SET D=%D:~0,-1%
FOR %%a IN ("%D%") DO SET SCEN=%%~nxa
ECHO ***SCENARIO: %SCEN%***

SET /A SELECT_COUNTY=-1

:: Set up environment variables
CALL CTRAMP\runtime\CTRampEnv.bat

:: Set the model feedback iterations
SET /A MAX_ITERATION=3

::  Set choice model household sample rate
SET SAMPLERATE_ITERATION1=1.0
SET SAMPLERATE_ITERATION2=0.50
SET SAMPLERATE_ITERATION3=1.0
SET SAMPLERATE_ITERATION4=1.0
SET SAMPLERATE_ITERATION5=1.0

:: Set the model run year
SET MODEL_YEAR=2015

:: Scripts base directory
SET BASE_SCRIPTS=CTRAMP\scripts

:: Add these variables to the PATH environment variable, moving the current path to the back of the list
SET OLD_PATH=%PATH%
SET PATH=%RUNTIME%;%JAVA_PATH%/bin;%TPP_PATH%;%PYTHON_PATH%;%OLD_PATH%

:: Remove these properties if starting from scratch
:: SET /A ITERATION=1
:: IF %ITERATION% EQU 1 SET SAMPLERATE=%SAMPLERATE_ITERATION1%
:: call zoneSystem.bat

:: goto here

:: ------------------------------------------------------------------------------------------------------
::
:: Step 2:  Create the directory structure
::
:: ------------------------------------------------------------------------------------------------------

:: Create the working directories
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
copy INPUT\hwy\                 hwy\   /Y
copy INPUT\trn\                 trn\   /Y
copy INPUT\trn\transit_lines\   trn\   /Y
copy INPUT\trn\transit_fares\   trn\   /Y
copy INPUT\trn\transit_support\ trn\   /Y
copy INPUT\landuse\             landuse\   /Y
copy INPUT\popsyn\              popsyn\    /Y
copy INPUT\nonres\              nonres\    /Y
copy INPUT\warmstart\main\      main\      /Y
copy INPUT\warmstart\nonres\    nonres\    /Y

:: Create necessary directory structure for hh and matrix data servers
:: and copy dependencies
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

:: ------------------------------------------------------------------------------------------------------
::
:: Step 3:  Pre-process steps
::
:: ------------------------------------------------------------------------------------------------------

: Pre-Process

IF %SELECT_COUNTY% GTR 0 (
  :: Collapse the mazs outside select county
  runtpp %BASE_SCRIPTS%\preprocess\CreateCollapsedNetwork.job
  if ERRORLEVEL 2 goto done
)

:: Write a batch file with number of zones, taps, mazs
runtpp %BASE_SCRIPTS%\preprocess\writeZoneSystems.job
if ERRORLEVEL 2 goto done

::Run the batch file
call zoneSystem.bat

IF %SELECT_COUNTY% GTR 0 (
  ::Collapse the MAZ data (except county 9 which is Marin)
  "%PYTHON_PATH%"\python.exe %BASE_SCRIPTS%\preprocess\CollapseMAZ.PY landuse\maz_data.csv %SELECT_COUNTY%
)

:: Build sequential numberings
runtpp %BASE_SCRIPTS%\preprocess\zone_seq_net_builder.job
if ERRORLEVEL 2 goto done

:: Create all necessary input files based on updated sequential zone numbering
"%PYTHON_PATH%\python" %BASE_SCRIPTS%\preprocess\zone_seq_disseminator.py .
IF ERRORLEVEL 1 goto done

IF %SELECT_COUNTY% GTR 0 (
  :: Renumber the household file MAZs
  "%PYTHON_PATH%"\python.exe %BASE_SCRIPTS%\preprocess\RenumberHHFileMAZs.PY popsyn\households.csv landuse\maz_data.csv %SELECT_COUNTY%

  :: Sample households according to sample rates by TAZ
  "%PYTHON_PATH%"\python.exe %BASE_SCRIPTS%\preprocess\popsampler.PY landuse\sampleRateByTAZ.csv popsyn\households.csv popsyn\persons.csv
)


:: Write out the intersection and maz XYs
runtpp %BASE_SCRIPTS%\preprocess\maz_densities.job
if ERRORLEVEL 2 goto done

:: Calculate density fields and append to MAZ file
"%PYTHON_PATH%"\python.exe %BASE_SCRIPTS%\preprocess\createMazDensityFile.py 


:: Translate the roadway network into a non-motorized network
runtpp %BASE_SCRIPTS%\preprocess\CreateNonMotorizedNetwork.job
if ERRORLEVEL 2 goto done

:: Create the tap data
runtpp %BASE_SCRIPTS%\preprocess\tap_to_taz_for_parking.job
if ERRORLEVEL 2 goto done

:: Set the prices in the roadway network
runtpp %BASE_SCRIPTS%\preprocess\SetTolls.job
if ERRORLEVEL 2 goto done

:: Set a penalty to dummy links connecting HOV/HOT lanes and general purpose lanes
runtpp %BASE_SCRIPTS%\preprocess\SetHovXferPenalties.job
if ERRORLEVEL 2 goto done

:: Create areatype and capclass fields in network
runtpp %BASE_SCRIPTS%\preprocess\SetCapClass.job
if ERRORLEVEL 2 goto done

:: Create time-of-day-specific 
runtpp %BASE_SCRIPTS%\preprocess\CreateFiveHighwayNetworks.job
if ERRORLEVEL 2 goto done

:: Create taz networks
runtpp %BASE_SCRIPTS%\preprocess\BuildTazNetworks.job
if ERRORLEVEL 2 goto done

:: ------------------------------------------------------------------------------------------------------
::
:: Step 4:  Build non-motorized level-of-service matrices
::
:: ------------------------------------------------------------------------------------------------------

:: Non-Motorized Skims

:: Build the skim tables
runtpp %BASE_SCRIPTS%\skims\NonMotorizedSkims.job
if ERRORLEVEL 2 goto done

:::: Build the maz-maz skims
runtpp %BASE_SCRIPTS%\skims\MazMazSkims.job
if ERRORLEVEL 2 goto done


:: ------------------------------------------------------------------------------------------------------
::
:: Step 5:  Build the airport trip matrices (these are independent of level-of-service)
::
:: ------------------------------------------------------------------------------------------------------
:: Run the airport model
runtpp %BASE_SCRIPTS%\nonres\BuildAirPax.job
if ERRORLEVEL 2 goto done


:: Copy dependencies for HH data manager
ROBOCOPY hwy %HH_SERVER_BASE_DIR%\hwy *.csv /NDL /NFL
ROBOCOPY popsyn %HH_SERVER_BASE_DIR%\popsyn *.* /NDL /NFL
ROBOCOPY landuse %HH_SERVER_BASE_DIR%\landuse *.csv /NDL /NFL
ROBOCOPY skims %HH_SERVER_BASE_DIR%\skims *.csv *.txt /NDL /NFL
ROBOCOPY trn %HH_SERVER_BASE_DIR%\trn tapLines.csv /NDL /NFL

:itercnt



::Step X: Main model iteration setup
SET /A ITERATION=0
:iteration_start
SET /A ITERATION+=1
IF %ITERATION% EQU 1 SET SAMPLERATE=%SAMPLERATE_ITERATION1%
IF %ITERATION% EQU 2 SET SAMPLERATE=%SAMPLERATE_ITERATION2%
IF %ITERATION% EQU 3 SET SAMPLERATE=%SAMPLERATE_ITERATION3%
IF %ITERATION% EQU 4 SET SAMPLERATE=%SAMPLERATE_ITERATION4%
IF %ITERATION% EQU 5 SET SAMPLERATE=%SAMPLERATE_ITERATION5%
ECHO ****MODEL ITERATION %ITERATION% (SAMPLE RATE %SAMPLERATE%)****

:: ------------------------------------------------------------------------------------------------------
::
:: Step 6:  Build the highway and transit skims
::
:: ------------------------------------------------------------------------------------------------------


:: Build the highway and transit skims
runtpp %BASE_SCRIPTS%\skims\HwySkims.job
if ERRORLEVEL 2 goto done

runtpp %BASE_SCRIPTS%\skims\BuildTransitNetworks.job
if ERRORLEVEL 2 goto done

runtpp %BASE_SCRIPTS%\skims\TransitSkims.job
if ERRORLEVEL 2 goto done

runtpp %BASE_SCRIPTS%\skims\SkimSetsAdjustment.job
if ERRORLEVEL 2 goto done

:: Copy skims and other related files to remote machine
ROBOCOPY skims %HH_SERVER_BASE_DIR%\skims *.tpp drive_maz_taz_tap.csv /NDL /NFL
ROBOCOPY trn %HH_SERVER_BASE_DIR%\trn tapLines.csv /NDL /NFL

:: ------------------------------------------------------------------------------------------------------
::
:: Step 7:  Execute the choice models using CT-RAMP java code
::
:: ------------------------------------------------------------------------------------------------------

:core

::  Run CT-RAMP

::  Start remote worker node(s) - only if running in distributed mode
::CTRAMP\runtime\config\pskill \\w-ampdx-d-sag01 -u %UN% -p %PWD% java
::CTRAMP\runtime\config\psexec \\w-ampdx-d-sag01 C:\abmTools\mapThenRun.bat M: \\w-ampdx-d-sag04\projects\mtc\%SCEN% %PWD% %UN% CTRAMP\runtime runNode0.cmd -u %UN% -p %PWD% -d

:: Start remote servers
::remote servers locally
::start CTRAMP\runtime\runHhMgr.cmd "%JAVA_PATH%" %HOST_IP_ADDRESS%
::start CTRAMP\runtime\runMtxMgr.cmd %HOST_IP_ADDRESS% "%JAVA_PATH%"

::remote servers with username/password
::CTRAMP\runtime\config\pskill %HH_SERVER% -u %UN% -p %PWD% java
::CTRAMP\runtime\config\pskill %MATRIX_SERVER% -u %UN% -p %PWD% java
::CTRAMP\runtime\config\psexec %HH_SERVER% -u %UN% -p %PWD% -d %HH_SERVER_ABSOLUTE_BASE_DIR%\CTRAMP\runtime\runHhMgr.cmd "%HH_SERVER_JAVA_PATH%" %HOST_IP_ADDRESS%
::CTRAMP\runtime\config\psexec %MATRIX_SERVER% -u %UN% -p %PWD% -d %MATRIX_SERVER_ABSOLUTE_BASE_DIR%\CTRAMP\runtime\runMtxMgr.cmd %HOST_IP_ADDRESS% "%MATRIX_SERVER_JAVA_PATH%" 

::remote servers using current user (wait 10 seconds between each call because otherwise psXXX sometimes bashes on its own authentication/permissions)
rem CTRAMP\runtime\config\pskill %HH_SERVER% java\
rem ping -n 10 localhost
rem CTRAMP\runtime\config\pskill %MATRIX_SERVER% java
rem ping -n 10 localhost
CTRAMP\runtime\config\psexec %HH_SERVER% -d %HH_SERVER_ABSOLUTE_BASE_DIR%\CTRAMP\runtime\runHhMgr.cmd "%HH_SERVER_JAVA_PATH%" %HOST_IP_ADDRESS%
ping -n 10 localhost
rem CTRAMP\runtime\config\psexec %MATRIX_SERVER% -d %MATRIX_SERVER_ABSOLUTE_BASE_DIR%\CTRAMP\runtime\runMtxMgr.cmd %HOST_IP_ADDRESS% "%MATRIX_SERVER_JAVA_PATH%" 
rem ping -n 10 localhost


start CTRAMP\runtime\runDriver.cmd
start CTRAMP\runtime\runNode0.cmd

copy CTRAMP\runtime\mtctm2.properties mtctm2.properties    /Y
call CTRAMP\runtime\runMTCTM2ABM.cmd %SAMPLERATE% %ITERATION% "%JAVA_PATH%"
if ERRORLEVEL 2 goto done
del mtctm2.properties
rem taskkill /im "java.exe" /F



::Kill remote servers
::CTRAMP\runtime\config\pskill %HH_SERVER% -u %UN% -p %PWD% java
::CTRAMP\runtime\config\pskill %MATRIX_SERVER% -u %UN% -p %PWD% java
::CTRAMP\runtime\config\pskill %HH_SERVER% java
::ping -n 10 localhost
::CTRAMP\runtime\config\pskill %MATRIX_SERVER% java
::ping -n 10 localhost

:: copy results back over here
ROBOCOPY %MATRIX_SERVER_BASE_DIR%\ctramp_output ctramp_output *.mat /NDL /NFL

runtpp CTRAMP\scripts\assign\merge_demand_matrices.s
if ERRORLEVEL 2 goto done

:: ------------------------------------------------------------------------------------------------------
::
:: Step 8:  Execute the internal/external, and commercial vehicle models
::
:: -----------------------------------------------------------------------------------------------------

:nonres

:: Build the internal/external demand matrices forecast
runtpp CTRAMP\scripts\nonres\IxForecasts.job
if ERRORLEVEL 2 goto done

:: Apply diurnal factors to the fixed internal/external demand matrices
runtpp CTRAMP\scripts\nonres\IxTimeOfDay.job
if ERRORLEVEL 2 goto done

:: Apply a value toll choice model for the internal/external demand
runtpp CTRAMP\scripts\nonres\IxTollChoice.job
if ERRORLEVEL 2 goto done

:: Apply the commercial vehicle generation models
runtpp CTRAMP\scripts\nonres\TruckTripGeneration.job
if ERRORLEVEL 2 goto done

:: Apply the commercial vehicle distribution models
runtpp CTRAMP\scripts\nonres\TruckTripDistribution.job
if ERRORLEVEL 2 goto done

:: Apply the commercial vehicle diurnal factors
runtpp CTRAMP\scripts\nonres\TruckTimeOfDay.job
if ERRORLEVEL 2 goto done

:: Apply a value toll choice model for eligible commercial demand
runtpp CTRAMP\scripts\nonres\TruckTollChoice.job
if ERRORLEVEL 2 goto done

:hwyasgn

:: ------------------------------------------------------------------------------------------------------
::
:: Step 9:  Assignment
::
:: ------------------------------------------------------------------------------------------------------
:: Highway assignment
runtpp CTRAMP\scripts\assign\build_and_assign_maz_to_maz_auto.job
if ERRORLEVEL 2 goto done

runtpp CTRAMP\scripts\assign\HwyAssign.job
if ERRORLEVEL 2 goto done

runtpp CTRAMP\scripts\assign\AverageNetworkVolumes.job
if ERRORLEVEL 2 goto done

runtpp CTRAMP\scripts\assign\CalculateAverageSpeed.job
if ERRORLEVEL 2 goto done

runtpp CTRAMP\scripts\assign\MergeNetworks.job
if ERRORLEVEL 2 goto done

IF %ITERATION% LSS %MAX_ITERATION% GOTO iteration_start

runtpp CTRAMP\scripts\assign\TransitAssign.job
if ERRORLEVEL 2 goto done


:: ------------------------------------------------------------------------------------------------------
::
:: Step 10:  Cleanup
::
:: ------------------------------------------------------------------------------------------------------

:: Move all the TP+ printouts to the \logs folder
copy *.prn logs\*.prn

:: Delete all the temporary TP+ printouts and cluster files
del *.prn
del *.s
del *.job
del *.prj
del *.var
:: ------------------------------------------------------------------------------------------------------
::
:: Done
::
:: ------------------------------------------------------------------------------------------------------


:: Success target and message
:success
ECHO FINISHED SUCCESSFULLY!

:: Complete target and message
:done

:: Put the PATH back the way you found it
set PATH=%OLD_PATH%

ECHO FINISHED.  
