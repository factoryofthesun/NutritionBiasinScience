'''
Use the Author Keywords and supplement with Keywords Plus from data to extract the most common
topics addressed by the research.
'''

import pandas as pd
import numpy as np
import re
from nltk.corpus import words

# Read in final indudstry-tagged data
data_dir = "/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/WebOfScience/Industry_Tagging/Outputs/"
outputs_dir = "/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/Regression_Analysis/Distribution_Analysis/"

wos_df = pd.read_csv(f"{data_dir}wos_indtagged_final_wide_v1.csv")
wos_keywords = wos_df[['Abstract.Code', 'Food.Code', 'Food.Name', 'Is_Industry', 'FU_stripped_lower',
                        'DE', 'ID']]
wos_keywords.loc[wos_keywords['FU_stripped_lower'] == ' missing ', 'Is_Industry'] = 2

# Supplement missing DE (author keywords) with Keywords Plus
wos_keywords.loc[pd.isna(wos_keywords['DE']), 'DE'] = wos_keywords.loc[pd.isna(wos_keywords['DE']), 'ID']
# wos_keywords['DE'] = wos_keywords['DE'] + wos_keywords['ID']

# Split by semicolons
wos_keywords_long = wos_keywords.assign(DE=wos_keywords['DE'].str.split(';')).explode('DE')
wos_keywords_long['DE'] = wos_keywords_long['DE'].str.lower().str.replace('[^-a-z0-9\s]', '').str.strip()

# Get subject frequencies
'''
subject_freqs = wos_keywords_long[['Is_Industry', 'DE', 'ID']].groupby(['Is_Industry', 'DE'])['ID'].size().reset_index()
subject_freqs.rename(columns={"ID":"Counts", 'DE':'Subject'}, inplace=True)
subject_freqs['Is_Industry'] = subject_freqs['Is_Industry'].map({0:'Non_Ind', 1:'Ind', 2:'Missing'})

subject_wide = subject_freqs.pivot(index='Subject', columns='Is_Industry', values='Counts').reset_index()
subject_wide = subject_wide.fillna(0)
subject_wide = subject_wide[['Subject', 'Non_Ind', 'Ind', 'Missing']]
print(subject_wide.head())

subject_wide.to_excel(f"{outputs_dir}subject_distribution_raw.xlsx", index=False)

# Save 3 separate versions, taking top 25 of each industry type

# Remove subjects that contain food terms
food_terms = ['milk', 'wheat', 'barley', 'cheese', 'dairy', 'cattle', 'rice', 'maize']
subject_wide = subject_wide.loc[~subject_wide['Subject'].str.contains('|'.join(food_terms)),]

subject_nonind = subject_wide.sort_values(by='Non_Ind', ascending=False).head(25)
subject_ind = subject_wide.sort_values(by='Ind', ascending=False).head(25)
subject_miss = subject_wide.sort_values(by='Missing', ascending=False).head(25)

subject_nonind.to_csv(f"{outputs_dir}subject_nonind.csv", index=False)
subject_ind.to_csv(f"{outputs_dir}subject_ind.csv", index=False)
subject_miss.to_csv(f"{outputs_dir}subject_missing.csv", index=False)'''

# Save versions that use only author keywords/keywords plus

