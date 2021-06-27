from bot import bot
from subject import *
import os


TOKEN = os.environ.get('UNIMELB_HELPER_TOKEN')
bot.run(TOKEN)




