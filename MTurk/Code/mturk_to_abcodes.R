rm(list = ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)
setwd("/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/MTurk")

wos_wide <- setDT(read.csv("../WebOfScience/Industry_Tagging/Outputs/wos_indtagged_final_wide.csv"))

# ======== Compute relatedness measure for individual categories =========
# Read in MTurk tagged data 
oats_tagged <- read.csv("../Machine Learning/RL_Trained/Data/mturk_train.csv")
oats_tagged$polarity <- as.numeric(oats_tagged$count_pos >= 2)

grains_tagged <- setDT(read.csv("grains_formatted.csv"))
grains_tagged$polarity <- as.numeric(grains_tagged$Positive >= 2)

# Merge back with full dataset 
# Need to use apply with custom function to conduct substring-based merge for oats
wos_oats_search <- wos_wide[Food.Code == 13]
find_substr_match <- function(row){
  search <- grepl(row['inputtext'], wos_oats_search$AB, fixed=TRUE)
  ind <- which(search, arr.ind=T)
  return(data.frame('Abstract.Code' = wos_oats_search$Abstract.Code[ind], "Food.Code" = wos_oats_search$Food.Code[ind],
                    "Food.Name" = wos_oats_search$Food.Name[ind],"Abstract" = wos_oats_search$AB[ind], "Prediction" = row['polarity']))
}

oats_match <- apply(oats_tagged, 1, find_substr_match)
wos_oats <- bind_rows(oats_match)

wos_grains <- setDT(merge(wos_wide[Food.Code <= 22 & Food.Code != 13,list(Abstract.Code, Food.Code, Food.Name, AB)], 
                          grains_tagged[,list(Input.text, polarity)], by.x='AB', by.y='Input.text'))
colnames(wos_grains) <- c("Abstract", "Abstract.Code", "Food.Code", "Food.Name", "Prediction")
wos_full <- setDT(rbind(wos_grains, wos_oats)) # row bind oats and grains  
wos_full <- distinct(wos_full)

write.csv(wos_full, "labelled_with_codes.csv", row.names=F)
