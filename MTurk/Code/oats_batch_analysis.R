rm(list=ls())
library(ggplot2)
library(stargazer)
library(data.table)
library(dplyr)
setwd("~/Documents/Anita_Rao_RP/Rao-IndustryFoodScience/MTurk")

mturk_df <- read.csv("oats_batch_results.csv")
mturk_dt <- setDT(mturk_df)

# Check for unreliable workers 
worker_answers <- dcast(mturk_dt, WorkerId ~ Answer.sentiment.label, fun=length)
worker_avg_times <- mturk_dt[,.(Avg_Time = mean(WorkTimeInSeconds)), by=WorkerId]
worker_dt <- merge(worker_answers, worker_avg_times, by="WorkerId")

write.csv(worker_dt, "worker_avg_times.csv", row.names=FALSE)
