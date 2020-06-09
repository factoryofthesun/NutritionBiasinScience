import pandas as pd
from fuzzywuzzy import fuzz, process
from nltk.corpus import words
import re
import string
import time
import unidecode
from business_suffix_data import terms_by_type, terms_by_country

# ============= Set directory strings =================
inputs_dir = "/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/WebOfScience/Industry_Tagging/Inputs/"
temp_dir = "/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/WebOfScience/Industry_Tagging/Temp/"
outputs_dir = "/Volumes/GoogleDrive/.shortcut-targets-by-id/0B0efpUDNVRiVME9hOFNHaU1xVW8/Nutrition_BiasInScience/WebOfScience/Industry_Tagging/Outputs/"

# ============= Read in data  =================

final_cols = ['Food Code', 'Food Name', 'Is_Industry_Suf', 'Is_Industry_US', 'Is_Industry_UK',
        'Is_Industry_Top100', 'Is_Industry', 'Suffix_Match', 'US_Match', 'UK_Match','Top100_Match',
         'FU_stripped', 'FU_stripped_upper', 'FU','PT',
       'AU', 'BA', 'BE', 'GP', 'AF', 'BF', 'CA', 'TI', 'SO', 'SE', 'BS', 'LA',
       'DT', 'CT', 'CY', 'CL', 'SP', 'HO', 'DE', 'ID', 'AB', 'C1', 'RP', 'EM',
       'RI', 'OI', 'FX', 'CR', 'NR', 'TC', 'Z9', 'U1', 'U2', 'PU', 'PI',
       'PA', 'SN', 'EI', 'BN', 'J9', 'JI', 'PD', 'PY', 'VL', 'IS', 'PN', 'SU',
       'SI', 'MA', 'BP', 'EP', 'AR', 'DI', 'D2', 'EA', 'PG', 'WC', 'SC', 'GA',
       'UT', 'PM', 'OA', 'HC', 'HP', 'DA']

wos_full_df = pd.read_csv(f'{temp_dir}wos_full_coded.tsv', sep='\t')
top100_df = pd.read_excel(f'{inputs_dir}FP2019-Top100sort.xls',
                            sheet_name = 0) #Top 100 US food manufacturers
top100_fe_df = pd.read_csv(f'{inputs_dir}top100_FE.csv') #Top 100 global food manufacturers from Food Engineering
top100_exclude_df = pd.read_excel(f'{inputs_dir}FP2019-Top100sort.xls',
                            sheet_name = 2)
#products_df = pd.read_csv(f'{inputs_dir}products.tsv',
#                            sep = '\t', header = 0, encoding = 'latin1')

top100_exclude = top100_exclude_df.loc[:,'name_exclude'].tolist() #Names to exclude
products_names = list(set(products_df.loc[:, 'brand_descr'].str.lower().dropna().tolist()))

with open(f'{inputs_dir}uk_names.txt', 'r') as f:
    uk_list = f.readlines()

with open(f'{inputs_dir}us_names.txt', 'r') as f:
    us_list = f.readlines()

uk_list = set(uk_list)
us_list = set(us_list)
#scraped_list = list(set(uk_list + us_list))
us_uk_exclude = ['technology', 'key technology', 'americas', 'china international', 'nutrition',
                'national food', 'flanders', 'natural products', 'exchange', 'enterprise', 'belgium', 'alexander',
                'mushroom', 'apples', 'arabian', 'batch', 'berry', 'bovino', 'bread', 'brewery', 'bridge', 'catering',
                'centro', 'chocolate', 'cocoa', 'columbus', 'coffee', 'crane', 'creamery', 'descartes', 'flora', 'focus',
                'food manufacture','food products', 'food standards agency', 'fulton', 'grain processing', 'gulf marine',
                'human food', 'ingredient', 'institute of food science technology', 'jupiter', 'kerry', 'kitchen', 'larsen',
                'lateral', 'marco', 'meat processing', 'mexico food', 'micro', 'milk products', 'mills', 'nutrients', 'nutritional engineering',
                'ohara', 'olive', 'pasta', 'plant', 'prince', 'rojas', 'salud', 'salute', 'sanders', 'sigma', 'snack', 'trust', 'winery', 'xinhua',
                'millers', "national rice"]

