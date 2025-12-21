import os
import discord

def createEmbed(mongoHelpers, fx_collection, currency, missing_icons, script_dir):
    data = mongoHelpers.currency_specific_news(collection_file=fx_collection, currency=currency.upper())   
    
    my_embed = discord.Embed(
        title=f"MARKET VOLATILITY - {currency.upper()} News:",
        description=f"All news events pertaining to {currency.upper()} for the next 24 hours.",
        url="https://www.forexfactory.com",

        # documentation for all of the included colors: 
        color=discord.Color.blue(),
    )
    
    if currency in missing_icons:
        currency = 'ALL'

    icon_asset_path = os.path.join(script_dir, 'assets', f'{currency}.png')
    icon = discord.File(icon_asset_path, filename="fx_icon.png") 

    my_embed.set_thumbnail(url="attachment://fx_icon.png")

    for event in data:

        emj = None
        
        if event['impact-level'] == "High Impact Expected":
            emj = "🔴"
        elif event['impact-level'] == "Medium Impact Expected":
            emj = "🟠"
        elif event['impact-level'] == "Low Impact Expected":
            emj = "🟡"
        else:
            emj = "⚪"

        if event['time-occured'] == '':
            event['time-occured'] = 'N/A'

        if event['actual'] == '' and event['forecast'] == '' and event['previous'] == '':
            my_embed.add_field(
                name=f"{emj} {event['event-title']}",
                value=f"Time Scheduled: {event['time-occured']}",
                inline=True
            )
        else:
            my_embed.add_field(
                name=f"{emj} {event['event-title']}",
                value=f"Actual: {event['actual']}    Forecast: {event['forecast']}    Previous: {event['previous']}\nTime Scheduled: {event['time-occured']}",
                inline=False
            )


    my_embed.set_footer(text="Data is scraped from Forex Factory and is provided for informational purposes only.")
    
    my_embed.set_author(name="🌐 Forex Factory", url="https://www.forexfactory.com", icon_url="attachment://indicator.png")

    return my_embed, icon