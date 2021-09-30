# Create Census 2010 MAZ and TAZ shares of blockgroups.R
# ACS input data year should be set using the last year of a five year range using the ACS_eval_year variable
# e.g., for 2013-2017 - Sys.setenv(ACS_eval_year="2017")

# Notes

"

2010 decennial census household data at the block level were used to develop the share of households by block group. 
That share can then be applied to any household-level distribution for TM2 MAZ/TAZ2 data development. 

This script checks ACS year blockgroups against 2010 blockgroups to see if any of the ACS block groups have 
households where Census 2010 was zero. This is important to ensure full apportionment of ACS data. In cases 
that ACS block groups are >0 while Census 2010 values were zero, a straight apportionment to blocks is done
by the number of blocks in that block group. 
   
"

# Import Libraries
# Remove scientific notation

suppressMessages(library(tidyverse))
library(tidycensus)
library(logger)
options(scipen=999) 

# Set up directories, import TAZ/census block equivalence, install census key, set ACS year

censuskey            <- readLines("M:/Data/Census/API/api-key.txt")
census_api_key(censuskey, install = TRUE, overwrite = TRUE)
baycounties          <- c("01","13","41","55","75","81","85","95","97")

ACS_year            <- as.numeric(Sys.getenv("ACS_eval_year"))
sf1_year <- 2010
state_code ="06"

# Set up logger

logfile <- (paste0("ACS_",Sys.getenv("ACS_eval_year"),"_MAZ_TAZ_Crosswalk.log"))

if (file.exists(logfile)) {
  #Delete file if it exists
  file.remove(logfile)
}

log_appender(appender_tee(logfile))
log_info('Bringing in relevant files.')

# Set input path locations and working directory

USERPROFILE          <- gsub("\\\\","/", Sys.getenv("USERPROFILE"))
block_MAZ_TAZ_in     <- file.path(USERPROFILE,"Documents","GitHub","travel-model-two","maz_taz","blocks_mazs_tazs_v2.2.csv")

wd <- file.path(USERPROFILE,"Documents","GitHub","travel-model-two","maz_taz","crosswalks")
setwd(wd)

# Make decennial census calls, configure file for later joining

totalhhs <- "H016001"           # 2010 variable for decennial total households

sf1_block_hhs <- get_decennial(geography = "block", variables = totalhhs,
                               state = state_code, county=baycounties,
                               year=2010,
                               output="wide",
                               key=censuskey) %>% 
  rename(GEOID10 = GEOID,hhs=H016001) %>% 
  mutate(GEOID10 = as.numeric(GEOID10)) %>% 
  select(-NAME)

# Bring in block to MAZ/TAZ equivalence and join with census HH file

block_MAZ_TAZ    <- read.csv(block_MAZ_TAZ_in,header = T) %>% 
  left_join(.,sf1_block_hhs,by="GEOID10")

# Generate block group ID from block strings (note that leading zero for state FIPS falls off in numeric conversion)
# Summarize household total by block group 
# Calculate block share of total block group hhs 
# The calculated shares will be used to apportion block group households to MAZs and TAZs
# Watch for divide-by-zero error when calculating shares in if/else statement
# Rename and order variables

bg_MAZ_TAZ    <- block_MAZ_TAZ %>% 
  mutate(bg=as.numeric(substr(GEOID10,1,11))) 

bg_total <- bg_MAZ_TAZ %>% 
  group_by(bg) %>% 
  summarize(total_bg_hhs_2010=sum(hhs),total_blocks=n()) %>% 
  ungroup() 

block_share <- bg_MAZ_TAZ %>% 
  left_join(.,bg_total,by="bg") %>% 
  mutate(sharebg=if_else(total_bg_hhs_2010==0,0,hhs/total_bg_hhs_2010)) %>% 
  rename(block=GEOID10,block_hhs=hhs,blockgroup=bg,taz2=taz) %>% 
  select(block,block_hhs,blockgroup,total_bg_hhs_2010,sharebg,maz,taz2)

log_info('There are {nrow(block_share)} blocks and {nrow(bg_total)} block groups.')

# Create apportionment for mazs with no households
# Start by creating a block group file with number block group ID, number of hhs in 2010 and the ACS year

acs_hhs <- get_acs(geography = "block group", variables = "B19001_001E",
                      state = state_code, county=baycounties,
                      year=ACS_year,
                      output="wide",
                      survey = "acs5",
                      key = censuskey) %>% 
  select(-B19001_001M) %>% 
  rename(bg=GEOID,total_bg_hhs_ACS=B19001_001E) %>% 
  mutate(bg=as.numeric(bg)) %>% 
  left_join(.,bg_total,by="bg") %>% 
  filter(total_bg_hhs_2010==0 & total_bg_hhs_ACS>0) %>% 
  mutate(bad_sharebg=1/total_blocks)

log_info("BG(s) with no hhs in Census 2010, yet some in ACS {ACS_year}: {acs_hhs$bg} with {acs_hhs$total_blocks} blocks")

block_share <- block_share %>%
  left_join(.,select(acs_hhs,bg,bad_sharebg),by=c("blockgroup"="bg")) %>% 
  mutate(sharebg=if_else(!is.na(bad_sharebg),bad_sharebg,sharebg)) 
  

# Create files for maz and taz and output

maz_share_bg <- block_share %>% group_by(blockgroup,maz) %>% summarize(maz_share=sum(sharebg)) 
taz_share_bg <- block_share %>% group_by(blockgroup,taz2) %>% summarize(taz2_share=sum(sharebg)) 

write.csv(maz_share_bg,file = "Census 2010 hhs maz share of blockgroups.csv",row.names = F)
write.csv(taz_share_bg,file = "Census 2010 hhs taz2 share of blockgroups.csv",row.names = F)

