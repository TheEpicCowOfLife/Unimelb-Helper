import discord
from discord.ext import commands
from bot import bot,prefixes
from error import on_error,ValidationError

import json

# Module handles all server-specific settings. More to come?

# command looks like !prefix text

@bot.command(brief = "Sets the command prefix for the current server. Administrator only.")
@commands.has_guild_permissions(administrator = True)
@commands.guild_only()
async def prefix(ctx, *, prefix):
    
    server_id = ctx.guild.id
    prefix_string = prefix

    prefixes[str(server_id)] = prefix_string
    with open("data/prefixes.json","w") as f:
        json.dump(prefixes,f)

    msg = f"{ctx.author.mention} Successfully set prefix to '{prefix_string}' for this server."
    await ctx.send(msg)