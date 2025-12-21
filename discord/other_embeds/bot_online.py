import discord


def createEmbed():
    embed = discord.Embed(
        title="✨ Misty Online! 🚀",
        description="I'm officially connected and ready to assist your server!",
        color=0x7289DA
    )
    
    embed.add_field(
        name="Need help?",
        value="Try running `/misty-help` to see what I can do!",
        inline=False
    )

    return embed