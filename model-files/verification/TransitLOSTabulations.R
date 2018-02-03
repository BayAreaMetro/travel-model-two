# Dora Wu @ WSP USA Inc 12-12-2017
# script to generate transit LOS summaries

# arguments :
# RUNDIR, the folder where the run is located
# CREATE_TRIP_TOUR_FILES, if set to 0, assume tour/trip files with XFERS and BEST_MODE already exist in model run folder,
#                         else run appendLOSAttributes.R to create those files
# DISTRICT_COLUMN, column name of the district column in the TAZ file
# TRIP_IN_PA, if set to 1, trip district summary will be in PA format, else it will be in OD format 
# OUTFILE, the name of the output excel spreadsheet
# example: %R_LOC%\Rscript.exe --vanilla --verbose TransitLOSTabulations.R "C:\projects\mtc\tm2_2000" 1 DIST 1 Transit_LOS_summaries.xlsx > LOSTabulation.log
# 


args = commandArgs(TRUE)

RUNDIR = args[1]
CREATE_TOUR_TRIP_FILES = as.integer(args[2])
DISTRICT_COLUMN = args[3]
TRIP_IN_PA = as.integer(args[4])
OUTFILE = args[5]

list.of.packages <- c("reshape", "devtools", "foreign", "xlsx", "dplyr", "data.table")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]

if(length(new.packages)) install.packages(new.packages, repos='http://cran.us.r-project.org')

library(devtools)
library(reshape)
library(foreign)
library(xlsx)
library(data.table)
library(dplyr)

# for first time users
if(!require(rhdf5)){
    source("http://bioconductor.org/biocLite.R")
    biocLite("rhdf5")
    library(rhdf5)
}

if(!require(omxr)){
    devtools::install_github("gregmacfarlane/omxr")
    library(omxr)
}



# -------------- convert highway skims to OMX ----------------------

for ( tod in c("AM", "MD", "PM", "EV", "EA")){
    
    filename <- paste0(RUNDIR, "\\skims\\HWYSKM", tod, "_taz.TPP")
    omxname <- paste0(RUNDIR, "\\skims\\HWYSKM", tod, "_taz.omx")
    if(!file.exists(omxname)) {
        cmmd <- paste0("cube2omx.exe ", filename)
        print(cmmd)
        system(cmmd)
    }
}



AddTODNum <- function(TimePeriod) {
    
    # Function to get time period number because we need to do it multiple times
    # Args:
    #   TimePeriod: time period number from 
    
    tod <- numeric(length(TimePeriod))
    tod <- ifelse(TimePeriod <= 3, 5, tod)                     # EA
    tod <- ifelse(TimePeriod > 3 & TimePeriod <= 9, 1, tod)   # AM
    tod <- ifelse(TimePeriod > 9 & TimePeriod <= 22, 2, tod)  # MD
    tod <- ifelse(TimePeriod > 22 & TimePeriod <= 29, 3, tod)  # PM
    tod <- ifelse(TimePeriod > 29 & TimePeriod <= 40, 4, tod)  # EV
    
    return(tod)
    
}

BESTMODE_DICT <- data.frame(num = 0:6, 
                           name = c("NonTransit", "LocalBus", "ExpressBus", 
                                    "Ferry", "LRT", "HRT", "CMR"), 
                           stringsAsFactors = FALSE)


COUNTYDICT <- data.frame(NUM = 1:9, 
                         NAME = c("San Francisco",
                                  "San Mateo",
                                  "Santa Clara",
                                  "Alameda",
                                  "Contra Costa",
                                  "Solano",
                                  "Napa",
                                  "Sonoma",
                                  "Marin"))


TOURPURPOSE_DICT <- data.frame(num = 0:9,
                               name = c("Work", 
                                        "School", 
                                        "University", 
                                        "Maintenance",
                                        "Shop",
                                        "Discretionary",
                                        "Visiting",
                                        "Escort",
                                        "Eating Out",
                                        "Work-Based"),
                               stringsAsFactors = FALSE)

# read in highway DA distance skims and save in memory
hwySkimList <- c("HWYSKMAM_taz.omx", 
                 "HWYSKMMD_taz.omx",
                 "HWYSKMPM_taz.omx",
                 "HWYSKMEV_taz.omx",
                 "HWYSKMEA_taz.omx")

hwySkimFiles <- paste0(RUNDIR, "\\skims\\", hwySkimList)

allHwySkim <- lapply(1:length(hwySkimFiles), function(i) read_omx(hwySkimFiles[i], "DISTDA"))


# ----------------------------- read in SED -------------------------

tazfile <- read.csv(paste0(RUNDIR, "\\landuse\\taz_data.csv"), stringsAsFactors = FALSE)
taz2dist <- subset(tazfile, select = c("TAZ", DISTRICT_COLUMN))
colnames(taz2dist) <- c("TAZ", "District")

mazfile <- read.csv(paste0(RUNDIR, "\\landuse\\maz_data.csv"), stringsAsFactors = FALSE)
mazfile$DIST <- taz2dist$District[match(mazfile$TAZ, taz2dist$TAZ)]

tapfile <- read.csv(paste0(RUNDIR, "\\hwy\\tap_data.csv"), header = TRUE, stringsAsFactors = FALSE)

# get distance between PNR TAP and their corresponding TAZ
tap2taz <- fread(paste0(RUNDIR, "\\hwy\\tap_to_taz_for_parking.txt"),
                 colClasses = c("integer", "integer", "NULL", "NULL", "numeric"),
                 nrows = -1)
