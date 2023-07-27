from typing import TypedDict, List
import feedparser
import logging
from rich.logging import RichHandler
import requests
from bs4 import BeautifulSoup

FORMAT = "%(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt="[%X]",
                    handlers=[RichHandler(markup=True,
                                          rich_tracebacks=True,
                                          tracebacks_suppress=[feedparser,
                                                               requests, BeautifulSoup])])
log = logging.getLogger("rich")


class Review(TypedDict):
    title: str
    score: int
    author: str
    url: str
    image_url: str
    user_url: str
    username: str
    user_image_url: str


# noinspection PyTypeChecker
def get_user_image(user_id: int) -> str:
    user_image_url: str = None
    user_url = f"https://www.goodreads.com/user/show/{user_id}"  # f-string
    page = requests.get(user_url)
    soup = BeautifulSoup(page.content, "html.parser")
    picture_elements = soup.find("div", class_="leftAlignedProfilePicture").find("a")

    for element in picture_elements:
        if element is not None:
            user_image_url = element["src"]
            log.debug(f"Image URL found for {user_id} : {user_image_url}")
            return user_image_url
        else:
            log.debug(f"Not found URL image for {user_id}. Using generic.")
    return user_image_url


class RSSHelper:
    # Get RSS description
    def get_rss_data(self, users: List) -> List[Review]:
        reviews: List[Review] = []
        id = 0
        for user_id in users:
            try:
                rss_feed_url = f'https://www.goodreads.com/user/updates_rss/{user_id}'

                feedparser.USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
                rss_feed = feedparser.parse(rss_feed_url, referrer="http://google.com")
                log.debug(f"Parser HTML status code: {rss_feed.status}")

                # Extract Username
                index = rss_feed.feed.title.find("'s Updates")
                username = rss_feed.feed.title[:index].rstrip()
                log.debug(f"Parsing username: {username}")
                log.debug(f"Found {len(rss_feed.entries)} entries")

                # Get stars position
                for i, entry in enumerate(rss_feed.entries):
                    try:
                        # log.debug(f"Entry description: {entry.description}")
                        info = entry.description
                        second_href = info[info[info.find("href") + 1:].find("href"):]
                        star_position = info.find('star to <a class="bookTitle"')
                        stars_position = info.find('stars to <a class="bookTitle"')
                        is_starred = star_position != -1 or stars_position != -1

                        # Only reviews with Stars
                        # log.debug(f"Stars? {is_starred} {stars_position}")
                        if is_starred:
                            id += 1

                            # Extract Title
                            title = second_href[second_href.find(">") + 1: second_href.find("</a>")]
                            log.debug(f"Title: {title}")

                            # Extract Author
                            author_extract = second_href[second_href.find('<a class="authorName"'):]
                            author = author_extract[author_extract.find(">") + 1: author_extract.find("</a>")]

                            # Extract Score
                            score = 0
                            if star_position != -1:
                                score = info[star_position - 2: star_position].strip()
                            elif stars_position != -1:
                                score = info[stars_position - 2: stars_position].strip()

                            # Extract Images
                            image_url = info[info.find('src=') + 5: info.find('" title')]

                            # Extract URL
                            url = info[9: info.find('">')]

                            # Extract User URL
                            user_url = rss_feed_url.replace("updates_rss", "show")

                            try:
                                user_image_url = get_user_image(user_id)
                            except:
                                user_image_url = "https://i.imgur.com/9pNffkj.png"

                            reviews[id]: Review = {
                                "title": title,
                                "score": score,
                                "author": author,
                                "url": url,
                                "image_url": image_url,
                                "user_url": user_url,
                                "username": username,
                                "user_image_url": user_image_url
                            }
                            log.debug(f"Found review for: {reviews[id]['title']} from {username}")
                    except Exception as error:
                        log.debug(f"This was a bad entry")
            except Exception as error:
                # log.error(traceback.format_exc())
                log.error(f"Couldn't get RSS feed at: https://www.goodreads.com/user/updates_rss/{user_id}")

        return reviews


# Dependant Variables
rsh = RSSHelper()

# Debug
# info = rsh.get_rss_data([50670314, 35497141])
# print(info)
