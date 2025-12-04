import discord
from discord import app_commands
from dotenv import find_dotenv, load_dotenv
from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os, asyncio, sys, subprocess, json
from helpers import mongoHelpers

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
key = os.getenv('TOKEN')
key2 = os.getenv('MongoDB')
key3 = os.getenv("MistyDebug")

uri = f'mongodb+srv://rftestingnyc_db_user:{key2}@cluster.4n8bbif.mongodb.net/?appName=Cluster'
mongo_client = MongoClient(uri, server_api=ServerApi('1'))

try:
    mongo_client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Forex Factory 
fx_database = mongo_client["forex-factory"]
fx_collection = fx_database['fxdata']
forex_currencies = ['AUD', 'CAD', 'CHF', 'CNY', 'EUR', 'GBP', 'JPY', 'NZD', 'USD']
off_days = [6,7]

# Individual Server Information
server_database = mongo_client['registry']
server_collection = server_database['guilds']

# --- DISCORD STUFF ---

intents = discord.Intents.default()
intents.message_content = True

# CLIENT EVENTS 
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

global_guild_settings = {
    "announcement-channel": ""
}

# ---- Preset Messages -----

startup_message = str("""
    ## 🎉 **Bot Status: ONLINE** 🎉
    > ⚠️ **IMPORTANT DISCLAIMER:** This project is intended for **educational use only** to practice Python, Discord API, web scraping, and data analysis. **It is NOT designed for real-world financial trading, nor does it provide professional financial advice.** Do not rely on any data or predictions from this bot for real-money decisions. Note: All dates & timestamps given by this bot are in Eastern Standard time. It does not update automatically by location accessed. (sorry!)

    ## ✅ Post-Launch To-Do Checklist:
    Please ensure the following actions are completed to verify all systems are operating correctly:
    **Basic Command Check:**
        1. Run the `/help` command to view available commands.
        2. Run the `/register` and provide the servers "Server ID" (required for setting announcement channel)
        3. Use the `/set-announcement` to let Misty know where to send automated messages.
        4. Try any of the `/fx` commands! Misty is intended for quick on the fly reference to Forex Factory during conversation. 

    👋 Thanks for inviting me!
    """)

# -------------------------------------------

'''
FX interval refers to how often scraper.py is used to retrieve information. The other is a general interval for various usecases.
The reason I chose to do it this way is because although the scheduled times of news reactions are given on forex factory
that doesn't necessarily cover all possible updates that could occur on the main page. For example if some unforseen event occurs
having been relevant to USD is added randomly, having a continued refresh loop checking for new events will catch it.
'''
fx_interval_seconds = 600
system_interval_seconds = 5

async def fx_refresh_loop():
    await client.wait_until_ready()
    
    # Simple counters to track how many times the loop has run
    run_count = 0

    # This loop runs forever until the bot is manually stopped
    while not client.is_closed():
        run_count += 1

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] Loop Run #{run_count}: Printing to terminal:")
        print(f"Scraper will check for new data in 10mins.")

        result = subprocess.run([sys.executable, '../services/scraper.py'], capture_output=True, text=True).stdout

        # only god knows how this works
        channel = None
        channel_id = global_guild_settings['announcement-channel']

        if channel_id != "":
            channel = client.get_channel(int(channel_id))
        else:
            pass

        if channel != None:
                
                print(result, "No Updates. Passing over.")
                # turning the result string into a useable format
                if result != '[]':
                    result = result.replace("'",'"')
                    data = json.loads(result)

                    embed = discord.Embed(
                    title=f"📢 **Economic Data Release:**",
                    color=discord.Color.blue()
                    )

                    for event in data:

                        # theres probably a way better way to do this but im lazy
                        new_vals = []
                        if 'actual' in event:
                            new_vals.append((event['actual'], 'actual'))
                        else:
                            event['actual'] = 'N/A'
                            new_vals.append((event['actual'], 'actual'))

                        if 'forecast' in event: 
                            new_vals.append((event['forecast'], 'forecast'))
                        else:
                            event['forecast'] = 'N/A'
                            new_vals.append((event['forecast'], 'forecast'))

                        if 'previous' in event: 
                            new_vals.append((event['previous'], 'previous'))
                        else:
                            event['previous'] = 'N/A'
                            new_vals.append((event['previous'], 'previous'))



                        embed.add_field(
                            name=f"{event['currency-impacted']} - {event['event-title']}:",
                            value=f"**New Values:** Actual: {new_vals[0][0]}, Forecast: {new_vals[1][0]} Previous: {new_vals[2][0]}\n**Scheduled Update Time:** {event['time-occured']}",
                            inline=False
                        )

                await channel.send(embed=embed)
        else:
            pass


        # Wait for the specified interval before running the loop again
        await asyncio.sleep(fx_interval_seconds)

