import pandas as pd
from fuzzywuzzy import fuzz, process
from nltk.corpus import words
import re
import string
import time
import unidecode
from business_suffix_data import terms_by_type, terms_by_country

# ============= Set directory strings =================
inputs_dir = "/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/WebOfScience/Industry_Tagging/Inputs/"
temp_dir = "/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/WebOfScience/Industry_Tagging/Temp/"
outputs_dir = "/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/WebOfScience/Industry_Tagging/Outputs/"

# ============= Read in data  =================
final_cols = ['Abstract.Code', 'Funding.Code','Food Code', 'Food Name', 'Is_Industry_Suf', 'Is_Industry_US', 'Is_Industry_UK',
        'Is_Industry_Top100', 'Is_Industry_Googled', 'Is_Industry_Board','Is_Industry', 'Suffix_Match', 'US_Match', 'UK_Match','Top100_Match',
         'Google_Match', 'Boards','FU_stripped_lower', 'FU_stripped_upper', 'FU','PT',
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

top100_exclude = top100_exclude_df.loc[:,'name_exclude'].tolist() #Names to exclude

with open(f'{inputs_dir}uk_names.txt', 'r') as f:
    uk_list = f.read().splitlines()

with open(f'{inputs_dir}us_names.txt', 'r') as f:
    us_list = f.read().splitlines()

uk_list = set(uk_list)
us_list = set(us_list)

us_uk_exclude = ['technology', 'key technology', 'americas', 'china international', 'nutrition',
                'national food', 'flanders', 'natural products', 'exchange', 'enterprise', 'belgium', 'alexander',
                'mushroom', 'apples', 'arabian', 'batch', 'berry', 'bovino', 'bread', 'brewery', 'bridge', 'catering',
                'centro', 'chocolate', 'cocoa', 'columbus', 'coffee', 'crane', 'creamery', 'descartes', 'flora', 'focus',
                'food manufacture','food products', 'food standards agency', 'fulton', 'grain processing', 'gulf marine',
                'human food', 'ingredient', 'institute of food science technology', 'jupiter', 'kerry', 'kitchen', 'larsen',
                'lateral', 'marco', 'meat processing', 'mexico food', 'micro', 'milk products', 'mills', 'nutrients', 'nutritional engineering',
                'ohara', 'olive', 'pasta', 'plant', 'prince', 'rojas', 'salud', 'salute', 'sanders', 'sigma', 'snack', 'trust', 'winery', 'xinhua',
                'millers', "national rice", "snacks", "kinetic", "rich products", 'bread and', 'del monte', 'cakes', 'north central',
                'mayekawa', 'institute of food science and technology']
us_uk_include = ['kamut enterprises', 'dairy farmers', 'dairynl']

top100_extend = ['pepsi', 'coca cola', 'inbevbaillet', 'intrachem bio', 'bonduelle', 'conagra', 'heinz', 'cropp', 'mondelez',
                'munster bovine', 'morinaga', 'yamazaki', 'pizza hut', 'dyadic', 'hass', 'abb grain', 'bayer', 'archer daniels midland',
                'danisco']
top100_exclude = ['rich products']
suffix_exclude = ['eu', 'sep', 'private', 'sem', 'ca', 'sc', 'sca', 'sd', 'coop','ec','ei','cv','ok',
                'oe', 'od', 'sf', 'sp', 'cic', 'spp', 'ae', 'pt', 'ks', 'pp', 'gp', 'etat', 'fa', 'sgr',
                'dd', 'smba', 'nl']
suffix_names_exclude = ['isbe', 'barley fun food project']

# Assign abstract codes
wos_full_df['Abstract.Code'] = range(1,len(wos_full_df)+1)

# Split multiple funding sources into individual lines
wos_long_df = wos_full_df.assign(FU=wos_full_df['FU'].str.split(';')).explode('FU')

# Assign funding codes
wos_long_df['Funding.Code'] = wos_long_df.groupby('Abstract.Code').cumcount()+1

# ============= CLEANING =================
# Upper case for 2-char suffix check
wos_long_df['FU_stripped_upper'] = wos_long_df['FU'].str.replace('\s*[\(\[].*?[\)\]]\s*',' ') #Remove everything between brackets or parentheses
wos_long_df['FU_stripped_upper'] = wos_long_df['FU_stripped_upper'].str.replace('co\-', 'co', case=False) # All co- strings become co to avoid false positives
wos_long_df['FU_stripped_upper'] = wos_long_df['FU_stripped_upper'].str.replace('\s*[&]\s*', ' and ')
wos_long_df['FU_stripped_upper'] = wos_long_df['FU_stripped_upper'].str.replace('[^.\'A-Za-z0-9\s]+',' ')
wos_long_df['FU_stripped_upper'] = wos_long_df['FU_stripped_upper'].str.replace('[.\']','') # Consolidate period and apostrophe words
wos_long_df['FU_stripped_upper'] = wos_long_df['FU_stripped_upper'].str.replace('\s+', ' ') # Enforce at most one space
wos_long_df.loc[wos_long_df['FU_stripped_upper'].isna(), 'FU_stripped_upper'] = 'missing' #Fill nans
wos_long_df['FU_stripped_upper'] = ' ' + wos_long_df['FU_stripped_upper'].str.strip() + ' '

# Lower case for standard check
wos_long_df['FU_stripped_lower'] = wos_long_df['FU_stripped_upper'].str.lower() #Remove everything between brackets or parentheses

# Apply same cleaning procedure to top 100 names
top100_names = top100_df.loc[:, 'Company'].str.lower().dropna().tolist()
top100_names = [re.sub('\(.*\)', '', str(name)) for name in top100_names] #Remove everything between two parentheses
top100_names = [re.sub('\s*[&]\s*', ' and ', name) for name in top100_names]
top100_names = [re.sub('co\-', 'co', name, flags=re.IGNORECASE) for name in top100_names]
top100_names = [re.sub('[^.\'a-z0-9\s]+', ' ', name) for name in top100_names] #Same treatment of punctuation
top100_names = [re.sub('[.\']', '', name) for name in top100_names]
top100_names = [' ' + re.sub('\s+', ' ', name) + ' ' for name in top100_names] #Enforce at most only one space between words

us_suff = terms_by_country['United States of America'] #Strip all US specific company suffixes
us_suff_reg = '(' + '|'.join(list(set([' ' + re.sub('[^a-z]+', '', suff) + ' ' for suff in us_suff]))) + ')'

top100_names_clean = [re.sub(us_suff_reg, ' ', name).strip() for name in top100_names] #Strip any padded whitespace
top100_names_clean.extend(top100_extend) #Add manually known top names
top100_names_search = [' ' + name + ' ' for name in top100_names_clean if name not in top100_exclude] #Apply single whitespace pads

top100_fe_names = top100_fe_df.loc[:, 'Company'].str.lower().dropna().tolist()
top100_fe_names = [unidecode.unidecode(s) for s in top100_fe_names]
top100_fe_names = [re.sub('co\-', 'co', name, flags=re.IGNORECASE) for name in top100_fe_names]
top100_fe_names = [re.sub('\s*[&]\s*', ' and ', name) for name in top100_fe_names]
top100_fe_names = [re.sub('[^.\'a-z0-9\s]+', ' ', name) for name in top100_fe_names] #Same treatment of punctuation
top100_fe_names = [re.sub('[.\']', '', name) for name in top100_fe_names]
top100_fe_names = [' ' + re.sub('\s+', ' ', name) + ' ' for name in top100_fe_names] #Enforce at most only one space between words
top100_fe_names_clean = [re.sub(us_suff_reg, ' ', name).strip() for name in top100_fe_names] #Strip any padded whitespace
top100_fe_names_search = [' ' + name + ' ' for name in top100_fe_names_clean if name not in top100_exclude]

#Export combined list of top100 names
top100_tot = list(set(top100_names_search + top100_fe_names_search))

with open(f"{temp_dir}top100_tot_cleaned.txt", 'w') as f: #Check cleaned names
    f.writelines("%s\n" % name for name in top100_tot)

us_list = [re.sub('\s*[&]\s*', ' and ', name.lower()) for name in us_list]
us_list = [re.sub('co\-', 'co', name, flags=re.IGNORECASE) for name in us_list]
us_list = [re.sub('[^.a-z\'0-9\s]+', ' ', name) for name in us_list] #Same treatment of punctuations and hyphen
us_list = [' ' + re.sub('[\'.]', '', name).strip() + ' ' for name in us_list]
us_list = [re.sub(us_suff_reg, ' ', name).strip() for name in us_list] #Remove company suffixes
us_list_search = [re.sub('\s+', ' ', name) for name in us_list if (len(name) >= 5) and ('university' not in name)] #Remove all names under 5 chars or university sources
us_list_search.extend(us_uk_include) # Manually add known names
us_list_search = list(set([' ' + name + ' ' for name in us_list_search if (name not in us_uk_exclude) and not name.isdigit()])) #Remove names that are just numbers
us_list_search.sort(key = len)
with open(f"{temp_dir}US_names_cleaned.txt", 'w') as f: #Check cleaned names
    f.writelines("%s\n" % name for name in us_list_search)

uk_list = [re.sub('\s*[&]\s*', ' and ', name.lower()) for name in uk_list]
uk_list = [re.sub('co\-', 'co', name, flags=re.IGNORECASE) for name in uk_list]
uk_list = [re.sub('[^.a-z\'0-9\s]+', ' ', name) for name in uk_list] #Same treatment of punctuations and hyphen
uk_list = [' ' + re.sub('[\'.]', '', name).strip() + ' ' for name in uk_list]
uk_list = [re.sub(us_suff_reg, ' ', name).strip() for name in uk_list] #Remove company suffixes
uk_list_search = [re.sub('\s+', ' ', name) for name in uk_list if (len(name) >= 5) and ('university' not in name)] #Remove all names under 5 chars or university sources
uk_list_search.extend(us_uk_include)
uk_list_search = list(set([' ' + name + ' ' for name in uk_list_search if (name not in us_uk_exclude) and not name.isdigit()])) #Remove names that are just numbers
uk_list_search.sort(key = len)
with open(f"{temp_dir}UK_names_cleaned.txt", 'w') as f: #Check cleaned names
    f.writelines("%s\n" % name for name in uk_list_search)

#Collapse suffixes into single list
suffixes = [item for sublist in terms_by_type.values() for item in sublist] + \
            [item for sublist in terms_by_country.values() for item in sublist]
suffixes_clean = list(set([re.sub('[^a-z\s]+', '', name).strip() for name in suffixes])) #Strip punctuation then turn into set to eliminate duplicates
suffixes_clean = [suff for suff in suffixes_clean if len(suff.split()) == 1] #Remove multi-word suffixes
three_suff = [' ' + suff + ' ' for suff in suffixes_clean if len(suff) > 2 and suff not in suffix_exclude] + [' co '] #Co is the only two-char exception (CHECK FALSE POSITIVES HERE)
two_suff = [' ' + suff.upper() + ' ' for suff in suffixes_clean if len(suff) <= 2 and len(suff) > 0 and suff not in suffix_exclude] #Make two char suffixes uppercase
two_suff = [suff for suff in two_suff if suff]
two_suff.extend([' A S ']) #Manual addded suffixes
suff_check = three_suff + two_suff
with open(f"{temp_dir}suffix_cleaned.txt", 'w') as f: #Check cleaned names
    f.writelines("%s\n" % name for name in suff_check)

# ============= MANUAL NAMES ===============
# Read in googled names
with open(f"{inputs_dir}manual_names.txt", 'r') as f:
     googled_list = f.read().splitlines()
googled_list = [name.strip() for name in googled_list]
googled_search = [" " + name + " " for name in googled_list]
googled_search = list(set(googled_search))

# Parse through food names and generate association/board names to search through
food_names = wos_long_df['Food Name'].str.lower().unique().tolist()
food_names_clean = [name.replace("ti = ", "") for name in food_names] # Strip punctuation, "TI=" string
food_names_clean = [name.replace("ti=", "") for name in food_names_clean]
food_names_clean = [re.sub(r"[^a-z\s]+", "", name) for name in food_names_clean]
food_names_split = [name.split(" or ") for name in food_names_clean] # Split on "or" string
food_names_split = [name.strip() for sub_split in food_names_split for name in sub_split] # Collapse and remove any padded whitespace
food_names_split.extend(["pistachio", "hazelnut", "egg", "melon", "cherry", "chios mastic", "fruit", "blueberry", "fruit and vegetable",
                        "canola", "brewers", "malt", "cattle", "beef", "cereal", 'grain', "crop"])
# Generate possible board/association names
groups = ['farmers','growers', 'grower', 'producers', 'producer', 'manufacturer', 'manufacturers','planters', 'planter', 'research', 'marketing',
        'advisory', 'development', 'research and promotion', 'promotion', 'refiners']
orgs = ['board', 'council', 'association', 'commission', 'of', 'society', 'cooperative', 'foundation', 'institute', 'federation', 'committee']
board_names = []
simulated_exclude = ['dairy development of']
for name in food_names_split:
    for group in groups:
        for org in orgs:
            name_to_add = f"{name} {group} {org}"
            if org != "of":
                extra_name = f"{name} {org}"
            if name_to_add in simulated_exclude:
                continue
            board_names.append(name_to_add)
            board_names.append(extra_name)

known_boards = ["pistachio research board", "hazelnut marketing board", "american egg board", "melon research board",
        "cherry advisory board", "pecan shellers association", "grocery manufacturers association", "western pistachio association",
        "grains producers utilization board", "small grains board", "grain research and promotion board",
        "honey board", "sorghum research and promotion board", "pork board", "product board animal feed",
        "food safety promotion board", "crop improvement association", "corn refiners association", "cattlemens association",
        "grain growers", "pulse growers", "growers cooperative", "australian farmers", "farmers foundation for agricultural research",
        "saskpulse growers", "prairie oat grower association", "prairie oat growers association", "alberta oat growers",
        "peanut and tree nut processors association", "alabama peanut producers association", "florida peanut producers association",
        "us dry bean council", "international nut and dried fruit council", "almond hullers and processors association", "cranberry marketing committee"]
board_names.extend(known_boards)

board_search = [' ' + name + ' ' for name in board_names]
board_search = list(set(board_search))

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
wos_long_df['Is_Industry_Top100'] = 0
wos_long_df.loc[wos_long_df['FU_stripped_lower'].str.contains('|'.join(top100_tot)), 'Is_Industry_Top100'] = 1
wos_long_df['Top100_Match'] = wos_long_df['FU_stripped_lower'].str.extract('(' + '|'.join(top100_tot) + ')')

#Apply exclusions
wos_long_df.loc[wos_long_df['FU_stripped_lower'].str.contains('|'.join(top100_exclude)), ['Is_Industry_Top100', 'Top100_Match']] = 0, ""

# Record newly tagged
top100_new_tagged = len(wos_long_df.loc[wos_long_df['Is_Industry_Top100'] == 1].index)
search_count_file.write(f"Searching on Top 100 industry names finds {top100_new_tagged} new matches.\n")

print("Industry newly tagged using top 100 names: {} out of {} abstracts".format(
        top100_new_tagged, len(wos_long_df.index)
        ))

# US list search
print("Searching through US company names: {}".format(len(us_list_search)))
wos_long_df['Is_Industry_US'] = 0
wos_long_df.loc[wos_long_df['FU_stripped_lower'].str.contains('|'.join(us_list_search)), 'Is_Industry_US'] = 1
wos_long_df['US_Match'] = wos_long_df['FU_stripped_lower'].str.extract('(' + '|'.join(us_list_search) + ')')

# Record newly tagged
us_new_tagged = len(wos_long_df.loc[(wos_long_df['Is_Industry_US'] == 1) & \
                                        (wos_long_df['Is_Industry_Top100'] != 1)].index)
search_count_file.write(f"Searching on ReferenceUSA names finds {us_new_tagged} new matches.\n")

print("Industry newly tagged using scraped US names: {} out of {} abstracts".format(
        us_new_tagged, len(wos_long_df.index)
        ))

# UK list search
print("Searching through UK company names: {}".format(len(uk_list_search)))
wos_long_df['Is_Industry_UK'] = 0
wos_long_df.loc[wos_long_df['FU_stripped_lower'].str.contains('|'.join(uk_list_search)), 'Is_Industry_UK'] = 1
wos_long_df['UK_Match'] = wos_long_df['FU_stripped_lower'].str.extract('(' + '|'.join(uk_list_search) + ')')

# Record newly tagged
UK_new_tagged = len(wos_long_df.loc[(wos_long_df['Is_Industry_UK'] == 1) & \
                                    (wos_long_df['Is_Industry_US'] != 1) & \
                                    (wos_long_df['Is_Industry_Top100'] != 1)].index)

search_count_file.write(f"Searching on UK names finds {UK_new_tagged} new matches.\n")

print("Industry newly tagged using scraped UK names: {} out of {} abstracts".format(
        UK_new_tagged, len(wos_long_df.index)
        ))

# Suffixes search
print("Searching through suffixes...")
wos_long_df['Is_Industry_Suf'] = 0
wos_long_df.loc[wos_long_df['FU_stripped_lower'].str.contains('|'.join(three_suff)), 'Is_Industry_Suf'] = 1
wos_long_df.loc[wos_long_df['FU_stripped_upper'].str.contains('|'.join(two_suff)), 'Is_Industry_Suf'] = 1
wos_long_df['Suffix_Match'] = wos_long_df['FU_stripped_lower'].str.extract('(' + '|'.join(three_suff) + ')', expand = False)
two_char_matches = wos_long_df.loc[(wos_long_df['Suffix_Match'].isnull()) | (wos_long_df['Suffix_Match'] == ""),'FU_stripped_upper'].str.extract('(' + '|'.join(two_suff) + ')', expand = False)
wos_long_df.loc[(wos_long_df['Suffix_Match'].isnull()) | (wos_long_df['Suffix_Match'] == ""),'Suffix_Match'] = pd.Series(two_char_matches)

# Set exclusions
wos_long_df.loc[wos_long_df['FU_stripped_lower'].str.contains('|'.join(suffix_names_exclude)), 'Is_Industry_Suf'] = 0
wos_long_df.loc[wos_long_df['FU_stripped_lower'].str.contains('|'.join(suffix_names_exclude)), 'Suffix_Match'] = ""


suffix_new_tagged = len(wos_long_df.loc[(wos_long_df['Is_Industry_Suf'] == 1) & \
                                        (wos_long_df['Is_Industry_UK'] != 1) & \
                                        (wos_long_df['Is_Industry_US'] != 1) & \
                                        (wos_long_df['Is_Industry_Top100'] != 1)].index)

search_count_file.write(f"Searching on suffixes finds {suffix_new_tagged} new matches.\n")

print("Industry tagged using suffix data: {} out of {} abstracts".format(
        suffix_new_tagged, len(wos_long_df.index)
        ))

# Googled list search
print("Searching through googled names...")
wos_long_df['Is_Industry_Googled'] = 0
wos_long_df.loc[wos_long_df['FU_stripped_lower'].str.contains('|'.join(googled_search)), 'Is_Industry_Googled'] = 1
wos_long_df['Google_Match'] = wos_long_df['FU_stripped_lower'].str.extract('(' + '|'.join(googled_search) + ')', expand = False)

manual_new_tagged = len(wos_long_df.loc[(wos_long_df['Is_Industry_Googled'] == 1) & \
                                        (wos_long_df['Is_Industry_Suf'] != 1) & \
                                        (wos_long_df['Is_Industry_UK'] != 1) & \
                                        (wos_long_df['Is_Industry_US'] != 1) & \
                                        (wos_long_df['Is_Industry_Top100'] != 1)].index)
search_count_file.write(f"Searching on googled names finds {manual_new_tagged} new matches.\n")

print("Industry tagged using googled names data: {} out of {} abstracts".format(
        manual_new_tagged, len(wos_long_df.index)
        ))

# Simulated boards search
print("Searching through simulated board names...")
wos_long_df['Is_Industry_Board'] = 0
wos_long_df.loc[wos_long_df['FU_stripped_lower'].str.contains('|'.join(board_search)), 'Is_Industry_Board'] = 1
wos_long_df['Boards'] = wos_long_df['FU_stripped_lower'].str.extract('(' + '|'.join(board_search) + ')', expand = False)

board_new_tagged = len(wos_long_df.loc[(wos_long_df['Is_Industry_Board'] == 1) & \
                                        (wos_long_df['Is_Industry_Googled'] != 1) & \
                                        (wos_long_df['Is_Industry_Suf'] != 1) & \
                                        (wos_long_df['Is_Industry_UK'] != 1) & \
                                        (wos_long_df['Is_Industry_US'] != 1) & \
                                        (wos_long_df['Is_Industry_Top100'] != 1)].index)
search_count_file.write(f"Searching on simulated board names finds {board_new_tagged} new matches.\n")

print("Industry tagged using simulated board names: {} out of {} abstracts".format(
        board_new_tagged, len(wos_long_df.index)
        ))

search_count_file.close()

# Export
wos_long_df['Is_Industry'] = wos_long_df['Is_Industry_Suf'] | wos_long_df['Is_Industry_Top100'] | \
                            wos_long_df['Is_Industry_US'] | wos_long_df['Is_Industry_UK'] | \
                            wos_long_df['Is_Industry_Googled'] | wos_long_df['Is_Industry_Board']

print("Total industry tagged: {} out of {} abstracts".format(
    len(wos_long_df.loc[wos_long_df.Is_Industry == 1].index), len(wos_long_df.index)))

wos_long_df = wos_long_df[final_cols]

wos_long_df.to_csv(f"{temp_dir}wos_indtagged_long_temp.csv", index = False)
