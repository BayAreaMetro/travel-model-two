#######################################################################################
# Copy files from ABM summary folder to visualizer data/build folder
#
######################################################################################

#ABM_Summaries       <- "E:/projects/clients/sandag/TO21_AB2_Calibration/ABM_Summaries"
ABM_Summaries       <- "E:/projects/clients/sandag/TO21_AB2_Calibration/data/HTS_Summaries"
VISU_APP_PATH       <- "E:/projects/clients/sandag/TO21_AB2_Calibration/SANDAG_Visualizer"
BASE_DATA_PATH      <- file.path(VISU_APP_PATH, "data/base")
BUILD_DATA_PATH     <- file.path(VISU_APP_PATH, "data/base_HTS")

setwd(BASE_DATA_PATH)
base_csv = list.files(pattern="*.csv")

setwd(ABM_Summaries)
for(file in base_csv){
  full_file <- paste(ABM_Summaries, file, sep = "/")
  # copy if file exists in ABM summary folder
  if(file.exists(file)){
    file.copy(full_file, BUILD_DATA_PATH, overwrite = T, copy.date = T)
  } else{
    #winDialog("ok", paste(file, "does not exist"))
  }
  #cat(full_file)
}