top100_extend = ['pepsi', 'coca cola', 'inbevbaillet', 'intrachem bio', 'bonduelle', 'conagra', 'heinz', 'cropp', 'mondelez',
                'munster bovine', 'morinaga', 'yamazaki', 'pizza hut', 'dyadic', 'hass']
suffix_exclude = ['eu', 'sep', 'private', 'sem', 'ca', 'sc', 'sca']

# ============= CLEANING =================
wos_full_df['FU_stripped_upper'] = wos_full_df['FU'].str.replace('\s*[\(\[].*?[\)\]]\s*',' ') #Remove everything between brackets or parentheses
wos_full_df['FU_stripped_upper'] = wos_full_df['FU_stripped_upper'].str.replace('[^-.&\'A-Za-z0-9\s]+',' ') #Upper case for 2-char suffix check
wos_full_df['FU_stripped_upper'] = wos_full_df['FU_stripped_upper'].str.replace('[-.&\']','')
wos_full_df['FU_stripped_upper'] = wos_full_df['FU_stripped_upper'].str.replace('\s\s+', ' ') # Enforce at most one space
wos_full_df.loc[wos_full_df['FU_stripped_upper'].isna(), 'FU_stripped_upper'] = 'missing' #Fill nans
wos_full_df['FU_stripped_upper'] = ' ' + wos_full_df['FU_stripped_upper'].str.strip() + ' '

wos_full_df['FU_stripped'] = wos_full_df['FU'].str.replace('[\(\[].*?[\)\]]','') #Remove everything between brackets or parentheses
wos_full_df['FU_stripped'] = wos_full_df['FU_stripped'].str.lower().str.replace('[^-.\'&a-z0-9\s]+',' ')
wos_full_df['FU_stripped'] = wos_full_df['FU_stripped'].str.replace('[-.&\']','') #Some punctuation not spaced
wos_full_df['FU_stripped'] = wos_full_df['FU_stripped'].str.replace('\s\s+', ' ') #Enforce at most one space
wos_full_df.loc[wos_full_df['FU_stripped'].isna(), 'FU_stripped'] = 'missing' #Fill nans
wos_full_df['FU_stripped'] = ' ' + wos_full_df['FU_stripped'].str.strip() + ' '

top100_names = top100_df.loc[:, 'Company'].str.lower().dropna().tolist()
top100_names = [re.sub('\(.*\)', '', str(name)) for name in top100_names] #Remove everything between two parentheses
top100_names = [re.sub('[^-.&\'a-z0-9\s]+', ' ', name) for name in top100_names] #Same treatment of punctuation and hyphen
top100_names = [re.sub('[-.&\']', '', name) for name in top100_names]
top100_names = [' ' + re.sub('\s\s+', ' ', name) + ' ' for name in top100_names] #Enforce at most only one space between words
us_suff = terms_by_country['United States of America'] #Strip all US specific company suffixes
us_suff_reg = '(' + '|'.join(list(set([' ' + re.sub('[^a-z]+', '', suff) + ' ' for suff in us_suff]))) + ')'
top100_names_clean = [re.sub(us_suff_reg, ' ', name).strip() for name in top100_names] #Strip any padded whitespace
top100_names_clean.extend(top100_extend) #Add manually known top names
top100_names_search = [' ' + name + ' ' for name in top100_names_clean if name] #Apply single whitespace pads

'''top100_greedy_cleaned = [] #Greedy top100 names
for name in top100_names_clean:
    top100_greedy_cleaned.extend(name.split())
top100_greedy_search = [' ' + name + ' ' for name in top100_greedy_cleaned]
'''
top100_fe_names = top100_fe_df.loc[:, 'Company'].str.lower().dropna().tolist()
top100_fe_names = [unidecode.unidecode(s) for s in top100_fe_names]
top100_fe_names = [re.sub('[^-.&a-z\'0-9\s]+', ' ', name) for name in top100_fe_names] #Same treatment of punctuation and hyphen
top100_fe_names = [re.sub('[-.&\']', '', name) for name in top100_fe_names]
top100_fe_names = [' ' + re.sub('\s\s+', ' ', name) + ' ' for name in top100_fe_names] #Enforce at most only one space between words
top100_fe_names_clean = [re.sub(us_suff_reg, ' ', name).strip() for name in top100_fe_names] #Strip any padded whitespace
top100_fe_names_search = [' ' + name + ' ' for name in top100_fe_names_clean if name]

