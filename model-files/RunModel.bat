@echo on

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

:: Step 0: Copy over CTRAMP from %GITHUB_DIR%, which should be set prior to this (e.g. in SetUpModel.bat)
 if not exist CTRAMP (
  mkdir CTRAMP\model
  mkdir CTRAMP\runtime
  mkdir CTRAMP\scripts
  c:\windows\system32\Robocopy.exe /E "%GITHUB_DIR%\model-files\model"       CTRAMP\model
  c:\windows\system32\Robocopy.exe /E "%GITHUB_DIR%\model-files\runtime"     CTRAMP\runtime
  c:\windows\system32\Robocopy.exe /E "%GITHUB_DIR%\model-files\scripts"     CTRAMP\scripts
)
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
REM SET SAMPLERATE_ITERATION1=0.005
SET SAMPLERATE_ITERATION1=0.2
SET SAMPLERATE_ITERATION2=0.3
SET SAMPLERATE_ITERATION3=0.5
SET SAMPLERATE_ITERATION4=0.2
SET SAMPLERATE_ITERATION5=0.005

:: Set the model run year
SET MODEL_YEAR=2015
SET AV_SCENARIO=0

:: Scripts base directory
SET BASE_SCRIPTS=CTRAMP\scripts

:: expect conda to be in PATH
CALL conda activate %TM2_PYTHON_CONDA_ENV%
IF ERRORLEVEL 2 goto done

:: --------- restart block ------------------------------------------------------------------------------
:: Use these only if restarting
SET /A ITERATION=4
SET /A INNER_ITERATION=1
IF %ITERATION% EQU 1 SET SAMPLERATE=%SAMPLERATE_ITERATION1%
IF %ITERATION% EQU 2 SET SAMPLERATE=%SAMPLERATE_ITERATION2%
IF %ITERATION% EQU 3 SET SAMPLERATE=%SAMPLERATE_ITERATION3%
IF %ITERATION% EQU 4 SET SAMPLERATE=%SAMPLERATE_ITERATION4%
IF %ITERATION% EQU 5 SET SAMPLERATE=%SAMPLERATE_ITERATION5%
REM call zoneSystem.bat
REM goto core
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
"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\preprocess\preprocess_input_net.job
IF ERRORLEVEL 2 goto done

:: Write a batch file with number of zones, taps, mazs
"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\preprocess\writeZoneSystems.job
if ERRORLEVEL 2 goto done

::Run the batch file
call zoneSystem.bat

:: Build sequential numberings
"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\preprocess\zone_seq_net_builder.job

:: Create all necessary input files based on updated sequential zone numbering
:zones
python %BASE_SCRIPTS%\preprocess\zone_seq_disseminator.py .
IF ERRORLEVEL 1 goto done

:: Renumber the TAZ/MAZ in the households file
:hhrenum
python %BASE_SCRIPTS%\preprocess\renumber.py popsyn\households.csv popsyn\households_renum.csv --input_col MAZ TAZ --renum_join_col N N --renum_out_col MAZSEQ TAZSEQ --output_rename_col ORIG_MAZ ORIG_TAZ --output_new_col MAZ TAZ
IF ERRORLEVEL 1 goto done
move popsyn\households.csv       popsyn\households_original.csv
move popsyn\households_renum.csv popsyn\households.csv


IF %SELECT_COUNTY% GTR 0 (

  :: Collapse the mazs outside select county
  "%TPP_PATH%\runtpp" %BASE_SCRIPTS%\preprocess\CreateCollapsedNetwork.job
  if ERRORLEVEL 2 goto done

  :: RERUN: Write a batch file with number of zones, taps, mazs
  "%TPP_PATH%\runtpp" %BASE_SCRIPTS%\preprocess\writeZoneSystems.job
  if ERRORLEVEL 2 goto done

  ::RERUN: Run the batch file
  call zoneSystem.bat

  :: Collapse the MAZ data (except county 9 which is Marin)
  python %BASE_SCRIPTS%\preprocess\CollapseMAZ.PY landuse\maz_data.csv %SELECT_COUNTY%
  if ERRORLEVEL 2 goto done

  :: Renumber the household file MAZs
  python %BASE_SCRIPTS%\preprocess\RenumberHHFileMAZs.PY popsyn\households.csv landuse\maz_data.csv %SELECT_COUNTY%

  :: Sample households according to sample rates by TAZ
  python %BASE_SCRIPTS%\preprocess\popsampler.PY landuse\sampleRateByTAZ.csv popsyn\households.csv popsyn\persons.csv

  :: RERUN: Build sequential numberings
  "%TPP_PATH%\runtpp" %BASE_SCRIPTS%\preprocess\zone_seq_net_builder.job
  if ERRORLEVEL 2 goto done

  ::RERUN: Create all necessary input files based on updated sequential zone numbering
  python %BASE_SCRIPTS%\preprocess\zone_seq_disseminator.py .
  IF ERRORLEVEL 1 goto done

)

