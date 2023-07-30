import traceback
from pprint import pprint
import json
from typing import TypedDict, List
import feedparser
import logging
import requests
import datetime
from rich.logging import RichHandler
from bs4 import BeautifulSoup
from configuration import LOGLEVEL

logging.basicConfig(level=logging.INFO)
USERS_JSON_FILE_PATH = "data/users.json"

FORMAT = "%(message)s"
logging.basicConfig(level=LOGLEVEL,
                    format=FORMAT,
                    datefmt="[%X]",
                    handlers=[RichHandler(markup=True, rich_tracebacks=True)])
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


def get_user_image(user_id: int) -> str:
    user_url = f"https://www.goodreads.com/user/show/{user_id}"  # f-string
    page = requests.get(user_url)
    soup = BeautifulSoup(page.content, "html.parser")
    picture_elements = soup.find("div", class_="leftAlignedProfilePicture").find("a")
    for element in picture_elements:
        if element is not None:
            user_image_url = element["src"]
            log.debug(f"URL found for {user_id} : {user_image_url}")
        else:
            user_image_url = None
            log.debug(f"Not found {user_id} : {user_image_url}")
    return user_image_url

def get_data_from_users_json(json_file_path=USERS_JSON_FILE_PATH):
    f = open(json_file_path, "r+")
    data = json.load(f)
    return data

data = get_data_from_users_json()


def write_to_users_json(new_json_data, json_file_path=USERS_JSON_FILE_PATH):
    with open(json_file_path, 'w') as json_file:
      json.dump(new_json_data, json_file, indent = 4, sort_keys=True)


class RSSHelper:

    # Get RSS description
    def get_rss_data(self, users: List) -> List[Review]:
        reviews = {}
        id = 0
        for user_id in users:
            try:
                rss_feed_url = f'https://www.goodreads.com/user/updates_rss/{user_id}'

                feedparser.USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
                rss_feed = feedparser.parse(rss_feed_url, referrer="http://google.com")
                log.debug(f"Parser HTML status: {rss_feed.status}")



                # Extract Username
                index = rss_feed.feed.title.find("'s Updates")
                username = rss_feed.feed.title[:index].rstrip()
                log.debug(f"Found user: {username}")
                # log.debug(f"{rss_feed.feed}")

                # Get stars position
                for i, entry in enumerate(rss_feed.entries):
                    try:
                        # log.debug(f"Entry: {entry}")
                        # log.debug(f"Entry description: {entry.description}")
                        info = entry.description
                        second_href = info[info[info.find("href") + 1:].find("href"):]
                        star_position = info.find('star to <a class="bookTitle"')
                        stars_position = info.find('stars to <a class="bookTitle"')
                        is_starred = star_position != -1 or stars_position != -1

                        # Only reviews with Stars
                        # log.debug(f"Star found? {is_starred} Position? {stars_position}")
                        if is_starred:
                            id += 1

                            # Extract Timestamp
                            date = datetime.datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
                            hours_time_zone = datetime.timedelta(hours=9)
                            date_converted = date + hours_time_zone

                            for i, user in enumerate(data["users"]):
                                if user["id"] == user_id:
                                    data["users"][i]["last_review_ts"] = date_converted.strptime("%a, %d %b %Y %H:%M:%S")

                            write_to_users_json(data)

                            # Extract Title
                            title = second_href[second_href.find(">") + 1: second_href.find("</a>")]
                            log.debug(f"Title found: {title}")

                            # Extract Author
                            author_extract = second_href[second_href.find('<a class="authorName"'):]
                            author = author_extract[author_extract.find(">") + 1: author_extract.find("</a>")]

                            # Extract Score
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
                                "score": int(score),
                                "author": author,
                                "url": url,
                                "image_url": image_url,
                                "user_url": user_url,
                                "username": username,
                                "user_image_url": user_image_url
                            }
                            log.debug(f"Review found from: {username} for: {title}")
                    except Exception as error:
                        log.debug(f"Bad entry: {entry}")
            except Exception as error:
                # logging.error(traceback.format_exc())
                log.warning(f"Couldn't connect to RSS https://www.goodreads.com/user/updates_rss/{user_id}")

        return reviews


# Dependant Variables
rsh = RSSHelper()

# ------------------- Debug ----------------------
# info = rsh.get_rss_data([50670314, 35497141])
# user_id = 35497141
# rss_feed_url = f'https://www.goodreads.com/user/updates_rss/{user_id}'
# rss_feed = feedparser.parse(rss_feed_url, referrer="http://google.com")
