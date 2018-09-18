#######################################################
### Script for summarizing MTC ABM Output
### Author: Binny M Paul, binny.paul@rsginc.com, Oct 2017
#######################################################

library(plyr)
library(weights)
library(reshape)
library(data.table)

# one of "maz_v1_0" or "maz_v2_2"
geography = "maz_v2_2"

# User Inputs
if (Sys.getenv("USERNAME") == "lzorn") {
  USERPROFILE     <- gsub("\\\\","/", Sys.getenv("USERPROFILE"))
  BOX_TM2         <- file.path(USERPROFILE, "Box", "Modeling and Surveys", "Development", "Travel Model Two Development")
  RUN_NAME        <- "2015_01_lmz_04"
  
  # this is the output directory
  WD              <- file.path(BOX_TM2, "Calibration & Validation","Round 2","Calibration Spreadsheets",RUN_NAME,"ABM Summaries")
  if (geography == "maz_v1_0") {
    ABMOutputDir  <- file.path("model2-a","Model2A-Share", "Projects_TM2","2015_01_lmz_maz1","ctramp_output")
    tripLOSFile   <- file.path(ABMOutputDir, "indivTripData_transitwLOS_1.csv")
    SkimDir       <- file.path(BOX_TM2, "Observed Data",   "RSG_CHTS")
    geogXWalkDir  <- file.path(BOX_TM2, "Observed Data",   "CHTS Processing", "Trip End Geocodes maz_v1_0")
    CT_XWalkFile  <- file.path(BOX_TM2, "Population Synthesis", "Application", "GeographicXWalk", "GeogXWalk2010_MAZ_TAZ_CT_PUMA_CY.csv")
    mazDataDir    <- file.path(BOX_TM2, "Model Inputs",    "2015", "landuse")
    districtDef   <- file.path(BOX_TM2, "Model Geography", "Zones v1.0", "taz_superdistrictv1.csv")
  } else if (geography == "maz_v2_2") {
    ABMOutputDir  <- file.path("D:", "Projects_TM2",RUN_NAME,"ctramp_output")
    tripLOSFile   <- file.path(ABMOutputDir, "indivTripData_transitwLOS_1.csv")
    SkimDir       <- file.path(BOX_TM2, "Model Geography", "Zones v2.2")
    geogXWalkDir  <- file.path(BOX_TM2, "Observed Data",   "CHTS Processing", "Trip End Geocodes maz_v2_2")
    mazDataDir    <- file.path(BOX_TM2, "Model Inputs",    "2015_revised_mazs", "landuse")
    districtDef   <- file.path(BOX_TM2, "Model Geography", "Zones v2.2", "sd22_from_tazV2_2.csv")
    CT_XWalkFile  <- file.path(BOX_TM2, "Model Geography", "Zones v2.2", "census_tracts_mazs_tazs_v2.2.csv")
  }
  # todo
  CensusDir      <- file.path(BOX_TM2, "Observed Data","RSG_CHTS","ACS_5YearEstimates")
} else {
  USERPROFILE   <- gsub("\\\\","/", Sys.getenv("USERPROFILE"))
  BOX_TM2       <- file.path(USERPROFILE, "Box", "Travel Model Two Development")
  
  WD            <- "E:/projects/clients/mtc/Calibration_2015/ModelOutputs/081318/ABM_Summaries" # change by khademul
  ABMOutputDir  <- "E:/projects/clients/mtc/Calibration_2015/ModelOutputs/081318" # change by khademul
  tripLOSFile   <- "E:/projects/clients/mtc/2015_calibration/individual_transitTrip_wLOS.csv"
  geogXWalkDir  <- "E:/projects/clients/mtc/data/Trip End Geocodes"
  SkimDir       <- "E:/projects/clients/mtc/data/Skim2015"
  CT_XWalkFile  <- "E:/projects/clients/mtc/TO2_Task2/GeographicXWalk/GeogXWalk2010_MAZ_TAZ_CT_PUMA_CY.csv"
  CensusDir     <- "E:/projects/clients/mtc/data/Census/ACS_5YearEstimates"
  mazDataDir    <- "E:/projects/clients/mtc/2015_calibration/landuse"

  districtDef   <- file.path(BOX_TM2, "Model Geography", "Zones v1.0", "taz_superdistrictv1.csv")
}

# LOS columns expected: XFERS, BEST_MODE, [LB,EB,FR,LR,HR,CR]_TIME
# e.g run in the model dir: Rscript.exe --vanilla --verbose %TM2_REPO%\model-files\verification\appendLOSAttributes.R --transitonly 1 XFERS BEST_MODE LB_TIME EB_TIME FR_TIME LR_TIME HR_TIME CR_TIME
tripsLOS           <- fread(tripLOSFile)

setwd(ABMOutputDir)
hh                 <- fread("householdData_1.csv")
per                <- fread("personData_1.csv")
tours              <- fread("indivTourData_1.csv")
trips              <- fread("indivTripData_1.csv")
jtrips             <- fread("jointTripData_1.csv")
unique_joint_tours <- fread("jointTourData_1.csv")
wsLoc              <- fread("wsLocResults_1.csv")
aoResults          <- fread("aoResults.csv")
aoResults_Pre      <- fread("aoResults_Pre.csv")

xwalk              <- read.csv(file.path(geogXWalkDir, "geographicCWalk.csv"), as.is = T)
mazData            <- read.csv(file.path(mazDataDir,   "maz_data.csv"), as.is = T)
ct_xwalk           <- read.csv(CT_XWalkFile, as.is = T)
censusAO           <- read.csv(file.path(CensusDir, "ACS_11_5YR_MTC_CensusTract_AutoOwn.csv"), as.is = T)

xwalk_SDist        <- read.csv(districtDef, as.is = T)

DST_SKM            <- fread(file.path(SkimDir, "SOV_DIST_MD_HWYSKM.csv"), stringsAsFactors = F, header = T)
DST_SKM            <- melt(DST_SKM, id = c("DISTDA"))
colnames(DST_SKM)  <- c("o", "d", "dist")

districtList         <- sort(unique(xwalk$COUNTYNAME))
SuperdistrictList    <- sort(unique(xwalk_SDist$district_name))

pertypeCodes <- data.frame(code = c(1,2,3,4,5,6,7,8,"All"), 
                           name = c("FT Worker", "PT Worker", "Univ Stud", "Non Worker", "Retiree", "Driv Stud", "NonDriv Stud", "Pre-School", "All"))


#-------------------------------------------
# Prepare files for computing summary statistics
setwd(WD)

aoResults$HHVEH[aoResults$AO == 0] <- 0
aoResults$HHVEH[aoResults$AO == 1] <- 1
aoResults$HHVEH[aoResults$AO == 2] <- 2
aoResults$HHVEH[aoResults$AO == 3] <- 3
aoResults$HHVEH[aoResults$AO >= 4] <- 4

aoResults_Pre$HHVEH[aoResults_Pre$AO == 0] <- 0
aoResults_Pre$HHVEH[aoResults_Pre$AO == 1] <- 1
aoResults_Pre$HHVEH[aoResults_Pre$AO == 2] <- 2
aoResults_Pre$HHVEH[aoResults_Pre$AO == 3] <- 3
aoResults_Pre$HHVEH[aoResults_Pre$AO >= 4] <- 4

hh$HHVEH[hh$autos == 0] <- 0
hh$HHVEH[hh$autos == 1] <- 1
hh$HHVEH[hh$autos == 2] <- 2
hh$HHVEH[hh$autos == 3] <- 3
hh$HHVEH[hh$autos >= 4] <- 4

#HH Size
hhsize <- count(per, c("hh_id"), "hh_id>0")
hh$HHSIZ <- hhsize$freq[match(hh$hh_id, hhsize$hh_id)]
hh$HHSIZE[hh$HHSIZ == 1] <- 1
hh$HHSIZE[hh$HHSIZ == 2] <- 2
hh$HHSIZE[hh$HHSIZ == 3] <- 3
hh$HHSIZE[hh$HHSIZ == 4] <- 4
hh$HHSIZE[hh$HHSIZ >= 5] <- 5

#Adults in the HH
adults <- count(per, c("hh_id"), "age>=18 & age<99")
hh$ADULTS <- adults$freq[match(hh$hh_id, adults$hh_id)]

per$PERTYPE[per$type=="Full-time worker"] <- 1
per$PERTYPE[per$type=="Part-time worker"] <- 2
per$PERTYPE[per$type=="University student"] <- 3
per$PERTYPE[per$type=="Non-worker"] <- 4
per$PERTYPE[per$type=="Retired"] <- 5
per$PERTYPE[per$type=="Student of driving age"] <- 6
per$PERTYPE[per$type=="Student of non-driving age"] <- 7
per$PERTYPE[per$type=="Child too young for school"] <- 8

# Districts are Counties
wsLoc$HDISTRICT <- xwalk$COUNTYNAME[match(wsLoc$HomeMGRA, xwalk$MAZ)]
wsLoc$WDISTRICT <- xwalk$COUNTYNAME[match(wsLoc$WorkLocation, xwalk$MAZ)]

# Districts are super districts - translate first to original (nosequential) MAZ, TAZ for home and work
wsLoc$MAZ_ORIGINAL <- xwalk$MAZ_ORIGINAL[match(wsLoc$HomeMGRA, xwalk$MAZ)]
wsLoc$TAZ_ORIGINAL <- xwalk$TAZ_ORIGINAL[match(wsLoc$HomeMGRA, xwalk$MAZ)]
wsLoc$WorkLoc_MAZ_ORIG <- xwalk$MAZ_ORIGINAL[match(wsLoc$WorkLocation, xwalk$MAZ)]
wsLoc$WorkLoc_TAZ_ORIG <- xwalk$TAZ_ORIGINAL[match(wsLoc$WorkLocation, xwalk$MAZ)]

wsLoc$HDISTRICT_S <- xwalk_SDist$district_name[match(wsLoc$TAZ_ORIGINAL,     xwalk_SDist$TAZ_ORIGINAL)]
wsLoc$WDISTRICT_S <- xwalk_SDist$district_name[match(wsLoc$WorkLoc_TAZ_ORIG, xwalk_SDist$TAZ_ORIGINAL)]

wsLoc$fp_choice <- per$fp_choice[match(wsLoc$PersonID, per$person_id)]
wsLoc$reimb_pct <- per$reimb_pct[match(wsLoc$PersonID, per$person_id)]

#Workers in the HH
workersHH <- count(wsLoc, c("HHID"), "(wsLoc$PersonType<=2) | (wsLoc$PersonType==3 & wsLoc$WorkLocation>0)")
hh$WORKERS <- workersHH$freq[match(hh$hh_id, workersHH$HHID)]


#--------Compute Summary Statistics-------
#*****************************************

# Auto ownership
autoOwnership_Pre <- count(aoResults_Pre, c("HHVEH"))
write.csv(autoOwnership_Pre, "autoOwnership_Pre.csv", row.names = TRUE)

autoOwnership <- count(aoResults, c("HHVEH"))
write.csv(autoOwnership, "autoOwnership.csv", row.names = TRUE)

# Zero auto HHs by Census Tract
hh$CTIDFP10 <- ct_xwalk$CTIDFP10[match(hh$home_mgra, ct_xwalk$MAZSEQ)]
hh$COUNTYFP10 <- ct_xwalk$COUNTYFP10[match(hh$home_mgra, ct_xwalk$MAZSEQ)]
hh$uniweight <- 1
hh$ZeroAutoWgt[hh$HHVEH==0] <- 1
hh$ZeroAutoWgt[is.na(hh$ZeroAutoWgt)] <- 0
zeroAutoByCT <- aggregate(hh$ZeroAutoWgt, list(CTIDFP10 = hh$CTIDFP10), sum)
#zeroAutoByCY <- aggregate(hh$ZeroAutoWgt, list(COUNTYFP10 = hh$COUNTYFP10), sum)
numHHByCT <- aggregate(hh$uniweight, list(CTIDFP10 = hh$CTIDFP10), sum)
#numHHByCY <- aggregate(hh$uniweight, list(COUNTYFP10 = hh$COUNTYFP10), sum)
numHHByCT <- cbind(numHHByCT, zeroAutoByCT$x)
colnames(numHHByCT) <- c("CTIDFP10", "HH", "ZeroAutoHH")
write.csv(numHHByCT, "zeroAutoByCT.csv", row.names = F)

#numHHByCY <- cbind(numHHByCY, zeroAutoByCY$x)
#colnames(numHHByCY) <- c("COUNTYFP10", "HH", "ZeroAutoHH")
#write.csv(numHHByCY, "zeroAutoByCY.csv", row.names = F)

autoOwnershipCY <- count(hh, c("COUNTYFP10", "HHVEH"))
autoOwnershipCY <- cast(autoOwnershipCY, COUNTYFP10~HHVEH, value = "freq", sum)
write.csv(autoOwnershipCY, "autoOwnershipCY.csv", row.names = F)

# Persons by person type
pertypeDistbn <- count(per, c("PERTYPE"))
write.csv(pertypeDistbn, "pertypeDistbn.csv", row.names = TRUE)

# 

# Mandatory DC
workers <- wsLoc[wsLoc$WorkLocation > 0 & wsLoc$WorkLocation != 99999,]
students <- wsLoc[wsLoc$SchoolLocation > 0 & wsLoc$SchoolLocation != 88888,]

# code distance bins
workers$distbin <- cut(workers$WorkLocationDistance, breaks = c(seq(0,50, by=1), 9999), labels = F, right = F)
students$distbin <- cut(students$SchoolLocationDistance, breaks = c(seq(0,50, by=1), 9999), labels = F, right = F)

distBinCat <- data.frame(distbin = seq(1,51, by=1))

# compute TLFDs by district and total
tlfd_work <- ddply(workers[,c("HDISTRICT", "distbin")], c("HDISTRICT", "distbin"), summarise, work = sum(HDISTRICT>0))
tlfd_work <- cast(tlfd_work, distbin~HDISTRICT, value = "work", sum)
tlfd_work$Total <- rowSums(tlfd_work[,!colnames(tlfd_work) %in% c("distbin")])
tlfd_work_df <- merge(x = distBinCat, y = tlfd_work, by = "distbin", all.x = TRUE)
tlfd_work_df[is.na(tlfd_work_df)] <- 0

tlfd_univ <- ddply(students[students$PersonType==3,c("HDISTRICT", "distbin")], c("HDISTRICT", "distbin"), summarise, univ = sum(HDISTRICT>0))
tlfd_univ <- cast(tlfd_univ, distbin~HDISTRICT, value = "univ", sum)
tlfd_univ$Total <- rowSums(tlfd_univ[,!colnames(tlfd_univ) %in% c("distbin")])
tlfd_univ_df <- merge(x = distBinCat, y = tlfd_univ, by = "distbin", all.x = TRUE)
tlfd_univ_df[is.na(tlfd_univ_df)] <- 0

tlfd_schl <- ddply(students[students$PersonType>=6,c("HDISTRICT", "distbin")], c("HDISTRICT", "distbin"), summarise, schl = sum(HDISTRICT>0))
tlfd_schl <- cast(tlfd_schl, distbin~HDISTRICT, value = "schl", sum)
tlfd_schl$Total <- rowSums(tlfd_schl[,!colnames(tlfd_schl) %in% c("distbin")])
tlfd_schl_df <- merge(x = distBinCat, y = tlfd_schl, by = "distbin", all.x = TRUE)
tlfd_schl_df[is.na(tlfd_schl_df)] <- 0

write.csv(tlfd_work_df, "workTLFD.csv", row.names = F)
write.csv(tlfd_univ_df, "univTLFD.csv", row.names = F)
write.csv(tlfd_schl_df, "schlTLFD.csv", row.names = F)

# compute TLFDs by district and total (added by khademul)
tlfd_work_S <- ddply(workers[,c("HDISTRICT_S", "distbin")], c("HDISTRICT_S", "distbin"), summarise, work = sum(HDISTRICT_S>0))
tlfd_work_S <- cast(tlfd_work_S, distbin~HDISTRICT_S, value = "work", sum)
tlfd_work_S$Total <- rowSums(tlfd_work_S[,!colnames(tlfd_work_S) %in% c("distbin")])
tlfd_work_S_df <- merge(x = distBinCat, y = tlfd_work_S, by = "distbin", all.x = TRUE)
tlfd_work_S_df[is.na(tlfd_work_S_df)] <- 0

tlfd_univ_S <- ddply(students[students$PersonType==3,c("HDISTRICT_S", "distbin")], c("HDISTRICT_S", "distbin"), summarise, univ = sum(HDISTRICT_S>0))
tlfd_univ_S <- cast(tlfd_univ_S, distbin~HDISTRICT_S, value = "univ", sum)
tlfd_univ_S$Total <- rowSums(tlfd_univ_S[,!colnames(tlfd_univ_S) %in% c("distbin")])
tlfd_univ_S_df <- merge(x = distBinCat, y = tlfd_univ_S, by = "distbin", all.x = TRUE)
tlfd_univ_S_df[is.na(tlfd_univ_S_df)] <- 0

tlfd_schl_S <- ddply(students[students$PersonType>=6,c("HDISTRICT_S", "distbin")], c("HDISTRICT_S", "distbin"), summarise, schl = sum(HDISTRICT_S>0))
tlfd_schl_S <- cast(tlfd_schl_S, distbin~HDISTRICT_S, value = "schl", sum)
tlfd_schl_S$Total <- rowSums(tlfd_schl_S[,!colnames(tlfd_schl_S) %in% c("distbin")])
tlfd_schl_S_df <- merge(x = distBinCat, y = tlfd_schl_S, by = "distbin", all.x = TRUE)
tlfd_schl_S_df[is.na(tlfd_schl_S_df)] <- 0

write.csv(tlfd_work_S_df, "workTLFD_S.csv", row.names = F)
write.csv(tlfd_univ_S_df, "univTLFD_S.csv", row.names = F)
write.csv(tlfd_schl_S_df, "schlTLFD_S.csv", row.names = F)

cat("\n Average distance to workplace (Total): ", mean(workers$WorkLocationDistance, na.rm = TRUE))
cat("\n Average distance to university (Total): ", mean(students$SchoolLocationDistance[students$PersonType==3], na.rm = TRUE))
cat("\n Average distance to school (Total): ", mean(students$SchoolLocationDistance[students$PersonType>=6], na.rm = TRUE))

## Output avg trip lengths for visualizer
workTripLengths <- ddply(workers[,c("HDISTRICT", "WorkLocationDistance")], c("HDISTRICT"), summarise, work = mean(WorkLocationDistance))
totalLength     <- data.frame("Total", mean(workers$WorkLocationDistance))
colnames(totalLength) <- colnames(workTripLengths)
workTripLengths <- rbind(workTripLengths, totalLength)

univTripLengths <- ddply(students[students$PersonType==3,c("HDISTRICT", "SchoolLocationDistance")], c("HDISTRICT"), summarise, univ = mean(SchoolLocationDistance))
totalLength     <- data.frame("Total", mean(students$SchoolLocationDistance[students$PersonType==3]))
colnames(totalLength) <- colnames(univTripLengths)
univTripLengths <- rbind(univTripLengths, totalLength)

schlTripLengths <- ddply(students[students$PersonType>=6,c("HDISTRICT", "SchoolLocationDistance")], c("HDISTRICT"), summarise, schl = mean(SchoolLocationDistance))
totalLength     <- data.frame("Total", mean(students$SchoolLocationDistance[students$PersonType>=6]))
colnames(totalLength) <- colnames(schlTripLengths)
schlTripLengths <- rbind(schlTripLengths, totalLength)

mandTripLengths <- cbind(workTripLengths, univTripLengths$univ, schlTripLengths$schl)
colnames(mandTripLengths) <- c("District", "Work", "Univ", "Schl")
write.csv(mandTripLengths, "mandTripLengths.csv", row.names = F)

## Output avg trip lengths for visualizer (added by khademul)
workTripLengths_S <- ddply(workers[,c("HDISTRICT_S", "WorkLocationDistance")], c("HDISTRICT_S"), summarise, work = mean(WorkLocationDistance))
totalLength_S     <- data.frame("Total", mean(workers$WorkLocationDistance))
colnames(totalLength_S) <- colnames(workTripLengths_S)
workTripLengths_S <- rbind(workTripLengths_S, totalLength_S)

univTripLengths_S <- ddply(students[students$PersonType==3,c("HDISTRICT_S", "SchoolLocationDistance")], c("HDISTRICT_S"), summarise, univ = mean(SchoolLocationDistance))
totalLength_S     <- data.frame("Total", mean(students$SchoolLocationDistance[students$PersonType==3]))
colnames(totalLength_S) <- colnames(univTripLengths_S)
univTripLengths_S <- rbind(univTripLengths_S, totalLength_S)

schlTripLengths_S <- ddply(students[students$PersonType>=6,c("HDISTRICT_S", "SchoolLocationDistance")], c("HDISTRICT_S"), summarise, schl = mean(SchoolLocationDistance))
totalLength_S     <- data.frame("Total", mean(students$SchoolLocationDistance[students$PersonType>=6]))
colnames(totalLength_S) <- colnames(schlTripLengths_S)
schlTripLengths_S <- rbind(schlTripLengths_S, totalLength_S)

mandTripLengths_S <- cbind(workTripLengths_S, univTripLengths_S$univ, schlTripLengths_S$schl)
colnames(mandTripLengths_S) <- c("SuperDistrict", "Work", "Univ", "Schl")
write.csv(mandTripLengths_S, "mandTripLengths_S.csv", row.names = F)

# Work from home [for each district and total]
districtWorkers <- ddply(wsLoc[wsLoc$WorkLocation > 0,c("HDISTRICT")], c("HDISTRICT"), summarise, workers = sum(HDISTRICT>0))
districtWfh     <- ddply(wsLoc[wsLoc$WorkLocation==99999,c("HDISTRICT", "WorkLocation")], c("HDISTRICT"), summarise, wfh = sum(HDISTRICT>0))
wfh_summary     <- cbind(districtWorkers, districtWfh$wfh)
colnames(wfh_summary) <- c("District", "Workers", "WFH")
totalwfh        <- data.frame("Total", sum(wsLoc$WorkLocation>0), sum(wsLoc$WorkLocation==99999))
colnames(totalwfh) <- colnames(wfh_summary)
wfh_summary <- rbind(wfh_summary, totalwfh)
write.csv(wfh_summary, "wfh_summary.csv", row.names = F)

write.csv(wfh_summary[wfh_summary$District=="Total",], "wfh_summary_region.csv", row.names = F)

# Work from home [for each district and total] (added by khademul)
districtWorkers_S <- ddply(wsLoc[wsLoc$WorkLocation > 0,c("HDISTRICT_S")], c("HDISTRICT_S"), summarise, workers = sum(HDISTRICT_S>0))
districtWfh_S     <- ddply(wsLoc[wsLoc$WorkLocation==99999,c("HDISTRICT_S", "WorkLocation")], c("HDISTRICT_S"), summarise, wfh = sum(HDISTRICT_S>0))
wfh_summary_S     <- cbind(districtWorkers_S, districtWfh_S$wfh)
colnames(wfh_summary_S) <- c("SuperDistrict", "Workers", "WFH")
totalwfh_S        <- data.frame("Total", sum(wsLoc$WorkLocation>0), sum(wsLoc$WorkLocation==99999))
colnames(totalwfh_S) <- colnames(wfh_summary_S)
wfh_summary_S <- rbind(wfh_summary_S, totalwfh_S)
write.csv(wfh_summary_S, "wfh_summary_S.csv", row.names = F)

write.csv(wfh_summary_S[wfh_summary_S$SuperDistrict=="Total",], "wfh_summary_region_S.csv", row.names = F)

# County-County Flows
countyFlows <- xtabs(~HDISTRICT+WDISTRICT, data = workers)
countyFlows[is.na(countyFlows)] <- 0
countyFlows <- addmargins(as.table(countyFlows))
countyFlows <- as.data.frame.matrix(countyFlows)
colnames(countyFlows)[colnames(countyFlows)=="Sum"] <- "Total"
rownames(countyFlows)[rownames(countyFlows)=="Sum"] <- "Total"
write.csv(countyFlows, "countyFlows.csv", row.names = T)

# County-County Flows (added by khademul)
countyFlows_S <- xtabs(~HDISTRICT_S+WDISTRICT_S, data = workers)
countyFlows_S[is.na(countyFlows_S)] <- 0
countyFlows_S <- addmargins(as.table(countyFlows_S))
countyFlows_S <- as.data.frame.matrix(countyFlows_S)
colnames(countyFlows_S)[colnames(countyFlows_S)=="Sum"] <- "Total"
rownames(countyFlows_S)[rownames(countyFlows_S)=="Sum"] <- "Total"
write.csv(countyFlows_S, "countyFlows_S.csv", row.names = T)

