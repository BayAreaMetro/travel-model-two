## ---- echo = FALSE-------------------------------------------------------
NOT_CRAN <- identical(tolower(Sys.getenv("NOT_CRAN")), "true")
knitr::opts_chunk$set(purl = NOT_CRAN)

## ---- eval = FALSE-------------------------------------------------------
#  # Add key to .Renviron
#  Sys.setenv(CENSUS_KEY=YOURKEYHERE)
#  # Reload .Renviron
#  readRenviron("~/.Renviron")
#  # Check to see that the expected key is output in your R console
#  Sys.getenv("CENSUS_KEY")

## ---- message = FALSE----------------------------------------------------
library(censusapi)

## ---- eval = FALSE-------------------------------------------------------
#  apis <- listCensusApis()
#  View(apis)

## ------------------------------------------------------------------------
sahie_vars <- listCensusMetadata(name="timeseries/healthins/sahie", type = "variables")
head(sahie_vars)

## ------------------------------------------------------------------------
listCensusMetadata(name="timeseries/healthins/sahie", type = "geography")

## ---- eval = NOT_CRAN----------------------------------------------------
getCensus(name="timeseries/healthins/sahie",
	vars=c("NAME", "IPRCAT", "IPR_DESC", "PCTUI_PT"), 
	region="us:*", time=2015)

## ---- eval = NOT_CRAN----------------------------------------------------
sahie_states <- getCensus(name="timeseries/healthins/sahie",
	vars=c("NAME", "IPRCAT", "IPR_DESC", "PCTUI_PT"), 
	region="state:*", time=2015)
head(sahie_states)

## ---- eval = NOT_CRAN----------------------------------------------------
sahie_counties <- getCensus(name="timeseries/healthins/sahie",
	vars=c("NAME", "IPRCAT", "IPR_DESC", "PCTUI_PT"), 
	region="county:*", regionin="state:1,2", time=2015)
head(sahie_counties, n=12L)

## ---- eval = NOT_CRAN----------------------------------------------------
fips
tracts <- NULL
for (f in fips) {
	stateget <- paste("state:", f, sep="")
	temp <- getCensus(name="sf3", vintage=1990,
	vars=c("P0070001", "P0070002", "P114A001"), region="tract:*",
	regionin = stateget)
	tracts <- rbind(tracts, temp)
}
head(tracts)

## ---- eval = NOT_CRAN----------------------------------------------------
data2010 <- getCensus(name="sf1", vintage=2010,
	vars=c("P0010001", "P0030001"), 
	region="block:*", regionin="state:36+county:027")
head(data2010)

## ---- eval = NOT_CRAN----------------------------------------------------
data2000 <- getCensus(name="sf1", vintage=2000,
	vars=c("P001001", "P003001"), 
	region="block:*", regionin="state:36+county:027+tract:010000")
head(data2000)

