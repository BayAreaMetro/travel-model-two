::
:: batch file to run maz_taz_checker interatively in a semi-automated way
::

set WORKSPACE=M:\Data\GIS layers\TM2_maz_taz_v2.2
set TM2_DIR=C:\Users\lzorn\Documents\travel-model-two
set VERSION_CURR=2.1.1
set VERSION_NEXT=2.1.2

copy blocks_mazs_tazs_v%VERSION_CURR%.csv blocks_mazs_tazs.csv

call "C:\Program Files\R\R-3.4.1\bin\x64\Rscript.exe" --vanilla "%WORKSPACE%\csv_to_dbf.R"
IF ERRORLEVEL 1 goto error

:: save the dbf for this version
copy blocks_mazs_tazs.dbf blocks_mazs_tazs_v%VERSION_CURR%.dbf

:: clear the dissolve shapefiles so they'll regenerate
del mazs_TM2_v2_2.*
del tazs_TM2_v2_2.*
python "%TM2_DIR%\utilities\maz_taz_checker.py"
IF ERRORLEVEL 1 goto error

copy maz_taz_checker.log maz_taz_checker_v%VERSION_NEXT%.log
copy blocks_mazs_tazs_updated.csv blocks_mazs_tazs_v%VERSION_NEXT%.csv

echo Success!
goto done

:error
echo Oh no, an error

:done
echo Done