# Dora Wu @ WSP USA Inc 11-22-2017
# script to append selected skim LOS to tour and trip files

# arguments :
# TRANSIT_ONLY, if set to 1, write out tour and trip files that only contain transit tours/trips
# LOS_SELECTION, a vector contain 16 numbers, separated by comma,
#                indicating selected LOS in the order:
#                1 "COMPCOST", 2 "IWAIT", 3 "XWAIT", 4 "XPEN", 5 "BRDPEN", 6 "XFERS", 
#                7 "FARE", 8 "XWTIME", 9 "AEWTIME", 10 "LB_TIME", 11 "EB_TIME", 12 "FR_TIME",
#                13 "LR_TIME", 14 "HR_TIME", 15 "CR_TIME", 16 "BEST_MODE" 
# example: %R_LOC%\Rscript.exe --vanilla --verbose appendLOSAttributes.R 1 0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1 > appendLOSAttributes.log
# This example adds XFERS and BEST_MODE to the end of tour and trip files, and only write out transit tours/trips
# 

args=(commandArgs(TRUE))

TRANSIT_ONLY = as.integer(args[1])
LOS_SELECTION = as.integer(strsplit(args[2], ",")[[1]]) 

list.of.packages <- c("dplyr", "devtools", "tibble", "data.table", "bit64", "pryr")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]

if(length(new.packages)) install.packages(new.packages, repos='http://cran.us.r-project.org')

library(devtools)
library(pryr)
library(data.table)
library(bit64)
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



print("Initial Memeory Usage: ")
print(mem_used())

LOS_VARS <- c("COMPCOST", 
              "IWAIT",
              "XWAIT",
              "XPEN",
              "BRDPEN",
              "XFERS",
              "FARE",
              "XWTIME",
              "AEWTIME",
              "LB_TIME",
              "EB_TIME",
              "FR_TIME",
              "LR_TIME",
              "HR_TIME",
              "CR_TIME",
              "BEST_MODE")

LOS_VARS_TOADD <- LOS_VARS[LOS_SELECTION > 0]

# ============= function to read Ctramp trip and tour files ==================

