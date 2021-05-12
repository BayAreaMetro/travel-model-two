library(dplyr)


process_rawdata <- function(raw_data, source) {
    select_col <- c("unique_ID", "maz_o", "maz_d", "tap_o", "tap_d", "period", "skim_set", "access_mode", "egress_mode")
    day_part_to_period <- data.frame (day_part  = c("EARLY AM", "AM PEAK", "MIDDAY", "PM PEAK", "EVENING", "NIGHT"),
                                      period = c("EA", "AM", "MD", "PM", "EV", "EV"))

    clean <- raw_data

    # note: source can be either "samtrans" or "non-samtrans"
    if (source == "samtrans") {
        clean <- clean %>% rename(board_tap = first_board_tap,
                                  alight_tap = last_alight_tap,
                                  unique_ID = Unique_ID)
    }

    clean <- clean %>%
        # filter out incomplete records (that cannot be assigned to transit trip table)
        filter((weekpart == "WEEKDAY") & !(is.na(day_part))) %>%
        filter(!is.na(board_tap) & !is.na(alight_tap)) %>%
        filter(!is.na(access_mode) & !is.na(egress_mode)) %>%
        filter(!(access_mode %in% c("other", "missing")) & !(egress_mode %in% c("other", "missing"))) %>%
        # assign time period
        left_join(day_part_to_period, by = "day_part") %>%
        # assign transit skim set number
        mutate(skim_set = case_when((first_board_tech == "local bus" & last_alight_tech == "local bus") ~ 1,
                                   (first_board_tech != "local bus" & last_alight_tech != "local bus") ~ 2,
                                   (first_board_tech == "local bus" | last_alight_tech == "local bus") ~ 3)) %>%
        # renumber maz
        left_join(maz_seq, by=c("orig_maz"="N")) %>%
        rename(maz_o = MAZSEQ) %>%
        left_join(maz_seq, by=c("dest_maz"="N")) %>%
        rename(maz_d = MAZSEQ) %>%
        # renumber tap
        left_join(tap_seq, by=c("board_tap"="N")) %>%
        rename(tap_o = TAPSEQ) %>%
        left_join(tap_seq, by=c("alight_tap"="N")) %>%
        rename(tap_d = TAPSEQ) %>%
        # select columns needed
        select(select_col)

    return(clean)
}


get_period_set_trn_skim <- function(directory, period, skim_set) {

    skim_subset1 <- read.csv(paste0("outputs/set", skim_set, "/transit_skims_", period, "_set", skim_set, "_1.csv"),
                             col.names = c("tap_o", "tap_d", "compcost", "iwait", "xwait", "xpen", "brdpen", "xfers", "fare", "xwtime", "aewtime", "lb_time"))
    skim_subset2 <- read.csv(paste0("outputs/set", skim_set, "/transit_skims_", period, "_set", skim_set, "_2.csv"),
                             col.names = c("tap_o", "tap_d", "eb_time", "fr_time", "lr_time", "hr_time", "cr_time", "best_mode", "cwdwaita", "cwdwaitp", "cwdcostp", "excessdemand")) %>%
        select(-c(tap_o, tap_d))
    skim_subset3 <- read.csv(paste0("outputs/set", skim_set, "/transit_skims_", period, "_set", skim_set, "_3.csv"),
                             col.names = c("tap_o", "tap_d", "excessprop", "lb_dist", "eb_dist", "fr_dist", "lr_dist", "hr_dist", "cr_dist")) %>%
        select(-c(tap_o, tap_d))
    skim <- cbind(skim_subset1, skim_subset2, skim_subset3)

    return(skim)
}


add_tap_tap_skim <- function(period_set_data, period, skim_set) {

    print("start adding tap-tap skim")

    trn_skim <- get_period_set_trn_skim(period, skim_set)
    print("success: load tap-tap transit skim")

    result <- period_set_data %>% 
        left_join(trn_skim, by = c("tap_o", "tap_d"))

    # replace placeholder negative number (-999) by 0
    # note: -999 was used to replace 0 when writing out by Cube 
    #       to ensure the csv is in right format 
    result[result<0] <- 0

    return(result)
}


