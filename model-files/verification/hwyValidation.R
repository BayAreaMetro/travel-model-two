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
workingDir <- "E:/projects/clients/mtc"
obsDataDir <- paste(workingDir, "data/ObservedData", sep = "\\")
cntOutput  <- paste(workingDir, "data/ObservedData", sep = "\\")
volumeDir  <- paste(workingDir, "Calibration_2015/Spreadsheets/HighwaySummary/081318", sep = "\\")
volOutput  <- paste(workingDir, "Calibration_2015/Spreadsheets/HighwaySummary/081318", sep = "\\")


### Read Files
pems_period <- read.csv(paste(obsDataDir, "pems_period.csv", sep = "\\"), as.is = T)
pems_xwalk  <- read.csv(paste(obsDataDir, "pems_station_to_TM2_links_crosswalk.csv", sep = "\\"), as.is = T)
colnames(pems_xwalk)[colnames(pems_xwalk)=="station"] <- "pems_id"
#pems_xwalk  <- read.csv(paste(obsDataDir, "pems_model_xwalk.csv", sep = "\\"), as.is = T)
#pems_xwalk  <- pems_xwalk %>%
#  mutate(A_B = paste(as.character(a), as.character(b), sep = "_")) %>%
#  mutate(pems_id = pems.id)

#volumes     <- read.csv(paste(volumeDir, "msamerge3.csv", sep = "\\"), as.is = T)

vol_EA <- read.dbf(paste(volumeDir, "loadEA.dbf", sep = "\\"), as.is = T)
vol_AM <- read.dbf(paste(volumeDir, "loadAM.dbf", sep = "\\"), as.is = T)
vol_MD <- read.dbf(paste(volumeDir, "loadMD.dbf", sep = "\\"), as.is = T)
vol_PM <- read.dbf(paste(volumeDir, "loadPM.dbf", sep = "\\"), as.is = T)
vol_EV <- read.dbf(paste(volumeDir, "loadEV.dbf", sep = "\\"), as.is = T)

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
write.csv(volumes[volumes$PEMSID>0, ], paste(volumeDir, "total_volumes.csv", sep = "\\"), row.names = F)
  
# subset links with valid pemsid
#volumes_pems <- volumes[volumes$PEMSID>0, ]
volumes     <- read.csv(paste(volumeDir, "total_volumes.csv", sep = "\\"), as.is = T)
volumes_pems <- volumes


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

volumes_pems1 <- select(volumes_pems, A, B, OLD_A, OLD_B, PEMSID, FT, year, VolEA_tot, VolAM_tot, VolMD_tot, VolPM_tot, VolEV_tot)
colnames(volumes_pems1) <- c("a","b", "old_a", "old_b","pemsid","ft", "year", "EA", "AM", "MD", "PM", "EV")
volumes_pems1[is.na(volumes_pems1)] <- 0
volumes_pems1 <- volumes_pems1 %>%
  mutate(Total = EA+AM+MD+PM+EV)
temp1 <- melt(volumes_pems1, id = c("a", "b", "old_a", "old_b", "pemsid", "ft", "year"))
colnames(temp1) <- c("a","b", "old_a", "old_b","pemsid","ft", "year", "time_period", "volume")
volumes_pems2 <- select(volumes_pems, A, B, OLD_A, OLD_B, PEMSID, FT, year, pems_EA, pems_AM, pems_MD, pems_PM, pems_EV)
colnames(volumes_pems2) <- c("a","b", "old_a", "old_b","pemsid","ft", "year", "EA", "AM", "MD", "PM", "EV")
volumes_pems2[is.na(volumes_pems2)] <- 0
volumes_pems2 <- volumes_pems2 %>%
  mutate(Total = EA+AM+MD+PM+EV)
temp2 <- melt(volumes_pems2, id = c("a", "b", "old_a", "old_b", "pemsid", "ft", "year"))
colnames(temp2) <- c("a","b", "old_a", "old_b","pemsid","ft", "year", "time_period", "count")

comparison <- data.frame(temp1, temp2$count)
colnames(comparison) <- c("a","b", "old_a", "old_b","pemsid","ft", "year","time_period","volume","count")
comparison[is.na(comparison)] <- 0
comparison <- comparison %>%
  filter(volume>0 & count>0)

# write final output
write.csv(comparison, paste(volOutput, "volume_vs_count.csv", sep = "\\"), row.names = F)









## finish