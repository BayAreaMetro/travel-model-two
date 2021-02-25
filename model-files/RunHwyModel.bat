@echo on

:: set RUNTYPE=LOCAL to run everything on this machine
:: set RUNTYPE=DISTRIBUTED to farm out work to other nodes
set RUNTYPE=LOCAL

::~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:: RunHwyModel.bat (adjusted from RunModel.bat)
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

:: Set the inner transit capacity restraint iterations
SET /A MAX_INNER_ITERATION=1

::  Set choice model household sample rate
SET SAMPLERATE_ITERATION1=0.25
SET SAMPLERATE_ITERATION2=0.5
SET SAMPLERATE_ITERATION3=1.0
SET SAMPLERATE_ITERATION4=1.0
SET SAMPLERATE_ITERATION5=1.0

:: Set the model run year
SET MODEL_YEAR=2015
SET AV_SCENARIO=0

:: Scripts base directory
SET BASE_SCRIPTS=CTRAMP\scripts

:: Add these variables to the PATH environment variable, moving the current path to the back of the list
set PATH=%CD%\CTRAMP\runtime;C:\Windows\System32;%JAVA_PATH%\bin;%TPP_PATH%;%CUBE_PATH%;%CUBE_DLL_PATH%;%PYTHON_PATH%

:: --------- restart block ------------------------------------------------------------------------------
:: Use these only if restarting
:: SET /A ITERATION=3
:: SET /A INNER_ITERATION=1
:: IF %ITERATION% EQU 3 SET SAMPLERATE=%SAMPLERATE_ITERATION3%
:: call zoneSystem.bat
::goto starthere
:: ------------------------------------------------------------------------------------------------------


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
copy INPUT\hwy\                 hwy\       /Y
copy INPUT\trn\                 trn\       /Y
copy INPUT\landuse\             landuse\   /Y
copy INPUT\popsyn\              popsyn\    /Y
copy INPUT\nonres\              nonres\    /Y
copy INPUT\warmstart\main\      main\      /Y
copy INPUT\warmstart\nonres\    nonres\    /Y

:: Create necessary directory structure for hh and matrix
SET HH_DEPENDENCIES=(hwy popsyn landuse skims trn CTRAMP logs)
IF NOT %HH_SERVER%==localhost (
  IF NOT EXIST "%HH_SERVER_BASE_DIR%" MKDIR "%HH_SERVER_BASE_DIR%"
  FOR %%A IN %HH_DEPENDENCIES% DO (
    IF NOT EXIST "%HH_SERVER_BASE_DIR%\%%A" MKDIR "%HH_SERVER_BASE_DIR%\%%A"
  )
  ROBOCOPY CTRAMP %HH_SERVER_BASE_DIR%\CTRAMP *.* /E /NDL /NFL
)

:: Create necessary directory structure for matrix data server
SET MATRIX_DEPENDENCIES=(skims CTRAMP logs ctramp_output)
if NOT %MATRIX_SERVER%==localhost (
  IF NOT EXIST "%MATRIX_SERVER_BASE_DIR%" MKDIR "%MATRIX_SERVER_BASE_DIR%"
  FOR %%A IN %MATRIX_DEPENDENCIES% DO (
      IF NOT EXIST "%MATRIX_SERVER_BASE_DIR%\%%A" MKDIR "%MATRIX_SERVER_BASE_DIR%\%%A"
  )
  ROBOCOPY CTRAMP "%MATRIX_SERVER_BASE_DIR%\CTRAMP" *.* /E /NDL /NFL
)

:: ------------------------------------------------------------------------------------------------------
::
:: Step 3:  Pre-process steps
::
:: ------------------------------------------------------------------------------------------------------

: Pre-Process

:: preprocess input network to 
:: 1 - fix space issue in CNTYPE
:: 2 - add a FEET field based on DISTANCE
runtpp %BASE_SCRIPTS%\preprocess\preprocess_input_net.job
IF ERRORLEVEL 2 goto done

:: Write a batch file with number of zones, taps, mazs
runtpp %BASE_SCRIPTS%\preprocess\writeZoneSystems.job
if ERRORLEVEL 2 goto done

::Run the batch file
call zoneSystem.bat

:: Build sequential numberings
runtpp %BASE_SCRIPTS%\preprocess\zone_seq_net_builder.job

