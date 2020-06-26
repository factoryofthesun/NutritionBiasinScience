#==============================================================================
# Main regression analysis with rolling fixed effect controls. 
# Missing funding assumed to be non-industry. 
#==============================================================================
rm(list=ls())
library(ggplot2)
library(stargazer)
library(data.table)
library(tidyr)
library(stringr)
library(dplyr)
library(rowr)
setwd("/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/Regression_Analysis")

reg_data <- setDT(read.csv('regression_data.csv'))
top25_ind_kw <- setDT(read.csv("Distribution_Analysis/subject_ind.csv"))

# Create factors for missing covariates 
reg_data[Pub_Year < 1000, Pub_Year := 0] # 0 will be missing year level
reg_data[is.na(Journal) | Journal == "", Journal := "Missing"] # "Missing" will be missing journal level 
reg_data$Missing_Keywords <- reg_data$Keywords == "" # Indicator for missing keywords 

reg_data$Food.Code <- as.factor(reg_data$Food.Code)
reg_data$Pub_Year <- as.factor(reg_data$Pub_Year)

# ============= All Food Groups Regression w/ Fixed Effects ===========

# 1) Main industry effect 
logit_1 <- glm(Prediction ~ Is_Industry, family=binomial(link="logit"), data=reg_data)
summary(logit_1)

# 2) Food Group FE 
logit_2 <- glm(Prediction ~ Is_Industry + Food.Code, family=binomial(link="logit"), data=reg_data)
summary(logit_2)  

# 3) Publication Year FE
logit_3 <- glm(Prediction ~ Is_Industry + Food.Code + Pub_Year, family=binomial(link="logit"), data=reg_data)

# 4) Publication Journal FE
logit_4 <- glm(Prediction ~ Is_Industry + Food.Code + Pub_Year + Journal, family=binomial(link="logit"), data=reg_data)

# 5) Top 25 Keywords FE 
# Need to create indicator for whether one of the keywords for the paper is one of the top 25
reg_data_long <- reg_data %>% separate_rows(Keywords, sep=';')
reg_data_long$Keywords <- trimws(reg_data_long$Keywords)
reg_data_long$Top_KW <- reg_data_long$Keywords %in% top25_ind_kw$Subject
reg_data_kw <- setDT(reg_data_long)[,.(Top_KW = max(Top_KW), N_Top_KW=sum(Top_KW)), by=setdiff(names(reg_data_long), c("Keywords", "Top_KW"))]

# Logit 
logit_5 <- glm(Prediction ~ Is_Industry + Food.Code + Pub_Year + Journal + Top_KW + Missing_Keywords, 
               family=binomial(link="logit"), data=reg_data_kw)

# 6) # Top Keywords 
logit_6 <- glm(Prediction ~ Is_Industry + Food.Code + Pub_Year + Journal + N_Top_KW + Missing_Keywords, 
               family=binomial(link="logit"), data=reg_data_kw)

# Shortened Latex output 
stargazer(logit_1, logit_2, logit_3, logit_4, logit_5, logit_6, 
          omit=c("Food.Code", "Pub_Year", "Journal"),
          omit.labels=c("Food Group FE", "Publication Year FE", "Publication Journal FE"),
          dep.var.labels = rep("Positive (ML Imputed)", 6))

# Full excel output
summ_stats <- setDT(read.csv("../WebOfScience/Industry_Tagging/Outputs/Food Category Summary Statistics_v5.csv"))
logits <- list(logit_1, logit_2, logit_3, logit_4, logit_5, logit_6)

# Loop through all logits and cbind.fill results -- merge at very end with food code stats 
pvals <- summary(logit_1)$coefficients[,4] 
tvals <- summary(logit_1)$coefficients[,3] 
pvals_df <- data.frame(names(pvals), unname(pvals))
tvals_df <- data.frame(names(tvals), unname(tvals))
colnames(pvals_df) <- c("Covariate", "P_Value1")
colnames(tvals_df) <- c("Covariate", "T_Value1")
df <- data.frame(names(logit_1$coefficients), unname(logit_1$coefficients))
colnames(df) <- c("Covariate", "Logit1")
df$Row_Order <- 1:nrow(df)
df <- merge(df, pvals_df, by="Covariate", all.x=TRUE)
df <- merge(df, tvals_df, by="Covariate", all.x=TRUE)
df <- df %>% mutate("Significance1" = case_when("P_Value1" <= 0.001 ~ "1%",
                                             "P_Value1" <= 0.01 ~ "10%",
                                             "P_Value1" <= 0.05 ~ "5%", 
                                             TRUE ~ "None")) # Document significance 
full_coeff <- setDT(df)[order(Row_Order)]
full_coeff$Row_Order <- NULL

for (i in 2:6){
  logit <- logits[[i]]
  pvals <- summary(logit)$coefficients[,4] 
  tvals <- summary(logit)$coefficients[,3] 
  sig_name <- paste0("Significance", i)
  p_name <- paste0("P_Value", i)
  t_name <- paste0("T_Value", i)
  pvals_df <- data.frame(names(pvals), unname(pvals))
  tvals_df <- data.frame(names(tvals), unname(tvals))
  colnames(pvals_df) <- c("Covariate", p_name)
  colnames(tvals_df) <- c("Covariate", t_name)
  df <- data.frame(names(logit$coefficients), unname(logit$coefficients))
  colnames(df) <- c("Covariate", paste0("Logit", i))
  df$Row_Order <- 1:nrow(df)
  df <- merge(df, pvals_df, by="Covariate", all.x=TRUE)
  df <- merge(df, tvals_df, by="Covariate", all.x=TRUE)
  df <- df %>% mutate(!!sig_name := case_when(get(p_name) <= 0.001 ~ "1%",
                                                get(p_name)  <= 0.01 ~ "10%",
                                                get(p_name)  <= 0.05 ~ "5%", 
                                                TRUE ~ "None")) # Document significance 
  dt <- setDT(df)[order(Row_Order)]
  dt$Row_Order <- NULL
  full_coeff <- merge(full_coeff, dt, by="Covariate", all.y=T, sort=F)
}


