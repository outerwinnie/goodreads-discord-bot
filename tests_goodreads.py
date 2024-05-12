import feedparser
import logging
import traceback
import requests
import datetime
import re
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

rss_feed_url = 'https://www.goodreads.com/user/updates_rss/102039931'
log.debug(f"Trying for {rss_feed_url}")

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
        br_tags = info_parsed.find_all("br")
        review_clean = ""
        for tag in br_tags:
            review_dirty = tag.next_sibling.get_text()
            review_clean = review_clean + re.sub(r'^\s*', '',review_dirty).strip() + "\n"
            review_clean = re.sub(r'^\s*', '',review_clean)
        print(review_clean)
        #review_text = br_tag.find("br").get_text()
        #review_text = info[]
    except AttributeError:
        log.debug("No review text found.")
    except Exception as error:
        logging.error(traceback.format_exc())
        #return []
        
print(len("aaa"))