:: RERUN: Renumber the TAZ/MAZ in the households file
:: python %BASE_SCRIPTS%\preprocess\renumber.py popsyn\households.csv popsyn\households_renum.csv --input_col MAZ TAZ --renum_join_col N N --renum_out_col MAZSEQ TAZSEQ --output_rename_col ORIG_MAZ ORIG_TAZ --output_new_col MAZ TAZ
::  IF ERRORLEVEL 1 goto done
::  move popsyn\households.csv       popsyn\households_original_2.csv
::  move popsyn\households_renum.csv popsyn\households.csv

:: Write out the intersection and maz XYs
"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\preprocess\maz_densities.job
if ERRORLEVEL 2 goto done

:: Calculate density fields and append to MAZ file
python %BASE_SCRIPTS%\preprocess\createMazDensityFile.py
IF ERRORLEVEL 1 goto done

:: Build sequential numberings
"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\preprocess\zone_seq_net_builder.job
if ERRORLEVEL 2 goto done

:: Translate the roadway network into a non-motorized network
"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\preprocess\CreateNonMotorizedNetwork.job
if ERRORLEVEL 2 goto done

:: Create the tap data
"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\preprocess\tap_to_taz_for_parking.job
if ERRORLEVEL 2 goto done

python %BASE_SCRIPTS%\preprocess\tap_data_builder.py .
IF ERRORLEVEL 1 goto done

:: Set the prices in the roadway network (convert csv to dbf first)
python %BASE_SCRIPTS%\preprocess\csvToDbf.py hwy\tolls.csv hwy\tolls.dbf
IF ERRORLEVEL 1 goto done

"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\preprocess\SetTolls.job
if ERRORLEVEL 2 goto done

:: Set a penalty to dummy links connecting HOV/HOT lanes and general purpose lanes
"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\preprocess\SetHovXferPenalties.job
if ERRORLEVEL 2 goto done

:capclass
:: Create areatype and capclass fields in network
"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\preprocess\SetCapClass.job
if ERRORLEVEL 2 goto done

"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\preprocess\setInterchangeDistance.job
if ERRORLEVEL 2 goto done

:createfivehwynets
:: Create time-of-day-specific
"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\preprocess\CreateFiveHighwayNetworks.job
if ERRORLEVEL 2 goto done

:: Create taz networks
"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\preprocess\BuildTazNetworks.job
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
"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\skims\NonMotorizedSkims.job
if ERRORLEVEL 2 goto done

:::: Build the maz-maz skims
"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\skims\MazMazSkims.job
if ERRORLEVEL 2 goto done

echo COMPLETED NON-MOTORIZED-SKIMS  %DATE% %TIME% >> logs\feedback.rpt

:: ------------------------------------------------------------------------------------------------------
::
:: Step 5:  Build the airport trip matrices (these are independent of level-of-service)
::
:: ------------------------------------------------------------------------------------------------------
:: Run the airport model
"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\nonres\BuildAirPax.job
if ERRORLEVEL 2 goto done

:itercnt

:: ------------------------------------------------------------------------------------------------------
::
:: Step 6:  Build the highway and transit skims
::
:: ------------------------------------------------------------------------------------------------------

:: Build the initial highway and transit skims
:hwyskims
"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\skims\HwySkims.job
if ERRORLEVEL 2 goto done

:transitnet
"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\skims\BuildTransitNetworks.job
if ERRORLEVEL 2 goto done

:transitskimsprep
"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\skims\TransitSkimsPrep.job
if ERRORLEVEL 2 goto done

