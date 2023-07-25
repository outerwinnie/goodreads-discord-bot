from pprint import pprint
import feedparser, logging
from typing import TypedDict, List
logging.basicConfig(level=logging.INFO)

rss_feed_url = 'https://www.goodreads.com/user/updates_rss/35497141'


class Book(TypedDict):
    title: str
    score: int
    author: str
    url: str
    image_url: str
    user_url: str
    username: str


class RSSHelper:
    def __init__(self) -> None:
        return

    def get_rss_data(self, rss_feed) -> List[Book]:
        rss_feed = feedparser.parse(rss_feed)
        books = {}
        id = 0

        # Extract Username
        index = rss_feed.feed.title.find("'s Updates")
        username = rss_feed.feed.title[:index].rstrip()
        logging.info(username)

        for i, entry in enumerate(rss_feed.entries):
            info = entry.description
            # print(summary)
            second_href = info[info[info.find("href") + 1:].find("href"):]
            star_position = info.find('star to <a class="bookTitle"')
            stars_position = info.find('stars to <a class="bookTitle"')
            is_starred = star_position != -1 or stars_position != -1

            if is_starred:  # Only reviews with Stars
                id += 1

                # Extract Title
                title = second_href[second_href.find(">") + 1: second_href.find("</a>")]

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

                # Extract URL - TO DO
                url = info[9: info.find('">')]

                # Extract User URL
                user_url = rss_feed_url.replace("updates_rss", "show")

                #print(username)

                books[id]: Book = {
                    "title": title,
                    "score": int(score),
                    "author": author,
                    "url": url,
                    "image_url": image_url,
                    "user_url": user_url,
                    "username": username
                }

        # print("reviews: ", books)

        return books


rsh = RSSHelper()
# titles = rsh.get_rss_titles(rss_feed_url)
info = rsh.get_rss_data(rss_feed_url)
