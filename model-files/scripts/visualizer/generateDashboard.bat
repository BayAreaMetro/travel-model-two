:: ############################################################################
:: # Batch file to generate CTRAMP HTML Visualizer
:: # binny.mathewpaul@rsginc.com, June 2017
:: # 1. User should specify the path to base and build summaries the specified
:: #    directory should have all the files listed in
:: #    /templates/summaryFilesNames.csv
:: # 2. User should also specify the name of the base and build scenario if the
:: #    base/build scenario is specified as "HTS", scenario names are replaced
:: #    with appropriate Census sources names wherever applicable
:: ############################################################################
@ECHO off

SET MAX_ITER=%1

SET WORKING_DIR=%~dp0
SET ABM_DIR=%CD%

:: Getting datetime so as to not overwrite old files
For /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
For /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)

:: User Inputs
SET OUTPUT_HTML_NAME=TM2_vs_CHTS_%mydate%_%mytime%
SET BASE_SCENARIO_NAME=CHTS
SET BUILD_SCENARIO_NAME=TM2
:: for survey base legend names are different [Yes/No]
SET IS_BASE_SURVEY=Yes

:: ###########
SET BASE_SUMMARY_DIR=%ABM_DIR%\input\visualizer\data\CHTS_Summaries
SET ABM_OUTPUT_DIR=%ABM_DIR%\ctramp_output
SET ABM_SUMMARY_DIR=%ABM_DIR%\ctramp_output\ABM_summaries
SET BUILD_SUMMARY_DIR=%ABM_SUMMARY_DIR%
SET CT_ZERO_AUTO_FILE_NAME=ct_zero_auto.shp
SET VISUALIZER_INPUT_PATH=%ABM_DIR%\input\visualizer
SET CENSUS_DIR=%VISUALIZER_INPUT_PATH%\data\census
SET ZONES_DIR=%VISUALIZER_INPUT_PATH%\data\SHP
SET SKIMS_DIR=%ABM_DIR%\skims
SET LANDUSE_DIR=%ABM_DIR%\landuse

SET BASE_SAMPLE_RATE=1.0
SET BUILD_SAMPLE_RATE=1.0

SET SHP_FILE_NAME=tazs.shp

:: Set up dependencies
:: ###################
SET R_SCRIPT=%ABM_DIR%\input\visualizer\dependencies\R-3.4.1\bin\Rscript
SET R_LIBRARY=%ABM_DIR%\input\visualizer\dependencies\R-3.4.1\library
:: Set PANDOC path
SET RSTUDIO_PANDOC=%ABM_DIR%\input\visualizer\dependencies\Pandoc
:: Parameters file
SET PARAMETERS_FILE=%ABM_DIR%\input\visualizer\runtime\parameters.csv

ECHO Key,Value > %PARAMETERS_FILE%
ECHO WORKING_DIR,%WORKING_DIR% >> %PARAMETERS_FILE%
ECHO ABM_DIR,%ABM_DIR% >> %PARAMETERS_FILE%
ECHO ABM_OUTPUT_DIR,%ABM_OUTPUT_DIR% >> %PARAMETERS_FILE%
ECHO ABM_SUMMARY_DIR,%ABM_SUMMARY_DIR% >> %PARAMETERS_FILE%
ECHO VISUALIZER_INPUT_PATH,%VISUALIZER_INPUT_PATH% >> %PARAMETERS_FILE%
ECHO BASE_SUMMARY_DIR,%BASE_SUMMARY_DIR% >> %PARAMETERS_FILE%
ECHO BUILD_SUMMARY_DIR,%BUILD_SUMMARY_DIR% >> %PARAMETERS_FILE%
ECHO BASE_SCENARIO_NAME,%BASE_SCENARIO_NAME% >> %PARAMETERS_FILE%
ECHO BUILD_SCENARIO_NAME,%BUILD_SCENARIO_NAME% >> %PARAMETERS_FILE%
ECHO BASE_SAMPLE_RATE,%BASE_SAMPLE_RATE% >> %PARAMETERS_FILE%
ECHO BUILD_SAMPLE_RATE,%BUILD_SAMPLE_RATE% >> %PARAMETERS_FILE%
ECHO CT_ZERO_AUTO_FILE_NAME,%CT_ZERO_AUTO_FILE_NAME% >> %PARAMETERS_FILE%
ECHO ZONES_DIR,%ZONES_DIR% >> %PARAMETERS_FILE%
ECHO SKIMS_DIR,%SKIMS_DIR% >> %PARAMETERS_FILE%
ECHO LANDUSE_DIR,%LANDUSE_DIR% >> %PARAMETERS_FILE%
ECHO CENSUS_DIR,%CENSUS_DIR% >> %PARAMETERS_FILE%
ECHO MAX_ITER,%MAX_ITER% >> %PARAMETERS_FILE%
ECHO R_LIBRARY,%R_LIBRARY% >> %PARAMETERS_FILE%
ECHO OUTPUT_HTML_NAME,%OUTPUT_HTML_NAME% >> %PARAMETERS_FILE%
ECHO SHP_FILE_NAME,%SHP_FILE_NAME% >> %PARAMETERS_FILE%
ECHO IS_BASE_SURVEY,%IS_BASE_SURVEY% >> %PARAMETERS_FILE%


:: Call the R Script to CTRAMP summary outputs
:: #######################################
ECHO %startTime%%Time%: Creating CTRAMP summaries...
%R_SCRIPT% %ABM_DIR%\CTRAMP\scripts\visualizer\SummarizeABM_MTC_TM2.R %PARAMETERS_FILE%
IF %ERRORLEVEL% NEQ 0 goto error

:: Call the R Script to generate Jobs vs Workers Summary
:: #######################################
ECHO %startTime%%Time%: Running R script to generate Jobs vs Workers Summary...
%R_SCRIPT% %ABM_DIR%\CTRAMP\scripts\visualizer\workersByMAZ.R %PARAMETERS_FILE%
IF %ERRORLEVEL% NEQ 0 goto error

:: Call the R Script to generate Zero Auto CT plot
:: #######################################
ECHO %startTime%%Time%: Creating zero auto ownership map...
%R_SCRIPT% %ABM_DIR%\CTRAMP\scripts\visualizer\AutoOwnership_Census_CT_MTC_TM2.R %PARAMETERS_FILE%
IF %ERRORLEVEL% NEQ 0 goto error

:: Call the master R script
:: ########################
ECHO %startTime%%Time%: Running R script to generate visualizer...
%R_SCRIPT% %ABM_DIR%\CTRAMP\scripts\visualizer\Master.R %PARAMETERS_FILE%
IF %ERRORLEVEL% EQU 11 (
   ECHO File missing error. Check error file in outputs.
   EXIT /b %errorlevel%
)
IF %ERRORLEVEL% NEQ 0 goto error

:finished
ECHO %startTime%%Time%: Dashboard creation complete...
goto end

:error
ECHO Error occured, dashboard not created

:end
