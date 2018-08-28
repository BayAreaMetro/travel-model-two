########################################################################################

# R code to calculate toll costs for I-680 Contra Costa Express Lanes
# The results of this calculations form the inputs for...\Box\Modeling and Surveys\Development\Travel Model Two Development\Model Enhancements\Express Lanes\Tolls_2018.08.08revision.xlsx

########################################################################################


library(dplyr)
library(lubridate)

# clear the environment
rm(list=ls())

# read the ExpressLanesTransactionsMarch_2018.txt
In_file <- "M:/Development/Travel Model Two/Validation/MTC_express_lanes/ExpressLanesTransactionsMarch_2018.txt"
# In_file <- "C:/Users/ftsang/Documents/M_onLaptop/MTC_express_lanes_laptop/ExpressLanesTransactionsMarch_2018.txt"
In_df <- read.csv(file=In_file, header=TRUE, sep=";")
head(In_df)


# check FasTrak vs. non 
# -------------------------------------------------------------
In_df %>% count(transactiontype, sort = TRUE)

# fix the spelling of Fastrak
# from ?gsub: "fixed	logical.If TRUE, pattern is a string to be matched as is. Overrides all conflicting arguments."
In_df$transactiontype2 <- gsub("FasTrack", "FasTrak", In_df$transactiontype, fixed=TRUE)
# after checking that gsub works fine, drop the original column and rename the new column
In_df <- select(In_df, -transactiontype)
In_df = rename(In_df, transactiontype = transactiontype2)

# re-tabulate transactiontype
In_df %>% count(transactiontype, sort = TRUE)



# Add new columns for toll cost calculations
# -------------------------------------------------------------
# add a new column - weekday
In_df$weekday <- wday(In_df$dtfirsttransdatetime, label = TRUE)

# to delete the column "new"
# In_df <- select(In_df, -new)

# add a new column - start hour
In_df$starthour <- hour(In_df$dtfirsttransdatetime)

# add a new column - time period
In_df <- In_df %>%
    mutate(timeperiod = recode(starthour,
	"0" = "5 - EV",
	"1" = "5 - EV",
	"2" = "5 - EV",
	"3" = "1 - EA",
	"4" = "1 - EA",
	"5" = "1 - EA",
	"6" = "2 - AM",
	"7" = "2 - AM",
	"8" = "2 - AM",
	"9" = "2 - AM",
	"10" = "3 - MD",
	"11" = "3 - MD",
	"12" = "3 - MD",
	"13" = "3 - MD",
	"14" = "3 - MD",
	"15" = "4 - PM",
	"16" = "4 - PM",
	"17" = "4 - PM",
	"18" = "4 - PM",
	"19" = "5 - EV",
	"20" = "5 - EV",
	"21" = "5 - EV",
	"22" = "5 - EV",
	"23" = "5 - EV"))

# add a new column - start end combo
In_df$startendcombo <- paste(In_df$istartplaza, "-", In_df$iendplaza, sep="") 

# merge the distance based on the start end combo
Distance_file <- "M:/Development/Travel Model Two/Validation/MTC_express_lanes/expresslane_read_point_distances.csv"
Distance_df <- read.csv(file=Distance_file, header=TRUE, sep=",")
Distance_df$startendcombo <- paste(Distance_df$istartplaza, "-", Distance_df$iendplaza, sep="") 
ExpressLanes_df <- left_join(In_df, Distance_df, by = "startendcombo")

# after checking that the merge worked fine, drop columns that are not needed
ExpressLanes_df <- select(ExpressLanes_df, -istartplazaid.y, -iendplazaid.y)

# merge the pricing zone info (there are four pricing zones)
# -------------------------------------------------------------
# read in the data file 
PricingZone_file <- "M:/Development/Travel Model Two/Validation/MTC_express_lanes/expresslane_read_point_orderedNtoS.csv"
PricingZone_df <- read.csv(file=PricingZone_file, header=TRUE, sep=",")

# drop irrelevant columns
# keep direction, pricing zone, read point id start, read point id end
PricingZone_df <- select(PricingZone_df, vcdrctn, vczonnm, irdpntd, ReadPointID_new)

