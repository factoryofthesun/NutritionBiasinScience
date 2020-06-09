#==============================================================================
# Script to take the results-sentiment classified abstracts and perform some 
# initial analysis. 
#==============================================================================
rm(list=ls())
library(ggplot2)
library(stargazer)
library(data.table)
library(dplyr)

# Read in data 
setwd("/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/Regression_Analysis")
full_predictions <- read.csv("../Machine Learning/RL_Trained/Predictions/full_predictions_AdamW_grains.csv")
pred_dt <- setDT(full_predictions)
pred_dt <- na.omit(pred_dt) # Remove faulty na data 
pred_dt <- pred_dt[,c("Abstract.Code", "Prob_NotPositive", "Prob_Positive", "Prediction")]
  
wos_indtagged <- read.csv("../WebOfScience/Industry_Tagging/Outputs/wos_indtagged_final_wide.csv")
wos_indtagged <- setDT(wos_indtagged)

# Summary statistics data
summ_stats <- setDT(read.csv("../WebOfScience/Industry_Tagging/Outputs/Food Category Summary Statistics_v4.csv"))
summ_stats_nomiss <- rbind(summ_stats[!(Food.Code %in% c(134,166))],summ_stats[!(Food.Code %in% c(134,166))])
summ_stats_withmiss <- rbind(summ_stats, summ_stats)

# Create industry label variables 
wos_indtagged[Is_Industry==0, Industry_Labels := "Not Industry Funded"]
wos_indtagged[Is_Industry==1, Industry_Labels := "Industry Funded"]
wos_indtagged[FU=="", Industry_Labels := "Missing Funding Data"]

# Top 100 industry labels 
wos_indtagged[Is_Industry_Top100==0, Top100_Industry_Labels := "Not Top100 Industry Funded"]
wos_indtagged[Is_Industry_Top100==1, Top100_Industry_Labels := "Top100 Industry Funded"]
wos_indtagged[FU=="", Top100_Industry_Labels := "Missing Funding Data"]

industry_for_reg <- wos_indtagged[,c("Abstract.Code","Food.Code", "Food.Name","Is_Industry", "Is_Industry_Top100",
                                     "Industry_Labels", "Top100_Industry_Labels", "SO"), with=FALSE]

industry_for_reg <- na.omit(industry_for_reg) # Remove faulty na data 
colnames(industry_for_reg)[8] <- "Publication_Name"

# Create measure of "industry concentration" = # top 100 companies/# total companies
industry_counts <- industry_for_reg[,.(Tot_Industry = sum((Is_Industry)), Tot_Top100 = sum((Is_Industry_Top100))), by = Food.Code]
industry_counts$Industry_Concentration <- ifelse(industry_counts$Tot_Industry==0, 0, industry_counts$Tot_Top100/industry_counts$Tot_Industry)
all_industry_concentration <- sum(industry_counts$Tot_Top100)/sum(industry_counts$Tot_Industry) 
all_industry_concentration # Full top100 concentration

# Get final data for regression 
full_reg_df <- merge(industry_for_reg, pred_dt, by="Abstract.Code") # Output should be same length as pred_dt

full_reg_df$Prediction <- as.factor(full_reg_df$Prediction)
full_reg_df$Food.Code <- as.factor(full_reg_df$Food.Code)
full_reg_df$Is_Industry <- as.factor(full_reg_df$Is_Industry)
full_reg_df$Is_Industry_Top100 <- as.factor(full_reg_df$Is_Industry_Top100)

industry_sentiment_summary <- full_reg_df[,.(Counts=log(.N)),by=list(Industry_Labels, Prediction)]
industry_sentiment_top100_summary <- full_reg_df[,.(Counts=log(.N)),by=list(Top100_Industry_Labels, Prediction)]

# Save a separate regression data file that includes the article title + first 20 words 
# The raw text is included so it can be matched on the raw data files in the future 
industry_with_text <- wos_indtagged[,c("Abstract.Code","Food.Code", "AB", "TI","Food.Name","Is_Industry", "Is_Industry_Top100",
                                       "Industry_Labels", "Top100_Industry_Labels", "SO"), with=FALSE]
