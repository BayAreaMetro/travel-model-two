#####################################################################################
# Script to create highway validation inputs
#
#####################################################################################

### LIBRARIES
library(dplyr)
library(foreign)
library(reshape)

### USER INPUTS
## Paths
if (Sys.getenv("USERNAME") == "lzorn") {
  USERPROFILE     <- gsub("\\\\","/", Sys.getenv("USERPROFILE"))
  RUN_NAME        <- "2015_01_lmz_04"
  
  BOX_TM2         <- file.path(USERPROFILE, "Box", "Modeling and Surveys", "Development", "Travel Model Two Development")
  tm2CountsDir    <- file.path(BOX_TM2,     "Observed Data", "Traffic Counts")
  BOX_SHAREDATA   <- file.path(USERPROFILE, "Box", "Modeling and Surveys", "Development", "Share Data")
  pemsDataDir     <- file.path(BOX_SHAREDATA,     "pems-typical-weekday")
  volumeDir       <- file.path("D:", "Projects_TM2", RUN_NAME, "hwy")
  volOutput       <- file.path(BOX_TM2, "Calibration & Validation", "Round 2", "Calibration Spreadsheets", RUN_NAME)
} else {
  workingDir      <- "E:/projects/clients/mtc"
  tm2CountsDir    <- file.path(workingDir, "data", "ObservedData")
  pemsDataDir     <- file.path(workingDir, "data", "ObservedData")
  cntOutput       <- file.path(workingDir, "data", "ObservedData")
  volumeDir       <- file.path(workingDir, "Calibration_2015", "Spreadsheets", "HighwaySummary", "081318")
  volOutput       <- file.path(workingDir, "Calibration_2015", "Spreadsheets", "HighwaySummary", "081318")
}

### Read Files
pems_period <- read.csv(file.path(pemsDataDir,  "pems_period.csv"), as.is = T)
pems_xwalk  <- read.csv(file.path(tm2CountsDir, "pems_station_to_TM2_links_crosswalk.csv"), as.is = T)
colnames(pems_xwalk)[colnames(pems_xwalk)=="station"] <- "pems_id"
#pems_xwalk  <- read.csv(paste(obsDataDir, "pems_model_xwalk.csv", sep = "\\"), as.is = T)
#pems_xwalk  <- pems_xwalk %>%
#  mutate(A_B = paste(as.character(a), as.character(b), sep = "_")) %>%
#  mutate(pems_id = pems.id)

#volumes     <- read.csv(paste(volumeDir, "msamerge3.csv", sep = "\\"), as.is = T)

vol_EA <- read.dbf(file.path(volumeDir, "loadEA.dbf"), as.is = T)
vol_AM <- read.dbf(file.path(volumeDir, "loadAM.dbf"), as.is = T)
vol_MD <- read.dbf(file.path(volumeDir, "loadMD.dbf"), as.is = T)
vol_PM <- read.dbf(file.path(volumeDir, "loadPM.dbf"), as.is = T)
vol_EV <- read.dbf(file.path(volumeDir, "loadEV.dbf"), as.is = T)

#write.csv(vol_EA, paste(volumeDir, "vol_EA.csv", sep = "\\"), row.names = F)
#write.csv(vol_AM, paste(volumeDir, "vol_AM.csv", sep = "\\"), row.names = F)
#write.csv(vol_MD, paste(volumeDir, "vol_MD.csv", sep = "\\"), row.names = F)
#write.csv(vol_PM, paste(volumeDir, "vol_PM.csv", sep = "\\"), row.names = F)
#write.csv(vol_EV, paste(volumeDir, "vol_EV.csv", sep = "\\"), row.names = F)

vol_EA <- vol_EA %>%
  mutate(OLD_A_B = paste(as.character(OLD_A), as.character(OLD_B), sep = "_")) %>%
  mutate(VolEA_tot = V1_1+V2_1+V3_1+V4_1+V5_1+V6_1+V7_1+V8_1+V9_1+V10_1+MAZMAZVOL) %>%
  left_join(pems_xwalk[,c("A_B", "pems_id")], by = c("OLD_A_B" = "A_B")) %>%
  mutate(PEMSID = ifelse(is.na(pems_id), 0, pems_id)) %>%
  select(A, B, OLD_A, OLD_B, OLD_A_B, PEMSID, FT, VolEA_tot)