# Process Tour file
#------------------
tours$PERTYPE <- tours$person_type
tours$DISTMILE <- tours$SKIMDIST
tours$HHVEH <- hh$HHVEH[match(tours$hh_id, hh$hh_id)]
tours$ADULTS <- hh$ADULTS[match(tours$hh_id, hh$hh_id)]
#tours$AUTOSUFF[tours$HHVEH == 0] <- 0
#tours$AUTOSUFF[tours$HHVEH < tours$ADULTS & tours$HHVEH > 0] <- 1
#tours$AUTOSUFF[tours$HHVEH >= tours$ADULTS & tours$HHVEH > 0] <- 2

tours$WORKERS <- hh$WORKERS[match(tours$hh_id, hh$hh_id)]
tours$AUTOSUFF[tours$HHVEH == 0] <- 0
tours$AUTOSUFF[tours$HHVEH < tours$WORKERS & tours$HHVEH > 0] <- 1
tours$AUTOSUFF[tours$HHVEH >= tours$WORKERS & tours$HHVEH > 0] <- 2

# HHVEH X Workers CrossTab
write.csv(xtabs(~HHVEH+WORKERS, data = hh), "xtab_HHVEH_WORKERS.csv", row.names = T)


tours$num_tot_stops <- tours$num_ob_stops + tours$num_ib_stops

tours$OTAZ <- xwalk$TAZ[match(tours$orig_mgra, xwalk$MAZ)]
tours$DTAZ <- xwalk$TAZ[match(tours$dest_mgra, xwalk$MAZ)]
tours$OCOUNTY <- xwalk$COUNTYNAME[match(tours$orig_mgra, xwalk$MAZ)]
tours$DCOUNTY <- xwalk$COUNTYNAME[match(tours$dest_mgra, xwalk$MAZ)]
tours$OTAZ_ORIGINAL <- xwalk$TAZ_ORIGINAL[match(tours$OTAZ, xwalk$TAZ)]
tours$DTAZ_ORIGINAL <- xwalk$TAZ_ORIGINAL[match(tours$DTAZ, xwalk$TAZ)]
tours$OSDIST <- xwalk_SDist$district_name[match(tours$OTAZ_ORIGINAL, xwalk_SDist$TAZ_ORIGINAL)]
tours$DSDIST <- xwalk_SDist$district_name[match(tours$DTAZ_ORIGINAL, xwalk_SDist$TAZ_ORIGINAL)]
tours$SKIMDIST <- DST_SKM$dist[match(paste(tours$OTAZ, tours$DTAZ, sep = "-"), paste(DST_SKM$o, DST_SKM$d, sep = "-"))]

unique_joint_tours$HHVEH <- hh$HHVEH[match(unique_joint_tours$hh_id, hh$hh_id)]
unique_joint_tours$ADULTS <- hh$ADULTS[match(unique_joint_tours$hh_id, hh$hh_id)]
unique_joint_tours$AUTOSUFF[unique_joint_tours$HHVEH == 0] <- 0
unique_joint_tours$AUTOSUFF[unique_joint_tours$HHVEH < unique_joint_tours$ADULTS & unique_joint_tours$HHVEH > 0] <- 1
unique_joint_tours$AUTOSUFF[unique_joint_tours$HHVEH >= unique_joint_tours$ADULTS] <- 2

#Code tour purposes
tours$TOURPURP[tours$tour_purpose=="Work"] <- 1
tours$TOURPURP[tours$tour_purpose=="University"] <- 2
tours$TOURPURP[tours$tour_purpose=="School"] <- 3
tours$TOURPURP[tours$tour_purpose=="Escort"] <- 4
tours$TOURPURP[tours$tour_purpose=="Shop"] <- 5
tours$TOURPURP[tours$tour_purpose=="Maintenance"] <- 6
tours$TOURPURP[tours$tour_purpose=="Eating Out"] <- 7
tours$TOURPURP[tours$tour_purpose=="Visiting"] <- 8
tours$TOURPURP[tours$tour_purpose=="Discretionary"] <- 9
tours$TOURPURP[tours$tour_purpose=="Work-Based"] <- 10

#[0:Mandatory, 1: Indi Non Mand, 3: At Work]
tours$TOURCAT[tours$tour_purpose=="Work"] <- 0
tours$TOURCAT[tours$tour_purpose=="University"] <- 0
tours$TOURCAT[tours$tour_purpose=="School"] <- 0
tours$TOURCAT[tours$tour_purpose=="Escort"] <- 1
tours$TOURCAT[tours$tour_purpose=="Shop"] <- 1
tours$TOURCAT[tours$tour_purpose=="Maintenance"] <- 1
tours$TOURCAT[tours$tour_purpose=="Eating Out"] <- 1
tours$TOURCAT[tours$tour_purpose=="Visiting"] <- 1
tours$TOURCAT[tours$tour_purpose=="Discretionary"] <- 1
tours$TOURCAT[tours$tour_purpose=="Work-Based"] <- 2

#compute duration
tours$tourdur <- tours$end_period - tours$start_period + 1 #[to match survye]

#tours$TOURMODE[tours$tour_mode<=2] <- 1
#tours$TOURMODE[tours$tour_mode>=3 & tours$tour_mode<=5] <- 2
#tours$TOURMODE[tours$tour_mode>=6 & tours$tour_mode<=8] <- 3
#tours$TOURMODE[tours$tour_mode>=9] <- tours$tour_mode[tours$tour_mode>=9]-5

tours$TOURMODE[tours$tour_mode %in% c(1,2)]         <- 1 # SOV 
tours$TOURMODE[tours$tour_mode %in% c(3,4,5,15,16)] <- 2 # SR2, TAXI, TNC
tours$TOURMODE[tours$tour_mode %in% c(6,7,8)]       <- 3 # SR3
tours$TOURMODE[tours$tour_mode %in% c(9)]           <- 4 # Walk
tours$TOURMODE[tours$tour_mode %in% c(10)]          <- 5 # Bike
tours$TOURMODE[tours$tour_mode %in% c(11)]          <- 6 # WT
tours$TOURMODE[tours$tour_mode %in% c(12)]          <- 7 # PNR
tours$TOURMODE[tours$tour_mode %in% c(13,14)]       <- 8 # KNR_PERS, KNR_TNC
tours$TOURMODE[tours$tour_mode %in% c(17)]          <- 9 # SCHBUS

unique_joint_tours$JOINT_PURP[unique_joint_tours$tour_purpose=='Shop'] <- 5
unique_joint_tours$JOINT_PURP[unique_joint_tours$tour_purpose=='Maintenance'] <- 6
unique_joint_tours$JOINT_PURP[unique_joint_tours$tour_purpose=='Eating Out'] <- 7
unique_joint_tours$JOINT_PURP[unique_joint_tours$tour_purpose=='Visiting'] <- 8
unique_joint_tours$JOINT_PURP[unique_joint_tours$tour_purpose=='Discretionary'] <- 9




# get participant IDs
#unique_joint_tours$PER1[unique_joint_tours$NUMBER_HH>=1] <- substr(as.character(unique_joint_tours$tour_participants[unique_joint_tours$NUMBER_HH>=1]), 1, 1)
#unique_joint_tours$PER2[unique_joint_tours$NUMBER_HH>=2] <- substr(as.character(unique_joint_tours$tour_participants[unique_joint_tours$NUMBER_HH>=2]), 3, 3)
#unique_joint_tours$PER3[unique_joint_tours$NUMBER_HH>=3] <- substr(as.character(unique_joint_tours$tour_participants[unique_joint_tours$NUMBER_HH>=3]), 5, 5)
#unique_joint_tours$PER4[unique_joint_tours$NUMBER_HH>=4] <- substr(as.character(unique_joint_tours$tour_participants[unique_joint_tours$NUMBER_HH>=4]), 7, 7)
#unique_joint_tours$PER5[unique_joint_tours$NUMBER_HH>=5] <- substr(as.character(unique_joint_tours$tour_participants[unique_joint_tours$NUMBER_HH>=5]), 9, 9)
#unique_joint_tours$PER6[unique_joint_tours$NUMBER_HH>=6] <- substr(as.character(unique_joint_tours$tour_participants[unique_joint_tours$NUMBER_HH>=6]), 11, 11)
#unique_joint_tours$PER7[unique_joint_tours$NUMBER_HH>=7] <- substr(as.character(unique_joint_tours$tour_participants[unique_joint_tours$NUMBER_HH>=7]), 13, 13)
#unique_joint_tours$PER8[unique_joint_tours$NUMBER_HH>=8] <- substr(as.character(unique_joint_tours$tour_participants[unique_joint_tours$NUMBER_HH>=8]), 15, 15)
#unique_joint_tours$PER9[unique_joint_tours$NUMBER_HH>=9] <- substr(as.character(unique_joint_tours$tour_participants[unique_joint_tours$NUMBER_HH>=9]), 17, 17)
#unique_joint_tours$PER10[unique_joint_tours$NUMBER_HH>=10] <- substr(as.character(unique_joint_tours$tour_participants[unique_joint_tours$NUMBER_HH>=10]), 19, 20)
#unique_joint_tours$PER11[unique_joint_tours$NUMBER_HH>=11] <- substr(as.character(unique_joint_tours$tour_participants[unique_joint_tours$NUMBER_HH>=11]), 22, 23)
#unique_joint_tours$PER12[unique_joint_tours$NUMBER_HH>=12] <- substr(as.character(unique_joint_tours$tour_participants[unique_joint_tours$NUMBER_HH>=12]), 25, 27)

returnPERID <- function(str_txt, pos)
{
  ret_val <- unlist(strsplit(str_txt, " ", fixed = T))[pos]
  ret_val <- as.numeric(ret_val)
  return(ret_val)
}

PER1  <- apply(unique_joint_tours, 1, function(x) returnPERID(x["tour_participants"], 1))
PER2  <- apply(unique_joint_tours, 1, function(x) returnPERID(x["tour_participants"], 2))
PER3  <- apply(unique_joint_tours, 1, function(x) returnPERID(x["tour_participants"], 3))
PER4  <- apply(unique_joint_tours, 1, function(x) returnPERID(x["tour_participants"], 4))
PER5  <- apply(unique_joint_tours, 1, function(x) returnPERID(x["tour_participants"], 5))
PER6  <- apply(unique_joint_tours, 1, function(x) returnPERID(x["tour_participants"], 6))
PER7  <- apply(unique_joint_tours, 1, function(x) returnPERID(x["tour_participants"], 7))
PER8  <- apply(unique_joint_tours, 1, function(x) returnPERID(x["tour_participants"], 8))
PER9  <- apply(unique_joint_tours, 1, function(x) returnPERID(x["tour_participants"], 9))
PER10 <- apply(unique_joint_tours, 1, function(x) returnPERID(x["tour_participants"], 10))
PER11 <- apply(unique_joint_tours, 1, function(x) returnPERID(x["tour_participants"], 11))
PER12 <- apply(unique_joint_tours, 1, function(x) returnPERID(x["tour_participants"], 12))

PER1  <- data.frame(cbind(PER1))
PER2  <- data.frame(cbind(PER2))
PER3  <- data.frame(cbind(PER3))
PER4  <- data.frame(cbind(PER4))
PER5  <- data.frame(cbind(PER5))
PER6  <- data.frame(cbind(PER6))
PER7  <- data.frame(cbind(PER7))
PER8  <- data.frame(cbind(PER8))
PER9  <- data.frame(cbind(PER9))
PER10 <- data.frame(cbind(PER10))
PER11 <- data.frame(cbind(PER11))
PER12 <- data.frame(cbind(PER12))

unique_joint_tours <- cbind(unique_joint_tours,PER1,PER2,PER3,PER4,PER5,PER6,PER7,PER8,PER9,PER10,PER11,PER12)
unique_joint_tours[is.na(unique_joint_tours)] <- 0

unique_joint_tours$NUMBER_HH <- (unique_joint_tours$PER1>0) + 
  (unique_joint_tours$PER2>0) + 
  (unique_joint_tours$PER3>0) + 
  (unique_joint_tours$PER4>0) + 
  (unique_joint_tours$PER5>0) + 
  (unique_joint_tours$PER6>0) + 
  (unique_joint_tours$PER7>0) + 
  (unique_joint_tours$PER8>0) + 
  (unique_joint_tours$PER9>0) + 
  (unique_joint_tours$PER10>0) + 
  (unique_joint_tours$PER11>0) + 
  (unique_joint_tours$PER12>0)

# get person type for each participant
unique_joint_tours$PTYPE1 <- per$PERTYPE[match(paste(unique_joint_tours$hh_id,unique_joint_tours$PER1, sep = "-"), paste(per$hh_id,per$person_num, sep = "-"))]
unique_joint_tours$PTYPE2 <- per$PERTYPE[match(paste(unique_joint_tours$hh_id,unique_joint_tours$PER2, sep = "-"), paste(per$hh_id,per$person_num, sep = "-"))]
unique_joint_tours$PTYPE3 <- per$PERTYPE[match(paste(unique_joint_tours$hh_id,unique_joint_tours$PER3, sep = "-"), paste(per$hh_id,per$person_num, sep = "-"))]
unique_joint_tours$PTYPE4 <- per$PERTYPE[match(paste(unique_joint_tours$hh_id,unique_joint_tours$PER4, sep = "-"), paste(per$hh_id,per$person_num, sep = "-"))]
unique_joint_tours$PTYPE5 <- per$PERTYPE[match(paste(unique_joint_tours$hh_id,unique_joint_tours$PER5, sep = "-"), paste(per$hh_id,per$person_num, sep = "-"))]
unique_joint_tours$PTYPE6 <- per$PERTYPE[match(paste(unique_joint_tours$hh_id,unique_joint_tours$PER6, sep = "-"), paste(per$hh_id,per$person_num, sep = "-"))]
unique_joint_tours$PTYPE7 <- per$PERTYPE[match(paste(unique_joint_tours$hh_id,unique_joint_tours$PER7, sep = "-"), paste(per$hh_id,per$person_num, sep = "-"))]
unique_joint_tours$PTYPE8 <- per$PERTYPE[match(paste(unique_joint_tours$hh_id,unique_joint_tours$PER8, sep = "-"), paste(per$hh_id,per$person_num, sep = "-"))]
unique_joint_tours$PTYPE9 <- per$PERTYPE[match(paste(unique_joint_tours$hh_id,unique_joint_tours$PER9, sep = "-"), paste(per$hh_id,per$person_num, sep = "-"))]
unique_joint_tours$PTYPE10 <- per$PERTYPE[match(paste(unique_joint_tours$hh_id,unique_joint_tours$PER10, sep = "-"), paste(per$hh_id,per$person_num, sep = "-"))]
unique_joint_tours$PTYPE11 <- per$PERTYPE[match(paste(unique_joint_tours$hh_id,unique_joint_tours$PER11, sep = "-"), paste(per$hh_id,per$person_num, sep = "-"))]
unique_joint_tours$PTYPE12 <- per$PERTYPE[match(paste(unique_joint_tours$hh_id,unique_joint_tours$PER12, sep = "-"), paste(per$hh_id,per$person_num, sep = "-"))]

unique_joint_tours[is.na(unique_joint_tours)] <- 0

unique_joint_tours$num_tot_stops <- unique_joint_tours$num_ob_stops + unique_joint_tours$num_ib_stops

unique_joint_tours$OTAZ <- xwalk$TAZ[match(unique_joint_tours$orig_mgra, xwalk$MAZ)]
unique_joint_tours$DTAZ <- xwalk$TAZ[match(unique_joint_tours$dest_mgra, xwalk$MAZ)]
unique_joint_tours$OCOUNTY <- xwalk$COUNTYNAME[match(unique_joint_tours$orig_mgra, xwalk$MAZ)]
unique_joint_tours$DCOUNTY <- xwalk$COUNTYNAME[match(unique_joint_tours$dest_mgra, xwalk$MAZ)]
unique_joint_tours$OTAZ_ORIGINAL <- xwalk$TAZ_ORIGINAL[match(unique_joint_tours$OTAZ, xwalk$TAZ)]
unique_joint_tours$DTAZ_ORIGINAL <- xwalk$TAZ_ORIGINAL[match(unique_joint_tours$DTAZ, xwalk$TAZ)]
unique_joint_tours$OSDIST <- xwalk_SDist$district_name[match(unique_joint_tours$OTAZ_ORIGINAL, xwalk_SDist$TAZ_ORIGINAL)]
unique_joint_tours$DSDIST <- xwalk_SDist$district_name[match(unique_joint_tours$DTAZ_ORIGINAL, xwalk_SDist$TAZ_ORIGINAL)]

#compute duration
unique_joint_tours$tourdur <- unique_joint_tours$end_period - unique_joint_tours$start_period + 1 #[to match survye]

unique_joint_tours$SKIMDIST <- DST_SKM$dist[match(paste(unique_joint_tours$OTAZ, unique_joint_tours$DTAZ, sep = "-"), paste(DST_SKM$o, DST_SKM$d, sep = "-"))]


#unique_joint_tours$TOURMODE[unique_joint_tours$tour_mode<=2] <- 1
#unique_joint_tours$TOURMODE[unique_joint_tours$tour_mode>=3 & unique_joint_tours$tour_mode<=5] <- 2
#unique_joint_tours$TOURMODE[unique_joint_tours$tour_mode>=6 & unique_joint_tours$tour_mode<=8] <- 3
#unique_joint_tours$TOURMODE[unique_joint_tours$tour_mode>=9] <- unique_joint_tours$tour_mode[unique_joint_tours$tour_mode>=9]-5

unique_joint_tours$TOURMODE[unique_joint_tours$tour_mode %in% c(1,2)]         <- 1 # SOV 
unique_joint_tours$TOURMODE[unique_joint_tours$tour_mode %in% c(3,4,5,15,16)] <- 2 # SR2, TAXI, TNC
unique_joint_tours$TOURMODE[unique_joint_tours$tour_mode %in% c(6,7,8)]       <- 3 # SR3
unique_joint_tours$TOURMODE[unique_joint_tours$tour_mode %in% c(9)]           <- 4 # Walk
unique_joint_tours$TOURMODE[unique_joint_tours$tour_mode %in% c(10)]          <- 5 # Bike
unique_joint_tours$TOURMODE[unique_joint_tours$tour_mode %in% c(11)]          <- 6 # WT
unique_joint_tours$TOURMODE[unique_joint_tours$tour_mode %in% c(12)]          <- 7 # PNR
unique_joint_tours$TOURMODE[unique_joint_tours$tour_mode %in% c(13,14)]       <- 8 # KNR_PERS, KNR_TNC
unique_joint_tours$TOURMODE[unique_joint_tours$tour_mode %in% c(17)]          <- 9 # SCHBUS


#create person level file for joint tours
jtours_per <- melt(unique_joint_tours[,c("hh_id","tour_id", "PER1","PER2","PER3","PER4","PER5","PER6","PER7","PER8", "PER9", "PER10", "PER11", "PER12")], 
                   id = c("hh_id","tour_id"))
jtours_per$value <- as.numeric(jtours_per$value)
colnames(jtours_per) <- c("hh_id","tour_id","variable","perno")
jtours_per$variable <- NULL
jtours_per <- jtours_per[jtours_per$perno>0,]


# create a combined temp tour file for creating stop freq model summary
temp_tour1 <- tours[,c("TOURPURP","num_ob_stops","num_ib_stops")]
temp_tour2 <- unique_joint_tours[,c("JOINT_PURP","num_ob_stops","num_ib_stops")]
colnames(temp_tour2) <- colnames(temp_tour1)
temp_tour <- rbind(temp_tour1,temp_tour2)

# code stop frequency model alternatives
temp_tour$STOP_FREQ_ALT[temp_tour$num_ob_stops==0 & temp_tour$num_ib_stops==0] <- 1
temp_tour$STOP_FREQ_ALT[temp_tour$num_ob_stops==0 & temp_tour$num_ib_stops==1] <- 2
temp_tour$STOP_FREQ_ALT[temp_tour$num_ob_stops==0 & temp_tour$num_ib_stops==2] <- 3
temp_tour$STOP_FREQ_ALT[temp_tour$num_ob_stops==0 & temp_tour$num_ib_stops>=3] <- 4
temp_tour$STOP_FREQ_ALT[temp_tour$num_ob_stops==1 & temp_tour$num_ib_stops==0] <- 5
temp_tour$STOP_FREQ_ALT[temp_tour$num_ob_stops==1 & temp_tour$num_ib_stops==1] <- 6
temp_tour$STOP_FREQ_ALT[temp_tour$num_ob_stops==1 & temp_tour$num_ib_stops==2] <- 7
temp_tour$STOP_FREQ_ALT[temp_tour$num_ob_stops==1 & temp_tour$num_ib_stops>=3] <- 8
temp_tour$STOP_FREQ_ALT[temp_tour$num_ob_stops==2 & temp_tour$num_ib_stops==0] <- 9
temp_tour$STOP_FREQ_ALT[temp_tour$num_ob_stops==2 & temp_tour$num_ib_stops==1] <- 10
temp_tour$STOP_FREQ_ALT[temp_tour$num_ob_stops==2 & temp_tour$num_ib_stops==2] <- 11
temp_tour$STOP_FREQ_ALT[temp_tour$num_ob_stops==2 & temp_tour$num_ib_stops>=3] <- 12
temp_tour$STOP_FREQ_ALT[temp_tour$num_ob_stops>=3 & temp_tour$num_ib_stops==0] <- 13
temp_tour$STOP_FREQ_ALT[temp_tour$num_ob_stops>=3 & temp_tour$num_ib_stops==1] <- 14
temp_tour$STOP_FREQ_ALT[temp_tour$num_ob_stops>=3 & temp_tour$num_ib_stops==2] <- 15
temp_tour$STOP_FREQ_ALT[temp_tour$num_ob_stops>=3 & temp_tour$num_ib_stops>=3] <- 16
temp_tour$STOP_FREQ_ALT[is.na(temp_tour$STOP_FREQ_ALT)] <- 0

stopFreqModel_summary <- xtabs(~STOP_FREQ_ALT+TOURPURP, data = temp_tour[temp_tour$TOURPURP<=10,])
write.csv(stopFreqModel_summary, "stopFreqModel_summary.csv", row.names = T)


# Process Trip file
#------------------
#trips$TOURMODE[trips$tour_mode<=2] <- 1
#trips$TOURMODE[trips$tour_mode>=3 & trips$tour_mode<=5] <- 2
#trips$TOURMODE[trips$tour_mode>=6 & trips$tour_mode<=8] <- 3
#trips$TOURMODE[trips$tour_mode>=9] <- trips$tour_mode[trips$tour_mode>=9]-5

trips$TOURMODE[trips$tour_mode %in% c(1,2)]         <- 1 # SOV 
trips$TOURMODE[trips$tour_mode %in% c(3,4,5,15,16)] <- 2 # SR2, TAXI, TNC
trips$TOURMODE[trips$tour_mode %in% c(6,7,8)]       <- 3 # SR3
trips$TOURMODE[trips$tour_mode %in% c(9)]           <- 4 # Walk
trips$TOURMODE[trips$tour_mode %in% c(10)]          <- 5 # Bike
trips$TOURMODE[trips$tour_mode %in% c(11)]          <- 6 # WT
trips$TOURMODE[trips$tour_mode %in% c(12)]          <- 7 # PNR
trips$TOURMODE[trips$tour_mode %in% c(13,14)]       <- 8 # KNR_PERS, KNR_TNC
trips$TOURMODE[trips$tour_mode %in% c(17)]          <- 9 # SCHBUS

#trips$TRIPMODE[trips$trip_mode<=2] <- 1
#trips$TRIPMODE[trips$trip_mode>=3 & trips$trip_mode<=5] <- 2
#trips$TRIPMODE[trips$trip_mode>=6 & trips$trip_mode<=8] <- 3
#trips$TRIPMODE[trips$trip_mode>=9] <- trips$trip_mode[trips$trip_mode>=9]-5