colnames(tap2taz) = c("TAP_ORIGINAL", "TAZ_ORIGINAL", "Distance")
tap2taz$TAP <- tapfile$tap[match(tap2taz$TAP_ORIGINAL, tapfile$tap_original)]
tap2taz$TAZ <- tazfile$TAZ[match(tap2taz$TAZ_ORIGINAL, tazfile$TAZ_ORIGINAL)]
tap2taz$index <- tap2taz$TAZ * 10000 + tap2taz$TAP

hh <- fread(paste0(RUNDIR, "\\ctramp_output\\householdData_1.csv"),
                   colClasses = c("integer", "NULL", "NULL", "integer", 
                                  "NULL", "NULL", "NULL"), nrows = -1)

persons <- fread(paste0(RUNDIR, "\\ctramp_output\\personData_1.csv"),
                 colClasses = c("integer", rep("NULL", 4), "character", 
                                rep("NULL", 6)), nrows = -1)

persons$driver <- ifelse(persons$type %in% c("Child too young for school",
                                             "Student of non-driving age"), 0, 1)
hhDriver <- aggregate(driver ~ hh_id, data = persons, sum)

hh <- hh %>% 
    left_join(hhDriver, by = c("hh_id")) %>% 
    mutate(autoSuff = ifelse(autos >= driver, "sufficient", "deficient"),
           autoSuff = ifelse(autos == 0, "zeroCar", autoSuff)) 


wAccDist <- fread(paste0(RUNDIR, "\\skims\\ped_distance_maz_tap.txt"), 
                 colClasses = c("integer", "integer", "NULL", "NULL", "numeric"), 
                 nrows = -1)
colnames(wAccDist) <- c("MAZ", "TAP", "Distance")
wAccDist$index <- wAccDist$MAZ * 10000 + wAccDist$TAP


# -----------------   read in tour and trip files -----------------------

# create tour and trip files with XFERS and BEST_MODE if they don't exist
# appendLOSAttributes.R need to be called from the run folder
# make sure both appendLOSAttributes.R and cube2mat.exe are in the run folder
if (CREATE_TOUR_TRIP_FILES){
    cwd <- getwd()
	setwd(RUNDIR)
    system("Rscript.exe --vanilla --verbose appendLOSAttributes.R 1 0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1")
	setwd(cwd)
}


tourfileClass <- c(rep("integer", 5), "character", "character",
                   rep("integer", 5), "numeric", "numeric", 
                   rep("integer", 9), rep("numeric", 28), rep("integer", 5))


itransTour <- fread(paste0(RUNDIR, "\\individual_transitTour_wLOS.csv"), 
                    colClasses = tourfileClass, 
                    nrows = -1, header = TRUE)


tripfileClass <- c(rep("integer", 6), rep("character", 3), "integer", "integer",
                   "numeric", rep("integer", 7), "numeric", "numeric", "numeric", 
                   rep("integer", 4))

itransTrip <- fread(paste0(RUNDIR, "\\individual_transitTrip_wLOS.csv"), 
                    colClasses = tripfileClass, 
                    nrows = -1, header = TRUE)

itripClasses <- c(rep("integer", 6), 'character', 'character', 'character',
                  'integer', 'integer', 'numeric', rep("integer", 3), 
                  rep("NULL", 8))
itrip <- fread(paste0(RUNDIR, "\\ctramp_output\\indivTripData_1.csv"), 
               colClasses = itripClasses, nrows = -1)


# ----------------  process tour file -------------------------------

itransTour <- itransTour %>% 
    mutate(start_tod = AddTODNum(start_period),
           ODIST = mazfile$DIST[match(orig_mgra, mazfile$MAZ)],
           DDIST = mazfile$DIST[match(dest_mgra, mazfile$MAZ)],
           OTAZ = mazfile$TAZ[match(orig_mgra, mazfile$MAZ)],
           autoSuff = hh$autoSuff[match(hh_id, hh$hh_id)],
           parkingTAZ = ifelse(tour_mode == 11, 1, tapfile$taz[match(out_btap, tapfile$tap)]),
           accindex_OUT = ifelse(tour_mode == 11, 
                                 orig_mgra * 10000 + out_btap,
                                 parkingTAZ * 10000 + out_btap),
           accDist_OUT = ifelse(tour_mode == 11,
                                wAccDist$Distance[match(accindex_OUT, wAccDist$index)],
                                tap2taz$Distance[match(accindex_OUT, tap2taz$index)])) %>% 
    rowwise() %>%
    mutate(drvDist = ifelse(tour_mode == 11, 0, allHwySkim[[start_tod]][OTAZ, parkingTAZ]),
           accDist_OUT = accDist_OUT/5280 + drvDist,
           accDistC = ifelse(tour_mode == 11, accDist_OUT %/% 0.25, accDist_OUT %/% 1),
           accessMode = ifelse(tour_mode == 11, "Walk", 
                            ifelse(tour_mode == 12, "PNR", "KNR"))) %>% 
    rename(tours = tourWeight) %>% 
    mutate(tourPurpNum = TOURPURPOSE_DICT$num[match(tour_purpose, TOURPURPOSE_DICT$name)],
           tourindex = person_id * 1000 + tourPurpNum * 100 + tour_id)


# ---------------- Process Trip File ---------------------------------


