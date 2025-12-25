import discord

def createEmbed(results, years):

    strategy = results['strategy']
    total_return = results['total_return']
    win_rate = results['win_rate']
    trades = results['trade_count']
    benchmark = results['benchmark']
    final_balance = results['balance']

    embed = discord.Embed(
        title=f"📊 Backtest Results: {strategy}",
        description=f"Performance summary for the {strategy} trading strategy.",
        color=discord.Color.yellow()
    )

    embed.add_field(name="Total Return", value=f"{total_return}", inline=True)
    embed.add_field(name="Win Rate", value=f"{win_rate}", inline=True)
    embed.add_field(name="Trade Count", value=f"{trades}", inline=True)

    embed.add_field(name="Benchmark (Buy & Hold)", value=f"{benchmark}", inline=True)
    embed.add_field(name="Final Balance", value=f"{final_balance}", inline=True)
    embed.add_field(name="Index:", value="S&P500")

    # Footer for context
    embed.set_footer(text=f"Backtest period: Past {years} years. | Initial Balance: $10,000.00")

    return embed

