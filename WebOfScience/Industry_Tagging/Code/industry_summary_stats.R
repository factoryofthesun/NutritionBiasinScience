rm(list = ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)
setwd("/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/WebOfScience/Industry_Tagging")

ind_tag_df <- read.csv('Outputs/wos_indtagged_final_long.csv')

#Industry Funded Article Counts 
sum(ind_tag_df$Is_Industry == 1) #Total counts 
nrow(ind_tag_df) #Total number of articles 
sum(ind_tag_df$FU_stripped_lower != " missing ") #Total number of articles excl. missing funding source 
sum(ind_tag_df$Is_Industry == 1 & ind_tag_df$Food.Code == 13) #Oat counts 
sum(ind_tag_df$Food.Code == 13) #Total oats articles
sum(ind_tag_df$Food.Code == 13 & ind_tag_df$FU_stripped_lower != " missing ") #Total oat counts excl missing funding source

#Known industry frequency counts 
ind_tag_df$Companies <- trimws(ind_tag_df$Companies)
industry_matches <- ind_tag_df$Companies
industry_matches <- industry_matches[industry_matches != ""]

#Group by count unique values 
freq_table <- as.data.frame(table(industry_matches))
freq_table <- freq_table[order(-freq_table$Freq),]
colnames(freq_table)[1] <- "Company Name"

write.table(freq_table, "Outputs/industry_freq_counts.txt", row.names = FALSE)
nrow(freq_table) #Count of unique companies found 

#Frequency counts for oats 
oats_freq_table <- as.data.frame(table(ind_tag_df[which(ind_tag_df$Food.Code == 13), "Companies"]))
oats_freq_table <- oats_freq_table[order(-oats_freq_table$Freq),]
oats_freq_table <- oats_freq_table[-1,]
colnames(oats_freq_table)[1] <- "Company Name"
write.table(oats_freq_table, "Outputs/oats_industry_freq.txt", row.names = FALSE)

#Industry counts grouped by food category 
#Use the wide dataframe here to get accurate per-abstract counts 
ind_tag_wide <- read.csv('Outputs/wos_indtagged_final_wide.csv')

ind_tag_wide$Non_Missing_Funding <- ind_tag_wide$FU_stripped_lower != " missing "
ind_tag_wide$Non_Missing_Abstracts <- ind_tag_wide$AB != ""

foodcat_ind_freq <- ind_tag_wide %>% group_by(Food.Code, Food.Name) %>%
  summarise(total_raw = n(), total_abstracts = sum(Non_Missing_Abstracts), total_funding = sum(Non_Missing_Funding), 
            industry_suffix = sum(Is_Industry_Suf), industry_top100 = sum(Is_Industry_Top100), industry_b2c = sum(Is_Industry_B2C), 
            industry_suff_company = sum(Is_Industry_Suf_Company), industry_manual = sum(Is_Industry_Manual), 
            industry_us = sum(Is_Industry_US) , industry_total = sum(Is_Industry))

#Top Five Industry Names for each food group 
foodcat_ind <- subset(ind_tag_df, ind_tag_df$Companies != "")
foodcat_ind <- foodcat_ind[,c("Food.Code", "Food.Name", "Companies")]
foodcat_topfive <- foodcat_ind %>% group_by(Food.Code, Food.Name, Companies) %>% 
  summarise(counts = n()) %>% top_n(n = 5, wt = counts) %>% arrange(Food.Code, desc(counts)) %>%
  do(head(., 5)) %>% mutate(freq_rank = 1:n()) 
write.table(foodcat_topfive, "Outputs/topfive_byfood_industry.txt", row.name = FALSE)

#Pivot to wide format 
topfive_wide <- pivot_wider(foodcat_topfive, names_from=freq_rank, 
                            values_from=c(Companies, counts))

# Top Five B2C Companies for each food group
foodcat_b2c <- subset(ind_tag_df, ind_tag_df$Is_Industry_B2C == 1)
foodcat_b2c <- foodcat_b2c[, c("Food.Code", "Food.Name", "Companies")]
foodcat_b2c_topfive <- foodcat_b2c %>% group_by(Food.Code, Food.Name, Companies) %>% 
  summarise(counts = n()) %>% top_n(n = 5, wt = counts) %>% arrange(Food.Code, desc(counts)) %>%
  do(head(., 5)) %>% mutate(freq_rank = 1:n()) 
write.table(foodcat_b2c_topfive, "Outputs/topfive_byfood_b2c.txt", row.name = FALSE)

#Pivot to wide format 
topfive_wide_b2c <- pivot_wider(foodcat_b2c_topfive, names_from=freq_rank, 
                            values_from=c(Companies, counts))
colnames(topfive_wide_b2c) <- c(colnames(topfive_wide_b2c[1:2]), paste("B2C", colnames(topfive_wide_b2c)[3:12], sep="_")) # Change column names to distinguish B2C tag 

#Append to total food cat dataframe 
foodcat_tot <- merge(foodcat_ind_freq, topfive_wide[-2], by = "Food.Code", all.x = TRUE)
foodcat_tot <- merge(foodcat_tot, topfive_wide_b2c[-2], by = 'Food.Code', all.x = TRUE)
  
write.csv(foodcat_tot, "Outputs/Food Category Summary Statistics_v5.csv", row.names= FALSE)  