itransTrip <- itransTrip %>% 
    filter(BEST_MODE != 0) %>% 
    mutate(tod = AddTODNum(stop_period),
           ODIST = mazfile$DIST[match(orig_mgra, mazfile$MAZ)],
           DDIST = mazfile$DIST[match(dest_mgra, mazfile$MAZ)],
	   PDIST = ifelse(inbound == 0, ODIST, DDIST),
           ADIST = ifelse(inbound == 0, DDIST, ODIST),
           PMAZ = ifelse(inbound == 0, orig_mgra, dest_mgra),
           PTAZ = mazfile$TAZ[match(PMAZ, mazfile$MAZ)],
           PTAP = ifelse(inbound == 0, trip_board_tap, trip_alight_tap),
           parkingTAZ = ifelse(trip_mode == 11, 1, 
                               tapfile$taz[match(PTAP, tapfile$tap)]),
           accindex = ifelse(trip_mode == 11, PMAZ * 10000 + PTAP, 
                             parkingTAZ * 10000 + PTAP),
           accDist = ifelse(trip_mode == 11,
                            wAccDist$Distance[match(accindex, wAccDist$index)],
                            tap2taz$Distance[match(accindex, tap2taz$index)])) %>% 
    rowwise() %>% 
    mutate(drvDist = ifelse(trip_mode == 11, 0, 
                            ifelse(inbound == 0, 
							       allHwySkim[[tod]][PTAZ, parkingTAZ],
							       allHwySkim[[tod]][parkingTAZ, PTAZ])),
           accDist = accDist/5280 + drvDist,
           accDistC = ifelse(trip_mode == 11, accDist %/% 0.25, accDist %/% 1),
           accessMode = ifelse(trip_mode == 11, "Walk", 
                               ifelse(trip_mode == 12, "PNR", "KNR"))) %>% 
    rename(trips =  tripWeight) %>% 
    mutate(tourPurpNum = TOURPURPOSE_DICT$num[match(tour_purpose, TOURPURPOSE_DICT$name)],
           tourindex = person_id * 1000 + tourPurpNum * 100 + tour_id)


rm(allHwySkim)
gc()


# ----------- More processing for tour and Trip Mode Comparison --------------

# for each tour, check if either or both inbound and outbound trip is transit trip,
# from trip file
itrip <- itrip %>% 
    mutate(tourPurpNum = TOURPURPOSE_DICT$num[match(tour_purpose, TOURPURPOSE_DICT$name)],
           tourindex = person_id * 1000 + tourPurpNum * 100 + tour_id,
           intrip_transit = ifelse(inbound == 1 & trip_mode %in% c(11, 12, 13), 1, 0),
           outtrip_transit = ifelse(inbound == 0 & trip_mode %in% c(11, 12, 13), 1, 0))


tripmode <- aggregate(cbind(intrip_transit, outtrip_transit) ~ tourindex, data = itrip, sum)

itransTour <- merge(itransTour, tripmode, by = "tourindex", all.x = TRUE)

itransTour <- itransTour %>% 
    mutate(transittour = ifelse(BEST_MODE_IN & BEST_MODE_OUT, "BOTH", "NOT TRANSIT"), 
           transittour = ifelse((BEST_MODE_IN == 0) & BEST_MODE_OUT, "OUTBOUND ONLY", transittour),
           transittour = ifelse((BEST_MODE_OUT == 0) & BEST_MODE_IN, "INBOUND ONLY", transittour),
           transittrip = ifelse(outtrip_transit & intrip_transit, "BOTH", "NOT TRANSIT"),
           transittrip = ifelse(outtrip_transit & (intrip_transit == 0), "OUTBOUND ONLY", transittrip),
           transittrip = ifelse((outtrip_transit == 0) & intrip_transit, "INBOUND ONLY", transittrip))


itransTrip_melt <- melt(itransTrip, id.vars = c("tourindex", "inbound"), measure.vars = c("BEST_MODE"))

trip_bestmode <- cast(itransTrip_melt, tourindex ~ inbound, max)
colnames(trip_bestmode) = c("tourindex", "tripOutMode", "tripInMode")
trip_bestmode <- do.call(data.frame,lapply(trip_bestmode, 
                                           function(x) replace(x, is.infinite(x), 0)))

itransTour <- merge(itransTour, trip_bestmode, by = "tourindex", all.x = TRUE)

itransTour <- itransTour %>% 
    mutate(modeMatch = ifelse(transittour == "INBOUND ONLY" & 
                                  transittrip %in% c("INBOUND ONLY", "BOTH") & 
                                  BEST_MODE_IN == tripInMode, tours, 0),
           modeMatch = ifelse(transittrip == "INBOUND ONLY" & 
                                  transittour %in% c("INBOUND ONLY", "BOTH") & 
                                  BEST_MODE_IN == tripInMode, tours, modeMatch),
           modeMatch = ifelse(transittour == "OUTBOUND ONLY" & 
                                  transittrip %in% c("OUTBOUND ONLY", "BOTH") & 
                                  BEST_MODE_OUT == tripOutMode, tours, modeMatch),
           modeMatch = ifelse(transittrip == "OUTBOUND ONLY" & 
                                  transittour %in% c("OUTBOUND ONLY", "BOTH") & 
                                  BEST_MODE_OUT == tripOutMode, tours, modeMatch),
           modeMatch = ifelse(transittour == "BOTH" & 
                                  transittrip == "BOTH" & 
                                  BEST_MODE_OUT == tripOutMode & 
                                  BEST_MODE_IN == tripInMode, tours, modeMatch))

