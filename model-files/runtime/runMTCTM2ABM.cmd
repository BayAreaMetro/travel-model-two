
rem ### Set the directory of the jdk version desired for this model run
rem ### Note that a jdk is required; a jre is not sufficient, as the UEC class generates
rem ### and compiles code during the model run, and uses javac in the jdk to do this.
set JAVA_PATH=%~3
echo JAVA_PATH=[%JAVA_PATH%]

rem ### set sample rate from command line argument
SET sampleRate=%1
SET iteration=%2
set PROJECT_DIRECTORY=%CD%
rem Want this one with forward slashes
set PROJECT_DIRECTORY2=%CD:\=/%
echo PROJECT_DIRECTORY2=[%PROJECT_DIRECTORY2%]

rem ### Name the project directory.  This directory will hava data and runtime subdirectories
set RUNTIME=%PROJECT_DIRECTORY%
set CONFIG=%RUNTIME%\CTRAMP\runtime\config
set JAR_LOCATION=%RUNTIME%\CTRAMP\runtime
set JPPF_LIB=%JAR_LOCATION%\lib\JPPF-2.5-admin-ui\lib\*
set LIB_JAR_PATH=%JPPF_LIB%;%JAR_LOCATION%\lib\sandagLib\*;%JAR_LOCATION%\lib\jxlLib\*;%JAR_LOCATION%\lib\ssjLib\*;%JAR_LOCATION%\lib\cmfLib\*;%JAR_LOCATION%\lib\log4jLib\*

rem ### Define the CLASSPATH environment variable for the classpath needed in this model run.
set CLASSPATH=%JAR_LOCATION%\common-base.jar;%JAR_LOCATION%\mtctm2.jar;%CONFIG%;%RUNTIME%;%LIB_JAR_PATH%

IF %RUNTYPE%==LOCAL (
  echo ### Run ABM LOCAL
  set DEBUG_OPTIONS=-agentlib:jdwp=transport=dt_socket,address=8998,server=y
  java -server -Xmx130g -cp "%CLASSPATH%" -Dlog4j.configuration=log4j.xml -Dproject.folder=%PROJECT_DIRECTORY2% -Djppf.config=jppf-clientLocal.properties com.pb.mtctm2.abm.application.MTCTM2TourBasedModel mtctm2 -iteration %iteration% -sampleRate %sampleRate% -sampleSeed 0
  IF ERRORLEVEL 2 goto done_core  
)

IF %RUNTYPE%==DISTRIBUTED (
  echo ### Run ABM DISTRIBUTED
  rem java -Xdebug -Xrunjdwp:transport=dt_socket,address=1045,server=y,suspend=y -server Xmx130g -cp "%CLASSPATH%" -Dlog4j.configuration=log4j.xml -Dproject.folder=%PROJECT_DIRECTORY2% -Djppf.config=jppf-clientDistributed.properties com.pb.mtctm2.abm.application.MTCTM2TourBasedModel mtctm2 -iteration 1 -sampleRate %sampleRate% -sampleSeed 0
  rem java -server -Xmx130g -cp "%CLASSPATH%" -Dlog4j.configuration=log4j.xml -Dproject.folder=%PROJECT_DIRECTORY2% -Djppf.config=jppf-clientDistributed.properties com.pb.mtctm2.abm.application.MTCTM2TourBasedModel mtctm2 -iteration 1 -sampleRate %sampleRate% -sampleSeed 0
)

rem ### create demand matrices in Cube matrix format - must restart mtx manager before running?
java -Xmx80g -cp "%CLASSPATH%" -Dproject.folder=%PROJECT_DIRECTORY2% com.pb.mtctm2.abm.application.MTCTM2TripTables mtctm2 -iteration %iteration% -sampleRate %sampleRate%
rem java -Xdebug -Xrunjdwp:transport=dt_socket,address=1045,server=y,suspend=y -server -Xmx80g -cp "%CLASSPATH%" -Dproject.folder=%PROJECT_DIRECTORY2% com.pb.mtctm2.abm.application.MTCTM2TripTables mtctm2 -iteration %iteration% -sampleRate %sampleRate%

:done_core