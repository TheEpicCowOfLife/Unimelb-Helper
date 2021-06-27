import discord
from discord.ext import commands
import json



# thanks to stackoverflow I learn that the command_prefix attribute accepts callables.
with open("data/prefixes.json") as f:
    # is it bad practice to have this global variable modified by other files? I feel
    # dirty even being able to do this. At least this can only be modified by admin.py
    prefixes = json.load(f)

default_prefix = "?"

def get_prefix(bot, message):
    if (message.guild == None):
        return default_prefix
    id = message.guild.id
    print(f"{id}, {prefixes.get(str(id))}")

    return prefixes.get(str(id), default_prefix)

description = '''A simple helper bot for unimelb students'''

intents = discord.Intents.default()
intents.members = False

bot = commands.Bot(command_prefix=get_prefix, description=description, intents=intents)    

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.event
async def on_message(message):

    # we do not want the bot to reply to itself
    if message.author == bot.user:
        return

    # add some bonus easter eggs
    content = message.content.strip().lower()
    channel = message.channel
    if content == "good bot":
        await channel.send("*purrs happily")
    elif content == "bad bot":
        if message.author.id == 276296473858277377:
            await channel.send("apologies master... did i do something wrong?")
        else:
            await channel.send("*hisses angrily")
    else:
        # and then actually process the commands otherwise
        await bot.process_commands(message)

