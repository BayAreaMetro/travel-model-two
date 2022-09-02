#Marin vs MTC highway assignment summary script
#Khademul Haque, khademul.haque@rsginc.com, August 2018

# Libraries

library(foreign)
library(dplyr)
library(tidyverse)
library(ggplot2)

## User Inputs

# Directories
WD <- "E:/projects/clients/marin/HighwaySummary"
DataDir_marin <- file.path(WD, "data/assign/marin")
DataDir_mtc <- file.path(WD, "data/assign/mtc")
OutputDir <- file.path(WORKING_DIR, "data/JPEG")

## Data read
marin_am <- read.dbf(paste(DataDir_marin, "loadAM.dbf", sep = "/"), as.is = T)
marin_ea <- read.dbf(paste(DataDir_marin, "loadEA.dbf", sep = "/"), as.is = T)
marin_md <- read.dbf(paste(DataDir_marin, "loadMD.dbf", sep = "/"), as.is = T)
marin_pm <- read.dbf(paste(DataDir_marin, "loadPM.dbf", sep = "/"), as.is = T)
marin_ev <- read.dbf(paste(DataDir_marin, "loadEV.dbf", sep = "/"), as.is = T)
mtc_am <- read.dbf(paste(DataDir_mtc, "loadAM.dbf", sep = "/"), as.is = T)
mtc_ea <- read.dbf(paste(DataDir_mtc, "loadEA.dbf", sep = "/"), as.is = T)
mtc_md <- read.dbf(paste(DataDir_mtc, "loadMD.dbf", sep = "/"), as.is = T)
mtc_pm <- read.dbf(paste(DataDir_mtc, "loadPM.dbf", sep = "/"), as.is = T)
mtc_ev <- read.dbf(paste(DataDir_mtc, "loadEV.dbf", sep = "/"), as.is = T)

marin_ea2 <- marin_ea %>% 
  mutate(VolEA_tot = V1_1+V2_1+V3_1+V4_1+V5_1+V6_1+V7_1+V8_1+V9_1+V10_1+MAZMAZVOL) %>% 
  select(OLD_A, OLD_B, VolEA_tot) %>%
  mutate(linkID=str_c(OLD_A,OLD_B))
marin_am2 <- marin_am %>% 
  mutate(VolAM_tot = V1_1+V2_1+V3_1+V4_1+V5_1+V6_1+V7_1+V8_1+V9_1+V10_1+MAZMAZVOL) %>% 
  select(OLD_A, OLD_B, VolAM_tot) %>%
  mutate(linkID=str_c(OLD_A,OLD_B)) %>% 
  select(-OLD_A, -OLD_B)
marin_md2 <- marin_md %>% 
  mutate(VolMD_tot = V1_1+V2_1+V3_1+V4_1+V5_1+V6_1+V7_1+V8_1+V9_1+V10_1+MAZMAZVOL) %>% 
  select(OLD_A, OLD_B, VolMD_tot) %>%
  mutate(linkID=str_c(OLD_A,OLD_B)) %>% 
  select(-OLD_A, -OLD_B)
marin_pm2 <- marin_pm %>% 
  mutate(VolPM_tot = V1_1+V2_1+V3_1+V4_1+V5_1+V6_1+V7_1+V8_1+V9_1+V10_1+MAZMAZVOL) %>% 
  select(OLD_A, OLD_B, VolPM_tot) %>%
  mutate(linkID=str_c(OLD_A,OLD_B)) %>% 
  select(-OLD_A, -OLD_B)
marin_ev2 <- marin_ev %>% 
  mutate(VolEV_tot = V1_1+V2_1+V3_1+V4_1+V5_1+V6_1+V7_1+V8_1+V9_1+V10_1+MAZMAZVOL) %>% 
  select(OLD_A, OLD_B, VolEV_tot) %>%
  mutate(linkID=str_c(OLD_A,OLD_B)) %>% 
  select(-OLD_A, -OLD_B)

marin_daily <- marin_ea2 %>% 
  left_join(marin_am2, by = "linkID") %>%
  left_join(marin_md2, by = "linkID") %>%
  left_join(marin_pm2, by = "linkID") %>%
  left_join(marin_ev2, by = "linkID") %>%
  mutate(vol_daily=VolEA_tot+VolAM_tot+VolMD_tot+VolPM_tot+VolEV_tot)

mtc_ea2 <- mtc_ea %>% 
  mutate(VolEA_tot_mtc = V1_1+V2_1+V3_1+V4_1+V5_1+V6_1+V7_1+V8_1+V9_1+V10_1) %>% 
  select(OLD_A, OLD_B, VolEA_tot_mtc) %>%
  mutate(linkID=str_c(OLD_A,OLD_B)) %>% 
  select(-OLD_A, -OLD_B)
