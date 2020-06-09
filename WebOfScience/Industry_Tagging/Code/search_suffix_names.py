'''
Use the suffix-matched company names to search through the funding data again.
Output final industry tagged data in two formats: wide and long
~~~DEPRECATED: Some abstracts have too many funders (>60)~~~~~
Wide Format:
FU_X
Is_Industry_X
Match_Type_X
Companies_X
where X is funding source #
Each row is a separate abstract.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
New Abstract-Collapsed Format:
Companies: Concatenated string of business names separated by semicolon
Each row is a separate abstract.

Long Format:
Original temp file format.
Each row is a separate abstract-funding source.
'''

import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz, process
from nltk.corpus import words
import re
import string
import time
import unidecode
from business_suffix_data import terms_by_type, terms_by_country

# ============= Set directory strings =================
temp_dir = "/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/WebOfScience/Industry_Tagging/Temp/"
outputs_dir = "/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/WebOfScience/Industry_Tagging/Outputs/"

# ============= Read in data  =================
final_cols = ['Funding.Code','Abstract.Code', 'Food.Code', 'Food.Name', 'Is_Industry_Suf', 'Is_Industry_US', 'Is_Industry_UK',
        'Is_Industry_Top100', 'Is_Industry_Suf_Company', 'Is_Industry_Manual','Is_Industry_B2C','Is_Industry', 'Suffix_Match', 'US_Match', 'UK_Match',
         'Top100_Match', 'Manual_Match', 'Suff_Company', 'Companies','FU_stripped_lower', 'FU_stripped_upper', 'FU','PT',
       'AU', 'BA', 'BE', 'GP', 'AF', 'BF', 'CA', 'TI', 'SO', 'SE', 'BS', 'LA',
       'DT', 'CT', 'CY', 'CL', 'SP', 'HO', 'DE', 'ID', 'AB', 'C1', 'RP', 'EM',
       'RI', 'OI', 'FX', 'CR', 'NR', 'TC', 'Z9', 'U1', 'U2', 'PU', 'PI',
       'PA', 'SN', 'EI', 'BN', 'J9', 'JI', 'PD', 'PY', 'VL', 'IS', 'PN', 'SU',
       'SI', 'MA', 'BP', 'EP', 'AR', 'DI', 'D2', 'EA', 'PG', 'WC', 'SC', 'GA',
       'UT', 'PM', 'OA', 'HC', 'HP', 'DA']

exclude = ['public interest', 'waters', 'peanut','food research', 'cotton','orbit', 'revival','proceedings','dairy foods', 'milk products',
            'dairy', 'montana', 'state laboratory', 'md', 'animal husbandry', 'genus','micronutrients', 'dairy research', 'quality control',
            'poet','consulting','angel', 'coro', 'greenery', 'iga', 'the peanut','dutch', 'dairy industries', 'industrial research',
            'public interest', 'edmonton', 'software', 'aquaculture', 'pn ii', 'kinetic', 'iaf', 'north central', 'biodiversity',
            'rich products', 'horticultural development', 'vale', 'meiji']

wos_indtagged = pd.read_csv(f'{temp_dir}wos_suff_indtagged_long.csv')
wos_indtagged = wos_indtagged.fillna("")

# Save suffix-searched company names
suff_names = wos_indtagged.loc[wos_indtagged['Suff_Company'] != "",'Suff_Company'].unique()
suff_names = sorted([name for name in suff_names if name not in exclude])

with open(f'{temp_dir}suffix_names.txt','w+') as f:
    f.writelines("%s\n" % name for name in suff_names)

suff_names = [" " + name + " " for name in suff_names] # Add whitespace padding

# ============= Search and save long formatted industry tags =================
# Run search
print("Searching through suffix-found names...")
suff_company_matches = wos_indtagged.loc[wos_indtagged['Suff_Company']=="",'FU_stripped_lower'].str.extract('(' + '|'.join(suff_names) + ')', expand=False)
wos_indtagged.loc[wos_indtagged['Suff_Company']=="",'Suff_Company'] = pd.Series(suff_company_matches)

wos_indtagged['Is_Industry_Suf_Company'] = 0
wos_indtagged.loc[(wos_indtagged['Suff_Company'] != "") & ~wos_indtagged['Suff_Company'].isna(), 'Is_Industry_Suf_Company'] = 1

wos_indtagged['Is_Industry'] = wos_indtagged["Is_Industry"] | wos_indtagged['Is_Industry_Suf_Company']
wos_indtagged.loc[wos_indtagged['Companies'] == "",'Companies'] = wos_indtagged.loc[wos_indtagged['Companies'] == "",'Suff_Company']