itransTrip$tourBestMode <- ifelse(itransTrip$inbound == 0, 
                                  itransTour$BEST_MODE_OUT[match(itransTrip$tourindex, itransTour$tourindex)], 
                                  itransTour$BEST_MODE_IN[match(itransTrip$tourindex, itransTour$tourindex)])


# ---------- convert variables to factors so the summaries look nice ----------

# tour file

itransTour$BEST_MODE_OUT <- BESTMODE_DICT$name[match(itransTour$BEST_MODE_OUT, BESTMODE_DICT$num)]
itransTour$BEST_MODE_IN <- BESTMODE_DICT$name[match(itransTour$BEST_MODE_IN, BESTMODE_DICT$num)]

itransTour$BEST_MODE_OUT <- factor(itransTour$BEST_MODE_OUT, levels = BESTMODE_DICT$name)
itransTour$BEST_MODE_IN <- factor(itransTour$BEST_MODE_IN, levels = BESTMODE_DICT$name)

itransTour$autoSuff <- factor(itransTour$autoSuff, 
                              levels = c("zeroCar", "deficient", "sufficient"))

itransTour$accessMode <- factor(itransTour$accessMode, levels = c("Walk", "PNR", "KNR"))

itransTour$transittour <- factor(itransTour$transittour, levels = c("BOTH", "INBOUND ONLY", "OUTBOUND ONLY"))
itransTour$transittrip <- factor(itransTour$transittrip, levels = c("BOTH", "INBOUND ONLY", 
                                                                    "OUTBOUND ONLY", "NOT TRANSIT"))

# trip file

itransTrip$BEST_MODE <- BESTMODE_DICT$name[match(itransTrip$BEST_MODE, BESTMODE_DICT$num)]
itransTrip$BEST_MODE <- factor(itransTrip$BEST_MODE, levels = BESTMODE_DICT$name)

itransTrip$tourBestMode <- BESTMODE_DICT$name[match(itransTrip$tourBestMode, BESTMODE_DICT$num)]
itransTrip$tourBestMode <- factor(itransTrip$tourBestMode, levels = BESTMODE_DICT$name)


itransTrip$accessMode <- factor(itransTrip$accessMode, levels = c("Walk", "PNR", "KNR"))


# ------------------ Create summary tables ------------------------------------


# summary 1 - transit tours by district, primary mode, and auto sufficiency 
summ1_to_cast <- melt(itransTour, id.vars = c("ODIST", "DDIST", "BEST_MODE_OUT",
                                                  "BEST_MODE_IN", "autoSuff"),
                          measure.vars = c("tours"))

summ1 <- cast(summ1_to_cast, ODIST + DDIST + BEST_MODE_OUT + BEST_MODE_IN ~ autoSuff,
                  sum, margins = TRUE)

# summary 2 - transit trips by primary mode
summ2 <- aggregate(trips ~ BEST_MODE, data = itransTrip, sum)
summ2$BEST_MODE <- as.character(summ2$BEST_MODE)
summ2 <- rbind(summ2, c("Total", sum(summ2$trips)))
summ2$trips <- as.numeric(summ2$trips)

# summary 3 - transit trips by access mode
summ3 <- aggregate(trips ~ accessMode, data = itransTrip, sum)
summ3$accessMode <- as.character(summ3$accessMode)
summ3 <- rbind(summ3, c("Total", sum(summ3$trips)))
summ3$trips <- as.numeric(summ3$trips)

# summary 4 - transit trips by district, primary mode and access mode
if (TRIP_IN_PA) {
    summ4_to_cast <- melt(itransTrip, id.vars = c("PDIST", "ADIST", "BEST_MODE",
                                              "accessMode"),
                      measure.vars = c("trips"))
    summ4 <- cast(summ4_to_cast, PDIST + ADIST + BEST_MODE ~ accessMode, sum, margins = TRUE)
} else {
    summ4_to_cast <- melt(itransTrip, id.vars = c("ODIST", "DDIST", "BEST_MODE",
                                                  "accessMode"),
                          measure.vars = c("trips"))
    summ4 <- cast(summ4_to_cast, ODIST + DDIST + BEST_MODE ~ accessMode, sum, margins = TRUE)
    }

# summary 5 - transit tours by primary mode, access mode and access distance
summ5 <- aggregate(tours ~ BEST_MODE_IN + BEST_MODE_OUT + accDistC + accessMode, 
                   data = itransTour, sum)

summ5 <- summ5 %>% 
    mutate(accessDistance = ifelse(accessMode == "Walk", 
                                   paste0(as.character(accDistC * 0.25), "-", 
                                          as.character((accDistC + 1) * 0.25), " mile"),
                                   paste0(as.character(accDistC), "-", 
                                          as.character(accDistC + 1), " mile"))) %>% 
    select(accessMode, accessDistance, BEST_MODE_OUT, BEST_MODE_IN, tours) 

# summary 6 -  transit trips by primary mode, access mode and access distance
summ6 <- aggregate(trips ~ BEST_MODE + accDistC + accessMode, data = itransTrip, sum)

summ6 <- summ6 %>% 
    mutate(accessDistance = ifelse(accessMode == "Walk", 
                                   paste0(as.character(accDistC * 0.25), "-", 
                                          as.character((accDistC + 1) * 0.25), " mile"),
                                   paste0(as.character(accDistC), "-", 
                                          as.character(accDistC + 1), " mile"))) %>% 
    select(accessMode, accessDistance, BEST_MODE, trips) 

