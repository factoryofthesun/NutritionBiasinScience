"""
Scrape the SJR (Scimago Journal & Country Rank) database for the SJR scores of the journals in
the WOS data. This will likely replace SCR given the lack of coverage from SCR.

Breakdown of SJR scoring formula here: https://www.scimagojr.com/files/SJR2.pdf
"""

import pandas as pd
import numpy as np
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from time import sleep
import sys

# ========= Set directory strings ===========
data_dir = "/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/WebOfScience/Industry_Tagging/Outputs/"
output_dir = "/Volumes/GoogleDrive/My Drive/Nutrition_BiasInScience/Regression_Analysis/"

# ========= Read in data ===========
wos_data = pd.read_csv(f"{data_dir}wos_indtagged_final_wide_FEclean.csv")
journals = sorted(wos_data.Journal.dropna().unique().tolist())

# ========= Scrape ===========

# We'll start from a random journal page to make the loop clean
sjr_link = "https://www.scimagojr.com/journalsearch.php?q=21880&tip=sid&clean=0"

chrome_options = Options()
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(f'{output_dir}Code/chromedriver', options=chrome_options)
driver.get(sjr_link)
sleep(3)

sjr_scores = []
sjr_years = []
h_indexes = []
for journal in journals:
    search_box = driver.find_element_by_xpath("//form[@id='searchbox']/input[1]")
    search_button = driver.find_element_by_xpath("//form[@id='searchbox']/input[2]")
    search_box.send_keys(journal)
    search_button.click()
    sleep(2)
    try:
        journal_link = driver.find_element_by_xpath("//div[@class='search_results']/a")
        journal_link.click()
    except:
        print(f"Journal {journal} not found!")
        sjr_scores.append(None)
        sjr_years.append(None)
        h_indexes.append(None)
        continue
    sleep(2)
    try:
        scores = driver.find_elements_by_xpath("//div[@class='dashboard']/div[@class='cell1x1 dynamiccell'][1]/\
                                                div[2]/div[2]/table/tbody/tr/td[2]")
        years = driver.find_elements_by_xpath("//div[@class='dashboard']/div[@class='cell1x1 dynamiccell'][1]/\
                                                div[2]/div[2]/table/tbody/tr/td[1]")
        sjr_scores.append(scores[-1].text)
        sjr_years.append(years[-1].text)
    except:
        print(f"SJR scores for {journal} not found!")
        sjr_scores.append(None)
        sjr_years.append(None)
    try:
        h_index_el = driver.find_element_by_xpath("//div[@class='journaldescription colblock']/table/tbody/tr[1]/td[3]/div[1]")
        h_index = h_index_el.text
        h_indexes.append(h_index)
    except:
        print(f"H_Index for {journal} not found!")
        h_indexes.append(None)

final_df = pd.DataFrame({"Journal":journals, "SJR_Score":sjr_scores,"H_Index":h_indexes, "Year":sjr_years})
final_df.to_csv(f"{output_dir}sjr_scrape.csv", index=False)
