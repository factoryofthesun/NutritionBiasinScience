#==============================================================================
# Author: Richard Liu 
# Description: Script to compare distribution of research categories between industry
# and non-industry funded articles. 
#==============================================================================
rm(list = ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)
library(gridExtra)
setwd("/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/Regression_Analysis")

abstract_dt <- setDT(read.csv("../WebOfScience/Industry_Tagging/Outputs/wos_indtagged_final_wide_v1.csv"))
abstract_dt[FU_stripped_lower == " missing ", Is_Industry := 2]
abstract_sc_grouped <- abstract_dt[,.(Counts=.N), by=list(SC,Is_Industry)]
abstract_sc_wide <- dcast(abstract_sc_grouped, SC ~ Is_Industry, value.var="Counts")
abstract_sc_wide <- abstract_sc_wide[-(1:3),]
abstract_sc_wide[is.na(abstract_sc_wide)] <- 0
colnames(abstract_sc_wide) <- c("Category", "Non_Ind", "Ind", "Missing")

write.xlsx(abstract_sc_wide, "Distribution_Analysis/category_distribution.xlsx", row.names=F)

# Statistical test (chi-square)
chisq_tbl <- as.data.frame(abstract_sc_wide)
rownames(chisq_tbl) <- chisq_tbl$Category  
chisq_tbl$Category <- NULL
chisq.test(chisq_tbl)

  