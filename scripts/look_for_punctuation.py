import json
import re
import pprint
from common import *
subjects = load_subjects()
unique_dict = {}
for code in subjects:
    # for letter in subjects[code]["overview"]:
    #     if not re.match("[a-zA-Z0-9]",letter):
    #         unique_dict[letter] = code
    for letter in subjects[code]["title"]:
        if not re.match("[a-zA-Z0-9]",letter):
            unique_dict[letter] = code
print(sorted([letter for letter in unique_dict]))
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(unique_dict)

