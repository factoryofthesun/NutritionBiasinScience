'''
Author: Richard Liu
Description: Read in compiled list of general sentiment + health sentiment words, and take only
the most frequent words that occur in the abstract data (30 general + 30 health). These are the
words we will run the exclusion checks over in order to determine what kind of sentiment words
the ML model is sensitive to. Average labelling time is ~40 min so total labelling time ~1.5 days.

TODO: Get list of health sentiment words
'''

import pandas as pd
import numpy as np
import re
import os
import sys

# ============= Set directory strings =================
ab_dir = "/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/WebOfScience/Industry_Tagging/Outputs/"
words_dir = "/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/Machine Learning/RL_Trained/Data/"

# ============= Script ==============
abs_df = pd.read_csv(f"{ab_dir}wos_indtagged_final_wide.csv")
abs_data = abs_df['AB'].dropna().tolist()
abs_data = [ab for ab in abs_data if ab != '']

with open(f'{words_dir}positive-words.txt', 'r') as f:
    general_words = f.read().splitlines()

general_words = [' ' + word + ' ' for word in general_words]
general_freqs = []

for word in general_words:
    general_freqs.append(len([ab for ab in abs_data if word in ab]))

general_df = pd.DataFrame({'Word':general_words, 'Freq':general_freqs}).sort_values(by='Freq', ascending=False).reset_index()

print(general_df.head(30)) # Top 30

# No medical lexicon yet, so save general lexicon for now
with open(f'{words_dir}pos_words_cleaned.txt', 'w+') as f:
    for i in range(50):
        word = general_df['Word'][i]
        freq = general_df['Freq'][i]
        f.write(f"{word},{freq}\n")
