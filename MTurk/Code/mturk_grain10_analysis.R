rm(list = ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)
library(ggplot2)
setwd("/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/MTurk/")

grain_results <- setDT(read.csv("Batch_Results/wholegrains_batch_results.csv"))
grain_analysis <- dcast(grain_results[,c("Input.text", "Answer.sentiment.label")], 
                         Input.text~Answer.sentiment.label, length)

mode_fun <- function(x) unique(x)[which.max(tabulate(match(x,unique(x))))]
quality_checks <- grain_results[,list(Input.text, Answer.quality.check.1)][,
                                .(Health_Check = mode_fun(Answer.quality.check.1)), by=Input.text]

grain_analysis <- setDT(merge(grain_analysis, quality_checks, by="Input.text"))

grain_analysis[,Classification := ifelse(Unrelated > 3, "Unrelated", ifelse(Positive >= 3, "Positive", "Non-Positive"))]

write.csv(grain_analysis, "grains_formatted.csv")
ggplot(grain_analysis, aes(x=Classification, fill = Classification)) + geom_bar(stat= "count") + 
  labs(title="Abstract Classification Counts")

ggsave("Plots/grains_classifications.png")
