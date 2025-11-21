import discord
from discord.ext import commands
from discord import app_commands
from dotenv import find_dotenv, load_dotenv
import os

# Grabbing bot token
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
key = os.getenv('TOKEN')

# --- DISCORD STUFF ---

intents = discord.Intents.default()
intents.message_content = True

# CLIENT EVENTS 
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

    # For slash commands to work and appear on the users discord client we sync the command tree on startup
    try:
        await tree.sync()
        print("Command tree synced globally.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

# COMMAND EVENTS
# Use this wrapper to define a command:
# This is saying: Listen out for a user invoking /greet
@tree.command(
    # Command name: e.g. /greet
    name="greet", 
    # Command desc in list:
    description="Says hello using a slash command!"
)
# When /greet is invoked do the following
async def greet_command(interaction: discord.Interaction):
    
    # This says: Wherever interaction occured. respond to the interaction. by sending a message (.......)

    # interaction.user refers to the user who used the command.  |  ephermeral means if others can see the msg. True for No, False for yes.
    await interaction.response.send_message(f"Hello, {interaction.user.mention}! This is a slash command.", ephemeral=False)

@tree.command(
    name="printer", 
    description="I will print whatever you give me."
)                   
# print: str | is saying that this func will have atleast 1 arg passed into it. Names of the params are arbitrary, will reference a data type.
# the variable name itself is previewed on the discord client in the command list so you can use it to make commands more intuitive.
# for example. /news - currency  | this prompts the user to type the currency of news they want without extra explanation.
async def printer(interaction: discord.Interaction, your_sentence: str):
    # Like a typical python function you can make calls to the print variable we passed in.
    print(your_sentence)
    
    # if you hover over send_message() you'll find more attributes for what happens to the message after sending.
    # delete after x seconds will be useful for spam.
    await interaction.response.send_message(your_sentence, delete_after=5)

client.run(token=str(key))
