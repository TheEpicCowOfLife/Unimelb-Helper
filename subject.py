
from bot import bot
from error import on_error,ValidationError
import requests
import discord
import re
from discord.ext import commands


subject_code_regex = r"^[a-zA-Z]{4}[0-9]{5}$"

@bot.command()
async def hello(ctx):
    msg = f'Hello {ctx.author.mention}!'
    await ctx.send(msg)

@bot.command()
async def subject(ctx, *args):
    if (len(args) != 1):
        raise ValidationError(f"Expecting exactly one argument. Usage is '{ctx.prefix}subject ABCD12345'. Case insensitive")

    subject_code = args[0]
    if not re.match(subject_code_regex,subject_code):
        raise ValidationError(f"{subject_code} is an invalid subject code. Subject codes are of the form 'ABCD12345'. Case insensitive.")
    else:
        urls = []
        
        handbook_url = f"https://handbook.unimelb.edu.au/2021/subjects/{subject_code.lower()}"
        r = requests.get(handbook_url)
        if (r.status_code == 200):
            urls.append(handbook_url)
        
        studentvip_url = f"https://studentvip.com.au/unimelb/subjects/{subject_code.lower()}"
        r = requests.get(studentvip_url)
        if (r.status_code == 200):
            urls.append(studentvip_url)

        if len(urls) == 0:
            raise ValidationError(f"Subject code {subject_code} doesn't exist")
        else:
            msg = "\n".join(urls)
    await ctx.send(msg)

@subject.error
async def subject_error(ctx, error):
    await on_error(ctx,error)
