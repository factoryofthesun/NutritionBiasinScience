#' ---
#' author: "Richard Liu"
#' output: pdf
#' description: Comparing scraped journal impact data and grains coverage 
#' ---
rm(list=ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)
library(gridExtra)
library(readxl)
setwd("/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/Regression_Analysis/Journal_Analysis")

jcr <- setDT(read.csv("jcr_impact_factors.csv"))
sjr <- setDT(read.csv("sjr_scrape.csv"))

# Check coverage with each other 
full_data <- merge(jcr, sjr, by='Journal')
full_data$X <- NULL
colnames(full_data)[c(3,6)] <- c("Impact_Year", "SJR_Year")
full_data[Impact_Factor == "", Impact_Factor := NaN]

jcr_no_sjr <- full_data[is.na(SJR_Score) & !is.na(Impact_Factor)]
sjr_no_jcr <- full_data[is.na(Impact_Factor) & !is.na(SJR_Score)]
sjr_no_jcr_h <- full_data[is.na(Impact_Factor) & !is.na(H_Index)]
  
# Check grains coverage 
wos <- setDT(read.csv("../../WebOfScience/Industry_Tagging/Outputs/wos_indtagged_final_wide_FEclean.csv"))
grains_journals <- unique(wos[Food.Code <= 22, Journal])

full_data$Grains_Journal <- full_data$Journal %in% grains_journals
grains_missing <- full_data[Grains_Journal & (is.na(Impact_Factor) | is.na(SJR_Score))]
grains_missing_sjr <- grains_missing[is.na(SJR_Score)] #182/418 
grains_missing_jcr <- grains_missing[is.na(Impact_Factor)] #199/418 

write.csv(full_data, "full_journals_data.csv", row.names=F)




