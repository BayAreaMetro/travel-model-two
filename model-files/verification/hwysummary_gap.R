#Marin highway assignment summary script (gap summary)
#Khademul Haque, khademul.haque@rsginc.com, July 2018

# Libraries

library(foreign)
library(dplyr)
library(reshape)

## User Inputs

# marin <- TRUE
# mtc <- FALSE
marin <- FALSE
mtc <- TRUE

# Directories
if(marin){
  # Only Marin HHs
  WD         <- "E:/projects/clients/marin/HighwaySummary/output/marin_vs_count"
}

if(mtc){
  # Full Marin run
  WD         <- "E:/projects/clients/marin/HighwaySummary/output/mtc_vs_count"
}
# WD <- "E:/projects/clients/marin/HighwaySummary"
# WD <- "E:/projects/clients/marin/HighwaySummary/070918"
# volumes <- read.csv(paste(WD, "total_volumes.csv", sep = "\\"), as.is = T)
comparison <- read.csv(paste(WD, "volume_vs_count.csv", sep = "\\"), as.is = T)

# comparison <- comparison %>%
#   mutate(OLD_A_B = paste(as.character(old_a), as.character(old_b), sep = "_"))
# comparison2 <- comparison2 %>%
#   mutate(OLD_A_B = paste(as.character(old_a), as.character(old_b), sep = "_"))
# 
# comparison$test <- comparison2$OLD_A_B[match(comparison$OLD_A_B, comparison2$OLD_A_B)]


facility_types        <- c('Connector', 'Freeway to Freeway', 'Freeway', 'Expressway', 'Collector', 'Ramp', 'Special Facility', 'Major Arterial')
facility_codes        <- c(0, 1, 2, 3, 4, 5, 6, 7)
facility_df           <- data.frame(code = facility_codes, type = facility_types)

### create subset data for other summary spreadsheets
factype <- comparison %>% 
  group_by(pemsid) %>% 
  summarise(FT=mean(ft))

EA_data <- data.frame(comparison[which(comparison$time_period=="EA"),])
EA_data_2 <- EA_data %>% 
  filter(year>2011) %>% 
  group_by(pemsid) %>% 
  summarise(avg_vol=mean(volume))
EA_data_3 <- EA_data %>% 
  filter(year>2011) %>% 
  group_by(pemsid) %>% 
  summarise(avg_count=mean(count))
EA_data_final <- EA_data_2 %>% 
  left_join(EA_data_3, by = "pemsid")
EA_data_final <- EA_data_final %>% 
  mutate(use=1) %>% 
  left_join(factype, by = "pemsid")
write.csv(EA_data_final, paste(WD, "volume_vs_count_EA.csv", sep = "\\"), row.names = F)

AM_data <- data.frame(comparison[which(comparison$time_period=="AM"),])
AM_data_2 <- AM_data %>% 
  filter(year>2011) %>% 
  group_by(pemsid) %>% 
  summarise(avg_vol=mean(volume))
AM_data_3 <- AM_data %>% 
  filter(year>2011) %>% 
  group_by(pemsid) %>% 
  summarise(avg_count=mean(count))
AM_data_final <- AM_data_2 %>% 
  left_join(AM_data_3, by = "pemsid")
AM_data_final <- AM_data_final %>% 
  mutate(use=1) %>% 
  left_join(factype, by = "pemsid")
write.csv(AM_data_final, paste(WD, "volume_vs_count_AM.csv", sep = "\\"), row.names = F)

MD_data <- data.frame(comparison[which(comparison$time_period=="MD"),])
MD_data_2 <- MD_data %>% 
  filter(year>2011) %>% 
  group_by(pemsid) %>% 
  summarise(avg_vol=mean(volume))
MD_data_3 <- MD_data %>% 
  filter(year>2011) %>% 
  group_by(pemsid) %>% 
  summarise(avg_count=mean(count))
MD_data_final <- MD_data_2 %>% 
  left_join(MD_data_3, by = "pemsid")
MD_data_final <- MD_data_final %>% 
  mutate(use=1) %>% 
  left_join(factype, by = "pemsid")
write.csv(MD_data_final, paste(WD, "volume_vs_count_MD.csv", sep = "\\"), row.names = F)

PM_data <- data.frame(comparison[which(comparison$time_period=="PM"),])
PM_data_2 <- PM_data %>% 
  filter(year>2011) %>% 
  group_by(pemsid) %>% 
  summarise(avg_vol=mean(volume))
PM_data_3 <- PM_data %>% 
  filter(year>2011) %>% 
  group_by(pemsid) %>% 
  summarise(avg_count=mean(count))
PM_data_final <- PM_data_2 %>% 
  left_join(PM_data_3, by = "pemsid")
PM_data_final <- PM_data_final %>% 
  mutate(use=1) %>% 
  left_join(factype, by = "pemsid")
write.csv(PM_data_final, paste(WD, "volume_vs_count_PM.csv", sep = "\\"), row.names = F)

EV_data <- data.frame(comparison[which(comparison$time_period=="EV"),])
EV_data_2 <- EV_data %>% 
  filter(year>2011) %>% 
  group_by(pemsid) %>% 
  summarise(avg_vol=mean(volume))
EV_data_3 <- EV_data %>% 
  filter(year>2011) %>% 
  group_by(pemsid) %>% 
  summarise(avg_count=mean(count))
EV_data_final <- EV_data_2 %>% 
  left_join(EV_data_3, by = "pemsid")
EV_data_final <- EV_data_final %>% 
  mutate(use=1) %>% 
  left_join(factype, by = "pemsid")
write.csv(EV_data_final, paste(WD, "volume_vs_count_EV.csv", sep = "\\"), row.names = F)

names(EA_data_final)[names(EA_data_final) == "avg_vol"]     <- "avg_vol_EA"
names(EA_data_final)[names(EA_data_final) == "avg_count"] <- "avg_count_EA"
names(AM_data_final)[names(AM_data_final) == "avg_vol"]     <- "avg_vol_AM"
names(AM_data_final)[names(AM_data_final) == "avg_count"] <- "avg_count_AM"
names(MD_data_final)[names(MD_data_final) == "avg_vol"]     <- "avg_vol_MD"
names(MD_data_final)[names(MD_data_final) == "avg_count"] <- "avg_count_MD"
names(PM_data_final)[names(PM_data_final) == "avg_vol"]     <- "avg_vol_PM"
names(PM_data_final)[names(PM_data_final) == "avg_count"] <- "avg_count_PM"
names(EV_data_final)[names(EV_data_final) == "avg_vol"]     <- "avg_vol_EV"
names(EV_data_final)[names(EV_data_final) == "avg_count"] <- "avg_count_EV"