#Export combined list of top100 names
top100_tot = list(set(top100_names_search + top100_fe_names_search))
with open(f"{temp_dir}top100_tot_cleaned.txt", 'w') as f: #Check cleaned names
    f.writelines("%s\n" % name for name in top100_tot)

'''#Create greedy search
top100_tot_greedy = [] #Greedy top100 names
for name in top100_tot:
    top100_tot_greedy.extend(name.split())

#Filtered greedy search (remove all words that exist in english language)
#Also remove single characters
top100_tot_greedy_nonenglish = [' ' + name.strip() + ' ' for name in top100_tot_greedy if (name.strip() not in words.words()) and (len(name.strip()) > 1)]
with open("Output/top100_tot_greedy_nonenglish.txt", 'w') as f:
    f.writelines("%s\n" % name.strip() for name in top100_tot_greedy_nonenglish)

print("Reduced greedy list after filtering out English words from {} to {}".format(
        len(top100_tot_greedy), len(top100_tot_greedy_nonenglish)))
'''
us_list = [re.sub('[^-.&a-z\'0-9\s]+', ' ', name.lower()) for name in us_list] #Same treatment of punctuations and hyphen
us_list = [' ' + re.sub('[-\'.&]', '', name).strip() + ' ' for name in us_list]
us_list = [re.sub(us_suff_reg, ' ', name).strip() for name in us_list] #Remove company suffixes
us_list_search = [re.sub('\s\s+', ' ', name) for name in us_list if (len(name) >= 5) and ('university' not in name)] #Remove all names under 5 chars or university sources
us_list_search = list(set([' ' + name + ' ' for name in us_list_search if (name not in us_uk_exclude) and not name.isdigit()])) #Remove names that are just numbers
us_list_search.extend([' dairy farmers ']) #Manually add known names
us_list_search.sort(key = len)
with open(f"{temp_dir}US_names_cleaned.txt", 'w') as f: #Check cleaned names
    f.writelines("%s\n" % name for name in us_list_search)

uk_list = [re.sub('[^-.&a-z\'0-9\s]+', ' ', name.lower()) for name in uk_list] #Same treatment of punctuations and hyphen
uk_list = [' ' + re.sub('[-\'.&]', '', name).strip() + ' ' for name in uk_list]
uk_list = [re.sub(us_suff_reg, ' ', name).strip() for name in uk_list] #Remove company suffixes
uk_list_search = [re.sub('\s\s+', ' ', name) for name in uk_list if (len(name) >= 5) and ('university' not in name)] #Remove all names under 5 chars or university sources
uk_list_search = list(set([' ' + name + ' ' for name in uk_list_search if (name not in us_uk_exclude) and not name.isdigit()])) #Remove names that are just numbers
uk_list_search.extend([' dairy farmers ']) #Manually add known names
uk_list_search.sort(key = len)
with open(f"{temp_dir}UK_names_cleaned.txt", 'w') as f: #Check cleaned names
    f.writelines("%s\n" % name for name in uk_list_search)

'''products_names = [re.sub('[^-.&\'a-z\s]+', ' ', name) for name in products_names] #Same treatment of punctuations and hyphen
products_names = [re.sub('[-.&\']', '', name).strip() for name in products_names]
products_names = [name for name in products_names if len(name) >= 5] #Remove all strings under 5 characters long
products_names_search = list(set([' ' + re.sub('\s\s+', ' ', name) + ' ' for name in products_names if name]))
products_names_search.sort(key = len)

with open(f"{temp_dir}Nielsen_names_cleaned.txt", 'w') as f: #Check cleaned names
    f.writelines("%s\n" % name for name in products_names_search)
'''
#Collapse suffixes into single list
suffixes = [item for sublist in terms_by_type.values() for item in sublist] + \
            [item for sublist in terms_by_country.values() for item in sublist]