async def system_refresh_loop():
    await client.wait_until_ready()
    sys_run_count = 0

    # to track if we sent the message that day. We get 1 send per day.
    market_open_msg = 0
    market_close_msg = 0

    while not client.is_closed():
        sys_run_count += 1

        # if 24hrs worth of 5 seconds pass
        if sys_run_count == 17268:
            # reset the message counts:
                sys_run_count = 0
                market_open_msg = 0
                market_close_msg = 0

                sys_run_count += 1
        else:
            pass        

        curr_day = datetime.now().isoweekday()

        # only god knows how this works
        channel = None
        channel_id = global_guild_settings['announcement-channel']

        if channel_id != "":
            channel = client.get_channel(int(channel_id))
        else:
            pass

        if channel != None:
            # INSIDE HERE IS WHERE ANY AUTOMATIC ANNOUNCEMENTS ON X TIME INTERVAL NEED TO BE BUILT.
            if market_open_msg == 0: 
                if datetime.now().hour == 9 and datetime.now().minute == 30 and curr_day not in off_days:
                    timestamp = datetime.now().strftime("%I:%M %p EST")
                    
                    embed = discord.Embed(
                        title="🔔 US Market Open Alert! 🔔",
                        description="The **NYSE** and **Nasdaq** are officially **OPEN** for business at 9:30 AM EST! The session is underway.",
                        color=discord.Color.gold()
                    )
                    
                    embed.add_field(
                        name="✅ Pre-Trade Reminders:",
                        value="Be sure to stick to your trading strategy!",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="📰 News Check",
                        value="Review any last-minute economic or company news.",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="📊 Indices Check",
                        value="Note the current direction of major benchmarks (S&P 500, Nasdaq).",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="🛑 Risk Management",
                        value="Confirm your stop-losses and position sizing before executing trades.",
                        inline=True
                    )
                    
                    embed.set_footer(text=f"Good luck and happy trading! | Sent: {timestamp}")

                    await channel.send(embed=embed) # type: ignore
                    market_open_msg += 1

            if market_close_msg == 0:
                if datetime.now().hour == 4 and datetime.now().minute == 00 and curr_day not in off_days:
                    timestamp = datetime.now().strftime("%I:%M %p EST")
                    
                    embed = discord.Embed(
                        title="🔔 Market Close: Trading Day Complete! 🔔",
                        description="The **NYSE** and **Nasdaq** regular trading sessions are officially **CLOSED** at 4:00 PM EST. The floor is quiet, but the analysis begins!",
                        color=discord.Color.dark_purple() 
                    )
                    
                    embed.add_field(
                        name="📝 End-of-Day Checklist:",
                        value="Focus now shifts to review, logging, and planning for tomorrow.",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="📋 Trade Journaling",
                        value="Log all executed trades, noting your rationale, outcome, and emotional state.",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="📉 Daily Review",
                        value="Analyze key price action, volume, and major economic data releases.",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="🗓️ Tomorrow's Prep",
                        value="Identify potential movers and update your watchlist for the next open.",
                        inline=False
                    )
                    
                    embed.set_footer(text=f"Session officially concluded at 4:00 PM EST | Sent: {timestamp}")

                    await channel.send(embed=embed) # type: ignore
                    market_close_msg += 1

      
        # Pass the announcement if no announcement channel is set.
        else:
            pass

        # Wait for the specified interval before running the loop again
        await asyncio.sleep(system_interval_seconds)