daily_data <- PM_data_final %>% 
  left_join(AM_data_final, by = "pemsid") %>% 
  left_join(MD_data_final, by = "pemsid") %>% 
  left_join(EA_data_final, by = "pemsid") %>% 
  left_join(EV_data_final, by = "pemsid")
daily_data <- daily_data[!is.na(daily_data$avg_vol_EA) & !is.na(daily_data$avg_count_EA),]
daily_data <- daily_data[!is.na(daily_data$avg_vol_AM) & !is.na(daily_data$avg_count_AM),]
daily_data <- daily_data[!is.na(daily_data$avg_vol_MD) & !is.na(daily_data$avg_count_MD),]
daily_data <- daily_data[!is.na(daily_data$avg_vol_PM) & !is.na(daily_data$avg_count_PM),]
daily_data <- daily_data[!is.na(daily_data$avg_vol_EV) & !is.na(daily_data$avg_count_EV),]

daily_data <- daily_data %>% 
  mutate(avg_vol=avg_vol_PM+avg_vol_AM+avg_vol_MD+avg_vol_EA+avg_vol_EV) %>% 
  mutate(avg_count=avg_count_PM+avg_count_AM+avg_count_MD+avg_count_EA+avg_count_EV) %>% 
  select(pemsid, avg_vol, avg_count)
daily_data <- daily_data %>% 
  mutate(use=1) %>% 
  left_join(factype, by = "pemsid")
write.csv(daily_data, paste(WD, "volume_vs_count_daily.csv", sep = "\\"), row.names = F)

### create file for table

comparison_mtc <- comparison
names(comparison_mtc)[names(comparison_mtc) == "ft"] <- "FACTYPE"
names(comparison_mtc)[names(comparison_mtc) == "pemsid"] <- "id"

## EA
testEA <- data.frame(comparison_mtc[which(comparison_mtc$time_period=="EA"),])
testEA_count <- testEA %>% 
  select(id, FACTYPE, count)
names(testEA_count)[names(testEA_count) == "count"] <- "ea_vol"
testEA_vol <- testEA %>% 
  select(id, FACTYPE, volume)
names(testEA_vol)[names(testEA_vol) == "volume"] <- "ea_vol"

## AM
testAM <- data.frame(comparison_mtc[which(comparison_mtc$time_period=="AM"),])
testAM_count <- testAM %>% 
  select(id, FACTYPE, count)
names(testAM_count)[names(testAM_count) == "count"] <- "am_vol"
testAM_vol <- testAM %>% 
  select(id, FACTYPE, volume)
names(testAM_vol)[names(testAM_vol) == "volume"] <- "am_vol"

## MD
testMD <- data.frame(comparison_mtc[which(comparison_mtc$time_period=="MD"),])
testMD_count <- testMD %>% 
  select(id, FACTYPE, count)
names(testMD_count)[names(testMD_count) == "count"] <- "md_vol"
testMD_vol <- testMD %>% 
  select(id, FACTYPE, volume)
names(testMD_vol)[names(testMD_vol) == "volume"] <- "md_vol"

## PM
testPM <- data.frame(comparison_mtc[which(comparison_mtc$time_period=="PM"),])
testPM_count <- testPM %>% 
  select(id, FACTYPE, count)
names(testPM_count)[names(testPM_count) == "count"] <- "pm_vol"
testPM_vol <- testPM %>% 
  select(id, FACTYPE, volume)
names(testPM_vol)[names(testPM_vol) == "volume"] <- "pm_vol"

## EV
testEV <- data.frame(comparison_mtc[which(comparison_mtc$time_period=="EV"),])
testEV_count <- testEV %>% 
  select(id, FACTYPE, count)
names(testEV_count)[names(testEV_count) == "count"] <- "ev_vol"
testEV_vol <- testEV %>% 
  select(id, FACTYPE, volume)
names(testEV_vol)[names(testEV_vol) == "volume"] <- "ev_vol"

## Total (daily): filtered because some PEMSID do not have volume for all time periods
testtotal <- data.frame(comparison_mtc[which(comparison_mtc$time_period=="Total"),])
testtotal <- testtotal %>% 
  filter(id %in% testEA$id) %>%
  filter(id %in% testAM$id) %>%
  filter(id %in% testMD$id) %>%
  filter(id %in% testPM$id) %>%
  filter(id %in% testEV$id)
  
testtotal <- testtotal %>% 
  select(id, FACTYPE, count, volume)
names(testtotal)[names(testtotal) == "volume"] <- "day_vol"
names(testtotal)[names(testtotal) == "count"] <- "day_cnt"

## daily

# prepare data for gap summary
base_df <- testtotal %>% 
  select(id, FACTYPE, day_cnt)
names(base_df)[names(base_df) == "day_cnt"] <- "day_vol"
build_df <- testtotal %>% 
  select(id, FACTYPE, day_vol)

counts_df <- data.frame(base_df[,c("id","FACTYPE", "day_vol")], build_df$day_vol)
counts_df$FACTYPE <- facility_df$type[match(counts_df$FACTYPE, facility_df$code)]
counts_df$FACTYPE <- factor(counts_df$FACTYPE, levels = facility_types)

colnames(counts_df) <- c("CountLocation", "FACTYPE", "x", "y")

#remove rows where both x and y are zeros
counts_df <- counts_df[!(counts_df$x==0 & counts_df$y==0),]
y_max <- max(counts_df$y)
x_max <- max(counts_df$x)

# Gap summary
counts_df <- counts_df %>%
  mutate(diff = y - x) %>%
  mutate(pdiff = diff/x) %>%
  mutate(gapRange = ifelse(pdiff>=1, ">=100%", "NA")) %>%
  mutate(gapRange = ifelse((pdiff>=0.5) & (pdiff<1), "50%~100%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.3) & (pdiff<0.5), "30%~50%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.2) & (pdiff<0.3), "20%~30%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.1) & (pdiff<0.2), "10%~20%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0) & (pdiff<0.1), "0%~10%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.1) & (pdiff< 0), "-10%~0%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.2) & (pdiff< -0.1), "-20%~-10%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.3) & (pdiff< -0.2), "-30%~-20%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.5) & (pdiff< -0.3), "-50%~-30%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff < -0.5), "<-50%", gapRange)) %>%
  mutate(gapRange1 = ifelse((pdiff>=-0.1) & (pdiff< 0.1), 1, 0)) %>%
  mutate(gapRange2 = ifelse((pdiff>=-0.2) & (pdiff< 0.2), 1, 0)) %>%
  mutate(gapRange3 = ifelse((pdiff>=-0.3) & (pdiff< 0.3), 1, 0))

