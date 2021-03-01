import requests
s = "PHYC10696"
handbook_url = f"https://studentvip.com.au/unimelb/subjects/mast20696"
r = requests.get(handbook_url)
print(r.status_code )