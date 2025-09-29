@ECHO OFF

rem ############  PARAMETERS  ############
rem mapped drive location is already set
set PROJECT_DIRECTORY=%CD%
set RUNTIME=%PROJECT_DIRECTORY%
set CONFIG=%RUNTIME%\config
set JAR_LOCATION=%RUNTIME%
set JPPF_LIB=%JAR_LOCATION%\lib\JPPF-2.5-node\lib\*

rem ############  JPPF NODE  ############
set CLASSPATH=%CONFIG%;%JPPF_LIB%
ECHO ***calling: java -server -Xms16m -Xmx16m -cp "%CLASSPATH%" -Dlog4j.configuration=log4j-node0.properties -Djppf.config=jppf-node0.properties org.jppf.node.NodeLauncher
java -server -Xms16m -Xmx16m -cp "%CLASSPATH%" -Dlog4j.configuration=log4j-node0.properties -Djppf.config=jppf-node0.properties org.jppf.node.NodeLauncher