trips$TRIPMODE[trips$trip_mode %in% c(1,2)]         <- 1 # SOV 
trips$TRIPMODE[trips$trip_mode %in% c(3,4,5,15,16)] <- 2 # SR2, TAXI, TNC
trips$TRIPMODE[trips$trip_mode %in% c(6,7,8)]       <- 3 # SR3
trips$TRIPMODE[trips$trip_mode %in% c(9)]           <- 4 # Walk
trips$TRIPMODE[trips$trip_mode %in% c(10)]          <- 5 # Bike
trips$TRIPMODE[trips$trip_mode %in% c(11)]          <- 6 # WT
trips$TRIPMODE[trips$trip_mode %in% c(12)]          <- 7 # PNR
trips$TRIPMODE[trips$trip_mode %in% c(13,14)]       <- 8 # KNR_PERS, KNR_TNC
trips$TRIPMODE[trips$trip_mode %in% c(17)]          <- 9 # SCHBUS


#Code tour purposes
trips$TOURPURP[trips$tour_purpose=="Home"] <- 0
trips$TOURPURP[trips$tour_purpose=="Work"] <- 1
trips$TOURPURP[trips$tour_purpose=="University"] <- 2
trips$TOURPURP[trips$tour_purpose=="School"] <- 3
trips$TOURPURP[trips$tour_purpose=="Escort"] <- 4
trips$TOURPURP[trips$tour_purpose=="Shop"] <- 5
trips$TOURPURP[trips$tour_purpose=="Maintenance"] <- 6
trips$TOURPURP[trips$tour_purpose=="Eating Out"] <- 7
trips$TOURPURP[trips$tour_purpose=="Visiting"] <- 8
trips$TOURPURP[trips$tour_purpose=="Discretionary"] <- 9
trips$TOURPURP[trips$tour_purpose=="Work-Based" | trips$tour_purpose=="work related"] <- 10

trips$OPURP[trips$orig_purpose=="Home"] <- 0
trips$OPURP[trips$orig_purpose=="Work"] <- 1
trips$OPURP[trips$orig_purpose=="University"] <- 2
trips$OPURP[trips$orig_purpose=="School"] <- 3
trips$OPURP[trips$orig_purpose=="Escort"] <- 4
trips$OPURP[trips$orig_purpose=="Shop"] <- 5
trips$OPURP[trips$orig_purpose=="Maintenance"] <- 6
trips$OPURP[trips$orig_purpose=="Eating Out"] <- 7
trips$OPURP[trips$orig_purpose=="Visiting"] <- 8
trips$OPURP[trips$orig_purpose=="Discretionary"] <- 9
trips$OPURP[trips$orig_purpose=="Work-Based" | trips$orig_purpose=="work related"] <- 10

trips$DPURP[trips$dest_purpose=="Home"] <- 0
trips$DPURP[trips$dest_purpose=="Work"] <- 1
trips$DPURP[trips$dest_purpose=="University"] <- 2
trips$DPURP[trips$dest_purpose=="School"] <- 3
trips$DPURP[trips$dest_purpose=="Escort"] <- 4
trips$DPURP[trips$dest_purpose=="Shop"] <- 5
trips$DPURP[trips$dest_purpose=="Maintenance"] <- 6
trips$DPURP[trips$dest_purpose=="Eating Out"] <- 7
trips$DPURP[trips$dest_purpose=="Visiting"] <- 8
trips$DPURP[trips$dest_purpose=="Discretionary"] <- 9
trips$DPURP[trips$dest_purpose=="Work-Based" | trips$dest_purpose=="work related"] <- 10

#[0:Mandatory, 1: Indi Non Mand, 3: At Work]
trips$TOURCAT[trips$tour_purpose=="Work"] <- 0
trips$TOURCAT[trips$tour_purpose=="University"] <- 0
trips$TOURCAT[trips$tour_purpose=="School"] <- 0
trips$TOURCAT[trips$tour_purpose=="Escort"] <- 1
trips$TOURCAT[trips$tour_purpose=="Shop"] <- 1
trips$TOURCAT[trips$tour_purpose=="Maintenance"] <- 1
trips$TOURCAT[trips$tour_purpose=="Eating Out"] <- 1
trips$TOURCAT[trips$tour_purpose=="Visiting"] <- 1
trips$TOURCAT[trips$tour_purpose=="Discretionary"] <- 1
trips$TOURCAT[trips$tour_purpose=="Work-Based"] <- 2

#Mark stops and get other attributes
nr <- nrow(trips)
trips$inb_next <- 0
trips$inb_next[1:nr-1] <- trips$inbound[2:nr]
trips$stops[trips$DPURP>0 & ((trips$inbound==0 & trips$inb_next==0) | (trips$inbound==1 & trips$inb_next==1))] <- 1
trips$stops[is.na(trips$stops)] <- 0

trips$OTAZ <- xwalk$TAZ[match(trips$orig_mgra, xwalk$MAZ)]
trips$DTAZ <- xwalk$TAZ[match(trips$dest_mgra, xwalk$MAZ)]
trips$OCOUNTY <- xwalk$COUNTYNAME[match(trips$orig_mgra, xwalk$MAZ)]
trips$DCOUNTY <- xwalk$COUNTYNAME[match(trips$dest_mgra, xwalk$MAZ)]
trips$OTAZ_ORIGINAL <- xwalk$TAZ_ORIGINAL[match(trips$OTAZ, xwalk$TAZ)]
trips$DTAZ_ORIGINAL <- xwalk$TAZ_ORIGINAL[match(trips$DTAZ, xwalk$TAZ)]
trips$OSDIST <- xwalk_SDist$district_name[match(trips$OTAZ_ORIGINAL, xwalk_SDist$TAZ_ORIGINAL)]
trips$DSDIST <- xwalk_SDist$district_name[match(trips$DTAZ_ORIGINAL, xwalk_SDist$TAZ_ORIGINAL)]

trips$TOUROTAZ <- tours$OTAZ[match(trips$hh_id*1000+trips$person_num*100+trips$TOURCAT*10+trips$tour_id, 
                                   tours$hh_id*1000+tours$person_num*100+tours$TOURCAT*10+tours$tour_id)]
trips$TOURDTAZ <- tours$DTAZ[match(trips$hh_id*1000+trips$person_num*100+trips$TOURCAT*10+trips$tour_id, 
                                   tours$hh_id*1000+tours$person_num*100+tours$TOURCAT*10+tours$tour_id)]	

trips$od_dist <- DST_SKM$dist[match(paste(trips$OTAZ, trips$DTAZ, sep = "-"), paste(DST_SKM$o, DST_SKM$d, sep = "-"))]
trips$od_dist[is.na(trips$od_dist)] <- 0


#create stops table
stops <- trips[trips$stops==1,]

stops$finaldestTAZ[stops$inbound==0] <- stops$TOURDTAZ[stops$inbound==0]
stops$finaldestTAZ[stops$inbound==1] <- stops$TOUROTAZ[stops$inbound==1]

stops$od_dist <- DST_SKM$dist[match(paste(stops$OTAZ, stops$finaldestTAZ, sep = "-"), paste(DST_SKM$o, DST_SKM$d, sep = "-"))]
stops$os_dist <- DST_SKM$dist[match(paste(stops$OTAZ, stops$DTAZ, sep = "-"), paste(DST_SKM$o, DST_SKM$d, sep = "-"))]
stops$sd_dist <- DST_SKM$dist[match(paste(stops$DTAZ, stops$finaldestTAZ, sep = "-"), paste(DST_SKM$o, DST_SKM$d, sep = "-"))]

stops$out_dir_dist <- stops$os_dist + stops$sd_dist - stops$od_dist									

#joint trip
#jtrips$TOURMODE[jtrips$tour_mode<=2] <- 1
#jtrips$TOURMODE[jtrips$tour_mode>=3 & jtrips$tour_mode<=5] <- 2
#jtrips$TOURMODE[jtrips$tour_mode>=6 & jtrips$tour_mode<=8] <- 3
#jtrips$TOURMODE[jtrips$tour_mode>=9] <- jtrips$tour_mode[jtrips$tour_mode>=9]-5

jtrips$TOURMODE[jtrips$trip_mode %in% c(1,2)]         <- 1 # SOV 
jtrips$TOURMODE[jtrips$trip_mode %in% c(3,4,5,15,16)] <- 2 # SR2, TAXI, TNC
jtrips$TOURMODE[jtrips$trip_mode %in% c(6,7,8)]       <- 3 # SR3
jtrips$TOURMODE[jtrips$trip_mode %in% c(9)]           <- 4 # Walk
jtrips$TOURMODE[jtrips$trip_mode %in% c(10)]          <- 5 # Bike
jtrips$TOURMODE[jtrips$trip_mode %in% c(11)]          <- 6 # WT
jtrips$TOURMODE[jtrips$trip_mode %in% c(12)]          <- 7 # PNR
jtrips$TOURMODE[jtrips$trip_mode %in% c(13,14)]       <- 8 # KNR_PERS, KNR_TNC
jtrips$TOURMODE[jtrips$trip_mode %in% c(17)]          <- 9 # SCHBUS


#jtrips$TRIPMODE[jtrips$trip_mode<=2] <- 1
#jtrips$TRIPMODE[jtrips$trip_mode>=3 & jtrips$trip_mode<=5] <- 2
#jtrips$TRIPMODE[jtrips$trip_mode>=6 & jtrips$trip_mode<=8] <- 3
#jtrips$TRIPMODE[jtrips$trip_mode>=9] <- jtrips$trip_mode[jtrips$trip_mode>=9]-5

jtrips$TRIPMODE[jtrips$trip_mode %in% c(1,2)]         <- 1 # SOV 
jtrips$TRIPMODE[jtrips$trip_mode %in% c(3,4,5,15,16)] <- 2 # SR2, TAXI, TNC
jtrips$TRIPMODE[jtrips$trip_mode %in% c(6,7,8)]       <- 3 # SR3
jtrips$TRIPMODE[jtrips$trip_mode %in% c(9)]           <- 4 # Walk
jtrips$TRIPMODE[jtrips$trip_mode %in% c(10)]          <- 5 # Bike
jtrips$TRIPMODE[jtrips$trip_mode %in% c(11)]          <- 6 # WT
jtrips$TRIPMODE[jtrips$trip_mode %in% c(12)]          <- 7 # PNR
jtrips$TRIPMODE[jtrips$trip_mode %in% c(13,14)]       <- 8 # KNR_PERS, KNR_TNC
jtrips$TRIPMODE[jtrips$trip_mode %in% c(17)]          <- 9 # SCHBUS


#Code joint tour purposes
jtrips$TOURPURP[jtrips$tour_purpose=="Work"] <- 1
jtrips$TOURPURP[jtrips$tour_purpose=="University"] <- 2
jtrips$TOURPURP[jtrips$tour_purpose=="School"] <- 3
jtrips$TOURPURP[jtrips$tour_purpose=="Escort"] <- 4
jtrips$TOURPURP[jtrips$tour_purpose=="Shop"] <- 5
jtrips$TOURPURP[jtrips$tour_purpose=="Maintenance"] <- 6
jtrips$TOURPURP[jtrips$tour_purpose=="Eating Out"] <- 7
jtrips$TOURPURP[jtrips$tour_purpose=="Visiting"] <- 8
jtrips$TOURPURP[jtrips$tour_purpose=="Discretionary"] <- 9
jtrips$TOURPURP[jtrips$tour_purpose=="Work-Based" | jtrips$tour_purpose=="work related"] <- 10

jtrips$OPURP[jtrips$orig_purpose=="Home"] <- 0
jtrips$OPURP[jtrips$orig_purpose=="Work"] <- 1
jtrips$OPURP[jtrips$orig_purpose=="University"] <- 2
jtrips$OPURP[jtrips$orig_purpose=="School"] <- 3
jtrips$OPURP[jtrips$orig_purpose=="Escort"] <- 4
jtrips$OPURP[jtrips$orig_purpose=="Shop"] <- 5
jtrips$OPURP[jtrips$orig_purpose=="Maintenance"] <- 6
jtrips$OPURP[jtrips$orig_purpose=="Eating Out"] <- 7
jtrips$OPURP[jtrips$orig_purpose=="Visiting"] <- 8
jtrips$OPURP[jtrips$orig_purpose=="Discretionary"] <- 9
jtrips$OPURP[jtrips$orig_purpose=="Work-Based" | jtrips$orig_purpose=="work related"] <- 10

jtrips$DPURP[jtrips$dest_purpose=="Home"] <- 0
jtrips$DPURP[jtrips$dest_purpose=="Work"] <- 1
jtrips$DPURP[jtrips$dest_purpose=="University"] <- 2
jtrips$DPURP[jtrips$dest_purpose=="School"] <- 3
jtrips$DPURP[jtrips$dest_purpose=="Escort"] <- 4
jtrips$DPURP[jtrips$dest_purpose=="Shop"] <- 5
jtrips$DPURP[jtrips$dest_purpose=="Maintenance"] <- 6
jtrips$DPURP[jtrips$dest_purpose=="Eating Out"] <- 7
jtrips$DPURP[jtrips$dest_purpose=="Visiting"] <- 8
jtrips$DPURP[jtrips$dest_purpose=="Discretionary"] <- 9
jtrips$DPURP[jtrips$dest_purpose=="Work-Based" | jtrips$dest_purpose=="work related"] <- 10

#[0:Mandatory, 1: Indi Non Mand, 3: At Work]
jtrips$TOURCAT[jtrips$tour_purpose=="Work"] <- 0
jtrips$TOURCAT[jtrips$tour_purpose=="University"] <- 0
jtrips$TOURCAT[jtrips$tour_purpose=="School"] <- 0
jtrips$TOURCAT[jtrips$tour_purpose=="Escort"] <- 1
jtrips$TOURCAT[jtrips$tour_purpose=="Shop"] <- 1
jtrips$TOURCAT[jtrips$tour_purpose=="Maintenance"] <- 1
jtrips$TOURCAT[jtrips$tour_purpose=="Eating Out"] <- 1
jtrips$TOURCAT[jtrips$tour_purpose=="Visiting"] <- 1
jtrips$TOURCAT[jtrips$tour_purpose=="Discretionary"] <- 1
jtrips$TOURCAT[jtrips$tour_purpose=="Work-Based"] <- 2

#Mark stops and get other attributes
nr <- nrow(jtrips)
jtrips$inb_next <- 0
jtrips$inb_next[1:nr-1] <- jtrips$inbound[2:nr]
jtrips$stops[jtrips$DPURP>0 & ((jtrips$inbound==0 & jtrips$inb_next==0) | (jtrips$inbound==1 & jtrips$inb_next==1))] <- 1
jtrips$stops[is.na(jtrips$stops)] <- 0

jtrips$OTAZ <- xwalk$TAZ[match(jtrips$orig_mgra, xwalk$MAZ)]
jtrips$DTAZ <- xwalk$TAZ[match(jtrips$dest_mgra, xwalk$MAZ)]
jtrips$OCOUNTY <- xwalk$COUNTYNAME[match(jtrips$orig_mgra, xwalk$MAZ)]
jtrips$DCOUNTY <- xwalk$COUNTYNAME[match(jtrips$dest_mgra, xwalk$MAZ)]
jtrips$OTAZ_ORIGINAL <- xwalk$TAZ_ORIGINAL[match(jtrips$OTAZ, xwalk$TAZ)]
jtrips$DTAZ_ORIGINAL <- xwalk$TAZ_ORIGINAL[match(jtrips$OTAZ, xwalk$TAZ)]
jtrips$OSDIST <- xwalk_SDist$district_name[match(jtrips$OTAZ_ORIGINAL, xwalk_SDist$TAZ_ORIGINAL)]
jtrips$DSDIST <- xwalk_SDist$district_name[match(jtrips$DTAZ_ORIGINAL, xwalk_SDist$TAZ_ORIGINAL)]

jtrips$TOUROTAZ <- unique_joint_tours$OTAZ[match(jtrips$hh_id*1000+jtrips$tour_id, 
                                                 unique_joint_tours$hh_id*1000+unique_joint_tours$tour_id)]
jtrips$TOURDTAZ <- unique_joint_tours$DTAZ[match(jtrips$hh_id*1000+jtrips$tour_id, 
                                                 unique_joint_tours$hh_id*1000+unique_joint_tours$tour_id)]	

#create stops table
jstops <- jtrips[jtrips$stops==1,]

jstops$finaldestTAZ[jstops$inbound==0] <- jstops$TOURDTAZ[jstops$inbound==0]
jstops$finaldestTAZ[jstops$inbound==1] <- jstops$TOUROTAZ[jstops$inbound==1]

jstops$od_dist <- DST_SKM$dist[match(paste(jstops$OTAZ, jstops$finaldestTAZ, sep = "-"), paste(DST_SKM$o, DST_SKM$d, sep = "-"))]
jstops$os_dist <- DST_SKM$dist[match(paste(jstops$OTAZ, jstops$DTAZ, sep = "-"), paste(DST_SKM$o, DST_SKM$d, sep = "-"))]
jstops$sd_dist <- DST_SKM$dist[match(paste(jstops$DTAZ, jstops$finaldestTAZ, sep = "-"), paste(DST_SKM$o, DST_SKM$d, sep = "-"))]

jstops$out_dir_dist <- jstops$os_dist + jstops$sd_dist - jstops$od_dist		

#---------------------------------------------------------------------------

# Recode workrelated tours which are not at work subtour as work tour
#tours$TOURPURP[tours$TOURPURP == 10 & tours$IS_SUBTOUR == 0] <- 1

workCounts   <- count(tours, c("hh_id", "person_num"), "TOURPURP == 1") #[excluding at work subtours]
atWorkCounts <- count(tours, c("hh_id", "person_num"), "TOURPURP == 10")
schlCounts   <- count(tours, c("hh_id", "person_num"), "TOURPURP == 2 | TOURPURP == 3")
inmCounts    <- count(tours, c("hh_id", "person_num"), "TOURPURP>=4 & TOURPURP<=9")
itourCounts  <- count(tours, c("hh_id", "person_num"), "TOURPURP <= 9")  #number of tours per person [excluding at work subtours]
jtourCounts  <- count(jtours_per, c("hh_id", "perno"), "tour_id>=0") 

# -----------------------
# added for calibration by nagendra.dhakar@rsginc.com
# for indivudal NM tour generation
tours_temp <- tours[,c("hh_id", "person_num", "TOURPURP")]
tours_temp$FULLY_JOINT <- 0
jtours_temp <- jtours_per[,c("hh_id", "perno", "tour_id")]
colnames(jtours_temp)[colnames(jtours_temp)=="perno"] <- "person_num"

jtours_temp$TOURPURP <- unique_joint_tours$JOINT_PURP[match(paste(jtours_temp$hh_id, jtours_temp$tour_id), 
                                                            paste(unique_joint_tours$hh_id, unique_joint_tours$tour_id))]
jtours_temp$FULLY_JOINT <- 1
jtours_temp <- jtours_temp[,-c("tour_id")]

all_tours <- rbind(tours_temp, jtours_temp)

#all_tours$cdap <- hh$cdap_pattern[match(all_tours$hh_id, hh$hh_id)]

workCounts_temp <- count(all_tours, c("hh_id", "person_num"), "TOURPURP == 1")
schlCounts_temp <- count(all_tours, c("hh_id", "person_num"), "TOURPURP == 2 | TOURPURP == 3")
inmCounts_temp <- count(all_tours, c("hh_id", "person_num"), "TOURPURP>=4 & TOURPURP<=9 & FULLY_JOINT==0")  
atWorkCounts_temp <- count(all_tours, c("hh_id", "person_num"), "TOURPURP == 10")
jToursCounts_temp <- count(all_tours, c("hh_id", "person_num"), "FULLY_JOINT==1")  


colnames(workCounts_temp)[3] <- "freq_work"
colnames(schlCounts_temp)[3] <- "freq_schl"
colnames(inmCounts_temp)[3] <- "freq_inm"
colnames(atWorkCounts_temp)[3] <- "freq_atwork"
colnames(jToursCounts_temp)[3] <- "freq_jtours"

temp <- merge(workCounts_temp, schlCounts_temp, by = c("hh_id", "person_num"))
temp1 <- merge(temp, inmCounts_temp, by = c("hh_id", "person_num"))
temp1$freq_m <- temp1$freq_work + temp1$freq_schl
temp1$freq_itours <- temp1$freq_m+temp1$freq_inm

#joint tours
##identify persons that made joint tour
#temp_joint <- melt(unique_joint_tours[,c("hh_id","tour_id" ,"PER1", "PER2", "PER3", "PER4", "PER5", "PER6", "PER7", "PER8")], id = c("hh_id","tour_id"))
#colnames(temp_joint) <- c("hh_id", "tour_id", "var", "person_num")
#temp_joint <- as.data.frame(temp_joint)
#temp_joint$person_num <- as.integer(temp_joint$person_num)
#temp_joint$joint<- 0
#temp_joint$joint[temp_joint$person_num>0] <- 1
#
#temp_joint <- temp_joint[temp_joint$joint==1,]
#person_unique_joint <- aggregate(joint~hh_id+person_num, temp_joint, sum)

temp2 <- merge(temp1, jToursCounts_temp, by = c("hh_id", "person_num"), all = T)
temp2 <- merge(temp2, atWorkCounts_temp, by = c("hh_id", "person_num"), all = T)
temp2[is.na(temp2)] <- 0

#add number of joint tours to non-mandatory
temp2$freq_nm <- temp2$freq_inm + temp2$freq_jtours

#get person type
temp2$PERTYPE <- per$PERTYPE[match(temp2$hh_id*10+temp2$person_num,per$hh_id*10+per$person_num)]

#total tours
temp2$total_tours <- temp2$freq_nm+temp2$freq_m+temp2$freq_atwork

persons_mand <- temp2[temp2$freq_m>0,]   #persons with atleast 1 mandatory tours
persons_nomand <- temp2[temp2$freq_m==0,] #active persons with 0 mandatory tours

# joint tours counted as iNM for calibraiton purpose [model does not allow 0 iNM and >0 JT]

freq_nmtours_mand <- count(persons_mand, c("PERTYPE","freq_nm"))
freq_nmtours_nomand <- count(persons_nomand, c("PERTYPE","freq_nm"))
test <- count(temp2, c("PERTYPE","freq_inm","freq_m","freq_nm","freq_atwork"))
write.csv(test, "tour_rate_debug.csv", row.names = F)
write.csv(temp2,"temp2.csv", row.names = F)

write.table("Non-Mandatory Tours for Persons with at-least 1 Mandatory Tour", "indivNMTourFreq.csv", sep = ",", row.names = F, append = F)
write.table(freq_nmtours_mand, "indivNMTourFreq.csv", sep = ",", row.names = F, append = T)
write.table("Non-Mandatory Tours for Active Persons with 0 Mandatory Tour", "indivNMTourFreq.csv", sep = ",", row.names = F, append = T)
write.table(freq_nmtours_nomand, "indivNMTourFreq.csv", sep = ",", row.names = F, append = TRUE)

# end of addition for calibration
# -----------------------

joint5 <- count(unique_joint_tours, c("hh_id"), "JOINT_PURP==5")
joint6 <- count(unique_joint_tours, c("hh_id"), "JOINT_PURP==6")
joint7 <- count(unique_joint_tours, c("hh_id"), "JOINT_PURP==7")
joint8 <- count(unique_joint_tours, c("hh_id"), "JOINT_PURP==8")
joint9 <- count(unique_joint_tours, c("hh_id"), "JOINT_PURP==9")

hh$joint5 <- joint5$freq[match(hh$hh_id, joint5$hh_id)]
hh$joint6 <- joint6$freq[match(hh$hh_id, joint6$hh_id)]
hh$joint7 <- joint7$freq[match(hh$hh_id, joint7$hh_id)]
hh$joint8 <- joint8$freq[match(hh$hh_id, joint8$hh_id)]
hh$joint9 <- joint9$freq[match(hh$hh_id, joint9$hh_id)]
hh$jtours <- hh$joint5+hh$joint6+hh$joint7+hh$joint8+hh$joint9

hh$joint5[is.na(hh$joint5)] <- 0
hh$joint6[is.na(hh$joint6)] <- 0
hh$joint7[is.na(hh$joint7)] <- 0
hh$joint8[is.na(hh$joint8)] <- 0
hh$joint9[is.na(hh$joint9)] <- 0
hh$jtours[is.na(hh$jtours)] <- 0

#joint tour indicator
hh$JOINT <- 0
hh$JOINT[substr(hh$cdap_pattern, nchar(as.character(hh$cdap_pattern)), nchar(as.character(hh$cdap_pattern)))=="j"] <- 1

# code JTF category
hh$jtf[hh$jtours==0] <- 1 
hh$jtf[hh$joint5==1] <- 2
hh$jtf[hh$joint6==1] <- 3
hh$jtf[hh$joint7==1] <- 4
hh$jtf[hh$joint8==1] <- 5
hh$jtf[hh$joint9==1] <- 6

