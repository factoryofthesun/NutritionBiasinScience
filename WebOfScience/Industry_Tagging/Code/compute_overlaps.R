rm(list = ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)
setwd("/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/WebOfScience/Industry_Tagging/Outputs")

industry_tags <- setDT(read.csv("wos_indtagged_final_wide.csv"))
industry_tags <- industry_tags[AB != "" & !is.na(AB)]
food_codes <- unique(industry_tags$Food.Code)

overlap <- c()
internal_dup <- c()
for (i in food_codes){
  food_i <- as.character(industry_tags[Food.Code == i, AB])
  internal_dup <- c(internal_dup, sum(duplicated(food_i)))
  food_i <- unique(food_i)
  # Remove internal duplicates
  for (j in food_codes){
    food_j <- as.character(industry_tags[Food.Code == j, AB])
    food_j <- unique(food_j)
    food_intersect <- intersect(food_i, food_j)
    perc <- length(food_intersect)/length(food_i)
    overlap <- c(overlap, perc)
  }
}

overlap_mat <- matrix(overlap, nrow=163, ncol=163, byrow=TRUE)
colnames(overlap_mat) <- food_codes
rownames(overlap_mat) <- food_codes

write.csv(overlap_mat, "../overlap_matrix.csv")

names(internal_dup) <- food_codes
which(internal_dup > 0)

dup_example <- industry_tags[Food.Code == 12, .(Count = .N), by = AB]
