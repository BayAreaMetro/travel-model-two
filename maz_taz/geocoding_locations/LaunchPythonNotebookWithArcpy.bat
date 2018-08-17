@echo off
set ARCGISPRO_PATH=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3
set path=%ARCGISPRO_PATH%;%ARCGISPRO_PATH%\Scripts
set PYTHONPATH=%ARCGISPRO_PATH%\Lib\site-packages
jupyter notebook "CHTS Geocode Engine.ipynb"