# summary 7 - transit tours by primary mode, number of tranfers and access mode
summ7_to_cast <- melt(itransTour, id.vars = c("XFERS_OUT", "XFERS_IN", 
                                              "BEST_MODE_OUT", "BEST_MODE_IN",
                                              "accessMode"), 
                      measure.vars = c("tours"))

summ7 <- cast(summ7_to_cast, BEST_MODE_OUT + BEST_MODE_IN + XFERS_OUT + XFERS_IN ~ accessMode,
              sum, margins = TRUE)

# summary 8 - transit trips by primary mode, number of transfer and access mode
summ8_to_cast <- melt(itransTrip, id.vars = c("XFERS", "BEST_MODE", "accessMode"),
                      measure.vars = c("trips"))

summ8 <- cast(summ8_to_cast, BEST_MODE + XFERS ~ accessMode, sum, margins = TRUE)


# summary 9 - tour and trip mode matrix
summ9_to_cast <- melt(itransTour, id.vars = c("transittour", "transittrip"), 
                        measure.vars = c("tours"))
summ9 <- cast(summ9_to_cast, transittour ~ transittrip, sum, margins = TRUE)

summ9_pct <- cast(summ9_to_cast, transittour ~ transittrip, sum)
summ9_pct[, 2:ncol(summ9_pct)] <- summ9_pct[, 2:ncol(summ9_pct)]/rowSums(summ9_pct)


# transit tours by primary mode match (with trips')
modematch_melt <- melt(itransTour, id.vars = c("transittour", "transittrip"),
                       measure.vars = c("modeMatch"))
bestModeMatch <- cast(modematch_melt, transittour ~ transittrip, sum)


# transit trips by tour and trip primary mode
tripModeMatch_melt <- melt(itransTrip, id.vars = c("tourBestMode", "BEST_MODE"),
                           measure.vars = c("trips"))
tripModeMatch <- cast(tripModeMatch_melt, tourBestMode ~ BEST_MODE, sum, margins = TRUE)



##########################################################################
#
#   Write summaries out to Excel
#
##########################################################################

# ------------ set up basic formatting for the workbook ------------
wb<-createWorkbook(type="xlsx")

TITLE_STYLE <- CellStyle(wb)+ Font(wb,  heightInPoints=14, 
                                   isBold=TRUE, underline=1)


# Styles for the data table row/column names
TABLE_ROWNAMES_STYLE <- CellStyle(wb) + Font(wb, isBold=TRUE)
TABLE_COLNAMES_STYLE <- CellStyle(wb) + Font(wb, isBold=TRUE) +
    Alignment(horizontal="ALIGN_CENTER") +
    Border(color="black", position=c("TOP", "BOTTOM"), 
           pen=c("BORDER_THIN", "BORDER_THICK")) 

GRAY_BACKGROUND <- Fill(backgroundColor = "grey86", foregroundColor = "grey86")
LIGHTBLUE_BACKGROUND <- Fill(backgroundColor = "lightblue", foregroundColor = "lightblue")

csNumColumn <- CellStyle(wb, dataFormat=DataFormat("#,##0"))
csPctColumn <- CellStyle(wb, dataFormat=DataFormat("0.0%"))
csOtherColumn <- CellStyle(wb, dataFormat=NULL, alignment=NULL,
                           border=NULL, fill=NULL, font=NULL)

# Helper function to add titles

xlsx.addTitle<-function(sheet, rowIndex, title, titleStyle){
    rows <-createRow(sheet,rowIndex=rowIndex)
    sheetTitle <-createCell(rows, colIndex=1)
    setCellValue(sheetTitle[[1,1]], title)
    setCellStyle(sheetTitle[[1,1]], titleStyle)
}

# function to add borders surrounding cellblock

xlsx.addBorderFrame <- function(cellblock, startRow, startCol, endRow, endCol, thickness){
    
    top_border <- Border(color="black", position=c("TOP"), pen=c(thickness))
    bottom_border <- Border(color="black", position=c("BOTTOM"), pen=c(thickness))
    left_border <- Border(color="black", position=c("LEFT"), pen=c(thickness))
    right_border <- Border(color="black", position=c("RIGHT"), pen=c(thickness))
    
    CB.setBorder(cellblock, top_border, startRow, startCol:endCol)
    CB.setBorder(cellblock, bottom_border, endRow, startCol:endCol)
    CB.setBorder(cellblock, left_border, startRow:endRow, startCol)
    CB.setBorder(cellblock, right_border, startRow:endRow, endCol)
    
    
}


# function to add row and column variable description
# startRow, startCol are the start point of the data.frame
# numRow, numCol correspond to the dimension of the data.frame
xlsx.addRowColDesc <- function(sheetName, startRow, startCol, numRow, numCol, 
                               fillcolor, rowDesc, colDesc) {
    # row description
    colCB <- CellBlock(sheetName, startRow+1, startCol-1, numRow, 1, create = TRUE)
    
    CB.setColData(colCB, rowDesc, 1, rowOffset=0, showNA=TRUE, 
                  colStyle=CellStyle(wb) +
                      Alignment(horizontal = "ALIGN_CENTER", vertical = "VERTICAL_CENTER"))
    CB.setFill(colCB, fillcolor, 1:numRow, 1)
    addMergedRegion(sheetName, startRow+1, startRow+numRow, startCol-1, startCol-1)
    
    # column description               
    rowCB <- CellBlock(sheetName, startRow-1, startCol+1, 1, numCol-1, create = TRUE)
    CB.setRowData(rowCB, colDesc, 1, colOffset=0, showNA=TRUE, 
                  rowStyle=CellStyle(wb) +
                      Alignment(horizontal = "ALIGN_CENTER", vertical = "VERTICAL_CENTER"))
    CB.setFill(rowCB, fillcolor, 1, 1:(numCol-1))
    addMergedRegion(sheetName, startRow-1, startRow-1, startCol+1, startCol+numCol-1)
    
}


