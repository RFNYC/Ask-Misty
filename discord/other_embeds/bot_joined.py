import discord


def createEmbed():

    embed = discord.Embed(
        title="🎉 Misty has joined the server! 🎉",
        color=0x9b59b6 
    )

    embed.add_field(
        name="⚠️ IMPORTANT DISCLAIMER",
        value=(
            "This project is intended for **educational use only**. It is **NOT** designed "
            "for real-world financial trading. Do not rely on this data for real-money decisions."
        ),
        inline=False
    )

    embed.add_field(
        name="✅ Post-Launch To-Do Checklist",
        value=(
            "**1. Setup:** Run `/register` and `/set-announcement` to receive status updates.\n"
            "**2. Help Menu:** Run `/misty-help` to see what I can do.\n"
            "**3. Try it out:** Test any of the `/fx` commands for on-the-fly data!"
        ),
        inline=False
    )

    embed.set_footer(text="Note: All timestamps are in Eastern Standard Time (EST).")
    
    return embed