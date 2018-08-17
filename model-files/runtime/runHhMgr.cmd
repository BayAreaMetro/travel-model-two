@echo off

echo "runHhMgr.cmd running"

:: get the ipaddress of this machine
:: IPCONFIG output includes a line like
::    IPv4 Address. . . . . . . . . . . : 192.168.1.206
:: so IP will be set to "Address. . . . . . . . . . . : 192.168.1.206"
FOR /F "TOKENS=1* DELIMS= " %%A IN ('IPCONFIG') DO (
  IF "%%A"=="IPv4" SET IP=%%B
)
:: this will end with IPADDRESs to 192.168.1.206
FOR %%A IN (%IP%) DO SET IPADDRESS=%%A
set HOST_IP_ADDRESS=%IPADDRESS%
set HOST_PORT=1117
echo HOST_IP_ADDRESS=[%HOST_IP_ADDRESS%]

rem ### Set the directory of the jdk version desired for this model run
rem ### Note that a jdk is required; a jre is not sufficient, as the UEC class generates
rem ### and compiles code during the model run, and uses javac in the jdk to do this.
set JAVA_PATH=%~1
CD %~dp0\..\..
set PROJECT_DIRECTORY=%CD%
echo JAVA_PATH=[%JAVA_PATH%]

rem ### Name the project directory.  This directory will hava data and runtime subdirectories
set RUNTIME=%PROJECT_DIRECTORY%
set CONFIG=%RUNTIME%\CTRAMP\runtime\config
set JAR_LOCATION=%RUNTIME%\CTRAMP\runtime
set JPPF_LIB=%JAR_LOCATION%\lib\JPPF-2.5-admin-ui\lib\*
set LIB_JAR_PATH=%JPPF_LIB%;%JAR_LOCATION%\lib\sandagLib\*;%JAR_LOCATION%\lib\jxlLib\*;%JAR_LOCATION%\lib\ssjLib\*;%JAR_LOCATION%\lib\cmfLib\*;%JAR_LOCATION%\lib\log4jLib\*;%JAR_LOCATION%\lib\JPPF-2.5.5-admin-ui\lib\*

rem ### Define the CLASSPATH environment variable for the classpath needed in this model run.
set CLASSPATH=%CONFIG%;%RUNTIME%;%LIB_JAR_PATH%;%JAR_LOCATION%\*;%JAR_LOCATION%\*

rem ### Change current directory to RUNTIME, and issue the java command to run the model.
ECHO ***calling: "%JAVA_PATH%\bin\java" -server -Xmx35000m -cp "%CLASSPATH%" -Dlog4j.configuration=log4j_hh.xml com.pb.mtctm2.abm.application.SandagHouseholdDataManager2 -hostname %HOST_IP_ADDRESS% -port %HOST_PORT%
START "Household Manager" "%JAVA_PATH%\bin\java" -server -Xmx35000m -cp "%CLASSPATH%" -Dlog4j.configuration=log4j_hh.xml com.pb.mtctm2.abm.application.SandagHouseholdDataManager2 -hostname %HOST_IP_ADDRESS% -port %HOST_PORT%