vol_AM <- vol_AM %>%
  mutate(OLD_A_B = paste(as.character(OLD_A), as.character(OLD_B), sep = "_")) %>%
  mutate(VolAM_tot = V1_1+V2_1+V3_1+V4_1+V5_1+V6_1+V7_1+V8_1+V9_1+V10_1+MAZMAZVOL) %>%
  left_join(pems_xwalk[,c("A_B", "pems_id")], by = c("OLD_A_B" = "A_B")) %>%
  mutate(PEMSID = ifelse(is.na(pems_id), 0, pems_id)) %>%
  select(A, B, OLD_A, OLD_B, OLD_A_B, PEMSID, FT, VolAM_tot)

vol_MD <- vol_MD %>%
  mutate(OLD_A_B = paste(as.character(OLD_A), as.character(OLD_B), sep = "_")) %>%
  mutate(VolMD_tot = V1_1+V2_1+V3_1+V4_1+V5_1+V6_1+V7_1+V8_1+V9_1+V10_1+MAZMAZVOL) %>%
  left_join(pems_xwalk[,c("A_B", "pems_id")], by = c("OLD_A_B" = "A_B")) %>%
  mutate(PEMSID = ifelse(is.na(pems_id), 0, pems_id)) %>%
  select(A, B, OLD_A, OLD_B, OLD_A_B, PEMSID, FT, VolMD_tot)

vol_PM <- vol_PM %>%
  mutate(OLD_A_B = paste(as.character(OLD_A), as.character(OLD_B), sep = "_")) %>%
  mutate(VolPM_tot = V1_1+V2_1+V3_1+V4_1+V5_1+V6_1+V7_1+V8_1+V9_1+V10_1+MAZMAZVOL) %>%
  left_join(pems_xwalk[,c("A_B", "pems_id")], by = c("OLD_A_B" = "A_B")) %>%
  mutate(PEMSID = ifelse(is.na(pems_id), 0, pems_id)) %>%
  select(A, B, OLD_A, OLD_B, OLD_A_B, PEMSID, FT, VolPM_tot)

vol_EV <- vol_EV %>%
  mutate(OLD_A_B = paste(as.character(OLD_A), as.character(OLD_B), sep = "_")) %>%
  mutate(VolEV_tot = V1_1+V2_1+V3_1+V4_1+V5_1+V6_1+V7_1+V8_1+V9_1+V10_1+MAZMAZVOL) %>%
  left_join(pems_xwalk[,c("A_B", "pems_id")], by = c("OLD_A_B" = "A_B")) %>%
  mutate(PEMSID = ifelse(is.na(pems_id), 0, pems_id)) %>%
  select(A, B, OLD_A, OLD_B, OLD_A_B, PEMSID, FT, VolEV_tot)

volumes <- vol_AM
volumes$VolEA_tot <- vol_EA$VolEA_tot[match(volumes$OLD_A_B, vol_EA$OLD_A_B)]
volumes$VolMD_tot <- vol_MD$VolMD_tot[match(volumes$OLD_A_B, vol_MD$OLD_A_B)]
volumes$VolPM_tot <- vol_PM$VolPM_tot[match(volumes$OLD_A_B, vol_PM$OLD_A_B)]
volumes$VolEV_tot <- vol_EV$VolEV_tot[match(volumes$OLD_A_B, vol_EV$OLD_A_B)]
volumes[is.na(volumes)] <- 0

#volumes <- data.frame(vol_EA, vol_AM$VolAM_tot, vol_MD$VolMD_tot, vol_PM$VolPM_tot, vol_EV$VolEV_tot)
write.csv(volumes[volumes$PEMSID>0, ], file.path(volumeDir, "total_volumes.csv"), row.names = F)
  
# subset links with valid pemsid
#volumes_pems <- volumes[volumes$PEMSID>0, ]
volumes     <- read.csv(file.path(volumeDir, "total_volumes.csv"), as.is = T)
volumes_pems <- volumes

## processing the pems_period data to subset only the latest year PEMS count
pems_period <- pems_period %>%
  mutate(station_year = paste(as.character(station), as.character(year), sep = "_"))
pems_period_latestyear <- aggregate(year ~ station, pems_period, function(x) max(x))
pems_period_latestyear <- pems_period_latestyear %>% 
  mutate(station_year = paste(as.character(station), as.character(year), sep = "_"))
pems_period_final <- pems_period %>% 
  filter(station_year %in% pems_period_latestyear$station_year)

## check for those PEMSID whose latest year do not have all time periods. Fix by taking the next latest year
check_pems <- data.frame(table(pems_period_final$station_year))
pems_2ndyear <- check_pems %>% 
  filter(Freq<5)
pems_2ndyear_stations <- pems_period_latestyear %>% 
  filter(station_year %in% pems_2ndyear$Var1)
pems_2ndyear_all <- pems_period %>% 
  filter(station %in% pems_2ndyear_stations$station)
