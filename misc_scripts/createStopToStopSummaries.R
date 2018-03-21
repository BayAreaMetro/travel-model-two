#####################################################################################
# Script to create BART stop-to-stop summaries
#
#####################################################################################

### LIBRARIES
library(dplyr)
library(foreign)
library(reshape2)

### USER INPUTS
## Paths
workingDir <- "E:/projects/clients/mtc"
obsDataDir <- paste(workingDir, "data/Observed Data Box Dec 14 2017/Transit/BART", sep = "/")
modelDir   <- paste(workingDir, "2015_Test/trn", sep = "/")
outputDir  <- paste(workingDir, "2015_Test/StopToStopSummary", sep = "/")


### Read Node Crosswalk and Station Codes
node_xwalk <- read.csv(paste(obsDataDir, "bartNodes2015.csv", sep = "/"), stringsAsFactors = F)
stationCodes <- read.csv(paste(obsDataDir, "stationCodes.csv", sep = "/"), stringsAsFactors = F)

### Read Model Output
EA_Set2 <- read.dbf(paste(modelDir, "mtc_stop2stop_EA_SET2.dbf", sep = "\\"), as.is = T)
EA_Set3 <- read.dbf(paste(modelDir, "mtc_stop2stop_EA_SET3.dbf", sep = "\\"), as.is = T)

AM_Set2 <- read.dbf(paste(modelDir, "mtc_stop2stop_AM_SET2.dbf", sep = "\\"), as.is = T)
AM_Set3 <- read.dbf(paste(modelDir, "mtc_stop2stop_AM_SET3.dbf", sep = "\\"), as.is = T)

MD_Set2 <- read.dbf(paste(modelDir, "mtc_stop2stop_MD_SET2.dbf", sep = "\\"), as.is = T)
MD_Set3 <- read.dbf(paste(modelDir, "mtc_stop2stop_MD_SET3.dbf", sep = "\\"), as.is = T)

PM_Set2 <- read.dbf(paste(modelDir, "mtc_stop2stop_PM_SET2.dbf", sep = "\\"), as.is = T)
PM_Set3 <- read.dbf(paste(modelDir, "mtc_stop2stop_PM_SET3.dbf", sep = "\\"), as.is = T)

EV_Set2 <- read.dbf(paste(modelDir, "mtc_stop2stop_EV_SET2.dbf", sep = "\\"), as.is = T)
EV_Set3 <- read.dbf(paste(modelDir, "mtc_stop2stop_EV_SET3.dbf", sep = "\\"), as.is = T)


### Add 2-digit from stop IDs to model output tables
EA_Set2$FromStop <- node_xwalk$Station_Code2[match(EA_Set2$FromNode, node_xwalk$NODE)]
EA_Set3$FromStop <- node_xwalk$Station_Code2[match(EA_Set3$FromNode, node_xwalk$NODE)]

AM_Set2$FromStop <- node_xwalk$Station_Code2[match(AM_Set2$FromNode, node_xwalk$NODE)]
AM_Set3$FromStop <- node_xwalk$Station_Code2[match(AM_Set3$FromNode, node_xwalk$NODE)]

MD_Set2$FromStop <- node_xwalk$Station_Code2[match(MD_Set2$FromNode, node_xwalk$NODE)]
MD_Set3$FromStop <- node_xwalk$Station_Code2[match(MD_Set3$FromNode, node_xwalk$NODE)]

PM_Set2$FromStop <- node_xwalk$Station_Code2[match(PM_Set2$FromNode, node_xwalk$NODE)]
PM_Set3$FromStop <- node_xwalk$Station_Code2[match(PM_Set3$FromNode, node_xwalk$NODE)]

EV_Set2$FromStop <- node_xwalk$Station_Code2[match(EV_Set2$FromNode, node_xwalk$NODE)]
EV_Set3$FromStop <- node_xwalk$Station_Code2[match(EV_Set3$FromNode, node_xwalk$NODE)]


