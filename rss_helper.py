import traceback
from pprint import pprint
import json, re
from json import JSONDecodeError
from typing import List
import feedparser
import logging
import requests
import datetime
from rich.console import Console
from rich.logging import RichHandler
from bs4 import BeautifulSoup
from configuration import LOGLEVEL, DATA_FOLDER, USERS_JSON_FILE_PATH, GOODREADS_SERVICE
from configuration import TIME_ZONE, DATE_FORMAT_INPUT, DATE_FORMAT_OUTPUT
import pytz
from classes import Review, BookUser, read_json_data, write_to_users_json, is_old_review
import bookwyrm

USERS_JSON_FILE_PATH = "data/users.json"



FORMAT = "%(message)s"
logging.basicConfig(level=LOGLEVEL,
                    format=FORMAT,
                    datefmt="[%X]",
                    handlers=[RichHandler(markup=True, rich_tracebacks=True)])
log = logging.getLogger("rich")
console = Console()


def get_user_image(user_id: str) -> str:
    user_url = f"https://www.goodreads.com/user/show/{user_id}"
    #page = requests.get(user_url)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    soup = BeautifulSoup(requests.get(user_url,headers=headers).text, "html.parser")
    try:
        picture_elements = soup.find("div", class_="leftAlignedProfilePicture").find("a")
        for element in picture_elements:
            if element is not None:
                user_image_url = element["src"]
                log.debug(f"URL found for {user_id} : {user_image_url}")
                return user_image_url
    except Exception as e:
        log.info(f"No picture found for user {user_id}, trying if author...")
        
    # try if author page
    try:
        picture_elements = soup.find("div", class_="leftContainer authorLeftContainer").find("a")
        for element in picture_elements:
            if element is not None:
                user_image_url = element["src"]
                log.debug(f"URL found for {user_id} : {user_image_url}")
                return user_image_url
    except Exception as e:
        log.info(f"No picture found for user {user_id}, using generic")
        
    ## Image not found, return generic   
    user_image_url = "https://i.imgur.com/9pNffkj.png"
    log.debug(f"Not found {user_id} : {user_image_url}")
    return user_image_url
    


# data = get_data_from_users_json()


class RSSHelper:

    # Get RSS description
    def get_rss_data_goodreads(self, users: List[BookUser]) -> List[Review]:
        reviews = []
        #user_list: List[BookUser] = [user for user in users]
        for user in users:
            if user["service"] != GOODREADS_SERVICE:
                continue
            try:
                rss_feed_url = f'https://www.goodreads.com/user/updates_rss/{user["id"]}'
                log.debug(f"Trying for {user['user_url']}")

                feedparser.USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
                rss_feed = feedparser.parse(rss_feed_url, referrer="http://google.com")
                log.debug(f"Parser HTML status: {rss_feed.status}")

                # Extract Username
                index = rss_feed.feed.title.find("'s Updates")
                username = rss_feed.feed.title[:index].rstrip()
                log.debug(f"Found user: {username}, {len(rss_feed.entries)} entries.")
                # log.debug(f"{rss_feed.feed}")

                # Get stars position
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
                        if is_starred:
                            log.debug("Review found!")

                            # Extract Review Timestamp
                            date = datetime.datetime.strptime(entry.published, DATE_FORMAT_INPUT)
                            review_date_timezoned = date.astimezone(pytz.timezone(TIME_ZONE))
                            
                            
                            # Extract Title
                            title = second_href[second_href.find(">") + 1: second_href.find("</a>")]
                            log.debug(f"Title found: {title}")

                            # Extract Author
                            author_extract = second_href[second_href.find('<a class="authorName"'):]
                            author = author_extract[author_extract.find(">") + 1: author_extract.find("</a>")]

                            # Extract Review URL
                            review_url = entry.link
                            log.debug(f"Review URL found: {review_url}")
                            
                            # Extract Score
                            if star_position != -1:
                                score = info[star_position - 2: star_position].strip()
                            elif stars_position != -1:
                                score = info[stars_position - 2: stars_position].strip()

                            # Extract Review Text
                                review_text = ""
                                try:
                                    info_parsed = BeautifulSoup(info, "html.parser")
                                    br_tags = info_parsed.find_all("br")
                                    for tag in br_tags:
                                        review_dirty = tag.next_sibling.get_text()
                                        review_text = review_text + re.sub(r'^\s*', '',review_dirty).strip() + "\n"
                                        review_text = re.sub(r'^\s*', '',review_text)
                                except AttributeError:
                                    log.debug("No review text found.")
                                except Exception as error:
                                    logging.error(traceback.format_exc())
                            
                            # Extract Images
                            image_url = info[info.find('src=') + 5: info.find('" title')]

                            # Extract URL
                            url = info[9: info.find('">')]
                            user_image_url = get_user_image(user["id"])
                            
                            review = {
                                "title": title,
                                "score": int(score),
                                "author": author,
                                "url": url,
                                "image_url": image_url,
                                "user_url": user["user_url"],
                                "username": username,
                                "user_image_url": user_image_url,
                                "review_text": review_text,
                                "review_url": review_url,
                                "review_time_stamp": review_date_timezoned.strftime(DATE_FORMAT_OUTPUT),
                            }
                            reviews.append(review)
                            log.debug(f"Review found from: {username} for: {title}")
                            if is_old_review(user, review):
                                log.info(f"Finished checking reviews for user {username}, found old review")
                                break
                    except AttributeError:
                        log.debug(f"Bad entry: {i}")
                    except Exception as error:
                        console.print_exception()
                        # log.debug(f"Bad entry: {entry}")
            except Exception as error:
                # logging.error(traceback.format_exc())
                log.warning(f"Couldn't connect to RSS https://www.goodreads.com/user/updates_rss/{user['id']}")
                #return []

        return reviews

    def get_bookwyrm_data (self, users: List[BookUser]) -> List[Review]:
        bookwyrm_reviews = bookwyrm.get_users_reviews(users)
        return bookwyrm_reviews
    
    def get_reviews(self, users: List[BookUser]) -> List[Review]:
        goodreads_reviews = self.get_rss_data_goodreads(users)
        bookwyrm_reviews = self.get_bookwyrm_data(users)
        return goodreads_reviews + bookwyrm_reviews
            
# Dependant Variables
rsh = RSSHelper()

# ------------------- Debug ----------------------
# info = rsh.get_rss_data_goodreads([50670314, 35497141])
# user_id = 35497141
# rss_feed_url = f'https://www.goodreads.com/user/updates_rss/{user_id}'
# rss_feed = feedparser.parse(rss_feed_url, referrer="http://google.com")