suffixes_clean = list(set([re.sub('[^a-z\s]+', '', name).strip() for name in suffixes])) #Strip punctuation then turn into set to eliminate duplicates
suffixes_clean = [suff for suff in suffixes_clean if len(suff.split()) == 1] #Remove multi-word suffixes
three_suff = [' ' + suff + ' ' for suff in suffixes_clean if (len(suff) > 2) and (suff not in suffix_exclude)] + [' co '] #Co is the only two-char exception (CHECK FALSE POSITIVES HERE)
two_suff = [' ' + suff.upper() + ' ' for suff in suffixes_clean if (len(suff) <= 2) and (len(suff) > 0) and (suff not in suffix_exclude)] #Make two char suffixes uppercase
two_suff = [suff for suff in two_suff if suff]
two_suff.extend([' A S ']) #Manual addded suffixes
suff_check = three_suff + two_suff
with open(f"{temp_dir}suffix_cleaned.txt", 'w') as f: #Check cleaned names
    f.writelines("%s\n" % name for name in suff_check)

# ============= TAGGING =================
'''
Tagging procedure:
0) Strip funding source data of punctuation (replace everyting except '-' with space) and make lowercase
1) Search for top 100 names
2) Search for names from US/UK scraped company data
3) Search for brands from Nielsen data (REMOVED BECAUSE INEFFICIENT)
4) Search for suffixes - search for only uppercase 2-char suffixes (excl. co), lowercase
'''
# Save record of how many new businesses each step tags
search_count_file = open(f"{outputs_dir}counts_each_search.txt", "w+")

#Top 100 names search
print("Searching through Top 100 names")
wos_full_df['Is_Industry_Top100'] = 0
wos_full_df.loc[wos_full_df['FU_stripped'].str.contains('|'.join(top100_tot)), 'Is_Industry_Top100'] = 1
wos_full_df['Top100_Match'] = wos_full_df['FU_stripped'].str.extract('(' + '|'.join(top100_tot) + ')')

#Apply exclusions
wos_full_df.loc[wos_full_df['FU_stripped'].str.contains('|'.join(top100_exclude)), ['Is_Industry_Top100', 'Top100_Match']] = 0, ""

# Record newly tagged
top100_new_tagged = len(wos_full_df.loc[wos_full_df['Is_Industry_Top100'] == 1].index)
search_count_file.write(f"Searching on Top 100 industry names finds {top100_new_tagged} new matches.\n")

print("Industry newly tagged using top 100 names: {} out of {} abstracts".format(
        top100_new_tagged, len(wos_full_df.index)
        ))

#Top 100 Greedy Filtered Search
'''wos_full_df['Is_Industry_Greedy_NonEnglish'] = 0
wos_full_df.loc[wos_full_df['FU_stripped'].str.contains('|'.join(top100_tot_greedy_nonenglish)), 'Is_Industry_Greedy_NonEnglish'] = 1
wos_full_df['Top100_Greedy_NonEnglish_Match'] = wos_full_df['FU_stripped'].str.extract('(' + '|'.join(top100_tot_greedy_nonenglish) + ')')

print("Industry tagged using top 100 greedy-filtered names: {} out of {} abstracts".format(
        len(wos_full_df.loc[wos_full_df['Is_Industry_Greedy_NonEnglish'] == 1].index), len(wos_full_df.index)
        ))'''

# US list search
print("Searching through US company names: {}".format(len(us_list_search)))
wos_full_df['Is_Industry_US'] = 0
wos_full_df.loc[wos_full_df['FU_stripped'].str.contains('|'.join(us_list_search)), 'Is_Industry_US'] = 1
wos_full_df['US_Match'] = wos_full_df['FU_stripped'].str.extract('(' + '|'.join(us_list_search) + ')')

# Record newly tagged
us_new_tagged = len(wos_full_df.loc[(wos_full_df['Is_Industry_US'] == 1) & \
                                        (wos_full_df['Is_Industry_Top100'] != 1)].index)
