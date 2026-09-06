import traceback
import logging, os, validators
from types import NoneType
from typing import List
from rich.logging import RichHandler
from rich import print
from rich.pretty import pprint
from rich.traceback import install
from rich.console import Console
from bs4 import BeautifulSoup, NavigableString
import re, pytz
import requests
from urllib.parse import urlparse, urljoin
from datetime import datetime, timedelta


from configuration import LOGLEVEL, BOOKWYRM_SERVICE
from configuration import TIME_ZONE, DATE_FORMAT_INPUT, HEADERS, DATE_FORMAT_OUTPUT
from classes import Review, BookUser
from classes import is_old_review

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

BOOKWYRM_HEADERS = {
    "User-Agent": "bookwyrm-review-reader/1.0",
    "Accept-Language": "en-US",
}

#rss_url = "https://bookwyrm.social/user/potajito/rss-reviews"
#user_profile_url = "https://bookwyrm.social/user/potajito"

def parse_book_name (s: str) -> str:
    """Extracts book name from a string, searching for the text between double quotes ("text")

    Args:
        s (str): _description_

    Returns:
        str: _description_
    """
    
    # Find the index of the first double quote
    start_index = s.find('"')
    # Find the index of the second double quote after the first one
    end_index = s.find('"', start_index + 1)

    # Extract the substring between the two double quotes
    result = s[start_index + 1:end_index]
    return result
    

def parse_score (s: str) -> int:
    """Extracts score from a string , searching for the number between parenthesis "(4 stars)"

    Args:
        s (str): _description_

    Returns:
        str: _description_
    """
    pattern = r"(\d+ stars)"
    match = re.search(pattern, s)
    
    if match:
        stars_string = match.group(1) # Extract the string "x stars". We do it like this to avoid extracting the wrong info with books that could contain numbers in the title
        # Now we extract the score
        score = int(stars_string.split()[0])
        return score
    else:
        log.debug(f"No score found on {s}")
        return 0

def append_to_url(url: str, path_to_append: str) -> str:
    # Ensure path_to_append starts with a slash and url doesn't have one
    if not url.endswith('/'):
        url = f"{url}/"
    if path_to_append.startswith('/'):
        path_to_append = path_to_append[1:]
        return url + path_to_append

def find_book_title(entry: NavigableString) -> str:
    try:
        tag: NavigableString = entry.find('a', href=lambda href: href and '/book/' in href)
        if tag:
            return tag.get_text().strip()
    except Exception:
        return 'Unknown book'
    
def find_book_author(entry: NavigableString) -> str:
    try:
        tag: NavigableString = entry.find('a', href=lambda href: href and '/author/' in href)
        if tag:
            book_author = tag.get_text().strip()
            if book_author:
                return book_author
        else:
            return 'Unknown author'        
    except Exception:
        return 'Unknown author'

def find_review_url(entry: NavigableString, profile_url: str) -> str:
    try:
        parsed_url = urlparse(profile_url)
        hostmane = re.escape(parsed_url.hostname)
        href_pattern = re.compile(rf'https://{hostmane}/user/.+')
        tag: NavigableString = entry.find('a', href=href_pattern)
        if tag:
            review_url = tag['href']
            if review_url:
                return review_url
        else:
            return profile_url        
    except Exception:
        return profile_url

def find_time_elapsed(entry: NavigableString, profile_url: str) -> str:
    try:
        parsed_url = urlparse(profile_url)
        hostmane = re.escape(parsed_url.hostname)
        href_pattern = re.compile(rf'https://{hostmane}/user/.+')
        tag: NavigableString = entry.find('a', href=href_pattern)
        if tag:
            time_elapsed_str = tag.get_text().strip()
            if time_elapsed_str:
                return time_elapsed_str
        else:
            return 'Unknown time'        
    except Exception:
        return 'Unknown time'


