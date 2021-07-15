from bot import bot
from subject import *
from search import *
from paginator import *
from admin import *

import os

# Main file. Run this to import all the components of the bot, and then run the bot.
# The secret authentication token is an environment variable that is read in. There will be no accidental leakage tonight!

TOKEN = os.environ.get('UNIMELB_HELPER_TOKEN')
bot.run(TOKEN)