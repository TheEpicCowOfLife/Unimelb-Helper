import asyncio
from asyncio.tasks import sleep
from enum import unique
import json
import random
import re
import os
import aiohttp
from bs4.element import NavigableString
import requests
import traceback
from bs4 import BeautifulSoup
from common import *
from post_processing import *
# At the bottom you can do one of two things.
# Run "do_everything()" which will scrape almost everything from scratch
# Run "update_studentVIP()" which will scrape studentVIP and update review counts and ratings.

# General pseudocode looks like this.

# Call scrape_code_list() to get a list of all the subject codes we care about, and initialise subjects{} dict with empty/default values for each code, 
# or simply add new entries that didn't previously exist.

# Call scrape_SOMEPAGE(code) which scrapes some page and populates corresponding entries in subjects[code] or other entries in subjects[code]
# Save scrape_SOMEPAGE

# You can also change this, and hope everything works the same way it did before.
# I almost guarantee it won't.
YEAR = "2021"

subject_code_regex = r"[a-zA-Z]{4}[0-9]{5}"

subject_code_regex_exact = r"^[a-zA-Z]{4}[0-9]{5}$"

"""
List of entries planned


Scraped information from handbook

Handbook main:
code: String for the subject code
has_handbook_page: Boolean for whether or not the handbook page exists
title: String for the title of the subject
level: Subject level. See unique_entries.txt for the possible strings that can appear.
availability: cbs explaining, just look in the data, and look at unique_entries.txt
points: Subject points
delivery: this has information on how and which campus the subject is held. See unique_entries.txt for the possible strings that can appear.
overview: the paragraph subsectioned 

Handbook requirements page:
prereq_for: List of subjects that use the current subject as a prereq. Note that this field can exist for subjects without a handbook entry.

Scraped information from studentvip
has_student_vip_page: 
rating: float, -1 if there is no rating
review_count: int NOTE there can be subjects with a rating and 0 reviews. As of today (july 4th 2021), one example is MCEN90008
"""

subjects = {}

def get_default_subject(code, title = "Unknown"):
    ret = {
        "code" : code,
        "has_handbook_page" : False,
        "title" : title,
        "level" : "",
        "points" : 0,
        "delivery" : "",
        "availability" : [],
        "overview" : "",
        "prereq_for" : [],

        "has_studentVIP_page" : False,
        "rating" : -1,
        "review_count" : 0
    }
    return ret
def get_default_subject_min(code, title = "Unknown"):
    ret = {
        "code" : code,
        "title" : title,
    }
    return ret




def write_to_test(thing):
    with open("test.txt","w") as f:
        f.write(thing)


class ProgressTracker():
    def __init__(self, period, message):
        self.val = 0
        self.period = period
        self.message = message
    
    def increment(self):
        self.val += 1
        if (self.val % self.period == 0):
            print(self.message % self.val)

cache_tracker = ProgressTracker(50,"Cached %s pages")

async def cache_page(session,url,path):
    global parsed_count
    try:
        async with session.get(url) as req:
            if req.status == 200:
                with open(path,"w") as f:
                    f.write(await req.text()) 
    except Exception as e:
        print(f"Error in caching {url}, {e}")
    cache_tracker.increment()


async def cache_handbook(session, subject_codes):
    tasks = []
    for subject_code in subject_codes:
        tasks.append(cache_page(session, 
            f"https://handbook.unimelb.edu.au/{YEAR}/subjects/{subject_code.lower()}", 
            f"data/site_cache/handbook_main/{subject_code}.html"
        ))
        tasks.append(cache_page(session, 
            f"https://handbook.unimelb.edu.au/{YEAR}/subjects/{subject_code}/eligibility-and-requirements",
            f"data/site_cache/handbook_requirements/{subject_code}.html"
        ))
    await asyncio.gather(*tasks)