def fill_review (title: str, score: int, author: str,
                url: str, image_url: str, user_url: str,
                username: str, user_image_url: str, review_time_stamp: str,
                review_text: str, review_url: str) -> Review:
    """Adds fields to Review class

    Args:
        review (Review): _description_
    """ 
    if review_time_stamp > datetime.now(review_time_stamp.tzinfo):
        review_time_stamp = review_time_stamp.replace(year=1984)

    review_time_stamp = review_time_stamp.strftime(DATE_FORMAT_OUTPUT)
    current_review = {
            "title": title,
            "score": score,
            "author": author,
            "url": url,
            "image_url": image_url,
            "user_url": user_url,
            "username": username,
            "user_image_url": user_image_url,
            "review_time_stamp": review_time_stamp,
            "review_text": review_text,
            "review_url": review_url
            }
    # log.debug(f"Added review: {current_review}")
    return current_review 

def bookwyrm_get(url: str, *, activity_json: bool = False) -> requests.Response:
    """Make a GET request to BookWyrm with the appropriate headers."""
    headers = BOOKWYRM_HEADERS.copy()
    if activity_json:
        headers["Accept"] = "application/activity+json"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response

def parse_user_profile(user: BookUser) -> List[Review]:
    reviews: List[Review] = []

    # Fetch user profile
    try:
        response = bookwyrm_get(user["user_url"], activity_json=True)
        data = response.json()
        log.debug("Fetched BookWyrm user profile data! Valid JSON!")
    except requests.exceptions.JSONDecodeError:
        log.error(
            f"Invalid JSON returned by {user['user_url']}. "
            "Cannot parse user profile."
        )
        return reviews
    except requests.exceptions.RequestException as exc:
        log.error(f"Could not fetch BookWyrm user {user['user_url']}: {exc}")
        return reviews

    icon = data.get("icon") or {}

    username = data.get("preferredUsername", "")
    user_image_url = icon.get("url", "")
    user_outbox_url = data.get("outbox", "")

    # Fetch user's outbox
    try:
        user_outbox_response = bookwyrm_get(user_outbox_url, activity_json=True)
        user_outbox_data = user_outbox_response.json()
        log.debug("Fetched BookWyrm user outbox data! Valid JSON!")
    except requests.exceptions.JSONDecodeError:
        log.error(
            f"Invalid JSON returned by {user_outbox_url}. "
            "Cannot parse user outbox."
        )
        return reviews

    outbox_first_url = user_outbox_data.get("first", "")

    # Fetch first page of outbox
    try:
        outbox_first_response = bookwyrm_get(outbox_first_url, activity_json=True)
        outbox_first_data = outbox_first_response.json()
        log.debug("Fetched BookWyrm user outbox first page data! Valid JSON!")
    except requests.exceptions.JSONDecodeError:
        log.error(
            f"Invalid JSON returned by {outbox_first_url}. "
            "Cannot parse user outbox first page."
        )
        return reviews

    for item in outbox_first_data.get("orderedItems", []):
        if item.get("type") != "Article":
            continue

        content = item.get("content", "")
        if not content:
            continue

        # Extract book name and score from review title
        title = item.get("name", "")
        score = parse_score(title)
        book_name = parse_book_name(title)

        # Extract review text
        review_text_match = re.search(
            r"<p>(.*?)</p>",
            content,
            re.DOTALL,
        )
        review_text = (
            review_text_match.group(1).strip()
            if review_text_match
            else ""
        )

        # Get image attached to the review
        attachments = item.get("attachment") or []
        capsule_image_url = (
            attachments[0].get("url", "")
            if attachments
            else ""
        )

        book_reviewed = item.get("inReplyToBook", "")

        # Fetch book information
        book_response = bookwyrm_get(
            book_reviewed,
            activity_json=True,
        )
        book_data = book_response.json()

        cover = book_data.get("cover") or {}
        book_title = cover.get("name", "")

        # Extract author from strings such as:
        # "Han Kang: La vegetariana (Paperback, Español language, 2024)"
        author = "Unknown author"
        author_match = re.match(
            r"^(.+?):\s*(?=[^(]+(?:\(|$))",
            book_title,
        )

        if author_match:
            author = author_match.group(1).strip()

        book_url_img = cover.get("url", "") or capsule_image_url

        published = datetime.fromisoformat(item.get("published", ""))
        review_url = item.get("id", "")

        review = fill_review(
            book_name,
            score,
            author,
            book_reviewed,
            book_url_img,
            user["user_url"],
            username,
            user_image_url,
            published,
            review_text,
            review_url,
        )

        reviews.append(review)
        log.debug(f"Added review: {review}")

    return reviews