### Add 2-digit to stop IDs to model output tables
EA_Set2$ToStop <- node_xwalk$Station_Code2[match(EA_Set2$ToNode, node_xwalk$NODE)]
EA_Set3$ToStop <- node_xwalk$Station_Code2[match(EA_Set3$ToNode, node_xwalk$NODE)]

AM_Set2$ToStop <- node_xwalk$Station_Code2[match(AM_Set2$ToNode, node_xwalk$NODE)]
AM_Set3$ToStop <- node_xwalk$Station_Code2[match(AM_Set3$ToNode, node_xwalk$NODE)]

MD_Set2$ToStop <- node_xwalk$Station_Code2[match(MD_Set2$ToNode, node_xwalk$NODE)]
MD_Set3$ToStop <- node_xwalk$Station_Code2[match(MD_Set3$ToNode, node_xwalk$NODE)]

PM_Set2$ToStop <- node_xwalk$Station_Code2[match(PM_Set2$ToNode, node_xwalk$NODE)]
PM_Set3$ToStop <- node_xwalk$Station_Code2[match(PM_Set3$ToNode, node_xwalk$NODE)]

EV_Set2$ToStop <- node_xwalk$Station_Code2[match(EV_Set2$ToNode, node_xwalk$NODE)]
EV_Set3$ToStop <- node_xwalk$Station_Code2[match(EV_Set3$ToNode, node_xwalk$NODE)]


### Set up grouping variable 
EA_Set2$From_To <- paste(EA_Set2$FromStop, "_", EA_Set2$ToStop, sep = "")
EA_Set3$From_To <- paste(EA_Set3$FromStop, "_", EA_Set3$ToStop, sep = "")

AM_Set2$From_To <- paste(AM_Set2$FromStop, "_", AM_Set2$ToStop, sep = "")
AM_Set3$From_To <- paste(AM_Set3$FromStop, "_", AM_Set3$ToStop, sep = "")

MD_Set2$From_To <- paste(MD_Set2$FromStop, "_", MD_Set2$ToStop, sep = "")
MD_Set3$From_To <- paste(MD_Set3$FromStop, "_", MD_Set3$ToStop, sep = "")

PM_Set2$From_To <- paste(PM_Set2$FromStop, "_", PM_Set2$ToStop, sep = "")
PM_Set3$From_To <- paste(PM_Set3$FromStop, "_", PM_Set3$ToStop, sep = "")

EV_Set2$From_To <- paste(EV_Set2$FromStop, "_", EV_Set2$ToStop, sep = "")
EV_Set3$From_To <- paste(EV_Set3$FromStop, "_", EV_Set3$ToStop, sep = "")


### Create daily ridership file from outputs
EA_Set2 <- EA_Set2 %>%
  group_by(From_To) %>%
  summarise(VOL_EA2 = sum(VOL)) %>%
  ungroup()
EA_Set3 <- EA_Set3 %>%
  group_by(From_To) %>%
  summarise(VOL_EA3 = sum(VOL)) %>%
  ungroup()

AM_Set2 <- AM_Set2 %>%
  group_by(From_To) %>%
  summarise(VOL_AM2 = sum(VOL)) %>%
  ungroup()
AM_Set3 <- AM_Set3 %>%
  group_by(From_To) %>%
  summarise(VOL_AM3 = sum(VOL)) %>%
  ungroup()

MD_Set2 <- MD_Set2 %>%
  group_by(From_To) %>%
  summarise(VOL_MD2 = sum(VOL)) %>%
  ungroup()
MD_Set3 <- MD_Set3 %>%
  group_by(From_To) %>%
  summarise(VOL_MD3 = sum(VOL)) %>%
  ungroup()

PM_Set2 <- PM_Set2 %>%
  group_by(From_To) %>%
  summarise(VOL_PM2 = sum(VOL)) %>%
  ungroup()
PM_Set3 <- PM_Set3 %>%
  group_by(From_To) %>%
  summarise(VOL_PM3 = sum(VOL)) %>%
  ungroup()

EV_Set2 <- EV_Set2 %>%
  group_by(From_To) %>%
  summarise(VOL_EV2 = sum(VOL)) %>%
  ungroup()