industry_with_text$AB <- substr(industry_with_text$AB, 1,200) # First 200 characters of AB
reg_data <- merge(industry_with_text, pred_dt, by="Abstract.Code", all.y = TRUE)
write.csv(reg_data, "regression_data.csv", row.names=FALSE)

# Plot of sentiment frequencies in industry vs non-industry funded research 
industry_sentiment_plot <- ggplot(data=industry_sentiment_summary, aes(x=Industry_Labels, y=Counts, fill=Prediction)) + 
  geom_bar(position="dodge", stat="identity") + labs(x="Industry Labels", y="Counts (Log)", title="Positive Abstracts by Funding Source")
industry_sentiment_plot
ggsave("Graphs/positive_counts_by_funding_allind.png")

top100industry_sentiment_plot <- ggplot(data=industry_sentiment_top100_summary, aes(x=Top100_Industry_Labels, y=Counts, fill=Prediction)) + 
  geom_bar(position="dodge", stat="identity") + theme(axis.text=element_text(size=7)) +
  labs(x="Industry Labels", y="Counts (Log)", title="Positive Abstracts by Funding Source")
top100industry_sentiment_plot
ggsave("Graphs/positive_counts_by_funding_top100ind.png")

# Exclude missing funding data for the regression analysis 
full_reg_df_nomiss <- full_reg_df[Industry_Labels != "Missing Funding Data"]
industry_counts_nomiss <- industry_counts[Food.Code %in% full_reg_df_nomiss$Food.Code] # Some food categories have no abstracts with funding data 
  
# ~~~~ Baseline logistic regession (food categories excluded) ~~~~
# P(positive) = b0 + b1 * 1_[Funding == Industry] + e 

# ===== Missing Funding Excluded =====
# All Food Categories
# All Companies  
base_logit_allind <- glm(Prediction ~ Is_Industry, family=binomial(link="logit"), data=full_reg_df_nomiss)
summary(base_logit_allind)

# Top 100 Companies 
base_logit_top100ind <- glm(Prediction ~ Is_Industry_Top100, family=binomial(link="logit"), data=full_reg_df_nomiss)
summary(base_logit_top100ind)

# Extract statistics 
base_allind_covariates <- c("Intercept", "Is_Industry")
allind_pvals <- summary(base_logit_allind)$coefficients[,4] 
allind_tvals <- summary(base_logit_allind)$coefficients[,3] 
allind_df <- data.frame(base_allind_covariates, unname(base_logit_allind$coefficients), allind_tvals, allind_pvals)
colnames(allind_df) <- c("Covariate", "All Companies", "AllInd_T","AllInd_P")

base_100ind_covariates <- c("Intercept", "Is_Top100_Industry")
top100_pvals <- summary(base_logit_top100ind)$coefficients[,4]
top100_tvals <- summary(base_logit_allind)$coefficients[,3] 
top100ind_df <- data.frame(base_100ind_covariates, unname(base_logit_top100ind$coefficients), top100_tvals, top100_pvals)
colnames(top100ind_df) <- c("Covariate", "Top 100 Companies", "Top100_T","Top100_P")
base_logit_df <- merge(allind_df, top100ind_df, by = "Covariate", all=TRUE)

# Save to excel 
write.csv(base_logit_df, file="Regression/Grains_Model/base_logit_nomissing.csv", row.names=FALSE)

# LaTeX output 
stargazer(base_logit_allind, base_logit_top100ind)

# ===== Missing Funding Assumed to be Non-Industry =====
# All Food Categories
# All Companies  
base_logit_allind <- glm(Prediction ~ Is_Industry, family=binomial(link="logit"), data=full_reg_df)
summary(base_logit_allind)

# Top 100 Companies 
base_logit_top100ind <- glm(Prediction ~ Is_Industry_Top100, family=binomial(link="logit"), data=full_reg_df)
summary(base_logit_top100ind)

