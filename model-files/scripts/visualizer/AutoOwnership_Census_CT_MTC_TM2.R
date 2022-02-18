######################################################################################
# Creating leaflet comparing census tract level auto ownership with model
#
######################################################################################

start_time <- Sys.time()

### Read Command Line Arguments
args                <- commandArgs(trailingOnly = TRUE)
Parameters_File     <- args[1]
# Parameters_File <- "F:/Projects/Clients/mtc/updated_networks/version_11_v4_new_population/input/visualizer/runtime/parameters.csv"

LOAD_PKGS_LIST <- c("leaflet", "htmlwidgets", "rgdal", "rgeos", "raster", "dplyr")
lib_sink <- suppressWarnings(suppressMessages(lapply(LOAD_PKGS_LIST, library, character.only = TRUE)))

### Read parameters from Parameters_File
parameters              <- read.csv(Parameters_File, header = TRUE)
ABM_DIR                 <- trimws(paste(parameters$Value[parameters$Key=="ABM_DIR"]))
ABM_OUTPUT_DIR          <- trimws(paste(parameters$Value[parameters$Key=="ABM_OUTPUT_DIR"]))
ABM_SUMMARY_DIR         <- trimws(paste(parameters$Value[parameters$Key=="ABM_SUMMARY_DIR"]))
CENSUS_DIR              <- trimws(paste(parameters$Value[parameters$Key=="CENSUS_DIR"]))
ZONES_DIR               <- trimws(paste(parameters$Value[parameters$Key=="ZONES_DIR"]))
R_LIBRARY               <- trimws(paste(parameters$Value[parameters$Key=="R_LIBRARY"]))
BUILD_SAMPLE_RATE       <- trimws(paste(parameters$Value[parameters$Key=="BUILD_SAMPLE_RATE"]))
CT_ZERO_AUTO_FILE_NAME  <- trimws(paste(parameters$Value[parameters$Key=="CT_ZERO_AUTO_FILE_NAME"]))
SHP_FILE_NAME           <- trimws(paste(parameters$Value[parameters$Key=="SHP_FILE_NAME"]))
MAX_ITER                <- trimws(paste(parameters$Value[parameters$Key=="MAX_ITER"]))

# INPUTS
########
# CensusData      <- "E:/Projects/Clients/SEMCOG/Tasks/Task5_Visualizer/data/census/ACS_2017_5yr_MI_CT_AutoOwn.csv"
CensusData      <- "ACS_2017_5yr_CA_CT_AutoOwn.csv"
# hh_file         <- "E:/Projects/Clients/SEMCOG/Tasks/Task5_Visualizer/data/activitySim_400k_hh/final_households.csv"
hh_file         <- "final_households.csv"
hh_file         <- paste("householdData_", MAX_ITER, ".csv", sep = "")
syn_hh_dir      <- paste(ABM_DIR, "/input/popsyn", sep="")
syn_hh_file     <- "households.csv"
# ct_shp_file     <- "E:/Projects/Clients/SEMCOG/Tasks/Task5_Visualizer/data/census/tl_2017_26_tract/tl_2017_26_tract.shp"
ct_shp_file     <- "tl_2017_06_tract.shp"

maz_to_ct_xwalk_file <- "census_tracts_mazs_tazs_v2.2.csv"


setwd(ABM_OUTPUT_DIR)
hh <- read.csv(hh_file)

setwd(syn_hh_dir)
syn_hh <- read.csv(syn_hh_file)

setwd(CENSUS_DIR)
census <- read.csv(CensusData, stringsAsFactors = F)

setwd(ZONES_DIR)
maz_to_ct_xwalk <- read.csv(maz_to_ct_xwalk_file, stringsAsFactors = F)

setwd(ZONES_DIR)
# taz_shp <- shapefile(SHP_FILE_NAME)
ct_shp <- shapefile(ct_shp_file)

setwd(ABM_SUMMARY_DIR) # output dir

ct_shp <- spTransform(ct_shp, CRS("+proj=longlat +ellps=GRS80"))

# Removing GQ households to match Census data
hh$TYPE <- syn_hh$TYPE[match(hh$hh_id, syn_hh$HHID)]
hh <- hh[hh$TYPE == 1,]

# Scaling numbers to full sample
hh$finalweight <- 1/hh$sampleRate
hh$hasZeroAutos <- ifelse(hh$autos==0, 1, 0)
hh$hasZeroAutosWeighted <- hh$hasZeroAutos * hh$finalweight

# using crosswalk to match home maz to census tract
hh$tract_id <- maz_to_ct_xwalk$CTIDFP10[match(hh$home_mgra, maz_to_ct_xwalk$MAZSEQ)]

