# =====================================================================
# Author: Richard Liu
# Description: Bonus distribution - if all 5 workers responded the same way. 
# Output: A CSV which contains the command-line commands to send bonuses 
# =====================================================================
rm(list = ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)
setwd("/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/MTurk")

grains_tagged <- setDT(read.csv("Batch_Results/wholegrains_batch_results.csv"))

# Group by abstract and count each response 
grain_analysis <- dcast(grains_tagged[,c("HITId", "Answer.sentiment.label")], 
                        HITId~Answer.sentiment.label, length)
grain_consensus <- grain_analysis[Negative == 5 | Positive == 5 | Neutral == 5,]
worker_consensus <- merge(grain_consensus, grains_tagged[,list(HITId, WorkerId, AssignmentId)], by="HITId")
worker_count <- worker_consensus[,.(Count=.N), by=WorkerId] # Check duplicate workers 

# Terminal string format: aws mturk send-bonus --worker-id --bonus-amount --assignment-id --reason
bonusString <- function(row){
  return(paste("aws mturk send-bonus --worker-id",row['WorkerId'],"--bonus-amount","0.15", 
           "--assignment-id",row['AssignmentId'],'--reason "Accuracy bonus"'))
}

bonuses <- apply(worker_consensus, 1, bonusString)
out_df <- data.frame("Command" = bonuses)
write.csv(out_df, "bonus_commands.csv")
