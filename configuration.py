import logging, os
from dotenv import load_dotenv

load_dotenv()

#.ENVS

if os.getenv("LOGLEVEL") is None:
    LOGLEVEL=logging.INFO
else:
    LOGLEVEL = int(os.getenv("LOGLEVEL"))
    ### LOGLEVELS

    #CRITICAL = 50
    #FATAL = CRITICAL
    #ERROR = 40
    #WARNING = 30
    #WARN = WARNING
    #INFO = 20
    #DEBUG = 10
    #NOTSET = 0
    
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN_ENV")
GUILD_ID = os.getenv("GUILD_ID") # string
CHANNEL_ID = os.getenv("CHANNEL_ID") # int

#.ENVS

DATA_FOLDER = "data"
USERS_JSON_FILE_NAME = "users.json"  
USERS_JSON_FILE_PATH = os.path.join(DATA_FOLDER,USERS_JSON_FILE_NAME)
GOODREADS_SERVICE = 0
BOOKWYRM_SERVICE = 1
BOOKWYRM_INSTANCES = [
    "bookwyrm.social",
    "www.bookwyrm.social",
    "lectura.social",
    "www.lectura.social"
]
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Accept-Language': 'en-US,en;q=0.9'
}

TIME_ZONE = "Europe/Madrid"
DATE_FORMAT_INPUT = "%a, %d %b %Y %H:%M:%S %z"
DATE_FORMAT_OUTPUT = "%Y-%m-%d %H:%M:%S"