search_count_file.write(f"Searching on ReferenceUSA names finds {us_new_tagged} new matches.\n")

print("Industry newly tagged using scraped US names: {} out of {} abstracts".format(
        us_new_tagged, len(wos_full_df.index)
        ))

# UK list search
print("Searching through UK company names: {}".format(len(uk_list_search)))
wos_full_df['Is_Industry_UK'] = 0
wos_full_df.loc[wos_full_df['FU_stripped'].str.contains('|'.join(uk_list_search)), 'Is_Industry_UK'] = 1
wos_full_df['UK_Match'] = wos_full_df['FU_stripped'].str.extract('(' + '|'.join(uk_list_search) + ')')

# Record newly tagged
UK_new_tagged = len(wos_full_df.loc[(wos_full_df['Is_Industry_UK'] == 1) & \
                                    (wos_full_df['Is_Industry_US'] != 1) & \
                                    (wos_full_df['Is_Industry_Top100'] != 1)].index)

search_count_file.write(f"Searching on UK names finds {UK_new_tagged} new matches.\n")

print("Industry newly tagged using scraped UK names: {} out of {} abstracts".format(
        UK_new_tagged, len(wos_full_df.index)
        ))

'''#Nielsen brands search
wos_full_df['Is_Industry_Nielsen'] = 0
print("Searching for Nielsen names: {}".format(len(products_names_search)))
wos_full_df.loc[wos_full_df['FU_stripped'].str.contains('|'.join(products_names_search)), 'Is_Industry_Nielsen'] = 1
wos_full_df['Nielsen_Match'] = wos_full_df['FU_stripped'].str.extract('(' + '|'.join(products_names_search) + ')')

print("Industry tagged using Nielsen data: {} out of {} abstracts".format(
        len(wos_full_df.loc[wos_full_df['Is_Industry_Nielsen'] == 1].index), len(wos_full_df.index)
        ))'''

#Suffixes search
print("Searching through suffixes...")
wos_full_df['Is_Industry_Suf'] = 0
wos_full_df.loc[wos_full_df['FU_stripped'].str.contains('|'.join(three_suff)), 'Is_Industry_Suf'] = 1
wos_full_df.loc[wos_full_df['FU_stripped_upper'].str.contains('|'.join(two_suff)), 'Is_Industry_Suf'] = 1
wos_full_df['Suffix_Match'] = wos_full_df['FU_stripped'].str.extract('(' + '|'.join(three_suff) + ')', expand = False)
two_char_matches = wos_full_df.loc[(wos_full_df['Suffix_Match'].isnull()) | (wos_full_df['Suffix_Match'] == ""),'FU_stripped_upper'].str.extract('(' + '|'.join(two_suff) + ')', expand = False)
wos_full_df.loc[(wos_full_df['Suffix_Match'].isnull()) | (wos_full_df['Suffix_Match'] == ""),'Suffix_Match'] = pd.Series(two_char_matches)

suffix_new_tagged = len(wos_full_df.loc[(wos_full_df['Is_Industry_Suf'] == 1) & \
                                        (wos_full_df['Is_Industry_UK'] != 1) & \
                                        (wos_full_df['Is_Industry_US'] != 1) & \
                                        (wos_full_df['Is_Industry_Top100'] != 1)].index)

search_count_file.write(f"Searching on suffixes finds {suffix_new_tagged} new matches.\n")

print("Industry tagged using suffix data: {} out of {} abstracts".format(
        suffix_new_tagged, len(wos_full_df.index)
        ))
search_count_file.close()
# Export
wos_full_df['Is_Industry'] = wos_full_df['Is_Industry_Suf'] | wos_full_df['Is_Industry_Top100'] | \
                            wos_full_df['Is_Industry_US'] | wos_full_df['Is_Industry_UK']
print("Total industry tagged: {} out of {} abstracts".format(
    len(wos_full_df.loc[wos_full_df.Is_Industry == 1].index), len(wos_full_df.index)))

wos_full_df = wos_full_df[final_cols]

wos_full_df.to_csv(f"{temp_dir}wos_indtagged_temp.csv", index = False)
