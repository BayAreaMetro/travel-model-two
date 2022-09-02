##########################################################
### Script to summarize workers by MAZ and Occupation Type

### Read Command Line Arguments
args                <- commandArgs(trailingOnly = TRUE)
Parameters_File     <- args[1]
# Parameters_File     <- "F:/Projects/Clients/mtc/updated_networks/version_12_landuse_scaling/input/visualizer/runtime/parameters.csv"

SYSTEM_REPORT_PKGS <- c("reshape", "dplyr", "ggplot2", "plotly")
lib_sink <- suppressWarnings(suppressMessages(lapply(SYSTEM_REPORT_PKGS, library, character.only = TRUE))) 

### Read parameters from Parameters_File
parameters          <- read.csv(Parameters_File, header = TRUE)
ABM_DIR             <- trimws(paste(parameters$Value[parameters$Key=="ABM_DIR"]))	
ABM_OUTPUT_DIR      <- trimws(paste(parameters$Value[parameters$Key=="ABM_OUTPUT_DIR"]))	
VISUALIZER_INPUT_PATH <- trimws(paste(parameters$Value[parameters$Key=="VISUALIZER_INPUT_PATH"]))	
WORKING_DIR         <- trimws(paste(parameters$Value[parameters$Key=="WORKING_DIR"]))
ZONES_DIR           <- trimws(paste(parameters$Value[parameters$Key=="ZONES_DIR"]))
LANDUSE_DIR           <- trimws(paste(parameters$Value[parameters$Key=="LANDUSE_DIR"]))
BUILD_SUMMARY_DIR   <- trimws(paste(parameters$Value[parameters$Key=="BUILD_SUMMARY_DIR"]))
MAX_ITER            <- trimws(paste(parameters$Value[parameters$Key=="MAX_ITER"]))
BUILD_SAMPLE_RATE   <- as.numeric(trimws(paste(parameters$Value[parameters$Key=="BUILD_SAMPLE_RATE"])))
geogXWalkDir        <- "E:/projects/clients/mtc/data/Trip End Geocodes"

# ABMInputDir   <- file.path(ABM_DIR, "input/landuse")
ABMInputDir   <- file.path(ABM_DIR, "landuse")
# factorDir     <- file.path(WORKING_DIR, "data")
factorDir     <- file.path(VISUALIZER_INPUT_PATH, "data")
OutputDir     <- file.path(VISUALIZER_INPUT_PATH, "data/JPEG")

# read data
wsLoc   <- read.csv(paste(ABM_OUTPUT_DIR, paste("wsLocResults_",MAX_ITER, ".csv", sep = ""), sep = "/"), as.is = T)
# mazData <- read.csv(paste(ABMInputDir, "maz_data.csv", sep = "/"), as.is = T)
mazData <- read.csv(paste(LANDUSE_DIR, "maz_data.csv", sep = "/"), as.is = T)
occFac  <- read.csv(paste(factorDir, "occFactors.csv", sep = "/"), as.is = T)
# xwalk   <- read.csv(paste(geogXWalkDir, "geographicCWalk.csv", sep = "/"), as.is = T)
xwalk   <- read.csv(paste(ZONES_DIR, "geographicCWalk.csv", sep = "/"), as.is = T)

occp_type_codes       <- c("occ1", "occ2", "occ3", "occ4", "occ5", "occ6", "Total")
occp_type_names       <- c("Management", "Proffesional", "Services", "Retail", "Manual", "Military", "Total")
occp_type_df          <- data.frame(code = occp_type_codes, name = occp_type_names)


### Functions
lm_eqn <- function(df){
  m <- lm(y ~ x - 1, df);
  eq <- paste("Y = ", format(coef(m)[1], digits = 2), " * X, ", " r2 = ", format(summary(m)$r.squared, digits = 3), sep = "")
  return(eq)
}

createScatter <- function(df, occ, plot_prefix='Jobs_Workers_'){
  df <- df[df$occp==occ,]
  colnames(df) <- c("CountLocation", "OCCTYPE", "y", "x")
  
  #remove rows where both x and y are zeros
  df <- df[!(df$x==0 & df$y==0),]
  
  x_pos <- round(max(df$x)*0.40)
  x_pos1 <- round(max(df$x)*0.75)
  y_pos <- round(max(df$y)*0.80)
  
  p2 <- ggplot(df, aes(x=x, y=y)) + 
    geom_point(shape=1, color = "#0072B2") + 
    geom_smooth(method=lm, formula = y ~ x - 1, se=FALSE, color = "#0072B2") + 
    geom_abline(intercept = 0, slope = 1, linetype = 2) + 
    geom_text(x = x_pos, y = y_pos,label = as.character(lm_eqn(df)) ,  parse = FALSE, color = "#0072B2", size = 6) + 
    geom_text(x = x_pos1, y = 0,label = "- - - - : 45 Deg Line",  parse = FALSE, color = "black") + 
    labs(x=paste("Employment", occ, sep = "-"), y=paste("Workers", occ, sep = "-"))
  
  ggsave(file=paste(OutputDir, paste(plot_prefix, occ, ".jpeg", sep = ""), sep = "/"), width=12,height=10)
}

