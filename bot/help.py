import discord
from discord.ext import commands

from bot import bot
from data import UoM_blue, subjects, YEAR
from error import on_error,ValidationError
from paginator import Field, add_paginator,paginators,EmbedPaginator

github_link =  'https://github.com/TheEpicCowOfLife/Unimelb-Helper'
@bot.command(brief = "Sends the github repo link for this bot.")
async def github(ctx, *args):
    await ctx.send(f"{ctx.author.mention} Contribute to this discord bot, and scream at TheEpicCowOfLife if this bot does not know about a certain subject here! {github_link}")


# Code lovingly stolen from https://gist.github.com/InterStella0/b78488fb28cadf279dfd3164b9f0cf96
# and modified a bit, of course.
class MyHelp(commands.HelpCommand):
    def get_command_signature(self, command):
        return '%s%s %s' % (self.clean_prefix, command.qualified_name, command.signature)

    async def send_bot_help(self, mapping):
        title = "UnimelbHelper commands"
        desc = f"A way to quickly search for subjects and view subject information faster than the handbook. Github link here: {github_link}"
        embed = discord.Embed(title="Help for discord")
        all_commands = []
        for cog, cog_commands in mapping.items():
            [all_commands.append(c) for c in cog_commands]

        fields = []
        for c in all_commands:
            fields.append(Field(title = self.get_command_signature(c), desc = c.brief))
        
        paginator = EmbedPaginator(title = title, description=desc, fields = fields)
        add_paginator(self.context.author,paginator)
        channel = self.get_destination()
        await channel.send(embed=paginator.make_embed(self.context,page=1))
bot.help_command = MyHelp()
bot.help_command.help = "Displays information about the bot's commands"

@bot.command(brief = "If you see this, scream at the TheEpicCowOfLife to remove this")
async def test(ctx, *args):
    for command in bot.commands:
        print(command.name)
        print(command.help)    
    await ctx.send(f"{ctx.author.mention} test")

def check_for_missing_help():
    for command in bot.commands:
        if command.help == None:
            
            pass