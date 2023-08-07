from typing import TypedDict
import logging
import datetime, pytz

from rich.logging import RichHandler
from rich.traceback import install
from rich.console import Console
from configuration import LOGLEVEL, USERS_JSON_FILE_PATH
from configuration import TIME_ZONE, DATE_FORMAT_INPUT, DATE_FORMAT_OUTPUT
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

class BookUser(TypedDict):
    service: int
    id: str
    last_review_ts: str
    user_url: str
    username: str
    user_image_url: str

def get_stars (score: int) -> str:
    score_star = ''
    for x in range(score):
        score_star += '★'
    return score_star


def check_new_reviews (reviews: list[Review], data: dict) -> list[Review]:
    log.info("Checking for new reviews")
    new_reviews = []
    for user in data["users"]:
        last_review_ts = datetime.datetime.strptime(user["last_review_ts"], DATE_FORMAT_OUTPUT)
        for review in reviews:
            if user["user_url"] == review["user_url"]:
                # review_date = datetime.datetime.strptime(review["review_time_stamp"], DATE_FORMAT_OUTPUT)
                if (last_review_ts.timestamp() < datetime.datetime.strptime(review["review_time_stamp"],DATE_FORMAT_OUTPUT).timestamp()):
                    new_reviews.append(review)
                    log.debug(f'User Review Datetime: {user["last_review_ts"]}')
                    log.info(f"New review for {review['title']} by {user['user_url']} on {review['review_time_stamp']}")
                    data_id = get_data_id_from_user_url(data, user["user_url"])
                    if data["users"][data_id]["last_review_ts"] < review["review_time_stamp"]:
                        data["users"][data_id]["last_review_ts"] = review["review_time_stamp"]
            else:
                log.debug("Old review, not sending.")
            
    write_to_users_json(data)
    return new_reviews

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