:createemmenetwork

:: Create emme project from scratch since it's the first iteration
"%PYTHON_PATH%\python" %BASE_SCRIPTS%\skims\cube_to_emme_network_conversion.py -p "trn" --first_iteration "yes"
IF ERRORLEVEL 1 goto done

"%PYTHON_PATH%\python" %BASE_SCRIPTS%\skims\create_emme_network.py -p "trn" --name "mtc_emme" --first_iteration "yes"
IF ERRORLEVEL 1 goto done

:: Passing the port specified in the Emme Desktop GUI 
:: see Tools > Application Options > Advanced.  
:: At the bottom of the pane, there is text: "Desktop API is listening on port 4242."
"%PYTHON_PATH%\python" %BASE_SCRIPTS%\skims\skim_transit_network.py -p "trn" -s "skims" --iteration 1 --skip_import_demand --port 4242
IF ERRORLEVEL 1 goto done

CALL conda deactivate
CALL conda activate mtc_py2

:afteremmeskims

REM "%TPP_PATH%\runtpp" %BASE_SCRIPTS%\skims\TransitSkims.job
REM if ERRORLEVEL 2 goto done

REM "%TPP_PATH%\runtpp" %BASE_SCRIPTS%\skims\SkimSetsAdjustment.job
REM if ERRORLEVEL 2 goto done

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

::  Run CT-RAMP

:: Start HH Server locally or remotely
IF %RUNTYPE%==LOCAL (
  rem =========== local ========================
  call CTRAMP\runtime\runHhMgr.cmd "%JAVA_PATH%" %HOST_IP_ADDRESS%
  echo Started household manager
  ping -n 10 localhost
) ELSE (
  rem =========== remote ========================
  rem Copy dependencies for HH data manager
  ROBOCOPY hwy     "%HH_SERVER_BASE_DIR%\hwy"     *.csv        /NDL /NFL
  ROBOCOPY popsyn  "%HH_SERVER_BASE_DIR%\popsyn"  *.*          /NDL /NFL
  ROBOCOPY landuse "%HH_SERVER_BASE_DIR%\landuse" *.csv        /NDL /NFL
  ROBOCOPY skims   "%HH_SERVER_BASE_DIR%\skims"   *.csv *.txt  /NDL /NFL
  ROBOCOPY trn     "%HH_SERVER_BASE_DIR%\trn"     tapLines.csv /NDL /NFL

  rem (wait 10 seconds between each call because otherwise psXXX sometimes bashes on its own authentication/permissions)
  CTRAMP\runtime\config\pskill %HH_SERVER% -u %UN% -p %PWD% java
  ping -n 10 localhost
  CTRAMP\runtime\config\psexec %HH_SERVER% -u %UN% -p %PWD% -d "%HH_SERVER_ABSOLUTE_BASE_DIR%\CTRAMP\runtime\runHhMgr.cmd" "%HH_SERVER_JAVA_PATH%"
  ping -n 10 localhost
)

:: Start Matrix Server remotely or locally
IF %RUNTYPE%==LOCAL (
  rem =========== local ========================
  call CTRAMP\runtime\runMtxMgr.cmd %HOST_IP_ADDRESS% "%JAVA_PATH%"
  echo Started matrix manager
  ping -n 10 localhost
) ELSE (
  rem =========== remote ========================
  rem (wait 10 seconds between each call because otherwise psXXX sometimes bashes on its own authentication/permissions)
  CTRAMP\runtime\config\pskill %MATRIX_SERVER% u %UN% -p %PWD% java
  ping -n 10 localhost
  CTRAMP\runtime\config\psexec %MATRIX_SERVER% -u %UN% -p %PWD% -d "%MATRIX_SERVER_ABSOLUTE_BASE_DIR%\CTRAMP\runtime\runMtxMgr.cmd" "%MATRIX_SERVER_JAVA_PATH%"
  ping -n 10 localhost
)

IF %RUNTYPE%==DISTRIBUTED (
  CTRAMP\runtime\runDriver.cmd
  CTRAMP\runtime\runNode0.cmd
)

