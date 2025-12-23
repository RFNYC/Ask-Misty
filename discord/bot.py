import discord
import os, asyncio, sys, subprocess, json
import commands, static_messages

from discord import app_commands
from dotenv import find_dotenv, load_dotenv
from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from helpers import mongoHelpers, yfinanceHelpers
from rag import build_rag_response

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
key = os.getenv('TOKEN')
key2 = os.getenv('MongoDB')
key3 = os.getenv("MistyDebug")

# will get passed to all functions that need to find assets
script_dir = os.path.dirname(os.path.abspath(__file__))

uri = f'mongodb+srv://rftestingnyc_db_user:{key2}@cluster.4n8bbif.mongodb.net/?appName=Cluster'
mongo_client = MongoClient(uri, server_api=ServerApi('1'))

try:
    mongo_client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Forex Factory Information
fx_database = mongo_client["forex-factory"]
fx_collection = fx_database['fxdata']
forex_currencies = ['AUD', 'CAD', 'CHF', 'CNY', 'EUR', 'GBP', 'JPY', 'NZD', 'USD']
missing_icons = ['CAD', 'AUD', 'NZD', 'CHF']
off_days = [6,7]

# Individual Server Information
server_database = mongo_client['registry']
server_collection = server_database['guilds']

# Rag Information
rag_database = mongo_client['static-info']
rag_collection = rag_database['vector-embeddings']

# --- DISCORD STUFF ---

intents = discord.Intents.default()
intents.message_content = True

# CLIENT EVENTS 
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

global_guild_settings = {
    "announcement-channel": ""
}

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
                    embed = static_messages.market_open.createEmbed(timestamp)

                    await channel.send(embed=embed) # type: ignore
                    market_close_msg += 1
                
                if market_close_msg == 0:
                    if datetime.now().hour == 4 and datetime.now().minute == 00 and curr_day not in off_days:
                        timestamp = datetime.now().strftime("%I:%M %p EST")
                        embed = static_messages.market_close.createEmbed(timestamp)

                        await channel.send(embed=embed) # type: ignore
                        market_close_msg += 1

        # Ignore the announcement if no announcement channel is set.
        else:
            pass

        # Wait for the specified interval before running the loop again
        await asyncio.sleep(system_interval_seconds)

async def send_activation_message():

    # Assuming end user has registered a channel for the server we want misty to send a message that its online.
    # to do this we have to retrieve all announcement channels and then send the message one by one.
    channels = mongoHelpers.get_announcement_channels(server_collection)
    for id in channels:
        target = client.get_channel(int(id))

        if target:
            embed = static_messages.bot_online.createEmbed()
            # await target.send(embed=embed) # type: ignore
    

