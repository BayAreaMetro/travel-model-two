@ECHO OFF
rem ############  PARAMETERS  ############
set PROJECT_DIRECTORY=%CD%
set RUNTIME=%PROJECT_DIRECTORY%
set CONFIG=%RUNTIME%\CTRAMP\runtime\config
set JAR_LOCATION=%RUNTIME%\CTRAMP\runtime
set JPPF_LIB=%JAR_LOCATION%\lib\JPPF-2.5-driver\lib\*

set CLASSPATH=%CONFIG%;%JPPF_LIB%
ECHO ***calling: java -server -Xmx16m -cp "%CLASSPATH%" -Dlog4j.configuration=log4j-driver.properties -Djppf.config=jppf-driver.properties org.jppf.server.DriverLauncher
java -server -Xmx16m -cp "%CLASSPATH%" -Dlog4j.configuration=log4j-driver.properties -Djppf.config=jppf-driver.properties org.jppf.server.DriverLauncher