mtc_am2 <- mtc_am %>% 
  mutate(VolAM_tot_mtc = V1_1+V2_1+V3_1+V4_1+V5_1+V6_1+V7_1+V8_1+V9_1+V10_1) %>% 
  select(OLD_A, OLD_B, VolAM_tot_mtc) %>%
  mutate(linkID=str_c(OLD_A,OLD_B)) %>% 
  select(-OLD_A, -OLD_B)
mtc_md2 <- mtc_md %>% 
  mutate(VolMD_tot_mtc = V1_1+V2_1+V3_1+V4_1+V5_1+V6_1+V7_1+V8_1+V9_1+V10_1) %>% 
  select(OLD_A, OLD_B, VolMD_tot_mtc) %>%
  mutate(linkID=str_c(OLD_A,OLD_B)) %>% 
  select(-OLD_A, -OLD_B)
mtc_pm2 <- mtc_pm %>% 
  mutate(VolPM_tot_mtc = V1_1+V2_1+V3_1+V4_1+V5_1+V6_1+V7_1+V8_1+V9_1+V10_1) %>% 
  select(OLD_A, OLD_B, VolPM_tot_mtc) %>%
  mutate(linkID=str_c(OLD_A,OLD_B)) %>% 
  select(-OLD_A, -OLD_B)
mtc_ev2 <- mtc_ev %>% 
  mutate(VolEV_tot_mtc = V1_1+V2_1+V3_1+V4_1+V5_1+V6_1+V7_1+V8_1+V9_1+V10_1) %>% 
  select(OLD_A, OLD_B, VolEV_tot_mtc) %>%
  mutate(linkID=str_c(OLD_A,OLD_B)) %>% 
  select(-OLD_A, -OLD_B)

mtc_daily <- mtc_ea2 %>% 
  left_join(mtc_am2, by = "linkID") %>%
  left_join(mtc_md2, by = "linkID") %>%
  left_join(mtc_pm2, by = "linkID") %>%
  left_join(mtc_ev2, by = "linkID") %>%
  mutate(vol_daily_mtc=VolEA_tot_mtc+VolAM_tot_mtc+VolMD_tot_mtc+VolPM_tot_mtc+VolEV_tot_mtc)

# Draw scatterplot

## Daily
assign_final <- marin_daily %>% 
  left_join(mtc_daily, by = "linkID") %>% 
  select(OLD_A, OLD_B, vol_daily, linkID, vol_daily_mtc)
colnames(assign_final) <- c("OLD_A", "OLD_B", "x", "linkID", "y")
x_pos  <- round(max(assign_final$x)*0.40)
x_pos1 <- round(max(assign_final$x)*0.75)
y_pos  <- round(max(assign_final$y)*0.80)
max_lim <- round(max(assign_final$x,assign_final$y))+1000
p <- ggplot(data = assign_final) + 
  geom_point(mapping = aes(x = x, y = y)) +
  geom_smooth(mapping = aes(x = x, y = y), method = "lm", formula = y ~ x) +
  geom_abline(intercept = 0, slope = 1, linetype = 2) +
  geom_text(x = x_pos1, y = 0,label = "- - - - : 45 Deg Line",  parse = FALSE, color = "black") +
  scale_x_continuous(limits = c(0, max_lim)) +
  scale_y_continuous(limits = c(0, max_lim)) +
  xlab("Marin") +
  ylab("MTC") +
  ggtitle("MTC vs Marin (Daily Volume Comparison)") +
  theme(axis.text.x = element_text(size = 20),
        axis.title = element_text(size = 20),
        axis.text.y = element_text(size = 20),
        legend.text = element_text(size = 15),
        legend.title = element_text(size = 20))
m <- lm(y ~ x, data = assign_final)
eq <- substitute(italic(r)^2~"="~r2,
                 list(r2 = format(summary(m)$r.squared, digits = 3)))
dftext <- data.frame(x = 70, y = 50, eq = as.character(as.expression(eq)))
p + geom_text(aes(label = eq, colour = "darkred"), data = dftext, parse = TRUE, x=x_pos, y=y_pos, show.legend = FALSE)
ggsave(file=paste(OutputDir, paste("assign_summary_Daily", ".jpeg", sep = ""), sep = "/"), width=12,height=10)

## AM
assign_final_am <- marin_am2 %>% 
  left_join(mtc_am2, by = "linkID") %>% 
  select(VolAM_tot, linkID, VolAM_tot_mtc)
