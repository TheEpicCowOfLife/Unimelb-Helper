import discord
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError, MissingPermissions

# Describes a kind of error that's totally fine bc of bad user input that was checked for.
class ValidationError(Exception):
    pass

async def on_error(ctx, error):
    msg = ""
    
    if (isinstance(error,CommandInvokeError)):
        if (isinstance(error.original,ValidationError)):
            msg = f"{ctx.author.mention} Error! {error.original}"
        else:
            print(f"oh no, {error}")
            msg = f"{ctx.author.mention} Critical error! Contact the dev(s). {error}"        
    else:
        msg = f"{ctx.author.mention} Error! {error}"
    await ctx.send(msg)