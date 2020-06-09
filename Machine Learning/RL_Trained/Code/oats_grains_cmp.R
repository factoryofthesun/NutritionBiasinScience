#==============================================================================
# Comparing the prediction results of the old oats model and the new 
# grains-added model. 
#==============================================================================
rm(list=ls())
library(ggplot2)
library(stargazer)
library(data.table)
library(dplyr)

setwd("/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/Machine Learning/RL_Trained")


new_pred <- setDT(read.csv("Predictions/full_predictions_AdamW_grains.csv"))
old_pred <- setDT(read.csv("Predictions/Old/full_predictions_AdamW.csv"))

merged_pred <- merge(new_pred, old_pred, by=c("Food.Code", "Abstract"))

# Old predictions had data errors for green beans 
non_new <- new_pred[!(Abstract.Code %in% merged_pred$Abstract.Code.x)]

merged_pred$Diff_Pred <- merged_pred$Prediction.x != merged_pred$Prediction.y
merged_diff <- merged_pred[Diff_Pred == T]

# Checking validation on oats 
oats_tagged <- read.csv("Data/mturk_train.csv")
oats_tagged$Label <- as.numeric(oats_tagged$count_pos >= 2)

find_substr_match <- function(row){
  search <- grepl(row['inputtext'], oats_preds$Abstract, fixed=TRUE)
  ind <- which(search, arr.ind=T)
  return(data.frame("Abstract.Code" = oats_preds$Abstract.Code.x[ind],"Abstract" = oats_preds$Abstract[ind],"Prediction_GrainsModel" = oats_preds$Prediction.x[ind], 
                    "Prediction_OatsModel" = oats_preds$Prediction.y[ind], "Label" = row['Label']))
}

oats_preds <- merged_pred[Food.Code ==13]
oats_merge <- apply(oats_tagged, 1, find_substr_match)
oats_merge <- bind_rows(oats_merge)

oats_merge$Grains_Correct <- oats_merge$Prediction_GrainsModel == oats_merge$Label
oats_merge$Oats_Correct <- oats_merge$Prediction_OatsModel == oats_merge$Label
sum(oats_merge$Grains_Correct)
sum(oats_merge$Oats_Correct)

oats_missing <- oats_preds[!(Abstract.Code.x %in% oats_merge$Abstract.Code)]

# Distribution of positive vs non-positive classifications among the differences 
cnames <- colnames(new_pred)
diff_new <- merged_diff[,c(3,1,4,2,5:7)]
diff_old <- merged_diff[,c(8,1,9,2,10:12)]
colnames(diff_new) <- cnames
colnames(diff_old) <- cnames

diff_new$Model <- "New"
diff_old$Model <- "Old"

diff_toplot <- rbind(diff_old, diff_new)
diff_toplot$Prediction <- as.factor(diff_toplot$Prediction)

ggplot(data=diff_toplot, aes(fill=Prediction,x=Model)) + geom_bar(position="dodge", stat="count") +
  labs(title="Model Label Differenes Count")
ggsave("Plots/compare_predictions.png")

# Distribution of differences among food groups 
merged_grouped <- merged_pred[,.(Tot=.N, Diff_Tot=sum(Diff_Pred)), by=list(Food.Code, Food.Name.x)]
merged_grouped$Perc_Diff <- merged_grouped$Diff_Tot/merged_grouped$Tot
  
ggplot(data=merged_grouped, aes(x=Food.Code, y=Perc_Diff)) + geom_bar(position="dodge", stat="identity") + 
  labs(title="Model Label Differences by Food Group", y="% Diff")
ggsave("Plots/pred_diffs_foodgroup.png")

# Investigate the outlier food group 
diff_grouped <- merged_diff[,.(Counts=.N), by=list(Food.Code, Food.Name.x)][order(-Counts)]

# Export abstracts with different predictions 
diff_out <- merged_pred[,list(Food.Code, Abstract,Food.Name.x, Prob_NotPositive.x, Prob_NotPositive.y, Prob_Positive.x,
                              Prob_Positive.y, Prediction.x, Prediction.y, Diff_Pred)]
colnames(diff_out) <- c("Food.Code", "Food.Name", "Abstract","New_Prob_NotPositive", "Old_Prob_NotPositive", 
                        "New_Prob_Positive", "Old_Prob_Positive", "New_Prediction", "Old_Prediction", "Diff")
write.csv(diff_out, "Predictions/predictions_comparison.csv", row.names=F)


