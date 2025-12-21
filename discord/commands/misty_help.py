import discord
import os
import json


def createEmbed(page_number):

    embed = discord.Embed(
        title="Misty's Command Guide",
        description="Thanks for inviting Misty! Here's a breakdown of her commands and functionality.",
        color=discord.Color.darker_grey()
    )

    mycwd = os.getcwd()
     # Open the file in read mode ('r')
    with open(f'{mycwd}/commands/misty_help.json', 'r', encoding='utf-8') as file:
        # Load the JSON data from the file into a Python object (usually a dictionary)
        data = json.load(file)

    # for page in misty_data
    target_page = data[page_number]
    # navigate to curr_page
    curr_page = target_page['Page']

    for field in curr_page:
        curr_field = curr_page[field]

        embed.add_field(
            name=f'{curr_field['name']}',
            value=f'{curr_field['value']}',
            inline=False
        )

        embed.set_footer(
            text=f"Page {page_number+1} of {len(data)}"
        )

    return embed