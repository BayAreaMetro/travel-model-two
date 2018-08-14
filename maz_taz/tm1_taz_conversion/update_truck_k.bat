::
:: Update the truck k factor source table from TM1 TAZs to TM2 TAZs
::
set SCRIPT_LOC=C:\Users\lzorn\Documents\travel-model-two

:: convert matrix to csv
runtpp "%SCRIPT_LOC%\maz_taz\tm1_taz_conversion\export_truckkfact_matrix.job"
if ERRORLEVEL 2 goto error

:: convert to tm2 tazs
python "%SCRIPT_LOC%\maz_taz\transform_data_for_maz_taz_update.py" truck_tm1_taz_to_tm2_taz_v22
IF ERRORLEVEL 1 goto error

:: TruckTripDistribution.job's taz_matrix_transfer will update the tazs to sequential
echo Finished Successfully!

:error