readCtrampFile <- function(dirLoc, fname, retainnames = NULL, nrows = -1, sampleRate = 1, vSampleRate = 1) {
  
  if (fname == 'itrip') {
    cnames <- c('hh_id', 'person_id', 'person_num', 'tour_id', 'stop_id', 'inbound', 'tour_purpose',
                'orig_purpose', 'dest_purpose', 'orig_mgra', 'dest_mgra', 'trip_dist', 'parking_mgra',
                'stop_period', 'trip_mode', 'trip_board_tap', 'trip_alight_tap', 'tour_mode', 'set', 
                'TRIP_TIME', 'TRIP_DISTANCE', 'TRIP_COST', 'FULL_MODE')
    if(is.null(retainnames)) retainnames <- cnames
    cclasses <- rep('NULL', length(cnames))
    tempclasses <- c('integer', 'integer', 'integer', 'integer', 'integer', 'integer', 'character',
                     'character', 'character', 'integer', 'integer', 'numeric', 'integer', 'integer',
                     'integer', 'integer', 'integer', 'integer',
                     'integer', 'numeric', 'numeric', 'numeric', 'integer')
    cclasses[match(retainnames, cnames)] <- tempclasses[match(retainnames, cnames)]
    temp_itp <- fread(paste0(dirLoc, '\\indivTripData_1.csv'), colClasses = cclasses, nrows = nrows)
    temp_itp[, tripWeight := 1/sampleRate]
    return(temp_itp)
  }
  
  if (fname == 'jtrip') {
    cnames <- c('hh_id', 'tour_id', 'stop_id', 'inbound', 'tour_purpose', 'orig_purpose', 'dest_purpose',
                'orig_mgra', 'dest_mgra', 'trip_dist', 'parking_mgra', 'stop_period', 'trip_mode',
                'num_participants', 'trip_board_tap', 'trip_alight_tap', 'tour_mode', 'set', 'TRIP_TIME',
                'TRIP_DISTANCE', 'TRIP_COST', 'FULL_MODE')
    if(is.null(retainnames)) retainnames <- cnames
    cclasses <- rep('NULL', length(cnames))
    tempclasses <- c('integer', 'integer', 'integer', 'integer', 'character', 'character', 'character',
                     'integer', 'integer', 'numeric', 'integer', 'integer', 'integer', 'integer', 'integer',
                     'integer', 'integer', 'integer', 'numeric', 'numeric', 'numeric', 'integer')
    cclasses[match(retainnames, cnames)] <- tempclasses[match(retainnames, cnames)]
    temp_jtp <- fread(paste0(dirLoc, '\\jointTripData_1.csv'), colClasses = cclasses, nrows = nrows)
    temp_jtp[, tripWeight := 1/sampleRate]
    return(temp_jtp)
  }
  
  if (fname == 'itour') {
    cnames <- c('hh_id', 'person_id', 'person_num', 'person_type', 'tour_id', 'tour_category',
                'tour_purpose', 'orig_mgra', 'dest_mgra', 'start_period', 'end_period', 'tour_mode',
                'tour_distance', 'tour_time', 'atWork_freq', 'num_ob_stops', 'num_ib_stops', 'out_btap',
                'out_atap', 'in_btap', 'in_atap', 'out_set', 'in_set')
    cnames <- c(cnames, paste0('util_', 1:14), paste0('prob_', 1:14))
    if(is.null(retainnames)) retainnames <- cnames
    cclasses <- rep('NULL', length(cnames))
    tempclasses <- c('integer', 'integer', 'integer', 'integer', 'integer', 'character', 'character',
                     'integer', 'integer', 'integer', 'integer', 'integer', 'numeric', 'numeric', 'integer',
                     'integer', 'integer', 'integer', 'integer', 'integer', 'integer', 'integer', 'integer')
    tempclasses <- c(tempclasses, rep('numeric, 28'))
    cclasses[match(retainnames, cnames)] <- tempclasses[match(retainnames, cnames)]
    temp_itr <- fread(paste0(dirLoc, '\\indivTourData_1.csv'), colClasses = cclasses,nrows = nrows)
    temp_itr[, tourWeight := 1/sampleRate]
    return(temp_itr)
  }   
  
  if (fname == 'jtour') {
    cnames <- c('hh_id', 'tour_id', 'tour_category', 'tour_purpose', 'tour_composition', 'tour_participants',
                'orig_mgra', 'dest_mgra', 'start_period', 'end_period', 'tour_mode', 'tour_distance', 'tour_time',
                'num_ob_stops', 'num_ib_stops', 'out_btap', 'out_atap', 'in_btap', 'in_atap', 'out_set', 'in_set')
    cnames <- c(cnames, paste0('util_', 1:14), paste0('prob_', 1:14))
    if(is.null(retainnames)) retainnames <- cnames
    cclasses <- rep('NULL', length(cnames))
    tempclasses <- c('integer', 'integer', 'character', 'character', 'integer', 'character', 'integer',
                     'integer', 'integer', 'integer', 'integer', 'numeric', 'numeric', 'integer', 'integer',
                     'integer', 'integer', 'integer', 'integer', 'integer', 'integer')
    tempclasses <- c(tempclasses, rep('numeric, 28'))
    cclasses[match(retainnames, cnames)] <- tempclasses[match(retainnames, cnames)]
    temp_jtr <- fread(paste0(dirLoc, '\\jointTourData_1.csv'), colClasses = cclasses,nrows = nrows)
    temp_jtr[, tourWeight := 1/sampleRate]
    return(temp_jtr)
  }  
  
}

  
# ===================== Convert Cube Skims to OMX ============================

# need to set up path for cube2omx.exe, now assume in working directory


print(paste0("Start: ", as.character(Sys.time())))

for (tod in c("AM", "MD", "PM", "EV", "EA")){
    for (i in 1:3){
        filename <- paste0("skims\\transit_skims_", tod, "_SET", as.character(i), ".TPP")
        omxname <- paste0("skims\\transit_skims_", tod, "_SET", as.character(i), ".omx")
        if (!file.exists(omxname)) {
            cmmd <- paste0("cube2omx.exe ", filename)
            print(cmmd)
            system(cmmd)
        }  
    }
}


print(paste0("OMX conversion all done: ", as.character(Sys.time())))



# read in LOS from skims


skimFileList <- c("transit_skims_AM_SET1.omx", "transit_skims_AM_SET2.omx", "transit_skims_AM_SET3.omx",
                  "transit_skims_MD_SET1.omx", "transit_skims_MD_SET2.omx", "transit_skims_MD_SET3.omx",
                  "transit_skims_PM_SET1.omx", "transit_skims_PM_SET2.omx", "transit_skims_PM_SET3.omx",
                  "transit_skims_EV_SET1.omx", "transit_skims_EV_SET2.omx", "transit_skims_EV_SET3.omx",
                  "transit_skims_EA_SET1.omx", "transit_skims_EA_SET2.omx", "transit_skims_EA_SET3.omx")


skimFiles <- paste0("skims\\", skimFileList)


# read in tour files
itour <- readCtrampFile("ctramp_output", 'itour', sampleRate = 0.1)
jtour <- readCtrampFile("ctramp_output", 'jtour', sampleRate = 0.1)

