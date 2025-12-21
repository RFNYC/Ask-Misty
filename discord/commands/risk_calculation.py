import discord


def createEmbed(yfinanceHelpers, equity, risk_percentage, entry_price, stop_loss, pair):

    account_equity = equity
    
    risk_amount = account_equity * (risk_percentage / 100)
    risk_pips = abs(entry_price - stop_loss) * 10000  # assuming its a 4-decimal pair for simplicity.
    pip_size = yfinanceHelpers.calculate_pip_value(pair)
     
    # Denominator: Monetary value of the trade risk, assuming 1 Standard Lot
    monetary_risk_per_standard_lot = risk_pips * pip_size

    # Final Lot Size (in standard lots: 1.0 = 100,000 units)
    lot_size = risk_amount / monetary_risk_per_standard_lot

    embed = discord.Embed(
        title="💰Position Size Calculation",
        description=f"Risk Management for **{pair.upper()}**",
        color=discord.Color.green()
    )
    embed.add_field(name="Account Equity", value=f"${account_equity:,.2f}", inline=True)
    embed.add_field(name="Risk % Defined", value=f"{risk_percentage}%", inline=True)
    embed.add_field(name="Monetary Risk", value=f"${risk_amount:,.2f}", inline=True)
    embed.add_field(name="Pip Size", value=f"{pip_size:.1f} pips", inline=True)
    embed.add_field(name="Risk in Pips", value=f"{risk_pips:.1f} pips", inline=True)
    embed.add_field(name="Lot Size (Standard Lots)", value=f"**{lot_size:.2f}** lots", inline=True)
    embed.set_footer(text="Disclaimer: Calculation uses a standard lot size of 100,000 units and assumes a 4 decimal pair. For non standard pairs like those including JPY, this tool won't give the expected results.")
    
    return embed