# ------------- Sheet 1 ----------------

sheet1 <- createSheet(wb, sheetName = "Tours by OD Dist, Mode & Auto")

xlsx.addTitle(sheet1, rowIndex=1, 
              title="Transit Tours by Origin/Destination District, Primary Transit Mode and Auto Sufficiency",
              titleStyle = TITLE_STYLE)

summ1.colVar = list(
    '1'=csOtherColumn,
    '2'=csOtherColumn,
    '3'=csOtherColumn,
    '4'=csOtherColumn)
summ1.colNum =list(
    '5'=csNumColumn,
    '6'=csNumColumn,
    '7'=csNumColumn,
    '8'=csNumColumn)

addDataFrame(summ1, sheet1, startRow=3, startColumn=1,
             colStyle=c(summ1.colVar, summ1.colNum),
             colnamesStyle = TABLE_COLNAMES_STYLE,
             rownamesStyle = TABLE_ROWNAMES_STYLE,
             row.names = FALSE)


setColumnWidth(sheet1, colIndex=c(1:2), colWidth=8)
setColumnWidth(sheet1, colIndex=c(3:4), colWidth=16)
setColumnWidth(sheet1, colIndex=c(5:ncol(summ1)), colWidth=12)

createFreezePane(sheet1, 4, 1, 4, 1)


# ------------- Sheet 2 ----------------

sheet2 <- createSheet(wb, sheetName = "Trips by OD Dist, Mode & Access")

xlsx.addTitle(sheet2, rowIndex=1, 
              title="Transit Trips by Primary Mode",
              titleStyle = TITLE_STYLE)

summ2.colVar = list('1' = csOtherColumn)
summ2.colNum = list('2' = csNumColumn)

addDataFrame(summ2, sheet2, startRow=3, startColumn=1,
             colStyle=c(summ2.colVar, summ2.colNum),
             colnamesStyle = TABLE_COLNAMES_STYLE,
             rownamesStyle = TABLE_ROWNAMES_STYLE,
             row.names = FALSE)


xlsx.addTitle(sheet2, rowIndex=12, 
              title="Transit Trips by Access Mode",
              titleStyle = TITLE_STYLE)

addDataFrame(summ3, sheet2, startRow=14, startColumn=1,
             colStyle=c(summ2.colVar, summ2.colNum),
             colnamesStyle = TABLE_COLNAMES_STYLE,
             rownamesStyle = TABLE_ROWNAMES_STYLE,
             row.names = FALSE)

if (TRIP_IN_PA) {
    xlsx.addTitle(sheet2, rowIndex=20, 
                  title="Transit Trips by Production/Attraction District, Primary Transit Mode and Access Mode",
                  titleStyle = TITLE_STYLE)
} else {
    xlsx.addTitle(sheet2, rowIndex=20, 
                  title="Transit Trips by Origin/Destination District, Primary Transit Mode and Access Mode",
                  titleStyle = TITLE_STYLE)
}

summ4.colVar = list(
    '1'=csOtherColumn,
    '2'=csOtherColumn,
    '3'=csOtherColumn)
summ4.colNum =list(
    '4'=csNumColumn,
    '5'=csNumColumn,
    '6'=csNumColumn,
    '7'=csNumColumn)

addDataFrame(summ4, sheet2, startRow=22, startColumn=1,
             colStyle=c(summ4.colVar, summ4.colNum),
             colnamesStyle = TABLE_COLNAMES_STYLE,
             rownamesStyle = TABLE_ROWNAMES_STYLE,
             row.names = FALSE)

setColumnWidth(sheet2, colIndex=c(1:2), colWidth=13)
setColumnWidth(sheet2, colIndex=c(3:ncol(summ4)), colWidth=12)

createFreezePane(sheet2, 23, 1, 23, 1)

border <- Border(color="black", position=c("TOP", "BOTTOM"),
                 pen=c("BORDER_THIN", "BORDER_THICK"))

cb <- CellBlock(sheet2, 10, 1, 1, 2, create = FALSE)
CB.setBorder(cb, border, 1, 1:2)

cb <- CellBlock(sheet2, 18, 1, 1, 2, create = FALSE)
CB.setBorder(cb, border, 1, 1:2)


# ------------- Sheet 3 ----------------

sheet3 <- createSheet(wb, sheetName = "by Mode, Access Mode & Distance")

row1 <- createRow(sheet3, rowIndex=1)

tourTitleCell <- createCell(row1, colIndex=1)[[1,1]]
tripTitleCell <- createCell(row1, colIndex=8)[[1,1]]

setCellValue(tourTitleCell, "Transit Tours by Access Distance, Primary Mode and Access Mode")
setCellValue(tripTitleCell, "Transit Trips by Access Distance, Primary Mode and Access Mode")

