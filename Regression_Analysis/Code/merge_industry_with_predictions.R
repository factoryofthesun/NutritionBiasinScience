rm(list = ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)
setwd("~/Documents/Anita_Rao_RP/Rao-IndustryFoodScience/Industry_Tagging")

# Abstracts to sample from 
# Use the output file from the most recent ML prediction
predictions <- setDT(read.csv("../Machine_Learning/full_predictions_AdamW.csv"))
industry_tags <- setDT(read.csv("./Output/wos_indtagged_v4.csv"))

abstracts_full <- merge(predictions, industry_tags[,c(1, 4:84)], 
                        by="Abstract.Code") 
write.csv(abstracts_full, "../abstracts_full_raw.csv", row.names=FALSE)