hh$jtf[hh$joint5>=2] <- 7
hh$jtf[hh$joint6>=2] <- 8
hh$jtf[hh$joint7>=2] <- 9
hh$jtf[hh$joint8>=2] <- 10
hh$jtf[hh$joint9>=2] <- 11

hh$jtf[hh$joint5>=1 & hh$joint6>=1] <- 12
hh$jtf[hh$joint5>=1 & hh$joint7>=1] <- 13
hh$jtf[hh$joint5>=1 & hh$joint8>=1] <- 14
hh$jtf[hh$joint5>=1 & hh$joint9>=1] <- 15

hh$jtf[hh$joint6>=1 & hh$joint7>=1] <- 16
hh$jtf[hh$joint6>=1 & hh$joint8>=1] <- 17
hh$jtf[hh$joint6>=1 & hh$joint9>=1] <- 18

hh$jtf[hh$joint7>=1 & hh$joint8>=1] <- 19
hh$jtf[hh$joint7>=1 & hh$joint9>=1] <- 20

hh$jtf[hh$joint8>=1 & hh$joint9>=1] <- 21

per$workTours   <- workCounts$freq[match(per$hh_id*100+per$person_num, workCounts$hh_id*100+workCounts$person_num)]
per$atWorkTours <- atWorkCounts$freq[match(per$hh_id*100+per$person_num, atWorkCounts$hh_id*100+atWorkCounts$person_num)]
per$schlTours   <- schlCounts$freq[match(per$hh_id*100+per$person_num, schlCounts$hh_id*100+schlCounts$person_num)]
per$inmTours    <- inmCounts$freq[match(per$hh_id*100+per$person_num, inmCounts$hh_id*100+inmCounts$person_num)]
per$inmTours[is.na(per$inmTours)] <- 0
per$inumTours <- itourCounts$freq[match(per$hh_id*100+per$person_num, itourCounts$hh_id*100+itourCounts$person_num)]
per$inumTours[is.na(per$inumTours)] <- 0
per$jnumTours <- jtourCounts$freq[match(per$hh_id*100+per$person_num, jtourCounts$hh_id*100+jtourCounts$perno)]
per$jnumTours[is.na(per$jnumTours)] <- 0
per$numTours <- per$inmTours + per$jnumTours

per$workTours[is.na(per$workTours)] <- 0
per$schlTours[is.na(per$schlTours)] <- 0
per$atWorkTours[is.na(per$atWorkTours)] <- 0

# Total tours by person type
per$numTours[is.na(per$numTours)] <- 0
toursPertypeDistbn <- count(tours[tours$PERTYPE>0 & tours$TOURPURP!=10,], c("PERTYPE"))
write.csv(toursPertypeDistbn, "toursPertypeDistbn.csv", row.names = TRUE)

# count joint tour fr each person type
temp_joint <- melt(unique_joint_tours[, c("hh_id","tour_id","PTYPE1","PTYPE2","PTYPE3","PTYPE4","PTYPE5","PTYPE6","PTYPE7","PTYPE8")], id = c("hh_id", "tour_id"))
names(temp_joint)[names(temp_joint)=="value"] <- "PERTYPE"
jtoursPertypeDistbn <- count(temp_joint[temp_joint$PERTYPE>0,], c("PERTYPE"))

# Total tours by person type for visualizer
totaltoursPertypeDistbn <- toursPertypeDistbn
totaltoursPertypeDistbn$freq <- totaltoursPertypeDistbn$freq + jtoursPertypeDistbn$freq
write.csv(totaltoursPertypeDistbn, "total_tours_by_pertype_vis.csv", row.names = F)


# Total indi NM tours by person type and purpose
tours_pertype_purpose <- count(tours[tours$TOURPURP>=4 & tours$TOURPURP<=9,], c("PERTYPE", "TOURPURP"))
write.csv(tours_pertype_purpose, "tours_pertype_purpose.csv", row.names = TRUE)

tours_pertype_purpose <- xtabs(freq~PERTYPE+TOURPURP, tours_pertype_purpose)
tours_pertype_purpose[is.na(tours_pertype_purpose)] <- 0
tours_pertype_purpose <- addmargins(as.table(tours_pertype_purpose))
tours_pertype_purpose <- as.data.frame.matrix(tours_pertype_purpose)

totalPersons <- sum(pertypeDistbn$freq)
totalPersons_DF <- data.frame("Total", totalPersons)
colnames(totalPersons_DF) <- colnames(pertypeDistbn)
pertypeDF <- rbind(pertypeDistbn, totalPersons_DF)
nm_tour_rates <- tours_pertype_purpose/pertypeDF$freq
nm_tour_rates$pertype <- row.names(nm_tour_rates)
nm_tour_rates <- melt(nm_tour_rates, id = c("pertype"))
colnames(nm_tour_rates) <- c("pertype", "tour_purp", "tour_rate")
nm_tour_rates$pertype <- as.character(nm_tour_rates$pertype)
nm_tour_rates$tour_purp <- as.character(nm_tour_rates$tour_purp)
nm_tour_rates$pertype[nm_tour_rates$pertype=="Sum"] <- "All"
nm_tour_rates$tour_purp[nm_tour_rates$tour_purp=="Sum"] <- "All"
nm_tour_rates$pertype <- pertypeCodes$name[match(nm_tour_rates$pertype, pertypeCodes$code)]

nm_tour_rates$tour_purp[nm_tour_rates$tour_purp==4] <- "Escorting"
nm_tour_rates$tour_purp[nm_tour_rates$tour_purp==5] <- "Shopping"
nm_tour_rates$tour_purp[nm_tour_rates$tour_purp==6] <- "Maintenance"
nm_tour_rates$tour_purp[nm_tour_rates$tour_purp==7] <- "EatingOut"
nm_tour_rates$tour_purp[nm_tour_rates$tour_purp==8] <- "Visiting"
nm_tour_rates$tour_purp[nm_tour_rates$tour_purp==9] <- "Discretionary"

write.csv(nm_tour_rates, "nm_tour_rates.csv", row.names = F)

