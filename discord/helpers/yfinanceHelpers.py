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
    time_period1 = indicators[0]["time-period1"]
    indicator2 = indicators[1]["type"]
    time_period2 = indicators[1]["time-period1"]
    buy_rule = rules["buy"]
    sell_rule = rules["sell"]
    

    response = f"{indicator1},{indicator2},{time_period1},{time_period2},{buy_rule},{sell_rule}, timeframe given: {timeframe}"

    # ---- Backtesting -----

    # Only tracking S&P500:
    ticker = "^GSPC"        
    end_date = datetime.now()
    start_date = end_date - pd.DateOffset(years=duration_years)
    
    # Fetch data directly into a DataFrame
    data_df = yf.download(
        ticker, 
        start=start_date.strftime('%Y-%m-%d'), 
        end=end_date.strftime('%Y-%m-%d'),
        interval=timeframe,                     
    ) 

    if data_df.empty:
        raise ValueError(f"Failed to retrieve data for {ticker} with interval '{timeframe}'.")

    # Calculate start date based on duration

    for indicator in indicators:
        type = indicator['type']
        period = int(indicator['time-period1'])

        if type.upper() == 'SMA': 
            print(f"Calculating SMA for period: {period}")
            data_df[f'SMA_{period}'] = data_df['Close'].rolling(window=period).mean()
        elif type.upper() == "EMA":
            print(f"Calculating EMA for period: {period}")
            data_df[f'EMA_{period}'] = data_df['Close'].ewm(span=period, adjust=False).mean()
        elif type.upper() == "RSI":
            print(f"Calculating RSI for period: {period}")
            # --- Step A: Calculate daily price changes (Differences) ---
            delta = data_df['Close'].diff()

            gains = delta.where(delta > 0, 0)
            losses = (-delta).where(delta < 0, 0)

            avg_gain = gains.ewm(span=period, adjust=False).mean()
            avg_loss = losses.ewm(span=period, adjust=False).mean()

            # The 0.00001 is to prevent division by zero for the RS calculation
            RS = avg_gain / (avg_loss.replace(0, 0.00001)) 

            # RSI Formula: RSI = 100 - (100 / (1 + RS))
            data_df[f'RSI_{period}'] = 100 - (100 / (1 + RS))

    # cleanup
    dataset = data_df.dropna()
    print(dataset)


def calculate_pip_value(ticker_symbol):
    
    ticker_symbol = f"{ticker_symbol.upper()}=X"
    ticker_symbol = ticker_symbol.upper()

    ticker = yf.Ticker(ticker_symbol)
    current_rate = ticker.info.get('regularMarketPrice')

    if current_rate is None:
        return None

    quote_currency = ticker_symbol[3:6]

    # for simplicity we're going to assume these things to be true.
    # these units are pretty standard for most pairs.
    lot_size_units = 100000
    pip_size = 0.0001
    account_currency = "USD"

    pip_value_in_quote = (pip_size / current_rate) * lot_size_units
    
    if quote_currency == account_currency:
        final_pip_value = pip_size * lot_size_units
    else:
        cross_ticker_symbol = f"{quote_currency}{account_currency}=X"
        cross_rate = yf.Ticker(cross_ticker_symbol).info.get('regularMarketPrice')
        
        if cross_rate is None:
            return None
            
        final_pip_value = pip_value_in_quote * cross_rate
        
    return final_pip_value