copy CTRAMP\runtime\mtctm2.properties mtctm2.properties    /Y
call CTRAMP\runtime\runMTCTM2ABM.cmd %SAMPLERATE% %ITERATION% "%JAVA_PATH%"
if ERRORLEVEL 2 goto done
del mtctm2.properties

taskkill /im "java.exe" /F


IF NOT %MATRIX_SERVER%==localhost (
  rem =========== Kill remote matrix server ===========
  CTRAMP\runtime\config\pskill %MATRIX_SERVER% -u %UN% -p %PWD% java
  ping -n 10 localhost
)
IF NOT %HH_SERVER%==localhost (
  rem =========== Kill remote household server ===========
  CTRAMP\runtime\config\pskill %HH_SERVER% -u %UN% -p %PWD% java
  ping -n 10 localhost
)

:: copy results back over here
ROBOCOPY "%MATRIX_SERVER_BASE_DIR%\ctramp_output" ctramp_output *.mat /NDL /NFL
ROBOCOPY "%MATRIX_SERVER_BASE_DIR%\ctramp_output" ctramp_output *.omx /NDL /NFL

:afterrobocopy
"%TPP_PATH%\runtpp" CTRAMP\scripts\assign\merge_auto_matrices.s
REM "%TPP_PATH%\runtpp" CTRAMP\scripts\assign\merge_demand_matrices.s
if ERRORLEVEL 2 goto done

:: ------------------------------------------------------------------------------------------------------
::
:: Step 8:  Execute the internal/external, and commercial vehicle models
::
:: -----------------------------------------------------------------------------------------------------

:nonres

:: Build the internal/external demand matrices forecast
"%TPP_PATH%\runtpp" CTRAMP\scripts\nonres\IxForecasts.job
if ERRORLEVEL 2 goto done

:: Apply diurnal factors to the fixed internal/external demand matrices
"%TPP_PATH%\runtpp" CTRAMP\scripts\nonres\IxTimeOfDay.job
if ERRORLEVEL 2 goto done

:: Apply a value toll choice model for the internal/external demand
"%TPP_PATH%\runtpp" CTRAMP\scripts\nonres\IxTollChoice.job
if ERRORLEVEL 2 goto done

:: Apply the commercial vehicle generation models
"%TPP_PATH%\runtpp" CTRAMP\scripts\nonres\TruckTripGeneration.job
if ERRORLEVEL 2 goto done

:: Apply the commercial vehicle distribution models
"%TPP_PATH%\runtpp" CTRAMP\scripts\nonres\TruckTripDistribution.job
if ERRORLEVEL 2 goto done

:: Apply the commercial vehicle diurnal factors
"%TPP_PATH%\runtpp" CTRAMP\scripts\nonres\TruckTimeOfDay.job
if ERRORLEVEL 2 goto done

:: Apply a value toll choice model for eligible commercial demand
"%TPP_PATH%\runtpp" CTRAMP\scripts\nonres\TruckTollChoice.job
if ERRORLEVEL 2 goto done

:hwyasgn

:: ------------------------------------------------------------------------------------------------------
::
:: Step 9:  Assignment
::
:: ------------------------------------------------------------------------------------------------------

:mazasgn
"%TPP_PATH%\runtpp" CTRAMP\scripts\assign\build_and_assign_maz_to_maz_auto.job
if ERRORLEVEL 2 goto done

:tazasgn
"%TPP_PATH%\runtpp" CTRAMP\scripts\assign\HwyAssign.job
if ERRORLEVEL 2 goto done

"%TPP_PATH%\runtpp" CTRAMP\scripts\assign\AverageNetworkVolumes.job
if ERRORLEVEL 2 goto done

"%TPP_PATH%\runtpp" CTRAMP\scripts\assign\CalculateAverageSpeed.job
if ERRORLEVEL 2 goto done

"%TPP_PATH%\runtpp" CTRAMP\scripts\assign\MergeNetworks.job
if ERRORLEVEL 2 goto done

:: If another iteration is to be run, run hwy skims
IF %ITERATION% LSS %MAX_ITERATION% (
  "%TPP_PATH%\runtpp" %BASE_SCRIPTS%\skims\HwySkims.job
  if ERRORLEVEL 2 goto done
)

"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\skims\BuildTransitNetworks.job
if ERRORLEVEL 2 goto done

