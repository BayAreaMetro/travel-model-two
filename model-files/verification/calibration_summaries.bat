
:: Run this in the model directory
::

:: Transit Summaries
Rscript --vanilla --verbose "%USERPROFILE%\Documents\travel-model-two\model-files\verification\appendLOSAttributes.R" --transitonly 1 XFERS LB_TIME EB_TIME FR_TIME LR_TIME HR_TIME CR_TIME BEST_MODE
