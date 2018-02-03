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
SET WORKING_DIR=%~dp0

:: User Inputs
:: ###########
::SET BASE_SUMMARY_DIR=E:\projects\clients\mtc\data\CHTS_Summaries
SET BASE_SUMMARY_DIR=E:\projects\clients\mtc\ModelOutput\102317_2010_R1\ABM_Summaries
SET BUILD_SUMMARY_DIR=E:\projects\clients\mtc\ModelOutput\102317\ABM_Summaries
SET OUTPUT_HTML_NAME=MTC_Dashboard_2010_R1_vs_R2_6Dec17

SET BASE_SCENARIO_NAME=2010_R1
SET BUILD_SCENARIO_NAME=2010_R2
:: for survey base legend names are different [Yes/No]
SET IS_BASE_SURVEY=No

SET BASE_SAMPLE_RATE=0.2
SET BUILD_SAMPLE_RATE=1.0

SET SHP_FILE_NAME=tazs.shp

:: Set up dependencies
:: ###################
SET R_SCRIPT=%~dp0\dependencies\R-3.4.1\bin\Rscript
SET R_LIBRARY=%~dp0\dependencies\R-3.4.1\library
:: Set PANDOC path
SET RSTUDIO_PANDOC=%~dp0\dependencies\Pandoc
:: Parameters file 
SET PARAMETERS_FILE=%~dp0\runtime\parameters.csv

ECHO Key,Value > %PARAMETERS_FILE%
ECHO WORKING_DIR,%WORKING_DIR% >> %PARAMETERS_FILE%
ECHO BASE_SUMMARY_DIR,%BASE_SUMMARY_DIR% >> %PARAMETERS_FILE%
ECHO BUILD_SUMMARY_DIR,%BUILD_SUMMARY_DIR% >> %PARAMETERS_FILE%
ECHO BASE_SCENARIO_NAME,%BASE_SCENARIO_NAME% >> %PARAMETERS_FILE%
ECHO BUILD_SCENARIO_NAME,%BUILD_SCENARIO_NAME% >> %PARAMETERS_FILE%
ECHO BASE_SAMPLE_RATE,%BASE_SAMPLE_RATE% >> %PARAMETERS_FILE%
ECHO BUILD_SAMPLE_RATE,%BUILD_SAMPLE_RATE% >> %PARAMETERS_FILE%
ECHO R_LIBRARY,%R_LIBRARY% >> %PARAMETERS_FILE%
ECHO OUTPUT_HTML_NAME,%OUTPUT_HTML_NAME% >> %PARAMETERS_FILE%
ECHO SHP_FILE_NAME,%SHP_FILE_NAME% >> %PARAMETERS_FILE%
ECHO IS_BASE_SURVEY,%IS_BASE_SURVEY% >> %PARAMETERS_FILE%

:: Call the master R script
:: ########################
ECHO %startTime%%Time%: Running R script to generate visualizer...
%R_SCRIPT% scripts\Master.R %PARAMETERS_FILE%
IF %ERRORLEVEL% EQU 11 (
   ECHO File missing error. Check error file in outputs.
   EXIT /b %errorlevel%
)
ECHO %startTime%%Time%: Dashboard creation complete...

