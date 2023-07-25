from typing import List
import requests
from bs4 import BeautifulSoup
import rss_helper
from rss_helper import RSSHelper, Book

rss_feed = rss_helper.rss_feed_url
rsh = RSSHelper()
books: List[Book] = rsh.get_rss_data(rss_feed)


for i in books:
    # URL = books[i]["user_url"]
    URL = "https://www.goodreads.com/user/show/35497141-marc-cejalvo"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    picture_elements = soup.find_all("div", class_="leftAlignedProfilePicture")
    print(picture_elements)