add_access_egress_skim <- function(period_set_data, period, skim_set) {

    print("start adding access/egress skim")
    if (period=="EA") {
        period_drive_skim <- drive_skim_EA
    }else if (period=="AM") {
        period_drive_skim <- drive_skim_AM
    }else if (period=="MD") {
        period_drive_skim <- drive_skim_MD
    }else if (period=="PM") {
        period_drive_skim <- drive_skim_PM
    }else if (period=="EV") {
        period_drive_skim <- drive_skim_EV
    }

    period_drive_skim <- period_drive_skim %>%
        select(taz_o, taz_d, mile = distda, time = timeda)
    print("success: load period taz-taz drive skim")

    result <- period_set_data %>%
        # set up skeleton for access/egress info
        mutate(access_mile_walk = 0,
               access_mile_bike = 0,
               access_mile_drive = 0,
               access_time_walk = 0,
               access_time_bike = 0,
               access_time_drive = 0,
               egress_mile_walk = 0,
               egress_mile_bike = 0,
               egress_mile_drive = 0,
               egress_time_walk = 0,
               egress_time_bike = 0,
               egress_time_drive = 0) %>%
        # add walk access/egress info
        left_join(ped_maz_tap_skim, by=c("maz_o"="maz", "tap_o"="tap")) %>%
        mutate(access_mile_walk = case_when(access_mode=="walk" ~ mile, TRUE ~ 0),
               access_time_walk = case_when(access_mode=="walk" ~ time, TRUE ~ 0)) %>% # only update rows where access by walk
        select(-c(mile, time)) %>%
        left_join(ped_maz_tap_skim, by=c("tap_d"="tap", "maz_d"="maz")) %>%
        mutate(egress_mile_walk = case_when(egress_mode=="walk" ~ mile, TRUE ~ 0),
               egress_time_walk = case_when(egress_mode=="walk" ~ time, TRUE ~ 0)) %>% # only update rows where egress by walk
        select(-c(mile, time)) %>%
        # add bike access/egress info
        left_join(bike_maz_tap_skim, by=c("maz_o"="maz", "tap_o"="tap")) %>%
        mutate(access_mile_bike = case_when(access_mode=="bike" ~ mile, TRUE ~ 0),
               access_time_bike = case_when(access_mode=="bike" ~ time, TRUE ~ 0)) %>% # only update rows where access by bike
        select(-c(mile, time)) %>%
        left_join(bike_maz_tap_skim, by=c("tap_d"="tap", "maz_d"="maz")) %>%
        mutate(egress_mile_bike = case_when(egress_mode=="bike" ~ mile, TRUE ~ 0),
               egress_time_bike = case_when(egress_mode=="bike" ~ time, TRUE ~ 0)) %>% # only update rows where egress by bike
        select(-c(mile, time)) %>%
        # find corresponding TAZ for maz_o and maz_d
        left_join(maz_taz_lookup, by=c("maz_o"="MAZ")) %>%
        rename(taz_maz_o = TAZ) %>%
        left_join(maz_taz_lookup, by=c("maz_d"="MAZ")) %>%
        rename(taz_maz_d = TAZ) %>%
        # find corresponding TAZ for tap_o and tap_d
        left_join(tap_taz_lookup, by=c("tap_o"="tap")) %>%
        rename(taz_tap_o = taz) %>%
        left_join(tap_taz_lookup, by=c("tap_d"="tap")) %>%
        rename(taz_tap_d = taz) %>%
        # add drive access/egress info based on taz-taz pairs on both ends of the trip
        left_join(period_drive_skim, by=c("taz_maz_o"="taz_o", "taz_tap_o"="taz_d")) %>%
        mutate(access_mile_drive = case_when((access_mode!="walk" & access_mode!="bike") ~ mile, TRUE ~ 0),
               access_time_drive = case_when((access_mode!="walk" & access_mode!="bike") ~ time, TRUE ~ 0)) %>%
        select(-c(mile, time)) %>%
        left_join(period_drive_skim, by=c("taz_tap_d"="taz_o", "taz_maz_d"="taz_d")) %>%
        mutate(egress_mile_drive = case_when((egress_mode!="walk" & egress_mode!="bike") ~ mile, TRUE ~ 0),
               egress_time_drive = case_when((egress_mode!="walk" & egress_mode!="bike") ~ time, TRUE ~ 0)) %>%
        select(-c(mile, time)) %>%
        # drop temporary taz columns
        select(-c(taz_maz_o, taz_maz_d, taz_tap_o, taz_tap_d)) %>%
        # combine access/egress info
        rowwise() %>%
        mutate(access_mile = sum(access_mile_walk, access_mile_bike, access_mile_drive, na.rm = TRUE),
               access_time = sum(access_time_walk, access_time_bike, access_time_drive, na.rm = TRUE),
               egress_mile = sum(egress_mile_walk, egress_mile_bike, egress_mile_drive, na.rm = TRUE),
               egress_time = sum(egress_time_walk, egress_time_bike, egress_time_drive, na.rm = TRUE))

    return(result)
}
