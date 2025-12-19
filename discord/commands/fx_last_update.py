import discord

def createEmbed(mongoHelpers, fx_collection, interaction):
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

    return update_embed