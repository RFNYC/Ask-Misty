import discord

def createEmbed(query, response, interaction):

    response_embed = discord.Embed(
        title="💭Your Question:",
        description=f"**{query}**",
        color=discord.Color.dark_grey() # A calming blue color
    )
    
    response_embed.add_field(
        name="Misty's Response:",
        value=f"{response}",
        inline=False
    )
    
    response_embed.set_footer(
        text=f"Requested by {interaction.user.display_name}", 
        icon_url=interaction.user.display_avatar.url
    )

    return response_embed