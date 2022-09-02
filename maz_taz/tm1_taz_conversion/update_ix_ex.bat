::
:: Update the IX/EX source table from TM1 TAZs to TM2 TAZs
:: Run in M:\Development\Travel Model Two\InternalExternal

:: TM1 version
set TAZ_COUNT=1454
set TAZ_EXTS_COUNT=1475
set SCRIPT_LOC=X:\travel-model-two-transit-ccr

:: convert TM1 matrix files to csv
set MATRIX_FILE=IXDaily2006x4.may2208.mat
runtpp "%SCRIPT_LOC%\maz_taz\tm1_taz_conversion\export_ix_matrix.job"
if ERRORLEVEL 2 goto error

set MATRIX_FILE=ixDaily2015.tpp
runtpp "%SCRIPT_LOC%\maz_taz\tm1_taz_conversion\export_ix_matrix.job"
if ERRORLEVEL 2 goto error

:: update both to use tm2 tazs using tm1 taz -> tm2 taz correspondence
python "%SCRIPT_LOC%\maz_taz\transform_data_for_maz_taz_update.py" ix_tm1_taz_to_tm2_taz_v22
IF ERRORLEVEL 1 goto error

:: this file is from a TM2 development run, output by scripts\preprocess\zone_seq_net_builder.job
set RENUMBER_FILE=mtc_final_network_zone_seq_tazext.csv
:: Renumber to consecutive zones
python "%SCRIPT_LOC%\model-files\scripts\preprocess\renumber.py" IXDaily2006x4.may2208_updated_ij.csv IXDaily2006x4.may2208_updated_ij_seq.csv --renumber_key_csv %RENUMBER_FILE% --input_col I_tm2 J_tm2 --renum_join_col N N --renum_out_col TAZSEQ TAZSEQ --output_rename_col DELETE DELETE --output_new_col I_tm2_taz J_tm2_taz

python "%SCRIPT_LOC%\model-files\scripts\preprocess\renumber.py" ixDaily2015_updated_ij.csv ixDaily2015_updated_ij_seq.csv --renumber_key_csv %RENUMBER_FILE% --input_col I_tm2 J_tm2 --renum_join_col N N --renum_out_col TAZSEQ TAZSEQ --output_rename_col DELETE DELETE --output_new_col I_tm2_taz J_tm2_taz

:: Setup for TM2
set TAZ_EXTS_COUNT=4756
:: convert matrix back to matrix
set MATRIX_FILE=IXDaily2006x4.may2208.mat
runtpp "%SCRIPT_LOC%\maz_taz\tm1_taz_conversion\import_ix_matrix.job"
if ERRORLEVEL 2 goto error

set MATRIX_FILE=ixDaily2015.tpp
runtpp "%SCRIPT_LOC%\maz_taz\tm1_taz_conversion\import_ix_matrix.job"
if ERRORLEVEL 2 goto error

echo Finished Successfully!

:error