setCellStyle(tourTitleCell, TITLE_STYLE)
setCellStyle(tripTitleCell, TITLE_STYLE)


summ5.colVar = list(
    '1'=csOtherColumn,
    '2'=csOtherColumn,
    '3'=csOtherColumn,
    '4'=csOtherColumn)
summ5.colNum =list('5'=csNumColumn)

addDataFrame(summ5, sheet3, startRow=3, startColumn=1,
             colStyle=c(summ5.colVar, summ5.colNum),
             colnamesStyle = TABLE_COLNAMES_STYLE,
             rownamesStyle = TABLE_ROWNAMES_STYLE,
             row.names = FALSE)


setColumnWidth(sheet3, colIndex=c(1:4), colWidth=16)
setColumnWidth(sheet3, colIndex=c(5:ncol(summ5)), colWidth=12)


# add trip table in this sheet too
summ6.colVar = list(
    '1'=csOtherColumn,
    '2'=csOtherColumn,
    '3'=csOtherColumn)
summ6.colNum =list('4'=csNumColumn)

addDataFrame(summ6, sheet3, startRow=3, startColumn=8,
             colStyle=c(summ6.colVar, summ6.colNum),
             colnamesStyle = TABLE_COLNAMES_STYLE,
             rownamesStyle = TABLE_ROWNAMES_STYLE,
             row.names = FALSE)

setColumnWidth(sheet3, colIndex=c(8:10), colWidth=16)
setColumnWidth(sheet3, colIndex=c(11), colWidth=12)

createFreezePane(sheet3, 4, 1, 4, 1)


# ---------------------------- Sheet 4 ----------------------------

sheet4 <- createSheet(wb, sheetName = "by Mode, Access Mode & Transfers")

sheet4row1 <- createRow(sheet4, rowIndex=1)

tourTitleCell <- createCell(sheet4row1, colIndex=1)[[1,1]]
tripTitleCell <- createCell(sheet4row1, colIndex=11)[[1,1]]

setCellValue(tourTitleCell, "Transit Tours by Primary Mode, Access Mode and Number of Transfers")
setCellValue(tripTitleCell, "Transit Trips by Primary Mode, Access Mode and Number of Transfers")

setCellStyle(tourTitleCell, TITLE_STYLE)
setCellStyle(tripTitleCell, TITLE_STYLE)


summ7.colVar = list(
    '1'=csOtherColumn,
    '2'=csOtherColumn,
    '3'=csOtherColumn,
    '4'=csOtherColumn)
summ7.colNum =list(
    '5'=csNumColumn,
    '6'=csNumColumn,
    '7'=csNumColumn,
    '8'=csNumColumn)

addDataFrame(summ7, sheet4, startRow=3, startColumn=1,
             colStyle=c(summ7.colVar, summ7.colNum),
             colnamesStyle = TABLE_COLNAMES_STYLE,
             rownamesStyle = TABLE_ROWNAMES_STYLE,
             row.names = FALSE)


setColumnWidth(sheet4, colIndex=c(1:4), colWidth=16)
setColumnWidth(sheet4, colIndex=c(5:ncol(summ7)), colWidth=12)


# add trip table in this sheet too
summ8.colVar = list(
    '1'=csOtherColumn,
    '2'=csOtherColumn)
summ8.colNum =list(
    '3'=csNumColumn,
    '4'=csNumColumn,
    '5'=csNumColumn,
    '6'=csNumColumn)

addDataFrame(summ8, sheet4, startRow=3, startColumn=11,
             colStyle=c(summ8.colVar, summ8.colNum),
             colnamesStyle = TABLE_COLNAMES_STYLE,
             rownamesStyle = TABLE_ROWNAMES_STYLE,
             row.names = FALSE)

setColumnWidth(sheet4, colIndex=c(11:12), colWidth=16)
setColumnWidth(sheet4, colIndex=c(13:(12+ncol(summ8))), colWidth=12)

createFreezePane(sheet4, 4, 1, 4, 1)


# ---------------------------- Sheet 5 ----------------------------

sheet5 <- createSheet(wb, sheetName = "Tour Trip Mode Comparison")

xlsx.addTitle(sheet5, rowIndex=1, 
              title="Transit Tours by Tour and Trip Mode",
              titleStyle = TITLE_STYLE)

xlsx.addRowColDesc(sheet5, 4, 3, nrow(summ9), ncol(summ9), 
                   GRAY_BACKGROUND, 
                   "Tour Mode = Transit", 
                   "Trip Mode = Transit")

summ9.colVar = list(
    '1'=csOtherColumn)
summ9.colNum =list(
    '2'=csNumColumn,
    '3'=csNumColumn,
    '4'=csNumColumn,
    '5'=csNumColumn,
    '6'=csNumColumn)

addDataFrame(summ9, sheet5, startRow=4, startColumn=3,
             colStyle=c(summ9.colVar, summ9.colNum),
             colnamesStyle = TABLE_COLNAMES_STYLE,
             rownamesStyle = TABLE_ROWNAMES_STYLE,
             row.names = FALSE)

emptyCells <- CellBlock(sheet5, 3, 2, 2, 2, create = TRUE)

summ9Cells <- CellBlock(sheet5, 3, 2, 2+nrow(summ9), 1+ncol(summ9), create = FALSE)