# Total tours by purpose X tourtype
t1 <- hist(tours$TOURPURP[tours$TOURPURP<10], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
t3 <- hist(unique_joint_tours$JOINT_PURP, breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tours_purpose_type <- data.frame(t1$counts, t3$counts)
colnames(tours_purpose_type) <- c("indi", "joint")
write.csv(tours_purpose_type, "tours_purpose_type.csv", row.names = TRUE)

# DAP by pertype
dapSummary <- count(per, c("PERTYPE", "activity_pattern"))
write.csv(dapSummary, "dapSummary.csv", row.names = TRUE)

# Prepare DAP summary for visualizer
dapSummary_vis <- xtabs(freq~PERTYPE+activity_pattern, dapSummary)
dapSummary_vis <- addmargins(as.table(dapSummary_vis))
dapSummary_vis <- as.data.frame.matrix(dapSummary_vis)

dapSummary_vis$id <- row.names(dapSummary_vis)
dapSummary_vis <- melt(dapSummary_vis, id = c("id"))
colnames(dapSummary_vis) <- c("PERTYPE", "DAP", "freq")
dapSummary_vis$PERTYPE <- as.character(dapSummary_vis$PERTYPE)
dapSummary_vis$DAP <- as.character(dapSummary_vis$DAP)
dapSummary_vis <- dapSummary_vis[dapSummary_vis$DAP!="Sum",]
dapSummary_vis$PERTYPE[dapSummary_vis$PERTYPE=="Sum"] <- "Total"
write.csv(dapSummary_vis, "dapSummary_vis.csv", row.names = TRUE)

# HHSize X Joint
hhsizeJoint <- count(hh[hh$HHSIZE>=2,], c("HHSIZE", "JOINT"))
write.csv(hhsizeJoint, "hhsizeJoint.csv", row.names = TRUE)

#mandatory tour frequency
mtfSummary <- count(per[per$imf_choice > 0,], c("PERTYPE", "imf_choice"))
write.csv(mtfSummary, "mtfSummary.csv")
#write.csv(tours, "tours_test.csv")

# Prepare MTF summary for visualizer
mtfSummary_vis <- xtabs(freq~PERTYPE+imf_choice, mtfSummary)
mtfSummary_vis <- addmargins(as.table(mtfSummary_vis))
mtfSummary_vis <- as.data.frame.matrix(mtfSummary_vis)

mtfSummary_vis$id <- row.names(mtfSummary_vis)
mtfSummary_vis <- melt(mtfSummary_vis, id = c("id"))
colnames(mtfSummary_vis) <- c("PERTYPE", "MTF", "freq")
mtfSummary_vis$PERTYPE <- as.character(mtfSummary_vis$PERTYPE)
mtfSummary_vis$MTF <- as.character(mtfSummary_vis$MTF)
mtfSummary_vis <- mtfSummary_vis[mtfSummary_vis$MTF!="Sum",]
mtfSummary_vis$PERTYPE[mtfSummary_vis$PERTYPE=="Sum"] <- "Total"
write.csv(mtfSummary_vis, "mtfSummary_vis.csv")

# indi NM summary
inm0Summary <- count(per[per$numTours==0,], c("PERTYPE"))
inm1Summary <- count(per[per$numTours==1,], c("PERTYPE"))
inm2Summary <- count(per[per$numTours==2,], c("PERTYPE"))
inm3Summary <- count(per[per$numTours>=3,], c("PERTYPE"))

inmSummary <- data.frame(PERTYPE = c(1,2,3,4,5,6,7,8))
inmSummary$tour0 <- inm0Summary$freq[match(inmSummary$PERTYPE, inm0Summary$PERTYPE)]
inmSummary$tour1 <- inm1Summary$freq[match(inmSummary$PERTYPE, inm1Summary$PERTYPE)]
inmSummary$tour2 <- inm2Summary$freq[match(inmSummary$PERTYPE, inm2Summary$PERTYPE)]
inmSummary$tour3pl <- inm3Summary$freq[match(inmSummary$PERTYPE, inm3Summary$PERTYPE)]

write.table(inmSummary, "innmSummary.csv", col.names=TRUE, sep=",")

# prepare INM summary for visualizer
inmSummary_vis <- melt(inmSummary, id=c("PERTYPE"))
inmSummary_vis$variable <- as.character(inmSummary_vis$variable)
inmSummary_vis$variable[inmSummary_vis$variable=="tour0"] <- "0"
inmSummary_vis$variable[inmSummary_vis$variable=="tour1"] <- "1"
inmSummary_vis$variable[inmSummary_vis$variable=="tour2"] <- "2"
inmSummary_vis$variable[inmSummary_vis$variable=="tour3pl"] <- "3pl"
inmSummary_vis <- xtabs(value~PERTYPE+variable, inmSummary_vis)
inmSummary_vis <- addmargins(as.table(inmSummary_vis))
inmSummary_vis <- as.data.frame.matrix(inmSummary_vis)

inmSummary_vis$id <- row.names(inmSummary_vis)
inmSummary_vis <- melt(inmSummary_vis, id = c("id"))
colnames(inmSummary_vis) <- c("PERTYPE", "nmtours", "freq")
inmSummary_vis$PERTYPE <- as.character(inmSummary_vis$PERTYPE)
inmSummary_vis$nmtours <- as.character(inmSummary_vis$nmtours)
inmSummary_vis <- inmSummary_vis[inmSummary_vis$nmtours!="Sum",]
inmSummary_vis$PERTYPE[inmSummary_vis$PERTYPE=="Sum"] <- "Total"
write.csv(inmSummary_vis, "inmSummary_vis.csv")

# Joint Tour Frequency and composition
jtfSummary <- count(hh[!is.na(hh$jtf),], c("jtf"))
jointComp <- count(unique_joint_tours, c("tour_composition"))
jointPartySize <- count(unique_joint_tours, c("NUMBER_HH"))
jointCompPartySize <- count(unique_joint_tours, c("tour_composition","NUMBER_HH"))

hh$jointCat[hh$jtours==0] <- 0
hh$jointCat[hh$jtours==1] <- 1
hh$jointCat[hh$jtours>=2] <- 2

jointToursHHSize <- count(hh[!is.na(hh$HHSIZE) & !is.na(hh$jointCat),], c("HHSIZE", "jointCat"))

write.table(jtfSummary, "jtfSummary.csv", col.names=TRUE, sep=",")
write.table(jointComp, "jtfSummary.csv", col.names=TRUE, sep=",", append=TRUE)
write.table(jointPartySize, "jtfSummary.csv", col.names=TRUE, sep=",", append=TRUE)
write.table(jointCompPartySize, "jtfSummary.csv", col.names=TRUE, sep=",", append=TRUE)
write.table(jointToursHHSize, "jtfSummary.csv", col.names=TRUE, sep=",", append=TRUE)

#cap joint party size to 5+
jointPartySize$freq[jointPartySize$NUMBER_HH==5] <- sum(jointPartySize$freq[jointPartySize$NUMBER_HH>=5])
jointPartySize <- jointPartySize[jointPartySize$NUMBER_HH<=5, ]

jtf <- data.frame(jtf_code = seq(from = 1, to = 21), 
                  alt_name = c("No Joint Tours", "1 Shopping", "1 Maintenance", "1 Eating Out", "1 Visiting", "1 Other Discretionary", 
                               "2 Shopping", "1 Shopping / 1 Maintenance", "1 Shopping / 1 Eating Out", "1 Shopping / 1 Visiting", 
                               "1 Shopping / 1 Other Discretionary", "2 Maintenance", "1 Maintenance / 1 Eating Out", 
                               "1 Maintenance / 1 Visiting", "1 Maintenance / 1 Other Discretionary", "2 Eating Out", "1 Eating Out / 1 Visiting", 
                               "1 Eating Out / 1 Other Discretionary", "2 Visiting", "1 Visiting / 1 Other Discretionary", "2 Other Discretionary"))
jtf$freq <- jtfSummary$freq[match(jtf$jtf_code, jtfSummary$jtf)]
jtf[is.na(jtf)] <- 0

jointComp$tour_composition[jointComp$tour_composition==1] <- "All Adult"
jointComp$tour_composition[jointComp$tour_composition==2] <- "All Children"
jointComp$tour_composition[jointComp$tour_composition==3] <- "Mixed"

jointToursHHSizeProp <- xtabs(freq~jointCat+HHSIZE, jointToursHHSize[jointToursHHSize$HHSIZE>1,])
jointToursHHSizeProp <- addmargins(as.table(jointToursHHSizeProp))
jointToursHHSizeProp <- jointToursHHSizeProp[-4,]  #remove last row 
jointToursHHSizeProp <- prop.table(jointToursHHSizeProp, margin = 2)
jointToursHHSizeProp <- as.data.frame.matrix(jointToursHHSizeProp)
jointToursHHSizeProp <- jointToursHHSizeProp*100
jointToursHHSizeProp$jointTours <- row.names(jointToursHHSizeProp)
jointToursHHSizeProp <- melt(jointToursHHSizeProp, id = c("jointTours"))
colnames(jointToursHHSizeProp) <- c("jointTours", "hhsize", "freq")
jointToursHHSizeProp$hhsize <- as.character(jointToursHHSizeProp$hhsize)
jointToursHHSizeProp$hhsize[jointToursHHSizeProp$hhsize=="Sum"] <- "Total"

jointCompPartySize$tour_composition[jointCompPartySize$tour_composition==1] <- "All Adult"
jointCompPartySize$tour_composition[jointCompPartySize$tour_composition==2] <- "All Children"
jointCompPartySize$tour_composition[jointCompPartySize$tour_composition==3] <- "Mixed"

jointCompPartySizeProp <- xtabs(freq~tour_composition+NUMBER_HH, jointCompPartySize)
jointCompPartySizeProp <- addmargins(as.table(jointCompPartySizeProp))
jointCompPartySizeProp <- jointCompPartySizeProp[,-6]  #remove last row 
jointCompPartySizeProp <- prop.table(jointCompPartySizeProp, margin = 1)
jointCompPartySizeProp <- as.data.frame.matrix(jointCompPartySizeProp)
jointCompPartySizeProp <- jointCompPartySizeProp*100
jointCompPartySizeProp$comp <- row.names(jointCompPartySizeProp)
jointCompPartySizeProp <- melt(jointCompPartySizeProp, id = c("comp"))
colnames(jointCompPartySizeProp) <- c("comp", "partysize", "freq")
jointCompPartySizeProp$comp <- as.character(jointCompPartySizeProp$comp)
jointCompPartySizeProp$comp[jointCompPartySizeProp$comp=="Sum"] <- "Total"

# Cap joint comp party size at 5
jointCompPartySizeProp <- jointCompPartySizeProp[jointCompPartySizeProp$partysize!="Sum",]
jointCompPartySizeProp$partysize <- as.numeric(as.character(jointCompPartySizeProp$partysize))
jointCompPartySizeProp$freq[jointCompPartySizeProp$comp=="All Adult" & jointCompPartySizeProp$partysize==5] <- 
  sum(jointCompPartySizeProp$freq[jointCompPartySizeProp$comp=="All Adult" & jointCompPartySizeProp$partysize>=5])
jointCompPartySizeProp$freq[jointCompPartySizeProp$comp=="All Children" & jointCompPartySizeProp$partysize==5] <- 
  sum(jointCompPartySizeProp$freq[jointCompPartySizeProp$comp=="All Children" & jointCompPartySizeProp$partysize>=5])
jointCompPartySizeProp$freq[jointCompPartySizeProp$comp=="Mixed" & jointCompPartySizeProp$partysize==5] <- 
  sum(jointCompPartySizeProp$freq[jointCompPartySizeProp$comp=="Mixed" & jointCompPartySizeProp$partysize>=5])
jointCompPartySizeProp$freq[jointCompPartySizeProp$comp=="Total" & jointCompPartySizeProp$partysize==5] <- 
  sum(jointCompPartySizeProp$freq[jointCompPartySizeProp$comp=="Total" & jointCompPartySizeProp$partysize>=5])

jointCompPartySizeProp <- jointCompPartySizeProp[jointCompPartySizeProp$partysize<=5,]


write.csv(jtf, "jtf.csv", row.names = F)
write.csv(jointComp, "jointComp.csv", row.names = F)
write.csv(jointPartySize, "jointPartySize.csv", row.names = F)
write.csv(jointCompPartySizeProp, "jointCompPartySize.csv", row.names = F)
write.csv(jointToursHHSizeProp, "jointToursHHSize.csv", row.names = F)

# TOD Profile
#work.dep <- table(cut(tours$ANCHOR_DEPART_BIN[!is.na(tours$ANCHOR_DEPART_BIN)], seq(1,48, by=1), right=FALSE))

tod1 <- hist(tours$start_period[tours$TOURPURP==1], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod1_2 <- hist(tours$start_period[tours$TOURPURP==1 & tours$PERTYPE==2], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
tod2 <- hist(tours$start_period[tours$TOURPURP==2], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
tod3 <- hist(tours$start_period[tours$TOURPURP==3], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
tod4 <- hist(tours$start_period[tours$TOURPURP==4], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
todi56 <- hist(tours$start_period[tours$TOURPURP>=5 & tours$TOURPURP<=6], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
todi789 <- hist(tours$start_period[tours$TOURPURP>=7 & tours$TOURPURP<=9], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod6 <- hist(tours$start_period[tours$TOURPURP==6], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod7 <- hist(tours$start_period[tours$TOURPURP==7], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod8 <- hist(tours$start_period[tours$TOURPURP==8], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod9 <- hist(tours$start_period[tours$TOURPURP==9], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
todj56 <- hist(unique_joint_tours$start_period[unique_joint_tours$JOINT_PURP>=5 & unique_joint_tours$JOINT_PURP<=6], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
todj789 <- hist(unique_joint_tours$start_period[unique_joint_tours$JOINT_PURP>=7 & unique_joint_tours$JOINT_PURP<=9], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod11 <- hist(unique_joint_tours$start_period[unique_joint_tours$JOINT_PURP==6], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod12 <- hist(unique_joint_tours$start_period[unique_joint_tours$JOINT_PURP==7], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod13 <- hist(unique_joint_tours$start_period[unique_joint_tours$JOINT_PURP==8], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod14 <- hist(unique_joint_tours$start_period[unique_joint_tours$JOINT_PURP==9], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
tod15 <- hist(tours$start_period[tours$TOURPURP==10], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)

todDepProfile <- data.frame(tod1$counts, tod2$counts, tod3$counts, tod4$counts, todi56$counts, todi789$counts
                            , todj56$counts, todj789$counts, tod15$counts)
colnames(todDepProfile) <- c("work", "univ", "sch", "esc", "imain", "idisc", 
                             "jmain", "jdisc", "atwork")
write.csv(todDepProfile, "todDepProfile.csv")

# prepare input for visualizer
todDepProfile_vis <- todDepProfile
todDepProfile_vis$id <- row.names(todDepProfile_vis)
todDepProfile_vis <- melt(todDepProfile_vis, id = c("id"))
colnames(todDepProfile_vis) <- c("id", "purpose", "freq_dep")

todDepProfile_vis$purpose <- as.character(todDepProfile_vis$purpose)
todDepProfile_vis <- xtabs(freq_dep~id+purpose, todDepProfile_vis)
todDepProfile_vis <- addmargins(as.table(todDepProfile_vis))
todDepProfile_vis <- as.data.frame.matrix(todDepProfile_vis)
todDepProfile_vis$id <- row.names(todDepProfile_vis)
todDepProfile_vis <- melt(todDepProfile_vis, id = c("id"))
colnames(todDepProfile_vis) <- c("timebin", "PURPOSE", "freq")
todDepProfile_vis$PURPOSE <- as.character(todDepProfile_vis$PURPOSE)
todDepProfile_vis$timebin <- as.character(todDepProfile_vis$timebin)
todDepProfile_vis <- todDepProfile_vis[todDepProfile_vis$timebin!="Sum",]
todDepProfile_vis$PURPOSE[todDepProfile_vis$PURPOSE=="Sum"] <- "Total"
todDepProfile_vis$timebin <- as.numeric(todDepProfile_vis$timebin)

tod1 <- hist(tours$end_period[tours$TOURPURP==1], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod1_2 <- hist(tours$end_period[tours$TOURPURP==1 & tours$PERTYPE==2], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
tod2 <- hist(tours$end_period[tours$TOURPURP==2], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
tod3 <- hist(tours$end_period[tours$TOURPURP==3], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
tod4 <- hist(tours$end_period[tours$TOURPURP==4], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
todi56 <- hist(tours$end_period[tours$TOURPURP>=5 & tours$TOURPURP<=6], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
todi789 <- hist(tours$end_period[tours$TOURPURP>=7 & tours$TOURPURP<=9], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod8 <- hist(tours$end_period[tours$TOURPURP==8], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod9 <- hist(tours$end_period[tours$TOURPURP==9], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
todj56 <- hist(unique_joint_tours$end_period[unique_joint_tours$JOINT_PURP>=5 & unique_joint_tours$JOINT_PURP<=6], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
todj789 <- hist(unique_joint_tours$end_period[unique_joint_tours$JOINT_PURP>=7 & unique_joint_tours$JOINT_PURP<=9], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod11 <- hist(unique_joint_tours$end_period[unique_joint_tours$JOINT_PURP==6], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod12 <- hist(unique_joint_tours$end_period[unique_joint_tours$JOINT_PURP==7], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod13 <- hist(unique_joint_tours$end_period[unique_joint_tours$JOINT_PURP==8], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod14 <- hist(unique_joint_tours$end_period[unique_joint_tours$JOINT_PURP==9], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
tod15 <- hist(tours$end_period[tours$TOURPURP==10], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)

todArrProfile <- data.frame(tod1$counts, tod2$counts, tod3$counts, tod4$counts, todi56$counts, todi789$counts
                            , todj56$counts, todj789$counts, tod15$counts)
colnames(todArrProfile) <- c("work", "univ", "sch", "esc", "imain", "idisc", 
                             "jmain", "jdisc", "atwork")
write.csv(todArrProfile, "todArrProfile.csv")

# prepare input for visualizer
todArrProfile_vis <- todArrProfile
todArrProfile_vis$id <- row.names(todArrProfile_vis)
todArrProfile_vis <- melt(todArrProfile_vis, id = c("id"))
colnames(todArrProfile_vis) <- c("id", "purpose", "freq_arr")

todArrProfile_vis$purpose <- as.character(todArrProfile_vis$purpose)
todArrProfile_vis <- xtabs(freq_arr~id+purpose, todArrProfile_vis)
todArrProfile_vis <- addmargins(as.table(todArrProfile_vis))
todArrProfile_vis <- as.data.frame.matrix(todArrProfile_vis)
todArrProfile_vis$id <- row.names(todArrProfile_vis)
todArrProfile_vis <- melt(todArrProfile_vis, id = c("id"))
colnames(todArrProfile_vis) <- c("timebin", "PURPOSE", "freq")
todArrProfile_vis$PURPOSE <- as.character(todArrProfile_vis$PURPOSE)
todArrProfile_vis$timebin <- as.character(todArrProfile_vis$timebin)
todArrProfile_vis <- todArrProfile_vis[todArrProfile_vis$timebin!="Sum",]
todArrProfile_vis$PURPOSE[todArrProfile_vis$PURPOSE=="Sum"] <- "Total"
todArrProfile_vis$timebin <- as.numeric(todArrProfile_vis$timebin)


tod1 <- hist(tours$tourdur[tours$TOURPURP==1], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod1_2 <- hist(tours$tourdur[tours$TOURPURP==1 & tours$PERTYPE==2], breaks = seq(0,41, by=1), freq = NULL, right=FALSE)
tod2 <- hist(tours$tourdur[tours$TOURPURP==2], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
tod3 <- hist(tours$tourdur[tours$TOURPURP==3], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
tod4 <- hist(tours$tourdur[tours$TOURPURP==4], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
todi56 <- hist(tours$tourdur[tours$TOURPURP>=5 & tours$TOURPURP<=6], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
todi789 <- hist(tours$tourdur[tours$TOURPURP>=7 & tours$TOURPURP<=9], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod6 <- hist(tours$tourdur[tours$TOURPURP==6], breaks = seq(0,41, by=1), freq = NULL, right=FALSE)
#tod7 <- hist(tours$tourdur[tours$TOURPURP==7], breaks = seq(0,41, by=1), freq = NULL, right=FALSE)
#tod8 <- hist(tours$tourdur[tours$TOURPURP==8], breaks = seq(0,41, by=1), freq = NULL, right=FALSE)
#tod9 <- hist(tours$tourdur[tours$TOURPURP==9], breaks = seq(0,41, by=1), freq = NULL, right=FALSE)
todj56 <- hist(unique_joint_tours$tourdur[unique_joint_tours$JOINT_PURP>=5 & unique_joint_tours$JOINT_PURP<=6], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
todj789 <- hist(unique_joint_tours$tourdur[unique_joint_tours$JOINT_PURP>=7 & unique_joint_tours$JOINT_PURP<=9], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)
#tod11 <- hist(unique_joint_tours$tourdur[unique_joint_tours$JOINT_PURP==6], breaks = seq(0,41, by=1), freq = NULL, right=FALSE)
#tod12 <- hist(unique_joint_tours$tourdur[unique_joint_tours$JOINT_PURP==7], breaks = seq(0,41, by=1), freq = NULL, right=FALSE)
#tod13 <- hist(unique_joint_tours$tourdur[unique_joint_tours$JOINT_PURP==8], breaks = seq(0,41, by=1), freq = NULL, right=FALSE)
#tod14 <- hist(unique_joint_tours$tourdur[unique_joint_tours$JOINT_PURP==9], breaks = seq(0,41, by=1), freq = NULL, right=FALSE)
tod15 <- hist(tours$tourdur[tours$TOURPURP==10], breaks = seq(1,41, by=1), freq = NULL, right=FALSE)

todDurProfile <- data.frame(tod1$counts, tod2$counts, tod3$counts, tod4$counts, todi56$counts, todi789$counts
                            , todj56$counts, todj789$counts, tod15$counts)
colnames(todDurProfile) <- c("work", "univ", "sch", "esc", "imain", "idisc", 
                             "jmain", "jdisc", "atwork")
write.csv(todDurProfile, "todDurProfile.csv")

# prepare input for visualizer
todDurProfile_vis <- todDurProfile
todDurProfile_vis$id <- row.names(todDurProfile_vis)
todDurProfile_vis <- melt(todDurProfile_vis, id = c("id"))
colnames(todDurProfile_vis) <- c("id", "purpose", "freq_dur")

todDurProfile_vis$purpose <- as.character(todDurProfile_vis$purpose)
todDurProfile_vis <- xtabs(freq_dur~id+purpose, todDurProfile_vis)
todDurProfile_vis <- addmargins(as.table(todDurProfile_vis))
todDurProfile_vis <- as.data.frame.matrix(todDurProfile_vis)
todDurProfile_vis$id <- row.names(todDurProfile_vis)
todDurProfile_vis <- melt(todDurProfile_vis, id = c("id"))
colnames(todDurProfile_vis) <- c("timebin", "PURPOSE", "freq")
todDurProfile_vis$PURPOSE <- as.character(todDurProfile_vis$PURPOSE)
todDurProfile_vis$timebin <- as.character(todDurProfile_vis$timebin)
todDurProfile_vis <- todDurProfile_vis[todDurProfile_vis$timebin!="Sum",]
todDurProfile_vis$PURPOSE[todDurProfile_vis$PURPOSE=="Sum"] <- "Total"
todDurProfile_vis$timebin <- as.numeric(todDurProfile_vis$timebin)

todDepProfile_vis <- todDepProfile_vis[order(todDepProfile_vis$timebin, todDepProfile_vis$PURPOSE), ]
todArrProfile_vis <- todArrProfile_vis[order(todArrProfile_vis$timebin, todArrProfile_vis$PURPOSE), ]
todDurProfile_vis <- todDurProfile_vis[order(todDurProfile_vis$timebin, todDurProfile_vis$PURPOSE), ]
todProfile_vis <- data.frame(todDepProfile_vis, todArrProfile_vis$freq, todDurProfile_vis$freq)
colnames(todProfile_vis) <- c("id", "purpose", "freq_dep", "freq_arr", "freq_dur")
write.csv(todProfile_vis, "todProfile_vis.csv", row.names = F)

# Tour Mode X Auto Suff [person tours]
tmode1_as0 <- hist(tours$TOURMODE[tours$TOURPURP==1 & tours$AUTOSUFF==0], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tmode2_as0 <- hist(tours$TOURMODE[tours$TOURPURP==2 & tours$AUTOSUFF==0], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tmode3_as0 <- hist(tours$TOURMODE[tours$TOURPURP==3 & tours$AUTOSUFF==0], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tmode4_as0 <- hist(tours$TOURMODE[tours$TOURPURP>=4 & tours$TOURPURP<=6 & tours$AUTOSUFF==0], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tmode5_as0 <- hist(tours$TOURMODE[tours$TOURPURP>=7 & tours$TOURPURP<=9 & tours$AUTOSUFF==0], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tmode6_as0 <- wtd.hist(unique_joint_tours$TOURMODE[unique_joint_tours$JOINT_PURP>=5 & unique_joint_tours$JOINT_PURP<=6 & unique_joint_tours$AUTOSUFF==0], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = unique_joint_tours$NUMBER_HH[unique_joint_tours$JOINT_PURP>=5 & unique_joint_tours$JOINT_PURP<=6 & unique_joint_tours$AUTOSUFF==0])
tmode7_as0 <- wtd.hist(unique_joint_tours$TOURMODE[unique_joint_tours$JOINT_PURP>=7 & unique_joint_tours$JOINT_PURP<=9 & unique_joint_tours$AUTOSUFF==0], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = unique_joint_tours$NUMBER_HH[unique_joint_tours$JOINT_PURP>=7 & unique_joint_tours$JOINT_PURP<=9 & unique_joint_tours$AUTOSUFF==0])
tmode8_as0 <- hist(tours$TOURMODE[tours$TOURPURP==10 & tours$AUTOSUFF==0], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)

tmodeAS0Profile <- data.frame(tmode1_as0$counts, tmode2_as0$counts, tmode3_as0$counts, tmode4_as0$counts,
                              tmode5_as0$counts, tmode6_as0$counts, tmode7_as0$counts, tmode8_as0$counts)
colnames(tmodeAS0Profile) <- c("work", "univ", "sch", "imain", "idisc", "jmain", "jdisc", "atwork")
write.csv(tmodeAS0Profile, "tmodeAS0Profile.csv")

# Prepeare data for visualizer
tmodeAS0Profile_vis <- tmodeAS0Profile[1:9,]
tmodeAS0Profile_vis$id <- row.names(tmodeAS0Profile_vis)
tmodeAS0Profile_vis <- melt(tmodeAS0Profile_vis, id = c("id"))
colnames(tmodeAS0Profile_vis) <- c("id", "purpose", "freq_as0")

tmodeAS0Profile_vis <- xtabs(freq_as0~id+purpose, tmodeAS0Profile_vis)
tmodeAS0Profile_vis[is.na(tmodeAS0Profile_vis)] <- 0
tmodeAS0Profile_vis <- addmargins(as.table(tmodeAS0Profile_vis))
tmodeAS0Profile_vis <- as.data.frame.matrix(tmodeAS0Profile_vis)

tmodeAS0Profile_vis$id <- row.names(tmodeAS0Profile_vis)
tmodeAS0Profile_vis <- melt(tmodeAS0Profile_vis, id = c("id"))
colnames(tmodeAS0Profile_vis) <- c("id", "purpose", "freq_as0")
tmodeAS0Profile_vis$id <- as.character(tmodeAS0Profile_vis$id)
tmodeAS0Profile_vis$purpose <- as.character(tmodeAS0Profile_vis$purpose)
tmodeAS0Profile_vis <- tmodeAS0Profile_vis[tmodeAS0Profile_vis$id!="Sum",]
tmodeAS0Profile_vis$purpose[tmodeAS0Profile_vis$purpose=="Sum"] <- "Total"

tmode1_as1 <- hist(tours$TOURMODE[tours$TOURPURP==1 & tours$AUTOSUFF==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tmode2_as1 <- hist(tours$TOURMODE[tours$TOURPURP==2 & tours$AUTOSUFF==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tmode3_as1 <- hist(tours$TOURMODE[tours$TOURPURP==3 & tours$AUTOSUFF==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tmode4_as1 <- hist(tours$TOURMODE[tours$TOURPURP>=4 & tours$TOURPURP<=6 & tours$AUTOSUFF==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tmode5_as1 <- hist(tours$TOURMODE[tours$TOURPURP>=7 & tours$TOURPURP<=9 & tours$AUTOSUFF==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tmode6_as1 <- wtd.hist(unique_joint_tours$TOURMODE[unique_joint_tours$JOINT_PURP>=5 & unique_joint_tours$JOINT_PURP<=6 & unique_joint_tours$AUTOSUFF==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = unique_joint_tours$NUMBER_HH[unique_joint_tours$JOINT_PURP>=5 & unique_joint_tours$JOINT_PURP<=6 & unique_joint_tours$AUTOSUFF==1])
tmode7_as1 <- wtd.hist(unique_joint_tours$TOURMODE[unique_joint_tours$JOINT_PURP>=7 & unique_joint_tours$JOINT_PURP<=9 & unique_joint_tours$AUTOSUFF==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = unique_joint_tours$NUMBER_HH[unique_joint_tours$JOINT_PURP>=7 & unique_joint_tours$JOINT_PURP<=9 & unique_joint_tours$AUTOSUFF==1])
tmode8_as1 <- hist(tours$TOURMODE[tours$TOURPURP==10 & tours$AUTOSUFF==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)

tmodeAS1Profile <- data.frame(tmode1_as1$counts, tmode2_as1$counts, tmode3_as1$counts, tmode4_as1$counts,
                              tmode5_as1$counts, tmode6_as1$counts, tmode7_as1$counts, tmode8_as1$counts)
colnames(tmodeAS1Profile) <- c("work", "univ", "sch", "imain", "idisc", "jmain", "jdisc", "atwork")
write.csv(tmodeAS1Profile, "tmodeAS1Profile.csv")

# Prepeare data for visualizer
tmodeAS1Profile_vis <- tmodeAS1Profile[1:9,]
tmodeAS1Profile_vis$id <- row.names(tmodeAS1Profile_vis)
tmodeAS1Profile_vis <- melt(tmodeAS1Profile_vis, id = c("id"))
colnames(tmodeAS1Profile_vis) <- c("id", "purpose", "freq_as1")

tmodeAS1Profile_vis <- xtabs(freq_as1~id+purpose, tmodeAS1Profile_vis)
tmodeAS1Profile_vis[is.na(tmodeAS1Profile_vis)] <- 0
tmodeAS1Profile_vis <- addmargins(as.table(tmodeAS1Profile_vis))
tmodeAS1Profile_vis <- as.data.frame.matrix(tmodeAS1Profile_vis)

tmodeAS1Profile_vis$id <- row.names(tmodeAS1Profile_vis)
tmodeAS1Profile_vis <- melt(tmodeAS1Profile_vis, id = c("id"))
colnames(tmodeAS1Profile_vis) <- c("id", "purpose", "freq_as1")
tmodeAS1Profile_vis$id <- as.character(tmodeAS1Profile_vis$id)
tmodeAS1Profile_vis$purpose <- as.character(tmodeAS1Profile_vis$purpose)
tmodeAS1Profile_vis <- tmodeAS1Profile_vis[tmodeAS1Profile_vis$id!="Sum",]
tmodeAS1Profile_vis$purpose[tmodeAS1Profile_vis$purpose=="Sum"] <- "Total"

tmode1_as2 <- hist(tours$TOURMODE[tours$TOURPURP==1 & tours$AUTOSUFF==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tmode2_as2 <- hist(tours$TOURMODE[tours$TOURPURP==2 & tours$AUTOSUFF==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tmode3_as2 <- hist(tours$TOURMODE[tours$TOURPURP==3 & tours$AUTOSUFF==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tmode4_as2 <- hist(tours$TOURMODE[tours$TOURPURP>=4 & tours$TOURPURP<=6 & tours$AUTOSUFF==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tmode5_as2 <- hist(tours$TOURMODE[tours$TOURPURP>=7 & tours$TOURPURP<=9 & tours$AUTOSUFF==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tmode6_as2 <- wtd.hist(unique_joint_tours$TOURMODE[unique_joint_tours$JOINT_PURP>=5 & unique_joint_tours$JOINT_PURP<=6 & unique_joint_tours$AUTOSUFF==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = unique_joint_tours$NUMBER_HH[unique_joint_tours$JOINT_PURP>=5 & unique_joint_tours$JOINT_PURP<=6 & unique_joint_tours$AUTOSUFF==2])
tmode7_as2 <- wtd.hist(unique_joint_tours$TOURMODE[unique_joint_tours$JOINT_PURP>=7 & unique_joint_tours$JOINT_PURP<=9 & unique_joint_tours$AUTOSUFF==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = unique_joint_tours$NUMBER_HH[unique_joint_tours$JOINT_PURP>=7 & unique_joint_tours$JOINT_PURP<=9 & unique_joint_tours$AUTOSUFF==2])
tmode8_as2 <- hist(tours$TOURMODE[tours$TOURPURP==10 & tours$AUTOSUFF==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)

tmodeAS2Profile <- data.frame(tmode1_as2$counts, tmode2_as2$counts, tmode3_as2$counts, tmode4_as2$counts,
                              tmode5_as2$counts, tmode6_as2$counts, tmode7_as2$counts, tmode8_as2$counts)
colnames(tmodeAS2Profile) <- c("work", "univ", "sch", "imain", "idisc", "jmain", "jdisc", "atwork")
write.csv(tmodeAS2Profile, "tmodeAS2Profile.csv")

# Prepeare data for visualizer
tmodeAS2Profile_vis <- tmodeAS2Profile[1:9,]
tmodeAS2Profile_vis$id <- row.names(tmodeAS2Profile_vis)
tmodeAS2Profile_vis <- melt(tmodeAS2Profile_vis, id = c("id"))
colnames(tmodeAS2Profile_vis) <- c("id", "purpose", "freq_as2")

tmodeAS2Profile_vis <- xtabs(freq_as2~id+purpose, tmodeAS2Profile_vis)
tmodeAS2Profile_vis[is.na(tmodeAS2Profile_vis)] <- 0
tmodeAS2Profile_vis <- addmargins(as.table(tmodeAS2Profile_vis))
tmodeAS2Profile_vis <- as.data.frame.matrix(tmodeAS2Profile_vis)

tmodeAS2Profile_vis$id <- row.names(tmodeAS2Profile_vis)
tmodeAS2Profile_vis <- melt(tmodeAS2Profile_vis, id = c("id"))
colnames(tmodeAS2Profile_vis) <- c("id", "purpose", "freq_as2")
tmodeAS2Profile_vis$id <- as.character(tmodeAS2Profile_vis$id)
tmodeAS2Profile_vis$purpose <- as.character(tmodeAS2Profile_vis$purpose)
tmodeAS2Profile_vis <- tmodeAS2Profile_vis[tmodeAS2Profile_vis$id!="Sum",]
tmodeAS2Profile_vis$purpose[tmodeAS2Profile_vis$purpose=="Sum"] <- "Total"


# Combine three AS groups
tmodeProfile_vis <- data.frame(tmodeAS0Profile_vis, tmodeAS1Profile_vis$freq_as1, tmodeAS2Profile_vis$freq_as2)
colnames(tmodeProfile_vis) <- c("id", "purpose", "freq_as0", "freq_as1", "freq_as2")
tmodeProfile_vis$freq_all <- tmodeProfile_vis$freq_as0 + tmodeProfile_vis$freq_as1 + tmodeProfile_vis$freq_as2
write.csv(tmodeProfile_vis, "tmodeProfile_vis.csv", row.names = F)


# Non Mand Tour lengths
tourdist4 <- hist(tours$SKIMDIST[tours$TOURPURP==4], breaks = c(seq(0,40, by=1), 9999), freq = NULL, right=FALSE)
tourdisti56 <- hist(tours$SKIMDIST[tours$TOURPURP>=5 & tours$TOURPURP<=6], breaks = c(seq(0,40, by=1), 9999), freq = NULL, right=FALSE)
tourdisti789 <- hist(tours$SKIMDIST[tours$TOURPURP>=7 & tours$TOURPURP<=9], breaks = c(seq(0,40, by=1), 9999), freq = NULL, right=FALSE)
tourdistj56 <- hist(unique_joint_tours$SKIMDIST[unique_joint_tours$JOINT_PURP>=5 & unique_joint_tours$JOINT_PURP<=6], breaks = c(seq(0,40, by=1), 9999), freq = NULL, right=FALSE)
tourdistj789 <- hist(unique_joint_tours$SKIMDIST[unique_joint_tours$JOINT_PURP>=7 & unique_joint_tours$JOINT_PURP<=9], breaks = c(seq(0,40, by=1), 9999), freq = NULL, right=FALSE)
tourdist10 <- hist(tours$SKIMDIST[tours$TOURPURP==10], breaks = c(seq(0,40, by=1), 9999), freq = NULL, right=FALSE)

tourDistProfile <- data.frame(tourdist4$counts, tourdisti56$counts, tourdisti789$counts, tourdistj56$counts, tourdistj789$counts, tourdist10$counts)

colnames(tourDistProfile) <- c("esco", "imain", "idisc", "jmain", "jdisc", "atwork")

write.csv(tourDistProfile, "nonMandTourDistProfile.csv")

#prepare input for visualizer
tourDistProfile_vis <- tourDistProfile
tourDistProfile_vis$id <- row.names(tourDistProfile_vis)
tourDistProfile_vis <- melt(tourDistProfile_vis, id = c("id"))
colnames(tourDistProfile_vis) <- c("id", "purpose", "freq")

tourDistProfile_vis <- xtabs(freq~id+purpose, tourDistProfile_vis)
tourDistProfile_vis <- addmargins(as.table(tourDistProfile_vis))
tourDistProfile_vis <- as.data.frame.matrix(tourDistProfile_vis)
tourDistProfile_vis$id <- row.names(tourDistProfile_vis)
tourDistProfile_vis <- melt(tourDistProfile_vis, id = c("id"))
colnames(tourDistProfile_vis) <- c("distbin", "PURPOSE", "freq")
tourDistProfile_vis$PURPOSE <- as.character(tourDistProfile_vis$PURPOSE)
tourDistProfile_vis$distbin <- as.character(tourDistProfile_vis$distbin)
tourDistProfile_vis <- tourDistProfile_vis[tourDistProfile_vis$distbin!="Sum",]
tourDistProfile_vis$PURPOSE[tourDistProfile_vis$PURPOSE=="Sum"] <- "Total"
tourDistProfile_vis$distbin <- as.numeric(tourDistProfile_vis$distbin)

write.csv(tourDistProfile_vis, "tourDistProfile_vis.csv", row.names = F)

cat("\n Average Tour Distance [esco]: ", mean(tours$SKIMDIST[tours$TOURPURP==4], na.rm = TRUE))
cat("\n Average Tour Distance [imain]: ", mean(tours$SKIMDIST[tours$TOURPURP>=5 & tours$TOURPURP<=6], na.rm = TRUE))
cat("\n Average Tour Distance [idisc]: ", mean(tours$SKIMDIST[tours$TOURPURP>=7 & tours$TOURPURP<=9], na.rm = TRUE))
cat("\n Average Tour Distance [jmain]: ", mean(unique_joint_tours$SKIMDIST[unique_joint_tours$JOINT_PURP>=5 & unique_joint_tours$JOINT_PURP<=6], na.rm = TRUE))
cat("\n Average Tour Distance [jdisc]: ", mean(unique_joint_tours$SKIMDIST[unique_joint_tours$JOINT_PURP>=7 & unique_joint_tours$JOINT_PURP<=9], na.rm = TRUE))
cat("\n Average Tour Distance [atwork]: ", mean(tours$SKIMDIST[tours$TOURPURP==10], na.rm = TRUE))

## Retirees
#cat("\n Average Tour Distance [esco]: ", mean(tours$SKIMDIST[tours$TOURPURP==4 & tours$PERTYPE==5], na.rm = TRUE))
#cat("\n Average Tour Distance [imain]: ", mean(tours$SKIMDIST[tours$TOURPURP>=5 & tours$TOURPURP<=6 & tours$PERTYPE==5], na.rm = TRUE))
#cat("\n Average Tour Distance [idisc]: ", mean(tours$SKIMDIST[tours$TOURPURP>=7 & tours$TOURPURP<=9 & tours$PERTYPE==5], na.rm = TRUE))
#cat("\n Average Tour Distance [jmain]: ", mean(unique_joint_tours$SKIMDIST[unique_joint_tours$JOINT_PURP>=5 & unique_joint_tours$JOINT_PURP<=6 & unique_joint_tours$PERTYPE==5], na.rm = TRUE))
#cat("\n Average Tour Distance [jdisc]: ", mean(unique_joint_tours$SKIMDIST[unique_joint_tours$JOINT_PURP>=7 & unique_joint_tours$JOINT_PURP<=9 & unique_joint_tours$PERTYPE==5], na.rm = TRUE))
#cat("\n Average Tour Distance [atwork]: ", mean(tours$SKIMDIST[tours$TOURPURP==10 & tours$PERTYPE==5], na.rm = TRUE))
#
## Non-reitrees
#cat("\n Average Tour Distance [esco]: ", mean(tours$SKIMDIST[tours$TOURPURP==4 & tours$PERTYPE!=5], na.rm = TRUE))
#cat("\n Average Tour Distance [imain]: ", mean(tours$SKIMDIST[tours$TOURPURP>=5 & tours$TOURPURP<=6 & tours$PERTYPE!=5], na.rm = TRUE))
#cat("\n Average Tour Distance [idisc]: ", mean(tours$SKIMDIST[tours$TOURPURP>=7 & tours$TOURPURP<=9 & tours$PERTYPE!=5], na.rm = TRUE))
#cat("\n Average Tour Distance [jmain]: ", mean(unique_joint_tours$SKIMDIST[unique_joint_tours$JOINT_PURP>=5 & unique_joint_tours$JOINT_PURP<=6 & unique_joint_tours$PERTYPE!=5], na.rm = TRUE))
#cat("\n Average Tour Distance [jdisc]: ", mean(unique_joint_tours$SKIMDIST[unique_joint_tours$JOINT_PURP>=7 & unique_joint_tours$JOINT_PURP<=9 & unique_joint_tours$PERTYPE!=5], na.rm = TRUE))
#cat("\n Average Tour Distance [atwork]: ", mean(tours$SKIMDIST[tours$TOURPURP==10 & tours$PERTYPE!=5], na.rm = TRUE))
#

## Output average trips lengths for visualizer

avgTripLengths <- c(mean(tours$SKIMDIST[tours$TOURPURP==4], na.rm = TRUE),
                    mean(tours$SKIMDIST[tours$TOURPURP>=5 & tours$TOURPURP<=6], na.rm = TRUE),
                    mean(tours$SKIMDIST[tours$TOURPURP>=7 & tours$TOURPURP<=9], na.rm = TRUE),
                    mean(unique_joint_tours$SKIMDIST[unique_joint_tours$JOINT_PURP>=5 & unique_joint_tours$JOINT_PURP<=6], na.rm = TRUE),
                    mean(unique_joint_tours$SKIMDIST[unique_joint_tours$JOINT_PURP>=7 & unique_joint_tours$JOINT_PURP<=9], na.rm = TRUE),
                    mean(tours$SKIMDIST[tours$TOURPURP==10], na.rm = TRUE))

totAvgNonMand <- mean(c(tours$SKIMDIST[tours$TOURPURP %in% c(4,5,6,7,8,9,10)], 
                            unique_joint_tours$SKIMDIST[unique_joint_tours$JOINT_PURP %in% c(5,6,7,8,9)]), 
                      na.rm = T)
avgTripLengths <- c(avgTripLengths, totAvgNonMand)

nonMandTourPurpose <- c("esco", "imain", "idisc", "jmain", "jdisc", "atwork", "Total")

nonMandTripLengths <- data.frame(purpose = nonMandTourPurpose, avgTripLength = avgTripLengths)

write.csv(nonMandTripLengths, "nonMandTripLengths.csv", row.names = F)



# STop Frequency
#Outbound
stopfreq1 <- hist(tours$num_ob_stops[tours$TOURPURP==1], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)
stopfreq2 <- hist(tours$num_ob_stops[tours$TOURPURP==2], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)
stopfreq3 <- hist(tours$num_ob_stops[tours$TOURPURP==3], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)
stopfreq4 <- hist(tours$num_ob_stops[tours$TOURPURP==4], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)
stopfreqi56 <- hist(tours$num_ob_stops[tours$TOURPURP>=5 & tours$TOURPURP<=6], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)
stopfreqi789 <- hist(tours$num_ob_stops[tours$TOURPURP>=7 & tours$TOURPURP<=9], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)
stopfreqj56 <- hist(unique_joint_tours$num_ob_stops[unique_joint_tours$JOINT_PURP>=5 & unique_joint_tours$JOINT_PURP<=6], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)
stopfreqj789 <- hist(unique_joint_tours$num_ob_stops[unique_joint_tours$JOINT_PURP>=7 & unique_joint_tours$JOINT_PURP<=9], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)
stopfreq10 <- hist(tours$num_ob_stops[tours$TOURPURP==10], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)

stopFreq <- data.frame(stopfreq1$counts, stopfreq2$counts, stopfreq3$counts, stopfreq4$counts, stopfreqi56$counts
                       , stopfreqi789$counts, stopfreqj56$counts, stopfreqj789$counts, stopfreq10$counts)
colnames(stopFreq) <- c("work", "univ", "sch", "esco","imain", "idisc", "jmain", "jdisc", "atwork")
write.csv(stopFreq, "stopFreqOutProfile.csv")

# prepare stop frequency input for visualizer
stopFreqout_vis <- stopFreq
stopFreqout_vis$id <- row.names(stopFreqout_vis)
stopFreqout_vis <- melt(stopFreqout_vis, id = c("id"))
colnames(stopFreqout_vis) <- c("id", "purpose", "freq")

stopFreqout_vis <- xtabs(freq~purpose+id, stopFreqout_vis)
stopFreqout_vis <- addmargins(as.table(stopFreqout_vis))
stopFreqout_vis <- as.data.frame.matrix(stopFreqout_vis)
stopFreqout_vis$id <- row.names(stopFreqout_vis)
stopFreqout_vis <- melt(stopFreqout_vis, id = c("id"))
colnames(stopFreqout_vis) <- c("purpose", "nstops", "freq")
stopFreqout_vis$purpose <- as.character(stopFreqout_vis$purpose)
stopFreqout_vis$nstops <- as.character(stopFreqout_vis$nstops)
stopFreqout_vis <- stopFreqout_vis[stopFreqout_vis$nstops!="Sum",]
stopFreqout_vis$purpose[stopFreqout_vis$purpose=="Sum"] <- "Total"

#Inbound
stopfreq1 <- hist(tours$num_ib_stops[tours$TOURPURP==1], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)
stopfreq2 <- hist(tours$num_ib_stops[tours$TOURPURP==2], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)
stopfreq3 <- hist(tours$num_ib_stops[tours$TOURPURP==3], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)
stopfreq4 <- hist(tours$num_ib_stops[tours$TOURPURP==4], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)
stopfreqi56 <- hist(tours$num_ib_stops[tours$TOURPURP>=5 & tours$TOURPURP<=6], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)
stopfreqi789 <- hist(tours$num_ib_stops[tours$TOURPURP>=7 & tours$TOURPURP<=9], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)
stopfreqj56 <- hist(unique_joint_tours$num_ib_stops[unique_joint_tours$JOINT_PURP>=5 & unique_joint_tours$JOINT_PURP<=6], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)
stopfreqj789 <- hist(unique_joint_tours$num_ib_stops[unique_joint_tours$JOINT_PURP>=7 & unique_joint_tours$JOINT_PURP<=9], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)
stopfreq10 <- hist(tours$num_ib_stops[tours$TOURPURP==10], breaks = c(seq(0,3, by=1), 9999), freq = NULL, right=FALSE)

stopFreq <- data.frame(stopfreq1$counts, stopfreq2$counts, stopfreq3$counts, stopfreq4$counts, stopfreqi56$counts
                       , stopfreqi789$counts, stopfreqj56$counts, stopfreqj789$counts, stopfreq10$counts)
colnames(stopFreq) <- c("work", "univ", "sch", "esco","imain", "idisc", "jmain", "jdisc", "atwork")
write.csv(stopFreq, "stopFreqInbProfile.csv")

# prepare stop frequency input for visualizer
stopFreqinb_vis <- stopFreq
stopFreqinb_vis$id <- row.names(stopFreqinb_vis)
stopFreqinb_vis <- melt(stopFreqinb_vis, id = c("id"))
colnames(stopFreqinb_vis) <- c("id", "purpose", "freq")

stopFreqinb_vis <- xtabs(freq~purpose+id, stopFreqinb_vis)
stopFreqinb_vis <- addmargins(as.table(stopFreqinb_vis))
stopFreqinb_vis <- as.data.frame.matrix(stopFreqinb_vis)
stopFreqinb_vis$id <- row.names(stopFreqinb_vis)
stopFreqinb_vis <- melt(stopFreqinb_vis, id = c("id"))
colnames(stopFreqinb_vis) <- c("purpose", "nstops", "freq")
stopFreqinb_vis$purpose <- as.character(stopFreqinb_vis$purpose)
stopFreqinb_vis$nstops <- as.character(stopFreqinb_vis$nstops)
stopFreqinb_vis <- stopFreqinb_vis[stopFreqinb_vis$nstops!="Sum",]
stopFreqinb_vis$purpose[stopFreqinb_vis$purpose=="Sum"] <- "Total"


stopfreqDir_vis <- data.frame(stopFreqout_vis, stopFreqinb_vis$freq)
colnames(stopfreqDir_vis) <- c("purpose", "nstops", "freq_out", "freq_inb")
write.csv(stopfreqDir_vis, "stopfreqDir_vis.csv", row.names = F)


#Total
stopfreq1 <- hist(tours$num_tot_stops[tours$TOURPURP==1], breaks = c(seq(0,6, by=1), 9999), freq = NULL, right=FALSE)
stopfreq2 <- hist(tours$num_tot_stops[tours$TOURPURP==2], breaks = c(seq(0,6, by=1), 9999), freq = NULL, right=FALSE)
stopfreq3 <- hist(tours$num_tot_stops[tours$TOURPURP==3], breaks = c(seq(0,6, by=1), 9999), freq = NULL, right=FALSE)
stopfreq4 <- hist(tours$num_tot_stops[tours$TOURPURP==4], breaks = c(seq(0,6, by=1), 9999), freq = NULL, right=FALSE)
stopfreqi56 <- hist(tours$num_tot_stops[tours$TOURPURP>=5 & tours$TOURPURP<=6], breaks = c(seq(0,6, by=1), 9999), freq = NULL, right=FALSE)
stopfreqi789 <- hist(tours$num_tot_stops[tours$TOURPURP>=7 & tours$TOURPURP<=9], breaks = c(seq(0,6, by=1), 9999), freq = NULL, right=FALSE)
stopfreqj56 <- hist(unique_joint_tours$num_tot_stops[unique_joint_tours$JOINT_PURP>=5 & unique_joint_tours$JOINT_PURP<=6], breaks = c(seq(0,6, by=1), 9999), freq = NULL, right=FALSE)
stopfreqj789 <- hist(unique_joint_tours$num_tot_stops[unique_joint_tours$JOINT_PURP>=7 & unique_joint_tours$JOINT_PURP<=9], breaks = c(seq(0,6, by=1), 9999), freq = NULL, right=FALSE)
stopfreq10 <- hist(tours$num_tot_stops[tours$TOURPURP==10], breaks = c(seq(0,6, by=1), 9999), freq = NULL, right=FALSE)

stopFreq <- data.frame(stopfreq1$counts, stopfreq2$counts, stopfreq3$counts, stopfreq4$counts, stopfreqi56$counts
                       , stopfreqi789$counts, stopfreqj56$counts, stopfreqj789$counts, stopfreq10$counts)
colnames(stopFreq) <- c("work", "univ", "sch", "esco","imain", "idisc", "jmain", "jdisc", "atwork")
write.csv(stopFreq, "stopFreqTotProfile.csv")

# prepare stop frequency input for visualizer
stopFreq_vis <- stopFreq
stopFreq_vis$id <- row.names(stopFreq_vis)
stopFreq_vis <- melt(stopFreq_vis, id = c("id"))
colnames(stopFreq_vis) <- c("id", "purpose", "freq")

stopFreq_vis <- xtabs(freq~purpose+id, stopFreq_vis)
stopFreq_vis <- addmargins(as.table(stopFreq_vis))
stopFreq_vis <- as.data.frame.matrix(stopFreq_vis)
stopFreq_vis$id <- row.names(stopFreq_vis)
stopFreq_vis <- melt(stopFreq_vis, id = c("id"))
colnames(stopFreq_vis) <- c("purpose", "nstops", "freq")
stopFreq_vis$purpose <- as.character(stopFreq_vis$purpose)
stopFreq_vis$nstops <- as.character(stopFreq_vis$nstops)
stopFreq_vis <- stopFreq_vis[stopFreq_vis$nstops!="Sum",]
stopFreq_vis$purpose[stopFreq_vis$purpose=="Sum"] <- "Total"

write.csv(stopFreq_vis, "stopfreq_total_vis.csv", row.names = F)

#STop purpose X TourPurpose
stopfreq1 <- hist(stops$DPURP[stops$TOURPURP==1], breaks = c(seq(1,10, by=1), 9999), freq = NULL, right=FALSE)
stopfreq2 <- hist(stops$DPURP[stops$TOURPURP==2], breaks = c(seq(1,10, by=1), 9999), freq = NULL, right=FALSE)
stopfreq3 <- hist(stops$DPURP[stops$TOURPURP==3], breaks = c(seq(1,10, by=1), 9999), freq = NULL, right=FALSE)
stopfreq4 <- hist(stops$DPURP[stops$TOURPURP==4], breaks = c(seq(1,10, by=1), 9999), freq = NULL, right=FALSE)
stopfreqi56 <- hist(stops$DPURP[stops$TOURPURP>=5 & stops$TOURPURP<=6], breaks = c(seq(1,10, by=1), 9999), freq = NULL, right=FALSE)
stopfreqi789 <- hist(stops$DPURP[stops$TOURPURP>=7 & stops$TOURPURP<=9], breaks = c(seq(1,10, by=1), 9999), freq = NULL, right=FALSE)
stopfreqj56 <- hist(jstops$DPURP[jstops$TOURPURP>=5 & jstops$TOURPURP<=6], breaks = c(seq(1,10, by=1), 9999), freq = NULL, right=FALSE)
stopfreqj789 <- hist(jstops$DPURP[jstops$TOURPURP>=7 & jstops$TOURPURP<=9], breaks = c(seq(1,10, by=1), 9999), freq = NULL, right=FALSE)
stopfreq10 <- hist(stops$DPURP[stops$TOURPURP==10], breaks = c(seq(1,10, by=1), 9999), freq = NULL, right=FALSE)

stopFreq <- data.frame(stopfreq1$counts, stopfreq2$counts, stopfreq3$counts, stopfreq4$counts, stopfreqi56$counts
                       , stopfreqi789$counts, stopfreqj56$counts, stopfreqj789$counts, stopfreq10$counts)
colnames(stopFreq) <- c("work", "univ", "sch", "esco","imain", "idisc", "jmain", "jdisc", "atwork")
write.csv(stopFreq, "stopPurposeByTourPurpose.csv")

# prepare stop frequency input for visualizer
stopFreq_vis <- stopFreq
stopFreq_vis$id <- row.names(stopFreq_vis)
stopFreq_vis <- melt(stopFreq_vis, id = c("id"))
colnames(stopFreq_vis) <- c("stop_purp", "purpose", "freq")

stopFreq_vis <- xtabs(freq~purpose+stop_purp, stopFreq_vis)
stopFreq_vis <- addmargins(as.table(stopFreq_vis))
stopFreq_vis <- as.data.frame.matrix(stopFreq_vis)
stopFreq_vis$purpose <- row.names(stopFreq_vis)
stopFreq_vis <- melt(stopFreq_vis, id = c("purpose"))
colnames(stopFreq_vis) <- c("purpose", "stop_purp", "freq")
stopFreq_vis$purpose <- as.character(stopFreq_vis$purpose)
stopFreq_vis$stop_purp <- as.character(stopFreq_vis$stop_purp)
stopFreq_vis <- stopFreq_vis[stopFreq_vis$stop_purp!="Sum",]
stopFreq_vis$purpose[stopFreq_vis$purpose=="Sum"] <- "Total"

write.csv(stopFreq_vis, "stoppurpose_tourpurpose_vis.csv", row.names = F)

#Out of direction - Stop Location
stopfreq1 <- hist(stops$out_dir_dist[stops$TOURPURP==1], breaks = c(-9999,seq(0,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreq2 <- hist(stops$out_dir_dist[stops$TOURPURP==2], breaks = c(-9999,seq(0,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreq3 <- hist(stops$out_dir_dist[stops$TOURPURP==3], breaks = c(-9999,seq(0,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreq4 <- hist(stops$out_dir_dist[stops$TOURPURP==4], breaks = c(-9999,seq(0,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreqi56 <- hist(stops$out_dir_dist[stops$TOURPURP>=5 & stops$TOURPURP<=6], breaks = c(-9999,seq(0,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreqi789 <- hist(stops$out_dir_dist[stops$TOURPURP>=7 & stops$TOURPURP<=9], breaks = c(-9999,seq(0,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreqj56 <- hist(jstops$out_dir_dist[jstops$TOURPURP>=5 & jstops$TOURPURP<=6], breaks = c(-9999,seq(0,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreqj789 <- hist(jstops$out_dir_dist[jstops$TOURPURP>=7 & jstops$TOURPURP<=9], breaks = c(-9999,seq(0,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreq10 <- hist(stops$out_dir_dist[stops$TOURPURP==10], breaks = c(-9999,seq(0,40, by=1), 9999), freq = NULL, right=FALSE)

stopFreq <- data.frame(stopfreq1$counts, stopfreq2$counts, stopfreq3$counts, stopfreq4$counts, stopfreqi56$counts
                       , stopfreqi789$counts, stopfreqj56$counts, stopfreqj789$counts, stopfreq10$counts)
colnames(stopFreq) <- c("work", "univ", "sch", "esco","imain", "idisc", "jmain", "jdisc", "atwork")
write.csv(stopFreq, "stopOutOfDirectionDC.csv")

# prepare stop location input for visualizer
stopDC_vis <- stopFreq
stopDC_vis$id <- row.names(stopDC_vis)
stopDC_vis <- melt(stopDC_vis, id = c("id"))
colnames(stopDC_vis) <- c("id", "purpose", "freq")

stopDC_vis <- xtabs(freq~id+purpose, stopDC_vis)
stopDC_vis <- addmargins(as.table(stopDC_vis))
stopDC_vis <- as.data.frame.matrix(stopDC_vis)
stopDC_vis$id <- row.names(stopDC_vis)
stopDC_vis <- melt(stopDC_vis, id = c("id"))
colnames(stopDC_vis) <- c("distbin", "PURPOSE", "freq")
stopDC_vis$PURPOSE <- as.character(stopDC_vis$PURPOSE)
stopDC_vis$distbin <- as.character(stopDC_vis$distbin)
stopDC_vis <- stopDC_vis[stopDC_vis$distbin!="Sum",]
stopDC_vis$PURPOSE[stopDC_vis$PURPOSE=="Sum"] <- "Total"
stopDC_vis$distbin <- as.numeric(stopDC_vis$distbin)

write.csv(stopDC_vis, "stopDC_vis.csv", row.names = F)

# compute average out of dir distance for visualizer
avgDistances <- c(mean(stops$out_dir_dist[stops$TOURPURP==1], na.rm = TRUE),
                  mean(stops$out_dir_dist[stops$TOURPURP==2], na.rm = TRUE),
                  mean(stops$out_dir_dist[stops$TOURPURP==3], na.rm = TRUE),
                  mean(stops$out_dir_dist[stops$TOURPURP==4], na.rm = TRUE),
                  mean(stops$out_dir_dist[stops$TOURPURP>=5 & stops$TOURPURP<=6], na.rm = TRUE),
                  mean(stops$out_dir_dist[stops$TOURPURP>=7 & stops$TOURPURP<=9], na.rm = TRUE),
                  mean(jstops$out_dir_dist[jstops$TOURPURP>=5 & jstops$TOURPURP<=6], na.rm = TRUE),
                  mean(jstops$out_dir_dist[jstops$TOURPURP>=7 & jstops$TOURPURP<=9], na.rm = TRUE),
                  mean(stops$out_dir_dist[stops$TOURPURP==10], na.rm = TRUE))

purp <- c("work", "univ", "sch", "esco","imain", "idisc", "jmain", "jdisc", "atwork", "total")

###
stopsDist <- c(stops$out_dir_dist[stops$TOURPURP %in% c(1, 2, 3,4,5,6,7,8,9, 10)], 
               jstops$out_dir_dist[jstops$TOURPURP %in% c(5,6,7,8,9)])

totAvgStopDist <- mean(stopsDist, na.rm = TRUE)

avgDistances <- c(avgDistances, totAvgStopDist)

###

avgStopOutofDirectionDist <- data.frame(purpose = purp, avgDist = avgDistances)

write.csv(avgStopOutofDirectionDist, "avgStopOutofDirectionDist_vis.csv", row.names = F)

#Stop Departure Time
stopfreq1 <- hist(stops$stop_period[stops$TOURPURP==1], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreq2 <- hist(stops$stop_period[stops$TOURPURP==2], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreq3 <- hist(stops$stop_period[stops$TOURPURP==3], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreq4 <- hist(stops$stop_period[stops$TOURPURP==4], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreqi56 <- hist(stops$stop_period[stops$TOURPURP>=5 & stops$TOURPURP<=6], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreqi789 <- hist(stops$stop_period[stops$TOURPURP>=7 & stops$TOURPURP<=9], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreqj56 <- hist(jstops$stop_period[jstops$TOURPURP>=5 & jstops$TOURPURP<=6], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreqj789 <- hist(jstops$stop_period[jstops$TOURPURP>=7 & jstops$TOURPURP<=9], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreq10 <- hist(stops$stop_period[stops$TOURPURP==10], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)

stopFreq <- data.frame(stopfreq1$counts, stopfreq2$counts, stopfreq3$counts, stopfreq4$counts, stopfreqi56$counts
                       , stopfreqi789$counts, stopfreqj56$counts, stopfreqj789$counts, stopfreq10$counts)
colnames(stopFreq) <- c("work", "univ", "sch", "esco","imain", "idisc", "jmain", "jdisc", "atwork")
write.csv(stopFreq, "stopDeparture.csv")

# prepare stop departure input for visualizer
stopDep_vis <- stopFreq
stopDep_vis$id <- row.names(stopDep_vis)
stopDep_vis <- melt(stopDep_vis, id = c("id"))
colnames(stopDep_vis) <- c("id", "purpose", "freq_stop")

stopDep_vis$purpose <- as.character(stopDep_vis$purpose)
stopDep_vis <- xtabs(freq_stop~id+purpose, stopDep_vis)
stopDep_vis <- addmargins(as.table(stopDep_vis))
stopDep_vis <- as.data.frame.matrix(stopDep_vis)
stopDep_vis$id <- row.names(stopDep_vis)
stopDep_vis <- melt(stopDep_vis, id = c("id"))
colnames(stopDep_vis) <- c("timebin", "PURPOSE", "freq")
stopDep_vis$PURPOSE <- as.character(stopDep_vis$PURPOSE)
stopDep_vis$timebin <- as.character(stopDep_vis$timebin)
stopDep_vis <- stopDep_vis[stopDep_vis$timebin!="Sum",]
stopDep_vis$PURPOSE[stopDep_vis$PURPOSE=="Sum"] <- "Total"
stopDep_vis$timebin <- as.numeric(stopDep_vis$timebin)

#Trip Departure Time
stopfreq1 <- hist(trips$stop_period[trips$TOURPURP==1], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreq2 <- hist(trips$stop_period[trips$TOURPURP==2], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreq3 <- hist(trips$stop_period[trips$TOURPURP==3], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreq4 <- hist(trips$stop_period[trips$TOURPURP==4], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreqi56 <- hist(trips$stop_period[trips$TOURPURP>=5 & trips$TOURPURP<=6], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreqi789 <- hist(trips$stop_period[trips$TOURPURP>=7 & trips$TOURPURP<=9], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreqj56 <- hist(jtrips$stop_period[jtrips$TOURPURP>=5 & jtrips$TOURPURP<=6], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreqj789 <- hist(jtrips$stop_period[jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)
stopfreq10 <- hist(trips$stop_period[trips$TOURPURP==10], breaks = c(seq(1,40, by=1), 9999), freq = NULL, right=FALSE)

stopFreq <- data.frame(stopfreq1$counts, stopfreq2$counts, stopfreq3$counts, stopfreq4$counts, stopfreqi56$counts
                       , stopfreqi789$counts, stopfreqj56$counts, stopfreqj789$counts, stopfreq10$counts)
colnames(stopFreq) <- c("work", "univ", "sch", "esco","imain", "idisc", "jmain", "jdisc", "atwork")
write.csv(stopFreq, "tripDeparture.csv")

# prepare stop departure input for visualizer
tripDep_vis <- stopFreq
tripDep_vis$id <- row.names(tripDep_vis)
tripDep_vis <- melt(tripDep_vis, id = c("id"))
colnames(tripDep_vis) <- c("id", "purpose", "freq_trip")

tripDep_vis$purpose <- as.character(tripDep_vis$purpose)
tripDep_vis <- xtabs(freq_trip~id+purpose, tripDep_vis)
tripDep_vis <- addmargins(as.table(tripDep_vis))
tripDep_vis <- as.data.frame.matrix(tripDep_vis)
tripDep_vis$id <- row.names(tripDep_vis)
tripDep_vis <- melt(tripDep_vis, id = c("id"))
colnames(tripDep_vis) <- c("timebin", "PURPOSE", "freq")
tripDep_vis$PURPOSE <- as.character(tripDep_vis$PURPOSE)
tripDep_vis$timebin <- as.character(tripDep_vis$timebin)
tripDep_vis <- tripDep_vis[tripDep_vis$timebin!="Sum",]
tripDep_vis$PURPOSE[tripDep_vis$PURPOSE=="Sum"] <- "Total"
tripDep_vis$timebin <- as.numeric(tripDep_vis$timebin)

stopTripDep_vis <- data.frame(stopDep_vis, tripDep_vis$freq)
colnames(stopTripDep_vis) <- c("id", "purpose", "freq_stop", "freq_trip")
write.csv(stopTripDep_vis, "stopTripDep_vis.csv", row.names = F)

#Trip Mode Summary
#Work
tripmode1 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==1 & trips$TOURMODE==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode2 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==1 & trips$TOURMODE==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode3 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==1 & trips$TOURMODE==3], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode4 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==1 & trips$TOURMODE==4], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode5 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==1 & trips$TOURMODE==5], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode6 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==1 & trips$TOURMODE==6], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode7 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==1 & trips$TOURMODE==7], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode8 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==1 & trips$TOURMODE==8], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode9 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==1 & trips$TOURMODE==9], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)

tripModeProfile <- data.frame(tripmode1$counts, tripmode2$counts, tripmode3$counts, tripmode4$counts,
                              tripmode5$counts, tripmode6$counts, tripmode7$counts, tripmode8$counts, tripmode9$counts)
colnames(tripModeProfile) <- c("tourmode1", "tourmode2", "tourmode3", "tourmode4", "tourmode5", "tourmode6", "tourmode7", "tourmode8", "tourmode9")
write.csv(tripModeProfile, "tripModeProfile_Work.csv")

# Prepeare data for visualizer
tripModeProfile1_vis <- tripModeProfile[1:9,]
tripModeProfile1_vis$id <- row.names(tripModeProfile1_vis)
tripModeProfile1_vis <- melt(tripModeProfile1_vis, id = c("id"))
colnames(tripModeProfile1_vis) <- c("id", "purpose", "freq1")

tripModeProfile1_vis <- xtabs(freq1~id+purpose, tripModeProfile1_vis)
tripModeProfile1_vis[is.na(tripModeProfile1_vis)] <- 0
tripModeProfile1_vis <- addmargins(as.table(tripModeProfile1_vis))
tripModeProfile1_vis <- as.data.frame.matrix(tripModeProfile1_vis)

tripModeProfile1_vis$id <- row.names(tripModeProfile1_vis)
tripModeProfile1_vis <- melt(tripModeProfile1_vis, id = c("id"))
colnames(tripModeProfile1_vis) <- c("id", "purpose", "freq1")
tripModeProfile1_vis$id <- as.character(tripModeProfile1_vis$id)
tripModeProfile1_vis$purpose <- as.character(tripModeProfile1_vis$purpose)
tripModeProfile1_vis <- tripModeProfile1_vis[tripModeProfile1_vis$id!="Sum",]
tripModeProfile1_vis$purpose[tripModeProfile1_vis$purpose=="Sum"] <- "Total"


#University
tripmode1 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==2 & trips$TOURMODE==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode2 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==2 & trips$TOURMODE==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode3 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==2 & trips$TOURMODE==3], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode4 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==2 & trips$TOURMODE==4], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode5 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==2 & trips$TOURMODE==5], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode6 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==2 & trips$TOURMODE==6], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode7 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==2 & trips$TOURMODE==7], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode8 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==2 & trips$TOURMODE==8], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode9 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==2 & trips$TOURMODE==9], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)

tripModeProfile <- data.frame(tripmode1$counts, tripmode2$counts, tripmode3$counts, tripmode4$counts,
                              tripmode5$counts, tripmode6$counts, tripmode7$counts, tripmode8$counts, tripmode9$counts)
colnames(tripModeProfile) <- c("tourmode1", "tourmode2", "tourmode3", "tourmode4", "tourmode5", "tourmode6", "tourmode7", "tourmode8", "tourmode9")
write.csv(tripModeProfile, "tripModeProfile_Univ.csv")

tripModeProfile2_vis <- tripModeProfile[1:9,]
tripModeProfile2_vis$id <- row.names(tripModeProfile2_vis)
tripModeProfile2_vis <- melt(tripModeProfile2_vis, id = c("id"))
colnames(tripModeProfile2_vis) <- c("id", "purpose", "freq2")

tripModeProfile2_vis <- xtabs(freq2~id+purpose, tripModeProfile2_vis)
tripModeProfile2_vis[is.na(tripModeProfile2_vis)] <- 0
tripModeProfile2_vis <- addmargins(as.table(tripModeProfile2_vis))
tripModeProfile2_vis <- as.data.frame.matrix(tripModeProfile2_vis)

tripModeProfile2_vis$id <- row.names(tripModeProfile2_vis)
tripModeProfile2_vis <- melt(tripModeProfile2_vis, id = c("id"))
colnames(tripModeProfile2_vis) <- c("id", "purpose", "freq2")
tripModeProfile2_vis$id <- as.character(tripModeProfile2_vis$id)
tripModeProfile2_vis$purpose <- as.character(tripModeProfile2_vis$purpose)
tripModeProfile2_vis <- tripModeProfile2_vis[tripModeProfile2_vis$id!="Sum",]
tripModeProfile2_vis$purpose[tripModeProfile2_vis$purpose=="Sum"] <- "Total"

#School
tripmode1 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==3 & trips$TOURMODE==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode2 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==3 & trips$TOURMODE==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode3 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==3 & trips$TOURMODE==3], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode4 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==3 & trips$TOURMODE==4], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode5 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==3 & trips$TOURMODE==5], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode6 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==3 & trips$TOURMODE==6], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode7 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==3 & trips$TOURMODE==7], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode8 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==3 & trips$TOURMODE==8], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode9 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==3 & trips$TOURMODE==9], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)

tripModeProfile <- data.frame(tripmode1$counts, tripmode2$counts, tripmode3$counts, tripmode4$counts,
                              tripmode5$counts, tripmode6$counts, tripmode7$counts, tripmode8$counts, tripmode9$counts)
colnames(tripModeProfile) <- c("tourmode1", "tourmode2", "tourmode3", "tourmode4", "tourmode5", "tourmode6", "tourmode7", "tourmode8", "tourmode9")
write.csv(tripModeProfile, "tripModeProfile_Schl.csv")

tripModeProfile3_vis <- tripModeProfile[1:9,]
tripModeProfile3_vis$id <- row.names(tripModeProfile3_vis)
tripModeProfile3_vis <- melt(tripModeProfile3_vis, id = c("id"))
colnames(tripModeProfile3_vis) <- c("id", "purpose", "freq3")

tripModeProfile3_vis <- xtabs(freq3~id+purpose, tripModeProfile3_vis)
tripModeProfile3_vis[is.na(tripModeProfile3_vis)] <- 0
tripModeProfile3_vis <- addmargins(as.table(tripModeProfile3_vis))
tripModeProfile3_vis <- as.data.frame.matrix(tripModeProfile3_vis)

tripModeProfile3_vis$id <- row.names(tripModeProfile3_vis)
tripModeProfile3_vis <- melt(tripModeProfile3_vis, id = c("id"))
colnames(tripModeProfile3_vis) <- c("id", "purpose", "freq3")
tripModeProfile3_vis$id <- as.character(tripModeProfile3_vis$id)
tripModeProfile3_vis$purpose <- as.character(tripModeProfile3_vis$purpose)
tripModeProfile3_vis <- tripModeProfile3_vis[tripModeProfile3_vis$id!="Sum",]
tripModeProfile3_vis$purpose[tripModeProfile3_vis$purpose=="Sum"] <- "Total"

#iMain
tripmode1 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=4 & trips$TOURPURP<=6 & trips$TOURMODE==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode2 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=4 & trips$TOURPURP<=6 & trips$TOURMODE==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode3 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=4 & trips$TOURPURP<=6 & trips$TOURMODE==3], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode4 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=4 & trips$TOURPURP<=6 & trips$TOURMODE==4], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode5 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=4 & trips$TOURPURP<=6 & trips$TOURMODE==5], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode6 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=4 & trips$TOURPURP<=6 & trips$TOURMODE==6], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode7 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=4 & trips$TOURPURP<=6 & trips$TOURMODE==7], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode8 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=4 & trips$TOURPURP<=6 & trips$TOURMODE==8], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode9 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=4 & trips$TOURPURP<=6 & trips$TOURMODE==9], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)

tripModeProfile <- data.frame(tripmode1$counts, tripmode2$counts, tripmode3$counts, tripmode4$counts,
                              tripmode5$counts, tripmode6$counts, tripmode7$counts, tripmode8$counts, tripmode9$counts)
colnames(tripModeProfile) <- c("tourmode1", "tourmode2", "tourmode3", "tourmode4", "tourmode5", "tourmode6", "tourmode7", "tourmode8", "tourmode9")
write.csv(tripModeProfile, "tripModeProfile_iMain.csv")

tripModeProfile4_vis <- tripModeProfile[1:9,]
tripModeProfile4_vis$id <- row.names(tripModeProfile4_vis)
tripModeProfile4_vis <- melt(tripModeProfile4_vis, id = c("id"))
colnames(tripModeProfile4_vis) <- c("id", "purpose", "freq4")

tripModeProfile4_vis <- xtabs(freq4~id+purpose, tripModeProfile4_vis)
tripModeProfile4_vis[is.na(tripModeProfile4_vis)] <- 0
tripModeProfile4_vis <- addmargins(as.table(tripModeProfile4_vis))
tripModeProfile4_vis <- as.data.frame.matrix(tripModeProfile4_vis)

tripModeProfile4_vis$id <- row.names(tripModeProfile4_vis)
tripModeProfile4_vis <- melt(tripModeProfile4_vis, id = c("id"))
colnames(tripModeProfile4_vis) <- c("id", "purpose", "freq4")
tripModeProfile4_vis$id <- as.character(tripModeProfile4_vis$id)
tripModeProfile4_vis$purpose <- as.character(tripModeProfile4_vis$purpose)
tripModeProfile4_vis <- tripModeProfile4_vis[tripModeProfile4_vis$id!="Sum",]
tripModeProfile4_vis$purpose[tripModeProfile4_vis$purpose=="Sum"] <- "Total"

#iDisc
tripmode1 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=7 & trips$TOURPURP<=9 & trips$TOURMODE==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode2 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=7 & trips$TOURPURP<=9 & trips$TOURMODE==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode3 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=7 & trips$TOURPURP<=9 & trips$TOURMODE==3], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode4 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=7 & trips$TOURPURP<=9 & trips$TOURMODE==4], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode5 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=7 & trips$TOURPURP<=9 & trips$TOURMODE==5], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode6 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=7 & trips$TOURPURP<=9 & trips$TOURMODE==6], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode7 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=7 & trips$TOURPURP<=9 & trips$TOURMODE==7], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode8 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=7 & trips$TOURPURP<=9 & trips$TOURMODE==8], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode9 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP>=7 & trips$TOURPURP<=9 & trips$TOURMODE==9], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)

tripModeProfile <- data.frame(tripmode1$counts, tripmode2$counts, tripmode3$counts, tripmode4$counts,
                              tripmode5$counts, tripmode6$counts, tripmode7$counts, tripmode8$counts, tripmode9$counts)
colnames(tripModeProfile) <- c("tourmode1", "tourmode2", "tourmode3", "tourmode4", "tourmode5", "tourmode6", "tourmode7", "tourmode8", "tourmode9")
write.csv(tripModeProfile, "tripModeProfile_iDisc.csv")

tripModeProfile5_vis <- tripModeProfile[1:9,]
tripModeProfile5_vis$id <- row.names(tripModeProfile5_vis)
tripModeProfile5_vis <- melt(tripModeProfile5_vis, id = c("id"))
colnames(tripModeProfile5_vis) <- c("id", "purpose", "freq5")

tripModeProfile5_vis <- xtabs(freq5~id+purpose, tripModeProfile5_vis)
tripModeProfile5_vis[is.na(tripModeProfile5_vis)] <- 0
tripModeProfile5_vis <- addmargins(as.table(tripModeProfile5_vis))
tripModeProfile5_vis <- as.data.frame.matrix(tripModeProfile5_vis)

tripModeProfile5_vis$id <- row.names(tripModeProfile5_vis)
tripModeProfile5_vis <- melt(tripModeProfile5_vis, id = c("id"))
colnames(tripModeProfile5_vis) <- c("id", "purpose", "freq5")
tripModeProfile5_vis$id <- as.character(tripModeProfile5_vis$id)
tripModeProfile5_vis$purpose <- as.character(tripModeProfile5_vis$purpose)
tripModeProfile5_vis <- tripModeProfile5_vis[tripModeProfile5_vis$id!="Sum",]
tripModeProfile5_vis$purpose[tripModeProfile5_vis$purpose=="Sum"] <- "Total"

#jMain
tripmode1 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==1])
tripmode2 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==2])
tripmode3 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==3], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==3])
tripmode4 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==4], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==4])
tripmode5 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==5], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==5])
tripmode6 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==6], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==6])
tripmode7 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==7], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==7])
tripmode8 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==8], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==8])
tripmode9 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==9], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=4 & jtrips$TOURPURP<=6 & jtrips$TOURMODE==9])

tripModeProfile <- data.frame(tripmode1$counts, tripmode2$counts, tripmode3$counts, tripmode4$counts,
                              tripmode5$counts, tripmode6$counts, tripmode7$counts, tripmode8$counts, tripmode9$counts)
colnames(tripModeProfile) <- c("tourmode1", "tourmode2", "tourmode3", "tourmode4", "tourmode5", "tourmode6", "tourmode7", "tourmode8", "tourmode9")
write.csv(tripModeProfile, "tripModeProfile_jMain.csv")

tripModeProfile6_vis <- tripModeProfile[1:9,]
tripModeProfile6_vis$id <- row.names(tripModeProfile6_vis)
tripModeProfile6_vis <- melt(tripModeProfile6_vis, id = c("id"))
colnames(tripModeProfile6_vis) <- c("id", "purpose", "freq6")

tripModeProfile6_vis <- xtabs(freq6~id+purpose, tripModeProfile6_vis)
tripModeProfile6_vis[is.na(tripModeProfile6_vis)] <- 0
tripModeProfile6_vis <- addmargins(as.table(tripModeProfile6_vis))
tripModeProfile6_vis <- as.data.frame.matrix(tripModeProfile6_vis)

tripModeProfile6_vis$id <- row.names(tripModeProfile6_vis)
tripModeProfile6_vis <- melt(tripModeProfile6_vis, id = c("id"))
colnames(tripModeProfile6_vis) <- c("id", "purpose", "freq6")
tripModeProfile6_vis$id <- as.character(tripModeProfile6_vis$id)
tripModeProfile6_vis$purpose <- as.character(tripModeProfile6_vis$purpose)
tripModeProfile6_vis <- tripModeProfile6_vis[tripModeProfile6_vis$id!="Sum",]
tripModeProfile6_vis$purpose[tripModeProfile6_vis$purpose=="Sum"] <- "Total"

#jDisc
tripmode1 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==1])
tripmode2 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==2])
tripmode3 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==3], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==3])
tripmode4 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==4], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==4])
tripmode5 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==5], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==5])
tripmode6 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==6], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==6])
tripmode7 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==7], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==7])
tripmode8 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==8], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==8])
tripmode9 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==9], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURPURP>=7 & jtrips$TOURPURP<=9 & jtrips$TOURMODE==9])

tripModeProfile <- data.frame(tripmode1$counts, tripmode2$counts, tripmode3$counts, tripmode4$counts,
                              tripmode5$counts, tripmode6$counts, tripmode7$counts, tripmode8$counts, tripmode9$counts)
colnames(tripModeProfile) <- c("tourmode1", "tourmode2", "tourmode3", "tourmode4", "tourmode5", "tourmode6", "tourmode7", "tourmode8", "tourmode9")
write.csv(tripModeProfile, "tripModeProfile_jDisc.csv")

tripModeProfile7_vis <- tripModeProfile[1:9,]
tripModeProfile7_vis$id <- row.names(tripModeProfile7_vis)
tripModeProfile7_vis <- melt(tripModeProfile7_vis, id = c("id"))
colnames(tripModeProfile7_vis) <- c("id", "purpose", "freq7")

tripModeProfile7_vis <- xtabs(freq7~id+purpose, tripModeProfile7_vis)
tripModeProfile7_vis[is.na(tripModeProfile7_vis)] <- 0
tripModeProfile7_vis <- addmargins(as.table(tripModeProfile7_vis))
tripModeProfile7_vis <- as.data.frame.matrix(tripModeProfile7_vis)

tripModeProfile7_vis$id <- row.names(tripModeProfile7_vis)
tripModeProfile7_vis <- melt(tripModeProfile7_vis, id = c("id"))
colnames(tripModeProfile7_vis) <- c("id", "purpose", "freq7")
tripModeProfile7_vis$id <- as.character(tripModeProfile7_vis$id)
tripModeProfile7_vis$purpose <- as.character(tripModeProfile7_vis$purpose)
tripModeProfile7_vis <- tripModeProfile7_vis[tripModeProfile7_vis$id!="Sum",]
tripModeProfile7_vis$purpose[tripModeProfile7_vis$purpose=="Sum"] <- "Total"

#At work
tripmode1 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==10 & trips$TOURMODE==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode2 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==10 & trips$TOURMODE==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode3 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==10 & trips$TOURMODE==3], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode4 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==10 & trips$TOURMODE==4], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode5 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==10 & trips$TOURMODE==5], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode6 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==10 & trips$TOURMODE==6], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode7 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==10 & trips$TOURMODE==7], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode8 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==10 & trips$TOURMODE==8], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
tripmode9 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURPURP==10 & trips$TOURMODE==9], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)

tripModeProfile <- data.frame(tripmode1$counts, tripmode2$counts, tripmode3$counts, tripmode4$counts,
                              tripmode5$counts, tripmode6$counts, tripmode7$counts, tripmode8$counts, tripmode9$counts)
colnames(tripModeProfile) <- c("tourmode1", "tourmode2", "tourmode3", "tourmode4", "tourmode5", "tourmode6", "tourmode7", "tourmode8", "tourmode9")
write.csv(tripModeProfile, "tripModeProfile_AtWork.csv")

tripModeProfile8_vis <- tripModeProfile[1:9,]
tripModeProfile8_vis$id <- row.names(tripModeProfile8_vis)
tripModeProfile8_vis <- melt(tripModeProfile8_vis, id = c("id"))
colnames(tripModeProfile8_vis) <- c("id", "purpose", "freq8")

tripModeProfile8_vis <- xtabs(freq8~id+purpose, tripModeProfile8_vis)
tripModeProfile8_vis[is.na(tripModeProfile8_vis)] <- 0
tripModeProfile8_vis <- addmargins(as.table(tripModeProfile8_vis))
tripModeProfile8_vis <- as.data.frame.matrix(tripModeProfile8_vis)

tripModeProfile8_vis$id <- row.names(tripModeProfile8_vis)
tripModeProfile8_vis <- melt(tripModeProfile8_vis, id = c("id"))
colnames(tripModeProfile8_vis) <- c("id", "purpose", "freq8")
tripModeProfile8_vis$id <- as.character(tripModeProfile8_vis$id)
tripModeProfile8_vis$purpose <- as.character(tripModeProfile8_vis$purpose)
tripModeProfile8_vis <- tripModeProfile8_vis[tripModeProfile8_vis$id!="Sum",]
tripModeProfile8_vis$purpose[tripModeProfile8_vis$purpose=="Sum"] <- "Total"

#iTotal
itripmode1 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURMODE==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
itripmode2 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURMODE==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
itripmode3 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURMODE==3], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
itripmode4 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURMODE==4], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
itripmode5 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURMODE==5], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
itripmode6 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURMODE==6], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
itripmode7 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURMODE==7], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
itripmode8 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURMODE==8], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)
itripmode9 <- hist(trips$TRIPMODE[trips$TRIPMODE>0 & trips$TOURMODE==9], breaks = seq(1,10, by=1), freq = NULL, right=FALSE)

#jTotal
jtripmode1 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURMODE==1], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURMODE==1])
jtripmode2 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURMODE==2], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURMODE==2])
jtripmode3 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURMODE==3], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURMODE==3])
jtripmode4 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURMODE==4], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURMODE==4])
jtripmode5 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURMODE==5], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURMODE==5])
jtripmode6 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURMODE==6], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURMODE==6])
jtripmode7 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURMODE==7], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURMODE==7])
jtripmode8 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURMODE==8], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURMODE==8])
jtripmode9 <- wtd.hist(jtrips$TRIPMODE[jtrips$TRIPMODE>0 & jtrips$TOURMODE==9], breaks = seq(1,10, by=1), freq = NULL, right=FALSE, weight = jtrips$num_participants[jtrips$TRIPMODE>0 & jtrips$TOURMODE==9])