# --- EVENTS ----

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

    channel_id = 1441475314445320212 
    channel = client.get_channel(channel_id)
    #await channel.send(f'{startup_message}') # type: ignore


    # BACKGROUND TASKS:
    client.loop.create_task(system_refresh_loop())
    client.loop.create_task(fx_refresh_loop())

    # For slash commands to work and appear on the users discord client we sync the command tree on startup
    try:
        await tree.sync()
        print("Command tree synced globally.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


# COMMAND EVENTS
@tree.command(
    name="debug-check-data", 
    description="Debug: Used to check what info Misty recieved from MongoDB."
)
async def data_check(interaction: discord.Interaction, authkey: str):
    if authkey == f"{key3}":
        data = mongoHelpers.get_all_news(collection_file=fx_collection)

        print(fx_collection, " <--- should be checking")
        print(data,' <-- recieved') 

        channel = interaction.channel

        await channel.send(f'curr server_id: {interaction.guild_id}') # type: ignore
    else:
        await interaction.response.send_message(f"Hello, {interaction.user.mention}! Your debug key is invalid.", ephemeral=False)


@tree.command(
    name="debug-force-update", 
    description="Debug: Force Misty to retrieve latest ForexFactory data."
)
async def force_update(interaction: discord.Interaction, authkey: str):
    
    print('FORCING UPDATE')
    print(authkey, key3)
    print(type(key3))
    
    if authkey == key3:

        # Create an Embed for successful update
        success_embed = discord.Embed(
            title="✅ Update Forced Successfully",
            description="Misty is now retrieving the latest ForexFactory data.",
            color=discord.Color.green() 
        )
        success_embed.add_field(
            name="Confirmation", 
            value="Check the console output or MongoDB for confirmation of the updated data.", 
            inline=False
        )
        
        # Send the success Embed
        await interaction.response.send_message(embed=success_embed, ephemeral=False)

        # Needs to run after the embed is sent or else it times out.
        result = subprocess.run([sys.executable, '../services/scraper.py'], capture_output=True, text=True)
        print(result)
            
    else:
        # Create an Embed for invalid key
        error_embed = discord.Embed(
            title="❌ Debug Key Invalid",
            description=f"Hello, {interaction.user.mention}! The authentication key you provided is incorrect.",
            color=discord.Color.red()
        )
            
        error_embed.add_field(
            name="Required Key", 
            value="Please ensure you are using the correct debug key.", 
            inline=False
        )
        
        # Send the error Embed
        await interaction.response.send_message(embed=error_embed, ephemeral=False)


@tree.command(
    name="fx-last-update", 
    description="Fetches the timestamp of the last time Misty scraped Forex Factory."
)
async def last_update(interaction: discord.Interaction):
    last_update = mongoHelpers.get_last_timestamp(collection_file=fx_collection)

    update_embed = discord.Embed(
        title="🗓️ Last Forex Factory Scrape Time",
        description=f"The latest data retrieved by Misty is from the following time:",
        color=discord.Color.blue() # A calming blue color
    )
    
    update_embed.add_field(
        name="Last Scrape Timestamp",
        value=f"**{last_update}**",
        inline=False
    )
    
    update_embed.set_footer(
        text=f"Requested by {interaction.user.display_name}", 
        icon_url=interaction.user.display_avatar.url
    )

    await interaction.response.send_message(embed=update_embed, ephemeral=False)

@tree.command(
    name="register", 
    description="Register your server with Misty's Database! (required for setting announcement channel)"
)
async def guild_register(interaction: discord.Interaction, server_id: str, server_name: str):
    
    int_guild_id = int(server_id)
    true_guild_id = int_guild_id
    guild = client.get_guild(true_guild_id)
    
    print(server_id)
    print(type(server_id))
    channel = interaction.channel

    if guild is not None:
        
        success_fetch_embed = discord.Embed(
            title="✅ Server ID Validated",
            description=f"Successfully fetched server details for registration.",
            color=discord.Color.blue()
        )
        success_fetch_embed.add_field(
            name="Chosen Server",
            value=f"**{guild.name}** (`{guild.id}`)",
            inline=False
        )
        success_fetch_embed.set_footer(text=f"Initiated by {interaction.user.display_name}")

        await interaction.response.send_message(embed=success_fetch_embed, ephemeral=False)        
        await channel.send("Attempting to register this server with the database...") # type: ignore
        
        res = mongoHelpers.register_guild(collection_file=server_collection, guild_id=server_id, server_name=server_name)
        
        
        result_embed = discord.Embed(
            title="📝 Registration Result",
            description="The database operation is complete.",
            color=discord.Color.green() if "success" in res.lower() else discord.Color.gold()
        )
        result_embed.add_field(
            name="Database Response",
            value=f"```\n{res}\n```",
            inline=False
        )
        await channel.send(embed=result_embed) # type: ignore

    else:
        error_embed = discord.Embed(
            title="❌ Server Fetch Failed",
            description=f"Hello, {interaction.user.mention}! The provided Server ID could not be matched to an accessible Discord server.",
            color=discord.Color.red()
        )
        error_embed.add_field(
            name="Troubleshooting",
            value="Please ensure the ID is correct and that the bot is a member of that server.",
            inline=False
        )
        
        await interaction.response.send_message(embed=error_embed, ephemeral=False)


@tree.command(
    name="set-announcement-channel", 
    description="Sets which channel Misty sends automated announcement messages to!"
)
async def set_announcement(interaction: discord.Interaction, channel_id: str, server_id: str):
    
    int_channel_id = int(channel_id)
    int_guild_id = int(server_id)
    true_guild_id = int_guild_id

    res = mongoHelpers.check_guild_exists(collection_file=server_collection, guild_id=true_guild_id)
    
    if res == '[404]':
        not_found_embed = discord.Embed(
            title="⚠️ Server Not Registered",
            description=f"Hello, {interaction.user.mention}! That server was not found in my database.",
            color=discord.Color.gold()
        )
        not_found_embed.add_field(
            name="Action Required",
            value=f"Please make sure you've registered Server-ID:**{server_id}** with me using `/register`. If you have, please ensure the ID is correct.",
            inline=False
        )
        
        await interaction.response.send_message(embed=not_found_embed, ephemeral=True) # Changed to ephemeral=True since it's an error for the user
        
    else:
        channel = interaction.channel
        await channel.send("Attempting to set announcement channel...", delete_after=5) # type: ignore

        announcement_channel_id = int_channel_id 
        target_channel = client.get_channel(announcement_channel_id) # Use a clearer variable name

        print(target_channel)
        print(type(target_channel))

        if target_channel is not None:
            
            fetch_success_embed = discord.Embed(
                title="✅ Channel ID Validated",
                description=f"Announcement channel fetched successfully. Attempting to save to database...",
                color=discord.Color.blue()
            )
            fetch_success_embed.add_field(
                name="Chosen Channel",
                value=f"{target_channel.mention}",
                inline=False
            )
            await interaction.response.send_message(embed=fetch_success_embed, ephemeral=True)
            
            res = mongoHelpers.set_announcement_channel(collection_file=server_collection, guild_id=server_id, channel_id=channel_id)
            global_guild_settings['announcement-channel'] = channel_id

            confirmation_embed = discord.Embed(
                title="✅ Announcement Channel Set!",
                description=f"Automatic announcements will now be sent to **{target_channel.mention}** as they occur.",
                color=discord.Color.green()
            )
            await target_channel.send(embed=confirmation_embed) # type: ignore
            
        else: 
            channel_error_embed = discord.Embed(
                title="❌ Channel Fetch Failed",
                description=f"Hello, {interaction.user.mention}! The Announcement Channel ID provided could not be fetched.",
                color=discord.Color.red()
            )
            channel_error_embed.add_field(
                name="Troubleshooting",
                value="Please ensure the ID is correct and that I have **view and send permissions** in that channel.",
                inline=False
            )
            
            await interaction.response.send_message(embed=channel_error_embed, ephemeral=True)

@tree.command(
    name="fx-all-news", 
    description="ForexFactory: Quickly reference today's scheduled news."
)                   
async def sendAll(interaction: discord.Interaction):

    data = mongoHelpers.get_all_news(collection_file=fx_collection)   

    # not including the first document since its a timestamp, NOT an event entry.
    data = data[1:]

    my_embed = discord.Embed(
        title=f"MARKET VOLATILITY - All News:",
        description=f"All news events scheduled for the next 24 hours.",
        url="https://www.forexfactory.com",

        # documentation for all of the included colors: 
        color=discord.Color.blue(),
    )

    # Navigating to image:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_asset_path = os.path.join(script_dir, 'assets', 'fx_factory_icon.png')
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
                name=f"{emj} {event['currency-impacted']} - {event['event-title']}",
                value=f"Time Scheduled: {event['time-occured']}",
                inline=True
            )
        else:
            my_embed.add_field(
                name=f"{emj} {event['currency-impacted']} - {event['event-title']}",
                value=f"Actual: {event['actual']}    Forecast: {event['forecast']}    Previous: {event['previous']}\nTime Scheduled: {event['time-occured']}",
                inline=False
            )


    # bottom text
    my_embed.set_footer(text="Data is scraped from Forex Factory and is provided for informational purposes only.")
    my_embed.set_author(name="🌐 Forex Factory", url="https://www.forexfactory.com", icon_url="attachment://indicator.png")
    await interaction.response.send_message(embed=my_embed, files=[icon])