# Author Keywords
'''wos_keywords = wos_df[['Abstract.Code', 'Food.Code', 'Food.Name', 'Is_Industry', 'FU_stripped_lower',
                        'DE', 'ID']]
wos_keywords.loc[wos_keywords['FU_stripped_lower'] == ' missing ', 'Is_Industry'] = 2


wos_keywords_long = wos_keywords.assign(DE=wos_keywords['DE'].str.split(';')).explode('DE')
wos_keywords_long['DE'] = wos_keywords_long['DE'].str.lower().str.replace('[^-a-z0-9\s]', '').str.strip()

# Get subject frequencies
subject_freqs = wos_keywords_long[['Is_Industry', 'DE', 'ID']].groupby(['Is_Industry', 'DE'])['ID'].size().reset_index()
subject_freqs.rename(columns={"ID":"Counts", 'DE':'Subject'}, inplace=True)
subject_freqs['Is_Industry'] = subject_freqs['Is_Industry'].map({0:'Non_Ind', 1:'Ind', 2:'Missing'})

subject_wide = subject_freqs.pivot(index='Subject', columns='Is_Industry', values='Counts').reset_index()
subject_wide = subject_wide.fillna(0)
subject_wide = subject_wide[['Subject', 'Non_Ind', 'Ind', 'Missing']]

subject_wide.to_excel(f"{outputs_dir}subject_distribution_raw_DE.xlsx", index=False)
# Remove subjects that contain food terms
food_terms = ['milk', 'wheat', 'barley', 'cheese', 'dairy', 'cattle', 'rice', 'maize']
subject_wide = subject_wide.loc[~subject_wide['Subject'].str.contains('|'.join(food_terms)),]

subject_nonind = subject_wide.sort_values(by='Non_Ind', ascending=False).head(25)
subject_ind = subject_wide.sort_values(by='Ind', ascending=False).head(25)
subject_miss = subject_wide.sort_values(by='Missing', ascending=False).head(25)

subject_nonind.to_csv(f"{outputs_dir}subject_nonind_DE.csv", index=False)
subject_ind.to_csv(f"{outputs_dir}subject_ind_DE.csv", index=False)
subject_miss.to_csv(f"{outputs_dir}subject_missing_DE.csv", index=False)

# Keywords Plus
wos_keywords = wos_df[['Abstract.Code', 'Food.Code', 'Food.Name', 'Is_Industry', 'FU_stripped_lower',
                        'DE', 'ID']]
wos_keywords.loc[wos_keywords['FU_stripped_lower'] == ' missing ', 'Is_Industry'] = 2


wos_keywords_long = wos_keywords.assign(DE=wos_keywords['ID'].str.split(';')).explode('DE')
wos_keywords_long['DE'] = wos_keywords_long['DE'].str.lower().str.replace('[^-a-z0-9\s]', '').str.strip()

# Get subject frequencies
subject_freqs = wos_keywords_long[['Is_Industry', 'DE', 'ID']].groupby(['Is_Industry', 'DE'])['ID'].size().reset_index()
subject_freqs.rename(columns={"ID":"Counts", 'DE':'Subject'}, inplace=True)
subject_freqs['Is_Industry'] = subject_freqs['Is_Industry'].map({0:'Non_Ind', 1:'Ind', 2:'Missing'})

subject_wide = subject_freqs.pivot(index='Subject', columns='Is_Industry', values='Counts').reset_index()
subject_wide = subject_wide.fillna(0)
subject_wide = subject_wide[['Subject', 'Non_Ind', 'Ind', 'Missing']]

subject_wide.to_excel(f"{outputs_dir}subject_distribution_raw_ID.xlsx", index=False)

# Remove subjects that contain food terms
food_terms = ['milk', 'wheat', 'barley', 'cheese', 'dairy', 'cattle', 'rice', 'maize']
subject_wide = subject_wide.loc[~subject_wide['Subject'].str.contains('|'.join(food_terms)),]

subject_nonind = subject_wide.sort_values(by='Non_Ind', ascending=False).head(25)
subject_ind = subject_wide.sort_values(by='Ind', ascending=False).head(25)
subject_miss = subject_wide.sort_values(by='Missing', ascending=False).head(25)

subject_nonind.to_csv(f"{outputs_dir}subject_nonind_ID.csv", index=False)
subject_ind.to_csv(f"{outputs_dir}subject_ind_ID.csv", index=False)
subject_miss.to_csv(f"{outputs_dir}subject_missing_ID.csv", index=False)
'''
# Within each keyword, how much overlap is there between industry and non-industry?
# Similarity measure: for each AB1, AB2, # overlap keywords/# total keywords
unique_keywords = wos_keywords_long['DE'].unique()
avg_overlap = []
count_industry = []
count_nonind = []
count_missing = []
for word in unique_keywords:
    wos_sub = wos_keywords_long.loc[wos_keywords_long['DE'] == word,]
    industry_list = wos_sub.loc[wos_sub['Is_Industry'] == 1,'Abstract.Code'].unique()
    nonind_list = wos_sub.loc[wos_sub['Is_Industry'] == 0,'Abstract.Code'].unique()
    missing_list = wos_sub.loc[wos_sub['Is_Industry'] == 2,'Abstract.Code'].unique()
    overlap_tmp = []
    for ab_code1 in industry_list:
        for ab_code2 in nonind_list:
            if ab_code1 == ab_code2:
                continue
            ab_keywords1 = wos_keywords_long.loc[wos_keywords_long['Abstract.Code']==ab_code1, 'DE'].tolist()
            ab_keywords2 = wos_keywords_long.loc[wos_keywords_long['Abstract.Code']==ab_code2, 'DE'].tolist()
            common_words = [word for word in ab_keywords1 if word in ab_keywords2] # Count intersection
            overlap_ratio = len(common_words)/len(set(ab_keywords1 + ab_keywords2))
            overlap_tmp.append(overlap_ratio)
    if len(overlap_tmp) == 0:
        avg_overlap.append(np.nan)
    else:
        avg_overlap_tmp = sum(overlap_tmp)/len(overlap_tmp)
        avg_overlap.append(avg_overlap_tmp)
    count_industry.append(len(industry_list))
    count_nonind.append(len(nonind_list))
    count_missing.append(len(missing_list))


overlap_df = pd.DataFrame({'Keyword':unique_keywords, 'Avg_Overlap':avg_overlap, 'N_Ind':count_industry,
                            'N_NonInd':count_nonind, 'N_Missing':count_missing})
overlap_df.to_csv(f"{outputs_dir}keyword_overlap.csv", index=False)