gap_summary_df <- counts_df %>%
  mutate(FACTYPE = as.character(FACTYPE)) %>%
  mutate(FACTYPE = ifelse((FACTYPE == "Principal Arterial" | FACTYPE == "Minor Arterial"), "Arterial", FACTYPE)) %>%
  mutate(FACTYPE = ifelse((FACTYPE == "Major Collector" | FACTYPE == "Minor Collector" | FACTYPE == "Local Road"), "Collector", FACTYPE))

## First Summary
gap_summary <- xtabs(~gapRange+FACTYPE, gap_summary_df)
gap_summary[is.na(gap_summary)] <- 0
gap_summary <- addmargins(as.table(gap_summary))
gap_summary <- as.data.frame.matrix(gap_summary)
gap_summary$id <- row.names(gap_summary)
# colnames(gap_summary) <- c("Arterial","Collector","Interstate","Ramp","Total", "GapRange")
names(gap_summary)[names(gap_summary) == "id"] <- "GapRange"
names(gap_summary)[names(gap_summary) == "Sum"] <- "Total"
gap_summary$GapRange[gap_summary$GapRange=="Sum"] <- "Total"
# gap_summary$HOV_Toll <- 0
gap_summary <- gap_summary %>%
  select(GapRange, Expressway, Freeway, `Freeway to Freeway`, Ramp, Total)

#Order the rows
GapRange <- c(">=100%", "50%~100%", "30%~50%", "20%~30%", "10%~20%", "0%~10%", 
              "-10%~0%", "-20%~-10%", "-30%~-20%", "-50%~-30%", "<-50%", "Total")
temp <- data.frame(GapRange, stringsAsFactors = F)
gap_summary <- temp %>%
  left_join(gap_summary, by = c("GapRange" = "GapRange"))
gap_summary[is.na(gap_summary)] <- 0

