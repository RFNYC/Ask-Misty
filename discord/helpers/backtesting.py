"""
To avoid more connections to mongoDB we'll use the same method of passing the collection file a helper
to give our backtesting engine access to user defined strategies.
"""


def backtest_strategy(collection_file, strategy_name, guild_id):

    # retrieving strategy
    query = { "guild-id": f"{guild_id}" }
    document = collection_file.find_one(query)
    strategies = document['strategies'] # type: ignore
    target_strategy = strategies[f"{strategy_name}"]

    # preparing information
    indicators = target_strategy["indicators"]
    rules = target_strategy["rules"]
    indicator1 = indicators[0]["type"]
    indicator2 = indicators[1]["type"]
    time_period1 = indicators[0]["time-period1"]
    time_period2 = indicators[1]["time-period1"]
    buy_rule = rules["buy"]
    sell_rule = rules["sell"]

    # ---- Backtesting -----

    pass