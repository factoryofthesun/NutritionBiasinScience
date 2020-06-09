#==============================================================================
# Author: Richard Liu 
# Description: Correlation analysis of the "unrelated" classification and the 
# research categories recorded on WoS
#==============================================================================

rm(list = ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)
setwd("/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/MTurk")

wos_wide <- read.csv("../WebOfScience/Industry_Tagging/Outputs/wos_indtagged_final_wide.csv")

# ======== Compute relatedness measure for individual categories =========
wos_long <- wos_wide %>% separate_rows(SC, sep=";")
wos_long$SC <- trimws(wos_long$SC)

# Read in MTurk tagged data 
oats_tagged <- read.csv("../Machine Learning/RL_Trained/Data/mturk_train.csv")
oats_tagged$Unrelated_80Perc <- oats_tagged$count_unrelated >= 4
oats_tagged$Unrelated_All <- oats_tagged$count_unrelated == 5

grains_tagged <- setDT(read.csv("Batch_Results/wholegrains_batch_results.csv"))
grains_grouped <- grains_tagged[,.(Counts = .N), by=list(Input.text, Answer.sentiment.label)] 
grains_grouped <- grains_grouped[,.(Perc_Unrelated = .SD[Answer.sentiment.label=="Unrelated", Counts]/sum(Counts)), by=list(Input.text)]
grains_grouped$Unrelated_80Perc <- grains_grouped$Perc_Unrelated >= 0.8
grains_grouped$Unrelated_All <- grains_grouped$Perc_Unrelated == 1

# Merge back with full dataset 
# Need to use apply with custom function to conduct substring-based merge for oats
wos_sub <- wos_long[,c("AB", "SC")]
wos_sub <- distinct(wos_sub) # Remove duplicates 

find_substr_match <- function(row){
  search <- grepl(row['inputtext'], wos_sub$AB, fixed=TRUE)
  ind <- which(search, arr.ind=T)
  return(data.frame("AB" = wos_sub$AB[ind],"SC" = wos_sub$SC[ind], "Unrelated_80Perc" = row['Unrelated_80Perc'], 
                    "Unrelated_All" = row['Unrelated_All']))
}

oats_match <- apply(oats_tagged, 1, find_substr_match)
wos_oats <- bind_rows(oats_match)
wos_oats$Unrelated_80Perc <- as.logical(wos_oats$Unrelated_80Perc)
wos_oats$Unrelated_All <- as.logical(wos_oats$Unrelated_All)

wos_grains <- setDT(merge(wos_sub, grains_grouped[,list(Input.text, Unrelated_80Perc, Unrelated_All)], by.x='AB', by.y='Input.text'))
length(unique(wos_grains[is.na(Unrelated_All), AB])) # Make sure all abstracts were merged

wos_full <- setDT(rbind(wos_grains, wos_oats)) # row bind oats and grains  
wos_full$SC <- trimws(wos_full$SC)
wos_full$AB <- wos_full$AB
wos_full <- distinct(wos_full)
wos_sc <- wos_full[,.(Count_Total = .N, Count_Unrelated_80Perc = nrow(.SD[Unrelated_80Perc==T]), Perc_Unrelated_80Perc = nrow(.SD[Unrelated_80Perc == T])/.N, 
                      Count_Unrelated_All = nrow(.SD[Unrelated_All==T]), Perc_Unrelated_All = nrow(.SD[Unrelated_All==T])/.N), by=SC][order(Perc_Unrelated_80Perc)] # Group by SC and compute % unrelated 

write.csv(wos_sc, "research_area_related_single.csv")

# Sanity check: chi-square test of significance
chisq.test(wos_full$SC, wos_full$Unrelated_80Perc)
chisq.test(wos_full$SC, wos_full$Unrelated_All)

library(rcompanion)
cramerV(wos_full$SC, wos_full$Unrelated_80Perc, bias.correct=T) 
cramerV(wos_full$SC, wos_full$Unrelated_All, bias.correct=T) 

# ======== Compute relatedness measure grouping on existing research area cross-sections =========
wos_full <- wos_full[order(AB, SC)]
wos_full_wide <- wos_full[,.(SC = paste(SC, collapse="; ")), by=list(AB, Unrelated_80Perc, Unrelated_All)]
wos_sc_wide <- wos_full_wide[,.(Count_Total = .N, Count_Unrelated_80Perc = nrow(.SD[Unrelated_80Perc==T]), Perc_Unrelated_80Perc = nrow(.SD[Unrelated_80Perc == T])/.N, 
                                Count_Unrelated_All = nrow(.SD[Unrelated_All==T]), Perc_Unrelated_All = nrow(.SD[Unrelated_All==T])/.N), by=SC][order(Perc_Unrelated_80Perc)]

write.csv(wos_sc_wide, "research_area_related_groups.csv")

# Sanity check: chi-square test of significance
chisq.test(wos_full_wide$SC, wos_full_wide$Unrelated_80Perc)
chisq.test(wos_full_wide$SC, wos_full_wide$Unrelated_All)

cramerV(wos_full_wide$SC, wos_full_wide$Unrelated_80Perc, bias.correct=T) 
cramerV(wos_full_wide$SC, wos_full_wide$Unrelated_All, bias.correct=T) 