pems_2ndyear_all <- pems_2ndyear_all %>% 
  select(station, year) %>% 
  mutate(counter=1)

pems_2ndyear_pivot <- dcast(pems_2ndyear_all, station ~ year, value.var = "counter", fun.aggregate = length)
pems_2ndyear_pivot <- pems_2ndyear_pivot %>% 
  mutate(ind_2005=if_else(`2005`==5,1,0)) %>%
  mutate(ind_2006=if_else(`2006`==5,1,0)) %>%
  mutate(ind_2007=if_else(`2007`==5,1,0)) %>%
  mutate(ind_2008=if_else(`2008`==5,1,0)) %>%
  mutate(ind_2009=if_else(`2009`==5,1,0)) %>%
  mutate(ind_2010=if_else(`2010`==5,1,0)) %>%
  mutate(ind_2011=if_else(`2011`==5,1,0)) %>%
  mutate(ind_2012=if_else(`2012`==5,1,0)) %>%
  mutate(ind_2013=if_else(`2013`==5,1,0)) %>%
  mutate(ind_2014=if_else(`2014`==5,1,0)) %>%
  mutate(ind_2015=if_else(`2015`==5,1,0)) %>% 
  mutate(final_year=if_else(ind_2015==1,2015,if_else(ind_2014==1,2014,if_else(ind_2013==1,2013,if_else(ind_2012==1,2012,if_else(ind_2011==1,2011,if_else(ind_2010==1,2010,if_else(ind_2009==1,2009,if_else(ind_2008==1,2008,if_else(ind_2007==1,2007,if_else(ind_2006==1,2006,if_else(ind_2005==1,2005,0))))))))))))
pems_2ndyear_final <- pems_2ndyear_pivot %>% 
  select(station, final_year)
pems_period_final <- pems_period_final %>% 
  filter(!(station %in% pems_2ndyear_final$station))
pems_2ndyear_final <- pems_2ndyear_final %>% 
  filter(final_year>0) %>% 
  mutate(station_year = paste(as.character(station), as.character(final_year), sep = "_"))
pems_period_final_filtered <- pems_period %>% 
  filter(station_year %in% pems_2ndyear_final$station_year)
pems_period_test <- merge(pems_period_final, pems_period_final_filtered, all = T)

## manually correct PEMSID with multiple time period data for same year
check_pems2 <- check_pems %>% 
  filter(Freq>5)
pems_period_multiPEMS <- pems_period_test %>% 
  filter(station_year %in% check_pems2$Var1)
station_400040 <- pems_period_multiPEMS %>% 
  filter(station==400040) %>% 
  filter(lanes>2)
station_400236 <- pems_period_multiPEMS %>% 
  filter(station==400236) %>% 
  filter(lanes>2)
station_400521 <- pems_period_multiPEMS %>% 
  filter(station==400521) %>% 
  filter(lanes>2)
station_400596 <- pems_period_multiPEMS %>% 
  filter(station==400596) %>% 
  filter(lanes>2)
station_401433 <- pems_period_multiPEMS %>% 
  filter(station==401433) %>% 
  filter(lanes>4)
station_402536 <- pems_period_multiPEMS %>% 
  filter(station==402536) %>% 
  filter(type=="ML")
station_404462 <- pems_period_multiPEMS %>% 
  filter(station==404462) %>% 
  filter(lanes>2)
station_407332 <- pems_period_multiPEMS %>% 
  filter(station==407332) %>% 
  filter(type=="HV")
station_407359 <- pems_period_multiPEMS %>% 
  filter(station==407359) %>% 
  filter(type=="HV")
pems_period_test_2 <- merge(station_400040, merge(station_400236, merge(station_400521, merge(station_400596, merge(station_401433, merge(station_402536, merge(station_404462, merge(station_407332, station_407359, all = T), all = T), all = T), all = T), all = T), all = T), all = T), all = T)
pems_period_test <- pems_period_test %>% 
  filter(!(station_year %in% check_pems2$Var1))
pems_period <- merge(pems_period_test, pems_period_test_2, all=T)

# subset pems by period
pems_EA <- pems_period[pems_period$time_period=="EA",]
pems_AM <- pems_period[pems_period$time_period=="AM",]
pems_MD <- pems_period[pems_period$time_period=="MD",]
pems_PM <- pems_period[pems_period$time_period=="PM",]
pems_EV <- pems_period[pems_period$time_period=="EV",]

