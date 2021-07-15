import discord
from discord.ext import commands

from typing import OrderedDict
from collections import OrderedDict
from functools import cmp_to_key

from bot import bot
from error import on_error,ValidationError
from paginator import *
from data import subjects,UoM_blue,YEAR

# This module implements the search engine

def compare(match1, match2):
    key0 = int(match2["has_handbook_page"])-int(match1["has_handbook_page"])
    key1 = match2["review_count"]-match1["review_count"]
    if (key0 == 0):
        return key1
    return key0

def sort_by_importance(subject_list):
    return sorted(subject_list,key = cmp_to_key(compare))

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

# The search algorithm ranks results first by the type of match they are, 
# and among those of the same kind of match uses a heuristic sort_by_importance.
# Sorting by "type of match" is a heuristic for search relevance. An exact code match is more relevant
# than the query being a substring of the title. See the funcs[] list for the exact ordering I have devised.
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
        for match in sort_by_importance(f(query)):
            ret[match["code"]] = match

    return [match for code,match in ret.items()]