:: Create all necessary input files based on updated sequential zone numbering
"%PYTHON_PATH%\python" %BASE_SCRIPTS%\preprocess\zone_seq_disseminator.py .
IF ERRORLEVEL 1 goto done

:: Renumber the TAZ/MAZ in the households file
"%PYTHON_PATH%\python" %BASE_SCRIPTS%\preprocess\renumber.py popsyn\households.csv popsyn\households_renum.csv --input_col MAZ TAZ --renum_join_col N N --renum_out_col MAZSEQ TAZSEQ --output_rename_col ORIG_MAZ ORIG_TAZ --output_new_col MAZ TAZ
IF ERRORLEVEL 1 goto done
move popsyn\households.csv       popsyn\households_original.csv
move popsyn\households_renum.csv popsyn\households.csv

IF %SELECT_COUNTY% GTR 0 (

  :: Collapse the mazs outside select county
  runtpp %BASE_SCRIPTS%\preprocess\CreateCollapsedNetwork.job
  if ERRORLEVEL 2 goto done
  
  :: RERUN: Write a batch file with number of zones, taps, mazs
  runtpp %BASE_SCRIPTS%\preprocess\writeZoneSystems.job
  if ERRORLEVEL 2 goto done
  
  ::RERUN: Run the batch file
  call zoneSystem.bat
  
  :: Collapse the MAZ data (except county 9 which is Marin)
  "%PYTHON_PATH%"\python.exe %BASE_SCRIPTS%\preprocess\CollapseMAZ.PY landuse\maz_data.csv %SELECT_COUNTY%
  if ERRORLEVEL 2 goto done
  
  :: Renumber the household file MAZs
  "%PYTHON_PATH%"\python.exe %BASE_SCRIPTS%\preprocess\RenumberHHFileMAZs.PY popsyn\households.csv landuse\maz_data.csv %SELECT_COUNTY%

  :: Sample households according to sample rates by TAZ
  "%PYTHON_PATH%"\python.exe %BASE_SCRIPTS%\preprocess\popsampler.PY landuse\sampleRateByTAZ.csv popsyn\households.csv popsyn\persons.csv
  
  :: RERUN: Build sequential numberings
runtpp %BASE_SCRIPTS%\preprocess\zone_seq_net_builder.job
  if ERRORLEVEL 2 goto done
  
  ::RERUN: Create all necessary input files based on updated sequential zone numbering
  "%PYTHON_PATH%\python" %BASE_SCRIPTS%\preprocess\zone_seq_disseminator.py .
  IF ERRORLEVEL 1 goto done

)
rem goto done
:: RERUN: Renumber the TAZ/MAZ in the households file
:: "%PYTHON_PATH%\python" %BASE_SCRIPTS%\preprocess\renumber.py popsyn\households.csv popsyn\households_renum.csv --input_col MAZ TAZ --renum_join_col N N --renum_out_col MAZSEQ TAZSEQ --output_rename_col ORIG_MAZ ORIG_TAZ --output_new_col MAZ TAZ
::  IF ERRORLEVEL 1 goto done
::  move popsyn\households.csv       popsyn\households_original_2.csv
::  move popsyn\households_renum.csv popsyn\households.csv

:: Write out the intersection and maz XYs
runtpp %BASE_SCRIPTS%\preprocess\maz_densities.job
if ERRORLEVEL 2 goto done

:: Calculate density fields and append to MAZ file
"%PYTHON_PATH%"\python.exe %BASE_SCRIPTS%\preprocess\createMazDensityFile.py 
IF ERRORLEVEL 1 goto done

:: Build sequential numberings
runtpp %BASE_SCRIPTS%\preprocess\zone_seq_net_builder.job
if ERRORLEVEL 2 goto done

:: Translate the roadway network into a non-motorized network
runtpp %BASE_SCRIPTS%\preprocess\CreateNonMotorizedNetwork.job
if ERRORLEVEL 2 goto done

:: Create the tap data
runtpp %BASE_SCRIPTS%\preprocess\tap_to_taz_for_parking.job
if ERRORLEVEL 2 goto done

"%PYTHON_PATH%\python.exe" %BASE_SCRIPTS%\preprocess\tap_data_builder.py .
IF ERRORLEVEL 1 goto done

