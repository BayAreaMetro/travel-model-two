library(dplyr)
library(feather)
source("survey_helper.R")

## specific input/output file paths
survey_file <- "data/survey/onboard_survey030121.rds"
survey_file_samtrans <- "data/survey/SamTrans033021.RData"
zone_seq_file <- "data/model/ver9/mtc_final_network_zone_seq_ver9.csv"
bike_maz_tap_skim_file <- "data/model/ver9/bike_distance_maz_tap.txt"
ped_maz_tap_skim_file <- "data/model/ver9/ped_distance_maz_tap.txt"
maz_taz_lookup_file <- "data/model/ver9/maz_data_withDensity.csv"
tap_taz_lookup_file <- "data/model/ver9/tap_data.csv"
drive_skim_EA_file <- "data/model/ver9/DA_EA_taz_time.csv"
drive_skim_AM_file <- "data/model/ver9/DA_AM_taz_time.csv"
drive_skim_MD_file <- "data/model/ver9/DA_MD_taz_time.csv"
drive_skim_PM_file <- "data/model/ver9/DA_PM_taz_time.csv"
drive_skim_EV_file <- "data/model/ver9/DA_EV_taz_time.csv"

survey_skim_output_file <- "outputs/trn_survey_skim_db.feather"

## load required input data
# (1) lookup files - zone sequence, maz-taz correspondance, and tap-closest taz correspondance
zone_seq <- read.csv(zone_seq_file)
maz_seq <- zone_seq %>% filter(MAZSEQ > 0) %>% select(N, MAZSEQ)
tap_seq <- zone_seq %>% filter(TAPSEQ > 0) %>% select(N, TAPSEQ)
maz_taz_lookup <- read.csv(maz_taz_lookup_file) %>% select(TAZ, MAZ)
tap_taz_lookup <- read.csv(tap_taz_lookup_file,
                           col.names = c("tap", "tap_origal", "lotid", "taz", "capacity")) %>%
    select(tap, taz)


# (2) bike & ped maz-tap skim
bike_maz_tap_skim <- read.csv(bike_maz_tap_skim_file,
                              col.names = c("maz", "tap", "tap2", "cost", "feet")) %>%
    mutate(mile = round(feet/5280, 3),
           time = round(mile/12, 3)) %>%  # model assumption for bike speed: 12 mph
    select(-c(tap2, cost, feet))

ped_maz_tap_skim <- read.csv(ped_maz_tap_skim_file,
                             col.names = c("maz", "tap", "tap2", "cost", "feet")) %>%
    mutate(mile = round(feet/5280, 3),
           time = round(mile/3, 3)) %>% # model assumption for walk speed: 3 mph
    select(-c(tap2, cost, feet))


# (3) taz-taz drive skim by time period
drive_skim_EA <- read.csv(drive_skim_EA_file,
                          col.names = c("taz_o", "taz_d", "taz_o2","timeda", "distda"))
drive_skim_AM <- read.csv(drive_skim_AM_file,
                          col.names = c("taz_o", "taz_d", "taz_o2","timeda", "distda"))
drive_skim_MD <- read.csv(drive_skim_MD_file,
                          col.names = c("taz_o", "taz_d", "taz_o2","timeda", "distda"))
drive_skim_PM <- read.csv(drive_skim_PM_file,
                          col.names = c("taz_o", "taz_d", "taz_o2","timeda", "distda"))
drive_skim_EV <- read.csv(drive_skim_EV_file,
                          col.names = c("taz_o", "taz_d", "taz_o2","timeda", "distda"))


## preprocess raw on-board survey data
raw_data <- readRDS(survey_file) %>% process_rawdata(source="without_samtrans")
raw_data_samtrans <- readRDS(survey_file_samtrans) %>% process_rawdata(source="samtrans")
data <- rbind(raw_data, raw_data_samtrans)
rm(raw_data, raw_data_samtrans)


## add skim info for survey records
# access skim: origin maz -> origin tap
# trn skim: origin tap -> destination tap
# egress skim: destination tap -> destination maz
result_df <- data.frame()

for (per in c("EA", "AM", "MD", "PM", "EV")) {
    for (set in 1:3) {

        print(paste0("process ", per, " set ", set, sep=""))
        period_set_skim <- data %>%
            filter(period==per & skim_set==set) %>%
            add_tap_tap_skim(per, set) %>%
            add_access_egress_skim(per, set)

        result_df <- rbind(result_df, period_set_skim)
    }
}


## export result
write_feather(result_df, survey_skim_output_file)
