import requests
import re
import json
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import random
# This hot mess of a codebase is what happens when you get a guy who knows nothing about HTTP and asynchronous programming and just wants to
# do the bare minimum. Boy is the web a confusing pile of hot spaghetti

subject_code_regex = r"[a-zA-Z]{4}[0-9]{5}"

subject_code_regex_exact = r"^[a-zA-Z]{4}[0-9]{5}$"
# Scrapes a specific part of https://sws.unimelb.edu.au/2021/ for a list of all subject codes
# and writes it to codes.json
def scrape_code_list(path):
    with open(path,"r") as f:
        contents = f.read()
        unique = {}
        for match in re.findall(subject_code_regex,contents):
            unique[str(match)] = ""
        for i in unique:
            print(i)
        
    with open("data/codes.json","w") as f:
        f.write(json.dumps({"codes" : [i for i in unique]}))

# scrape_code_list("data/raw/subject_codes_2021.txt")


"""
List of entries planned


Scraped information from handbook

code: String for the subject code
has_handbook_page: Boolean for whether or not the handbook page exists
title: String for the title of the subject
prereq_for: list of subject codes that mention this subject in their prereqs.
availability: when the subject is available, list of strings
points: 

Scraped information from studentvip
has_student_vip_page:
rating:
review_count:


Derived information
level: subject level? inferred from subject code, may not be useful
"""


subjects = {}

def load_subjects():
    global subjects
    with open("data/subjects.json") as f:
        subjects = json.load(f)

def dump_subjects():
    with open("data/subjects.json","w") as f:
        f.write(json.dumps(subjects, indent = 4))

def write_to_test(thing):
    with open("test.txt","w") as f:
        f.write(thing)


unique_terms = {}
unique_study_modes = {}
unique_delivery = {}
unique_level = {}
parsed_count = 0
async def scrape_handbook_main(session, subject_code):
    global parsed_count
    handbook_url = f"https://handbook.unimelb.edu.au/2021/subjects/{subject_code.lower()}"
    subject = subjects[subject_code]
    try:
        async with session.get(handbook_url) as req:
            if (req.status == 200):
                subject["has_handbook_page"] = True

                soup = BeautifulSoup(await req.text(), 'html.parser')                
                title_result = soup.find(class_ = "header--course-and-subject__main")
                title = title_result.text.strip()

                if re.search(subject_code_regex,title):
                    title = title[:-12]
                else:
                    print(f"weirrrd, {subject_code} does not follow title convention")
                subject["title"] = title
                
                # Scraping level, points, and delivery method/campus. May or may not be useful?
                details_header = soup.find(class_ = "header--course-and-subject__details")
                if (details_header == None or len(details_header.contents) != 3):
                    print(f"Details header of {subject_code} is weird")
                else:
                    subject["level"] = details_header.contents[0].text
                    subject["points"] = float(details_header.contents[1].text[8:])
                    subject["delivery"] = details_header.contents[2].text

                    unique_level[subject["level"]] = subject_code
                    unique_delivery[subject["delivery"]] = subject_code


                # Scraping availability data
                matches = soup.find_all(string = "Availability")
                if (len(matches) == 0):
                    # This subject is not available in 2021
                    print(f"{subject_code} appears to not be available in 2021")
                else:
                    if (len(matches) != 1):
                        print(f"Weird, {subject_code} matches availability more than once")
                    count = 0
                    for match in matches:
                        # I hope this heuristic works for filtering out any spurious matches for "Availability".
                        if (match.parent.name != "th"):
                            continue
                        count += 1
                        
                        # this fires if my heuristic fails
                        if (count == 2):
                            print(f"damnit {subject_code} broke my availability heuristic")

                        # Entries is a tag that looks like this:
                        # <td><div>Summer Term - Dual-Delivery</div><div>Semester 1 - Dual-Delivery</div><div>Semester 2 - Dual-Delivery</div></td>
                        entries = match.parent.parent.contents[1]
                        subject["availability"] = []
                        for entry in entries.contents:
                            s = entry.text
                            # s is dumb. It's a string that looks like this: Summer Term - Dual-Delivery
                            # And I have to parse it.
                            # And there is no good separation between what is the term, or the study-mode
                            # But I'm going to try anyways
                            # Oh look I actually got it reasonable
                            contains_dumb_string = "Early-Start" in s

                            s = [i.strip() for i in s.split('-')]
                            if (contains_dumb_string):
                                term = "-".join(s[0:2])
                                study_mode = "-".join(s[2:])
                            else:
                                term = s[0]
                                study_mode = "-".join(s[1:])
                            
                            unique_terms[term] = subject_code
                            unique_study_modes[study_mode] = subject_code
                            subject["availability"].append({"term" : term, "mode" : study_mode})

            else:
                subject["has_handbook_page"] = False

    except Exception as e:
        print(f"{subject_code}, {e}")
    parsed_count += 1
    if (parsed_count % 50 == 0):
        print(parsed_count)

async def scrape_studentVIP_main(subject_code):
    pass

def print_dict(d, dict_name):
    print(dict_name)
    for key,val in d.items():
        print(f"{key,val}")
    print()

async def scrape_everything(num_subjects = 99999):
    with open("data/codes.json") as f:
        codes = json.loads(f.read())["codes"]
    # codes = ["MAST10006", "COMP20003", "NURS90118"]
    # codes = ["MAST10006"]

    
    # Ensuring entries exist for each entry in the dictionary
    for i,code in enumerate(codes):
        if (i == num_subjects):
            break
        # if (i % 100 != 0):
        #     continue
        subjects[code] = {"code" : code}

    tasks = []

    async with aiohttp.ClientSession() as session:
        for i,code in enumerate(codes):
            if (i == num_subjects):
                break
            # if (i % 100 != 0):
            #     continue

            tasks.append(scrape_handbook_main(session, code))
        await asyncio.gather(*tasks)
    

    print_dict(unique_terms, "Terms:")
    print_dict(unique_study_modes, "Study modes:")
    print_dict(unique_delivery, "Delivery:")
    print_dict(unique_level, "Levels:")

    dump_subjects()

    # print("No handbook entries:")
    # for i in noHandBookEntry:
    #     print(i)

    # print("No studentvip entries:")
    # for i in noHandBookEntry:
    #     print(i)
# loop = asyncio.get_event_loop()
# future = asyncio.ensure_future(scrape_everything(4))
# loop.run_until_complete(future)
asyncio.run(scrape_everything())
aiohttp.ClientResponse 
