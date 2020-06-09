#==============================================================================
# Author: Richard Liu 
# Description: Script to compute and visualize the distribution of publication dates between
# missing/non-missing funding sources and between industry/non-industry sources 
#==============================================================================

rm(list = ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)
library(gridExtra)
library(ggplot2)
setwd("/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/Regression_Analysis")

wos_data <- setDT(read.csv("../WebOfScience/Industry_Tagging/Outputs/wos_indtagged_final_wide.csv"))
wos_data$Funding_Missing <- (wos_data$FU_stripped_lower == ' missing ')
wos_data$Pub_Year <- str_extract(wos_data$PY, "\\d+") # Extract numeric values from publication year column 
wos_data$PD <- str_extract(wos_data$PD, "\\d+")
wos_data$EA <- str_extract(wos_data$EA, "\\d+")
  
wos_data$Pub_Year <- as.numeric(wos_data$Pub_Year)
wos_data$PD <- as.numeric(wos_data$PD)
wos_data$EA <- as.numeric(wos_data$EA)
wos_data[is.na(PD), PD := 0]
wos_data[is.na(EA), EA := 0]
wos_data[is.na(Pub_Year) | (Pub_Year > 0 & Pub_Year < 1000), Pub_Year := pmax(PD, EA, na.rm = TRUE)]

nrow(wos_data[Pub_Year < 1800]) # Remove all publication years before 1800 (data error)
wos_data <- wos_data[Pub_Year >= 1800]

wos_funding_grouped <- wos_data[,.(Counts = .N), by = list(Pub_Year, Funding_Missing)]
wos_funding_grouped <- wos_funding_grouped[, Perc := Counts/sum(Counts), by=Funding_Missing]
ggplot(wos_funding_grouped, aes(x=Pub_Year, y=Perc)) + geom_bar(stat="identity") + 
  facet_wrap(~Funding_Missing, ncol=1) + 
  labs(x="Publication Year", y="% Articles", title="Year of Publication by Missing Funding Status")
ggsave("Graphs/pub_year_funding.png")

wos_industry_grouped <- wos_data[, .(Counts=.N), by = list(Pub_Year, Is_Industry)]
wos_industry_grouped <- wos_industry_grouped[, Perc := Counts/sum(Counts), by=Is_Industry]
ggplot(wos_industry_grouped, aes(x=Pub_Year, y=Perc)) + geom_bar(stat="identity") + 
  facet_wrap(~Is_Industry, ncol=1) + 
  labs(x="Publication Year", y="% Articles", title="Year of Publication by Industry Status")
ggsave("Graphs/pub_year_industry.png")

# Save excel output of year distribution
wos_data_newind <- wos_data
wos_data_newind[Funding_Missing==T, Is_Industry := 2]
wos_industry_nomiss <- wos_data_newind[, .(Counts=.N), by = list(Pub_Year, Is_Industry)]
wos_industry_final <- pivot_wider(wos_industry_nomiss, names_from = Is_Industry, values_from = Counts)
wos_industry_final <- wos_industry_final[order(-wos_industry_final$Pub_Year),c("Pub_Year", "0", "1", "2")]
colnames(wos_industry_final) <- c("Publication Year", "Non_Ind", "Ind", "Missing")
wos_industry_final[is.na(wos_industry_final)] <- 0
write.xlsx(wos_industry_final, "Distribution_Analysis/pub_year.xlsx", row.names=F)

# Run pairwise Wilcox rank sum test 
kruskal.test(Pub_Year ~ Is_Industry, data=wos_data_newind)
pairwise.wilcox.test(wos_data_newind$Pub_Year, wos_data_newind$Is_Industry, p.adjust.method = "BH")