# Aggregating by census tract
num_hh_per_tract <- aggregate(hh$finalweight, by=list(Category=hh$tract_id), FUN=sum)
zero_auto_hh_by_CT <- aggregate(hh$hasZeroAutosWeighted, by=list(Category=hh$tract_id), FUN=sum)
names(zero_auto_hh_by_CT)[names(zero_auto_hh_by_CT)=="Category"] <- "tract_id"
names(zero_auto_hh_by_CT)[names(zero_auto_hh_by_CT)=="x"] <- "ZeroAutoHH"
zero_auto_hh_by_CT$HH <- num_hh_per_tract$x
model <- zero_auto_hh_by_CT

# remove non-included tracts
ct_shp$GEOID <- as.numeric(ct_shp$GEOID)
ct_shp <- ct_shp[ct_shp$GEOID %in% model$tract_id,]

# Create DF with model and census
names(model)[names(model)=="HH"] <- "Model_HH"
names(model)[names(model)=="ZeroAutoHH"] <- "Model_A0"

census$Census_Auto0Prop <- (census$Census_A0/census$Census_HH)*100
census[is.na(census)] <- 0

model$Model_Auto0Prop <- (model$Model_A0/model$Model_HH)*100
model[is.na(model)] <- 0

df <- census %>%
  left_join(model, by = c("TractID"="tract_id")) %>%
  mutate(Diff_ZeroAuto = Model_Auto0Prop - Census_Auto0Prop)
df[is.na(df)] <- 0

#Copy plot variable to SHP
ct_shp@data <- ct_shp@data %>%
  left_join(df, by = c("GEOID"="TractID"))
ct_shp@data[is.na(ct_shp@data)] <- 0

# Create Map
ct_shp <- ct_shp[!is.na(ct_shp@data$Diff_ZeroAuto),]
ct_shp@data$textComment1 <- paste("Total Census HH: ", ct_shp$Census_HH, sep = "")
ct_shp@data$textComment2 <- ifelse(ct_shp@data$Diff_ZeroAuto<0,'Model under predicts by',
                                     ifelse(ct_shp@data$Diff_ZeroAuto==0,"Model correct",'Model over predicts by'))

writeOGR(ct_shp, ABM_SUMMARY_DIR, sub(".shp", "", CT_ZERO_AUTO_FILE_NAME), driver="ESRI Shapefile", check_exists = TRUE, overwrite_layer = TRUE)

# labels <- sprintf(
#   "<strong>%s</strong><br/><strong>%s %.2f %s</strong><br/> %s",
#   ct_shp@data$CensusTract, ct_shp@data$textComment2, ct_shp@data$Diff_ZeroAuto, "%", ct_shp@data$textComment1
# ) %>% lapply(htmltools::HTML)
# 
# 
# bins <- c(-Inf, -100, -75, -50, -25, -5, 5, 25, 50, 75, 100, Inf)
# pal <- colorBin("PiYG", domain = ct_shp@data$Diff_ZeroAuto, na.color="transparent", bins = bins)
# 
# m <- leaflet(data = ct_shp)%>%
#   addTiles() %>%
#   addProviderTiles(providers$OpenStreetMap, group = "Background Map") %>%
#   addLayersControl(
#     overlayGroups = "Background Map", options = layersControlOptions(collapsed = FALSE)
#   ) %>%
#   addPolygons(group='ZeroCarDiff',
#               fillColor = ~pal(Diff_ZeroAuto),
#               weight = 0.2,
#               opacity = 1,
#               color = "gray",
#               stroke=T,
#               dashArray = "5, 1",
#               fillOpacity = 0.7,
#               highlight = highlightOptions(
#                 weight = 1,
#                 color = "blue",
#                 dashArray = "",
#                 fillOpacity = 0.7,
#                 bringToFront = TRUE),
#               label = labels,
#               labelOptions = labelOptions(
#                 style = list("font-weight" = "normal", padding = "3px 8px"),
#                 textsize = "15px",
#                 direction = "auto")) %>%
#   addLegend(pal = pal, values = ~density, opacity = 0.7, title = "Estimated(%) - Observed(%) Bins",
#             position = "bottomright")
# 
# 
# # Output HTML
# saveWidget(m, file=paste(Out_Dir, "CT_ZeroAutoDiff_Census_vs_Model.html", sep = "/"), selfcontained = TRUE)
# 
# 
# # Write tabular CSV
# write.csv(df, paste(Out_Dir, "Data_CT_ZeroAutoDiff_Census_vs_Model.csv", sep = "/"), row.names = F)
# 
# print("Map Created!")

end_time <- Sys.time()
end_time - start_time
cat("\n Script finished, run time: ", end_time - start_time, "sec \n")
