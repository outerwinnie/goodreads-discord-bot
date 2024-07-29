from typing import TypedDict
import logging
import datetime, pytz
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
from rich.logging import RichHandler
from rich.traceback import install
from rich.console import Console
from configuration import BOOKWYRM_SERVICE, BOOKWYRM_INSTANCES, GOODREADS_SERVICE, LOGLEVEL, USERS_JSON_FILE_PATH
from configuration import TIME_ZONE, DATE_FORMAT_INPUT, DATE_FORMAT_OUTPUT
from exceptions import UrlNotValid
import json
#from rss_helper import write_to_users_json

if logging.root.level == logging.DEBUG:
    install(show_locals=True)
else:
    install(show_locals=False)
console = Console()

FORMAT = "%(message)s"
logging.basicConfig(level=LOGLEVEL,
                    format=FORMAT,
                    datefmt="[%X]",
                    handlers=[RichHandler(markup=True, rich_tracebacks=True)])
log = logging.getLogger("rich")
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

class Review(TypedDict):
    title: str
    score: int
    author: str
    review_time_stamp: str
    url: str
    image_url: str
    user_url: str
    username: str
    user_image_url: str
    review_text: str
    review_url: str

class BookUser(TypedDict):
    service: int
    id: str
    last_review_ts: str
    user_url: str
    username: str
    user_image_url: str

def extract_user_from_url(url) -> dict:
    parsed_url = urlparse(url)
    if parsed_url.hostname == "goodreads.com" or parsed_url.hostname == "www.goodreads.com":
        if "/author/" in parsed_url.path:
            try: 
                soup = BeautifulSoup(requests.get(url,headers=headers).text, "html.parser")
                author_url = soup.find('link', rel='alternate', title='Bookshelves')
                if author_url:
                    parsed_url = urlparse(author_url.get('href'))
                    user_id: str = parsed_url.path.split('/')[-1]
                    user_url = f"https://www.goodreads.com/user/show/{user_id}"
                    user = {
                        "service": GOODREADS_SERVICE,
                        "id": user_id,
                        "user_url" : user_url
                        }
                    log.info(f"Author URL found for Goodreads : {user_url}")
                else:
                    log.error(f"Author URL not found!")
                    raise UrlNotValid
            except Exception as e:
                log.error(f"Issue with author URL!")
                raise UrlNotValid
        else:    
            user_id: str = parsed_url.path.split('/')[-1].split('-')[0]
            user = {
                "service": GOODREADS_SERVICE,
                "id": user_id,
                "user_url" : f"{parsed_url.scheme}://{parsed_url.hostname}{parsed_url.path}"
            }
        if user_id.isdigit():
            log.debug(f"BookUser {user_id} found for Goodreads")
            return user
        else:
            log.error(f"URL not supported!")
            raise UrlNotValid
        
    if parsed_url.hostname in BOOKWYRM_INSTANCES:
        if "/author/" in parsed_url.path:
            log.error(f"URL not supported!")
            raise UrlNotValid
        else:
            user_id = parsed_url.path.split('/')[-1]
            user = {
                "service": BOOKWYRM_SERVICE,
                "id" : user_id,
                "user_url" : f"{parsed_url.scheme}://{parsed_url.hostname}{parsed_url.path}"
            }
            log.debug(f"BookUser {user_id} found for Bookwyrm")
            return user  
    else:
        log.error(f"URL not supported!")
        raise UrlNotValid


def get_stars (score: int) -> str:
    score_star = ''
    for x in range(score):
        score_star += '★'
    return score_star

def is_old_review (user: BookUser, review: Review):
    last_review_ts = datetime.datetime.strptime(user["last_review_ts"], DATE_FORMAT_OUTPUT)
    if user["user_url"] == review["user_url"]:
        if (last_review_ts.timestamp() < datetime.datetime.strptime(review["review_time_stamp"],DATE_FORMAT_OUTPUT).timestamp()):
            #new_reviews.append(review)
            log.debug(f'User Review Datetime: {user["last_review_ts"]}')
            log.info(f"New review for {review['title']} by {user['user_url']} on {review['review_time_stamp']}")
            if user["last_review_ts"] < review["review_time_stamp"]:
                return False
        else:
            log.debug(f"Old review: {review['title']}. Stopping loop.")
            return True
            

def check_new_reviews (reviews: list[Review], data: dict) -> list[Review]:
    log.info("Checking for new reviews")
    new_reviews = []
    for user in data["users"]:
        last_review_ts = datetime.datetime.strptime(user["last_review_ts"], DATE_FORMAT_OUTPUT)
        for review in reviews:
            if user["user_url"] == review["user_url"]:
                # review_date = datetime.datetime.strptime(review["review_time_stamp"], DATE_FORMAT_OUTPUT)
                if (last_review_ts.timestamp() < datetime.datetime.strptime(review["review_time_stamp"],DATE_FORMAT_OUTPUT).timestamp()):
                #if True:
                    new_reviews.append(review)
                    log.debug(f'User Review Datetime: {user["last_review_ts"]}')
                    log.info(f"New review for {review['title']} by {user['user_url']} on {review['review_time_stamp']}")
                    data_id = get_data_id_from_user_url(data, user["user_url"])
                    if data["users"][data_id]["last_review_ts"] < review["review_time_stamp"]:
                        data["users"][data_id]["last_review_ts"] = review["review_time_stamp"]
                else:
                    log.debug(f"Old review: {review['title']}, not sending.")
            
    write_to_users_json(data)
    return new_reviews

def format_review_text (review: Review) -> str:
    max_review_lenght = 350
    if len(review["review_text"]) > max_review_lenght:
        review["review_text"] = review["review_text"][:max_review_lenght] + "..."
    review["review_text"] = (f"{review['author']}\n\n"
                            f">>> {review['review_text']}\n"
                            f"[Ver reseña completa]({review['review_url']})")
    return review["review_text"]

def get_data_id_from_user_url(data: dict, user_url: str) -> int:
    for i, user in enumerate(data["users"]):
        if user["user_url"] == user_url:
            return i
    

def read_json_data(json_file_path=USERS_JSON_FILE_PATH) -> dict:
    try:        
        f = open(json_file_path, "r+")
        data = json.load(f)
        return data
    except json.JSONDecodeError:
        log.info("No users in json file")
        return {}


def write_to_users_json(new_json_data, json_file_path=USERS_JSON_FILE_PATH):
    with open(json_file_path, 'w') as json_file:
        json.dump(new_json_data, json_file, indent=4, sort_keys=True)