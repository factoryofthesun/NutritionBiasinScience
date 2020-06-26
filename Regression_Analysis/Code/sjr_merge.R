#' ---
#' author: "Richard Liu"
#' output: pdf
#' description: Script to merge sjr weights with the scraped jcr scores 
#' ---

rm(list=ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)
library(gridExtra)
library(readxl)
setwd("/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/Regression_Analysis")

jcr_dt <- setDT(read.csv("jcr_impact_factors.csv"))
sjr_dt <- setDT(read_excel("sjr_journal_weights.xlsx", col_types=c("numeric", "numeric", rep("text", 5), 
                                                                   rep("numeric", 6), rep("text", 7))))

# SJR is in European format -- need to clean up titles and values
sjr_dt$SJR <- gsub(",", "", sjr_dt$SJR, fixed=TRUE)
sjr_dt$SJR <- as.numeric(sjr_dt$SJR)/1000

# Standardize journal names 
sjr_dt$Clean_Title <- gsub("[[:punct:]]", " ", sjr_dt$Title)
sjr_dt$Clean_Title <- tolower(trimws(gsub("\\s\\s+", " ", sjr_dt$Clean_Title))) # Remove extra spaces

jcr_dt$Clean_Title <- gsub("[[:punct:]]", " ", jcr_dt$Journal)
jcr_dt$Clean_Title <- tolower(trimws(gsub("\\s\\s+", " ", jcr_dt$Clean_Title))) 

# Looks like the downloaded coverage from SJR isn't good either...will have to scrape for the
# remaining journal names 
merge_out <- merge(sjr_dt[,c("Rank", "Title", "SJR", "H index", "Coverage", "Clean_Title")], 
                   jcr_dt, by="Clean_Title", all.y = T)
colnames(merge_out)[c(2,10)] <- c("SJR_Rank", "Impact_Year")
  
  
