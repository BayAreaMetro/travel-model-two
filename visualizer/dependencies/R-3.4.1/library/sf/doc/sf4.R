## ----echo=FALSE, include=FALSE-------------------------------------------
knitr::opts_chunk$set(collapse = TRUE)

## ------------------------------------------------------------------------
library(sf)
nc <- st_read(system.file("shape/nc.shp", package="sf"))
nc <- st_transform(nc, 2264)
nc[1,]

## ------------------------------------------------------------------------
library(dplyr)
nc %>% select(NWBIR74) %>% head(2)

## ------------------------------------------------------------------------
nc %>% as.data.frame %>% select(NWBIR74) %>% head(2)

## ------------------------------------------------------------------------
nc[1, "NWBIR74"]

## ------------------------------------------------------------------------
nc[1, "NWBIR74", drop = TRUE]

## ------------------------------------------------------------------------
Ashe = nc[nc$NAME == "Ashe",]
nc[Ashe,]

## ------------------------------------------------------------------------
Ashe = nc[nc$NAME == "Ashe",]
nc[Ashe, op = st_touches]

## ------------------------------------------------------------------------
nc %>% filter(lengths(st_touches(., Ashe)) > 0)

## ------------------------------------------------------------------------
nc <- nc %>% mutate(frac74 = SID74 / BIR74)
(a <- aggregate(nc[,"frac74"], list(Ashe_nb = lengths(st_intersects(nc, Ashe)) > 0), mean))
plot(a[2], col = c(grey(.8), grey(.5)))
plot(st_geometry(Ashe), border = '#ff8888', add = TRUE, lwd = 2)

