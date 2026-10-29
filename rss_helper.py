import traceback
from pprint import pprint
import json, re
from typing import List
import logging
import requests
import datetime
from rich.console import Console
from rich.logging import RichHandler
from bs4 import BeautifulSoup
from configuration import LOGLEVEL, DATA_FOLDER, HEADERS, USERS_JSON_FILE_PATH, GOODREADS_SERVICE
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

def parse_goodreads_date(ts_str: str) -> str:
    if not ts_str:
        return ""
    pacific_tz = pytz.timezone("America/Los_Angeles")
    target_tz = pytz.timezone(TIME_ZONE)
    for fmt in ("%B %d, %Y %H:%M", "%B %d, %Y %I:%M%p", "%b %d, %Y %I:%M%p", "%b %d, %Y %I:%M %p"):
        try:
            dt = datetime.datetime.strptime(ts_str.strip(), fmt)
            dt_pacific = pacific_tz.localize(dt)
            return dt_pacific.astimezone(target_tz).strftime(DATE_FORMAT_OUTPUT)
        except ValueError:
            pass
    return ""


def extract_score(stars_el, action_text: str = "") -> float:
    if not stars_el:
        return 0.0

    # 1. Sum up star spans (p10 = 1.0, p6/p5 = 0.5, p3/p2 = 0.25, p7/p8 = 0.75)
    score = 0.0
    for span in stars_el.find_all("span", class_=re.compile(r"staticStar")):
        classes = span.get("class", [])
        for c in classes:
            if c == "p10":
                score += 1.0
            elif c in ("p6", "p5"):
                score += 0.5
            elif c in ("p3", "p2"):
                score += 0.25
            elif c in ("p7", "p8"):
                score += 0.75

    if score > 0:
        return score

    # 2. Check title attribute or action text for numerical rating (e.g. "4.5" or "4.25")
    title_attr = (stars_el.get("title") or "").strip()
    m = re.search(r"(\d+(?:\.\d+)?)", title_attr)
    if m and any(char in title_attr for char in (".", "star")):
        return float(m.group(1))

    # 3. Traditional Goodreads tooltip text (e.g. "really liked it")
    label_map = {
        "did not like it": 1.0,
        "it was ok": 2.0,
        "liked it": 3.0,
        "really liked it": 4.0,
        "it was amazing": 5.0,
    }
    if title_attr.lower() in label_map:
        return label_map[title_attr.lower()]

    # 4. Fallback: regex search in action text
    m_act = re.search(r"(\d+(?:\.\d+)?)\s*stars?", action_text, re.IGNORECASE)
    if m_act:
        return float(m_act.group(1))

    return 0.0


def get_widget_ratings(user_id: str) -> dict:
    url = f"https://www.goodreads.com/review/custom_widget/{user_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        start = r.text.find("var widget_code = '")
        end = r.text.rfind("var widget_div =")
        if start == -1 or end == -1:
            return {"by_id": {}, "by_title": {}}
        raw = r.text[start + len("var widget_code = '"): end].rstrip("\n' ")
        raw = raw.replace('\\\"', '"').replace(r'\/', '/').replace(r"\'", "'").replace(r'\n', '\n')

        ratings_by_id = {}
        ratings_by_title = {}
        chunks = re.split(r'class=[\"\']gr_custom_book_container_[\"\']', raw)
        for chunk in chunks[1:]:
            m_rating = re.search(r'class=[\"\']gr_custom_rating_[\"\']>(.*?)(?:</div>|<div)', chunk, re.S)
            if not m_rating:
                continue
            rating_html = m_rating.group(1)
            score = 0.0
            for img_src in re.findall(r'gr_flat_red_star_([a-zA-Z0-9_]+)\.png', rating_html):
                if img_src == "active":
                    score += 1.0
                elif img_src == "75pct":
                    score += 0.75
                elif img_src == "50pct":
                    score += 0.50
                elif img_src == "25pct":
                    score += 0.25

            m_rev = re.search(r'/review/show/(\d+)', chunk)
            if m_rev:
                ratings_by_id[m_rev.group(1)] = score

            m_title = re.search(r'title=[\"\']([^\"\']+)[\"\']', chunk)
            if m_title:
                ratings_by_title[m_title.group(1).lower().strip()] = score

        return {"by_id": ratings_by_id, "by_title": ratings_by_title}
    except Exception:
        return {"by_id": {}, "by_title": {}}


def get_user_image(user_id: str) -> str:
    user_url = f"https://www.goodreads.com/user/show/{user_id}"
    try:
        soup = BeautifulSoup(requests.get(user_url, headers=HEADERS, timeout=10).text, "html.parser")
        picture_elements = soup.find("div", class_="leftAlignedProfilePicture")
        if picture_elements and picture_elements.find("img"):
            user_image_url = picture_elements.find("img").get("src")
            if user_image_url:
                log.debug(f"URL found for {user_id} : {user_image_url}")
                return user_image_url

        author_elements = soup.find("div", class_="leftContainer authorLeftContainer")
        if author_elements and author_elements.find("img"):
            user_image_url = author_elements.find("img").get("src")
            if user_image_url:
                log.debug(f"URL found for {user_id} : {user_image_url}")
                return user_image_url
    except Exception as e:
        log.info(f"No picture found for user {user_id}, using generic")

    user_image_url = "https://i.imgur.com/9pNffkj.png"
    log.debug(f"Not found {user_id} : {user_image_url}")
    return user_image_url