# --- EVENTS ----

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

    # BACKGROUND TASKS:
    # Basically tells the client to run x func this once the bot is fully active & has all cached information.
    client.loop.create_task(system_refresh_loop())
    client.loop.create_task(fx_refresh_loop())
    client.loop.create_task(send_activation_message())

    # For slash commands to work and appear on the users discord client we sync the command tree on startup
    try:
        await tree.sync()
        print("Command tree synced globally.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@client.event
async def on_guild_join(guild: discord.Guild):
    print(f"Joined a new server: {guild.name} (ID: {guild.id})")
    
    target_channel = guild.system_channel

    if target_channel:
        embed = static_messages.bot_joined.createEmbed()
        await target_channel.send(embed=embed)

# COMMAND EVENTS

# ----- SETUP COMMANDS ------
# Not to be moved into commands, very finicky, dont want to debug.

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
        await channel.send("Attempting to register this server with the database...", delete_after=3) # type: ignore
        
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
        await channel.send("Attempting to set announcement channel...", delete_after=3) # type: ignore

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

# ---- END OF SETUP COMMANDS -----

@tree.command(
    name="misty-help", 
    description="Sends a list of commands and a description of what they do."
)
async def send_help(interaction: discord.Interaction):
    # Page numbers are hardcoded, im lazy and this wont get updated that often where it has to be dynamic
    page_number = 0

    class MenuButtons(discord.ui.View):
        @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
        async def previous_button_callback(self, interaction: discord.Interaction, button):
            nonlocal page_number
            if page_number == 0:
                pass
            else:
                page_number -= 1
                embed = commands.misty_help.createEmbed(page_number)
                await interaction.response.edit_message(embed=embed, view=MenuButtons())
    
        @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
        async def next_button_callback(self, interaction: discord.Interaction, button):
            nonlocal page_number
            if page_number == 1:
                pass
            else:
                page_number += 1
                embed = commands.misty_help.createEmbed(page_number)
                await interaction.response.edit_message(embed=embed, view=MenuButtons())

    embed = commands.misty_help.createEmbed(page_number)
    # saving await responses to variables allows you to manipulate it later, ex: sent_message.edit()
    sent_message = await interaction.response.send_message(embed=embed, view=MenuButtons(), delete_after=30)


# Not being moved to commands until it is finished.
@tree.command(
        name="define-strategy",
        description="Create a strategy for Misty to backtest!"
)
async def define_strategy(interaction: discord.Interaction, strategy_name: str, indicator1: str, time_period1: str, indicator2: str, time_period2: str, buy_condition: str, sell_condition: str):
    
    """
    Note: I know this is super tedious and doesn't allow for many strategies or complex capabilities but this is the only option I could think of without
    having to learn NLP and creating an algorithm for it. That could take me months to implement from scratch. The other option is feeding into an LLM but 
    that's not very helpful either given AI hallucinations and generally just variance in response.

    So keeping that in mind, the resulting command is a very rigid proof of concept.
    Lets begin by making a json object for this information.
    """

    strategy = {
        f"{strategy_name}": {

            "indicators": [
                {
                    "id": "indicator1", 
                    "type": f"{indicator1}", 
                    "time-period1": f"{time_period1}"
                },
                {
                    "id": "indicator1", 
                    "type": f"{indicator2}", 
                    "time-period1": f"{time_period2}"
                },
            ],

            "rules": {
                "buy": f"{buy_condition}",
                "sell": f"{sell_condition}"
            }
        }
    }

    # obtaining guild id for helper
    guild = interaction.guild_id
    try:
        result = mongoHelpers.set_new_strategy(collection_file=server_collection, strategy_object=strategy, guild_id=guild)
    except Exception as e:
        print(f"error: {e}")

    await interaction.response.send_message(f"set strategy response: {result}")


# Not being moved to commands until it is finished.
@tree.command(
    name="backtest-strategy", 
    description="Have Misty generate a report on any of the servers saved strategies!"
)
async def backtest(interaction: discord.Interaction, strategy_name: str, timeframe: str, years: int):

    await interaction.response.defer()

    server = interaction.guild_id
    response = yfinanceHelpers.backtest_strategy(collection_file=server_collection, strategy_name=strategy_name, guild_id=server, timeframe=timeframe, years=years)

    await interaction.followup.send(response)


@tree.command(
    name="risk-calculation",
    description="Have Misty generate the correct lot size for your positon based on your risk tolerance."
)
async def risk_calc(interaction: discord.Interaction, pair: str, equity: float, entry_price: float, stop_loss: float, risk_percentage: float):

    account_equity = equity

    if risk_percentage <= 0 or account_equity <= 0:
        await interaction.response.send_message(
            "**Error:** Risk percentage and Account Equity must be positive values.", 
            ephemeral=True
        )
        return
    else:
        risk_pips = abs(entry_price - stop_loss) * 10000  # assuming its a 4-decimal pair for simplicity.

        if risk_pips == 0:
            await interaction.response.send_message(
                "**Error:** Entry Price and Stop Loss Price cannot be the same. Risk in pips is zero.",
                ephemeral=True
            )
            return
        else:
            embed = commands.risk_calculation.createEmbed(yfinanceHelpers, equity, risk_percentage, entry_price, stop_loss, pair)
            await interaction.response.send_message(embed=embed, ephemeral=False)


@tree.command(
    name="fx-last-update", 
    description="ForexFactory: Fetches the timestamp of the last time Misty scraped Forex Factory."
)
async def last_update(interaction: discord.Interaction):
    embed = commands.fx_last_update.createEmbed(mongoHelpers, fx_collection, interaction)
    await interaction.response.send_message(embed=embed, ephemeral=False)
    

@tree.command(
    name="fx-currency-lookup", 
    description="ForexFactory: Displays news from ForexFactory.com relevant to your chosen currency."
)                   
async def sendSpecificCurrency(interaction: discord.Interaction, currency: str):

    if currency.upper() not in forex_currencies:
            await interaction.response.send_message(f'Hey {interaction.user.mention} you wrote: "{currency}" which is not a tracked currency.\nHere is a list of currencies ForexFactory tracks:\n{forex_currencies}')
    else:
        embed, icon = commands.fx_currency_lookup.createEmbed(mongoHelpers, fx_collection, currency, missing_icons, script_dir)
        await interaction.response.send_message(embed=embed, files=[icon])


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
        embed, icon = commands.fx_pair_lookup.createEmbed(mongoHelpers, fx_collection, base_currency, quote_currency, script_dir)
        await interaction.response.send_message(embed=embed, files=[icon])


@tree.command(
    name="fx-high-impact",
    description="ForexFactory: Quickly reference today's high-impact forex news."
)
async def sendHighImpact(interaction: discord.Interaction):
    embed, icon = commands.fx_high_impact.createEmbed(mongoHelpers, fx_collection, script_dir)
    await interaction.response.send_message(embed=embed, files=[icon])


@tree.command(
    name="ask-misty",
    description="If you have any questions about how a command works, or where information is sourced from, just ask!"
)
async def askMisty(interaction: discord.Interaction, question: str):
    # Required to allow the bot to think. Else bot will time out
    await interaction.response.defer()
    try:
        response = build_rag_response(rag_collection, question)
        embed = commands.ask_misty.createEmbed(question, response, interaction)
        await interaction.followup.send(embed=embed)
    except:
        await interaction.followup.send("It seems our agent is unavailable right now. In the meantime try: `/misty-help`!")

client.run(token=str(key))

