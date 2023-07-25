import feedparser, logging
from typing import TypedDict, List
import requests
from bs4 import BeautifulSoup
logging.basicConfig(level=logging.INFO)


USER_ID = 35497141 # TO DO, Placeholder, Discord

rss_feed_url = f'https://www.goodreads.com/user/updates_rss/{USER_ID}'


class Review(TypedDict):
    title: str
    score: int
    author: str
    url: str
    image_url: str
    user_url: str
    username: str
    user_image_url: str


def get_user_image(user_id : int) -> str:
    user_url = f"https://www.goodreads.com/user/show/{user_id}" #f-string
    page = requests.get(user_url)
    soup = BeautifulSoup(page.content, "html.parser")
    picture_elements = soup.find("div", class_="leftAlignedProfilePicture").find("a")
    for element in picture_elements:
        if element is not None:
            user_image_url = element["src"]
        else:
            user_image_url = None
    return user_image_url


class RSSHelper:

    # Get RSS description
    def get_rss_data(self, rss_feed) -> List[Review]:
        """
        Esta función envía nudes de hmmm de choicolate pero no hmmmm de hombres asbes

        """
        rss_feed = feedparser.parse(rss_feed)
        reviews = {}
        id = 0

        # Extract Username
        index = rss_feed.feed.title.find("'s Updates")
        username = rss_feed.feed.title[:index].rstrip()
        # logging.info(username)

        # Get stars position
        for i, entry in enumerate(rss_feed.entries):
            info = entry.description
            # print(summary)
            second_href = info[info[info.find("href") + 1:].find("href"):]
            star_position = info.find('star to <a class="bookTitle"')
            stars_position = info.find('stars to <a class="bookTitle"')
            is_starred = star_position != -1 or stars_position != -1

            # Only reviews with Stars
            if is_starred:
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

                # Extract URL
                url = info[9: info.find('">')]

                # Extract User URL
                user_url = rss_feed_url.replace("updates_rss", "show")


                # print(username)

                reviews[id]: Review = {
                    "title": title,
                    "score": int(score),
                    "author": author,
                    "url": url,
                    "image_url": image_url,
                    "user_url": user_url,
                    "username": username,
                    "user_image_url" : get_user_image(USER_ID)
                }


        return reviews


# Dependant Variables
rsh = RSSHelper()
# info = rsh.get_rss_data(rss_feed_url)

