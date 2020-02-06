
These scripts create summary files for model calibration/validation.

### processObsDataBase.R

Creates summaries of onboard survey data in a standardized (undocumented) format.


### SummarizeCHTS_districts.R

Creates summaries of California Household Travel Survey data in the same(ish) standardized (undocumented) format.


### SummarizeABM_districts.R

Creates summaries of the TM2 model results in the same(ish) standardized (undocumented) format.  Requires [appendLOSAttributes.R](appendLOSAttributes.R) to be run first to convert the skims to omx format and also the add transit LOS attributes to the trip and tour files.


### [hwyValidation.R](hwyValidation.R)

Summarized pems data vs model results and outputs a summary file, `volume_vs_count.csv`.
