# ACS 2013-2017 create TAZ data for 2015.R
# Create "2015" TAZ data from ACS 2013-2017 
# SI
# Updated 4/24/20 with new employment data

# Notes

# The working directory is set as the location of the script. All other paths in Petrale will be relative.

wd <- paste0(dirname(rstudioapi::getActiveDocumentContext()$path),"/")
setwd(wd)

"

1. ACS data here is downloaded for the 2013-2017 5-year dataset. The end year can be updated 
   by changing the *ACS_year* variable. 

2. ACS block group variables used in all instances where not suppressed. If suppressed at the block group 
   level, tract-level data used instead. Suppressed variables may change if ACS_year is changed. This 
   should be checked, as this change could cause the script not to work.

3. Group quarters data start with the decennial census data. There are some small TAZ-specific 
   additions from university growth that are incorporated in the script, and then TAZs are scaled up to match 
   ACS 2013-2017 county-level totals. 
   
"
# Import Libraries

suppressMessages(library(tidyverse))
library(tidycensus)

# Set up directories, import TAZ/census block equivalence, install census key, set ACS year,set CPI inflation


censuskey            <- readLines("M:/Data/Census/API/api-key.txt")
baycounties          <- c("01","13","41","55","75","81","85","95","97")
census_api_key(censuskey, install = TRUE, overwrite = TRUE)

ACS_year <- 2017
sf1_year <- 2010
ACS_product="5"
state="06"
CPI_current <- 274.92  # CPI value for 2017
CPI_reference <- 180.20 # CPI value for 2000
CPI_ratio <- CPI_current/CPI_reference # 2017 CPI/2000 CPI

USERPROFILE          <- gsub("\\\\","/", Sys.getenv("USERPROFILE"))
block_MAZ_TAZ_in     <- file.path(USERPROFILE,"Documents","GitHub","travel-model-two","maz_taz","blocks_mazs_tazs_v2.2.csv")
#BOX_TM               <- file.path(USERPROFILE, "Box", "Modeling and Surveys")
#PBA_TAZ_2010         <- file.path(BOX_TM, "Share Data",   "plan-bay-area-2040", "2010_06_003","tazData.csv")

# Make decennial census calls, configure file for later joining

totalhhs <- "H016001"           # 2010 variable for decennial total households

sf1_block_hhs <- get_decennial(geography = "block", variables = totalhhs,
                               state = "06", county=baycounties,
                               year=2010,
                               output="wide",
                               key=censuskey) %>% 
  rename(GEOID10 = GEOID,hhs=H016001) %>% 
  mutate(GEOID10 = as.numeric(GEOID10)) %>% 
  select(-NAME)

# Bring in block to MAZ/TAZ equivalence and join with census HH file

block_MAZ_TAZ    <- read.csv(block_MAZ_TAZ_in,header = T) %>% 
  left_join(.,sf1_block_hhs,by="GEOID10")

# Summarize by MAZ and create file with block group share of MAZ

bg_MAZ    <- block_MAZ_TAZ %>% 
  mutate(bg=as.numeric(substr(GEOID10,1,11))) %>% 
  select(-taz)

bg_total <- bg_MAZ %>% 
  group_by(bg) %>% 
  summarize(total_bg_hhs=sum(hhs)) %>% 
  ungroup() %>% 
  select(bg,total_bg_hhs)

combo_total <- bg_MAZ %>% 
  group_by(maz,bg) %>% 
  summarize(total_combo_hhs=sum(hhs)) %>% 
  ungroup() %>% 
  left_join(.,bg_total,by="bg") %>% 
  mutate(sharebg=if_else(total_bg_hhs==0,0,total_combo_hhs/total_bg_hhs))
              
# Household income variables

hh_income_vars <-   c("B19001_002E",   # Household income 0 to $10k 
                           "B19001_003E",		# Household income $10 to $15k
                           "B19001_004E",		# Household income $15 to $20k
                           "B19001_005E",		# Household income $20 to $25k
                           "B19001_006E",		# Household income $25 to $30k
                           "B19001_007E",		# Household income $30 to $35k
                           "B19001_008E",		# Household income $35 to $40k
                           "B19001_009E",		# Household income $40 to $45k
                           "B19001_010E",		# Household income $45 to $50k
                           "B19001_011E",		# Household income 50 to $60k
                           "B19001_012E",		# Household income 60 to $75k
                           "B19001_013E",		# Household income 75 to $100k
                           "B19001_014E",		# Household income $100 to $1$25k
                           "B19001_015E",		# Household income $1$25 to $150k
                           "B19001_016E",		# Household income $150 to $200k
                           "B19001_017E")		# Household income $200k+
  
  paste0("B19001_002E,",   # Household income 0 to $10k 
                    "B19001_003E,",		# Household income $10 to $15k
                    "B19001_004E,",		# Household income $15 to $20k
                    "B19001_005E,",		# Household income $20 to $25k
                    "B19001_006E,",		# Household income $25 to $30k
                    "B19001_007E,",		# Household income $30 to $35k
                    "B19001_008E,",		# Household income $35 to $40k
                    "B19001_009E,",		# Household income $40 to $45k
                    "B19001_010E,",		# Household income $45 to $50k
                    "B19001_011E,",		# Household income 50 to $60k
                    "B19001_012E,",		# Household income 60 to $75k
                    "B19001_013E,",		# Household income 75 to $100k
                    "B19001_014E,",		# Household income $100 to $1$25k
                    "B19001_015E,",		# Household income $1$25 to $150k
                    "B19001_016E,",		# Household income $150 to $200k
                    "B19001_017E")		# Household income $200k+
                    