NCOL_ITOUR <- ncol(itour)
NCOL_JTOUR <- ncol(jtour)

# read in trip files
itrip <- readCtrampFile("ctramp_output", 'itrip', sampleRate = 0.1)
jtrip <- readCtrampFile("ctramp_output", 'jtrip', sampleRate = 0.1)

NCOL_ITRIP <- ncol(itrip)
NCOL_JTRIP <- ncol(jtrip)


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




# get transit only tour
itransTour <- subset(itour, tour_mode >= 11 & tour_mode <= 13)
jtransTour <- subset(jtour, tour_mode >= 11 & tour_mode <= 13)
itransTrip <- subset(itrip, trip_mode >= 11 & trip_mode <= 13)
jtransTrip <- subset(jtrip, trip_mode >= 11 & trip_mode <= 13)


# add time period numbers to tour and trip datasets
itransTour$start_tod <- AddTODNum(itransTour$start_period)
itransTour$end_tod <- AddTODNum(itransTour$end_period)

itransTour[, nmatrixOut := (start_tod - 1) * 3 + out_set + 1]
itransTour[, nmatrixIn := (end_tod - 1) * 3 + in_set + 1]

itransTrip$stop_tod <- AddTODNum(itransTrip$stop_period)
itransTrip[, nmatrix := (stop_tod - 1) * 3 + set + 1]


if (nrow(jtransTour)) {
    
    jtransTour$start_tod <- AddTODNum(jtransTour$start_period)
    jtransTour$end_tod <- AddTODNum(jtransTour$end_period)
    
    jtransTour[, nmatrixOut := (start_tod - 1) * 3 + out_set + 1]
    jtransTour[, nmatrixIn := (end_tod - 1) * 3 + in_set + 1]
    
    
}




if (nrow(jtransTrip)) {
    
    jtransTrip$stop_tod <- AddTODNum(jtransTrip$stop_period)
    jtransTrip[, nmatrix := (stop_tod - 1) * 3 + set + 1]
    
}

print("Memory usage before reading skims: ")
print(mem_used())
print(paste0("Time: ", as.character(Sys.time())))


for (los_var in LOS_VARS_TOADD){

    print(paste0("Reading in ", los_var, " skims..."))
    allmatrix <- lapply(1:length(skimFiles), function(ii) read_omx(skimFiles[ii], los_var))
    
    print(paste0("Memory usage after reading ", los_var, " skims: "))
    print(mem_used())
    
    
    itransTour <- itransTour  %>%  rowwise() %>% 
        mutate(newvar = allmatrix[[nmatrixOut]][out_btap, out_atap],
               newvar2 = allmatrix[[nmatrixIn]][in_btap, in_atap]) 
    
    
    names(itransTour)[ncol(itransTour) - 1] <- paste0(los_var, "_OUT")
    names(itransTour)[ncol(itransTour)] <- paste0(los_var, "_IN")
    
    
    itransTrip <- itransTrip  %>%  rowwise() %>% 
        mutate(newvar = allmatrix[[nmatrix]][trip_board_tap, trip_alight_tap]) 
    names(itransTrip)[ncol(itransTrip)] <- los_var
     
    
    if(nrow(jtransTour)){
        
        jtransTour <- jtransTour  %>%  rowwise() %>% 
            mutate(newvar = allmatrix[[nmatrixOut]][out_btap, out_atap],
                   newvar2 = allmatrix[[nmatrixIn]][in_btap, out_atap]
                   ) 
        names(jtransTour)[ncol(jtransTour) - 1] <- paste0(los_var, "_OUT")
        names(jtransTour)[ncol(jtransTour)] <- paste0(los_var, "IN")
  
    }
    
    if(nrow(jtransTrip)) {
        
        jtransTrip <- jtransTrip  %>%  rowwise() %>% 
            mutate(newvar = allmatrix[[nmatrix]][trip_board_tap, trip_alight_tap]) 
        names(jtransTrip)[ncol(jtransTrip)] <- los_var
        
    }
    
    rm(allmatrix)
    print(paste0("Memory usage after removing ", los_var, " Skims: "))
    print(mem_used())
}


print(paste0("Appending selected LOS attributes done: ", as.character(Sys.time())))


