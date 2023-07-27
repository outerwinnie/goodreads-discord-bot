import traceback
from pprint import pprint
from typing import TypedDict, List
import feedparser
import logging
import requests
from bs4 import BeautifulSoup

#RESTORE

logging.basicConfig(level=logging.INFO)


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
            logging.debug(f"URL found for {user_id} : {user_image_url}")
        else:
            user_image_url = None
            logging.debug(f"Not found {user_id} : {user_image_url}")
    return user_image_url


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
                logging.debug(f"Estado del parser {rss_feed.status}")

                # Extract Username
                index = rss_feed.feed.title.find("'s Updates")
                username = rss_feed.feed.title[:index].rstrip()
                logging.debug(f"Nombre de usuario {username}")
                logging.debug(f"{rss_feed.feed}")

                # Get stars position
                for i, entry in enumerate(rss_feed.entries):
                    try:
                        logging.debug(f"Entry: {entry}")
                        logging.debug(f"Entry description: {entry.description}")
                        info = entry.description
                        logging.debug(f"RSS {info}")
                        second_href = info[info[info.find("href") + 1:].find("href"):]
                        star_position = info.find('star to <a class="bookTitle"')
                        stars_position = info.find('stars to <a class="bookTitle"')
                        is_starred = star_position != -1 or stars_position != -1

                        # Only reviews with Stars
                        logging.debug(f"Hay estrella? Su posicion? {is_starred} {stars_position}")
                        if is_starred:
                            id += 1

                            # Extract Title
                            title = second_href[second_href.find(">") + 1: second_href.find("</a>")]
                            logging.debug(f"Titulo {title}")

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
                            logging.debug(f"Contenido de la review {username} {title}")
                    except Exception as error:
                        logging.debug(f"Entrada malota: {entry}")
            except Exception as error:
                # logging.error(traceback.format_exc())
                logging.debug(f"No se ha podido conectar al RSS https://www.goodreads.com/user/updates_rss/{user_id}")

        return reviews


# Dependant Variables
rsh = RSSHelper()

# Debug
# info = rsh.get_rss_data([50670314, 35497141])
# print(info)
