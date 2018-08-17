@echo off
set path=C:\Python27\ArcGIS10.1;C:\Anaconda32;C:\Anaconda32\Scripts
set PYTHONPATH=C:\Anaconda32\Lib\site-packages;C:\Python27\ArcGIS10.1\Lib\site-packages\;C:\Python27\ArcGIS10.1\Lib;C:\Anaconda32\Lib;%pythonpath%
start C:\Python27\ArcGIS10.1\python.exe -c "import sys; from IPython.html.notebookapp import launch_new_instance; sys.exit(launch_new_instance())" %*
exit /B %ERRORLEVEL%
