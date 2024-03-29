import discord
from discord.ext import commands

import re
import traceback

from bot import bot
from data import UoM_blue, subjects, YEAR
from error import ValidationError
from paginator import Field, add_paginator,EmbedPaginator
from search import do_search, sort_by_importance

# This module handles everything related to displaying subjects and accessing its information.

subject_code_regex = r"^[a-zA-Z]{4}[0-9]{5}$"

def get_studentVIP_URL(code):
    return f"https://studentvip.com.au/unimelb/subjects/{code.lower()}"


def get_handbook_URL(code, year = YEAR):
    return f"https://handbook.unimelb.edu.au/{year}/subjects/{code.lower()}"

# Adds a overview field.
OVERVIEW_LENGTH = 300
def add_overview_field(embed, subject, inline = False):
    overview = subject['overview']
    if len(overview) < OVERVIEW_LENGTH:
        cropped_overview = overview
    else:
        # find the first space after cropping
        cutoff = overview[OVERVIEW_LENGTH:].find(' ')
        if (cutoff == -1):
            cutoff = OVERVIEW_LENGTH
        else:
            cutoff += OVERVIEW_LENGTH
        cutoff = min(cutoff,len(overview))
        # Cutoff is now set to the location of the first space, or the end of the overview.        
        # Non exhaustive list lol, tell me if there are bugs.
        punctuation = ['"',"'",".",",","!",'?', " "]    
        # Remove any trailing punctuation so we can add the elipsis
        while (overview[cutoff-1] in punctuation):
            cutoff -= 1
        cropped_overview = overview[:cutoff] + "..."
    embed.add_field(name = "Overview", value = cropped_overview, inline = inline)

    # # This code displays the whole thing. It is long. TODO: Possibly paginate it.
    # overview_pars = subject['overview'].split("\n")
    # embed.add_field(name = "Overview", value = overview_pars[0], inline = False)
    # for par in overview_pars[1:]:
    #     if (len(par) > 1021):
    #         print(f"{subject['code']} has a stupid monolithic handbook overview")
    #     embed.add_field(name = "​", value = par, inline = False)

# Add the availability field to a given embed
def add_availability_field(embed,subject, inline = False):
    availability = subject['availability']
    avail_desc = []
    if len(availability) == 0:
        avail_desc = [f"Not available in {YEAR}"]
    else:
        for thing in availability:
            if (thing['mode'] == ""):
                # separate case so we don't have a weird trailing dash.
                avail_desc.append(f"{thing['term']}")
            else:
                avail_desc.append(f"{thing['term']} - {thing['mode']}")
    avail_desc = "\n".join(avail_desc)
    embed.add_field(name = "Availability", value = avail_desc, inline = inline)

# Add the review field to a given embed
def add_review_field(embed,subject, inline = False):
    if (subject['rating'] == -1):
        subject_desc = "No ratings."
    else:
        subject_desc = f"Rated {subject['rating']} star(s) in {subject['review_count']} review(s)"
    embed.add_field(name = "StudentVIP rating:", value = subject_desc, inline = inline)

# Add the links field to a given embed
def add_links_field(embed,subject, inline = False):
    links = []
    if (subject['has_handbook_page']):
        links.append(f"[Handbook]({get_handbook_URL(subject['code'])})")
    if (subject['has_studentVIP_page']):
        links.append(f"[StudentVIP]({get_studentVIP_URL(subject['code'])})")
    links_desc = ""
    if (len(links) == 0):
        links_desc = "No links exist for this subject"
    else:
        links_desc = "\n".join(links)
    embed.add_field(name = "Links:", value = links_desc, inline = inline)

