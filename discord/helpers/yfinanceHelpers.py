import pandas as pd
import yfinance as yf
from datetime import datetime

def backtest_strategy(collection_file, strategy_name, guild_id, timeframe, years):
    query = {"guild-id": f"{guild_id}"}
    document = collection_file.find_one(query)
    
    if not document or 'strategies' not in document:
        return "Guild data or strategies not found."
        
    strategies = document['strategies']
    target_strategy = strategies.get(strategy_name)
    if not target_strategy:
        return f"Strategy '{strategy_name}' not found."
        
    indicators = target_strategy["indicators"]
    rules = target_strategy["rules"]
    
    # hardcoding this because getting data's a bitch
    ticker = "^GSPC"  
    end_date = datetime.now()
    start_date = end_date - pd.DateOffset(years=years)
    
    data_df = yf.download(
        ticker, 
        start=start_date.strftime('%Y-%m-%d'), 
        end=end_date.strftime('%Y-%m-%d'),
        interval=timeframe,
        progress=False
    ) 

    if data_df is None or data_df.empty:
        return "No data retrieved from Yahoo Finance."

    if isinstance(data_df.columns, pd.MultiIndex):
        data_df.columns = data_df.columns.get_level_values(0)

    rule_mapping = {}

    for i, indicator in enumerate(indicators):
        indicator_type = str(indicator.get('type', '')).strip().upper()
        period_val = str(indicator.get('time-period1', '14')).strip()
        period = int(period_val)
        
        col_name = f"{indicator_type}_{period}"
        rule_mapping[f"indicator{i+1}"] = col_name

        if indicator_type == 'SMA':
            data_df[col_name] = data_df['Close'].rolling(window=period).mean()
        elif indicator_type == "EMA":
            data_df[col_name] = data_df['Close'].ewm(span=period, adjust=False).mean()
        elif indicator_type == "RSI":
            delta = data_df['Close'].diff()
            gains, losses = delta.clip(lower=0), -1 * delta.clip(upper=0)
            avg_gain = gains.ewm(span=period, adjust=False).mean()
            avg_loss = losses.ewm(span=period, adjust=False).mean()
            rs = avg_gain / (avg_loss.replace(0, 0.00001)) 
            data_df[col_name] = 100 - (100 / (1 + rs))

    buy_rule = rules["buy"]
    sell_rule = rules["sell"]
    for key, val in rule_mapping.items():
        buy_rule = buy_rule.replace(key, val)
        sell_rule = sell_rule.replace(key, val)

    dataset = data_df.dropna().copy()
    if dataset.empty:
        return "Insufficient data for these indicator periods."

    # placeholder account data
    balance = 10000.0
    initial_balance = balance
    position = 0 
    buy_price = 0
    trades = []

    for _, row in dataset.iterrows():
        context = row.to_dict()
        try:
            if position == 0 and eval(buy_rule, {"__builtins__": None}, context):
                position = 1
                buy_price = float(row['Close'])
            
            elif position == 1 and eval(sell_rule, {"__builtins__": None}, context):
                current_close = float(row['Close'])
                trade_return = (current_close - buy_price) / buy_price
                balance *= (1 + trade_return)
                trades.append(trade_return)
                position = 0
        except Exception as e:
            return f"Logic Error in Rule Evaluation: {e}"

    total_return = ((balance - initial_balance) / initial_balance) * 100
    win_rate = (len([t for t in trades if t > 0]) / len(trades) * 100) if trades else 0
    
    final_close = float(dataset['Close'].iloc[-1])
    start_close = float(dataset['Close'].iloc[0])
    bh_return = ((final_close - start_close) / start_close) * 100

    return {
        "strategy": strategy_name,
        "total_return": f"{total_return:+.2f}%",
        "win_rate": f"{win_rate:.1f}%",
        "trade_count": len(trades),
        "benchmark": f"{bh_return:+.2f}%",
        "balance": f"${balance:,.2f}"
    }

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