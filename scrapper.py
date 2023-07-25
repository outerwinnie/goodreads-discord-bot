from typing import List
import requests
from rss_helper import RSSHelper, Book

rss_feed = 'https://www.goodreads.com/user/updates_rss/35497141'
rsh = RSSHelper()
books: List[Book] = rsh.get_rss_data(rss_feed)


for i in books:
        URL = books[i]["user_url"]
        page = requests.get(URL)
        print(page.text)