volumes_pems$pems_EA <- pems_EA$avg_flow[match(volumes_pems$PEMSID, pems_EA$station)]
volumes_pems$pems_AM <- pems_AM$avg_flow[match(volumes_pems$PEMSID, pems_AM$station)]
volumes_pems$pems_MD <- pems_MD$avg_flow[match(volumes_pems$PEMSID, pems_MD$station)]
volumes_pems$pems_PM <- pems_PM$avg_flow[match(volumes_pems$PEMSID, pems_PM$station)]
volumes_pems$pems_EV <- pems_EV$avg_flow[match(volumes_pems$PEMSID, pems_EV$station)]
volumes_pems$year <- pems_period$year[match(volumes_pems$PEMSID, pems_period$station)]

# changes: keep links with counts > 0.
# calculate total based on all time periods

## Delete all rows with no count data
volumes_pems <- volumes_pems %>% 
  filter(!is.na(year))
volumes_pems <- volumes_pems %>% 
  mutate(VolAM_tot2=if_else(is.na(pems_AM),99999,VolAM_tot)) %>% 
  mutate(VolEA_tot2=if_else(is.na(pems_EA),99999,VolEA_tot)) %>% 
  mutate(VolMD_tot2=if_else(is.na(pems_MD),99999,VolMD_tot)) %>% 
  mutate(VolPM_tot2=if_else(is.na(pems_PM),99999,VolPM_tot)) %>% 
  mutate(VolEV_tot2=if_else(is.na(pems_EV),99999,VolEV_tot))
volumes_pems$VolAM_tot2[volumes_pems$VolAM_tot2 == 99999] <- NA
volumes_pems$VolEA_tot2[volumes_pems$VolEA_tot2 == 99999] <- NA
volumes_pems$VolMD_tot2[volumes_pems$VolMD_tot2 == 99999] <- NA
volumes_pems$VolPM_tot2[volumes_pems$VolPM_tot2 == 99999] <- NA
volumes_pems$VolEV_tot2[volumes_pems$VolEV_tot2 == 99999] <- NA

volumes_pems1 <- select(volumes_pems, A, B, OLD_A, OLD_B, OLD_A_B, PEMSID, FT, year, VolEA_tot2, VolAM_tot2, VolMD_tot2, VolPM_tot2, VolEV_tot2)
colnames(volumes_pems1) <- c("a","b", "old_a", "old_b", "old_a_b", "pemsid","ft", "year", "EA", "AM", "MD", "PM", "EV")
volumes_pems1 <- volumes_pems1 %>% 
  rowwise() %>% 
  mutate(Total=sum(EA,AM,MD,PM,EV, na.rm=TRUE)) %>% 
  ungroup()
temp1 <- melt(data.frame(volumes_pems1), id = c("a", "b", "old_a", "old_b", "old_a_b", "pemsid", "ft", "year"))
colnames(temp1) <- c("a","b", "old_a", "old_b", "old_a_b", "pemsid","ft", "year", "time_period", "volume")

volumes_pems2 <- select(volumes_pems, A, B, OLD_A, OLD_B, OLD_A_B, PEMSID, FT, year, pems_EA, pems_AM, pems_MD, pems_PM, pems_EV)
colnames(volumes_pems2) <- c("a","b", "old_a", "old_b", "old_a_b", "pemsid","ft", "year", "EA", "AM", "MD", "PM", "EV")
volumes_pems2 <- volumes_pems2 %>% 
  rowwise() %>% 
  mutate(Total=sum(EA,AM,MD,PM,EV, na.rm=TRUE)) %>% 
  ungroup()
temp2 <- melt(data.frame(volumes_pems2), id = c("a", "b", "old_a", "old_b", "old_a_b", "pemsid", "ft", "year"))
colnames(temp2) <- c("a","b", "old_a", "old_b", "old_a_b", "pemsid","ft", "year", "time_period", "count")

comparison <- data.frame(temp1, temp2$count)
colnames(comparison) <- c("a","b", "old_a", "old_b", "old_a_b", "pemsid","ft", "year","time_period","volume","count")
comparison[is.na(comparison)] <- 0
comparison <- comparison %>%
  filter(count>0)

# manually fix links with multiple PEMSID based on lowest count volume difference
comparison_EA <- comparison[comparison$time_period=="EA",]
comparison_AM <- comparison[comparison$time_period=="AM",]
comparison_MD <- comparison[comparison$time_period=="MD",]
comparison_PM <- comparison[comparison$time_period=="PM",]
comparison_EV <- comparison[comparison$time_period=="EV",]
comparison_total <- comparison[comparison$time_period=="Total",]

# EA
dup_links_EA <- data.frame(table(comparison_EA$old_a_b))
dup_links_EA <- dup_links_EA %>% 
  filter(Freq>1)
