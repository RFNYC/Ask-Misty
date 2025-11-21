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

@tree.command(
    name="sheperd-facts",
    description="check wikipedia for dog info"
)
async def sendEmbed(interaction: discord.Interaction):
    # Other information such as the embed thumbnail, fields, and author is not set here. Its set in their own functions.
    my_embed = discord.Embed(
        title="German Sheperd",
        description="The German Shepherd, also known in Britain as an Alsatian, is a German breed of working dog of medium to large size. It is characterized by its intelligent and obedient nature. Its historical role was as a herding dog, for herding sheep.The German Shepherd, also known in Britain as an Alsatian, is a German breed of working dog of medium to large size. It is characterized by its intelligent and obedient nature. Its historical role was as a herding dog, for herding sheep.",
        url="https://en.wikipedia.org/wiki/German_Shepherd",

        # documentation for all of the included colors: 
        color=discord.Color.blue(),
    )

    # Adding an image to an embed. Will appear in the top right corner of the message.
    my_embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/d/d0/German_Shepherd_-_DSC_0346_%2810096362833%29.jpg")

    # Each field is added in the same way. Its done like this.
    my_embed.add_field(
        name="1890s",
        value="During the 1890s, attempts were being made to standardise dog breeds. Dogs were being bred to preserve traits that assisted in their job of herding sheep and protecting their flocks from predators. In Germany this was practised within local communities, where shepherds selected and bred dogs. It was recognised that the breed had the necessary skills for herding sheep, such as intelligence, speed, strength and keen sense of smell. The results were dogs that were able to do such things, but that differed significantly, both in appearance and ability, from one locality to another.",

        # IMPORTANT: The inline attribute determines whether or not any other fields can accompany this one on the same line.
        # IF set to false then the next field will appear under it, if set to true the next field will appear next to it.
        inline=False
    )
    my_embed.add_field(
        name="1900s",
        value="Empty"
    )

    my_embed.add_field(
        name="20th Century",
        value="Empty"
    )

    my_embed.add_field(
        name="Naming",
        value="Empty"
    )

    my_embed.set_footer(text="Information sourced via Wikepedia.org")
    my_embed.set_author(name="Wikipedia.org", url="https://www.wikipedia.org", icon_url="https://www.wikipedia.org/portal/wikipedia.org/assets/img/Wikipedia-logo-v2@1.5x.png")

    await interaction.response.send_message(embed=my_embed)

client.run(token=str(key))