colnames(assign_final_am) <- c("x", "linkID", "y")
x_pos  <- round(max(assign_final_am$x)*0.40)
x_pos1 <- round(max(assign_final_am$x)*0.75)
y_pos  <- round(max(assign_final_am$y)*0.80)
max_lim <- round(max(assign_final_am$x,assign_final_am$y))+1000
p <- ggplot(data = assign_final_am) + 
  geom_point(mapping = aes(x = x, y = y)) +
  geom_smooth(mapping = aes(x = x, y = y), method = "lm", formula = y ~ x) +
  geom_abline(intercept = 0, slope = 1, linetype = 2) +
  geom_text(x = x_pos1, y = 0,label = "- - - - : 45 Deg Line",  parse = FALSE, color = "black") +
  scale_x_continuous(limits = c(0, max_lim)) +
  scale_y_continuous(limits = c(0, max_lim)) +
  xlab("Marin") +
  ylab("MTC") +
  ggtitle("MTC vs Marin (AM Volume Comparison)") +
  theme(axis.text.x = element_text(size = 20),
        axis.title = element_text(size = 20),
        axis.text.y = element_text(size = 20),
        legend.text = element_text(size = 15),
        legend.title = element_text(size = 20))
m <- lm(y ~ x, data = assign_final_am)
eq <- substitute(italic(r)^2~"="~r2,
                 list(r2 = format(summary(m)$r.squared, digits = 3)))
dftext <- data.frame(x = 70, y = 50, eq = as.character(as.expression(eq)))
p + geom_text(aes(label = eq, colour = "darkred"), data = dftext, parse = TRUE, x=x_pos, y=y_pos, show.legend = FALSE)
ggsave(file=paste(OutputDir, paste("assign_summary_AM", ".jpeg", sep = ""), sep = "/"), width=12,height=10)

## EA
assign_final_ea <- marin_ea2 %>% 
  left_join(mtc_ea2, by = "linkID") %>% 
  select(VolEA_tot, linkID, VolEA_tot_mtc)
colnames(assign_final_ea) <- c("x", "linkID", "y")
x_pos  <- round(max(assign_final_ea$x)*0.40)
x_pos1 <- round(max(assign_final_ea$x)*0.75)
y_pos  <- round(max(assign_final_ea$y)*0.80)
max_lim <- round(max(assign_final_ea$x,assign_final_ea$y))+1000
p <- ggplot(data = assign_final_ea) + 
  geom_point(mapping = aes(x = x, y = y)) +
  geom_smooth(mapping = aes(x = x, y = y), method = "lm", formula = y ~ x) +
  geom_abline(intercept = 0, slope = 1, linetype = 2) +
  geom_text(x = x_pos1, y = 0,label = "- - - - : 45 Deg Line",  parse = FALSE, color = "black") +
  scale_x_continuous(limits = c(0, max_lim)) +
  scale_y_continuous(limits = c(0, max_lim)) +
  xlab("Marin") +
  ylab("MTC") +
  ggtitle("MTC vs Marin (EA Volume Comparison)") +
  theme(axis.text.x = element_text(size = 20),
        axis.title = element_text(size = 20),
        axis.text.y = element_text(size = 20),
        legend.text = element_text(size = 15),
        legend.title = element_text(size = 20))
m <- lm(y ~ x, data = assign_final_ea)
eq <- substitute(italic(r)^2~"="~r2,
                 list(r2 = format(summary(m)$r.squared, digits = 3)))
dftext <- data.frame(x = 70, y = 50, eq = as.character(as.expression(eq)))
p + geom_text(aes(label = eq, colour = "darkred"), data = dftext, parse = TRUE, x=x_pos, y=y_pos, show.legend = FALSE)
ggsave(file=paste(OutputDir, paste("assign_summary_EA", ".jpeg", sep = ""), sep = "/"), width=12,height=10)

## MD
assign_final_md <- marin_md2 %>% 
  left_join(mtc_md2, by = "linkID") %>% 
  select(VolMD_tot, linkID, VolMD_tot_mtc)
colnames(assign_final_md) <- c("x", "linkID", "y")
x_pos  <- round(max(assign_final_md$x)*0.40)
x_pos1 <- round(max(assign_final_md$x)*0.75)
y_pos  <- round(max(assign_final_md$y)*0.80)
max_lim <- round(max(assign_final_md$x,assign_final_md$y))+1000
p <- ggplot(data = assign_final_md) + 
  geom_point(mapping = aes(x = x, y = y)) +
  geom_smooth(mapping = aes(x = x, y = y), method = "lm", formula = y ~ x) +
  geom_abline(intercept = 0, slope = 1, linetype = 2) +
  geom_text(x = x_pos1, y = 0,label = "- - - - : 45 Deg Line",  parse = FALSE, color = "black") +
  scale_x_continuous(limits = c(0, max_lim)) +
  scale_y_continuous(limits = c(0, max_lim)) +
  xlab("Marin") +
  ylab("MTC") +
  ggtitle("MTC vs Marin (MD Volume Comparison)") +
  theme(axis.text.x = element_text(size = 20),
        axis.title = element_text(size = 20),
        axis.text.y = element_text(size = 20),
        legend.text = element_text(size = 15),
        legend.title = element_text(size = 20))
