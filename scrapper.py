from typing import List
import requests
from bs4 import BeautifulSoup
import rss_helper
from rss_helper import RSSHelper, Review

rss_feed = rss_helper.rss_feed_url
rsh = RSSHelper()
reviews: List[Review] = rsh.get_rss_data(rss_feed)


