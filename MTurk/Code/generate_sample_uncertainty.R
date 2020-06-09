#==============================================================================
# Author: Richard Liu 
# Description: Script to select the abstract samples (excl. oats) for MTurk tagging 
# Parameters for selection: % of each food group, industry concentration, uncertainty sampling 
#==============================================================================

rm(list = ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)
setwd("/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/MTurk")

# Abstracts to sample from 
# Use the output file from the most recent ML prediction
predictions <- setDT(read.csv("../Machine_Learning/RL_Trained/Predictions/full_predictions_AdamW.csv"))
industry_tags <- setDT(read.csv("../WebOfScience/Industry_Tagging/Outputs/wos_indtagged_v4.csv"))

abstracts_full <- merge(predictions, industry_tags[,c("Abstract.Code", "Is_Industry")], 
                        by="Abstract.Code") 

nrow(abstracts_full[!complete.cases(abstracts_full)])

# Set parameters for selection 
sample_perc <- 0.1 
industry_concentration <- 0.25 
uncertainty_sampling <- TRUE 

# Take sample 

# X% of each food group 
abstracts_full[,To_Sample_Tot := .N*sample_perc, by=Food.Code]

# Apply concentration ratio, or all industry abstracts, whichever is smaller 
abstracts_full[Is_Industry==1, To_Sample := min(.N,round(To_Sample_Tot*industry_concentration)), by=Food.Code]
abstracts_full[is.na(To_Sample), To_Sample := 0]
abstracts_full[, To_Sample := max(To_Sample, na.rm=TRUE), by=Food.Code]
abstracts_full[Is_Industry==0, To_Sample := min(.N, round(To_Sample_Tot - To_Sample)),by=Food.Code]

set.seed(1)

if (!uncertainty_sampling){
  final_sample <- abstracts_full[,sample(Abstract, To_Sample), by=list(Food.Code, Is_Industry)]
  colnames(final_sample)[3] <- "text" 
}

else{
  abstracts_full$Certainty <- abs(abstracts_full$Prob_Positive - abstracts_full$Prob_NotPositive)
  final_sample <- abstracts_full[order(Food.Code, Certainty), head(Abstract, mean(To_Sample)), by=list(Food.Code,Is_Industry)]
  colnames(final_sample)[3] <- "text" 
}

# Output as single-column CSV 
final_abstracts <- final_sample[,"text"]
write.csv(final_abstracts, "mturk_selection_allfood.csv", row.names=FALSE)

# Grains only sample 
final_abstracts_grain <- final_sample[Food.Code %in% 1:22, "text"]
write.csv(final_abstracts_grain, "mturk_selection_grains.csv", row.names=FALSE)
