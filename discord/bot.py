import discord
from discord import app_commands
from dotenv import find_dotenv, load_dotenv
from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os, asyncio, sys, subprocess
from helpers import mongoHelpers

# Grabbing bot token & db password
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
key = os.getenv('TOKEN')
key2 = os.getenv('MongoDB')
key3 = os.getenv("MistyDebug")

# Setting up MongoDB:
uri = f'mongodb+srv://rftestingnyc_db_user:{key2}@cluster.4n8bbif.mongodb.net/?appName=Cluster'
mongo_client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection to MongoDB
try:
    mongo_client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

database = mongo_client["forex-factory"]
collection = database['fxdata']
forex_currencies = ['AUD', 'CAD', 'CHF', 'CNY', 'EUR', 'GBP', 'JPY', 'NZD', 'USD']

# --- DISCORD STUFF ---

intents = discord.Intents.default()
intents.message_content = True

# CLIENT EVENTS 
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Set the desired interval in seconds (e.g., 3600 seconds = 1 hour)
loop_interval_seconds = 3600

async def timed_loop():
    # Wait until the Discord client is fully connected
    await client.wait_until_ready()
    
    # Simple counter to track how many times the loop has run
    run_count = 0
    
    # This loop runs forever until the bot is manually stopped
    while not client.is_closed():
        run_count += 1
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] Loop Run #{run_count}: Printing to terminal:")

        # Sends the signal to run the scraping script.
        result = subprocess.run([sys.executable, '../services/scraper.py'], capture_output=True, text=True)

        #print(result)

        # TODO: FIGURE OUT A BETTER WAY TO SEND INFO BACK TO THE BOT FOR FILTERING PURPOSES AND SUCH.
        # DOING MONGODB SEARCHING IS PROBALBY WAY EASIER THAN MAKING A FUNCTION TO SEARCH YOURSELF.
        # print(result)

        print(f"Scraper will check for new data in {loop_interval_seconds / 3600} hours(s).")
        # Wait for the specified interval before running the loop again
        await asyncio.sleep(loop_interval_seconds)



# --- EVENTS ----

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

    # startup_message = f"FXFACTORY LAST SCRAPE: {mongoHelpers.get_last_timestamp(collection_file=collection)}"
    startup_message = "Startup"
    # You can also send a message to a specific channel on startup, for example:
    channel_id = 1441475314445320212 # Replace with your channel ID
    channel = client.get_channel(channel_id)
    # await channel.send(f'{startup_message}') # type: ignore

    # TASKS:
    client.loop.create_task(timed_loop())
    # For slash commands to work and appear on the users discord client we sync the command tree on startup
    try:
        await tree.sync()
        print("Command tree synced globally.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# COMMAND EVENTS
# Use this wrapper to define a command:
# This is saying: Listen out for a user invoking /greet
@tree.command(
    # Command name: e.g. /greet
    name="debug-check-data", 
    # Command desc in list:
    description="Debug: Used to check what info Misty recieved from MongoDB."
)
# When /greet is invoked do the following
async def data_check(interaction: discord.Interaction, authkey: str):
    # This says: Wherever interaction occured. respond to the interaction. by sending a message (.......)

    if authkey == f"{key3}":
        data = mongoHelpers.get_all_news(collection_file=collection)

        print(collection, " <--- should be checking")
        print(data,' <-- recieved') 

        # interaction.user refers to the user who used the command.  |  ephermeral means if others can see the msg. True for No, False for yes.
        await interaction.response.send_message(f"Hello, {interaction.user.mention}! RAW DATA RECIEVED:\n{data}", ephemeral=True)
    else:
        await interaction.response.send_message(f"Hello, {interaction.user.mention}! Your debug key is invalid.", ephemeral=True)

@tree.command(
    name="debug-force-update", 
    description="Debug: Force Misty to retrieve latest ForexFactory data."
)
async def force_update(interaction: discord.Interaction, authkey: str):
    if authkey == f"{key3}":

        result = subprocess.run([sys.executable, '../services/scraper.py'], capture_output=True, text=True)

        await interaction.response.send_message(f"{result}", ephemeral=False)
    else:
        await interaction.response.send_message(f"Hello, {interaction.user.mention}! Your debug key is invalid.", ephemeral=False)


@tree.command(
    name="fx-all-news", 
    description="ForexFactory: Quickly reference today's scheduled news."
)                   

async def sendAll(interaction: discord.Interaction):

    data = mongoHelpers.get_all_news(collection_file=collection)   

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
                value=f"Actual: {event['actual']},   Forecast: {event['forecast']},   Previous: {event['previous']}\nTime Scheduled: {event['time-occured']}",
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
# print: str | is saying that this func will have atleast 1 arg passed into it. Names of the params are arbitrary, will reference a data type.
# the variable name itself is previewed on the discord client in the command list so you can use it to make commands more intuitive.
# for example. /news - currency  | this prompts the user to type the currency of news they want without extra explanation.
async def sendSpecificCurrency(interaction: discord.Interaction, currency: str):

    if currency.upper() not in forex_currencies:
            await interaction.response.send_message(f'Hey {interaction.user.mention} you wrote: "{currency}" which is not a tracked currency.\nHere is a list of currencies ForexFactory tracks:\n{forex_currencies}')
    else:
        # Like a typical python function you can make calls to the print variable we passed in.
        data = mongoHelpers.currency_specific_news(collection_file=collection, currency=currency.upper())   
        
        # Other information such as the embed thumbnail, fields, and author is not set here. Its set in their own functions.
        my_embed = discord.Embed(
            title=f"MARKET VOLATILITY - {currency.upper()} News:",
            description=f"All news events pertaining to {currency.upper()} for the next 24 hours.",
            url="https://www.forexfactory.com",

            # documentation for all of the included colors: 
            color=discord.Color.blue(),
        )

        # Navigating to image:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_asset_path = os.path.join(script_dir, 'assets', f'{currency}.png')
        icon = discord.File(icon_asset_path, filename="fx_icon.png") 

        # Adding an image to an embed. Will appear in the top right corner of the message.
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
                    value=f"Actual: {event['actual']},   Forecast: {event['forecast']},   Previous: {event['previous']}\nTime Scheduled: {event['time-occured']}",
                    inline=False
                )


        # bottom text
        my_embed.set_footer(text="Data is scraped from Forex Factory and is provided for informational purposes only.")
        
        # image appears on top left. then the author name. the author name will have a link attached.
        my_embed.set_author(name="🌐 Forex Factory", url="https://www.forexfactory.com", icon_url="attachment://indicator.png")
        
        # if you hover over send_message() you'll find more attributes for what happens to the message after sending.
        # delete after x seconds will be useful for spam.
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
        data = mongoHelpers.pair_specific_news(collection_file=collection, currency1=base_currency.upper(), currency2=quote_currency.upper())   
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
                    value=f"Actual: {event['actual']},   Forecast: {event['forecast']},   Previous: {event['previous']}\nTime Scheduled: {event['time-occured']}",
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

    data = mongoHelpers.high_impact_news(collection_file=collection)

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
            value=f"Actual: {event['actual']}, Forecast: {event['forecast']}, Previous: {event['previous']}\nTime Scheduled: {event['time-occured']}",
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