# i should totally use enums, whatever.
# get_soup may return none if it fails. Assuming that is best practice.
async def get_soup(subject_code, url_type, session = None):
    try:
        if (url_type == "handbook_main"):
            with open(f"data/site_cache/handbook_main/{subject_code}.html") as f:
                return BeautifulSoup(f.read(), 'html.parser')

        elif (url_type == "handbook_requirements"):
            with open(f"data/site_cache/handbook_requirements/{subject_code}.html") as f:
                return BeautifulSoup(f.read(), 'html.parser')

        elif (url_type == "studentVIP"):
            # So uhhhh, I accidentally scraped studentVIP at the speed of light, and cached them on my end.
            # The folders will not exist on github, so studentVIP will be requested on demand
            if (False or os.path.exists(f"data/site_cache/studentVIP/{subject_code}.html")):
                with open(f"data/site_cache/studentVIP/{subject_code}.html") as f:
                    return BeautifulSoup(f.read(), 'html.parser')
            else:            
                url = f"https://studentvip.com.au/unimelb/subjects/{subject_code.lower()}"
                async with session.get(url) as req:
                    # print("making request why")
                    if req.status == 200:
                        return BeautifulSoup(await req.text(), 'html.parser')
        else:
            print(f"Passed in wrong url_type lol {subject_code},{url_type}")
    except Exception as e:
        print(f"Error in {subject_code} doing {url_type}, {e}")
handbook_results_tracker = ProgressTracker(20, "Retrieved %s pages of results")
async def get_handbook_results_soup(page, session):
    try:
        url = f"https://handbook.unimelb.edu.au/search?area_of_study%5B%5D=all&campus_and_attendance_mode%5B%5D=all&org_unit%5B%5D=all&page={page}&sort=external_code%7Casc&study_periods%5B%5D=all&subject_level_type%5B%5D=all&types%5B%5D=subject&year={YEAR}"
        async with session.get(url) as req:
            if (req.status == 200):
                handbook_results_tracker.increment()
                return BeautifulSoup(await req.text(), 'html.parser')
    except Exception as e:
        print(f"Error in page {page} of results page, {e}")
 
def process_results_page(soup: BeautifulSoup):
    results_list = soup.find(class_ = "search-results__list")
    ret = {}
    for result in results_list:
        thing = result.find(class_ = "search-result-item__name")
        title = thing.contents[0].text
        code = thing.contents[1].text
        ret[code] = title
    return ret

# Scrapes https://sws.unimelb.edu.au/2021/ for a list of all subject codes
# and writes it to codes.json. You need to actually click on the subjects button, and paste the HTML manually
# into input_path. Clicking a js button really is the bane of this scraper.

# Actually it turns out sws is useless and misses out on like 5 billion subjects. Now also scraping handbook results page for completeness.
async def scrape_code_list(session, input_paths,output_path):
    unique_dict = {}
    for path in input_paths:
        with open(path,"r") as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Apparently the only thing with id dlObject is what we're looking for,
            # which just seems like a coincidence that we shouldn't rely on.
            # But i see no better way.
            for option in soup.find(id = "dlObject").contents:
                # Apparently half of the contents are empty navigable strings. Yeah I have no idea what
                # this cooked HTML did to beautiful soup
                if (type(option) == NavigableString):
                    continue
                s = option.text
                code = s[:9]
                title = "-".join(s.split("-")[1:]).strip()
                unique_dict[code] = title
    
    temp = await get_handbook_results_soup(1,session)
    if (temp == None):
        print("WTFF????")
    else:
        initial_soup: BeautifulSoup = temp    
        # print(initial_soup)
        result = initial_soup.find(class_ = "search-results__paginate")
        number_of_pages = int(result.contents[2].text.split(" ")[1])
        # print(number_of_pages)        
        # number_of_pages = min(number_of_pages,10)
        tasks = []
        for i in range(2,number_of_pages+1):
            tasks.append(get_handbook_results_soup(i,session))
        soups = [initial_soup] + await asyncio.gather(*tasks)
        for soup in soups:
            if (soup == None): 
                continue
            return_dict = process_results_page(soup)
            for code,title in return_dict.items():
                unique_dict[code] = title
    with open(output_path,"w") as f:
        f.write(json.dumps({"codes" : sorted([(code,title) for code,title in unique_dict.items()], key = lambda k: k[0])},indent = 4))


unique_terms = {}
unique_study_modes = {}
unique_delivery = {}
unique_level = {}