tripModeProfile <- data.frame(itripmode1$counts+jtripmode1$counts, itripmode2$counts+jtripmode2$counts, itripmode3$counts+jtripmode3$counts, itripmode4$counts+jtripmode4$counts,
                              itripmode5$counts+jtripmode5$counts, itripmode6$counts+jtripmode6$counts, itripmode7$counts+jtripmode7$counts, itripmode8$counts+jtripmode8$counts, 
                              itripmode9$counts+jtripmode9$counts)
colnames(tripModeProfile) <- c("tourmode1", "tourmode2", "tourmode3", "tourmode4", "tourmode5", "tourmode6", "tourmode7", "tourmode8", "tourmode9")
write.csv(tripModeProfile, "tripModeProfile_Total.csv")

tripModeProfile9_vis <- tripModeProfile[1:9,]
tripModeProfile9_vis$id <- row.names(tripModeProfile9_vis)
tripModeProfile9_vis <- melt(tripModeProfile9_vis, id = c("id"))
colnames(tripModeProfile9_vis) <- c("id", "purpose", "freq9")

tripModeProfile9_vis <- xtabs(freq9~id+purpose, tripModeProfile9_vis)
tripModeProfile9_vis[is.na(tripModeProfile9_vis)] <- 0
tripModeProfile9_vis <- addmargins(as.table(tripModeProfile9_vis))
tripModeProfile9_vis <- as.data.frame.matrix(tripModeProfile9_vis)

