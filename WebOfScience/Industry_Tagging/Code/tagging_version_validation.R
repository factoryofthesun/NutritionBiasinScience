#' ---
#' title: "Industry tagging boards validation"
#' author: "Richard Liu"
#' ---
# Script to validate whether the _v1 version of industry tagging matches up with the last non-boards version
rm(list = ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)

setwd("/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/WebOfScience/Industry_Tagging")

v1 <- setDT(read.csv("Outputs/wos_indtagged_final_wide_v1.csv"))
vold <- setDT(read.csv("Outputs/wos_indtagged_final_wide.csv"))
vmerge <- merge(v1[,.(Abstract.Code, Food.Code, Companies, Boards)], vold[,.(Abstract.Code, Companies)],
                by="Abstract.Code")

vmerge$Companies.x <- as.character(vmerge$Companies.x)
vmerge$Companies.y <- as.character(vmerge$Companies.y)
issues <- vmerge[Companies.x != Companies.y]
colnames(issues)[3] <- "Companies_V1"
colnames(issues)[5] <- "Companies_Old"

write.csv(issues, "Temp/v1_old_wos_diffs.csv", row.names=FALSE)
