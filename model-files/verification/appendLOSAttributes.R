USAGE <- "Script to append selected skim LOS to tour and trip files.
Requires cube2omx.exe to be available and in your PATH. @ MTC, there is a copy in M:\\Software

Example: Rscript.exe --vanilla --verbose appendLOSAttributes.R --transitonly 1 XFERS BEST_MODE  > appendLOSAttributes.log

This example adds XFERS and BEST_MODE to the end of tour and trip files, and only writes out transit tours/trips

Input:  ctramp_output/[indiv,joint][Trip,Tour]Data_[ITER].csv
Output: ctramp_output/[indiv,joint][Trip,Tour]Data_transitwLOS_[ITER].csv
"
USAGE_epilog <- "Initial revision by Dora Wu @ WSP USA Inc 11-22-2017"
USAGE <- gsub("\n", " ", USAGE)

list.of.packages <- c("argparse", "dplyr", "devtools", "tibble", "data.table", "bit64", "pryr")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]

if(length(new.packages)) install.packages(new.packages, repos='http://cran.us.r-project.org')

library(argparse)
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

parser <- ArgumentParser(description=USAGE, epilog=USAGE_epilog)
parser$add_argument("--transitonly",  dest="TRANSIT_ONLY", action="store_true", help="Output only transit tours and trips")
parser$add_argument("ITER",           type="integer", help="Iteration's output files to read")
parser$add_argument("--replaceomx",   dest="REPLACE_OMX", action="store_true", help="Force conversion of transit skims to OMX even if they exist already")
parser$add_argument("LOS_VARS_TOADD", help="LOS variables from skim tables", nargs="+")

args <- parser$parse_args( commandArgs(trailingOnly=TRUE) )
print(args)

print("Initial Memeory Usage: ")
print(mem_used())
  
# ===================== Convert Cube Skims to OMX ============================

print(paste0(as.character(Sys.time()), ": Start"))

for (tod in c("AM", "MD", "PM", "EV", "EA")){
    for (i in 1:3){
        filename <- file.path("skims", paste0("transit_skims_", tod, "_SET", as.character(i), ".TPP"))
        omxname  <- file.path("skims", paste0("transit_skims_", tod, "_SET", as.character(i), ".omx"))
        if (!file.exists(omxname) | (args$REPLACE_OMX)) {
            cmmd <- paste0("cube2omx.exe ", filename)
            print(cmmd)
            system(cmmd)
        }
    }
}

print(paste0(as.character(Sys.time()), ": OMX conversion all done"))


# read in LOS from skims

skimFileList <- c("transit_skims_AM_SET1.omx", "transit_skims_AM_SET2.omx", "transit_skims_AM_SET3.omx",
                  "transit_skims_MD_SET1.omx", "transit_skims_MD_SET2.omx", "transit_skims_MD_SET3.omx",
                  "transit_skims_PM_SET1.omx", "transit_skims_PM_SET2.omx", "transit_skims_PM_SET3.omx",
                  "transit_skims_EV_SET1.omx", "transit_skims_EV_SET2.omx", "transit_skims_EV_SET3.omx",
                  "transit_skims_EA_SET1.omx", "transit_skims_EA_SET2.omx", "transit_skims_EA_SET3.omx")

skimFiles <- file.path("skims", skimFileList)


# read in tour files
itour <- fread(file.path("ctramp_output", paste0("indivTourData_",args$ITER,".csv")))
jtour <- fread(file.path("ctramp_output", paste0("jointTourData_",args$ITER,".csv")))

NCOL_ITOUR <- ncol(itour)
NCOL_JTOUR <- ncol(jtour)

# read in trip files
itrip <- fread(file.path("ctramp_output", paste0("indivTripData_",args$ITER,".csv")))
jtrip <- fread(file.path("ctramp_output", paste0("jointTripData_",args$ITER,".csv")))

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
itransTour$end_tod   <- AddTODNum(itransTour$end_period)

itransTour[, nmatrixOut := (start_tod - 1) * 3 + out_set + 1]
itransTour[, nmatrixIn := (end_tod - 1) * 3 + in_set + 1]

itransTrip$stop_tod <- AddTODNum(itransTrip$stop_period)
itransTrip[, nmatrix := (stop_tod - 1) * 3 + set + 1]


if (nrow(jtransTour)) {
    
    jtransTour$start_tod <- AddTODNum(jtransTour$start_period)
    jtransTour$end_tod   <- AddTODNum(jtransTour$end_period)
    
    jtransTour[, nmatrixOut := (start_tod - 1) * 3 + out_set + 1]
    jtransTour[, nmatrixIn := (end_tod - 1) * 3 + in_set + 1]

}

if (nrow(jtransTrip)) {
    
    jtransTrip$stop_tod <- AddTODNum(jtransTrip$stop_period)
    jtransTrip[, nmatrix := (stop_tod - 1) * 3 + set + 1]
    
}

print("Memory usage before reading skims: ")
print(mem_used())

for (los_var in args$LOS_VARS_TOADD){

    print(paste0(as.character(Sys.time()), ": Reading in ", los_var, " skims..."))
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


print(paste0(as.character(Sys.time()), ": Appending selected LOS attributes done: "))


if (args$TRANSIT_ONLY) {
    
    itransTour <- itransTour %>% 
        select(-start_tod, -end_tod, -nmatrixOut, -nmatrixIn)
    write.csv(itransTour, file.path("ctramp_output", paste0("indivTourData_transitwLOS_", args$ITER, ".csv")), row.names = FALSE)
    
    itransTrip <- itransTrip %>% select(-stop_tod, -nmatrix)
    write.csv(itransTrip, file.path("ctramp_output", paste0("indivTripData_transitwLOS_", args$ITER, ".csv")), row.names = FALSE)
    
    if(nrow(jtransTour)){
        jtransTour <- jtransTour %>% 
            select(-start_tod, -end_tod, -nmatrixOut, -nmatrixIn)
        write.csv(jtransTour, file.path("ctramp_output", paste0("jointTourData_transitwLOS_", args$ITER, ".csv")), row.names = FALSE)
    }
    if(nrow(jtransTrip)){
        jtransTrip <- jtransTrip %>% select(-stop_tod, -nmatrix)
        write.csv(jtransTrip, file.path("ctramp_output", paste0("jointTripData_transitwLOS_", args$ITER, ".csv")), row.names = FALSE)
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

print(paste0(as.character(Sys.time()), ": All done!"))