comparison_EA_dup <- comparison_EA %>% 
  filter(old_a_b %in% dup_links_EA$Var1) %>% 
  mutate(gap=abs(volume-count))
comparison_EA_dup2 <- comparison_EA_dup %>% 
  group_by(old_a_b) %>% 
  filter(gap == min(gap))
comparison_EA_dup2$gap <- NULL
comparison_EA1 <- comparison_EA %>% 
  filter(!(old_a_b %in% comparison_EA_dup2$old_a_b))
comparison_EA <- merge(comparison_EA1, comparison_EA_dup2, all=T)

# AM
dup_links_AM <- data.frame(table(comparison_AM$old_a_b))
dup_links_AM <- dup_links_AM %>% 
  filter(Freq>1)
comparison_AM_dup <- comparison_AM %>% 
  filter(old_a_b %in% dup_links_AM$Var1) %>% 
  mutate(gap=abs(volume-count))
comparison_AM_dup2 <- comparison_AM_dup %>% 
  group_by(old_a_b) %>% 
  filter(gap == min(gap))
comparison_AM_dup2$gap <- NULL
comparison_AM1 <- comparison_AM %>% 
  filter(!(old_a_b %in% comparison_AM_dup2$old_a_b))
comparison_AM <- merge(comparison_AM1, comparison_AM_dup2, all=T)

# MD
dup_links_MD <- data.frame(table(comparison_MD$old_a_b))
dup_links_MD <- dup_links_MD %>% 
  filter(Freq>1)
comparison_MD_dup <- comparison_MD %>% 
  filter(old_a_b %in% dup_links_MD$Var1) %>% 
  mutate(gap=abs(volume-count))
comparison_MD_dup2 <- comparison_MD_dup %>% 
  group_by(old_a_b) %>% 
  filter(gap == min(gap))
comparison_MD_dup2$gap <- NULL
comparison_MD1 <- comparison_MD %>% 
  filter(!(old_a_b %in% comparison_MD_dup2$old_a_b))
comparison_MD <- merge(comparison_MD1, comparison_MD_dup2, all=T)

# PM
dup_links_PM <- data.frame(table(comparison_PM$old_a_b))
dup_links_PM <- dup_links_PM %>% 
  filter(Freq>1)
comparison_PM_dup <- comparison_PM %>% 
  filter(old_a_b %in% dup_links_PM$Var1) %>% 
  mutate(gap=abs(volume-count))
comparison_PM_dup2 <- comparison_PM_dup %>% 
  group_by(old_a_b) %>% 
  filter(gap == min(gap))
comparison_PM_dup2$gap <- NULL
comparison_PM1 <- comparison_PM %>% 
  filter(!(old_a_b %in% comparison_PM_dup2$old_a_b))
comparison_PM <- merge(comparison_PM1, comparison_PM_dup2, all=T)

# EV
dup_links_EV <- data.frame(table(comparison_EV$old_a_b))
dup_links_EV <- dup_links_EV %>% 
  filter(Freq>1)
comparison_EV_dup <- comparison_EV %>% 
  filter(old_a_b %in% dup_links_EV$Var1) %>% 
  mutate(gap=abs(volume-count))
comparison_EV_dup2 <- comparison_EV_dup %>% 
  group_by(old_a_b) %>% 
  filter(gap == min(gap))
comparison_EV_dup2$gap <- NULL
comparison_EV1 <- comparison_EV %>% 
  filter(!(old_a_b %in% comparison_EV_dup2$old_a_b))
comparison_EV <- merge(comparison_EV1, comparison_EV_dup2, all=T)

# Total
dup_links_total <- data.frame(table(comparison_total$old_a_b))
dup_links_total <- dup_links_total %>% 
  filter(Freq>1)
comparison_total_dup <- comparison_total %>% 
  filter(old_a_b %in% dup_links_total$Var1) %>% 
  mutate(gap=abs(volume-count))
comparison_total_dup2 <- comparison_total_dup %>% 
  group_by(old_a_b) %>% 
  filter(gap == min(gap))
comparison_total_dup2$gap <- NULL
comparison_total1 <- comparison_total %>% 
  filter(!(old_a_b %in% comparison_total_dup2$old_a_b))
comparison_total <- merge(comparison_total1, comparison_total_dup2, all=T)

comparison <- merge(comparison_EA, merge(comparison_AM, merge(comparison_MD, merge(comparison_PM, merge(comparison_EV, comparison_total, all=T), all=T), all=T), all=T), all=T)

# write final output
write.csv(comparison, paste(OutputDir, "volume_vs_count.csv", sep = "\\"), row.names = F)

## finish