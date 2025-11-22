  # Yahoo Finance API 
import requests
from dotenv import find_dotenv, load_dotenv
import os

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
key = os.getenv('Yahoo')

base_url = "https://yfapi.net/v8/"

def get_stock_Info(ticker):
    url = f"{base_url}finance/chart/{ticker}"
    response = requests.get(url, headers={"x-api-key":f"{key}"})
    
    if response.status_code == 200:
        stock_data = response.json()
        return stock_data
    else:
       print(f"Failed to retrieve data: {response.status_code}")

ticker = "AAPL"
stock_data= get_stock_Info(ticker)

if stock_data:
   print(f"{ticker}")
   print(f"{stock_data['chart']['result'][0]['meta']}")
