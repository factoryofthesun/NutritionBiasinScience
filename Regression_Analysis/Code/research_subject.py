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

# Split by semicolons
wos_keywords_long = wos_keywords.assign(DE=wos_keywords['DE'].str.split(';')).explode('DE')
wos_keywords_long['DE'] = wos_keywords_long['DE'].str.lower().str.replace('[^-a-z0-9\s]', '').str.strip()

# Get top 25 subject frequencies
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
subject_miss.to_csv(f"{outputs_dir}subject_missing.csv", index=False)
