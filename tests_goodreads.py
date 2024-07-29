from urllib.parse import urlparse
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

def extract_user_from_url(url) -> dict:
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Accept-Language': 'en-US,en;q=0.9'
    }
    parsed_url = urlparse(url)
    if parsed_url.hostname == "goodreads.com" or parsed_url.hostname == "www.goodreads.com":
        if "/author/" in parsed_url.path:
            try: 
                soup = BeautifulSoup(requests.get(url,headers=headers).text, "html.parser")
                author_url = soup.find('link', rel='alternate', title='Bookshelves')
                if author_url:
                    parsed_url = urlparse(author_url.get('href'))
                    user_id: str = parsed_url.path.split('/')[-1]
                    user_url = f"https://www.goodreads.com/user/updates_rss/{user_id}"
                    log.info(f"Author URL found for Goodreads : {user_url}")
                else:
                    log.error(f"Author URL not found!")
            except Exception as e:
                log.error(f"Issue with author URL!")
                
extract_user_from_url("https://www.goodreads.com/author/show/13428625.Yolanda_Camacho")