m <- lm(y ~ x, data = assign_final_md)
eq <- substitute(italic(r)^2~"="~r2,
                 list(r2 = format(summary(m)$r.squared, digits = 3)))
dftext <- data.frame(x = 70, y = 50, eq = as.character(as.expression(eq)))
p + geom_text(aes(label = eq, colour = "darkred"), data = dftext, parse = TRUE, x=x_pos, y=y_pos, show.legend = FALSE)
ggsave(file=paste(OutputDir, paste("assign_summary_MD", ".jpeg", sep = ""), sep = "/"), width=12,height=10)

## PM
assign_final_pm <- marin_pm2 %>% 
  left_join(mtc_pm2, by = "linkID") %>% 
  select(VolPM_tot, linkID, VolPM_tot_mtc)
colnames(assign_final_pm) <- c("x", "linkID", "y")
x_pos  <- round(max(assign_final_pm$x)*0.40)
x_pos1 <- round(max(assign_final_pm$x)*0.75)
y_pos  <- round(max(assign_final_pm$y)*0.80)
max_lim <- round(max(assign_final_pm$x,assign_final_pm$y))+1000
p <- ggplot(data = assign_final_pm) + 
  geom_point(mapping = aes(x = x, y = y)) +
  geom_smooth(mapping = aes(x = x, y = y), method = "lm", formula = y ~ x) +
  geom_abline(intercept = 0, slope = 1, linetype = 2) +
  geom_text(x = x_pos1, y = 0,label = "- - - - : 45 Deg Line",  parse = FALSE, color = "black") +
  scale_x_continuous(limits = c(0, max_lim)) +
  scale_y_continuous(limits = c(0, max_lim)) +
  xlab("Marin") +
  ylab("MTC") +
  ggtitle("MTC vs Marin (PM Volume Comparison)") +
  theme(axis.text.x = element_text(size = 20),
        axis.title = element_text(size = 20),
        axis.text.y = element_text(size = 20),
        legend.text = element_text(size = 15),
        legend.title = element_text(size = 20))
m <- lm(y ~ x, data = assign_final_pm)
eq <- substitute(italic(r)^2~"="~r2,
                 list(r2 = format(summary(m)$r.squared, digits = 3)))
dftext <- data.frame(x = 70, y = 50, eq = as.character(as.expression(eq)))
p + geom_text(aes(label = eq, colour = "darkred"), data = dftext, parse = TRUE, x=x_pos, y=y_pos, show.legend = FALSE)
ggsave(file=paste(OutputDir, paste("assign_summary_PM", ".jpeg", sep = ""), sep = "/"), width=12,height=10)

## EV
assign_final_ev <- marin_ev2 %>% 
  left_join(mtc_ev2, by = "linkID") %>% 
  select(VolEV_tot, linkID, VolEV_tot_mtc)
colnames(assign_final_ev) <- c("x", "linkID", "y")
x_pos  <- round(max(assign_final_ev$x)*0.40)
x_pos1 <- round(max(assign_final_ev$x)*0.75)
y_pos  <- round(max(assign_final_ev$y)*0.80)
max_lim <- round(max(assign_final_ev$x,assign_final_ev$y))+1000
p <- ggplot(data = assign_final_ev) + 
  geom_point(mapping = aes(x = x, y = y)) +
  geom_smooth(mapping = aes(x = x, y = y), method = "lm", formula = y ~ x) +
  geom_abline(intercept = 0, slope = 1, linetype = 2) +
  geom_text(x = x_pos1, y = 0,label = "- - - - : 45 Deg Line",  parse = FALSE, color = "black") +
  scale_x_continuous(limits = c(0, max_lim)) +
  scale_y_continuous(limits = c(0, max_lim)) +
  xlab("Marin") +
  ylab("MTC") +
  ggtitle("MTC vs Marin (EV Volume Comparison)") +
  theme(axis.text.x = element_text(size = 20),
        axis.title = element_text(size = 20),
        axis.text.y = element_text(size = 20),
        legend.text = element_text(size = 15),
        legend.title = element_text(size = 20))
m <- lm(y ~ x, data = assign_final_ev)
eq <- substitute(italic(r)^2~"="~r2,
                 list(r2 = format(summary(m)$r.squared, digits = 3)))
dftext <- data.frame(x = 70, y = 50, eq = as.character(as.expression(eq)))
p + geom_text(aes(label = eq, colour = "darkred"), data = dftext, parse = TRUE, x=x_pos, y=y_pos, show.legend = FALSE)
ggsave(file=paste(OutputDir, paste("assign_summary_EV", ".jpeg", sep = ""), sep = "/"), width=12,height=10)

