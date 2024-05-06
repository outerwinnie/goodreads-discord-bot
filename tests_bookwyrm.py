import feedparser
import logging
import requests
from typing import List
import datetime
from bs4 import BeautifulSoup, NavigableString
from rich.console import Console
from rich.logging import RichHandler
from urllib.parse import urlparse, urljoin
import re
from classes import Review, BookUser

FORMAT = "%(message)s"
logging.basicConfig(level="DEBUG",
                    format=FORMAT,
                    datefmt="[%X]",
                    handlers=[RichHandler(markup=True, rich_tracebacks=True)])
log = logging.getLogger("rich")
console = Console()

profile_url = 'https://bookwyrm.social/user/potajito'
log.debug(f"Trying for https://www.goodreads.com/user/updates_rss/34998873")

def append_to_url(url: str, path_to_append: str) -> str:
    # Ensure path_to_append starts with a slash and url doesn't have one
    if not url.endswith('/'):
        url = f"{url}/"
    if path_to_append.startswith('/'):
        path_to_append = path_to_append[1:]
        return url + path_to_append


def parse_user_profile (profile_url: str) -> List[Review]:
    reviews: List[Review] = []
    try:
        profile_url_domain = urlparse(profile_url).hostname
        profile_url_scheme = urlparse(profile_url).scheme
        reviews_url = append_to_url(profile_url,'/reviews-comments')
        soup = BeautifulSoup(requests.get(reviews_url).text,"html.parser")
        
        user_image_url = soup.find('img', class_=re.compile(r'avatar image*')).get('src')
         
        header_entries: List[NavigableString] = soup.find_all('div', class_='media-content')
        #box_entries = soup.find_all('section', class_='card-content')

        for entry in header_entries:
            if ' rated ' in entry.text:
                username = entry.find('span', itemprop='name').text.strip()
                book_name = find_book_title(entry)
                time_elapsed_str = find_time_elapsed(entry)
                review_time_stamp = convert_elapsed_to_timestamp(time_elapsed_str)
                score_in_stars = entry.select_one('.stars .is-sr-only').text.strip()
                score = int(re.findall(r'\d+', score_in_stars)[0])

                section_tag = entry.find_next('section', class_='card-content')
                author = find_book_author(section_tag)
                section_a_tags = section_tag.find_all('a')
                section_img_tag = section_tag.find("img", class_="book-cover")
                try:
                    image_url = section_img_tag.get('src')
                except Exception:
                    image_url = 'https://cover2coverbookdesign.com/site/wp-content/uploads/2019/03/geometric1.jpg'
                
                for a_tag in section_a_tags:
                    if "/book/" in a_tag.get('href'):
                        book_url = f"{profile_url_scheme}://{profile_url_domain}{a_tag.get('href')}" 
                        
                        # log.debug(book_url)
                        break
                reviews.append(fill_review(book_name, score, author,
                                           book_url, image_url, profile_url,
                                           username, user_image_url, review_time_stamp))
                clean_string = f"{username} rated {book_name} by {author}: {score}"
                log.info(clean_string)
            if ' reviewed ' in entry.text:
                username = entry.find('span', itemprop='name').text.strip()
                book_name = find_book_title(entry)
                time_elapsed_str = find_time_elapsed(entry)
                review_time_stamp = convert_elapsed_to_timestamp(time_elapsed_str)
                author = find_book_author(entry)

                section_tag = entry.find_next('section', class_='card-content')
                score_in_stars = section_tag.find('span', class_='is-sr-only').text.strip()
                score = int(re.findall(r'\d+', score_in_stars)[0])
                
                section_a_tags = section_tag.find_all('a')
                section_img_tag = section_tag.find("img", class_="book-cover")
                
                # Extract review text
                
                
                try:
                    image_url = section_img_tag.get('src')
                except Exception:
                    image_url = 'https://cover2coverbookdesign.com/site/wp-content/uploads/2019/03/geometric1.jpg'
                
                for a_tag in section_a_tags:
                    if "/book/" in a_tag.get('href'):
                        book_url = f"{profile_url_scheme}://{profile_url_domain}{a_tag.get('href')}" 
                        
                        # log.debug(book_url)
                        break
                reviews.append(fill_review(book_name, score, author,
                            book_url, image_url, profile_url,
                            username, user_image_url, review_time_stamp))
                clean_string = f"{username} reviewed {book_name} by {author}: {score}"
                log.info(clean_string)
        log.info(f"Found {len(reviews)} reviews")
        #log.debug(pprint(reviews))
        return reviews
    
                        
    except Exception as error:
        print('Could not parse:', reviews_url)
        console.print_exception()
        return []