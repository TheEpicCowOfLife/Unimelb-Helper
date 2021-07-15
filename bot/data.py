from functools import cmp_to_key
import json

# Contains constants loads data, and other things to be accessed globally

with open("data/subjects.json") as f:
    subjects = json.loads(f.read())

# Create acronyms for subjects 
def create_acronyms():
    # There's a bunch of ways acronyms are created
    # There's case sensitive letters 
    # There's case sensitive minus numbers
    # Capital letters only
    # Case insensitive (probably not)

    # Do i want to do this? nah
    # but it'd be a pretty cool feature for future me
    # this is a huge TODO
    # and it may not even be a desired feature.
    acronyms = []
    pass
create_acronyms()



UoM_blue = 0x094183

YEAR = 2021