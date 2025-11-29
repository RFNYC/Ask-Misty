import yfinance as yf
import pandas as pd 
import matplotlib.pyplot as plt
import os
import numpy as np
import datetime as dt

ticker = input("Enter stock ticker symbol: ").upper()
stock = ticker
enddate = dt.datetime.now()
startdate = enddate - dt.timedelta(days=365*2)

df = yf.download(stock, start=startdate, end=enddate)

df.head()

Close_prices= df['Close']

log_returns = np.log(Close_prices / Close_prices.shift(1))
log_returns = log_returns.dropna()

Cummulative_log_returns = log_returns.cumsum()
Cummulative_log_returns.head()

Cummulative_log_returns.plot(title=f'Cummulative Log Returns for {ticker}', figsize=(10,6))

# Saves the file in current working directory.
filename = f'{ticker}_Cumulative_Log_Returns.png' 
plt.savefig(filename, dpi=72, bbox_inches='tight')
