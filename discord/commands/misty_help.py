import discord


def createEmbed():

    embed = discord.Embed(
        title="Misty's Command Guide",
        description="Thanks for inviting Misty! Here's a breakdown of her commands and functionality.",
        color=discord.Color.yellow()
    )

    # --- Information Note Section ---
    embed.add_field(
        name="ℹ️ A Quick Note on `/fx` Commands",
        value=(
            "All commands with the suffix `/fx` scrape **ForexFactory.com** for scheduled news and insights. "
            "These events help traders gauge market safety and potential volatility."
        ),
        inline=False
    )
    
    # --- Setup Commands Section ---
    setup_commands = (
        "**`/register`**\n"
        "Registers you with our database. This is **REQUIRED** for announcement channel persistence and future features.\n\n"
        "**`/set-announcement`**\n"
        "Dictates where Misty will send automated messages (online status, market open announcements, etc.). "
        "**PLEASE SET THIS** to avoid missing important status updates!"
    )
    embed.add_field(
        name="🛠️ Setup Commands (PLEASE DO THESE FIRST)",
        value=setup_commands,
        inline=False
    )

    # --- ForexFactory Commands Section ---
    fx_commands = (
        "**`/fx-all-news`**\n"
        "Returns all news events scheduled for today.\n\n"
        "**`/fx-high-impact`**\n"
        "Returns only **HIGH IMPACT** news scheduled today (usually defines market volatility).\n\n"
        "**`/fx-currency-lookup <currency>`**\n"
        "Filters to show news only pertaining to the chosen currency. Ex: `USD`.\n\n"
        "**`/fx-pair-lookup <pair>`**\n"
        "Filters to show news for a given currency pair. Ex: `EUR/USD`.\n\n"
        "**`/fx-last-update`**\n"
        "Check when Misty last scraped data from Forex Factory."
    )
    embed.add_field(
        name="📊 ForexFactory Commands",
        value=fx_commands,
        inline=False
    )

    # --- Other Commands Section ---
    embed.add_field(
        name="⏳ Other Commands",
        value="Still under construction. Stay tuned for new features!",
        inline=False
    )

    return embed