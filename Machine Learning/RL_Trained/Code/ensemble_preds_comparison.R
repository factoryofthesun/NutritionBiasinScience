#==============================================================================
# Comparing the prediction results of the latest model and the ensemble model
#==============================================================================
rm(list=ls())
library(ggplot2)
library(stargazer)
library(data.table)
library(dplyr)

setwd("/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/Machine Learning/RL_Trained")


new_pred <- setDT(read.csv("Predictions/full_predictions_AdamW_grains.csv"))
ensemble_pred <- setDT(read.csv("Predictions/AdamW_grains_preds_ensemble.csv"))

merged_pred <- merge(new_pred, ensemble_pred, by=c("Food.Code", "Abstract.Code"))

merged_diffs <- merged_pred[Committee_Vote_Pred != Prediction | Committee_Avg_Pred != Prediction]

# Based on a manual inspection, the commitee vote model seems better
sum(merged_diffs$Committee_Vote_Pred == 1)/nrow(merged_diffs) # Proportion of positive label diff

merged_diffs$Abstract.y <- NULL
merged_diffs$Food.Name.y <- NULL

write.csv(merged_diffs, "Predictions/ensemble_preds_comparison.csv", row.names=F)



