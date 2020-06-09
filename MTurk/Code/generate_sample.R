#==============================================================================
# Author: Richard Liu 
# Description: Script to select the abstract samples for MTurk tagging, using method
#   10% non industry + 100% industry per food group
# Parameters for selection: % of industry/non-industry to sample 
#==============================================================================

rm(list = ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)
setwd("/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/MTurk")

# Abstracts to sample from 
industry_tags <- setDT(read.csv("../WebOfScience/Industry_Tagging/Outputs/wos_indtagged_final_wide.csv"))

# Remove empty abstracts
industry_tags <- industry_tags[AB != "" & !is.na(AB)]

# Set parameters for selection 
non_ind_perc <- 0.1 
ind_perc <- 1

# Create sample variable
industry_tags$To_Sample <- 0
industry_tags <- industry_tags[,c(86, 1:85)]

# Take industry sample 
industry_codes_dt <- industry_tags[Is_Industry == 1,list(Abstract.Code, Food.Code)]
industry_sample_dt <- industry_codes_dt[, .SD[sample(x=.N, size= round(.N*ind_perc))], by=Food.Code]
industry_sample <- industry_sample_dt$Abstract.Code
industry_tags[Abstract.Code %in% industry_sample, To_Sample := 1]

# Take non-industry sample
non_ind_codes_dt <- industry_tags[Is_Industry != 1,list(Abstract.Code, Food.Code)]
non_ind_sample_dt <- non_ind_codes_dt[,.SD[sample(x=.N, size = round(.N*non_ind_perc))], by = Food.Code]
non_ind_sample <- non_ind_sample_dt$Abstract.Code
industry_tags[Abstract.Code %in% non_ind_sample, To_Sample := 1]

# Take sampled abstracts and transform into 10-column table for MTurk upload 
sampled_abstracts <- as.character(industry_tags[To_Sample == 1]$AB)
sampled_abstracts <- sample(sampled_abstracts) # Shuffle 
length(sampled_abstracts) <- ceiling(length(sampled_abstracts)/10) * 10 # Pad vector to multiple of 10 
sample_matrix <- matrix(sampled_abstracts, ncol = 10) # To matrix
sample_out <- as.data.frame(sample_matrix)
colnames(sample_out) <- gsub("V", "text", colnames(sample_out))

# Output as 10-column CSV
write.csv(sample_out, "mturk_selection_allfood.csv", row.names=FALSE)

# Repeat for whole grains only sample 
sampled_abstracts_grains <- as.character(industry_tags[To_Sample == 1 & Food.Code %in% 1:22 & Food.Code != 13]$AB)
sampled_abstracts_grains <- sample(sampled_abstracts_grains) # Shuffle 
length(sampled_abstracts_grains) <- ceiling(length(sampled_abstracts_grains)/10) * 10 # Pad vector to multiple of 10 
sample_matrix_grains <- matrix(sampled_abstracts_grains, ncol = 10) # To matrix
sample_out_grains <- as.data.frame(sample_matrix_grains)
colnames(sample_out_grains) <- gsub("V", "text", colnames(sample_out_grains))

write.csv(sample_out_grains, "mturk_selection_grains.csv", row.names=FALSE)

# Save wide file with sample tagged column 
write.csv(industry_tags, "../WebOfScience/Industry_Tagging/Outputs/wos_indtagged_final_wide.csv", row.names=FALSE)
