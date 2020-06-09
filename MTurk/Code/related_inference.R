#==============================================================================
# Author: Richard Liu 
# Description: Use oats/grains relatedness results as well as food group overlap measures
# to infer how many "related" abstracts will be left after stripping out 
# food groups with >=95% overlap and research category cross-section with >=88% unrelatededness.
# For "new" food groups: 
#==============================================================================
rm(list = ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)
library(ggplot2)
setwd("/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/MTurk/")

food_groups_exclude <- c(50, 62, 89, 95, 100, 109, 115)
research_groups <- setDT(read.csv("research_area_related_groups.csv"))
research_single <- setDT(read.csv("research_area_related_single.csv"))

wos_wide <- setDT(read.csv("../WebOfScience/Industry_Tagging/Outputs/wos_indtagged_final_wide.csv"))
wos_wide <- wos_wide[AB != "" & !is.na(AB) & Food.Code > 22]

wos_sub <- wos_wide[!(Food.Code %in% food_groups_exclude), list(AB, SC)] 
wos_long <- wos_sub %>% separate_rows(SC, sep=";")
wos_long$SC <- trimws(wos_long$SC)
wos_long <- distinct(wos_long)
wos_long <- wos_long[order(AB, SC)]
wos_sub_ordered <- wos_long[,.(SC = paste(SC, collapse="; ")), by=list(AB)]

# Check cross sections for full dataset
wos_full <- merge(wos_sub_ordered, research_groups[,list(SC, Perc_Unrelated_80Perc, Perc_Unrelated_All)], all.x = T, by = "SC") 
cross_sections <- data.table("SC" = unique(wos_full$SC))
cx_exclude <- cross_sections[c(1:3, 99)] # First 3 and last groups are data errors 
wos_full_clean <- wos_full[!(SC %in% cx_exclude$SC)] 
nrow(wos_full_clean[is.na(Perc_Unrelated_80Perc)]) # Number of abstracts with new research groups
wos_to_remove <- wos_full_clean[Perc_Unrelated_80Perc > 0.88, .(Counts = .N), by=SC] # Check groups to be removed 

# Infer unrelated percentage by averaging the individual categories
new_groups <- wos_full_clean[is.na(Perc_Unrelated_80Perc),.(Counts=.N),by=SC] 
new_groups$Group_ID <- 1:nrow(new_groups)
new_groups_long <- new_groups %>% separate_rows(SC, sep=";")
new_groups_long$SC <- trimws(new_groups_long$SC)
new_groups_long <- merge(new_groups_long, research_single[,list(SC, Perc_Unrelated_80Perc, Perc_Unrelated_All)], by="SC", all.x=T)

cat_exclude <- c("DC7UJ", "HV4OL", "IM1UP") # Exclude data errors
unknown_categories <- unique(new_groups_long[is.na(Perc_Unrelated_80Perc) & !(SC %in% cat_exclude), SC])

new_groups_long <- new_groups_long[!(SC %in% cat_exclude)]
new_groups_infer <- new_groups_long[,.(SC = paste(SC, collapse="; "), Infer_Unrelated_80Perc = mean(Perc_Unrelated_80Perc, na.rm=T), 
                                       Infer_Unrelated_All = mean(Perc_Unrelated_All, na.rm=T)),
                                    by=Group_ID]
nrow(new_groups_infer[Infer_Unrelated_80Perc >= 0.88]) # None of the predicted percentages exceed 88%

# Create summary file with all research groups, counts, and unrelated %s 
wos_summary <- wos_full_clean[,.(Counts=.N, Perc_Unrelated_80Perc = mean(Perc_Unrelated_80Perc, na.rm=T),
                                 Perc_Unrelated_All = mean(Perc_Unrelated_All, na.rm=T)), by=SC]
wos_summary <- merge(wos_summary, new_groups_infer[,list(SC, Infer_Unrelated_80Perc, Infer_Unrelated_All)],
                     by = "SC", all.x = T)
wos_summary$Inferred_Vals <- F
wos_summary[Perc_Unrelated_80Perc == "NaN", c("Perc_Unrelated_80Perc", "Perc_Unrelated_All", "Inferred_Vals") := 
              list(Infer_Unrelated_80Perc, Infer_Unrelated_All, T)]
wos_summary <- wos_summary[order(Perc_Unrelated_80Perc)][-93:-95]
wos_summary <- wos_summary[,list(SC, Counts, Perc_Unrelated_80Perc, Perc_Unrelated_All, Inferred_Vals)]
write.csv(wos_summary, "nongrains_group_summary.csv", row.names = F)

# Summary statistics 
nrow(wos_wide) # Original fruits, vegetables, dairy # excluding missing abstracts
nrow(wos_wide[!duplicated(AB)])
nrow(wos_full_clean) # Exclude food groups with >=95% overlap 
nrow(wos_full_clean) - sum(wos_to_remove$Counts) # Exclude research groups with >88% unrelated 
# These groups are: 
# Agriculture; Business & Economics; Food Science & Technology
# Agriculture; Business & Economics; Food Science & Technology; Nutrition & Dietetics	
# Chemistry; Food Science & Technology; Spectroscopy	
# Food Science & Technology; Public, Environmental & Occupational Health	

# There are no new inferred groups that can be excluded on the 88% margin 

# At what threshold does the sample drop to 50%?

# For 80% Unrelated Rule 
wos_80sample_check <- wos_summary[order(-Perc_Unrelated_80Perc)]
wos_80sample_check[,Sample_Cum := cumsum(Counts)]
which(wos_80sample_check$Sample_Cum >= sum(wos_80sample_check$Counts)/2)

# For 100% Unrelated Rule 
wos_allsample_check <- wos_summary[order(-Perc_Unrelated_All)]
wos_allsample_check[,Sample_Cum := cumsum(Counts)]
which(wos_allsample_check$Sample_Cum >= sum(wos_allsample_check$Counts)/2)

# Predict relatedness by food group 
wos_sub <- wos_wide[!(Food.Code %in% food_groups_exclude), list(Abstract.Code, Food.Code, SC)] 
wos_long <- wos_sub %>% separate_rows(SC, sep=";")
wos_long$SC <- trimws(wos_long$SC)
wos_long <- distinct(wos_long)
wos_long <- wos_long[order(Abstract.Code, Food.Code, SC)]
wos_sub_ordered <- wos_long[,.(SC = paste(SC, collapse="; ")), by=list(Abstract.Code, Food.Code)]
wos_grouped <- wos_sub_ordered[,.(Counts=.N), by=list(Food.Code,SC)]
wos_grouped$SC <- trimws(wos_grouped$SC)

wos_preds <- merge(wos_grouped, wos_summary[,list(SC, Perc_Unrelated_80Perc,Inferred_Vals)], by="SC")
wos_preds$Pred_Unrel <- round(wos_preds$Counts * wos_preds$Perc_Unrelated_80Perc)
wos_food_preds <- wos_preds[,.(N_Tot=sum(Counts), N_Unrel=sum(Pred_Unrel)), by=Food.Code]
wos_food_preds$Perc_Unrel <- wos_food_preds$N_Unrel/wos_food_preds$N_Tot

ggplot(wos_food_preds, aes(x=Food.Code, y=Perc_Unrel)) + geom_bar(position='dodge', stat="identity") + 
  labs(y="Predicted Unrelated %")