@tree.command(
    name="fx-currency-lookup", 
    description="ForexFactory: Displays news from ForexFactory.com relevant to your chosen currency."
)                   
async def sendSpecificCurrency(interaction: discord.Interaction, currency: str):

    if currency.upper() not in forex_currencies:
            await interaction.response.send_message(f'Hey {interaction.user.mention} you wrote: "{currency}" which is not a tracked currency.\nHere is a list of currencies ForexFactory tracks:\n{forex_currencies}')
    else:
        data = mongoHelpers.currency_specific_news(collection_file=fx_collection, currency=currency.upper())   
        
        my_embed = discord.Embed(
            title=f"MARKET VOLATILITY - {currency.upper()} News:",
            description=f"All news events pertaining to {currency.upper()} for the next 24 hours.",
            url="https://www.forexfactory.com",

            # documentation for all of the included colors: 
            color=discord.Color.blue(),
        )

        script_dir = os.path.dirname(os.path.abspath(__file__))
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
        
        await interaction.response.send_message(embed=my_embed, files=[icon])


@tree.command(
    name="fx-pair-lookup", 
    description="ForexFactory: Displays news from ForexFactory.com relevant to your currency pair."
)                   
async def sendPair(interaction: discord.Interaction, base_currency: str, quote_currency: str):

    if base_currency.upper() not in forex_currencies and quote_currency.upper() not in forex_currencies:
        await interaction.response.send_message(f'Hey {interaction.user.mention} Neither of the currencies you gave are a tracked currency.\nHere is a list of currencies ForexFactory tracks:\n{forex_currencies}')

    elif base_currency.upper() not in forex_currencies or quote_currency.upper() not in forex_currencies:
        await interaction.response.send_message(f'Hey {interaction.user.mention} One of the currencies you gave are a tracked currency.\nHere is a list of currencies ForexFactory tracks:\n{forex_currencies}')

    else:
        data = mongoHelpers.pair_specific_news(collection_file=fx_collection, currency1=base_currency.upper(), currency2=quote_currency.upper())   
        print(data)
        
        my_embed = discord.Embed(
            title=f"MARKET VOLATILITY - {base_currency}/{quote_currency} News:",
            description=f"All news events pertaining to your chosen pair in the next 24 hours.",
            url="https://www.forexfactory.com",

            color=discord.Color.blue(),
        )

        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_asset_path = os.path.join(script_dir, 'assets', 'fx_factory_icon.png')
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
                    name=f"{emj} {event['currency-impacted']} - {event['event-title']}",
                    value=f"Time Scheduled: {event['time-occured']}",
                    inline=True
                )
            else:
                my_embed.add_field(
                    name=f"{emj} {event['currency-impacted']} - {event['event-title']}",
                    value=f"Actual: {event['actual']}    Forecast: {event['forecast']}    Previous: {event['previous']}\nTime Scheduled: {event['time-occured']}",
                    inline=False
                )

        my_embed.set_footer(text="Data is scraped from Forex Factory and is provided for informational purposes only.")
        my_embed.set_author(name="🌐 Forex Factory", url="https://www.forexfactory.com", icon_url="attachment://indicator.png")
        await interaction.response.send_message(embed=my_embed, files=[icon])