tripModeProfile9_vis$id <- row.names(tripModeProfile9_vis)
tripModeProfile9_vis <- melt(tripModeProfile9_vis, id = c("id"))
colnames(tripModeProfile9_vis) <- c("id", "purpose", "freq9")
tripModeProfile9_vis$id <- as.character(tripModeProfile9_vis$id)
tripModeProfile9_vis$purpose <- as.character(tripModeProfile9_vis$purpose)
tripModeProfile9_vis <- tripModeProfile9_vis[tripModeProfile9_vis$id!="Sum",]
tripModeProfile9_vis$purpose[tripModeProfile9_vis$purpose=="Sum"] <- "Total"


# combine all tripmode profile for visualizer
tripModeProfile_vis <- data.frame(tripModeProfile1_vis, tripModeProfile2_vis$freq2, tripModeProfile3_vis$freq3
                                  , tripModeProfile4_vis$freq4, tripModeProfile5_vis$freq5, tripModeProfile6_vis$freq6
                                  , tripModeProfile7_vis$freq7, tripModeProfile8_vis$freq8, tripModeProfile9_vis$freq9)
colnames(tripModeProfile_vis) <- c("tripmode", "tourmode", "work", "univ", "schl", "imain", "idisc", "jmain", "jdisc", "atwork", "total")

temp <- melt(tripModeProfile_vis, id = c("tripmode", "tourmode"))
#tripModeProfile_vis <- cast(temp, tripmode+variable~tourmode)
#write.csv(tripModeProfile_vis, "tripModeProfile_vis.csv", row.names = F)
temp$grp_var <- paste(temp$variable, temp$tourmode, sep = "")

# rename tour mode to standard names
temp$tourmode[temp$tourmode=="tourmode1"] <- 'Auto SOV'
temp$tourmode[temp$tourmode=="tourmode2"] <- 'Auto 2 Person'
temp$tourmode[temp$tourmode=="tourmode3"] <- 'Auto 3+ Person'
temp$tourmode[temp$tourmode=="tourmode4"] <- 'Walk'
temp$tourmode[temp$tourmode=="tourmode5"] <- 'Bike/Moped'
temp$tourmode[temp$tourmode=="tourmode6"] <- 'Walk-Transit'
temp$tourmode[temp$tourmode=="tourmode7"] <- 'PNR-Transit'
temp$tourmode[temp$tourmode=="tourmode8"] <- 'KNR-Transit'
temp$tourmode[temp$tourmode=="tourmode9"] <- 'School Bus'

colnames(temp) <- c("tripmode","tourmode","purpose","value","grp_var")

write.csv(temp, "tripModeProfile_vis.csv", row.names = F)

# Total number of stops, trips & tours
cat("\n Total number of stops : ", nrow(stops) + sum(jstops$num_participants))
cat("\n Total number of trips : ", nrow(trips) + sum(jtrips$num_participants))
cat("\n Total number of tours : ", nrow(tours) + sum(unique_joint_tours$NUMBER_HH))


# output total numbers in a file
total_population <- sum(pertypeDistbn$freq)
total_households <- nrow(hh)
total_tours <- nrow(tours) + sum(unique_joint_tours$NUMBER_HH)
total_trips <- nrow(trips) + sum(jtrips$num_participants)
total_stops <- nrow(stops) + sum(jstops$num_participants)

