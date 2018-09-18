:: ############################################################################
:: # Batch file to generate CTRAMP HTML Visualizer
:: # binny.mathewpaul@rsginc.com, June 2017
:: # 1. User should specify the path to base and build summaries the specified 
:: #    directory should have all the files listed in 
:: #    /templates/summaryFilesNames.csv
:: # 2. User should also specify the name of the base and build scenario if the 
:: #    base/build scenario is specified as "HTS", scenario names are replaced 
:: #    with appropriate Census sources names wherever applicable
:: # 3. Run this script from this directory. e.g. .\generateDashboard.bat
:: #    Dashboard and error files will be in subdir "outputs"
:: ## TODO Document caveats for CHTS/Survey and tripModeProfile_vis.csv, tmodeProfile_vis.csv
:: ############################################################################
@ECHO off
SET WORKING_DIR=%~dp0

:: User Inputs
:: ###########
SET BASE_SUMMARY_DIR=M:\Data\HomeInterview\2010\Analysis\Calibration Targets\maz_v2_2
SET BUILD_SUMMARY_DIR=C:\Users\lzorn\Box\Modeling and Surveys\Development\Travel Model Two Development\Calibration and Validation\Round 2\Calibration Spreadsheets\2015_01_lmz_04\ABM Summaries
SET OUTPUT_HTML_NAME=MTC_Dashboard_CHTS_vs_2015_01_lmz_04

SET BASE_SCENARIO_NAME=CHTS
SET BUILD_SCENARIO_NAME=2015_01_lmz_04
:: for survey base legend names are different [Yes/No]
SET IS_BASE_SURVEY=Yes

SET BASE_SAMPLE_RATE=1.0
SET BUILD_SAMPLE_RATE=0.2

:: in data/SHP
SET SHP_FILE_NAME=tazs_TM2_v2_2.shp

if not exist outputs (mkdir outputs)
if not exist runtime (mkdir runtime)

:: Set up dependencies
:: ###################
SET R_SCRIPT=C:\Program Files\R\R-3.5.1\bin\x64\Rscript
:: Use standard R environment variables to tell R where to find libraries (R_LIBS, R_LIBS_USER, etc)
:: Set PANDOC path
SET RSTUDIO_PANDOC=C:\Program Files (x86)\Pandoc
:: Parameters file 
SET PARAMETERS_FILE=runtime\parameters.csv

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
"%R_SCRIPT%" scripts\Master.R %PARAMETERS_FILE%
IF %ERRORLEVEL% EQU 11 (
   ECHO File missing error. Check error file in outputs.
   EXIT /b %errorlevel%
)
ECHO %startTime%%Time%: Dashboard creation complete...

