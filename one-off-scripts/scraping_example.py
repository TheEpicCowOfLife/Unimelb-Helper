# Demonstration of async webscraping with aiohttp + beautiful soup that I (TheEpicCowOfLife) wrote for a friend after

import aiohttp
import asyncio
from bs4 import BeautifulSoup

# Gets soup. Soup is an abstract representation of the HTML that has already been nicely parsed. 
# Has plenty of nice helper functions
async def get_soup(session,url):
    print("hi")
    async with session.get(url) as req:
        if req.status == 200:
            return BeautifulSoup(await req.text(), 'html.parser')
    return None

async def process_url(session,url):
    soup = await get_soup(session,url)
    if (soup != None):        
        # Look up the beautifulsoup documentation to see what you can do with this soup object
        result = soup.find(class_ = "nav nav-tabs")
    
        # go to the next sibling
        print (result.next_sibling)

        # ... a couple times
        print (result.next_sibling.next_sibling)
        print (result.next_sibling.next_sibling.next_sibling)
        print (result.next_sibling.next_sibling.next_sibling.next_sibling)

        # I am pretty sure a lot of times you want the .text attribute too
# basically our main function, we have to put it in async so we can go faste
async def do_stuff():
    async with aiohttp.ClientSession() as session:
        # we make an array of all the tasks 
        tasks = []

        tasks.append(process_url(session,"http://orac.amt.edu.au/cgi-bin/train/fame_detail.pl?problemid=1081"))
        tasks.append(process_url(session,"http://orac.amt.edu.au/cgi-bin/train/fame_detail.pl?problemid=1080"))
        # Note that at this point, not all the functions in tasks have returned yet. Hence we wait for it
        # by calling asyncio.gather
        # If process_url returns something then results will contain all the return values 
        
        results = await asyncio.gather(*tasks)
    
# Actually call do_stuff
asyncio.run(do_stuff())