# Create two pricing zone data frames for merging - one for start plazas, one for end plazas
PricingZoneStart_df = rename(PricingZone_df, direction_start = vcdrctn, pzone_start = vczonnm, readpointid_start = irdpntd, longid_start = ReadPointID_new)
PricingZoneEnd_df = rename(PricingZone_df, direction_end = vcdrctn, pzone_end = vczonnm, readpointid_end = irdpntd, longid_end = ReadPointID_new)

# merge twice - one to the start plaza, another to the end plaza
ExpressLanes_df <- left_join(ExpressLanes_df, PricingZoneStart_df, by = c("istartplazaid.x" = "readpointid_start"))
ExpressLanes_df <- left_join(ExpressLanes_df, PricingZoneEnd_df, by = c("iendplazaid.x" = "readpointid_end"))

# clean the "revenue" column
# "," should be "."
# -------------------------------------------------------------
ExpressLanes_df$revenue2 <- gsub(",", ".", ExpressLanes_df$revenue, fixed=TRUE)
ExpressLanes_df$revenue_numeric <- as.numeric(ExpressLanes_df$revenue2)
# after checking gsub worked, delete the variable revenue2
ExpressLanes_df <- select(ExpressLanes_df, -revenue2)

# the distance variable also needs to be converted numeric
# -------------------------------------------------------------
ExpressLanes_df$distance <- as.numeric(ExpressLanes_df$distance_between_readings)

# calculate cost per mile
ExpressLanes_df$costpermile <- (ExpressLanes_df$revenue_numeric / ExpressLanes_df$distance)

# add a new column - start and end pricing zones
# -------------------------------------------------------------
ExpressLanes_df$startendpzones <- paste(ExpressLanes_df$pzone_start, "-", ExpressLanes_df$pzone_start, sep="") 

# check if any of the transactions cross pricing zones
# -------------------------------------------------------------
ExpressLanes_df %>% count(startendpzones, sort = TRUE)

# all transactions are within the same pricing zones - this keeps things simple
# Four startendpzones:
# - Livorna-Livorna
# - Crow Canyon SB-Crow Canyon SB
# - Crow Canyon NB-Crow Canyon NB
# - Alcosta-Alcosta


# aggregate data by pricing zones and time period
# -------------------------------------------------------------

# tollcost_df <- ExpressLanes_df %>%
#   group_by(startendpzones, timeperiod) %>%
#   summarise(revenue_total = sum(revenue_numeric, na.rm = TRUE),
#            transaction_num = n(),
#            costpermile_avg = mean(costpermile, na.rm = TRUE))

# instead of using the na.rm = TRUE option, explicitly account for the rows where revenue_numeric is na
# also separate out Fastrak vs non Fastrak transactions
ExpressLanes_df$revenue_na <- is.na(ExpressLanes_df$revenue_numeric)

tollcost_df <- ExpressLanes_df %>%
   group_by(transactiontype, revenue_na, startendpzones, timeperiod) %>%
   summarise(revenue_total = sum(revenue_numeric),
            transaction_num = n(),
            costpermile_avg = mean(costpermile))


# calculate cost per vehicle 
# -------------------------------------------------------------
tollcost_df$costperveh <- tollcost_df$revenue_total/tollcost_df$transaction_num


# write to csv
# -------------------------------------------------------------
# write out the data frame with the trasaction data and pricing zone info
Out_transaction_file <- "M:/Development/Travel Model Two/Validation/MTC_express_lanes/I680_Contra_Costa_Express_Lanes_transaction_data_March2018.csv"
write.table(ExpressLanes_df, file=(Out_transaction_file), sep = ",", row.names=FALSE, col.names=TRUE)

# write out the data frame with the trasaction data and pricing zone info
Out_toll_file <- "M:/Development/Travel Model Two/Validation/MTC_express_lanes/I680_Contra_Costa_Express_Lanes_toll_March2018.csv"
write.table(tollcost_df, file=(Out_toll_file), sep = ",", row.names=FALSE, col.names=TRUE)


# questions:
# how come some of the revenue values show up as na? (it looks like some of these are fastrak user traveling at peak hours)
# how come some of the transaction is non fastrak (is using fastrak only the right approach. probably yes)