acs_income <- get_acs(geography = "block group", variables = hh_income_vars,
          state = "06", county=baycounties,
          year=ACS_year,
          output="wide",
          survey = "acs5",
          key = censuskey) %>% 
  select(GEOID,NAME,hhinc0_10E = B19001_002E,    # Income categories 
                    hhinc10_15E = B19001_003E,
                    hhinc15_20E = B19001_004E,
                    hhinc20_25E = B19001_005E,
                    hhinc25_30E = B19001_006E,
                    hhinc30_35E = B19001_007E,
                    hhinc35_40E = B19001_008E,
                    hhinc40_45E = B19001_009E,
                    hhinc45_50E = B19001_010E,
                    hhinc50_60E = B19001_011E,
                    hhinc60_75E = B19001_012E,
                    hhinc75_100E = B19001_013E,
                    hhinc100_125E = B19001_014E,
                    hhinc125_150E = B19001_015E,
                    hhinc150_200E = B19001_016E,
                    hhinc200pE = B19001_017E) %>% 
  mutate(bg=as.numeric(GEOID))

# Income table - Guidelines for HH income values used from ACS
"

    2000 income breaks 2017 CPI equivalent   Nearest 2017 ACS breakpoint
    ------------------ -------------------   ---------------------------
    $30,000            $45,769               $45,000
    $60,000            $91,538               $91,538* 
    $100,000           $152,564              $150,000
    ------------------ -------------------   ---------------------------

    * Because the 2017$ equivalent of $60,000 in 2000$ ($91,538) doesn't closely align with 2017 ACS income 
      categories, households within the $75,000-$99,999 category will be apportioned above and below $91,538. 
      Using the ACS 2013-2017 PUMS data, the share of households above $91,538 within the $75,000-$99,999 
      category is 0.3042492.That is, approximately 30 percent of HHs in the $75,000-$99,999 category will be 
      apportioned above this value (Q3) and 70 percent below it (Q2). The table below compares 2000$ and 2017$.

Household Income Category Equivalency, 2000$ and 2017$

          Year      Lower Bound     Upper Bound
          ----      ------------    -----------
HHINCQ1   2000      $-inf           $29,999
          2017      $-inf           $44,999
HHINCQ2   2000      $30,000         $59,999
          2017      $45,000         $91,537
HHINCQ3   2000      $60,000         $99,999
          2017      $91,538         $149,999
HHINCQ4   2000      $100,000        $inf
          2017      $150,000        $inf
          ----      -------------   -----------

"

shareabove91538 <- 0.3113032 # Use this value to later divvy up HHs in the 30-60k and 60-100k respective quartiles.


# Join 2013-2017 ACS block group and tract variables to combined_block file
# Combine and collapse ACS categories to get land use control totals, as appropriate
# Apply block share of 2013-2017 ACS variables using block/block group and block/tract shares of 2010 total population
# Note that "E" on the end of each variable is appended by tidycensus package to denote "estimate"

workingdata <- left_join(combo_total,acs_income, by="bg") %>% 
  mutate(
  HHINCQ1=(hhinc0_10E+
             hhinc10_15E+
             hhinc15_20E+
             hhinc20_25E+
             hhinc25_30E+
             hhinc30_35E+
             hhinc35_40E+
             hhinc40_45E)*sharebg,
  HHINCQ2=(hhinc45_50E+
             hhinc50_60E+
             hhinc60_75E+
             (hhinc75_100E*(1-shareabove91538)))*sharebg, # Apportions HHs below $91,538 within $75,000-$100,000
  HHINCQ3=((hhinc75_100E*shareabove91538)+                # Apportions HHs above $91,538 within $75,000-$100,000
             hhinc100_125E+
             hhinc125_150E)*sharebg,
  HHINCQ4=(hhinc150_200E+hhinc200pE)*sharebg)

hh_columns <- c("HHINCQ1","HHINCQ2","HHINCQ3","HHINCQ4")

final <- workingdata %>%
  group_by(maz) %>%
  summarize(  HHINCQ1=sum(HHINCQ1),
              HHINCQ2=sum(HHINCQ2),
              HHINCQ3=sum(HHINCQ3),
              HHINCQ4=sum(HHINCQ4)) %>% 
  mutate(hh_total=rowSums(select(.,all_of(hh_columns)))) %>% 
  mutate_at(c(all_of(hh_columns),"hh_total"),~round(.,digits = 0)) %>% 
  mutate(hh_subtotal=rowSums(select(.,all_of(hh_columns))),
         max_hh = hh_columns[max.col(select(.,hh_columns), ties.method="first")],
         hh_diff = hh_total - hh_subtotal)

for (col in hh_columns) {
  final[col] <- if_else(final$max_hh==col, 
                                     final[[col]] + final[["hh_diff"]],
                                     final[[col]])
}

final <- final %>% 
  select(MAZ=maz,HHINCQ1,HHINCQ2,HHINCQ3,HHINCQ4)

write.csv(final,"MAZ Households by Income.csv",row.names = F)