@tree.command(
    name="fx-high-impact",
    description="ForexFactory: Quickly reference today's high-impact forex news."
)
async def sendHighImpact(interaction: discord.Interaction):

    data = mongoHelpers.high_impact_news(collection_file=fx_collection)

    # Other information such as the embed thumbnail, fields, and author is not set here. Its set in their own functions.
    my_embed = discord.Embed(
        title="MARKET VOLATILITY - High-Impact News:",
        description="All Red Folder events scheduled for the next 24 hours.",
        url="https://www.forexfactory.com",

        # documentation for all of the included colors: 
        color=discord.Color.blue(),
    )

    # Navigating to image:
    script_dir = os.path.dirname(os.path.abspath(__file__))
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

    # bottom text
    my_embed.set_footer(text="Data is scraped from Forex Factory and is provided for informational purposes only.")
    
    # image appears on top left. then the author name. the author name will have a link attached.
    my_embed.set_author(name="🌐 Forex Factory", url="https://www.forexfactory.com", icon_url="attachment://indicator.png")

    await interaction.response.send_message(embed=my_embed, files=[icon])


# To render a button OR a GROUP of buttons we need to write a class to handle that specific situation
class View(discord.ui.View):
    # This line creates the button which is generated by the function on_button_click() which is defined below it.
    # All buttons need to have a function attached or else this line alone will be highlighted squiggly/incorrect syntax
    @discord.ui.button(label="Click Me", style=discord.ButtonStyle.success, emoji="✅")

    # You MUST pass: self, button, and interaction. 
    async def on_success_click(self, button, interaction):
        # Here is where you can determine how the bot responds 
        await button.response.send_message(f"Button was clicked.")
    

    # To render more than one button you literally just copy and paste the same structure and edit as need:

    @discord.ui.button(label="Click Me", style=discord.ButtonStyle.danger, emoji="❌")
    async def on_failure_click(self, button, interaction):
        await button.response.send_message(f"Button was clicked.")

    @discord.ui.button(label="Click Me", style=discord.ButtonStyle.primary, emoji="⚙️")
    async def on_premium_click(self, button, interaction):
        await button.response.send_message(f"Button was clicked.")
    

