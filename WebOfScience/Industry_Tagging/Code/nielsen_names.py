import pandas as pd
import re
import numpy as np
from nltk.corpus import words

# ============= Set directory strings =================
data_dir = "/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/WebOfScience/Industry Names/"
temp_dir = "/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/WebOfScience/Industry_Tagging/Temp/"

# ============= Read in Nielsen product names and extract B2C company names =================
nielsen_df = pd.read_csv(f"{data_dir}products.tsv", sep='\t', encoding='latin1')
products = nielsen_df['brand_descr']

# Cleaning: same procedure as industry tagging
products_cleaned = products.str.lower()
products_cleaned = products.str.replace('\s*[\(\[].*?[\)\]]\s*',' ')
products_cleaned = products.str.replace('co\-', 'co', case=False)
products_cleaned = products.str.replace('\s*[&]\s*', ' and ')
products_cleaned = products.str.replace('[^.\'A-Za-z\s]+',' ') # Also remove numbers
products_cleaned = products.str.replace('[.\']','')
products_cleaned = products.str.replace('\s+', ' ')
products_cleaned = products_cleaned.drop_duplicates()

# Strip out all English words using nltk corpus
vocab = set(words.words())
vocab_reg = '|'.join(vocab)
products_stripped = products_cleaned.str.replace(vocab_reg, "").str.strip()

# Keep rows with non-empty/non-na strings
products_stripped = products_stripped[products_stripped != ""].dropna()

products_stripped.to_csv(f"{temp_dir}nielsen_b2c.csv", index=False)
