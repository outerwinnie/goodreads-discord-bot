from typing import TypedDict

class Review(TypedDict):
    title: str
    score: int
    author: str
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
