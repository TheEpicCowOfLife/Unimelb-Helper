import discord
from discord.ext import commands

from typing import OrderedDict
from collections import OrderedDict
from functools import cmp_to_key

from bot import bot
from error import on_error,ValidationError
from paginator import *
from subject import subject_list_to_fields
from data import subjects,UoM_blue,YEAR


# Within each categories the subjects are sorted by this function
def compare(match1, match2):
    key0 = int(match2["has_handbook_page"])-int(match1["has_handbook_page"])
    key1 = match2["review_count"]-match1["review_count"]
    if (key0 == 0):
        return key1
    return key0

# Different functions that return a list of subjects depending on the kind of match they are
def match_code_exact(code):
    # code = code.upper()
    if (code in subjects):
        return [subjects[code]]
    return []


def match_code_prefix(code_prefix):
    # code_prefix = code_prefix.upper()
    ret = []
    for code in subjects:
        if code.startswith(code_prefix):
            ret.append(subjects[code])
    return ret 

def match_title_exact(title):
    title = title.lower()
    ret = []
    for code in subjects:
        if subjects[code]["title"].lower().strip() == title:
            ret.append(subjects[code])
    return ret

def match_title_prefix(prefix):
    ret = []
    prefix = prefix.lower()
    for code in subjects:
        if subjects[code]["title"].lower().startswith(prefix):
            ret.append(subjects[code])
    return ret 

def match_title_contains(substring):
    ret = []
    substring = substring.lower()
    for code in subjects:
        if substring in subjects[code]["title"].lower():
            ret.append(subjects[code])
    return ret 


def do_search(query):
    # Ordered dict has the nice property of maintaining insertion order and removing duplicates.
    ret = OrderedDict()

    # NOTE must be in order of decreasing priority of matches.
    funcs = [match_code_exact, 
        match_title_exact,
        match_code_prefix,
        match_title_prefix,
        match_title_contains]
    
    for f in funcs:
        for match in sorted(f(query), key = cmp_to_key(compare)):
            ret[match["code"]] = match
    return [match for code,match in ret.items()]


@bot.command()
async def search(ctx, *, arg):
    arg = arg.strip()
    subject_list = do_search(arg)
    author_id = ctx.author.id

    title = f"Displaying result(s) for search '{arg}'"

    # Send a special embed for no results
    if (len(subject_list) == 0):
        desc = "No results found"
        await ctx.send(embed = discord.Embed(title = title, description = desc, color = UoM_blue))
    else:
        desc = f"{len(subject_list)} result(s) found"
        fields = subject_list_to_fields(subject_list)
        paginators[author_id] = EmbedPaginator(title = title, description = desc, fields = fields)
        await ctx.send(embed = paginators[author_id].make_embed(ctx,page = 1))    


@search.error
async def subject_error(ctx, error):
    await on_error(ctx,error)





@bot.command()
async def test(ctx,*args):

    markdown_test = f"""
    - unordered list? kek
    - test2
    - breh
    ---
    1. what about this
    2. heh?
    3. kekw
    """
    embed = discord.Embed(title="Title", description="Desc", color=UoM_blue)
    embed.add_field(name="Field1", value="# hi **markdown** test", inline=True)
    embed.add_field(name="Field2", value=markdown_test, inline=True)
    await ctx.send(embed=embed)