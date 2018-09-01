@echo off

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
set HOST_MATRIX_PORT=1191

rem ### Set the directory of the jdk version desired for this model run
rem ### Note that a jdk is required; a jre is not sufficient, as the UEC class generates
rem ### and compiles code during the model run, and uses javac in the jdk to do this.
set JAVA_PATH=%~1
CD %~dp0\..\..
set PROJECT_DIRECTORY=%CD%

rem ### Name the project directory.  This directory will hava data and runtime subdirectories
set RUNTIME=%PROJECT_DIRECTORY%
set CONFIG=%RUNTIME%\CTRAMP\runtime\config
set JAR_LOCATION=%RUNTIME%\CTRAMP\runtime
set JPPF_LIB=%JAR_LOCATION%\lib\JPPF-2.5-admin-ui\lib\*
set LIB_JAR_PATH=%JPPF_LIB%;%JAR_LOCATION%\lib\sandagLib\*;%JAR_LOCATION%\lib\cmfLib\*;%JAR_LOCATION%\lib\log4jLib\*

rem ### Define the CLASSPATH environment variable for the classpath needed in this model run.
set CLASSPATH=%JAR_LOCATION%\common-base.jar;%JAR_LOCATION%\mtctm2.jar;%CONFIG%;%RUNTIME%;%LIB_JAR_PATH%

ECHO ***calling: "%JAVA_PATH%\bin\java" -Dname=p%HOST_MATRIX_PORT% -Xmx64g -cp "%CLASSPATH%" -Dlog4j.configuration=log4j_mtx.xml com.pb.mtctm2.abm.ctramp.MatrixDataServer -hostname %HOST_IP_ADDRESS% -port %HOST_MATRIX_PORT%
START "Matrix Manager" "%JAVA_PATH%\bin\java" -Dname=p%HOST_MATRIX_PORT% -Xmx64g -cp "%CLASSPATH%" -Dlog4j.configuration=log4j_mtx.xml com.pb.mtctm2.abm.ctramp.MatrixDataServer -hostname %HOST_IP_ADDRESS% -port %HOST_MATRIX_PORT%

