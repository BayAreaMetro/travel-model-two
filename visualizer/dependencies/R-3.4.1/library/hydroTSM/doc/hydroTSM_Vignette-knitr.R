## ----installation1, eval=FALSE-------------------------------------------
#  install.packages("hydroTSM")

## ----installation2, eval=FALSE-------------------------------------------
#  if (!require(devtools)) install.packages("devtools")
#  library(devtools)
#  install_github("hzambran/hydroTSM")

## ----LoadingPkg----------------------------------------------------------
library(hydroTSM)

## ----LoadingData---------------------------------------------------------
data(SanMartinoPPts)

## ----Window--------------------------------------------------------------
x <- window(SanMartinoPPts, start=as.Date("1985-01-01"))

## ----daily2monthly-------------------------------------------------------
( m <- daily2monthly(x, FUN=sum) )

## ----Dates---------------------------------------------------------------
dates <- time(x)

## ----yip-----------------------------------------------------------------
( nyears <- yip(from=start(x), to=end(x), out.type="nmbr" ) )

## ----smry----------------------------------------------------------------
smry(x)

## ----hydroplot, dev='pdf', fig.width=10, fig.height=8--------------------
hydroplot(x, var.type="Precipitation", main="at San Martino", 
          pfreq = "dm", from="1987-01-01")

## ----dwi1----------------------------------------------------------------
dwi(x)

## ----dwi2----------------------------------------------------------------
dwi(x, out.unit="mpy")

## ----matrixplot----------------------------------------------------------
# Daily zoo to monthly zoo
m <- daily2monthly(x, FUN=sum, na.rm=TRUE)
     
# Creating a matrix with monthly values per year in each column
M <- matrix(m, ncol=12, byrow=TRUE)
colnames(M) <- month.abb
rownames(M) <- unique(format(time(m), "%Y"))
     
# Plotting the monthly precipitation values
require(lattice)
print(matrixplot(M, ColorRamp="Precipitation", 
           main="Monthly precipitation at San Martino st., [mm/month]"))

## ----daily2annual--------------------------------------------------------
daily2annual(x, FUN=sum, na.rm=TRUE)

## ----daily2annual2-------------------------------------------------------
mean( daily2annual(x, FUN=sum, na.rm=TRUE) )

## ----annualfunction------------------------------------------------------
annualfunction(x, FUN=sum, na.rm=TRUE) / nyears

## ----monthlyfunction-----------------------------------------------------
monthlyfunction(m, FUN=median, na.rm=TRUE)

## ----cmonth--------------------------------------------------------------
cmonth <- format(time(m), "%b")

## ----months--------------------------------------------------------------
months <- factor(cmonth, levels=unique(cmonth), ordered=TRUE)

## ----boxplotMonthly, dev='pdf'-------------------------------------------
boxplot( coredata(m) ~ months, col="lightblue", main="Monthly Precipitation", 
         ylab="Precipitation, [mm]", xlab="Month")

## ----seasonalfunction----------------------------------------------------
seasonalfunction(x, FUN=sum, na.rm=TRUE) / nyears

## ----dm2seasonal---------------------------------------------------------
( DJF <- dm2seasonal(x, season="DJF", FUN=sum) )
( MAM <- dm2seasonal(m, season="MAM", FUN=sum) )
( JJA <- dm2seasonal(m, season="JJA", FUN=sum) )
( SON <- dm2seasonal(m, season="SON", FUN=sum) )

## ----hydroplot2, dev='pdf', fig.width=12, fig.height=10------------------
hydroplot(x, pfreq="seasonal", FUN=sum, stype="default")

## ----LoadingData2--------------------------------------------------------
data(SanMartinoPPts)

## ----Window2-------------------------------------------------------------
x <- window(SanMartinoPPts, start=as.Date("1988-01-01"))

## ----hydroplot3, dev='pdf'-----------------------------------------------
hydroplot(x,  ptype="ts", pfreq="o", var.unit="mm")

## ----R10mm---------------------------------------------------------------
( R10mm <- length( x[x>10] ) )

## ----wet_index-----------------------------------------------------------
wet.index <- which(x >= 1)

## ----PRwn95--------------------------------------------------------------
( PRwn95 <- quantile(x[wet.index], probs=0.95, na.rm=TRUE) )

## ----very_wet_index------------------------------------------------------
(very.wet.index <- which(x >= PRwn95))

## ----R95p----------------------------------------------------------------
( R95p <- sum(x[very.wet.index]) )

## ----x_5max, dev='pdf'---------------------------------------------------
x.5max <- rollapply(data=x, width=5, FUN=sum, fill=NA, partial= TRUE, 
                    align="center")

hydroplot(x.5max,  ptype="ts+boxplot", pfreq="o", var.unit="mm")

## ----(x_5max_annual------------------------------------------------------
(x.5max.annual <- daily2annual(x.5max, FUN=max, na.rm=TRUE))

## ----echo=FALSE----------------------------------------------------------
sessionInfo()$platform
sessionInfo()$R.version$version.string 
paste("hydroTSM", sessionInfo()$otherPkgs$hydroTSM$Version)

