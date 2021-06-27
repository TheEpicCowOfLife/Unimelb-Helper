import discord
from discord.ext import commands

description = '''A simple helper bot for unimelb students'''

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='?', description=description, intents=intents)


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