class RSSHelper:

    def get_rss_data_goodreads(self, users: List[BookUser]) -> List[Review]:
        reviews = []
        for user in users:
            if user["service"] != GOODREADS_SERVICE:
                continue
            try:
                user_id = user["id"]
                url = f"https://www.goodreads.com/user/delayable_user_show/{user_id}"
                log.debug(f"Checking Goodreads updates for {user['user_url']}")

                r = requests.get(url, headers=HEADERS, timeout=15)
                if r.status_code != 200:
                    log.warning(f"Couldn't fetch Goodreads updates for {user_id}, status {r.status_code}")
                    continue

                widget_ratings = get_widget_ratings(user_id)
                soup = BeautifulSoup(r.text, "html.parser")
                h2 = soup.find("h2")
                default_username = re.sub(r"[’']s Recent Updates.*$", "", h2.get_text(strip=True)) if h2 else ""
                user_image_url = get_user_image(user_id)

                updates = soup.find_all("tr", class_="update", attrs={"data-timestamp": True})
                log.debug(f"Found user: {default_username}, {len(updates)} entries.")

                for i, u in enumerate(updates):
                    try:
                        stars_el = u.find(class_="staticStars")
                        action_el = u.find(class_="updateAction")
                        action_text = action_el.get_text(" ", strip=True) if action_el else ""

                        if not stars_el and "rated a book" not in action_text:
                            continue

                        # Extract book title and URL
                        title_el = u.find("a", class_="bookTitle")
                        if not title_el:
                            continue
                        title = title_el.get_text(strip=True)
                        book_url = title_el.get("href", "")
                        if book_url.startswith("/"):
                            book_url = f"https://www.goodreads.com{book_url}"

                        # Extract author
                        author_el = u.find("a", class_="authorName")
                        author = author_el.get_text(strip=True) if author_el else ""

                        # Extract review URL
                        review_url = book_url
                        rev_id = None
                        rev_a = u.find("a", href=re.compile(r"^/review/show/\d+"))
                        if not rev_a:
                            sib = u.find_next_sibling("tr")
                            while sib and not sib.has_attr("data-timestamp"):
                                rev_a = sib.find("a", href=re.compile(r"^/review/show/\d+"))
                                if rev_a:
                                    break
                                sib = sib.find_next_sibling("tr")
                        if rev_a:
                            rev_path = rev_a["href"].split("?")[0]
                            review_url = f"https://www.goodreads.com{rev_path}" if rev_path.startswith("/") else rev_path
                            m_rev_id = re.search(r"/review/show/(\d+)", rev_path)
                            if m_rev_id:
                                rev_id = m_rev_id.group(1)

                        # Extract score: prefer exact fractional rating from custom_widget, fallback to CSS classes
                        score = 0.0
                        if rev_id and rev_id in widget_ratings.get("by_id", {}):
                            score = widget_ratings["by_id"][rev_id]
                        elif title.lower().strip() in widget_ratings.get("by_title", {}):
                            score = widget_ratings["by_title"][title.lower().strip()]

                        if not score:
                            score = extract_score(stars_el, action_text)

                        if not score:
                            continue

                        # Extract review text
                        review_text = ""
                        text_el = u.find(id=re.compile(r"^freeTextreview")) or u.find(id=re.compile(r"^freeTextContainerreview"))
                        if not text_el:
                            sib = u.find_next_sibling("tr")
                            while sib and not sib.has_attr("data-timestamp"):
                                text_el = sib.find(id=re.compile(r"^freeTextreview")) or sib.find(id=re.compile(r"^freeTextContainerreview"))
                                if text_el:
                                    break
                                sib = sib.find_next_sibling("tr")
                        if text_el:
                            review_text = text_el.get_text("\n", strip=True)

                        # Extract cover image
                        img_el = u.find("div", class_="updateImage")
                        img_tag = img_el.find("img") if img_el else None
                        image_url = img_tag.get("src", "") if img_tag else ""

                        # Extract timestamp
                        raw_ts = u.get("data-timestamp")
                        review_time = parse_goodreads_date(raw_ts) if raw_ts else ""
                        if not review_time:
                            ts_tag = u.find("a", class_="updatedTimestamp")
                            if ts_tag:
                                review_time = parse_goodreads_date(ts_tag.get_text(strip=True))
                        if not review_time:
                            review_time = datetime.datetime.now().strftime(DATE_FORMAT_OUTPUT)

                        # Extract username
                        user_a = action_el.find("a", href=re.compile(r"/user/show/")) if action_el else None
                        username = user_a.get_text(strip=True) if user_a else default_username

                        review = {
                            "title": title,
                            "score": float(score),
                            "author": author,
                            "url": book_url,
                            "image_url": image_url,
                            "user_url": user["user_url"],
                            "username": username,
                            "user_image_url": user_image_url,
                            "review_text": review_text,
                            "review_url": review_url,
                            "review_time_stamp": review_time,
                        }
                        reviews.append(review)
                        log.debug(f"Review found from: {username} for: {title}")
                        if is_old_review(user, review):
                            log.info(f"Finished checking reviews for user {username}, found old review")
                            break
                    except Exception as error:
                        log.debug(f"Bad entry #{i} for user {user_id}: {error}")
            except Exception as error:
                log.warning(f"Couldn't connect to Goodreads for user {user['id']}: {error}")

        return reviews

    def get_bookwyrm_data(self, users: List[BookUser]) -> List[Review]:
        bookwyrm_reviews = bookwyrm.get_users_reviews(users)
        return bookwyrm_reviews

    def get_reviews(self, users: List[BookUser]) -> List[Review]:
        goodreads_reviews = self.get_rss_data_goodreads(users)
        bookwyrm_reviews = self.get_bookwyrm_data(users)
        return goodreads_reviews + bookwyrm_reviews


# Dependant Variables
rsh = RSSHelper()
