import os
import discord


def createEmbed(mongoHelpers, fx_collection, script_dir):
    data = mongoHelpers.high_impact_news(collection_file=fx_collection)

    # Other information such as the embed thumbnail, fields, and author is not set here. Its set in their own functions.
    my_embed = discord.Embed(
        title="MARKET VOLATILITY - High-Impact News:",
        description="All Red Folder events scheduled for the next 24 hours.",
        url="https://www.forexfactory.com",
        color=discord.Color.blue(),
    )

    # Navigating to image:
    icon_asset_path = os.path.join(script_dir, 'assets', 'fx_factory_icon.png')
    icon = discord.File(icon_asset_path, filename="fx_icon.png") 

    # Adding an image to an embed. Will appear in the top right corner of the message.
    my_embed.set_thumbnail(url="attachment://fx_icon.png")
    
    for event in data:
        if event['time-occured'] == '':
            event['time-occured'] = 'N/A'

        my_embed.add_field(
            name=f"{event['currency-impacted']}  -  {event['event-title']}",
            value=f"Actual: {event['actual']}  Forecast: {event['forecast']}  Previous: {event['previous']}\nTime Scheduled: {event['time-occured']}",
            inline=False
        )

    my_embed.set_footer(text="Data is scraped from Forex Factory and is provided for informational purposes only.")
    
    # image appears on top left. then the author name. the author name will have a link attached.
    my_embed.set_author(name="🌐 Forex Factory", url="https://www.forexfactory.com", icon_url="attachment://indicator.png")

    return my_embed, icon