wos_indtagged['Companies'] = wos_indtagged['Companies'].str.strip() # Strip whitespace
wos_indtagged.fillna("", inplace=True)

# Replace company match with shortest string
def get_shortest_string(row):
    tmp = row[["Top100_Match", "US_Match", "UK_Match", "Manual_Match", "Suff_Company", 'Companies']]
    tmp[tmp==""] = np.nan
    min_index = tmp.map(len, na_action='ignore').idxmin()
    if not pd.isnull(min_index):
        return tmp[min_index]
    else:
        return ""

wos_indtagged['Companies'] = wos_indtagged.apply(get_shortest_string, axis=1)

# ============= Tag B2C Companies =================
with open(temp_dir + "B2C_names.txt", 'r') as f:
    b2c_names = f.read().splitlines()

b2c_names = [' ' + name.strip() + ' ' for name in b2c_names]

wos_indtagged['Is_Industry_B2C'] = 0
wos_indtagged.loc[wos_indtagged['FU_stripped_lower'].str.contains('|'.join(b2c_names)), 'Is_Industry_B2C'] = 1

# Export
wos_indtagged = wos_indtagged[final_cols]
wos_indtagged.to_csv(f'{outputs_dir}wos_indtagged_final_long_v1.csv', index=False)

new_tagged = len(wos_indtagged.loc[(wos_indtagged['Is_Industry_Suf_Company'] == 1) & \
                                (wos_indtagged['Is_Industry_Manual'] != 1) & \
                                (wos_indtagged['Is_Industry_Suf'] != 1) & \
                                (wos_indtagged['Is_Industry_UK'] != 1) & \
                                (wos_indtagged['Is_Industry_US'] != 1) & \
                                (wos_indtagged['Is_Industry_Top100'] != 1)].index)

print(f"Searching on company names extracted from suffix search yields {new_tagged} new matches.")

overwrite = False
with open(f'{outputs_dir}counts_each_search.txt', 'a+') as f:
    if len(f.readlines()) < 6:
        f.write(f"Searching on company names extracted from suffix search finds {new_tagged} new matches.\n")
    else:
        overwrite = True
        data = f.readlines()
f.close()

if overwrite:
    data[5] = f"Searching on company names extracted from suffix search finds {new_tagged} new matches.\n"
    with open(f'{outputs_dir}counts_each_search.txt', 'w') as f:
        f.writelines(data)
    f.close()

# Save list of most frequent new company tags
new_names = wos_indtagged.loc[(wos_indtagged['Is_Industry_Suf_Company'] == 1) & \
                                (wos_indtagged['Is_Industry_Manual'] != 1) & \
                                (wos_indtagged['Is_Industry_Suf'] != 1) & \
                                (wos_indtagged['Is_Industry_UK'] != 1) & \
                                (wos_indtagged['Is_Industry_US'] != 1) & \
                                (wos_indtagged['Is_Industry_Top100'] != 1), 'Suff_Company']

new_names_agg = new_names.value_counts()
new_names_agg.to_csv(f'{temp_dir}suff_company_freqs.csv')

# ============= Save abstract-collapsed dataframe =================
industry_aggs = [(ind_col, "max") for ind_col in wos_indtagged.columns if "Is_Industry" in ind_col]
match_aggs = [(match_col, lambda x: '' if (x=="").all() else '; '.join(x)) for match_col in wos_indtagged.columns if "Match" in match_col]
company_aggs = [(comp_col, lambda x: '' if (x=="").all() else '; '.join(x)) for comp_col in wos_indtagged.columns if "Companies" in comp_col or "Suff_Company" in comp_col]
fu_aggs = [(col, '; '.join) for col in wos_indtagged.columns if "FU" in col]
remainder_aggs = [(col, 'first') for col in wos_indtagged.columns if "Is_Industry" not in col and "Match" not in col \
                                                                and "Companies" not in col and 'FU' not in col and "Suff_Company" not in col]
aggs = dict(industry_aggs + match_aggs + company_aggs + fu_aggs + remainder_aggs)

wos_wide = wos_indtagged.groupby("Abstract.Code").agg(aggs)

# Remove empty semicolons
wos_wide.loc[:,"Suffix_Match":"Companies"].replace(r'(; )\1{1,}', r"\1",inplace=True, regex=True)
wos_wide.loc[:,"Suffix_Match":"Companies"] = wos_wide.loc[:,"Suffix_Match":"Companies"].apply(lambda x: x.str.strip('; '))

final_cols.remove("Funding.Code")
wos_wide = wos_wide[final_cols]
wos_wide.to_csv(f'{outputs_dir}wos_indtagged_final_wide_v1.csv', index = False)
