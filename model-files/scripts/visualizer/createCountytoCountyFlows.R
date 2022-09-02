#######################################################
### Script for summarizing County to County worker flows
### Author: Khademul Haque, khademul.haque@rsginc.com, August 2018
### Modified by david.hensle@rsginc.com, July 2021 to remove workers working at home
#######################################################

start_time <- Sys.time()

library(dplyr)
library(data.table)

## User Inputs
perDir        <- "F:/Projects/Clients/mtc/MTC_Visualizer/data/census/acs_pums_2017_5yr"
OutputDir     <- "F:/Projects/Clients/mtc/MTC_Visualizer/data/census/acs_pums_2017_5yr"
geogXWalkDir  <- "E:/projects/clients/mtc/Tasks/TO2_Task2/GeographicXWalk"

setwd(perDir)
perPUMS       <- fread("psam_p06.csv")

ct_xwalk      <- read.csv(paste(geogXWalkDir, "GeogXWalk2010_MAZ_TAZ_CT_PUMA_CY.csv", sep = "/"), as.is = T)

ct_xwalk$COUNTYNAME[ct_xwalk$COUNTYFP10==75] <- "San Francisco"
ct_xwalk$COUNTYNAME[ct_xwalk$COUNTYFP10==81] <- "San Mateo"
ct_xwalk$COUNTYNAME[ct_xwalk$COUNTYFP10==85] <- "Santa Clara"
ct_xwalk$COUNTYNAME[ct_xwalk$COUNTYFP10==1]  <- "Alameda"
ct_xwalk$COUNTYNAME[ct_xwalk$COUNTYFP10==13] <- "Contra Costa"
ct_xwalk$COUNTYNAME[ct_xwalk$COUNTYFP10==95] <- "Solano"
ct_xwalk$COUNTYNAME[ct_xwalk$COUNTYFP10==55] <- "Napa"
ct_xwalk$COUNTYNAME[ct_xwalk$COUNTYFP10==97] <- "Sonoma"
ct_xwalk$COUNTYNAME[ct_xwalk$COUNTYFP10==41] <- "Marin"

colnames(ct_xwalk)[colnames(ct_xwalk)=="PUMA10"] <- "PUMA"

# get unique pumas from crosswalk
puma_county_xwalk <- unique(ct_xwalk[,c("PUMA", "COUNTYNAME")])
colnames(puma_county_xwalk)[colnames(puma_county_xwalk)=="COUNTYNAME"] <- "HCOUNTYNAME"

perPUMS_worker <- perPUMS %>% 
  filter(ESR %in% c(1,2,4,5)) %>%
  filter(JWTR != 11)  # Means of transportation to work is not "worked from home"

perPUMS_select <- perPUMS_worker %>% 
  select(PUMA, PWGTP, POWPUMA)

perPUMS_select$WCOUNTYNAME[perPUMS_select$POWPUMA==7500] <- "San Francisco"
perPUMS_select$WCOUNTYNAME[perPUMS_select$POWPUMA==8100] <- "San Mateo"
perPUMS_select$WCOUNTYNAME[perPUMS_select$POWPUMA==8500] <- "Santa Clara"
perPUMS_select$WCOUNTYNAME[perPUMS_select$POWPUMA==100] <- "Alameda"
perPUMS_select$WCOUNTYNAME[perPUMS_select$POWPUMA==1300] <- "Contra Costa"
perPUMS_select$WCOUNTYNAME[perPUMS_select$POWPUMA==9500] <- "Solano"
perPUMS_select$WCOUNTYNAME[perPUMS_select$POWPUMA==5500] <- "Napa"
perPUMS_select$WCOUNTYNAME[perPUMS_select$POWPUMA==9700] <- "Sonoma"
perPUMS_select$WCOUNTYNAME[perPUMS_select$POWPUMA==4100] <- "Marin"


perPUMS_county <- perPUMS_select %>% 
  left_join(puma_county_xwalk, by = "PUMA")
perPUMS_county <- perPUMS_county[!is.na(perPUMS_county$WCOUNTYNAME) & !is.na(perPUMS_county$HCOUNTYNAME),]

countyflow <- xtabs(PWGTP~HCOUNTYNAME+WCOUNTYNAME, data = perPUMS_county)
countyflow[is.na(countyflow)] <- 0
countyflow <- addmargins(as.table(countyflow))
countyflow <- as.data.frame.matrix(countyflow)
colnames(countyflow)[colnames(countyflow)=="Sum"] <- "Total"
rownames(countyflow)[rownames(countyflow)=="Sum"] <- "Total"


setwd(OutputDir)

write.csv(countyflow, "countytocountyflows2013_17.csv")



#finish

end_time <- Sys.time()
end_time - start_time