# workers by occupation type
workersbyMAZ <- wsLoc[wsLoc$PersonType<=3 & wsLoc$WorkLocation>0 & wsLoc$WorkSegment %in% c(0,1,2,3,4,5),] %>%
  mutate(weight = 1/BUILD_SAMPLE_RATE) %>%
  group_by(WorkLocation, WorkSegment) %>%
  mutate(num_workers = sum(weight)) %>%
  select(WorkLocation, WorkSegment, num_workers)

ABM_Summary <- cast(workersbyMAZ, WorkLocation~WorkSegment, value = "num_workers", fun.aggregate = max)
ABM_Summary$`0`[is.infinite(ABM_Summary$`0`)] <- 0
ABM_Summary$`1`[is.infinite(ABM_Summary$`1`)] <- 0
ABM_Summary$`2`[is.infinite(ABM_Summary$`2`)] <- 0
ABM_Summary$`3`[is.infinite(ABM_Summary$`3`)] <- 0
ABM_Summary$`4`[is.infinite(ABM_Summary$`4`)] <- 0
ABM_Summary$`5`[is.infinite(ABM_Summary$`5`)] <- 0

colnames(ABM_Summary) <- c("MAZ", "occ1", "occ2", "occ3", "occ4", "occ5", "occ6")


# compute jobs by occupation type
empCat <- colnames(occFac)[colnames(occFac)!="emp_code"]

mazData$occ1 <- 0
mazData$occ2 <- 0
mazData$occ3 <- 0
mazData$occ4 <- 0
mazData$occ5 <- 0
mazData$occ6 <- 0

for(cat in empCat){
  mazData$occ1 <- mazData$occ1 + mazData[,c(cat)]*occFac[1,c(cat)]
  mazData$occ2 <- mazData$occ2 + mazData[,c(cat)]*occFac[2,c(cat)]
  mazData$occ3 <- mazData$occ3 + mazData[,c(cat)]*occFac[3,c(cat)]
  mazData$occ4 <- mazData$occ4 + mazData[,c(cat)]*occFac[4,c(cat)]
  mazData$occ5 <- mazData$occ5 + mazData[,c(cat)]*occFac[5,c(cat)]
  mazData$occ6 <- mazData$occ6 + mazData[,c(cat)]*occFac[6,c(cat)]
}

### get df in right format before outputting
df1 <- mazData[,c("MAZ", "MAZ_ORIGINAL")] %>%
  left_join(ABM_Summary, by = c("MAZ"="MAZ")) %>%
  select(-MAZ_ORIGINAL)

df1[is.na(df1)] <- 0
df1$Total <- rowSums(df1[,!colnames(df1) %in% c("MAZ")])
df1[is.na(df1)] <- 0
df1 <- melt(df1, id = c("MAZ"))
colnames(df1) <- c("MAZ", "occp", "value")

df2 <- mazData[,c("MAZ","occ1", "occ2", "occ3", "occ4", "occ5", "occ6")]
df2[is.na(df2)] <- 0
df2$Total <- rowSums(df2[,!colnames(df2) %in% c("MAZ")])
df2[is.na(df2)] <- 0
df2 <- melt(df2, id = c("MAZ"))
colnames(df2) <- c("MAZ", "occp", "value")

df <- cbind(df1, df2$value)
colnames(df) <- c("MAZ", "occp", "workers", "jobs")
df$occp <- occp_type_df$name[match(df$occp, occp_type_df$code)]
df$occp <- factor(df$occp, levels = occp_type_names)
df$COUNTY <- xwalk$COUNTYNAME[match(df$MAZ, xwalk$MAZ)]
##df <- df[df$COUNTY=="San Francisco",]
### Create scatter plots
for(occ in occp_type_names){
  cat(occ, "\n")
  createScatter(df, occ)
}

df$TAZ <- mazData$TAZ[match(df$MAZ, mazData$MAZ)]
df_TAZ <- data.frame(aggregate(cbind(df$workers, df$jobs), by=list(TAZ=df$TAZ, occp=df$occp), FUN=sum))
colnames(df_TAZ) <- c('TAZ', 'occp', 'workers', 'jobs')
createScatter(df_TAZ, 'Total', 'Jobs_Workers_TAZ_')

### get df in right format before outputting
df1 <- mazData[,c("MAZ", "MAZ_ORIGINAL")] %>%
  left_join(ABM_Summary, by = c("MAZ"="MAZ")) %>%
  select(-MAZ_ORIGINAL)
  






# finish