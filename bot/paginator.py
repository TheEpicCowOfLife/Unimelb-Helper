import discord

from typing import List, Dict
import math

from bot import bot
from error import on_error,ValidationError
from data import UoM_blue

# The EmbedPaginator is a custom paginator that displays an embed with a list of fields.
# where a user can decide which 'page' of fields to interact with

# Current interaction is typing the ?page command, react coming soon
class Field():
    def __init__(self, title: str, desc: str, inline: bool = False) -> None:
        self.title = title
        self.desc = desc
        self.inline = inline

    def add_to_embed(self, embed):
        embed.add_field(name = self.title, value = self.desc, inline = self.inline)

class EmbedPaginator():
    def __init__(self, title: str, description: str, fields: List[Field], results_per_page = 5, have_results_footer = True) -> None:
        self.title = title
        self.description = description
        self.fields = fields
        self.RESULTS_PER_PAGE = results_per_page
        self.max_pages = math.ceil(len(fields)/results_per_page)
        self.have_results_footer = have_results_footer
    # Raises a ValidationError error if page is not a valid integer.
    def validate_page(self, page):
        try:
            p = int(page)
            assert(p > 0)
        except:
            raise ValidationError(f"'{page}' is not an integer between 1 and {self.max_pages} inclusive.")
        if p > self.max_pages:
            raise ValidationError(f"Error, page number specified is too high! Page must be between 1 and {self.max_pages} inclusive.")

    def make_embed(self, ctx, page = 1) -> discord.Embed:
        self.validate_page(page)
        embed = discord.Embed(title = self.title, description = self.description, color = UoM_blue)
        
        start = (page-1) * self.RESULTS_PER_PAGE
        stop = min(len(self.fields), start + self.RESULTS_PER_PAGE)
        for i in range(start,stop):
            self.fields[i].add_to_embed(embed)

        footer_text = "\n"

        if (self.have_results_footer):        
            footer_text += f"Displaying results {start+1}-{stop} out of {len(self.fields)} results\n"

        if (self.max_pages > 1):
            footer_text += f"Use {ctx.prefix}page {page % self.max_pages + 1} to see other results."
        
        embed.set_footer(text = footer_text)
        return embed

# User_id : Paginator        
paginators: Dict[int, EmbedPaginator] = {}    

def add_paginator(user: discord.User, paginator: EmbedPaginator):
    paginators[user.id] = paginator

@bot.command()
async def page(ctx, *, page_number):
    author_id = ctx.author.id
    if author_id not in paginators:
        raise ValidationError(f"There is nothing to use {ctx.prefix}page on!")

    paginator = paginators[author_id]
    paginator.validate_page(page_number)
    await ctx.send(embed = paginator.make_embed(ctx, page = int(page_number)))
