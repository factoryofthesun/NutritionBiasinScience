import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from time import sleep
import sys

uk_directory = 'http://www.foodmanufacturedirectory.co.uk/companies/letter-all'
us_directory = 'http://www.referenceusa.com.proxy.uchicago.edu/UsBusiness/Result/5eb12cdf8d5e4e17bfd2a014350bac92'
food_engineering_2019 = 'https://www.foodengineeringmag.com/2019-top-100-food-beverage-companies'

chrome_options = Options()
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--no-sandbox")
#Try adding user data
#chrome_options.add_argument("user-data-dir= /Users/guanzhi0/Library/Application Support/Google/Chrome")
driver = webdriver.Chrome('/Users/guanzhi0/Documents/Anita_Rao_RP/Rao-IndustryFoodScience/Industry_Tagging/chromedriver', options=chrome_options)

#Scrape Food Engineering Top 100 Global List
driver.get(food_engineering_2019)
sleep(3)

#Get header
header_el = driver.find_elements_by_xpath("//table/thead/tr/th")
header = [h.text for h in header_el]
ncol = len(header)

#Get cols
rank_el = driver.find_elements_by_xpath("//table/tbody/tr/td[0]/div/span")
company_el = driver.find_elements_by_xpath("//table/tbody/tr/td[1]/strong")
sales_el = driver.find_elements_by_xpath("//table/tbody/tr/td[2]")
sales_local_el = driver.find_elements_by_xpath("//table/tbody/tr/td[3]")
year_end_el = driver.find_elements_by_xpath("//table/tbody/tr/td[4]")

ranks = [e.text for e in rank_el]
companies = [e.text for e in company_el]
sales = [e.text for e in sales_el]
sales_local = [e.text for e in sales_local_el]
year_end = [e.text for e in year_end_el]

data = dict(zip(ranks, companies, sales, sales_local, year_end))

top100_df = pd.DataFrame(data)

top100_df.to_csv("Output/top100_FE.csv", index = False)


'''
#Scrape UK directory
driver.get(uk_directory)
sleep(3)

uk_names = driver.find_elements_by_xpath("//div[@class = 'organisation-list']/ul/li/a")
uk_names_list = [name.text for name in uk_names]
with open("Output/uk_names.txt", 'w') as f:
    f.writelines("%s\n" % name for name in uk_names_list)

#Scrape US directory
driver.get(us_directory)
sleep(3)

#Login using CNET
username = driver.find_element_by_name('j_username')
password = driver.find_element_by_name('j_password')
login = driver.find_element_by_xpath("//button[@type = 'submit']")

username.send_keys("guanzhi")
password.send_keys("Tompodges2015")
login.click()

sleep(3)

#Get past duo login
WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH,"//iframe[@id='duo_iframe']")))

#Check duologin frame html
with open('Output/duologin_html.txt', 'w') as f:
    f.write(driver.page_source)
f.close()

#call_me = driver.find_element_by_xpath("//form[@id = 'login-form']/div/div[1]/button")
call_me = driver.find_element_by_xpath("//div[@class = 'row-label phone-label']/button")
call_me.click()

sleep(30)

us_names_list = []
broke = 0
i = 1280
#Start from where script broke
page_input = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//div[@class = 'pageBar']/div[@class = 'pager']/div[@class = 'page click-enterkey']")))
page_input.send_keys(str(i))
page_input.send_keys(Keys.RETURN)

with open('Output/ref_usa_html.txt', 'w') as f:
    f.write(driver.page_source)
f.close()

while i <= 1351:
    print("Page {}...".format(i))
    myElem = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, 'searchResultsPage')))
    us_names = driver.find_elements_by_xpath("//tbody[@id = 'searchResultsPage']/tr/td[2]/a")
    us_names_list.extend([name.text for name in us_names])
    #next = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//div[@class = 'pageBar']/div[@class = 'pager']/div[2]")))
    #next.click()
    #i += 1
    try:
        next = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//div[@class = 'pageBar']/div[@class = 'pager']/div[@class = 'next button mousedown-enterkey']")))
        i += 1
        next.click()
    except:
        print("Stopped at page {}".format(i))
        print("Exporting US names...")
        with open("Output/us_names.txt", 'a') as f:
            f.writelines("%s\n" % name for name in us_names_list)
        f.close()
        broke = 1
        break

if not broke:
    with open("Output/us_names.txt", 'a') as f:
        f.writelines("%s\n" % name for name in us_names_list)
    f.close()
'''