handbook_main_tracker = ProgressTracker(50, "Scraped %s handbook main pages")
# Scrapes handbook main page for stuff. Also maintains the unique dicts that you may like to print
async def scrape_handbook_main(session, subject_code):
    subject = subjects[subject_code]
    try:
        soup = await get_soup(subject_code,"handbook_main",session)
        if (soup != None):
            # So. Stuff did not return a 404. Therefore... the page should be found right?
            # NOPE
            # https://handbook.unimelb.edu.au/2021/subjects/list-available/agri20030
            for match in soup.find_all(string = "Page not found"):
                # just another double check in case SOMEHOW page not found is a false positive
                if match.parent.name == "span" and "itemprop" in match.parent.attrs:
                    raise Exception(f"Has no handbook page but not 404")

            subject["has_handbook_page"] = True         
            
            # Scraping level, points, and delivery method/campus. May or may not be useful?
            details_header = soup.find(class_ = "header--course-and-subject__details")
            if (details_header == None or len(details_header.contents) not in [2,3]):
                print(f"Details header of {subject_code} is weird")
            else:
                if (len(details_header.contents) == 2):
                    subject["level"] = details_header.contents[0].text
                    subject["delivery"] = details_header.contents[1].text
                else:
                    subject["level"] = details_header.contents[0].text
                    subject["points"] = float(details_header.contents[1].text[8:])
                    subject["delivery"] = details_header.contents[2].text

                unique_level[subject["level"]] = subject_code
                unique_delivery[subject["delivery"]] = subject_code


            # Scraping availability data
            matches = soup.find_all(string = "Availability")
            if (len(matches) == 0):
                pass
                # This subject is not available in 2021
                # print(f"{subject_code} appears to not be available in {YEAR}")
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
                        # Oh look I actually got it reasonably

                        if (s.strip() == "Time-based Research"):
                            term = "Time-based Research"
                            study_mode = ""
                        else:
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
            
            # Scraping overview text

            # course__overview-wrapper actually encapsulates Overview, ILO and Generic skills
            ov_wrapper = soup.find(class_ = "course__overview-wrapper")

            # ILO and Generic skills are further wrapped in child divs
            for child in ov_wrapper.find_all("div"):
                child.decompose()

            # functional!
            subject["overview"] = '\n'.join(
                map(lambda x: re.sub(r'\n+', '\n', x.text.strip()), # multiple newlines -> only one
                    ov_wrapper.find_all('p'))
            ).strip()
    except Exception as e:
        print(f"Error in {subject_code}, {e}")
    handbook_main_tracker.increment()

studentVIP_main_tracker = ProgressTracker(10, "Scraped %s studentVIP main pages")
async def scrape_studentVIP_main(session, subject_code):
    subject = subjects[subject_code]
    try:
        soup = await get_soup(subject_code,"studentVIP",session)
        if (soup != None):
            subject["has_studentVIP_page"] = True

            # Find the overall rating
            missing_rating_result = soup.find(class_ = "subject-rating no-rating")
            if (missing_rating_result != None):
                # There is no rating for this subject
                subject["rating"] = -1
            else:
                rating_result = soup.find(class_ = "rating")
                if (rating_result == None):
                    # WTF HAPPENED?
                    print(f"{subject_code} has no rating and no no rating????")
                else:
                    # heh i wrote the line of code and it worked first try nice job me
                    subject["rating"] = len(rating_result.find_all(class_ = "fas fa-star")) + 0.5 * len(rating_result.find_all(class_ = "fas fa-star-half"))
            # and apparently studentVIP uses this specific class for all written reviews, and doesn't use it anywhere else.
            # So I'm going to piggyback off this. It appears to be correct. 
            subject["review_count"] = len(soup.find_all(class_ = 'panel panel-default'))
        else:
            # We may run this again and find a page has deleted
            subject["has_studentVIP_page"] = False
    except Exception as e:
        print(f"Error in {subject_code}, {e}")
    studentVIP_main_tracker.increment()

handbook_req_tracker = ProgressTracker(50, "Scraped %s handbook req pages")
# Subject_code has requirements. Updates each code in requirements
def process_requirements(subject_code, requirements):
    unique_dict = {}
    for requirement in requirements:
        unique_dict[requirement] = 0
    for requirement in unique_dict:
        if requirement not in subjects:
            subjects[requirement] = get_default_subject(requirement)
        subjects[requirement]["prereq_for"].append(subject_code)

