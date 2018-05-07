::
:: batch file to run maz_taz_checker interatively in a semi-automated way
::

setlocal enabledelayedexpansion

set PATH=c:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3
set WORKSPACE=M:\Data\GIS layers\TM2_maz_taz_v2.2
set TM2_DIR=C:\Users\lzorn\Documents\travel-model-two
set NUM_ITERS=5

:: run this in WORKSPACE

:: copy initial Files
copy %TM2_DIR%\maz_taz\Readme.txt .
copy %TM2_DIR%\maz_taz\csv_to_dbf.R .
copy %TM2_DIR%\maz_taz\blocks_mazs_tazs_v2.1.1.csv .

:: loop
for /L %%V in (1,1,%NUM_ITERS%) do (

  set /a NEXTV=%%V+1
  echo 2.1.%%V 2.1.!NEXTV!

  copy blocks_mazs_tazs_v2.1.%%V.csv blocks_mazs_tazs.csv

  call "C:\Program Files\R\R-3.4.1\bin\x64\Rscript.exe" --vanilla "%WORKSPACE%\csv_to_dbf.R"
  IF ERRORLEVEL 1 goto error

  rem save the dbf for this version
  copy blocks_mazs_tazs.dbf blocks_mazs_tazs_v2.1.%%V.dbf

  if not %%V==%NUM_ITERS% python "%TM2_DIR%\maz_taz\maz_taz_checker.py"
  if %%V==%NUM_ITERS% python "%TM2_DIR%\maz_taz\maz_taz_checker.py" --dissolve
  IF ERRORLEVEL 1 goto error

  if not %%V==%NUM_ITERS% (
    copy maz_taz_checker.log maz_taz_checker_v2.1.!NEXTV!.log
    copy blocks_mazs_tazs_updated.csv blocks_mazs_tazs_v2.1.!NEXTV!.csv
  )
)

echo Success!
goto done

:error
echo Oh no, an error

:done
echo Done