#==============================================================================
# Author: Richard Liu 
# Description: Script to compute and visualize the distribution of industry vs non-industry 
# abstracts among the food science journals. 
# Evidence for publication bias confounded with industry effect: 
#   Differing distribution of industry articles among journals, as that could mean that 
#   published industry-funded research could be more positive due to the publication effect of 
#   these journals which favor positive results. 
#   Can recover the industry effect by making a case for industry-influenced selection into these 
#   journals, but hard to see how we'd be able to even collect the data for that. 
#   
#==============================================================================

rm(list = ls())
library(dplyr)
library(tidyr)
library(data.table)
library(stringr)
library(gridExtra)
library(xlsx)
setwd("/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/Regression_Analysis")

abstract_dt <- setDT(read.csv("../WebOfScience/Industry_Tagging/Outputs/wos_indtagged_final_wide_FEclean.csv"))

length(unique(abstract_dt$Journal))

# Percentages by publication 
abstract_grouped <- abstract_dt[,.(Counts = .N), by = list(Journal, Is_Industry)]
abstract_grouped[,Perc_Industry_Status := Counts/sum(Counts), by = Is_Industry]
abstract_grouped <- abstract_grouped[order(Is_Industry, Perc_Industry_Status)]
abstract_grouped$Journal_ID <- as.numeric(abstract_grouped$Journal)

# Plot histograms 
ggplot(abstract_grouped, aes(x=Journal_ID, y=Perc_Industry_Status)) + geom_bar(stat="identity") + 
  facet_wrap(~Is_Industry, ncol=1) + labs(x="Journal_ID", y="Percent", title="Journal Distribution by Industry Label")
ggsave("Graphs/journal_distribution.png")

# Top 5 journals for each industry label 
top_journals <- abstract_grouped[order(Is_Industry, -Perc_Industry_Status), .SD[1:5], by=Is_Industry]
write.csv("top_journals.csv", row.names=FALSE)

# Journal distribution looks consistent - check top 3 positivity proportion 
# Positivity concentration within top 3 journals 
top3 <- top_journals$Journal[1:3]
top3_abstracts <- abstract_dt[Journal %in% top3]
top3_abstracts <- top3_abstracts[order(Journal),.(Perc_Positive = sum(Prediction)/.N), by=list(Journal, Is_Industry)]

# Journal of Dairy Science has large industry source proportion - check food groups that submit to it
dscience_abstracts <- abstract_dt[Journal=="JOURNAL OF DAIRY SCIENCE"]
dscience_foods <- dscience_abstracts[,.(Counts = .N), by=Food.Code][order(Counts)]

# Food Code 108, no surprises there 

"industry_abstracts <- abstract_dt[Is_Industry == 1]
ind_plot <- ggplot(industry_abstracts, aes(x=Journal)) + geom_bar(aes(y=(..count..)/sum(..count..))) + 
  scale_y_continuous(labels=scales::percent)

nonindustry_abstracts <- abstract_dt[Is_Industry == 0]
nonind_plot <- ggplot(nonindustry_abstracts, aes(x=Journal)) + geom_bar(aes(y=(..count..)/sum(..count..))) + 
  scale_y_continuous(labels=scales::percent)

grid.arrange(ind_plot, nonind_plot, ncol=1)"

# ============ Test for distributional difference among journals ==========
journal_distribution <- abstract_dt
journal_distribution[FU_stripped_lower == " missing ", Is_Industry := 2]
journal_distribution <- journal_distribution[,.(Counts=.N), by=list(Journal,Is_Industry)]
journal_wide <- pivot_wider(journal_distribution, names_from=Is_Industry,values_from=Counts)
journal_wide[is.na(journal_wide)] <- 0
colnames(journal_wide) <- c("Journal", "Non_Ind", "Missing", "Ind")

journal_wide <- journal_wide[order(journal_wide$Journal),c("Journal", "Non_Ind", "Ind", "Missing")]
levels(journal_wide$Journal)[levels(journal_wide$Journal) == ""] <- "Missing"

write.xlsx(journal_wide, "Distribution_Analysis/pub_journal.xlsx")

# Statistical test (chi-square)
chisq.test(abstract_dt$Journal, abstract_dt$Is_Industry)

# Post hoc test
library(chisq.posthoc.test)
library(matrixStats)
journal_wide$Tot <- apply(journal_wide[,c(2:4)], 1, sum) # Remove any cases where total sum of journal frequency is <10
journal_wide <- journal_wide[journal_wide$Tot >=10, ]
rownames(journal_wide) <- journal_wide$Journal
journal_wide$Journal <- NULL
journal_wide$Tot <- NULL 
posthoc <- chisq.posthoc.test(journal_wide)

write.csv(posthoc, "Distribution_Analysis/journal_posthoc.csv", row.names=F)