write.csv(full_coeff, "Regression/Fixed_Effects/all_food_FE_reg.csv", row.names=F)

# ============= Food Groups Interacted with Industry w/ Fixed Effects ===========
# 1) Main industry effect 
logit_1 <- glm(Prediction ~ 0 + Food.Code:Is_Industry, family=binomial(link="logit"), data=reg_data)
summary(logit_1)

# 2) Food Group FE 
logit_2 <- glm(Prediction ~ 0 + Food.Code + Food.Code:Is_Industry, family=binomial(link="logit"), data=reg_data)
summary(logit_2)  

# 3) Publication Year FE
logit_3 <- glm(Prediction ~ 0 + Food.Code + Food.Code:Is_Industry + Pub_Year, family=binomial(link="logit"), data=reg_data)

# 4) Publication Journal FE
logit_4 <- glm(Prediction ~ 0 + Food.Code + Food.Code:Is_Industry + Pub_Year + Journal, family=binomial(link="logit"), data=reg_data)

# 5) Top 25 Keywords FE 
logit_5 <- glm(Prediction ~ 0 + Food.Code + Food.Code:Is_Industry + Pub_Year + Journal + Top_KW + Missing_Keywords, 
               family=binomial(link="logit"), data=reg_data_kw)

# 6) # Top Keywords 
logit_6 <- glm(Prediction ~ 0 + Food.Code + Food.Code:Is_Industry + Pub_Year + Journal + N_Top_KW + Missing_Keywords, 
               family=binomial(link="logit"), data=reg_data_kw)

# Shortened Latex output 
tex <- capture.output(stargazer(logit_1, logit_2, logit_3, logit_4, logit_5, logit_6, 
          omit=c("Pub_Year", "Journal"),
          omit.labels=c("Publication Year FE", "Publication Journal FE"),
          dep.var.labels = rep("Positive (ML Imputed)", 6), out="Regression/Fixed_Effects/food_interaction_latex.tex"))

# Full excel output
summ_stats <- setDT(read.csv("../WebOfScience/Industry_Tagging/Outputs/Food Category Summary Statistics_v5.csv"))
logits <- list(logit_1, logit_2, logit_3, logit_4, logit_5, logit_6)

# Loop through all logits and cbind.fill results -- merge at very end with food code stats 
pvals <- summary(logit_1)$coefficients[,4] 
tvals <- summary(logit_1)$coefficients[,3] 
pvals_df <- data.frame(names(pvals), unname(pvals))
tvals_df <- data.frame(names(tvals), unname(tvals))
colnames(pvals_df) <- c("Covariate", "P_Value1")
colnames(tvals_df) <- c("Covariate", "T_Value1")
df <- data.frame(names(logit_1$coefficients), unname(logit_1$coefficients))
colnames(df) <- c("Covariate", "Logit1")
df$Row_Order <- 1:nrow(df)
df <- merge(df, pvals_df, by="Covariate", all.x=TRUE)
df <- merge(df, tvals_df, by="Covariate", all.x=TRUE)
df <- df %>% mutate("Significance1" = case_when("P_Value1" <= 0.001 ~ "1%",
                                                "P_Value1" <= 0.01 ~ "10%",
                                                "P_Value1" <= 0.05 ~ "5%", 
                                                TRUE ~ "None")) # Document significance 
full_coeff <- setDT(df)[order(Row_Order)]
full_coeff$Row_Order <- NULL

for (i in 2:6){
  logit <- logits[[i]]
  pvals <- summary(logit)$coefficients[,4] 
  tvals <- summary(logit)$coefficients[,3] 
  sig_name <- paste0("Significance", i)
  p_name <- paste0("P_Value", i)
  t_name <- paste0("T_Value", i)
  pvals_df <- data.frame(names(pvals), unname(pvals))
  tvals_df <- data.frame(names(tvals), unname(tvals))
  colnames(pvals_df) <- c("Covariate", p_name)
  colnames(tvals_df) <- c("Covariate", t_name)
  df <- data.frame(names(logit$coefficients), unname(logit$coefficients))
  colnames(df) <- c("Covariate", paste0("Logit", i))
  df$Row_Order <- 1:nrow(df)
  df <- merge(df, pvals_df, by="Covariate", all.x=TRUE)
  df <- merge(df, tvals_df, by="Covariate", all.x=TRUE)
  df <- df %>% mutate(!!sig_name := case_when(get(p_name) <= 0.001 ~ "1%",
                                              get(p_name)  <= 0.01 ~ "10%",
                                              get(p_name)  <= 0.05 ~ "5%", 
                                              TRUE ~ "None")) # Document significance 
  dt <- setDT(df)[order(Row_Order)]
  dt$Row_Order <- NULL
  full_coeff <- merge(full_coeff, dt, by="Covariate", all.y=T, sort=F)
}


write.csv(full_coeff, "Regression/Fixed_Effects/food_ind_interact_FE_reg.csv", row.names=F)

