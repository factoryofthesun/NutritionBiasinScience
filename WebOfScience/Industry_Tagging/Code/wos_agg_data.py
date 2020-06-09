import pandas as pd
import codecs
import selenium
import fuzzywuzzy as fz
import glob, os
import re
import string

# ============= Set directory strings =================
wos_data_dir = '/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/WebOfScience/WoS_Data/'
wos_data_coding_dir = '/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/WebOfScience/WoS_Data_Coding.xlsx'
temp_dir = "/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/WebOfScience/Industry_Tagging/Temp/"

# ============= Read in and aggregate txt files =================
wos_codes_df = pd.read_excel(wos_data_coding_dir)
wos_codes_short = wos_codes_df.loc[:,['Id', 'Title']]
print("Searching for files in directory {}".format(os.path.join(wos_data_dir, "*.txt")))
wos_data_files = glob.glob(os.path.join(wos_data_dir, "*.txt"))
print("Found {} files".format(len(wos_data_files)))

df_list = []
#Read in txt files using codecs to avoid weird tokenizer error
#Need to manually shift the data over once to the right due to way pandas is reading the text
#This method will still drop 3 lines that don't fit the column count
for f in wos_data_files:
    text = codecs.open(f, 'rU', 'utf-16')
    temp_df = pd.read_csv(text, sep = '\t', error_bad_lines = False)
    if "15.txt" not in f or "115.txt" in f:
        temp_df = temp_df.shift(periods = 1, axis = 'columns')
        temp_df['PT'] = 'J'
    food_code = int(os.path.split(f)[-1].replace(".txt", ""))
    temp_df['Food Code'] = food_code
    df_list.append(temp_df)

wos_df = pd.concat(df_list, ignore_index = True, sort = False)
wos_df_coded = wos_df.merge(wos_codes_short, left_on = 'Food Code', right_on = 'Id', how = 'left')
wos_df_coded.drop('Id', axis = 1, inplace = True)
wos_df_coded.rename(columns = {'Title':'Food Name'}, inplace = True)
wos_df_coded.sort_values(by = 'Food Code', inplace = True)

# Search for tab characters and replace them with spaces
# wos_df_coded.replace(to_replace = '\t', value = ' ', regex = True, inplace = True)

# Reorder columns
cols = wos_df_coded.columns.tolist()
cols = cols[-2:] + cols[:-2]
wos_df_coded = wos_df_coded[cols]

# Remove rows that duplicate the header
wos_df_coded = wos_df_coded[wos_df_coded.BA != "BA"]

# Remove empty rows
wos_df_coded.dropna(how='all', inplace=True)

# Remove within food group duplicates (keep ones which were published in different journals)
wos_df_coded.drop_duplicates(subset=cols[2:], inplace=True)

# Remove rows that have a non-numeric food code
wos_df_coded = wos_df_coded[pd.to_numeric(wos_df_coded['Food Code'], errors='coerce').notnull()]

print(wos_df_coded.columns, "Row count:", len(wos_df_coded.index))
wos_df_coded.to_csv(f'{temp_dir}wos_full_coded.tsv', sep = '\t',index = False)