trips$num_travel[trips$TRIPMODE==1] <- 1
trips$num_travel[trips$TRIPMODE==2] <- 2
trips$num_travel[trips$TRIPMODE==3] <- 3.5
trips$num_travel[is.na(trips$num_travel)] <- 0

jtrips$num_travel[jtrips$TRIPMODE==1] <- 1
jtrips$num_travel[jtrips$TRIPMODE==2] <- 2
jtrips$num_travel[jtrips$TRIPMODE==3] <- 3.5
jtrips$num_travel[is.na(jtrips$num_travel)] <- 0

total_vmt <- sum((trips$od_dist[trips$TRIPMODE<=3])/trips$num_travel[trips$TRIPMODE<=3]) + 
  sum((jtrips$od_dist[jtrips$TRIPMODE<=3])/jtrips$num_travel[jtrips$TRIPMODE<=3])

totals_var <- c("total_population", "total_households", "total_tours", "total_trips", "total_stops", "total_vmt")
totals_val <- c(total_population,total_households, total_tours, total_trips, total_stops, total_vmt)

totals_df <- data.frame(name = totals_var, value = totals_val)

write.csv(totals_df, "totals.csv", row.names = F)

# HH Size distribution
hhSizeDist <- count(hh, c("HHSIZE"))
write.csv(hhSizeDist, "hhSizeDist.csv", row.names = F)

# Active Persons by person type
actpertypeDistbn <- count(per[per$activity_pattern!="H",], c("PERTYPE"))
write.csv(actpertypeDistbn, "activePertypeDistbn.csv", row.names = TRUE)


# County-County trip flow by Tour Purpose and Trip Mode (changed by khademul)
trips$num_participants <- 1
trips_sample <- rbind(trips[,c("OCOUNTY", "DCOUNTY", "OSDIST", "DSDIST", "TRIPMODE", "tour_purpose", "num_participants")], 
                      jtrips[,c("OCOUNTY", "DCOUNTY", "OSDIST", "DSDIST", "TRIPMODE", "tour_purpose", "num_participants")])

tripModeNames <- c('Auto SOV','Auto 2 Person','Auto 3+ Person','Walk','Bike/Moped','Walk-Transit','PNR-Transit','KNR-Transit','School Bus')
tripModeCodes <- c(1, 2, 3, 4, 5, 6, 7, 8, 9)
tripMode_df <- data.frame(tripModeCodes, tripModeNames)

trips_sample$trip_mode <- tripMode_df$tripModeNames[match(trips_sample$TRIPMODE, tripMode_df$tripModeCodes)]
trips_sample <- trips_sample[,c("OCOUNTY", "DCOUNTY", "OSDIST", "DSDIST", "trip_mode", "tour_purpose", "num_participants")]
trips_sample <- data.table(trips_sample)

trips_flow <- trips_sample[, .(count = sum(num_participants)), by = list(OCOUNTY, DCOUNTY, trip_mode, tour_purpose)]
trips_flow_total <- data.table(trips_flow[,c("OCOUNTY", "DCOUNTY", "trip_mode", "count")])
trips_flow_total <- trips_flow_total[, (tot = sum(count)), by = list(OCOUNTY, DCOUNTY, trip_mode)]
trips_flow_total$tour_purpose <- "Total"
names(trips_flow_total)[names(trips_flow_total) == "V1"] <- "count"
trips_flow <- rbind(trips_flow, trips_flow_total[,c("OCOUNTY", "DCOUNTY", "trip_mode", "tour_purpose", "count")])

trips_flow_total <- data.table(trips_flow[,c("OCOUNTY", "DCOUNTY", "tour_purpose", "count")])
trips_flow_total <- trips_flow_total[, (tot = sum(count)), by = list(OCOUNTY, DCOUNTY, tour_purpose)]
trips_flow_total$trip_mode <- "Total"
names(trips_flow_total)[names(trips_flow_total) == "V1"] <- "count"
trips_flow <- rbind(trips_flow, trips_flow_total[,c("OCOUNTY", "DCOUNTY", "trip_mode", "tour_purpose", "count")])


write.table(trips_flow, paste(WD,"trips_flow.csv", sep = "//"), sep = ",", row.names = F)

# added by khademul
trips_flow_S <- trips_sample[, .(count = sum(num_participants)), by = list(OSDIST, DSDIST, trip_mode, tour_purpose)]
trips_flow_total_S <- data.table(trips_flow_S[,c("OSDIST", "DSDIST", "trip_mode", "count")])
trips_flow_total_S <- trips_flow_total_S[, (tot = sum(count)), by = list(OSDIST, DSDIST, trip_mode)]
trips_flow_total_S$tour_purpose <- "Total"
names(trips_flow_total_S)[names(trips_flow_total_S) == "V1"] <- "count"
trips_flow_S <- rbind(trips_flow_S, trips_flow_total_S[,c("OSDIST", "DSDIST", "trip_mode", "tour_purpose", "count")])

trips_flow_total_S <- data.table(trips_flow_S[,c("OSDIST", "DSDIST", "tour_purpose", "count")])
trips_flow_total_S <- trips_flow_total_S[, (tot = sum(count)), by = list(OSDIST, DSDIST, tour_purpose)]
trips_flow_total_S$trip_mode <- "Total"
names(trips_flow_total_S)[names(trips_flow_total_S) == "V1"] <- "count"
trips_flow_S <- rbind(trips_flow_S, trips_flow_total_S[,c("OSDIST", "DSDIST", "trip_mode", "tour_purpose", "count")])


write.table(trips_flow_S, paste(WD,"trips_flow_S.csv", sep = "//"), sep = ",", row.names = F)


#####################################################
#### Additional Transit SUmmaries for validation ####
#####################################################

# use transit trips appended with LOS
tripsLOS$access_mode[tripsLOS$trip_mode==11] <- "walk"
tripsLOS$access_mode[tripsLOS$trip_mode==12] <- "pnr"
tripsLOS$access_mode[tripsLOS$trip_mode==13] <- "knr"

tripsLOS$nTransfers <- ceiling(tripsLOS$XFERS)
tripsLOS$boards <- tripsLOS$nTransfers + 1

# Define dummy weights
tripsLOS$tripWeight <- 1
tripsLOS$boardWeight <- tripsLOS$boards

# Define period
tripsLOS$period[tripsLOS$stop_period<=3] <- "EA"
tripsLOS$period[tripsLOS$stop_period>=4  & tripsLOS$stop_period<= 9] <- "AM"
tripsLOS$period[tripsLOS$stop_period>=10 & tripsLOS$stop_period<=22] <- "MD"
tripsLOS$period[tripsLOS$stop_period>=23 & tripsLOS$stop_period<=29] <- "PM"
tripsLOS$period[tripsLOS$stop_period>=30] <- "EV"

tripsLOS$usedLB <- ifelse(tripsLOS$LB_TIME>0,1,0)
tripsLOS$usedEB <- ifelse(tripsLOS$EB_TIME>0,1,0)
tripsLOS$usedFR <- ifelse(tripsLOS$FR_TIME>0,1,0)
tripsLOS$usedLR <- ifelse(tripsLOS$LR_TIME>0,1,0)
tripsLOS$usedHR <- ifelse(tripsLOS$HR_TIME>0,1,0)
tripsLOS$usedCR <- ifelse(tripsLOS$CR_TIME>0,1,0)

tripsLOS$setType[tripsLOS$usedLB==1 & tripsLOS$usedEB==0 & tripsLOS$usedFR==0 & tripsLOS$usedLR==0 & tripsLOS$usedHR==0 & tripsLOS$usedCR==0] <- "LOC"
tripsLOS$setType[tripsLOS$usedLB==0 & (tripsLOS$usedEB + tripsLOS$usedFR + tripsLOS$usedLR + tripsLOS$usedHR + tripsLOS$usedCR)>0] <- "PRE"
tripsLOS$setType[tripsLOS$usedLB==1 & (tripsLOS$usedEB + tripsLOS$usedFR + tripsLOS$usedLR + tripsLOS$usedHR + tripsLOS$usedCR)>0] <- "MIX"

# Percentage of PNR trips to parking constrained zones ###
mazData$parkConstraint <- 0
mazData$parkConstraint[mazData$park_area==1] <- 1
tripsLOS$dest_park <- mazData$parkConstraint[match(tripsLOS$dest_mgra, mazData$MAZ)]

#  % of PNR trips to parking constraint zones
percentPNR <- sum(tripsLOS$access_mode=='pnr' & tripsLOS$dest_park==1)/sum(tripsLOS$access_mode=='pnr')*100
write.table("percentPNR", paste(WD,"TransitSummaries.csv", sep = "//"), sep = ",")
write.table(percentPNR, paste(WD,"TransitSummaries.csv", sep = "//"), sep = ",", append = T)

#  setType X accessType
set_access <- xtabs(~setType+access_mode, data = tripsLOS)
write.table("set_access", paste(WD,"TransitSummaries.csv", sep = "//"), sep = ",", append = T)
write.table(set_access, paste(WD,"TransitSummaries.csv", sep = "//"), sep = ",", append = T)

#  Transfers X setType
transfer_set <- xtabs(~nTransfers+setType, data = tripsLOS)
write.table("transfer_set", paste(WD,"TransitSummaries.csv", sep = "//"), sep = ",", append = T)
write.table(transfer_set, paste(WD,"TransitSummaries.csv", sep = "//"), sep = ",", append = T)

## Calculate transfer rates by period, accessType and setType
transfer_data <- aggregate(cbind(boardWeight, tripWeight)~period, data = tripsLOS, sum, na.rm = TRUE)
transfer_data$transfer_rate <- transfer_data$boardWeight/transfer_data$tripWeight
write.table("transfer_period", paste(WD,"TransitSummaries.csv", sep = "//"), sep = ",", append = T)
write.table(transfer_data, paste(WD,"TransitSummaries.csv", sep = "//"), sep = ",", append = T)

transfer_data <- aggregate(cbind(boardWeight, tripWeight)~access_mode, data = tripsLOS, sum, na.rm = TRUE)
transfer_data$transfer_rate <- transfer_data$boardWeight/transfer_data$tripWeight 
write.table("transfer_accessType", paste(WD,"TransitSummaries.csv", sep = "//"), sep = ",", append = T)
write.table(transfer_data, paste(WD,"TransitSummaries.csv", sep = "//"), sep = ",", append = T)

transfer_data <- aggregate(cbind(boardWeight, tripWeight)~setType, data = tripsLOS, sum, na.rm = TRUE)
transfer_data$transfer_rate <- transfer_data$boardWeight/transfer_data$tripWeight
write.table("transfer_setType", paste(WD,"TransitSummaries.csv", sep = "//"), sep = ",", append = T)
write.table(transfer_data, paste(WD,"TransitSummaries.csv", sep = "//"), sep = ",", append = T)

#  Transfers X accessType
transfer_access <- xtabs(~nTransfers+access_mode, data = tripsLOS)
write.table("transfer_access", paste(WD,"TransitSummaries.csv", sep = "//"), sep = ",", append = T)
write.table(transfer_access, paste(WD,"TransitSummaries.csv", sep = "//"), sep = ",", append = T)

transfer_data <- aggregate(cbind(boardWeight, tripWeight)~access_mode + setType, data = tripsLOS, sum, na.rm = TRUE)
transfer_data$transfer_rate <- transfer_data$boardWeight/transfer_data$tripWeight
write.table("transfer_access_mode_setType", paste(WD,"TransitSummaries.csv", sep = "//"), sep = ",", append = T)
write.table(transfer_data, paste(WD,"TransitSummaries.csv", sep = "//"), sep = ",", append = T)


### District to District FLows by Line Haul Mode ###
tripsLOS$OCOUNTY <- xwalk$COUNTYNAME[match(tripsLOS$orig_mgra, xwalk$MAZ)]
tripsLOS$DCOUNTY <- xwalk$COUNTYNAME[match(tripsLOS$dest_mgra, xwalk$MAZ)]
tripsLOS$OTAZ_ORIGINAL <- xwalk$TAZ_ORIGINAL[match(tripsLOS$orig_mgra, xwalk$MAZ)]
tripsLOS$DTAZ_ORIGINAL <- xwalk$TAZ_ORIGINAL[match(tripsLOS$dest_mgra, xwalk$MAZ)]
tripsLOS$OSDIST <- xwalk_SDist$district_name[match(tripsLOS$OTAZ_ORIGINAL, xwalk_SDist$TAZ_ORIGINAL)]
tripsLOS$DSDIST <- xwalk_SDist$district_name[match(tripsLOS$DTAZ_ORIGINAL, xwalk_SDist$TAZ_ORIGINAL)]

dt_tripsLOS <- data.table(tripsLOS[,c("OSDIST","DSDIST","access_mode","BEST_MODE","usedLB","usedEB","usedFR","usedLR","usedHR","usedCR")])
best_modes <- data.frame(code = c(1,2,3,4,5,6), name = c("LB", "EB", "FR", "LR", "HR", "CR"))
dt_tripsLOS$BEST_MODE <- best_modes$name[match(dt_tripsLOS$BEST_MODE, best_modes$code)]

# line haul mode summary

trips_transit_summary_best <- dt_tripsLOS[, .(count = .N), by = list(OSDIST, DSDIST, access_mode, BEST_MODE)]
trips_transit_summary_best_total <- data.table(trips_transit_summary_best[,c("OSDIST", "DSDIST", "access_mode", "count")])
trips_transit_summary_best_total <- trips_transit_summary_best_total[, (tot = sum(count)), by = list(OSDIST, DSDIST, access_mode)]
trips_transit_summary_best_total$BEST_MODE <- "Total"
names(trips_transit_summary_best_total)[names(trips_transit_summary_best_total) == "V1"] <- "count"
trips_transit_summary_best <- rbind(trips_transit_summary_best, trips_transit_summary_best_total[,c("OSDIST", "DSDIST", "access_mode", "BEST_MODE", "count")])

trips_transit_summary_best_total <- data.table(trips_transit_summary_best[,c("OSDIST", "DSDIST", "BEST_MODE", "count")])
trips_transit_summary_best_total <- trips_transit_summary_best_total[, (tot = sum(count)), by = list(OSDIST, DSDIST, BEST_MODE)]
trips_transit_summary_best_total$access_mode <- "Total"
names(trips_transit_summary_best_total)[names(trips_transit_summary_best_total) == "V1"] <- "count"
trips_transit_summary_best <- rbind(trips_transit_summary_best, trips_transit_summary_best_total[,c("OSDIST", "DSDIST", "access_mode", "BEST_MODE", "count")])

write.table(trips_transit_summary_best, paste(WD,"trips_transit_summary_best_S.csv", sep = "//"), sep = ",", row.names = F)

# used mode summary

trips_transit_summary_LB <- dt_tripsLOS[, .(freq = sum(usedLB)), by = list(OSDIST, DSDIST, access_mode)]
trips_transit_summary_LB$used_mode <- "LB"
trips_transit_summary_EB <- dt_tripsLOS[, .(freq = sum(usedEB)), by = list(OSDIST, DSDIST, access_mode)]
trips_transit_summary_EB$used_mode <- "EB"
trips_transit_summary_FR <- dt_tripsLOS[, .(freq = sum(usedFR)), by = list(OSDIST, DSDIST, access_mode)]
trips_transit_summary_FR$used_mode <- "FR"
trips_transit_summary_LR <- dt_tripsLOS[, .(freq = sum(usedLR)), by = list(OSDIST, DSDIST, access_mode)]
trips_transit_summary_LR$used_mode <- "LR"
trips_transit_summary_HR <- dt_tripsLOS[, .(freq = sum(usedHR)), by = list(OSDIST, DSDIST, access_mode)]
trips_transit_summary_HR$used_mode <- "HR"
trips_transit_summary_CR <- dt_tripsLOS[, .(freq = sum(usedCR)), by = list(OSDIST, DSDIST, access_mode)]
trips_transit_summary_CR$used_mode <- "CR"

trips_transit_summary_used <- rbind(trips_transit_summary_LB, 
                                    trips_transit_summary_EB,
                                    trips_transit_summary_FR,
                                    trips_transit_summary_LR,
                                    trips_transit_summary_HR,
                                    trips_transit_summary_CR)

trips_transit_summary_used_total <- data.table(trips_transit_summary_used[,c("OSDIST", "DSDIST", "access_mode", "freq")])
trips_transit_summary_used_total <- trips_transit_summary_used_total[, (tot = sum(freq)), by = list(OSDIST, DSDIST, access_mode)]
trips_transit_summary_used_total$used_mode <- "Total"
names(trips_transit_summary_used_total)[names(trips_transit_summary_used_total) == "V1"] <- "freq"
trips_transit_summary_used <- rbind(trips_transit_summary_used, trips_transit_summary_used_total[,c("OSDIST", "DSDIST", "access_mode", "used_mode", "freq")])

trips_transit_summary_used_total <- data.table(trips_transit_summary_used[,c("OSDIST", "DSDIST", "used_mode", "freq")])
trips_transit_summary_used_total <- trips_transit_summary_used_total[, (tot = sum(freq)), by = list(OSDIST, DSDIST, used_mode)]
trips_transit_summary_used_total$access_mode <- "Total"
names(trips_transit_summary_used_total)[names(trips_transit_summary_used_total) == "V1"] <- "freq"
trips_transit_summary_used <- rbind(trips_transit_summary_used, trips_transit_summary_used_total[,c("OSDIST", "DSDIST", "access_mode", "used_mode", "freq")])

trips_transit_summary_used <- trips_transit_summary_used[,c("OSDIST","DSDIST","access_mode","used_mode","freq")]

write.table(trips_transit_summary_used, paste(WD,"trips_transit_summary_used_S.csv", sep = "//"), sep = ",", row.names = F)


### County-County Flow of Transit Trips ###
#   joint trips/tours do not use transit in model
trips_transit <- trips[trips$TRIPMODE %in% c(6,7,8),]
trips_transit$access_mode[trips_transit$TRIPMODE==6] <- "walk"
trips_transit$access_mode[trips_transit$TRIPMODE==7] <- "pnr"
trips_transit$access_mode[trips_transit$TRIPMODE==8] <- "knr"
trips_transit$tourtype <- "Non-Mandatory"
trips_transit$tourtype[trips_transit$TOURPURP <= 3] <- "Mandatory"
transit_trips <- trips_transit
trips_transit <- data.table(trips_transit[,c("OCOUNTY", "DCOUNTY", "OSDIST", "DSDIST", "access_mode", "tourtype")]) # changed by khademul

trips_transit_summary <- trips_transit[, .(count = .N), by = list(OCOUNTY, DCOUNTY, access_mode, tourtype)]
trips_transit_summary_total <- data.table(trips_transit_summary[,c("OCOUNTY", "DCOUNTY", "access_mode", "count")])
trips_transit_summary_total <- trips_transit_summary_total[, (tot = sum(count)), by = list(OCOUNTY, DCOUNTY, access_mode)]
trips_transit_summary_total$tourtype <- "Total"
names(trips_transit_summary_total)[names(trips_transit_summary_total) == "V1"] <- "count"
trips_transit_summary <- rbind(trips_transit_summary, trips_transit_summary_total[,c("OCOUNTY", "DCOUNTY", "access_mode", "tourtype", "count")])

trips_transit_summary_total <- data.table(trips_transit_summary[,c("OCOUNTY", "DCOUNTY", "tourtype", "count")])
trips_transit_summary_total <- trips_transit_summary_total[, (tot = sum(count)), by = list(OCOUNTY, DCOUNTY, tourtype)]
trips_transit_summary_total$access_mode <- "Total"
names(trips_transit_summary_total)[names(trips_transit_summary_total) == "V1"] <- "count"
trips_transit_summary <- rbind(trips_transit_summary, trips_transit_summary_total[,c("OCOUNTY", "DCOUNTY", "access_mode", "tourtype", "count")])


write.table(trips_transit_summary, paste(WD,"trips_transit_summary.csv", sep = "//"), sep = ",", row.names = F)

# added by khademul
trips_transit_summary_S <- trips_transit[, .(count = .N), by = list(OSDIST, DSDIST, access_mode, tourtype)]
trips_transit_summary_total_S <- data.table(trips_transit_summary_S[,c("OSDIST", "DSDIST", "access_mode", "count")])
trips_transit_summary_total_S <- trips_transit_summary_total_S[, (tot = sum(count)), by = list(OSDIST, DSDIST, access_mode)]
trips_transit_summary_total_S$tourtype <- "Total"
names(trips_transit_summary_total_S)[names(trips_transit_summary_total_S) == "V1"] <- "count"
trips_transit_summary_S <- rbind(trips_transit_summary_S, trips_transit_summary_total_S[,c("OSDIST", "DSDIST", "access_mode", "tourtype", "count")])

trips_transit_summary_total_S <- data.table(trips_transit_summary_S[,c("OSDIST", "DSDIST", "tourtype", "count")])
trips_transit_summary_total_S <- trips_transit_summary_total_S[, (tot = sum(count)), by = list(OSDIST, DSDIST, tourtype)]
trips_transit_summary_total_S$access_mode <- "Total"
names(trips_transit_summary_total_S)[names(trips_transit_summary_total_S) == "V1"] <- "count"
trips_transit_summary_S <- rbind(trips_transit_summary_S, trips_transit_summary_total_S[,c("OSDIST", "DSDIST", "access_mode", "tourtype", "count")])


write.table(trips_transit_summary_S, paste(WD,"trips_transit_summary_S.csv", sep = "//"), sep = ",", row.names = F)




### Trip Length Distribution of Trasit Trips ###

# code distance bins
transit_trips$distbin <- cut(transit_trips$od_dist, breaks = c(seq(0,50, by=1), 9999), labels = F, right = F)
distBinCat <- data.frame(distbin = seq(1,51, by=1))

transit_trips$distbin10 <- cut(transit_trips$od_dist, breaks = c(seq(0,2, by=0.1), 9999), labels = F, right = F)
distBinCat10 <- data.frame(distbin10 = seq(1,21, by=1))

# compute TLFDs by district and total
tlfd_transit <- ddply(transit_trips[,c("access_mode", "distbin")], c("access_mode", "distbin"), summarise, transit = sum(!is.na(access_mode)))
tlfd_transit <- cast(tlfd_transit, distbin~access_mode, value = "transit", sum)
tlfd_transit$Total <- rowSums(tlfd_transit[,!colnames(tlfd_transit) %in% c("distbin")])
tlfd_transit_df <- merge(x = distBinCat, y = tlfd_transit, by = "distbin", all.x = TRUE)
tlfd_transit_df[is.na(tlfd_transit_df)] <- 0

write.csv(tlfd_transit_df, "transitTLFD.csv", row.names = F)

# compute TLFDs by tenths of mile
tlfd_transit <- ddply(transit_trips[,c("access_mode", "distbin10")], c("access_mode", "distbin10"), summarise, transit = sum(!is.na(access_mode)))
tlfd_transit <- cast(tlfd_transit, distbin10~access_mode, value = "transit", sum)
tlfd_transit$Total <- rowSums(tlfd_transit[,!colnames(tlfd_transit) %in% c("distbin10")])
tlfd_transit_df <- merge(x = distBinCat10, y = tlfd_transit, by = "distbin10", all.x = TRUE)
tlfd_transit_df[is.na(tlfd_transit_df)] <- 0

write.csv(tlfd_transit_df, "transitTLFD10.csv", row.names = F)

# parking provision model
fpSummary <- table(per$fp_choice)
write.table("fpSummary", "fpSummary.csv", sep = ",")
write.table(fpSummary, "fpSummary.csv", sep = ",", row.names = F, append = T)

# work tour going to parking constraint
tours_transit <- tours[tours$TOURMODE %in% c(6,7,8),]
tours_transit$access_mode[tours_transit$TOURMODE==6] <- "walk"
tours_transit$access_mode[tours_transit$TOURMODE==7] <- "pnr"
tours_transit$access_mode[tours_transit$TOURMODE==8] <- "knr"
tours_transit$dest_park <- mazData$parkConstraint[match(tours_transit$dest_mgra, mazData$MAZ)]

work_Tours <- table(tours_transit$access_mode[tours_transit$dest_park==1 & tours_transit$TOURPURP==1])
write.table("work_Tours", "work_Tours.csv", sep = ",")
write.table(work_Tours, "work_Tours.csv", sep = ",", row.names = F, append = T)

# Number of workers with work location in parking constraint zones
wsLoc$dest_park <- mazData$parkConstraint[match(wsLoc$WorkLocation, mazData$MAZ)]
workersParkZone <- table(wsLoc$dest_park)
write.table("workersParkZone", "workersParkZone.csv", sep = ",")
write.table(workersParkZone, "workersParkZone.csv", sep = ",", row.names = F, append = T)

#finish