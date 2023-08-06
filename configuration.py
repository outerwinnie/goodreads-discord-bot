import logging, os
from dotenv import load_dotenv

load_dotenv()

LOGLEVEL = logging.INFO
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN_ENV")
GUILD_ID = "757271564227182602" # string
CHANNEL_ID = 815716163102179350 # int
DATA_FOLDER = "data"
USERS_JSON_FILE_NAME = "users.json"  
USERS_JSON_FILE_PATH = os.path.join(DATA_FOLDER,USERS_JSON_FILE_NAME)
GOODREADS_SERVICE = 0
BOOKWYRM_SERVICE = 1

TIME_ZONE = "Europe/Madrid"
DATE_FORMAT_INPUT = "%a, %d %b %Y %H:%M:%S %z"
DATE_FORMAT_OUTPUT = "%Y-%m-%d %H:%M:%S"
