rm(list=ls())
library(stringr)
library(data.table)
setwd("/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/WebOfScience/Industry_Tagging/Outputs")

wos_data <- setDT(read.csv('wos_indtagged_final_wide_v1.csv'))
wos_author <- wos_data %>% separate_rows(DE, sep=';')
wos_plus <- wos_data %>% separate_rows(ID, sep=';')
wos_author$DE <- tolower(wos_author$DE)
wos_plus$ID <- tolower(wos_plus$ID)

wos_author$DE <- str_replace(wos_author$DE, '[^-a-z0-9\\s]', '')
wos_plus$ID <- str_replace(wos_plus$ID, '[^-a-z0-9\\s]', '')

tot_author <- unique(trimws(wos_author$DE))
tot_plus <- unique(trimws(wos_plus$ID))

nrow(wos_data[!is.na(DE) & DE != ""])
nrow(wos_data[!is.na(ID) & ID != ""])