xlsx.addBorderFrame(summ9Cells, 1, 1, 2+nrow(summ9), 1+ncol(summ9), "BORDER_THIN")
xlsx.addBorderFrame(summ9Cells, 1, 1, 2, 2, "BORDER_THIN")
xlsx.addBorderFrame(summ9Cells, 3, 3, 2+nrow(summ9), 1+ncol(summ9), "BORDER_THIN")


xlsx.addRowColDesc(sheet5, 12, 3, nrow(summ9_pct), ncol(summ9_pct), 
                   LIGHTBLUE_BACKGROUND, 
                   "Tour Mode = Transit", 
                   "Trip Mode = Transit")

summ9_pct.colPct =list(
    '2'=csPctColumn,
    '3'=csPctColumn,
    '4'=csPctColumn,
    '5'=csPctColumn)

addDataFrame(summ9_pct, sheet5, startRow=12, startColumn=3,
             colStyle=c(summ9.colVar, summ9_pct.colPct),
             colnamesStyle = TABLE_COLNAMES_STYLE,
             rownamesStyle = TABLE_ROWNAMES_STYLE,
             row.names = FALSE)

B10 <- CellBlock(sheet5, 10, 2, 1, 1, create = TRUE)
CB.setColData(B10, "Row Percentage", 1)

emptyCells <- CellBlock(sheet5, 11, 2, 2, 2, create = TRUE)

summ9_pctCells <- CellBlock(sheet5, 11, 2, 2+nrow(summ9_pct), 1+ncol(summ9_pct), create = FALSE)

xlsx.addBorderFrame(summ9_pctCells, 1, 1, 2+nrow(summ9_pct), 1+ncol(summ9_pct), "BORDER_THIN")
xlsx.addBorderFrame(summ9_pctCells, 1, 1, 2, 2, "BORDER_THIN")
xlsx.addBorderFrame(summ9_pctCells, 3, 3, 2+nrow(summ9_pct), 1+ncol(summ9_pct), "BORDER_THIN")


xlsx.addTitle(sheet5, rowIndex=17, 
              title="Transit Tours with Primary Mode Match Trips' ",
              titleStyle = TITLE_STYLE)

xlsx.addRowColDesc(sheet5, 20, 3, nrow(bestModeMatch), ncol(bestModeMatch), 
                   GRAY_BACKGROUND, 
                   "Tour Mode = Transit", 
                   "Trip Mode = Transit")

bmm.colNum =list(
    '2'=csNumColumn,
    '3'=csNumColumn,
    '4'=csNumColumn,
    '5'=csNumColumn)

addDataFrame(bestModeMatch, sheet5, startRow=20, startColumn=3,
             colStyle=c(summ9.colVar, bmm.colNum),
             colnamesStyle = TABLE_COLNAMES_STYLE,
             rownamesStyle = TABLE_ROWNAMES_STYLE,
             row.names = FALSE)

emptyCells <- CellBlock(sheet5, 19, 2, 2, 2, create = TRUE)

bmmCells <- CellBlock(sheet5, 19, 2, 2+nrow(bestModeMatch), 1+ncol(bestModeMatch), create = FALSE)

xlsx.addBorderFrame(bmmCells, 1, 1, 2+nrow(bestModeMatch), 1+ncol(bestModeMatch), "BORDER_THIN")
xlsx.addBorderFrame(bmmCells, 1, 1, 2, 2, "BORDER_THIN")
xlsx.addBorderFrame(bmmCells, 3, 3, 2+nrow(bestModeMatch), 1+ncol(bestModeMatch), "BORDER_THIN")


# Sheet 5 Table 4 
xlsx.addTitle(sheet5, rowIndex=25, 
              title="Transit Trips by Tour and Trip Primary Mode",
              titleStyle = TITLE_STYLE)

xlsx.addRowColDesc(sheet5, 28, 3, nrow(tripModeMatch), ncol(tripModeMatch), 
                   GRAY_BACKGROUND, 
                   "Tour Primary Mode", 
                   "Trip Primary Mode")

tmm.colVar = list(
    '1'=csOtherColumn)
tmm.colNum =list(
    '2'=csNumColumn,
    '3'=csNumColumn,
    '4'=csNumColumn,
    '5'=csNumColumn,
    '6'=csNumColumn,
    '7'=csNumColumn,
    '8'=csNumColumn)

addDataFrame(tripModeMatch, sheet5, startRow=28, startColumn=3,
             colStyle=c(tmm.colVar, tmm.colNum),
             colnamesStyle = TABLE_COLNAMES_STYLE,
             rownamesStyle = TABLE_ROWNAMES_STYLE,
             row.names = FALSE)

emptyCells <- CellBlock(sheet5, 27, 2, 2, 2, create = TRUE)

tmmCells <- CellBlock(sheet5, 27, 2, 2+nrow(tripModeMatch), 1+ncol(tripModeMatch), create = FALSE)

xlsx.addBorderFrame(tmmCells, 1, 1, 2+nrow(tripModeMatch), 1+ncol(tripModeMatch), "BORDER_THIN")
xlsx.addBorderFrame(tmmCells, 1, 1, 2, 2, "BORDER_THIN")
xlsx.addBorderFrame(tmmCells, 3, 3, 2+nrow(tripModeMatch), 1+ncol(tripModeMatch), "BORDER_THIN")


setColumnWidth(sheet5, colIndex=c(2), colWidth=18)
setColumnWidth(sheet5, colIndex=c(3), colWidth=11)
setColumnWidth(sheet5, colIndex=c(4:12), colWidth=16)

# write everything out!
saveWorkbook(wb, OUTFILE)

