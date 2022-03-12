:: -----------------------------------------------------------------------------------------------------------------------------------
:: We found that setting up model runs with key input directories was helpful in TM1.5 so this script
:: carries that convention forward.  See https://github.com/BayAreaMetro/travel-model-one/blob/master/model-files/SetUpModel_PBA50.bat
:: Note: This must be run as a local copy within the model run directory
:: -----------------------------------------------------------------------------------------------------------------------------------

:: set ENVTYPE=MTC or RSG
set ENVTYPE=MTC

:: ------------------------------
:: Step 1: Specify file locations
:: ------------------------------
:: set the location of the model run folder on M; this is where the input and output directories will be copied to
set M_DIR=M:\Development\Travel Model Two\Test Runs\2015_TM210_Test_00

:: set the location of the travel-model-two github repo
set GITHUB_DIR=\\tsclient\X\travel-model-two-transit-ccr

:: set the location of the networks (make sure the network version, year and variant are correct)
:: expect hwy and trn subdirectories to exist within
set INPUT_NETWORK=\\tsclient\C\Users\lzorn\Box\Modeling and Surveys\Development\Travel Model Two Development\Model Inputs\2015

:: set the location of the populationsim and land use inputs (make sure the land use version and year are correct) 
set INPUT_LU=\\tsclient\C\Users\lzorn\Box\Modeling and Surveys\Development\Travel Model Two Development\Model Inputs\2015\landuse
set INPUT_POPSYN=\\tsclient\C\Users\lzorn\Box\Modeling and Surveys\Development\Travel Model Two Development\Model Inputs\2015\popsyn

:: set the location of the nonres inputs
set INPUT_NONRES=\\tsclient\C\Users\lzorn\Box\Modeling and Surveys\Development\Travel Model Two Development\Model Inputs\2015\nonres

:: Not used yet, todo
set UrbanSimScenario=s24

:: set the location of the previous run (where warmstart inputs will be copied)
:: the INPUT folder of the previous run will also be used as the base for the compareinputs log
set PREV_RUN_DIR=NA

:: set the name and location of the properties file
:: often the properties file is on master during the active application phase
set PARAMS=NA

:: ------------------------------------
:: Step 2: Copy over RunModel and input
:: ------------------------------------

:: CTRAMP is copied over in RunModel.bat
copy /Y "%GITHUB_DIR%\model-files\RunModel.bat"     .
mkdir INPUT

:: TODO: slack

:: network input
c:\windows\system32\Robocopy.exe /E "%INPUT_NETWORK%\hwy"   INPUT\hwy
c:\windows\system32\Robocopy.exe /E "%INPUT_NETWORK%\trn"   INPUT\trn

:: popsyn and land use input
c:\windows\system32\Robocopy.exe /E "%INPUT_LU%"            INPUT\popsyn
c:\windows\system32\Robocopy.exe /E "%INPUT_POPSYN%"        INPUT\landuse

:: non residential input
c:\windows\system32\Robocopy.exe /E "%INPUT_NONRES%"        INPUT\nonres

:: warmstart (copy from the previous run)
:: TODO

:: Figure out model year
:: TODO, this is set in RunModel.bat right now

:: ---------------------------------------------------------------
:: Step 3: copy information back to the M drive for run management
:: ---------------------------------------------------------------

:: TODO
:: let's add this later when we start application; these are huge files right now...

::----------------------------------------------
:: add folder name to the command prompt window 
::----------------------------------------------
set MODEL_DIR=%CD%
set PROJECT_DIR=%~p0
set PROJECT_DIR2=%PROJECT_DIR:~0,-1%
:: get the base dir only
for %%f in (%PROJECT_DIR2%) do set myfolder=%%~nxf

title %myfolder%

:: copy this batch file itself to M
set CopyOfSetupModel=SetUpModel_%myfolder%.txt
copy SetUpModel.bat "%M_DIR%\%CopyOfSetupModel%"

::-----------------------------------------------------------------------
:: create a shortcut of the project directory using a temporary VBScript
::-----------------------------------------------------------------------

set TEMP_SCRIPT="%CD%\temp_script_to_create_shortcut.vbs"
set PROJECT_DIR=%~p0
set ALPHABET=%computername:~7,1%

echo Set oWS = WScript.CreateObject("WScript.Shell") >> %TEMP_SCRIPT%
echo sLinkFile = "%M_DIR%/model_run_on_%computername%.lnk" >> %TEMP_SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %TEMP_SCRIPT%
echo oLink.TargetPath = "M:" >> %TEMP_SCRIPT%
echo oLink.TargetPath = "\\%computername%\%PROJECT_DIR%" >> %TEMP_SCRIPT%

echo oLink.Save >> %TEMP_SCRIPT%

::C:\Windows\SysWOW64\cscript.exe /nologo %TEMP_SCRIPT%
C:\Windows\SysWOW64\cscript.exe %TEMP_SCRIPT%
del %TEMP_SCRIPT%