if (TRANSIT_ONLY) {
    
    itransTour <- itransTour %>% 
        select(-start_tod, -end_tod, -nmatrixOut, -nmatrixIn)
    write.csv(itransTour, "individual_transitTour_wLOS.csv", row.names = FALSE)
    
    itransTrip <- itransTrip %>% select(-stop_tod, -nmatrix)
    write.csv(itransTrip, "individual_transitTrip_wLOS.csv", row.names = FALSE)
    
    if(nrow(jtransTour)){
        jtransTour <- jtransTour %>% 
            select(-start_tod, -end_tod, -nmatrixOut, -nmatrixIn)
        write.csv(jtransTour, "joint_transitTour_wLOS.csv", row.names = FALSE)
    }
    if(nrow(jtransTrip)){
        jtransTrip <- jtransTrip %>% select(-stop_tod, -nmatrix)
        write.csv(jtransTrip, "joint_transitTrip_wLOS.csv", row.names = FALSE)
    }
    
    
} else {
    
    tourCategoryMap <- data.frame(tourCatNum = 0:9,
                                  tourCategory = c("Work", 
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
    
    selectcol_itr <- itransTour %>% 
        mutate(tourCatNum = tourCategoryMap$tourCatNum[match(tour_purpose, tourCategoryMap$tourCategory)]) %>% 
        mutate(id = person_id * 1000 + tourCatNum * 100 + tour_id) %>%
        select((NCOL_ITOUR + 5):(ncol(itransTour) + 2)) 
    
    itour <- itour %>%
        mutate(tourCatNum = tourCategoryMap$tourCatNum[match(tour_purpose, tourCategoryMap$tourCategory)]) %>% 
        mutate(id = person_id * 1000 + tourCatNum * 100 + tour_id) %>%
        select(-tourCatNum) %>% 
        left_join(selectcol_itr, by = "id" ) %>%
        select(-id, -tourCatNum)
        
    write.csv(itour, "individual_allTour_wLOS.csv", row.names = FALSE)
    
    
    selectcol_itp <- itransTrip %>% 
        mutate(tourCatNum = tourCategoryMap$tourCatNum[match(tour_purpose, tourCategoryMap$tourCategory)]) %>% 
        mutate(id = person_id * 100000 + tourCatNum * 10000 + tour_id * 100 + inbound * 10 + stop_id + 1) %>%
        select((NCOL_ITRIP + 3):(ncol(itransTrip) + 2))
    
    itrip <- itrip %>% 
        mutate(tourCatNum = tourCategoryMap$tourCatNum[match(tour_purpose, tourCategoryMap$tourCategory)]) %>%
        mutate(id = person_id * 100000 + tourCatNum * 10000 + tour_id * 100 + inbound * 10 + stop_id + 1) %>%
        select(-tourCatNum) %>% 
        left_join(selectcol_itp, by = "id" ) %>%
        select(-id, -tourCatNum)
    
    write.csv(itrip, "individual_allTrip_wLOS.csv", row.names = FALSE)
    
    if (nrow(jtransTour)) {
        
        selectcol_jtr <- jtransTour %>% 
            mutate(tourCatNum = tourCategoryMap$tourCatNum[match(tour_purpose, tourCategoryMap$tourCategory)]) %>% 
            mutate(id = hh_id * 1000 + tourCatNum * 100 + tour_id)  %>%
            select((NCOL_JTOUR + 5):(ncol(jtransTour) + 2))
        
        jtour <- jtour %>% 
            mutate(tourCatNum = tourCategoryMap$tourCatNum[match(tour_purpose, tourCategoryMap$tourCategory)]) %>% 
            mutate(id = hh_id * 1000 + tourCatNum * 100 + tour_id)  %>%
            select(-tourCatNum) %>%
            left_join(selectcol_jtr, by = "id" ) %>%
            select(-id, -tourCatNum)
        
        write.csv(itour, "joint_allTour_wLOS.csv", row.names = FALSE)
        
    }
    
    if (nrow(jtransTrip)) {
        
        selectcol_jtp <- jtransTrip %>% 
            mutate(tourCatNum = tourCategoryMap$tourCatNum[match(tour_purpose, tourCategoryMap$tourCategory)]) %>% 
            mutate(id = hh_id * 100000 + tourCatNum * 10000 + tour_id * 100 + inbound * 10 + stop_id + 1) %>%
            select((NCOL_JTRIP + 3):(ncol(jtransTrip) + 2))
        
        jtrip <- jtrip %>% 
            mutate(tourCatNum = tourCategoryMap$tourCatNum[match(tour_purpose, tourCategoryMap$tourCategory)]) %>%
            mutate(id = hh_id * 100000 + tourCatNum * 10000 + tour_id * 100 + inbound * 10 + stop_id + 1) %>%
            select(-tourCatNum) %>%
            left_join(selectcol_jtp, by = "id" ) %>%
            select(-id, -tourCatNum)
        
        write.csv(jtrip, "joint_allTrip_wLOS.csv", row.names = FALSE)
    }
}

print(paste0("All done! ", as.character(Sys.time())))