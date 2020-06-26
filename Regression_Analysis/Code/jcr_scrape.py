"""
Scrape the Journal Citation Reports (JCR) database for the impact factors of the journals present
in the WOS data
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
wos_data = pd.read_csv(f"{data_dir}wos_indtagged_final_wide_v1.csv")
journals = sorted(wos_data.SO.dropna().unique().tolist())
journals = [re.sub(r', VOL[^,]*','',name) for name in journals] # Clear edition and volume information
journals = [re.sub(r',[^,]+EDITION', '', name) for name in journals]
journals = sorted(list(set(journals)))

# ========= Scrape ===========
jcr_link = "https://jcr-clarivate-com.proxy.uchicago.edu/JCRJournalHomeAction.action"

chrome_options = Options()
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(f'{output_dir}Code/chromedriver', options=chrome_options)
driver.get(jcr_link)
sleep(3)

#Login using CNET
username = driver.find_element_by_name('j_username')
password = driver.find_element_by_name('j_password')
login = driver.find_element_by_xpath("//button[@type = 'submit']")
sleep(1)
username.send_keys("guanzhi")
password.send_keys("Tompodges2015")
login.click()
sleep(3)

#Get past duo login
WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH,"//iframe[@id='duo_iframe']")))
call_me = driver.find_element_by_xpath("//div[@class = 'row-label phone-label']/button")
call_me.click()

sleep(20)

search_box = driver.find_element_by_id('search-inputEl')
#search_button = driver.find_element_by_xpath("//div[@class='sidebar-header-search']/span") # Click search

impact_factor = []
year = []
for journal in journals:
    search_box.click()
    search_box.send_keys(journal)
    sleep(1)
    #search_button.click()
    base = driver.current_window_handle
    try:
        results_link = driver.find_element_by_xpath("//ul[@class='x-list-plain']/li[1]/a")
        results_link.click()
        sleep(3)
    except:
        pass
    #sleep(3)
    if len(driver.window_handles) == 2: # If results found, then new tab will open
        driver.switch_to.window(driver.window_handles[-1]) # Switch to new tab
        tab_button = driver.find_element_by_class_name('tab-1')
        tab_button.click()
        sleep(1)
        recent_yr_el = driver.find_element_by_xpath("//div[@class='data-table indicators-table']/div/div[2]/div[3]/table/tbody/tr[1]/td[1]/div")
        recent_impact_el = driver.find_element_by_xpath("//div[@class='data-table indicators-table']/div/div[2]/div[3]/table/tbody/tr[1]/td[3]/div")
        recent_yr = recent_yr_el.text
        recent_impact = recent_impact_el.text
        print(f"Impact factor: {recent_impact}")
        print(f"Impact year: {recent_yr}")
        impact_factor.append(recent_impact)
        year.append(recent_yr)
        driver.close()
        driver.switch_to.window(base)
    else:
        print(f"Journal {journal} not found.")
        impact_factor.append(None)
        year.append(None)
    search_box.clear()

final_df = pd.DataFrame({"Journal":journals, "Impact_Factor":impact_factor, "Year":year})
final_df.to_csv(f"{output_dir}jcr_impact_factors.csv", index=False)