:: Set the prices in the roadway network (convert csv to dbf first)
"%PYTHON_PATH%\python" %BASE_SCRIPTS%\preprocess\csvToDbf.py hwy\tolls.csv hwy\tolls.dbf
IF ERRORLEVEL 1 goto done

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

echo COMPLETED PREPROCESS  %DATE% %TIME% >> logs\feedback.rpt 

:: ------------------------------------------------------------------------------------------------------
::
:: Step 4:  Build non-motorized level-of-service matrices
::
:: ------------------------------------------------------------------------------------------------------

:: Non-Motorized Skims

:nonmot

:: Build the skim tables
runtpp %BASE_SCRIPTS%\skims\NonMotorizedSkims.job
if ERRORLEVEL 2 goto done

:::: Build the maz-maz skims
runtpp %BASE_SCRIPTS%\skims\MazMazSkims.job
if ERRORLEVEL 2 goto done

echo COMPLETED NON-MOTORIZED-SKIMS  %DATE% %TIME% >> logs\feedback.rpt 

:: ------------------------------------------------------------------------------------------------------
::
:: Step 5:  Build the airport trip matrices (these are independent of level-of-service)
::
:: ------------------------------------------------------------------------------------------------------
:: Run the airport model
runtpp %BASE_SCRIPTS%\nonres\BuildAirPax.job
if ERRORLEVEL 2 goto done

:itercnt

:: ------------------------------------------------------------------------------------------------------
::
:: Step 6:  Build the highway skims
::
:: ------------------------------------------------------------------------------------------------------

:: Build the initial highway skims
runtpp %BASE_SCRIPTS%\skims\HwySkims.job
if ERRORLEVEL 2 goto done

::Step X: Main model iteration setup
SET /A ITERATION=2
:iteration_start
SET /A ITERATION+=1
IF %ITERATION% EQU 1 SET SAMPLERATE=%SAMPLERATE_ITERATION1%
IF %ITERATION% EQU 2 SET SAMPLERATE=%SAMPLERATE_ITERATION2%
IF %ITERATION% EQU 3 SET SAMPLERATE=%SAMPLERATE_ITERATION3%
IF %ITERATION% EQU 4 SET SAMPLERATE=%SAMPLERATE_ITERATION4%
IF %ITERATION% EQU 5 SET SAMPLERATE=%SAMPLERATE_ITERATION5%
ECHO ****MODEL ITERATION %ITERATION% (SAMPLE RATE %SAMPLERATE%)****

:: Copy skims and other related files to remote machine
IF NOT %RUNTYPE%==LOCAL (
  ROBOCOPY skims "%HH_SERVER_BASE_DIR%\skims" *.tpp drive_maz_taz_tap.csv /NDL /NFL
  ROBOCOPY trn   "%HH_SERVER_BASE_DIR%\trn"    tapLines.csv               /NDL /NFL
)

:: ------------------------------------------------------------------------------------------------------
::
:: Step 7:  Execute the choice models using CT-RAMP java code
::
:: ------------------------------------------------------------------------------------------------------

:core

:: copy results back over here
ROBOCOPY "%MATRIX_SERVER_BASE_DIR%\ctramp_output" ctramp_output *.mat /NDL /NFL


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
:starthere
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

:mazasgn
runtpp CTRAMP\scripts\assign\build_and_assign_maz_to_maz_auto.job
if ERRORLEVEL 2 goto done

:tazasgn
runtpp CTRAMP\scripts\assign\HwyAssign.job
if ERRORLEVEL 2 goto done

runtpp CTRAMP\scripts\assign\AverageNetworkVolumes.job
if ERRORLEVEL 2 goto done

runtpp CTRAMP\scripts\assign\CalculateAverageSpeed.job
if ERRORLEVEL 2 goto done

runtpp CTRAMP\scripts\assign\MergeNetworks.job
if ERRORLEVEL 2 goto done

:: If another iteration is to be run, run hwy skims
IF %ITERATION% LSS %MAX_ITERATION% (

  runtpp %BASE_SCRIPTS%\skims\HwySkims.job
  if ERRORLEVEL 2 goto done
  
)

:here

IF %ITERATION% LSS %MAX_ITERATION% GOTO iteration_start

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

ECHO FINISHED.  
@pause