# Compute percentages
gap_summary$Expressway_p = paste(round(gap_summary$Expressway/gap_summary$Expressway[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Freeway_p = paste(round(gap_summary$Freeway/gap_summary$Freeway[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
# gap_summary$HOV_Toll_p = 0
gap_summary$F2F_p = paste(round(gap_summary$`Freeway to Freeway`/gap_summary$`Freeway to Freeway`[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Ramp_p = paste(round(gap_summary$Ramp/gap_summary$Ramp[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Total_p = paste(round(gap_summary$Total/gap_summary$Total[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")

## Second Summary
gap_summary2 <- gap_summary_df %>%
  group_by(FACTYPE) %>%
  summarise(gapRange1=sum(gapRange1), gapRange2=sum(gapRange2), gapRange3=sum(gapRange3))
gap_summary2 <- as.data.frame(t(gap_summary2))[-1, ]
gap_summary2$V1 <- as.numeric(as.character(gap_summary2$V1))
gap_summary2$V2 <- as.numeric(as.character(gap_summary2$V2))
gap_summary2$V3 <- as.numeric(as.character(gap_summary2$V3))
gap_summary2$V4 <- as.numeric(as.character(gap_summary2$V4))
colnames(gap_summary2) <- c("Expressway", "Freeway", "Freeway to Freeway", "Ramp")
gapRanges <- c("-10%~10%", "-20%~20%", "-30%~30%")
gap_summary2$GapRange <- gapRanges
gap_summary2$Total <- gap_summary2$Expressway+gap_summary2$Freeway+gap_summary2$`Freeway to Freeway`+gap_summary2$Ramp
# gap_summary2$HOV_Toll <- 0
gap_summary2 <- gap_summary2 %>%
  select(GapRange, Expressway, Freeway, `Freeway to Freeway`, Ramp, Total)

# compute percentages
gap_summary2 <- rbind(gap_summary2, gap_summary[gap_summary$GapRange=="Total", 1:6])
gap_summary2$Expressway_p = paste(round(gap_summary2$Expressway/gap_summary2$Expressway[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
# gap_summary2$HOV_Toll_p = 0
gap_summary2$Freeway_p = paste(round(gap_summary2$Freeway/gap_summary2$Freeway[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$F2F_p = paste(round(gap_summary2$`Freeway to Freeway`/gap_summary2$`Freeway to Freeway`[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$Ramp_p = paste(round(gap_summary2$Ramp/gap_summary2$Ramp[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$Total_p = paste(round(gap_summary2$Total/gap_summary2$Total[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2 <- gap_summary2[1:3, ]

summary <- rbind(gap_summary, gap_summary2)
colnames(summary) <- c("GapRange", "Expressway", "Freeway", "Freeway to Freeway", "Ramp", "Total", 
                       "Expressway", "Freeway", "Freeway to Freeway", "Ramp", "Total")

# write final output
write.csv(summary, paste(WD, "percent_of_links_daily.csv", sep = "\\"), row.names = F)



## EA

# prepare data for gap summary
base_df <- testEA_count
build_df <- testEA_vol

counts_df <- data.frame(base_df[,c("id","FACTYPE", "ea_vol")], build_df$ea_vol)
counts_df$FACTYPE <- facility_df$type[match(counts_df$FACTYPE, facility_df$code)]
counts_df$FACTYPE <- factor(counts_df$FACTYPE, levels = facility_types)

colnames(counts_df) <- c("CountLocation", "FACTYPE", "x", "y")

#remove rows where both x and y are zeros
counts_df <- counts_df[!(counts_df$x==0 & counts_df$y==0),]
y_max <- max(counts_df$y)
x_max <- max(counts_df$x)

# Gap summary
counts_df <- counts_df %>%
  mutate(diff = y - x) %>%
  mutate(pdiff = diff/x) %>%
  mutate(gapRange = ifelse(pdiff>=1, ">=100%", "NA")) %>%
  mutate(gapRange = ifelse((pdiff>=0.5) & (pdiff<1), "50%~100%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.3) & (pdiff<0.5), "30%~50%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.2) & (pdiff<0.3), "20%~30%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.1) & (pdiff<0.2), "10%~20%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0) & (pdiff<0.1), "0%~10%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.1) & (pdiff< 0), "-10%~0%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.2) & (pdiff< -0.1), "-20%~-10%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.3) & (pdiff< -0.2), "-30%~-20%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.5) & (pdiff< -0.3), "-50%~-30%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff < -0.5), "<-50%", gapRange)) %>%
  mutate(gapRange1 = ifelse((pdiff>=-0.1) & (pdiff< 0.1), 1, 0)) %>%
  mutate(gapRange2 = ifelse((pdiff>=-0.2) & (pdiff< 0.2), 1, 0)) %>%
  mutate(gapRange3 = ifelse((pdiff>=-0.3) & (pdiff< 0.3), 1, 0))

gap_summary_df <- counts_df %>%
  mutate(FACTYPE = as.character(FACTYPE)) %>%
  mutate(FACTYPE = ifelse((FACTYPE == "Principal Arterial" | FACTYPE == "Minor Arterial"), "Arterial", FACTYPE)) %>%
  mutate(FACTYPE = ifelse((FACTYPE == "Major Collector" | FACTYPE == "Minor Collector" | FACTYPE == "Local Road"), "Collector", FACTYPE))

## First Summary
gap_summary <- xtabs(~gapRange+FACTYPE, gap_summary_df)
gap_summary[is.na(gap_summary)] <- 0
gap_summary <- addmargins(as.table(gap_summary))
gap_summary <- as.data.frame.matrix(gap_summary)
gap_summary$id <- row.names(gap_summary)
# colnames(gap_summary) <- c("Arterial","Collector","Interstate","Ramp","Total", "GapRange")
names(gap_summary)[names(gap_summary) == "id"] <- "GapRange"
names(gap_summary)[names(gap_summary) == "Sum"] <- "Total"
gap_summary$GapRange[gap_summary$GapRange=="Sum"] <- "Total"
# gap_summary$HOV_Toll <- 0
gap_summary <- gap_summary %>%
  select(GapRange, Expressway, Freeway, `Freeway to Freeway`, Ramp, Total)

#Order the rows
GapRange <- c(">=100%", "50%~100%", "30%~50%", "20%~30%", "10%~20%", "0%~10%", 
              "-10%~0%", "-20%~-10%", "-30%~-20%", "-50%~-30%", "<-50%", "Total")
temp <- data.frame(GapRange, stringsAsFactors = F)
gap_summary <- temp %>%
  left_join(gap_summary, by = c("GapRange" = "GapRange"))
gap_summary[is.na(gap_summary)] <- 0

# Compute percentages
gap_summary$Expressway_p = paste(round(gap_summary$Expressway/gap_summary$Expressway[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Freeway_p = paste(round(gap_summary$Freeway/gap_summary$Freeway[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
# gap_summary$HOV_Toll_p = 0
gap_summary$F2F_p = paste(round(gap_summary$`Freeway to Freeway`/gap_summary$`Freeway to Freeway`[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Ramp_p = paste(round(gap_summary$Ramp/gap_summary$Ramp[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Total_p = paste(round(gap_summary$Total/gap_summary$Total[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")

## Second Summary
gap_summary2 <- gap_summary_df %>%
  group_by(FACTYPE) %>%
  summarise(gapRange1=sum(gapRange1), gapRange2=sum(gapRange2), gapRange3=sum(gapRange3))
gap_summary2 <- as.data.frame(t(gap_summary2))[-1, ]
gap_summary2$V1 <- as.numeric(as.character(gap_summary2$V1))
gap_summary2$V2 <- as.numeric(as.character(gap_summary2$V2))
gap_summary2$V3 <- as.numeric(as.character(gap_summary2$V3))
gap_summary2$V4 <- as.numeric(as.character(gap_summary2$V4))
colnames(gap_summary2) <- c("Expressway", "Freeway", "Freeway to Freeway", "Ramp")
gapRanges <- c("-10%~10%", "-20%~20%", "-30%~30%")
gap_summary2$GapRange <- gapRanges
gap_summary2$Total <- gap_summary2$Expressway+gap_summary2$Freeway+gap_summary2$`Freeway to Freeway`+gap_summary2$Ramp
# gap_summary2$HOV_Toll <- 0
gap_summary2 <- gap_summary2 %>%
  select(GapRange, Expressway, Freeway, `Freeway to Freeway`, Ramp, Total)

# compute percentages
gap_summary2 <- rbind(gap_summary2, gap_summary[gap_summary$GapRange=="Total", 1:6])
gap_summary2$Expressway_p = paste(round(gap_summary2$Expressway/gap_summary2$Expressway[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
# gap_summary2$HOV_Toll_p = 0
gap_summary2$Freeway_p = paste(round(gap_summary2$Freeway/gap_summary2$Freeway[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$F2F_p = paste(round(gap_summary2$`Freeway to Freeway`/gap_summary2$`Freeway to Freeway`[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$Ramp_p = paste(round(gap_summary2$Ramp/gap_summary2$Ramp[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$Total_p = paste(round(gap_summary2$Total/gap_summary2$Total[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2 <- gap_summary2[1:3, ]

summary <- rbind(gap_summary, gap_summary2)
colnames(summary) <- c("GapRange", "Expressway", "Freeway", "Freeway to Freeway", "Ramp", "Total", 
                       "Expressway", "Freeway", "Freeway to Freeway", "Ramp", "Total")

# write final output
write.csv(summary, paste(WD, "percent_of_links_EA.csv", sep = "\\"), row.names = F)


## AM

# prepare data for gap summary
base_df <- testAM_count
build_df <- testAM_vol

counts_df <- data.frame(base_df[,c("id","FACTYPE", "am_vol")], build_df$am_vol)
counts_df$FACTYPE <- facility_df$type[match(counts_df$FACTYPE, facility_df$code)]
counts_df$FACTYPE <- factor(counts_df$FACTYPE, levels = facility_types)

colnames(counts_df) <- c("CountLocation", "FACTYPE", "x", "y")

#remove rows where both x and y are zeros
counts_df <- counts_df[!(counts_df$x==0 & counts_df$y==0),]
y_max <- max(counts_df$y)
x_max <- max(counts_df$x)

# Gap summary
counts_df <- counts_df %>%
  mutate(diff = y - x) %>%
  mutate(pdiff = diff/x) %>%
  mutate(gapRange = ifelse(pdiff>=1, ">=100%", "NA")) %>%
  mutate(gapRange = ifelse((pdiff>=0.5) & (pdiff<1), "50%~100%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.3) & (pdiff<0.5), "30%~50%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.2) & (pdiff<0.3), "20%~30%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.1) & (pdiff<0.2), "10%~20%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0) & (pdiff<0.1), "0%~10%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.1) & (pdiff< 0), "-10%~0%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.2) & (pdiff< -0.1), "-20%~-10%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.3) & (pdiff< -0.2), "-30%~-20%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.5) & (pdiff< -0.3), "-50%~-30%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff < -0.5), "<-50%", gapRange)) %>%
  mutate(gapRange1 = ifelse((pdiff>=-0.1) & (pdiff< 0.1), 1, 0)) %>%
  mutate(gapRange2 = ifelse((pdiff>=-0.2) & (pdiff< 0.2), 1, 0)) %>%
  mutate(gapRange3 = ifelse((pdiff>=-0.3) & (pdiff< 0.3), 1, 0))

gap_summary_df <- counts_df %>%
  mutate(FACTYPE = as.character(FACTYPE)) %>%
  mutate(FACTYPE = ifelse((FACTYPE == "Principal Arterial" | FACTYPE == "Minor Arterial"), "Arterial", FACTYPE)) %>%
  mutate(FACTYPE = ifelse((FACTYPE == "Major Collector" | FACTYPE == "Minor Collector" | FACTYPE == "Local Road"), "Collector", FACTYPE))

## First Summary
gap_summary <- xtabs(~gapRange+FACTYPE, gap_summary_df)
gap_summary[is.na(gap_summary)] <- 0
gap_summary <- addmargins(as.table(gap_summary))
gap_summary <- as.data.frame.matrix(gap_summary)
gap_summary$id <- row.names(gap_summary)
# colnames(gap_summary) <- c("Arterial","Collector","Interstate","Ramp","Total", "GapRange")
names(gap_summary)[names(gap_summary) == "id"] <- "GapRange"
names(gap_summary)[names(gap_summary) == "Sum"] <- "Total"
gap_summary$GapRange[gap_summary$GapRange=="Sum"] <- "Total"
# gap_summary$HOV_Toll <- 0
gap_summary <- gap_summary %>%
  select(GapRange, Expressway, Freeway, `Freeway to Freeway`, Ramp, Total)

#Order the rows
GapRange <- c(">=100%", "50%~100%", "30%~50%", "20%~30%", "10%~20%", "0%~10%", 
              "-10%~0%", "-20%~-10%", "-30%~-20%", "-50%~-30%", "<-50%", "Total")
temp <- data.frame(GapRange, stringsAsFactors = F)
gap_summary <- temp %>%
  left_join(gap_summary, by = c("GapRange" = "GapRange"))
gap_summary[is.na(gap_summary)] <- 0

# Compute percentages
gap_summary$Expressway_p = paste(round(gap_summary$Expressway/gap_summary$Expressway[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Freeway_p = paste(round(gap_summary$Freeway/gap_summary$Freeway[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
# gap_summary$HOV_Toll_p = 0
gap_summary$F2F_p = paste(round(gap_summary$`Freeway to Freeway`/gap_summary$`Freeway to Freeway`[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Ramp_p = paste(round(gap_summary$Ramp/gap_summary$Ramp[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Total_p = paste(round(gap_summary$Total/gap_summary$Total[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")

## Second Summary
gap_summary2 <- gap_summary_df %>%
  group_by(FACTYPE) %>%
  summarise(gapRange1=sum(gapRange1), gapRange2=sum(gapRange2), gapRange3=sum(gapRange3))
gap_summary2 <- as.data.frame(t(gap_summary2))[-1, ]
gap_summary2$V1 <- as.numeric(as.character(gap_summary2$V1))
gap_summary2$V2 <- as.numeric(as.character(gap_summary2$V2))
gap_summary2$V3 <- as.numeric(as.character(gap_summary2$V3))
gap_summary2$V4 <- as.numeric(as.character(gap_summary2$V4))
colnames(gap_summary2) <- c("Expressway", "Freeway", "Freeway to Freeway", "Ramp")
gapRanges <- c("-10%~10%", "-20%~20%", "-30%~30%")
gap_summary2$GapRange <- gapRanges
gap_summary2$Total <- gap_summary2$Expressway+gap_summary2$Freeway+gap_summary2$`Freeway to Freeway`+gap_summary2$Ramp
# gap_summary2$HOV_Toll <- 0
gap_summary2 <- gap_summary2 %>%
  select(GapRange, Expressway, Freeway, `Freeway to Freeway`, Ramp, Total)

# compute percentages
gap_summary2 <- rbind(gap_summary2, gap_summary[gap_summary$GapRange=="Total", 1:6])
gap_summary2$Expressway_p = paste(round(gap_summary2$Expressway/gap_summary2$Expressway[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
# gap_summary2$HOV_Toll_p = 0
gap_summary2$Freeway_p = paste(round(gap_summary2$Freeway/gap_summary2$Freeway[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$F2F_p = paste(round(gap_summary2$`Freeway to Freeway`/gap_summary2$`Freeway to Freeway`[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$Ramp_p = paste(round(gap_summary2$Ramp/gap_summary2$Ramp[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$Total_p = paste(round(gap_summary2$Total/gap_summary2$Total[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2 <- gap_summary2[1:3, ]

summary <- rbind(gap_summary, gap_summary2)
colnames(summary) <- c("GapRange", "Expressway", "Freeway", "Freeway to Freeway", "Ramp", "Total", 
                       "Expressway", "Freeway", "Freeway to Freeway", "Ramp", "Total")

# write final output
write.csv(summary, paste(WD, "percent_of_links_AM.csv", sep = "\\"), row.names = F)


## MD

# prepare data for gap summary
base_df <- testMD_count
build_df <- testMD_vol

counts_df <- data.frame(base_df[,c("id","FACTYPE", "md_vol")], build_df$md_vol)
counts_df$FACTYPE <- facility_df$type[match(counts_df$FACTYPE, facility_df$code)]
counts_df$FACTYPE <- factor(counts_df$FACTYPE, levels = facility_types)

colnames(counts_df) <- c("CountLocation", "FACTYPE", "x", "y")

#remove rows where both x and y are zeros
counts_df <- counts_df[!(counts_df$x==0 & counts_df$y==0),]
y_max <- max(counts_df$y)
x_max <- max(counts_df$x)

# Gap summary
counts_df <- counts_df %>%
  mutate(diff = y - x) %>%
  mutate(pdiff = diff/x) %>%
  mutate(gapRange = ifelse(pdiff>=1, ">=100%", "NA")) %>%
  mutate(gapRange = ifelse((pdiff>=0.5) & (pdiff<1), "50%~100%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.3) & (pdiff<0.5), "30%~50%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.2) & (pdiff<0.3), "20%~30%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.1) & (pdiff<0.2), "10%~20%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0) & (pdiff<0.1), "0%~10%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.1) & (pdiff< 0), "-10%~0%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.2) & (pdiff< -0.1), "-20%~-10%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.3) & (pdiff< -0.2), "-30%~-20%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.5) & (pdiff< -0.3), "-50%~-30%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff < -0.5), "<-50%", gapRange)) %>%
  mutate(gapRange1 = ifelse((pdiff>=-0.1) & (pdiff< 0.1), 1, 0)) %>%
  mutate(gapRange2 = ifelse((pdiff>=-0.2) & (pdiff< 0.2), 1, 0)) %>%
  mutate(gapRange3 = ifelse((pdiff>=-0.3) & (pdiff< 0.3), 1, 0))

gap_summary_df <- counts_df %>%
  mutate(FACTYPE = as.character(FACTYPE)) %>%
  mutate(FACTYPE = ifelse((FACTYPE == "Principal Arterial" | FACTYPE == "Minor Arterial"), "Arterial", FACTYPE)) %>%
  mutate(FACTYPE = ifelse((FACTYPE == "Major Collector" | FACTYPE == "Minor Collector" | FACTYPE == "Local Road"), "Collector", FACTYPE))

## First Summary
gap_summary <- xtabs(~gapRange+FACTYPE, gap_summary_df)
gap_summary[is.na(gap_summary)] <- 0
gap_summary <- addmargins(as.table(gap_summary))
gap_summary <- as.data.frame.matrix(gap_summary)
gap_summary$id <- row.names(gap_summary)
# colnames(gap_summary) <- c("Arterial","Collector","Interstate","Ramp","Total", "GapRange")
names(gap_summary)[names(gap_summary) == "id"] <- "GapRange"
names(gap_summary)[names(gap_summary) == "Sum"] <- "Total"
gap_summary$GapRange[gap_summary$GapRange=="Sum"] <- "Total"
# gap_summary$HOV_Toll <- 0
gap_summary <- gap_summary %>%
  select(GapRange, Expressway, Freeway, `Freeway to Freeway`, Ramp, Total)

#Order the rows
GapRange <- c(">=100%", "50%~100%", "30%~50%", "20%~30%", "10%~20%", "0%~10%", 
              "-10%~0%", "-20%~-10%", "-30%~-20%", "-50%~-30%", "<-50%", "Total")
temp <- data.frame(GapRange, stringsAsFactors = F)
gap_summary <- temp %>%
  left_join(gap_summary, by = c("GapRange" = "GapRange"))
gap_summary[is.na(gap_summary)] <- 0

# Compute percentages
gap_summary$Expressway_p = paste(round(gap_summary$Expressway/gap_summary$Expressway[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Freeway_p = paste(round(gap_summary$Freeway/gap_summary$Freeway[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
# gap_summary$HOV_Toll_p = 0
gap_summary$F2F_p = paste(round(gap_summary$`Freeway to Freeway`/gap_summary$`Freeway to Freeway`[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Ramp_p = paste(round(gap_summary$Ramp/gap_summary$Ramp[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Total_p = paste(round(gap_summary$Total/gap_summary$Total[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")

## Second Summary
gap_summary2 <- gap_summary_df %>%
  group_by(FACTYPE) %>%
  summarise(gapRange1=sum(gapRange1), gapRange2=sum(gapRange2), gapRange3=sum(gapRange3))
gap_summary2 <- as.data.frame(t(gap_summary2))[-1, ]
gap_summary2$V1 <- as.numeric(as.character(gap_summary2$V1))
gap_summary2$V2 <- as.numeric(as.character(gap_summary2$V2))
gap_summary2$V3 <- as.numeric(as.character(gap_summary2$V3))
gap_summary2$V4 <- as.numeric(as.character(gap_summary2$V4))
colnames(gap_summary2) <- c("Expressway", "Freeway", "Freeway to Freeway", "Ramp")
gapRanges <- c("-10%~10%", "-20%~20%", "-30%~30%")
gap_summary2$GapRange <- gapRanges
gap_summary2$Total <- gap_summary2$Expressway+gap_summary2$Freeway+gap_summary2$`Freeway to Freeway`+gap_summary2$Ramp
# gap_summary2$HOV_Toll <- 0
gap_summary2 <- gap_summary2 %>%
  select(GapRange, Expressway, Freeway, `Freeway to Freeway`, Ramp, Total)

# compute percentages
gap_summary2 <- rbind(gap_summary2, gap_summary[gap_summary$GapRange=="Total", 1:6])
gap_summary2$Expressway_p = paste(round(gap_summary2$Expressway/gap_summary2$Expressway[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
# gap_summary2$HOV_Toll_p = 0
gap_summary2$Freeway_p = paste(round(gap_summary2$Freeway/gap_summary2$Freeway[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$F2F_p = paste(round(gap_summary2$`Freeway to Freeway`/gap_summary2$`Freeway to Freeway`[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$Ramp_p = paste(round(gap_summary2$Ramp/gap_summary2$Ramp[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$Total_p = paste(round(gap_summary2$Total/gap_summary2$Total[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2 <- gap_summary2[1:3, ]

summary <- rbind(gap_summary, gap_summary2)
colnames(summary) <- c("GapRange", "Expressway", "Freeway", "Freeway to Freeway", "Ramp", "Total", 
                       "Expressway", "Freeway", "Freeway to Freeway", "Ramp", "Total")

# write final output
write.csv(summary, paste(WD, "percent_of_links_MD.csv", sep = "\\"), row.names = F)


## PM

# prepare data for gap summary
base_df <- testPM_count
build_df <- testPM_vol

counts_df <- data.frame(base_df[,c("id","FACTYPE", "pm_vol")], build_df$pm_vol)
counts_df$FACTYPE <- facility_df$type[match(counts_df$FACTYPE, facility_df$code)]
counts_df$FACTYPE <- factor(counts_df$FACTYPE, levels = facility_types)

colnames(counts_df) <- c("CountLocation", "FACTYPE", "x", "y")

#remove rows where both x and y are zeros
counts_df <- counts_df[!(counts_df$x==0 & counts_df$y==0),]
y_max <- max(counts_df$y)
x_max <- max(counts_df$x)

# Gap summary
counts_df <- counts_df %>%
  mutate(diff = y - x) %>%
  mutate(pdiff = diff/x) %>%
  mutate(gapRange = ifelse(pdiff>=1, ">=100%", "NA")) %>%
  mutate(gapRange = ifelse((pdiff>=0.5) & (pdiff<1), "50%~100%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.3) & (pdiff<0.5), "30%~50%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.2) & (pdiff<0.3), "20%~30%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.1) & (pdiff<0.2), "10%~20%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0) & (pdiff<0.1), "0%~10%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.1) & (pdiff< 0), "-10%~0%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.2) & (pdiff< -0.1), "-20%~-10%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.3) & (pdiff< -0.2), "-30%~-20%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.5) & (pdiff< -0.3), "-50%~-30%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff < -0.5), "<-50%", gapRange)) %>%
  mutate(gapRange1 = ifelse((pdiff>=-0.1) & (pdiff< 0.1), 1, 0)) %>%
  mutate(gapRange2 = ifelse((pdiff>=-0.2) & (pdiff< 0.2), 1, 0)) %>%
  mutate(gapRange3 = ifelse((pdiff>=-0.3) & (pdiff< 0.3), 1, 0))

gap_summary_df <- counts_df %>%
  mutate(FACTYPE = as.character(FACTYPE)) %>%
  mutate(FACTYPE = ifelse((FACTYPE == "Principal Arterial" | FACTYPE == "Minor Arterial"), "Arterial", FACTYPE)) %>%
  mutate(FACTYPE = ifelse((FACTYPE == "Major Collector" | FACTYPE == "Minor Collector" | FACTYPE == "Local Road"), "Collector", FACTYPE))

## First Summary
gap_summary <- xtabs(~gapRange+FACTYPE, gap_summary_df)
gap_summary[is.na(gap_summary)] <- 0
gap_summary <- addmargins(as.table(gap_summary))
gap_summary <- as.data.frame.matrix(gap_summary)
gap_summary$id <- row.names(gap_summary)
# colnames(gap_summary) <- c("Arterial","Collector","Interstate","Ramp","Total", "GapRange")
names(gap_summary)[names(gap_summary) == "id"] <- "GapRange"
names(gap_summary)[names(gap_summary) == "Sum"] <- "Total"
gap_summary$GapRange[gap_summary$GapRange=="Sum"] <- "Total"
# gap_summary$HOV_Toll <- 0
gap_summary <- gap_summary %>%
  select(GapRange, Expressway, Freeway, `Freeway to Freeway`, Ramp, Total)

#Order the rows
GapRange <- c(">=100%", "50%~100%", "30%~50%", "20%~30%", "10%~20%", "0%~10%", 
              "-10%~0%", "-20%~-10%", "-30%~-20%", "-50%~-30%", "<-50%", "Total")
temp <- data.frame(GapRange, stringsAsFactors = F)
gap_summary <- temp %>%
  left_join(gap_summary, by = c("GapRange" = "GapRange"))
gap_summary[is.na(gap_summary)] <- 0

# Compute percentages
gap_summary$Expressway_p = paste(round(gap_summary$Expressway/gap_summary$Expressway[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Freeway_p = paste(round(gap_summary$Freeway/gap_summary$Freeway[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
# gap_summary$HOV_Toll_p = 0
gap_summary$F2F_p = paste(round(gap_summary$`Freeway to Freeway`/gap_summary$`Freeway to Freeway`[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Ramp_p = paste(round(gap_summary$Ramp/gap_summary$Ramp[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Total_p = paste(round(gap_summary$Total/gap_summary$Total[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")

## Second Summary
gap_summary2 <- gap_summary_df %>%
  group_by(FACTYPE) %>%
  summarise(gapRange1=sum(gapRange1), gapRange2=sum(gapRange2), gapRange3=sum(gapRange3))
gap_summary2 <- as.data.frame(t(gap_summary2))[-1, ]
gap_summary2$V1 <- as.numeric(as.character(gap_summary2$V1))
gap_summary2$V2 <- as.numeric(as.character(gap_summary2$V2))
gap_summary2$V3 <- as.numeric(as.character(gap_summary2$V3))
gap_summary2$V4 <- as.numeric(as.character(gap_summary2$V4))
colnames(gap_summary2) <- c("Expressway", "Freeway", "Freeway to Freeway", "Ramp")
gapRanges <- c("-10%~10%", "-20%~20%", "-30%~30%")
gap_summary2$GapRange <- gapRanges
gap_summary2$Total <- gap_summary2$Expressway+gap_summary2$Freeway+gap_summary2$`Freeway to Freeway`+gap_summary2$Ramp
# gap_summary2$HOV_Toll <- 0
gap_summary2 <- gap_summary2 %>%
  select(GapRange, Expressway, Freeway, `Freeway to Freeway`, Ramp, Total)

# compute percentages
gap_summary2 <- rbind(gap_summary2, gap_summary[gap_summary$GapRange=="Total", 1:6])
gap_summary2$Expressway_p = paste(round(gap_summary2$Expressway/gap_summary2$Expressway[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
# gap_summary2$HOV_Toll_p = 0
gap_summary2$Freeway_p = paste(round(gap_summary2$Freeway/gap_summary2$Freeway[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$F2F_p = paste(round(gap_summary2$`Freeway to Freeway`/gap_summary2$`Freeway to Freeway`[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$Ramp_p = paste(round(gap_summary2$Ramp/gap_summary2$Ramp[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$Total_p = paste(round(gap_summary2$Total/gap_summary2$Total[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2 <- gap_summary2[1:3, ]

summary <- rbind(gap_summary, gap_summary2)
colnames(summary) <- c("GapRange", "Expressway", "Freeway", "Freeway to Freeway", "Ramp", "Total", 
                       "Expressway", "Freeway", "Freeway to Freeway", "Ramp", "Total")

# write final output
write.csv(summary, paste(WD, "percent_of_links_PM.csv", sep = "\\"), row.names = F)


## EV

# prepare data for gap summary
base_df <- testEV_count
build_df <- testEV_vol

counts_df <- data.frame(base_df[,c("id","FACTYPE", "ev_vol")], build_df$ev_vol)
counts_df$FACTYPE <- facility_df$type[match(counts_df$FACTYPE, facility_df$code)]
counts_df$FACTYPE <- factor(counts_df$FACTYPE, levels = facility_types)

colnames(counts_df) <- c("CountLocation", "FACTYPE", "x", "y")

#remove rows where both x and y are zeros
counts_df <- counts_df[!(counts_df$x==0 & counts_df$y==0),]
y_max <- max(counts_df$y)
x_max <- max(counts_df$x)

# Gap summary
counts_df <- counts_df %>%
  mutate(diff = y - x) %>%
  mutate(pdiff = diff/x) %>%
  mutate(gapRange = ifelse(pdiff>=1, ">=100%", "NA")) %>%
  mutate(gapRange = ifelse((pdiff>=0.5) & (pdiff<1), "50%~100%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.3) & (pdiff<0.5), "30%~50%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.2) & (pdiff<0.3), "20%~30%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0.1) & (pdiff<0.2), "10%~20%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=0) & (pdiff<0.1), "0%~10%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.1) & (pdiff< 0), "-10%~0%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.2) & (pdiff< -0.1), "-20%~-10%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.3) & (pdiff< -0.2), "-30%~-20%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff>=-0.5) & (pdiff< -0.3), "-50%~-30%", gapRange)) %>%
  mutate(gapRange = ifelse((pdiff < -0.5), "<-50%", gapRange)) %>%
  mutate(gapRange1 = ifelse((pdiff>=-0.1) & (pdiff< 0.1), 1, 0)) %>%
  mutate(gapRange2 = ifelse((pdiff>=-0.2) & (pdiff< 0.2), 1, 0)) %>%
  mutate(gapRange3 = ifelse((pdiff>=-0.3) & (pdiff< 0.3), 1, 0))

gap_summary_df <- counts_df %>%
  mutate(FACTYPE = as.character(FACTYPE)) %>%
  mutate(FACTYPE = ifelse((FACTYPE == "Principal Arterial" | FACTYPE == "Minor Arterial"), "Arterial", FACTYPE)) %>%
  mutate(FACTYPE = ifelse((FACTYPE == "Major Collector" | FACTYPE == "Minor Collector" | FACTYPE == "Local Road"), "Collector", FACTYPE))

## First Summary
gap_summary <- xtabs(~gapRange+FACTYPE, gap_summary_df)
gap_summary[is.na(gap_summary)] <- 0
gap_summary <- addmargins(as.table(gap_summary))
gap_summary <- as.data.frame.matrix(gap_summary)
gap_summary$id <- row.names(gap_summary)
# colnames(gap_summary) <- c("Arterial","Collector","Interstate","Ramp","Total", "GapRange")
names(gap_summary)[names(gap_summary) == "id"] <- "GapRange"
names(gap_summary)[names(gap_summary) == "Sum"] <- "Total"
gap_summary$GapRange[gap_summary$GapRange=="Sum"] <- "Total"
# gap_summary$HOV_Toll <- 0
gap_summary <- gap_summary %>%
  select(GapRange, Expressway, Freeway, `Freeway to Freeway`, Ramp, Total)

#Order the rows
GapRange <- c(">=100%", "50%~100%", "30%~50%", "20%~30%", "10%~20%", "0%~10%", 
              "-10%~0%", "-20%~-10%", "-30%~-20%", "-50%~-30%", "<-50%", "Total")
temp <- data.frame(GapRange, stringsAsFactors = F)
gap_summary <- temp %>%
  left_join(gap_summary, by = c("GapRange" = "GapRange"))
gap_summary[is.na(gap_summary)] <- 0

# Compute percentages
gap_summary$Expressway_p = paste(round(gap_summary$Expressway/gap_summary$Expressway[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Freeway_p = paste(round(gap_summary$Freeway/gap_summary$Freeway[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
# gap_summary$HOV_Toll_p = 0
gap_summary$F2F_p = paste(round(gap_summary$`Freeway to Freeway`/gap_summary$`Freeway to Freeway`[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Ramp_p = paste(round(gap_summary$Ramp/gap_summary$Ramp[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary$Total_p = paste(round(gap_summary$Total/gap_summary$Total[gap_summary$GapRange=="Total"]*100, 1), "%", sep = "")

## Second Summary
gap_summary2 <- gap_summary_df %>%
  group_by(FACTYPE) %>%
  summarise(gapRange1=sum(gapRange1), gapRange2=sum(gapRange2), gapRange3=sum(gapRange3))
gap_summary2 <- as.data.frame(t(gap_summary2))[-1, ]
gap_summary2$V1 <- as.numeric(as.character(gap_summary2$V1))
gap_summary2$V2 <- as.numeric(as.character(gap_summary2$V2))
gap_summary2$V3 <- as.numeric(as.character(gap_summary2$V3))
gap_summary2$V4 <- as.numeric(as.character(gap_summary2$V4))
colnames(gap_summary2) <- c("Expressway", "Freeway", "Freeway to Freeway", "Ramp")
gapRanges <- c("-10%~10%", "-20%~20%", "-30%~30%")
gap_summary2$GapRange <- gapRanges
gap_summary2$Total <- gap_summary2$Expressway+gap_summary2$Freeway+gap_summary2$`Freeway to Freeway`+gap_summary2$Ramp
# gap_summary2$HOV_Toll <- 0
gap_summary2 <- gap_summary2 %>%
  select(GapRange, Expressway, Freeway, `Freeway to Freeway`, Ramp, Total)

# compute percentages
gap_summary2 <- rbind(gap_summary2, gap_summary[gap_summary$GapRange=="Total", 1:6])
gap_summary2$Expressway_p = paste(round(gap_summary2$Expressway/gap_summary2$Expressway[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
# gap_summary2$HOV_Toll_p = 0
gap_summary2$Freeway_p = paste(round(gap_summary2$Freeway/gap_summary2$Freeway[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$F2F_p = paste(round(gap_summary2$`Freeway to Freeway`/gap_summary2$`Freeway to Freeway`[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$Ramp_p = paste(round(gap_summary2$Ramp/gap_summary2$Ramp[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2$Total_p = paste(round(gap_summary2$Total/gap_summary2$Total[gap_summary2$GapRange=="Total"]*100, 1), "%", sep = "")
gap_summary2 <- gap_summary2[1:3, ]

summary <- rbind(gap_summary, gap_summary2)
colnames(summary) <- c("GapRange", "Expressway", "Freeway", "Freeway to Freeway", "Ramp", "Total", 
                       "Expressway", "Freeway", "Freeway to Freeway", "Ramp", "Total")

# write final output
write.csv(summary, paste(WD, "percent_of_links_EV.csv", sep = "\\"), row.names = F)

