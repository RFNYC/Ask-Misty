import discord


def createEmbed(timestamp):
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

    return embed