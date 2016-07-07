@ECHO OFF

SET PYTHON_PATH=C:\Python27_64bit
SET BASE_DIR=c:\projects\mtc\template_test

CD %BASE_DIR%

runtpp %BASE_DIR%\documentation\export_network.job
IF ERRORLEVEL 2 GOTO error

::%PYTHON_PATH%\python.exe %BASE_DIR%\documentation\zone_zone_straight_line_distance.py %BASE_DIR%
::IF ERRORLEVEL 1 GOTO error

::runtpp %BASE_DIR%\documentation\export_matrices.job
::IF ERRORLEVEL 2 GOTO error

::%PYTHON_PATH%\python.exe %BASE_DIR%\documentation\documentation_data.py %BASE_DIR%
::IF ERRORLEVEL 1 GOTO error



GOTO done

:error
ECHO
ECHO !!!ERROR!!!
GOTO end

:done
ECHO
ECHO ***FINISHED WITH NO PROBLEMS***

:end

CD %~dp0
