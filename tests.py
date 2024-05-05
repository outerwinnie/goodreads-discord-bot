import feedparser
import logging
import requests
import datetime
from bs4 import BeautifulSoup
from rich.console import Console
from rich.logging import RichHandler


FORMAT = "%(message)s"
logging.basicConfig(level="DEBUG",
                    format=FORMAT,
                    datefmt="[%X]",
                    handlers=[RichHandler(markup=True, rich_tracebacks=True)])
log = logging.getLogger("rich")
console = Console()

rss_feed_url = 'https://www.goodreads.com/user/updates_rss/34998873'
log.debug(f"Trying for https://www.goodreads.com/user/updates_rss/34998873")

feedparser.USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
rss_feed = feedparser.parse(rss_feed_url, referrer="http://google.com")

 # Extract Username
index = rss_feed.feed.title.find("'s Updates")
username = rss_feed.feed.title[:index].rstrip()
log.debug(f"Found user: {username}, {len(rss_feed.entries)} entries.")

for i, entry in enumerate(rss_feed.entries):
    try:
        #log.debug(f"Entry #{i}: {entry}")
        #log.debug(f"Entry description: {entry.description}")
        info = entry.description
        second_href = info[info[info.find("href") + 1:].find("href"):]
        star_position = info.find('star to <a class="bookTitle"')
        stars_position = info.find('stars to <a class="bookTitle"')
        is_starred = star_position != -1 or stars_position != -1

        # Only reviews with Stars
        # log.debug(f"Star found? {is_starred} Position? {stars_position}")
        # #Extract Review Text
        info_parsed = BeautifulSoup(info, "html.parser")
        last_br_tag = info_parsed.find_all('br')[-1]
        review_text = last_br_tag.find_next_sibling(text=True).strip()
        print(review_text)
        #review_text = info[]
    except Exception as error:
        # logging.error(traceback.format_exc())
        log.warning(f"Couldn't connect to RSS https://www.goodreads.com/user/updates")
        #return []