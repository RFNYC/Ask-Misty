import yfinance as yf
import pandas as pd 
import matplotlib.pyplot as plt
import os
import numpy as np
import datetime as dt

ticker = input("Enter stock ticker symbol: ").upper()
ticker_2 = input("Enter a second stock ticker symbol: ").upper()
years = input("Enter number of years you want to analyze the stock for: ")
stock = [ticker, ticker_2]
enddate = dt.datetime.now()
startdate = enddate - dt.timedelta(days=365*int(years))

df = yf.download(stock, start=startdate, end=enddate)

df.head()

Close_prices= df['Close']

Close_prices.plot(title=f'Stock Prices for {stock}', figsize=(10,5), ylabel='Price of Stock', xlabel='Date')
plt.margins(0)


# Saves the file in current working directory.
filename = f'{ticker}_and_{ticker_2}_Stock_Prices.png' 
plt.savefig(filename, dpi=72, bbox_inches='tight')

