from functools import cmp_to_key
import json
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


def compare(match1, match2):
    key0 = int(match2["has_handbook_page"])-int(match1["has_handbook_page"])
    key1 = match2["review_count"]-match1["review_count"]
    if (key0 == 0):
        return key1
    return key0

def sort_by_importance(subject_list):
    return sorted(subject_list,key = cmp_to_key(compare))