"""

Creating an __init__.py file like this and then importing all your helper files within the folder will allow you to use this folder
like a package. Meaning you can import the entire folder like a library and use it elsewhere. Some example usage:

import misty_commands

async def sendEmbedButton(interaction: discord.Interaction):
    embed, View = misty_commands.buttontest.testCreateButtonEmbed()
    await interaction.response.send_message(embed=embed, view=View) # type: ignore

In this example you see we call the package, navigate to a specific helper file, and have access to all its functions.
This lets us keep things more organized and easy to work on.

"""

from . import buttontest
from . import fx_high_impact
from . import fx_pair_lookup
from . import fx_currency_lookup
from . import fx_all_news
from . import fx_last_update
from . import misty_help
from . import risk_calculation
