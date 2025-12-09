from dotenv import find_dotenv, load_dotenv
from datetime import datetime
import numpy as np
import pandas as pd
import os, requests
import yfinance as yf

"""
To avoid more connections to mongoDB we'll use the same method of passing the collection file a helper
to give our backtesting engine access to user defined strategies.

I decided to actually limit this even further. I'm only going to backtest the strategy on historical data on the S&P500.
Its possible to retrieve data for a number of large securities but that comes with a ton of data inconsistency issues and costs.
To avoid all that and deploy this project as soon as possible I'm sticking with the basics.
"""

def backtest_strategy(collection_file, strategy_name, guild_id, timeframe, duration_years):

    # retrieving strategy
    query = { "guild-id": f"{guild_id}" }
    document = collection_file.find_one(query)
    strategies = document['strategies'] # type: ignore
    target_strategy = strategies[f"{strategy_name}"]
    duration_years = int(duration_years)
    timeframe = timeframe

    # preparing information
    indicators = target_strategy["indicators"]
    rules = target_strategy["rules"]
    indicator1 = indicators[0]["type"]
    indicator2 = indicators[1]["type"]
    time_period1 = indicators[0]["time-period1"]
    time_period2 = indicators[1]["time-period1"]
    buy_rule = rules["buy"]
    sell_rule = rules["sell"]
    

    response = f"{indicator1},{indicator2},{time_period1},{time_period2},{buy_rule},{sell_rule}, timeframe given: {timeframe}"

    # ---- Backtesting -----

    # DATA RETRIEVAL: Thanks donart

    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)
    key = os.getenv('Yahoo')

    base_url = "https://yfapi.net/v8/"

    # Only tracking S&P500:
    ticker = "^GSPC"        
    # Calculate start date based on duration
    end_date = datetime.now()
    start_date = end_date - pd.DateOffset(years=duration_years)
    
    # Fetch data directly into a DataFrame
    data_df = yf.download(
        ticker, 
        start=start_date.strftime('%Y-%m-%d'), # yfinance prefers string dates
        end=end_date.strftime('%Y-%m-%d'),
        interval=timeframe,                     # Uses the user's input string
        progress=False                          # Disable progress bar
    )

    if data_df.empty:
        raise ValueError(f"Failed to retrieve data for {ticker} with interval '{timeframe}'.")

    # The resulting DataFrame will have columns: ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    return data_df