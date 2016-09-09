
rem ### First save the JAVA_PATH environment variable so it s value can be restored at the end.
set OLDJAVAPATH=%JAVA_PATH%

rem ### Set the directory of the jdk version desired for this model run
rem ### Note that a jdk is required; a jre is not sufficient, as the UEC class generates
rem ### and compiles code during the model run, and uses javac in the jdk to do this.
set JAVA_PATH=%3

rem ### set sample rate from command line argument
SET sampleRate=%1
SET iteration=%2
set PROJECT_DIRECTORY=%CD:\=/%

rem ### Name the project directory.  This directory will hava data and runtime subdirectories
set RUNTIME=%PROJECT_DIRECTORY%
set CONFIG=%RUNTIME%\CTRAMP\runtime\config
set JAR_LOCATION=%RUNTIME%\CTRAMP\runtime
set JPPF_LIB=%JAR_LOCATION%\lib\JPPF-2.5-admin-ui\lib\*
set LIB_JAR_PATH=%JPPF_LIB%;%JAR_LOCATION%\lib\sandagLib\*;%JAR_LOCATION%\lib\jxlLib\*;%JAR_LOCATION%\lib\ssjLib\*;%JAR_LOCATION%\lib\cmfLib\*;%JAR_LOCATION%\lib\log4jLib\*

rem ### Define the CLASSPATH environment variable for the classpath needed in this model run.
set OLDCLASSPATH=%CLASSPATH%

rem ### Define the CLASSPATH environment variable for the classpath needed in this model run.
set CLASSPATH=%CONFIG%;%RUNTIME%;%LIB_JAR_PATH%;%JAR_LOCATION%\*

rem ### Save the name of the PATH environment variable, so it can be restored at the end of the model run.
set OLDPATH=%PATH%

rem ### Change the PATH environment variable so that JAVA_HOME is listed first in the PATH.
rem ### Doing this ensures that the JAVA_HOME path we defined above is the on that gets used in case other java paths are in PATH.
set PATH=%JAVA_PATH%\bin;%OLDPATH%

rem ### Run ABM LOCAL 
java -server -Xmx130g -cp "%CLASSPATH%" -Dlog4j.configuration=log4j.xml -Dproject.folder=%PROJECT_DIRECTORY% -Djppf.config=jppf-clientLocal.properties com.pb.mtctm2.abm.application.MTCTM2TourBasedModel mtctm2 -iteration %iteration% -sampleRate %sampleRate% -sampleSeed 0
::java -server -Xmx130g -cp "%CLASSPATH%" -Dlog4j.configuration=log4j.xml -Dproject.folder=%PROJECT_DIRECTORY% -Djppf.config=jppf-clientLocal.properties com.pb.mtctm2.abm.application.MTCTM2TourBasedModel mtctm2 -iteration %iteration% -sampleRate %sampleRate% -sampleSeed 0

rem java -Xdebug -Xrunjdwp:transport=dt_socket,address=1045,server=y,suspend=y -server -Xmx130g -cp "%CLASSPATH%" -Dlog4j.configuration=log4j.xml -Dproject.folder=%PROJECT_DIRECTORY% -Djppf.config=jppf-clientLocal.properties com.pb.mtctm2.abm.application.MTCTM2TourBasedModel mtctm2 -iteration 1 -sampleRate %sampleRate% -sampleSeed 0
rem java -agentlib:jdwp=transport=dt_socket,address=1045,server=y,suspend=y -server Xmx130g -cp "%CLASSPATH%" -Dlog4j.configuration=log4j.xml -Dproject.folder=%PROJECT_DIRECTORY% -Djppf.config=jppf-clientLocal.properties com.pb.mtctm2.abm.application.MTCTM2TourBasedModel mtctm2 -iteration 1 -sampleRate %sampleRate% -sampleSeed 0

rem ### Run ABM DISTRIBUTED
rem java -Xdebug -Xrunjdwp:transport=dt_socket,address=1045,server=y,suspend=y -server Xmx130g -cp "%CLASSPATH%" -Dlog4j.configuration=log4j.xml -Dproject.folder=%PROJECT_DIRECTORY% -Djppf.config=jppf-clientDistributed.properties com.pb.mtctm2.abm.application.MTCTM2TourBasedModel mtctm2 -iteration 1 -sampleRate %sampleRate% -sampleSeed 0
rem java -server Xmx130g -cp "%CLASSPATH%" -Dlog4j.configuration=log4j.xml -Dproject.folder=%PROJECT_DIRECTORY% -Djppf.config=jppf-clientDistributed.properties com.pb.mtctm2.abm.application.MTCTM2TourBasedModel mtctm2 -iteration 1 -sampleRate %sampleRate% -sampleSeed 0

rem ### create demand matrices in Cube matrix format - must restart mtx manager before running?
java -Xmx80g -cp "%CLASSPATH%" -Dproject.folder=%PROJECT_DIRECTORY% com.pb.mtctm2.abm.application.MTCTM2TripTables mtctm2 -iteration %iteration% -sampleRate %sampleRate%
::java -Xmx80g -cp "%CLASSPATH%" -Dproject.folder=%PROJECT_DIRECTORY% com.pb.mtctm2.abm.application.MTCTM2TripTables mtctm2 -iteration %iteration% -sampleRate %sampleRate%

rem ### restore saved environment variable values, and change back to original current directory
set JAVA_PATH=%OLDJAVAPATH%
set PATH=%OLDPATH%
set CLASSPATH=%OLDCLASSPATH%
