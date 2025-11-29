  # Yahoo Finance API 
import requests
from dotenv import find_dotenv, load_dotenv
import numpy as np
import os
import yfinance as yf


dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
key = os.getenv('Yahoo')

base_url = "https://yfapi.net/v8/"

def get_stock_Info(ticker):
    url = f"{base_url}finance/chart/{ticker}"
    response = requests.get(url, headers={"x-api-key": f"{key}"})
    
    if response.status_code == 200:
        stock_data = response.json()
        return stock_data
    else:
       print(f"Failed to retrieve data: {response.status_code}")

def calculate_pb_ratio(ticker):
  ticker = yf.Ticker(ticker)
  info = ticker.info
  book_value = info.get('bookValue', None)

  price = info.get('regularMarketPrice', None)
  pb_ratio = price / book_value if book_value else None
  formatter = "{:.2f}".format
  if pb_ratio:
      pb_ratio = formatter(pb_ratio)
  return pb_ratio

ticker = input("Enter stock ticker symbol: ").upper()
stock_data= get_stock_Info(ticker)

if stock_data:
   print('Ticker: 'f"{ticker}")
   print('Business: 'f"{stock_data['chart']['result'][0]['meta']['shortName']}")   
   print('Currency: 'f"{stock_data['chart']['result'][0]['meta']['currency']}")
   print('Market Price: 'f"{stock_data['chart']['result'][0]['meta']['regularMarketPrice']}$ ") 
   print(f"{stock_data['chart']['result'][0]['meta']['regularMarketVolume']} shares traded")
   print(f"{stock_data['chart']['result'][0]['meta']['fiftyTwoWeekHigh']}$ (52W High Price)")
   print(f"{stock_data['chart']['result'][0]['meta']['fiftyTwoWeekLow']}$ (52W Low Price)")
   print(f"P/B ratio: {calculate_pb_ratio(ticker)}")