# Extract statistics 
base_allind_covariates <- c("Intercept", "Is_Industry")
allind_pvals <- summary(base_logit_allind)$coefficients[,4] 
allind_tvals <- summary(base_logit_allind)$coefficients[,3] 
allind_df <- data.frame(base_allind_covariates, unname(base_logit_allind$coefficients), allind_tvals, allind_pvals)
colnames(allind_df) <- c("Covariate", "All Companies", "AllInd_T","AllInd_P")

base_100ind_covariates <- c("Intercept", "Is_Top100_Industry")
top100_pvals <- summary(base_logit_top100ind)$coefficients[,4]
top100_tvals <- summary(base_logit_allind)$coefficients[,3] 
top100ind_df <- data.frame(base_100ind_covariates, unname(base_logit_top100ind$coefficients), top100_tvals, top100_pvals)
colnames(top100ind_df) <- c("Covariate", "Top 100 Companies", "Top100_T","Top100_P")
base_logit_df <- merge(allind_df, top100ind_df, by = "Covariate", all=TRUE)

# Save to excel 
write.csv(base_logit_df, file="Regression/Grains_Model/base_logit_withmissing.csv", row.names=FALSE)

# LaTeX output 
stargazer(base_logit_allind, base_logit_top100ind)

# ~~~~ Main logistic regression (interaction b/w food category and funding source) ~~~~~
# P(positive) = b0 + b1*1_[Funding] +  FoodCat * A + FoodCat*1_[Funding] * B + e 

# ===== Missing Funding Excluded =====
# All Industries
foodcat_logit_allind <- glm(Prediction ~ 0 + Food.Code + Food.Code:Is_Industry, family=binomial(link="logit"), data=full_reg_df_nomiss)
summary(foodcat_logit_allind)

# Top 100 Industries 
foodcat_logit_top100ind <- glm(Prediction ~ 0 + Food.Code + Food.Code:Is_Industry_Top100, family=binomial(link="logit"), data=full_reg_df_nomiss)
summary(foodcat_logit_top100ind)

# Save results as excel 
allind_pvals <- summary(foodcat_logit_allind)$coefficients[,4] 
allind_tvals <- summary(foodcat_logit_allind)$coefficients[,3] 
allind_pvals_df <- data.frame(names(allind_pvals), unname(allind_pvals))
allind_tvals_df <- data.frame(names(allind_tvals), unname(allind_tvals))
colnames(allind_pvals_df) <- c("Covariate", "P_Value")
colnames(allind_tvals_df) <- c("Covariate", "T_Value")

allind_df <- data.frame(names(foodcat_logit_allind$coefficients), unname(foodcat_logit_allind$coefficients))
colnames(allind_df) <- c("Covariate", "All Companies")
allind_df$Row_Order <- 1:nrow(allind_df)
allind_df <- merge(allind_df, allind_pvals_df, by="Covariate", all.x=TRUE)
allind_df <- merge(allind_df, allind_tvals_df, by="Covariate", all.x=TRUE)
allind_df <- allind_df %>% mutate(Significance = case_when(P_Value <= 0.001 ~ "1%",
                                                           P_Value <= 0.01 ~ "10%",
                                                           P_Value <= 0.05 ~ "5%", 
                                                           TRUE ~ "None")) # Document significance 
allind_dt <- setDT(allind_df)[order(Row_Order)]
allind_dt$Industry_Concentration <- rep(industry_counts_nomiss$Industry_Concentration, 2)

allind_n <- cbind(allind_dt, summ_stats_nomiss[,list(Food.Name, total_funding, industry_total)])
colnames(allind_n)[c(9,10)] <- c("N_Sample", "N_Industry")
  
write.csv(allind_n[,c("Food.Name", "Covariate", "All Companies", "T_Value", "P_Value", "Significance", "Industry_Concentration",
                      "N_Sample", "N_Industry")], 
          file="Regression/Grains_Model/main_logit_allind_nomissing.csv", row.names=FALSE)

top100_pvals <- summary(foodcat_logit_top100ind)$coefficients[,4] 
top100_tvals <- summary(foodcat_logit_top100ind)$coefficients[,3] 
top100_pvals_df <- data.frame(names(top100_pvals), unname(top100_pvals))
top100_tvals_df <- data.frame(names(top100_tvals), unname(top100_tvals))
colnames(top100_pvals_df) <- c("Covariate", "P_Value")
colnames(top100_tvals_df) <- c("Covariate", "T_Value")

