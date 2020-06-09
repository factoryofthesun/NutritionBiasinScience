rm(list = ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)
setwd("/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/WebOfScience/Industry_Tagging")

ind_tag_df <- read.csv('Temp/wos_indtagged_long_temp.csv')

#Extract company names from the suffix search 
ind_tag_df$Suffix_stripped <- gsub("\\s", "", ind_tag_df$Suffix_Match)
ind_tag_df$Suffix_stripped <- tolower(paste0(" ", ind_tag_df$Suffix_stripped, " "))

extract_name <- function(i){
  if (ind_tag_df$Suffix_Match[i] != ""){
    to_ret <- str_extract(ind_tag_df$FU_stripped_lower[i], paste0("([a-z0-9\\s]+)(?=", ind_tag_df$Suffix_stripped[i], ")"))
  }
  else{
    to_ret <- ""
  }
  return(to_ret)
}

ind_tag_df$Suff_Company <- sapply(1:nrow(ind_tag_df), extract_name)

#Strip whitespaces from top100 and US/UK companies match 
ind_tag_df$Top100_Match <- trimws(as.character(ind_tag_df$Top100_Match))
ind_tag_df$US_Match <- trimws(as.character(ind_tag_df$US_Match))
ind_tag_df$UK_Match <- trimws(as.character(ind_tag_df$UK_Match))
ind_tag_df$Suff_Company <- trimws(as.character(ind_tag_df$Suff_Company))
ind_tag_df$Manual_Match <- trimws(as.character(ind_tag_df$Manual_Match))

# Remove excluded company names or anything containing 'university'
exclude_suffix_extraction <- c('brazilian', 'breeding', 'center for food', 'research', 'the', 'lebanese', 'north carolina', 'global',
                               'scientific and technical personnel service the','italian', 'international', 'dairy food', 'quality control',
                               'bioproducts', 'dutch', "research and development", "scientists", 'pn ii', 'biodiversity', 'iaf', 'fit',
                               'framework 2000 2006 and', 'fit')
exclude_keyword <- c('university', 'research program', 'ohio agricultural')

ind_tag_df[grepl(paste(exclude_keyword, collapse = "|"), ind_tag_df$Suff_Company), "Suff_Company"] <- ""
ind_tag_df[ind_tag_df$Suff_Company %in% exclude_suffix_extraction,"Suff_Company"] <- ""
ind_tag_df[is.na(ind_tag_df$Suff_Company), "Suff_Company"] <- ""

length(ind_tag_df$Suff_Company[!is.na(ind_tag_df$Suff_Company) & ind_tag_df$Suff_Company != ""])
head(ind_tag_df$Suff_Company[!is.na(ind_tag_df$Suff_Company) & ind_tag_df$Suff_Company != ""], 10)

# Combine company name columns 
ind_tag_df$Companies <- ind_tag_df$Top100_Match
ind_tag_df$Companies[ind_tag_df$Companies == ""] <- ind_tag_df[ind_tag_df$Companies == "", "US_Match"]
ind_tag_df$Companies[ind_tag_df$Companies == ""] <- ind_tag_df[ind_tag_df$Companies == "", "UK_Match"]
ind_tag_df$Companies[ind_tag_df$Companies == ""] <- ind_tag_df[ind_tag_df$Companies == "", "Suff_Company"]
ind_tag_df$Companies[ind_tag_df$Companies == ""] <- ind_tag_df[ind_tag_df$Companies == "", "Manual_Match"]

# Wipe industry label for points in which no company name extracted 
ind_tag_df$Is_Industry[ind_tag_df$Companies == "" | is.na(ind_tag_df$Companies)] <- 0 

#Consolidate known conglomerates 
ind_tag_df$Companies[grepl("coca", ind_tag_df$Companies, fixed = TRUE)] <- "coca cola" 
ind_tag_df$Companies[grepl("pepsi", ind_tag_df$Companies, fixed = TRUE)] <- "pepsi" 
ind_tag_df$Companies[grepl("dannon", ind_tag_df$Companies, fixed = TRUE)] <- "danone" 
ind_tag_df$Companies[grepl("nestle", ind_tag_df$Companies, fixed = TRUE)] <- "nestle" 
ind_tag_df$Companies[grepl("heinz", ind_tag_df$Companies, fixed = TRUE)] <- "kraft" 
ind_tag_df$Companies[grepl("kraft", ind_tag_df$Companies, fixed = TRUE)] <- "kraft" 
ind_tag_df$Companies[grepl("unilever", ind_tag_df$Companies, fixed = TRUE)] <- "unilever" 
ind_tag_df$Companies[grepl("dairy farmers", ind_tag_df$Companies, fixed = TRUE)] <- "dairy farmers" 
ind_tag_df$Companies[grepl("jbs", ind_tag_df$Companies, fixed = TRUE)] <- "jbs" 
ind_tag_df$Companies[grepl("mondelez", ind_tag_df$Companies, fixed = TRUE)] <- "mondelez" 
ind_tag_df$Companies[grepl("molson coors", ind_tag_df$Companies, fixed = TRUE)] <- "molson coors" 
ind_tag_df$Companies[grepl("keystone", ind_tag_df$Companies, fixed = TRUE)] <- "tyson" 
ind_tag_df$Companies[grepl("tyson", ind_tag_df$Companies, fixed = TRUE)] <- "tyson" 
ind_tag_df$Companies[grepl("hershey", ind_tag_df$Companies, fixed = TRUE)] <- "hershey" 
ind_tag_df$Companies[grepl("colgate", ind_tag_df$Companies, fixed = TRUE)] <- "colgate" 
ind_tag_df$Companies[grepl("organic valley", ind_tag_df$Companies, fixed = TRUE)] <- "organic valley" 
ind_tag_df$Companies[grepl("agropur", ind_tag_df$Companies, fixed = TRUE)] <- "agropur" 
ind_tag_df$Companies[grepl("danone", ind_tag_df$Companies, fixed = TRUE)] <- "danone" 
ind_tag_df$Companies[grepl("suntory", ind_tag_df$Companies, fixed = TRUE)] <- "suntory" 
ind_tag_df$Companies[grepl("kellog", ind_tag_df$Companies, fixed = TRUE)] <- "kellog" 

ind_tag_v4 <- setDT(ind_tag_df[,c(1:15, 86:87, 16:85)])

# Funding index within abstract groups 
write.csv(ind_tag_v4, file="Temp/wos_suff_indtagged_long.csv", row.names=FALSE) #Export 