@tree.command(
    name="send-button",
    description="Gives you something to click on"
)
async def sendButton(interaction: discord.Interaction):
    # To get the button to send as response to this command you pass the "View()" class we previously defined to the send_message portion:
    await interaction.response.send_message(view=View())


@tree.command(
    name="embed-with-button",
    description="sends an embed that also has a button"
)
async def sendButtonEmbed(interaction: discord.Interaction):
    button_embed = discord.Embed(
        title="Placeholder Embed",
        description="This is a placeholder embed. Click this button!"
    )

    await interaction.response.send_message(embed=button_embed, view=View())

# --- DROPDOWN MENU ---

# To build a dropdown menu you need to make a class view for the menu itself. THEN a class view for the dropdowns. Then link it to a command.

# Dropdown menu class:
class Dropdown(discord.ui.Select):
    def __init__(self):

        # options which will be passed to the menu
        drop_down_options = [
            discord.SelectOption(
                label="Option 1",
                value="Description of option 1",
                emoji="⚫"
            ),

            discord.SelectOption(
                label="Option 2",
                value="Description of option 2",
                emoji="⚫"
            ),

            discord.SelectOption(
                label="Option 3",
                value="Description of option 3",
                emoji="⚫"
            )
        ]

        # responsible for the placeholder text that shows before the user clicked the dropdown
        # also responsible for letting you pick 1 or more values. For a normal dropdown only allow one at a time.
        super().__init__(placeholder="Please choose an option:", min_values=1, max_values=1, options=drop_down_options)

    # this function must be called callback (DO NOT CHANGE)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{self.values[0]}")

# Overarching menu class:
class MenuView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(Dropdown())

@tree.command(
    name="send-dropdown-menu",
    description="sends a dropdown menu for you to interact with"
)
async def sendDropDown(interaction: discord.Interaction):
    await interaction.response.send_message(view=MenuView(), delete_after=(5))


client.run(token=str(key))