# Precondition: subject is a dictionary entry from subjects.json
def get_subject_embed_detailed(subject):
    embed = discord.Embed(title=f"__{subject['title']} ({subject['code']})__", color=UoM_blue)
    if (not subject['has_handbook_page']):
        embed.description = f"Unfortunately {subject['code']} does not appear to have a handbook page," \
        " which means that little is known about the subject and it likely won't be offered to uni students in the future"
        return embed
    else:
        embed.description = f"{subject['level']} / Points: {subject['points']} / {subject['delivery']}"
        add_overview_field(embed,subject)
        add_links_field(embed,subject, inline = True)   
        add_availability_field(embed,subject,inline = True)
        if (subject['has_studentVIP_page']):
            add_review_field(embed,subject)
    return embed

# Converts a list of subjects to fields to be displayed in a paginator
def subject_list_to_fields(subject_list):
    ret = []
    for subject in subject_list:
        title = f"{subject['code']}: {subject['title']}"
        desc = []
        if (subject["has_handbook_page"]):
            desc.append(f"[Handbook]({get_handbook_URL(subject['code'])})")
        if (subject['has_studentVIP_page']):
            desc.append(f"[StudentVIP]({get_studentVIP_URL(subject['code'])})")
        if (subject['points'] != 0):
            desc.append(f"Points: {subject['points']}")
        if (subject['delivery'] != ""):
            desc.append(f"{subject['delivery']}")
        if (len(desc) == 0):
            desc = "No known information"
        else:
            desc = " / ".join(desc)
        ret.append(Field(title,desc))
    return ret

def validate_subject_code(ctx, subject_code):
    if not re.match(subject_code_regex,subject_code):
        raise ValidationError(f"{subject_code} is an invalid subject code. Subject codes are of the form 'ABCD12345'. Case insensitive.")

    if subject_code.upper() not in subjects:
        raise ValidationError(f"Subject {subject_code} does not exist.")

def validate_args_is_subject_code(ctx,args):
    if (len(args) != 1):
        raise ValidationError(f"Expecting exactly one argument. Usage is '{ctx.prefix}subject ABCD12345'. Case insensitive")
    subject_code = args[0].upper()
    validate_subject_code(ctx,subject_code)
    

@bot.command(aliases = ['search'], brief = "Searchs for subjects and displays information about them.")
async def subject(ctx, *, query):
    query = query.strip()
    if (len(query) > 50):
        raise ValidationError(f"Argument too long, exceeds 50 character limit")
    subject_list = do_search(query)
    title = f"Displaying search result(s) for '{query}'"
    if (len(subject_list) == 0):
        desc = "No results found"
        await ctx.send(embed = discord.Embed(title = title, description = desc, color = UoM_blue))
    elif len(subject_list) == 1:
        await ctx.send(embed = get_subject_embed_detailed(subject=subject_list[0]))        
    else:
        desc = f"{len(subject_list)} result(s) found"
        fields = subject_list_to_fields(subject_list)
        paginator = EmbedPaginator(title = title, description = desc, fields = fields)
        add_paginator(ctx.author, paginator)
        await ctx.send(embed = paginator.make_embed(ctx,page = 1))        


@bot.command(brief = "Displays subjects that use 'subject_code' as a prerequisite. Good for looking at where a certain subject leads to.")
async def reqfor(ctx, *, subject_code):
    subject_code = subject_code.upper()
    validate_subject_code(ctx, subject_code)
    subject_title = subjects[subject_code]["title"]
    title = f"Displaying subjects that use '{subject_title}' as a prerequisite"    
    subject_list = sort_by_importance([subjects[code] for code in subjects[subject_code]['prereq_for']])

    # Send a special embed for no results
    if (len(subject_list) == 0):
        desc = f"No subjects use '{subject_code}' as a prerequisite"
        await ctx.send(embed = discord.Embed(title = title, description = desc, color = UoM_blue))
    else:
        desc = f"{len(subject_list)} result(s) found. Note that {subject_code} is one possible requirement for the following subjects"\
            " or it may even be simply listed as recommended subject. Always check the handbook for more details."
        fields = subject_list_to_fields(subject_list)
        paginator = EmbedPaginator(title = title, description = desc, fields = fields)
        add_paginator(ctx.author, paginator)
        await ctx.send(embed = paginator.make_embed(ctx,page = 1))    