# PRECONDITION: Handbook main has been scraped, and the has_handbook_page attribute is set correctly
async def scrape_handbook_req(session,subject_code):
    if (subjects[subject_code]["has_handbook_page"]):
        try:
            soup = await get_soup(subject_code,"handbook_requirements",session)
            if soup != None:
                for result in soup.find_all(string = "Recommended background knowledge"):
                    if (result.parent.name == "h3"):
                        process_requirements(subject_code,[str(match).upper() for match in re.findall(subject_code_regex, str(result.parent.next_sibling))])

                prereq_result = soup.find(id = "prerequisites")
                if (prereq_result != None):
                    process_requirements(subject_code,[str(match).upper() for match in re.findall(subject_code_regex, str(prereq_result))])
            
        except Exception as e:
            print(f"Error in {subject_code},",e)
            traceback.print_exc()
    handbook_req_tracker.increment()

def print_dict(d, dict_name):
    print(dict_name)
    for key,val in d.items():
        print(f"{key,val}")
    print()

def dict_to_string(d,dict_name):
    a = [dict_name] + [f"{key} : {val}" for key,val in d.items()]
    return "\n".join(a)

def save_unique_dicts():
    with open("data/unique_entries.txt","w") as f:
        f.write("""Here is a list of all the possible values certain things can take.\n
Should probably sort them so they appear in a sane order\n
Each entry is of the form (thing, subject_code) where subject_code is an example where thing appears\n\n""")
        f.write(dict_to_string(unique_terms, "Terms:") + "\n\n")
        f.write(dict_to_string(unique_study_modes, "Study modes:") + "\n\n")
        f.write(dict_to_string(unique_delivery, "Delivery:") + "\n\n")
        f.write(dict_to_string(unique_level, "Levels:"))





# asyncio.run(test())
# Runs all the code, start to finish. Input data/raw/sws{YEAR}.txt, outputs codes.json, subjects.json, and unique_entries.txt
# Don't forget to set the YEAR constant
# replace_subjects is a boolean describing whether or not the existing information in subjects.json will be replaced.
async def do_everything(replace_subjects = True):
    global subjects
    async with aiohttp.ClientSession() as session:
        if (not replace_subjects):
            subjects = load_subjects()
        # I have stored codes in a very lazy and haphazard manner. I apologise
        input_files = [f"data/raw/sws2021.html"]
        await scrape_code_list(session, input_files,"data/codes.json")

        with open("data/codes.json") as f:
            things = json.loads(f.read())["codes"]
            codes = [a[0] for a in things]
            
            for code,title in things:
                if (replace_subjects or code not in subjects):
                    subjects[code] = get_default_subject(code,title)

        await cache_handbook(session,codes)

        # From what I can gather, it's fine to scrape the handbook as fast as we want
        # And by that I mean I accidentally did it like 5 million times and I haven't been blocked.
        # Go figure
        tasks = []
        for code in codes:
            tasks.append(scrape_handbook_main(session, code))    
        await asyncio.gather(*tasks)
        
        tasks = []        
        for code in codes:
            tasks.append(scrape_handbook_req(session, code))
        await asyncio.gather(*tasks)

        # Write the contents of the unique dicts to unique_entries.txt
        save_unique_dicts()


        # Scraping studentVIP may or may not be fine. So I will limit it to a leisurely 5 requests a sec.
        # nah screw it I haven't faced any repercussions 
        # studentVIP will scream at you because a lot of 404s will be found.
        
        tasks = []
        for code in codes:
            tasks.append(scrape_studentVIP_main(session,code))
            # await scrape_studentVIP_main(session,code)
            # await sleep(0.2)
        await asyncio.gather(*tasks)

        process_everything(subjects)
        dump_subjects(subjects)

# asyncio.run(do_everything(replace_subjects=True))

# WARNING: Untested code.
async def update_studentVIP():
    global subjects
    async with aiohttp.ClientSession() as session:
        subjects = load_subjects()
        for code in subjects:
            await scrape_studentVIP_main(session,code)
            await sleep(0.2)
        process_everything(subjects)
        dump_subjects(subjects)

# asyncio.run(update_studentVIP())

async def test():
    async with aiohttp.ClientSession() as session:
        # input_files = [f"data/raw/sws2021.html"]
        # await scrape_code_list(session, input_files,"data/codes_test.json")
        with open("data/codes.json") as f:
            things = json.loads(f.read())["codes"]
            codes = [a[0] for a in things]
        await(cache_handbook(session,codes))
            
        #     for code,title in things:
        #         subjects[code] = get_default_subject_min(code,title)
        # dump_subjects()

# asyncio.run(test())