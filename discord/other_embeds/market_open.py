import discord


def createEmbed(timestamp):
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

    return embed