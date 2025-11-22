from selenium import webdriver
from selenium.webdriver.common.by import By
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import find_dotenv, load_dotenv
from datetime import datetime, timedelta
import os, sys

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
key = os.getenv('MongoDB')

# Setting up MongoDB:
uri = f'mongodb+srv://rftestingnyc_db_user:{key}@cluster.4n8bbif.mongodb.net/?appName=Cluster'
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection to MongoDB
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

database = client["forex-factory"]
collection = database['fxdata']



# Check if we need to scrape any information:
if collection.count_documents({}) == 0:
    pass
    print("Starting script...")
else:
    # Basically says if the last entry is younger than 24 hours simply stop the script else keep going.
    doc = collection.find_one()
    time_now = datetime.now()
    last_entry_time = doc['timestamp'] # type: ignore

    twenty_four = timedelta(24)
    time_difference = time_now - last_entry_time

    if time_difference > twenty_four:
        print("Last entry was over 24 Hours ago. Starting script...")
    else:
        print("Last entry was less than 24 Hours ago. Stopping script...")
        sys.exit()

# --- SCRAPING DATA ----

driver = webdriver.Chrome()
driver.get("https://www.forexfactory.com")

tab_name = driver.title

News_Event_Titles_List = driver.find_elements(By.CLASS_NAME, 'calendar__event-title')
Currencies_Impacted_List = driver.find_elements(By.CSS_SELECTOR, 'td.calendar__currency')
Calendar_Time_List = driver.find_elements(By.CSS_SELECTOR, 'td.calendar__time')
Actual_List = driver.find_elements(By.CSS_SELECTOR,'td.calendar__actual')
Forecasted_List = driver.find_elements(By.CSS_SELECTOR,'td.calendar__forecast')
Previous_List = driver.find_elements(By.CSS_SELECTOR, 'td.calendar__previous')
Event_Impact_Level_Icons = driver.find_elements(By.CSS_SELECTOR, 'td.calendar__impact')

try:
    # If theres no news this automatically fails and the script simply stops.
    Impact_level_DOM_title = Event_Impact_Level_Icons[0].find_element(By.TAG_NAME, 'span')
    
    impacts = []
    for x in range(len(Event_Impact_Level_Icons)):
        impact = Event_Impact_Level_Icons[x].find_element(By.TAG_NAME, 'span')
        impact = impact.get_attribute("title")

        impacts.append(impact)
except:
    print("An error has occured scraping data from ForexFactory.com.")

def get_content(selenium_arr):
    res = []
    for item in selenium_arr:
        res.append(item.text)
    return res

titles = get_content(News_Event_Titles_List)
currencies = get_content(Currencies_Impacted_List)
times = get_content(Calendar_Time_List)
actuals = get_content(Actual_List)
forecasts = get_content(Forecasted_List)
previous = get_content(Previous_List)

driver.quit()

# ---- Updating MongoDB ------


# Preparing for batch insert by compiling scraped data back into event objects:
all_events = []

for i in range(len(titles)):
    event = {}

    event["event-title"] = titles[i]
    event["currency-impacted"] = currencies[i]
    event["impact-level"] = impacts[i]
    event["time-occured"] = times[i]
    event["actual"] = actuals[i]
    event["forecast"] = forecasts[i]
    event["previous"] = previous[i]

    all_events.append(event)

# Batch Insert:
# Keep track of when we first put in data
temp = {
    'timestamp': datetime.now()
}

# Inserts the timestamp document at the top
collection.insert_one(temp)
collection.insert_many(all_events)

print("Data added successfully. Check out MongoDB.")
