import discord
from discord.ext import commands
from bot import bot,prefixes
from error import on_error,ValidationError

import json

# Module handles all server-specific settings. More to come?

# command looks like !prefix text

@bot.command()
@commands.has_guild_permissions(administrator = True)
@commands.guild_only()
async def prefix(ctx,*args):
    if (len(args) != 1):
        raise ValidationError(f"Expecting exactly one argument.")
    
    server_id = ctx.guild.id
    prefix_string = args[0]

    prefixes[str(server_id)] = prefix_string
    with open("data/prefixes.json","w") as f:
        json.dump(prefixes,f)

    msg = f"{ctx.author.mention} Successfully set prefix to {prefix_string} for this server."
    await ctx.send(msg)

    # set_prefix(ctx.guild.id,args[0])