top100ind_df <- data.frame(names(foodcat_logit_top100ind$coefficients), unname(foodcat_logit_top100ind$coefficients))
colnames(top100ind_df) <- c("Covariate", "Top 100 Companies")
top100ind_df$Row_Order <- 1:nrow(top100ind_df)
top100_df <- merge(top100ind_df, top100_pvals_df, by = "Covariate", all.x=TRUE)
top100_df <- merge(top100_df, top100_tvals_df, by="Covariate", all.x=TRUE)
top100_df <- top100_df %>% mutate(Significance = case_when(P_Value <= 0.001 ~ "1%",
                                                           P_Value <= 0.01 ~ "10%",
                                                           P_Value <= 0.05 ~ "5%", 
                                                           TRUE ~ "None")) # Document significance 
top100_dt <- setDT(top100_df)[order(Row_Order)]
top100_dt$Industry_Concentration <- rep(industry_counts_nomiss$Industry_Concentration, 2)
top100_n <- cbind(top100_dt, summ_stats_nomiss[,list(Food.Name, total_funding, industry_top100)])
colnames(top100_n)[c(9,10)] <- c("N_Sample", "N_Top100")

write.csv(top100_n[,c("Food.Name", "Covariate", "Top 100 Companies", "T_Value", "P_Value", "Significance", "Industry_Concentration",
                      "N_Sample", "N_Top100")], 
          file="Regression/Grains_Model/main_logit_top100_nomissing.csv", row.names=F)

# LaTeX Output
# stargazer(foodcat_logit_allind, foodcat_logit_top100ind, out="main_logit_latex.tex")

# ~~~~ Summary Statistics of Significance ~~~~
# Food categories with significance 
allind_foodcat_sig_nomiss <- allind_dt[162:nrow(allind_dt)][Significance != "None"]
top100_foodcat_sig_nomiss <- top100_dt[162:nrow(top100_dt)][Significance != "None"]

n_sig_allind_nomiss <- nrow(allind_foodcat_sig_nomiss)
n_sig_top100_nomiss <- nrow(top100_foodcat_sig_nomiss)

write.table(allind_foodcat_sig_nomiss$Covariate, file="Regression/Grains_Model/allcompanies_foodcat_sig_nomissing.txt", 
            sep="\t", row.names=FALSE, col.names = FALSE)
write.table(top100_foodcat_sig_nomiss$Covariate, file="Regression/Grains_Model/top100_foodcat_sig_nomissing.txt", 
            sep="\t", row.names=FALSE, col.names = FALSE)
# ===== Missing Funding Assumed to be Non-Industry =====
# All Industries
foodcat_logit_allind <- glm(Prediction ~ 0 + Food.Code + Food.Code:Is_Industry, family=binomial(link="logit"), data=full_reg_df)
summary(foodcat_logit_allind)

# Top 100 Industries 
foodcat_logit_top100ind <- glm(Prediction ~ 0 + Food.Code + Food.Code:Is_Industry_Top100, family=binomial(link="logit"), data=full_reg_df)
summary(foodcat_logit_top100ind)

# Save results as excel 
allind_pvals <- summary(foodcat_logit_allind)$coefficients[,4] 
allind_tvals <- summary(foodcat_logit_allind)$coefficients[,3] 
allind_pvals_df <- data.frame(names(allind_pvals), unname(allind_pvals))
allind_tvals_df <- data.frame(names(allind_tvals), unname(allind_tvals))
colnames(allind_pvals_df) <- c("Covariate", "P_Value")
colnames(allind_tvals_df) <- c("Covariate", "T_Value")