"%TPP_PATH%\runtpp" %BASE_SCRIPTS%\skims\TransitSkimsPrep.job
if ERRORLEVEL 2 goto done

:emmeseconditeration
:: changing to python 3 environment for emme
CALL conda deactivate
CALL conda activate mtc
:: Emme project already created, just updating congested link times
python %BASE_SCRIPTS%\skims\cube_to_emme_network_conversion.py -p "trn" --first_iteration "no"
IF ERRORLEVEL 1 goto done

:emmeseconditerationnetwork
%EMME_PYTHON_PATH%\python %BASE_SCRIPTS%\skims\create_emme_network.py -p "trn" --first_iteration "no"
IF ERRORLEVEL 1 goto done
:: changing back to python 2 environment
CALL conda deactivate
CALL conda activate mtc_py2
:afteremmeupdate

:: Create the block file that controls whether the crowding functions are called during transit assignment.
REM python %BASE_SCRIPTS%\assign\transit_assign_set_type.py CTRAMP\runtime\mtctm2.properties CTRAMP\scripts\block\transit_assign_type.block

::Inner iterations with transit assignment and path recalculator
SET /A INNER_ITERATION=0
:inner_iteration_start
SET /A INNER_ITERATION+=1

  :: no longer needed
	REM "%TPP_PATH%\runtpp" CTRAMP\scripts\assign\merge_transit_matrices.s
	REM if ERRORLEVEL 2 goto done

:innerskim
  CALL conda deactivate
  CALL conda activate mtc

  %EMME_PYTHON_PATH%\python %BASE_SCRIPTS%\skims\skim_transit_network.py -p "trn" -s "skims" --iteration %INNER_ITERATION% --output_transit_boardings
  IF ERRORLEVEL 1 goto done

  :: changing back to python 2 environment
  CALL conda deactivate
  CALL conda activate mtc_py2
:afterinnerskim

  :: Run Transit Assignment
  REM "%TPP_PATH%\runtpp" CTRAMP\scripts\assign\TransitAssign.job
  REM if ERRORLEVEL 2 goto done

  REM "%TPP_PATH%\runtpp" %BASE_SCRIPTS%\skims\SkimSetsAdjustment.job
  REM if ERRORLEVEL 2 goto done

  :: Start Matrix Server remotely or locally
  REM IF %RUNTYPE%==LOCAL (
  REM     rem =========== local ========================
  REM     call CTRAMP\runtime\runMtxMgr.cmd %HOST_IP_ADDRESS% "%JAVA_PATH%"
  REM     echo Started matrix manager
  REM ) ELSE (
  REM     rem =========== remote ========================
  REM     rem (wait 10 seconds between each call because otherwise psXXX sometimes bashes on its own authentication/permissions)
  REM     CTRAMP\runtime\config\pskill %MATRIX_SERVER% u %UN% -p %PWD% java
  REM     ping -n 10 localhost
  REM     CTRAMP\runtime\config\psexec %MATRIX_SERVER% -u %UN% -p %PWD% -d "%MATRIX_SERVER_ABSOLUTE_BASE_DIR%\CTRAMP\runtime\runMtxMgr.cmd" "%MATRIX_SERVER_JAVA_PATH%"
  REM     ping -n 10 localhost
  REM )

   :: Run Transit Best Path Recalculation (uncomment for transit capacity restraint)
   :: copy CTRAMP\runtime\mtctm2.properties mtctm2.properties    /Y
   :: call CTRAMP\runtime\runTransitPathRecalculator.cmd %ITERATION% "%JAVA_PATH%"
   :: if ERRORLEVEL 2 goto done
   :: del mtctm2.properties

	:: backup the trip files
	:: copy ctramp_output\indivTripDataResim_%ITERATION%.csv ctramp_output\indivTripDataResim_%ITERATION%_%INNER_ITERATION%.csv
 	:: copy ctramp_output\jointTripDataResim_%ITERATION%.csv ctramp_output\jointTripDataResim_%ITERATION%_%INNER_ITERATION%.csv

	IF %INNER_ITERATION% LSS %MAX_INNER_ITERATION% GOTO inner_iteration_start

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

:: Generate visualizer
:visualizer
CTRAMP\scripts\visualizer\generateDashboard.bat %ITERATION%

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
