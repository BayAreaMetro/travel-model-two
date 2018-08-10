@ECHO OFF

SET TOTAL_TAZS_EXTERNALS=4709
SET PYTHON=c:\Programs\Python27_32bit\python.exe
SET BASE_DIR=%~dp0

%PYTHON% %BASE_DIR%\airport\taz2old.py %BASE_DIR%
%PYTHON% %BASE_DIR%\ix_trips\scale_ix_to_new_tazs.py %BASE_DIR%
runtpp %BASE_DIR%\ix_trips\build_ix_matrix.job
%PYTHON% %BASE_DIR%\truck_model\transfer_truck_kfactors.py %BASE_DIR%