allind_df <- data.frame(names(foodcat_logit_allind$coefficients), unname(foodcat_logit_allind$coefficients))
colnames(allind_df) <- c("Covariate", "All Companies")
allind_df$Row_Order <- 1:nrow(allind_df)
allind_df <- merge(allind_df, allind_pvals_df, by="Covariate", all.x=TRUE)
allind_df <- merge(allind_df, allind_tvals_df, by="Covariate", all.x=TRUE)
allind_df <- allind_df %>% mutate(Significance = case_when(P_Value <= 0.001 ~ "1%",
                                                           P_Value <= 0.01 ~ "10%",
                                                           P_Value <= 0.05 ~ "5%", 
                                                           TRUE ~ "None")) # Document significance 
allind_dt <- setDT(allind_df)[order(Row_Order)]
allind_dt$Industry_Concentration <- rep(industry_counts$Industry_Concentration, 2)
allind_n <- cbind(allind_dt, summ_stats_withmiss[,list(Food.Name, total_abstracts, industry_total)])
colnames(allind_n)[c(9,10)] <- c("N_Sample", "N_Industry")

write.csv(allind_n[,c("Food.Name", "Covariate", "All Companies", "T_Value", "P_Value", "Significance", "Industry_Concentration",
                      "N_Sample", "N_Industry")], 
          file="Regression/Grains_Model/main_logit_allind_withmissing.csv", row.names=FALSE)

top100_pvals <- summary(foodcat_logit_top100ind)$coefficients[,4] 
top100_tvals <- summary(foodcat_logit_top100ind)$coefficients[,3] 
top100_pvals_df <- data.frame(names(top100_pvals), unname(top100_pvals))
top100_tvals_df <- data.frame(names(top100_tvals), unname(top100_tvals))
colnames(top100_pvals_df) <- c("Covariate", "P_Value")
colnames(top100_tvals_df) <- c("Covariate", "T_Value")

top100ind_df <- data.frame(names(foodcat_logit_top100ind$coefficients), unname(foodcat_logit_top100ind$coefficients))
colnames(top100ind_df) <- c("Covariate", "Top 100 Companies")
top100ind_df$Row_Order <- 1:nrow(top100ind_df)
top100_df <- merge(top100ind_df, top100_pvals_df, by = "Covariate", all.x=TRUE)
top100_df <- merge(top100_df, top100_tvals_df, by="Covariate", all.x=TRUE)
top100_df <- top100_df %>% mutate(Significance = case_when(P_Value <= 0.001 ~ "1%",
                                                           P_Value <= 0.01 ~ "10%",
                                                           P_Value <= 0.05 ~ "5%", 
                                                           TRUE ~ "None")) # Document significance 
top100_dt <- setDT(top100_df)[order(Row_Order)]
top100_dt$Industry_Concentration <- rep(industry_counts$Industry_Concentration, 2)
top100_n <- cbind(top100_dt, summ_stats_withmiss[,list(Food.Name, total_abstracts, industry_top100)])
colnames(top100_n)[c(9,10)] <- c("N_Sample", "N_Top100")

write.csv(top100_n[,c("Food.Name","Covariate", "Top 100 Companies", "T_Value", "P_Value", "Significance", "Industry_Concentration",
                      "N_Sample", "N_Top100")], 
          file="Regression/Grains_Model/main_logit_top100_withmissing.csv", row.names=F)

# LaTeX Output
# stargazer(foodcat_logit_allind, foodcat_logit_top100ind, out="main_logit_latex.tex")

# ~~~~ Summary Statistics of Significance ~~~~
# Food categories with significance 
allind_foodcat_sig_miss <- allind_dt[164:nrow(allind_dt)][Significance != "None"]
top100_foodcat_sig_miss <- top100_dt[164:nrow(top100_dt)][Significance != "None"]

n_sig_allind_miss <- nrow(allind_foodcat_sig_miss)
n_sig_top100_miss <- nrow(top100_foodcat_sig_miss)

write.table(allind_foodcat_sig_miss$Covariate, file="Regression/Grains_Model/allcompanies_foodcat_sig_withmissing.txt", 
            sep="\t", row.names=FALSE, col.names = FALSE)
write.table(top100_foodcat_sig_miss$Covariate, file="Regression/Grains_Model/top100_foodcat_sig_withmissing.txt", 
            sep="\t", row.names=FALSE, col.names = FALSE)
