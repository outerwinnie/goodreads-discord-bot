import logging, os
from dotenv import load_dotenv

load_dotenv()

LOGLEVEL = logging.DEBUG
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN_ENV")
GUILD_ID = "757271564227182602" # string
CHANNEL_ID = 815716163102179350 # int
DATA_FOLDER = "data"
USERS_JSON_FILE_NAME = "users.json"  
USERS_JSON_FILE_PATH = os.path.join(DATA_FOLDER,USERS_JSON_FILE_NAME)