EV_Set3 <- EV_Set3 %>%
  group_by(From_To) %>%
  summarise(VOL_EV3 = sum(VOL)) %>%
  ungroup()

### Create final dataframe fo daily stop-to-stop ridership
df <- expand.grid(From = stationCodes$Station_Code2, To = stationCodes$Station_Code2)
df$From_To <- paste(df$From, "_", df$To, sep = "")

#   join model summaries
df <- df %>%
  left_join(EA_Set2, by = c("From_To" = "From_To")) %>%
  left_join(EA_Set3, by = c("From_To" = "From_To")) %>%
  left_join(AM_Set2, by = c("From_To" = "From_To")) %>%
  left_join(AM_Set3, by = c("From_To" = "From_To")) %>%
  left_join(MD_Set2, by = c("From_To" = "From_To")) %>%
  left_join(MD_Set3, by = c("From_To" = "From_To")) %>%
  left_join(PM_Set2, by = c("From_To" = "From_To")) %>%
  left_join(PM_Set3, by = c("From_To" = "From_To")) %>%
  left_join(EV_Set2, by = c("From_To" = "From_To")) %>%
  left_join(EV_Set3, by = c("From_To" = "From_To")) 

df[is.na(df)] <- 0

df <- df %>%
  mutate(Daily_Vol = VOL_EA2 + VOL_EA3 + VOL_AM2 + VOL_AM3 + VOL_MD2 + VOL_MD3 + VOL_PM2 + VOL_PM3 + VOL_EV2 + VOL_EV3) %>%
  mutate(EA_Vol = VOL_EA2 + VOL_EA3) %>%
  mutate(AM_Vol = VOL_AM2 + VOL_AM3) %>%
  mutate(MD_Vol = VOL_MD2 + VOL_MD3) %>%
  mutate(PM_Vol = VOL_PM2 + VOL_PM3) %>%
  mutate(EV_Vol = VOL_EV2 + VOL_EV3) 

#  select(From, To, Daily_Vol)

#   create final OD tables
df_Daily <- dcast(df[,c("From", "To", "Daily_Vol")], From ~ To)
df_EA <- dcast(df[,c("From", "To", "EA_Vol")], From ~ To)
df_AM <- dcast(df[,c("From", "To", "AM_Vol")], From ~ To)
df_MD <- dcast(df[,c("From", "To", "MD_Vol")], From ~ To)
df_PM <- dcast(df[,c("From", "To", "PM_Vol")], From ~ To)
df_EV <- dcast(df[,c("From", "To", "EV_Vol")], From ~ To)


### Write outputs
write.table(df_Daily, paste(outputDir, "model_stop2stop_summary.csv", sep = "/"), sep = ",", row.names = F)
write.table("EA", paste(outputDir, "model_stop2stop_summary.csv", sep = "/"), sep = ",", row.names = F, append = T)
write.table(df_EA, paste(outputDir, "model_stop2stop_summary.csv", sep = "/"), sep = ",", row.names = F, append = T)
write.table("AM", paste(outputDir, "model_stop2stop_summary.csv", sep = "/"), sep = ",", row.names = F, append = T)
write.table(df_AM, paste(outputDir, "model_stop2stop_summary.csv", sep = "/"), sep = ",", row.names = F, append = T)
write.table("MD", paste(outputDir, "model_stop2stop_summary.csv", sep = "/"), sep = ",", row.names = F, append = T)
write.table(df_MD, paste(outputDir, "model_stop2stop_summary.csv", sep = "/"), sep = ",", row.names = F, append = T)
write.table("PM", paste(outputDir, "model_stop2stop_summary.csv", sep = "/"), sep = ",", row.names = F, append = T)
write.table(df_PM, paste(outputDir, "model_stop2stop_summary.csv", sep = "/"), sep = ",", row.names = F, append = T)
write.table("EV", paste(outputDir, "model_stop2stop_summary.csv", sep = "/"), sep = ",", row.names = F, append = T)
write.table(df_EV, paste(outputDir, "model_stop2stop_summary.csv", sep = "/"), sep = ",", row.names = F, append = T)






#finish