rm(list = ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)
setwd("/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/MTurk")

mturk_sample <- read.csv("mturk_selection_grains.csv", stringsAsFactors = F)
mturk_vec <- unname(unlist(mturk_sample))
mturk_vec <- mturk_vec[!duplicated(mturk_vec)] # Drop duplicates 
length(mturk_vec) <- ceiling(length(mturk_vec)/10) * 10 # Set to multiple of 10 
mturk_vec <- mturk_vec %>% replace_na("Freebie. Go ahead and input any response before submitting.") # Replace NA values with special instructions 
unique_mturk_mat <- as.data.frame(matrix(mturk_vec, ncol=10))
colnames(unique_mturk_mat) <- gsub("V", "text", colnames(unique_mturk_mat))

write.csv(unique_mturk_mat, "mturk_selection_grains_unique.csv", row.names=F)
