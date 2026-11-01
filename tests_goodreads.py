import logging
from rich.console import Console
from rich.logging import RichHandler
from pprint import pprint

from classes import extract_user_from_url, BookUser
from rss_helper import RSSHelper
from exceptions import UrlNotValid

FORMAT = "%(message)s"
logging.basicConfig(level="DEBUG",
                    format=FORMAT,
                    datefmt="[%X]",
                    handlers=[RichHandler(markup=True, rich_tracebacks=True)])
log = logging.getLogger("rich")
console = Console()

# normal Goodreads user
user_url = "https://www.goodreads.com/user/show/102039931-pablo"
extracted = extract_user_from_url(user_url)
log.info(f"Extracted user: {extracted}")
assert extracted["id"] == "102039931"

# goodreads Author with profile
author_url = "https://www.goodreads.com/author/show/2917920.Ken_Liu"
extracted_author = extract_user_from_url(author_url)
log.info(f"Extracted author: {extracted_author}")
assert extracted_author["id"] == "8309564"

# author without Goodreads user profile (should raise UrlNotValid)
try:
    extract_user_from_url("https://www.goodreads.com/author/show/13428625.Yolanda_Camacho")
    assert False, "Should have raised UrlNotValid"
except UrlNotValid:
    log.info("Non-user author correctly raised UrlNotValid")

# test scraping reviews for user
rsh = RSSHelper()
test_user: BookUser = {
    "service": 0,
    "id": "102039931",
    "last_review_ts": "2020-01-01 00:00:00",
    "user_url": "https://www.goodreads.com/user/show/102039931-pablo",
    "username": "Pablo",
    "user_image_url": "",
}

reviews = rsh.get_rss_data_goodreads([test_user])
log.info(f"Fetched {len(reviews)} reviews for user 102039931")
for rev in reviews:
    pprint(rev)
    assert rev["title"]
    assert rev["score"] > 0
    assert rev["url"].startswith("http")
    assert rev["review_time_stamp"]

cioran_rev = next((r for r in reviews if "9069461704" in r["review_url"]), None)
if cioran_rev:
    from classes import get_stars
    log.info(f"Review 9069461704 score: {cioran_rev['score']} -> {get_stars(cioran_rev['score'])}")
    assert cioran_rev["score"] == 2.75
    assert get_stars(cioran_rev["score"]) == "★★¾"

# 5. Test fractional stars extraction (half stars 0.5 and quarter stars 0.25)
from bs4 import BeautifulSoup
from rss_helper import extract_score

# 4.25 stars: 4 full stars (p10) + 1 quarter star (p3)
html_quarter = '<span class="staticStars"><span class="staticStar p10"></span><span class="staticStar p10"></span><span class="staticStar p10"></span><span class="staticStar p10"></span><span class="staticStar p3"></span></span>'
soup_q = BeautifulSoup(html_quarter, 'html.parser')
score_q = extract_score(soup_q.find(class_='staticStars'))
log.info(f"Quarter star test: {score_q}")
assert score_q == 4.25

# 3.5 stars: 3 full stars (p10) + 1 half star (p6)
html_half = '<span class="staticStars"><span class="staticStar p10"></span><span class="staticStar p10"></span><span class="staticStar p10"></span><span class="staticStar p6"></span><span class="staticStar p0"></span></span>'
soup_h = BeautifulSoup(html_half, 'html.parser')
score_h = extract_score(soup_h.find(class_='staticStars'))
log.info(f"Half star test: {score_h}")
assert score_h == 3.5

# 4.75 stars: 4 full stars (p10) + 1 three-quarter star (p8)
html_three_q = '<span class="staticStars"><span class="staticStar p10"></span><span class="staticStar p10"></span><span class="staticStar p10"></span><span class="staticStar p10"></span><span class="staticStar p8"></span></span>'
soup_tq = BeautifulSoup(html_three_q, 'html.parser')
score_tq = extract_score(soup_tq.find(class_='staticStars'))
log.info(f"Three-quarter star test: {score_tq}")
assert score_tq == 4.75
