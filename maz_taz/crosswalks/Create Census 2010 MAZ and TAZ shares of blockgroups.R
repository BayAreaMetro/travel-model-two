# Create Census 2010 MAZ and TAZ shares of blockgroups.R
# SI

# Notes

"

2010 decennial census household data at the block level were used to develop the share of households by block group. 
That share can then be applied to any household-level distribution for TM2 MAZ/TAZ2 data development. 
   
"
# Import Libraries

suppressMessages(library(tidyverse))
library(tidycensus)

# Set up directories, import TAZ/census block equivalence, install census key, set ACS year

censuskey            <- readLines("M:/Data/Census/API/api-key.txt")
census_api_key(censuskey, install = TRUE, overwrite = TRUE)
baycounties          <- c("01","13","41","55","75","81","85","95","97")


sf1_year <- 2010
state_code ="06"

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
  summarize(total_bg_hhs=sum(hhs)) %>% 
  ungroup() 

block_share <- bg_MAZ_TAZ %>% 
  left_join(.,bg_total,by="bg") %>% 
  mutate(sharebg=if_else(total_bg_hhs==0,0,hhs/total_bg_hhs)) %>% 
  rename(block=GEOID10,block_hhs=hhs,blockgroup=bg,taz2=taz) %>% 
  select(block,block_hhs,blockgroup,total_bg_hhs,sharebg,maz,taz2)

# Create files for maz and taz and output

maz_share_bg <- block_share %>%group_by(blockgroup,maz) %>% summarize(maz_share=sum(sharebg)) 
taz_share_bg <- block_share %>%group_by(blockgroup,taz2) %>% summarize(taz2_share=sum(sharebg)) 

write.csv(maz_share_bg,file = "Census 2010 hhs maz share of blockgroups.csv",row.names = F)
write.csv(taz_share_bg,file = "Census 2010 hhs taz2 share of blockgroups.csv",row.names = F)