def get_users_reviews (users: List[BookUser]) -> List[Review]:
    reviews: List[Review] = [] 
    for user in users:
        if user['service'] == BOOKWYRM_SERVICE:
            user_reviews = parse_user_profile(user)
            log.debug(reviews)
            log.debug(user_reviews)
            reviews = reviews + user_reviews
    #log.debug(pprint(reviews))
    return reviews

def convert_elapsed_to_timestamp(elapsed_time: str) -> str:
    """Converts elapsed time to timestamp.

    Converts elapsed time to timestamp.

    Examples:
        >>> convert_elapsed_to_timestamp("5 minutes ago")
        'Sat, 30 Sep 2019 21:00:00 +0000'
        >>> convert_elapsed_to_timestamp("6 hours ago")
        'Sat, 30 Sep 2019 15:00:00 +0000'
        >>> convert_elapsed_to_timestamp("6 seconds ago")
        'Sat, 30 Sep 2019 21:00:06 +0000'

    Notes:
        The elapsed time is in format "5 minutes ago", "6 hours ago", "6 seconds ago".
        The timestamp is in format "Sat, 30 Sep 2019 21:00:00 +0000".

    Args:
        elapsed_time (str): _description_

    Returns:
        str: _description_
    """
    # Map time units to corresponding timedelta units
    date_format_no_seconds = "%Y-%m-%d %H:%M:00"
    date_format_no_minutes = "%Y-%m-%d %H:00:00"
    bad_date = "2023-03-27 00:00:00"
    
    time_unit_map = {
        'second': 'seconds',
        'seconds': 'seconds',
        'minute': 'minutes',
        'minutes': 'minutes',
        'hour': 'hours',
        'hours': 'hours',
        'day': 'days',
        'days': 'days',
        'week': 'weeks',
        'weeks': 'weeks',
        'month': 'days',  # Approximation
        'months': 'days', # Approximation
        'year': 'days',   # Approximation
        'years': 'days'   # Approximation
    }
    # Parse the input elapsed time string
    parts = elapsed_time.split()
    if parts:
        try:
            if parts[0] in ["an", "a"]:
                quantity = 1
                unit = parts[1]
            elif parts[1] in time_unit_map:
                quantity = int(parts[0])
                unit = parts[1]
            else:
                try:
                    current_year = datetime.now().year
                    input_string_with_year = f"{elapsed_time} {current_year}"
                    target_date = datetime.strptime(input_string_with_year, "%b %d %Y")
                    formatted_date = target_date.strftime(date_format_no_seconds)
                    return formatted_date
                except ValueError:
                    return bad_date
        except (ValueError, IndexError):
            return bad_date
        
    
    # Calculate the timestamp
    current_time = datetime.now()
    delta = timedelta(**{time_unit_map[unit]: quantity})
    target_time = current_time - delta
    # Format the timestamp with time zone
    timestamp_format = date_format_no_seconds
    if parts[1] in ["hour", "hours"]: # To account of having no minutes info on "x hours ago"
        timestamp_format = date_format_no_minutes
        
    formatted_timestamp = target_time.strftime(timestamp_format)
    return formatted_timestamp

""" def test_this ():
    profile_url = 'https://bookwyrm.social/user/potajito'
   log.debug(f' Trying {profile_url}')
    parse_user_profile(profile_url)
    
test_this() """