from selenium import webdriver
from selenium.webdriver.common.by import By
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import find_dotenv, load_dotenv
from datetime import datetime, timedelta
import os, sys

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
key = os.getenv("MongoDB")

# Setting up MongoDB:
uri = f"mongodb+srv://rftestingnyc_db_user:{key}@cluster.4n8bbif.mongodb.net/?appName=Cluster"
client = MongoClient(uri, server_api=ServerApi("1"))

# Send a ping to confirm a successful connection to MongoDB
try:
    client.admin.command("ping")
    # print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

database = client["forex-factory"]
collection = database["fxdata"]

# --- SCRAPING DATA ----

driver = webdriver.Chrome()
driver.get("https://www.forexfactory.com")

tab_name = driver.title

News_Event_Titles_List = driver.find_elements(By.CLASS_NAME, "calendar__event-title")
Currencies_Impacted_List = driver.find_elements(By.CSS_SELECTOR, "td.calendar__currency")
Calendar_Time_List = driver.find_elements(By.CSS_SELECTOR, "td.calendar__time")
Actual_List = driver.find_elements(By.CSS_SELECTOR,"td.calendar__actual")
Forecasted_List = driver.find_elements(By.CSS_SELECTOR,"td.calendar__forecast")
Previous_List = driver.find_elements(By.CSS_SELECTOR, "td.calendar__previous")
Event_Impact_Level_Icons = driver.find_elements(By.CSS_SELECTOR, "td.calendar__impact")

try:
    # If theres no news this automatically fails and the script simply stops.
    Impact_level_DOM_title = Event_Impact_Level_Icons[0].find_element(By.TAG_NAME, "span")
    
    impacts = []
    for x in range(len(Event_Impact_Level_Icons)):
        impact = Event_Impact_Level_Icons[x].find_element(By.TAG_NAME, "span")
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

# Getting the info used in retrieveUpdates function
current_data = []
doc = collection.find({})

# mongoDB return object cant be indexed using in range()
counter = 0
for document in doc:
    if counter == 0:
        pass
    else:
        # getting rid of the mongoDB id (will cause issues if left in)
        # Get the first key
        first_key = next(iter(document.keys()))
        del document[first_key]
        current_data.append(document)

# print(type(events_pre_update))
# print(type(all_events), "<--")

def retrieveUpdates():
    all_updates = []
    for i in range(len(all_updates)):
        updates = {}
        
        event = dict(all_events[i])
        event2 = dict(current_data[i])

        for key_tuple in event.items(): # Changed variable name from "key" to "key_tuple" for clarity
            key = key_tuple[0]
            
            if key in event2:
                if event[key] != event2[key]:
                    #print(f"Key mismatch at: {key}. Values:\n{event[key]}", event2[key])
                    updates["event-title"] = event2["event-title"]
                    updates["currency-impacted"] = event2["currency-impacted"]
                    updates["time-occured"] = event2["time-occured"]
                    updates[key] = event[key]
                    
        all_updates.append(updates) # Appending the unique dictionary for this iteration

    result = all_updates
    return result

# This can be the only print statement not commented on prod.
# If anything else isn"t commented certain parts of the bot.py script will break.
print(retrieveUpdates())

# Batch Insert:
# Keep track of when we first put in data
temp = {
    "timestamp": datetime.now()
}

collection.delete_many({})

# Inserts the timestamp document at the top
collection.insert_one(temp)
collection.insert_many(all_events)
