#==============================================================================
# Author: Richard Liu 
# Description: Script to generate the MTurk sample for the remaining (non-grains) food groups.
# Sampling rule: All industry + 10% of remainder (remove duplicates)
# Use the nongrains_group_summary file to sample only from the research areas that have a 
# lower probability of being unrelated. 
#==============================================================================

rm(list = ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)

setwd("/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/MTurk")

wos_data <- setDT(read.csv("../WebOfScience/Industry_Tagging/Outputs/wos_indtagged_final_wide_v1.csv"))
areas <- setDT(read.csv("nongrains_group_summary.csv"))
food_groups_exclude <- c(50, 62, 89, 95, 100, 109, 115) # Food groups with 100% duplicated abstracts in another group

wos_data <- wos_data[AB != "" & !is.na(AB) & !(Food.Code %in% food_groups_exclude) & Food.Code >22]
groups_rem <- which(areas$SC == "Food Science & Technology")
groups_to_keep <- as.character(areas$SC)[1:(groups_rem-1)]

wos_long <- wos_data %>% separate_rows(SC, sep=";")
wos_long$SC <- trimws(wos_long$SC)
wos_long <- setDT(wos_long)[order(AB, SC)]
wos_ordered <- wos_long[,.(SC=paste(SC, collapse="; ")), by=list(Abstract.Code, Food.Code, AB, Is_Industry)][order(Abstract.Code)]
wos_ordered <- wos_ordered[!duplicated(AB),] # Remove remaining duplicate abstracts, keeping the abstracts with the lower code 

# Set parameters for selection 
non_ind_perc <- 0.1 
ind_perc <- 1

# Take industry sample
set.seed(1)
industry_sample_dt <- wos_ordered[Is_Industry==1, .SD[sample(x=.N, size= round(.N*ind_perc))], by=Food.Code]

# Take non-industry sample, choosing among the likely-related research groups
wos_nonind <- wos_ordered[Is_Industry == 0]
wos_nonind[,Sample_Size := round(.N * non_ind_perc), by=Food.Code]
set.seed(2)
nonind_sample <- wos_nonind[SC %in% groups_to_keep,.SD[sample(x=.N, size=Sample_Size)], by = Food.Code]

# Bind the samples and output
final_sample <- c(as.character(industry_sample_dt[,AB]), as.character(nonind_sample[,AB]))
final_dt <- data.frame("text" = final_sample)

write.csv(final_dt, "Samples/mturk_selection_fruitveg.csv", row.names=F)
