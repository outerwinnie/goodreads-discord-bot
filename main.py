import random
import json
from json import JSONDecodeError
import discord
from discord.ext import commands, tasks
import datetime
import logging
import os
from urllib.parse import urlparse
from rich.logging import RichHandler
from rich import print
from rich.traceback import install
from typing import List
import configuration
from configuration import LOGLEVEL, DATA_FOLDER, USERS_JSON_FILE_PATH, GOODREADS_SERVICE, BOOKWYRM_SERVICE
from classes import Review, BookUser, check_new_reviews, get_stars, read_json_data
from classes import read_json_data, write_to_users_json
from rss_helper import RSSHelper
from rss_helper import DATE_FORMAT_INPUT, DATE_FORMAT_OUTPUT


FORMAT = "%(message)s"
logging.basicConfig(level=LOGLEVEL,
                    format=FORMAT,
                    datefmt="[%X]",
                    handlers=[RichHandler(markup=True, rich_tracebacks=True)])
log = logging.getLogger("rich")

# Show Tracebacks if DEBUG
if logging.root.level == logging.DEBUG:
    install(show_locals=True)
else:
    install(show_locals=False)

def init_file_structure (users_json_path: str):
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
        with open(users_json_path, "w") as f:
            log.info("Data folder doesn't exists, creating folder and .json file...")
            pass # Creates empty file if none exist
    elif os.path.exists(DATA_FOLDER) and not os.path.exists(users_json_path):
        with open(users_json_path, "w") as f:
            log.info("Data folder exists, but .json file doesn't exists, creating...")
            pass
        
        
init_file_structure(USERS_JSON_FILE_PATH)

# Importing keys
try:
    DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
    GUILD_ID = os.environ['GUILD_ID']
    CHANNEL_ID = int(os.environ['CHANNEL_ID'])
except:
    DISCORD_TOKEN = configuration.DISCORD_TOKEN
    GUILD_ID = configuration.GUILD_ID
    CHANNEL_ID = configuration.CHANNEL_ID

logging.debug(f"Channel ID: {CHANNEL_ID}")

# Importing Users
try:    
    f = open(USERS_JSON_FILE_PATH)
    data = json.load(f)
    users: List[BookUser] = [user for user in data["users"]]
    log.info(f":books: Starting Discord Bot on ChannelID {CHANNEL_ID} :books:")
except JSONDecodeError:
    users: List[BookUser] = []
    log.warning("Json file is empty")
    log.info(f":books: Starting Discord Bot on ChannelID {CHANNEL_ID} :books:")
    

# Variables
rsh = RSSHelper()
#reviews: List[Review] = rsh.get_reviews(users)
intents = discord.Intents.default()
intents.message_content = True

# Connecting with Discord
class UpdatesClient(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg_sent = False
        self.synced = False

    async def on_ready(self):
        channel = client.get_channel(CHANNEL_ID)  # replace with channel ID that you want to send to
        if not self.synced:  # check if slash commands have been synced
            await tree.sync(guild=discord.Object(
                id=GUILD_ID))  # guild specific: leave blank if global (global registration can take 1-24 hours)
            self.synced = True
            log.info(f"Successfully logged and synced in as {client.user}")
        await self.timer.start(channel)
                   
    # @tasks.loop(seconds=5) # For debug purposes
    @tasks.loop(minutes=5)
    async def timer(self, channel, force_check=False):
        global reviews
        rand_debug = random.randrange(0,4)
        log.debug(f":stopwatch: Starting timer... Random:{rand_debug} :stopwatch:")
        log.debug(f"Is sync? {self.synced}")
        current_time = datetime.datetime.now()
        #if rand_debug == 1: # Uncomment to test
        if (current_time.minute == 0 or current_time.minute == 15 
            or current_time.minute == 30 or current_time.minute == 45
            or force_check):
            log.info (f":books: Starting review check... :books:")
            if not self.msg_sent or force_check:
                try:
                    data = read_json_data (USERS_JSON_FILE_PATH)
                    reviews = rsh.get_reviews(data["users"])
                    new_reviews = check_new_reviews(reviews, data)
                    for review in new_reviews:
                        score_star = get_stars(review['score'])
                        
                        embed = discord.Embed(title=review['title'] + ' ' + score_star,
                                            description=review['author'],
                                            url=review['url'])
                        embed.set_author(name=review['username'],
                                        url=review["user_url"], icon_url=review["user_image_url"])
                        embed.set_thumbnail(url=review['image_url'])
                        log.debug(f"Review sent for user: {review['username']}")
                        await channel.send(embed=embed, mention_author=True)
                    self.msg_sent = True
                    reviews = []
                    log.info (f":books: Review check finished. Sent {len(new_reviews)} new reviews :books:")
                except KeyError:
                    log.warning("Json file is empty")
                #reviews = rsh.get_reviews(users)
        else:
            self.msg_sent = False


client = UpdatesClient(command_prefix='/', intents=discord.Intents().all())
channel = client.get_channel(CHANNEL_ID)
tree = client.tree
 
# Discord Slash Commands
@tree.command(guild=discord.Object(id=GUILD_ID), name='add', description='Add BookUser')  # guild specific
async def add_user(interaction: discord.Interaction, user_input_url: str):
    await interaction.response.send_message("¡Añadido!", ephemeral=True)
    global users
    global reviews
    users_id: List[str] = []
    extracted_user = extract_user_from_url(user_input_url)
    
    data = read_json_data()
    current_user: BookUser = {
                "service" : extracted_user["service"],
                "id" : extracted_user["id"],
                "user_url" : extracted_user["user_url"],
                "last_review_ts" : datetime.datetime.now().strftime(DATE_FORMAT_OUTPUT)
                }
    if data:
        users_id = [user["id"] for user in data["users"]]
        if extracted_user["id"] not in users_id:
            
            data["users"].append(current_user)
            users.append(current_user)
            
    else: # For first user
       data.setdefault("users",[])
       data["users"].append(current_user)

       users.append(current_user)
    
    write_to_users_json(data)
    # reviews = rsh.get_reviews(users) # Need to fix to just 
                                # update reviews with this user reviews
    
    log.info (f"BookUser {user_input_url} added!")
    log.info (f"New user list: {users}")

    if not extracted_user:
        await interaction.response.send_message("URL not supported!", ephemeral=True)
        return

@tree.command(guild=discord.Object(id=GUILD_ID), name='remove', description='Remove User')  # guild specific
async def remove_user(interaction: discord.Interaction, user_input_url: str):
    await interaction.response.send_message("¡Eliminado!", ephemeral=True)
    global reviews
    global users

    extracted_user = extract_user_from_url(user_input_url)
    
    data = read_json_data()

    for i, user in enumerate(data["users"]):
        if user["id"] == extracted_user["id"] and user["service"] == extracted_user["service"]:
            del data["users"][i]
    write_to_users_json(data)
    users = data["users"]
    
    if not extracted_user:
        await interaction.response.send_message("URL not supported!", ephemeral=True)
        return
    
    log.info (f"BookUser {user_input_url} removed!")

@tree.command(guild=discord.Object(id=GUILD_ID), name='review_check', description='Trigger Review Check')  # guild specific
async def trigger_review_check(interaction: discord.Interaction):
    await interaction.response.send_message("Triggering review check...", ephemeral=True)
    await client.timer(client.get_channel(CHANNEL_ID), True)


@tree.command(guild=discord.Object(id=GUILD_ID), name='sync', description='Sync bot (dev)')  # guild specific
async def sync_bot(interaction: discord.Interaction):
    await tree.sync(guild=discord.Object(
                id=GUILD_ID))
    await interaction.response.send_message("Bot synced!", ephemeral=True)
    log.info (f"Bot synced!") 

def extract_user_from_url(url) -> dict:
    parsed_url = urlparse(url)
    if parsed_url.hostname == "goodreads.com" or parsed_url.hostname == "www.goodreads.com":
        if "/author/" in parsed_url.path:
            log.error(f"URL not supported!")
            return {}
        else:
            user_id = parsed_url.path.split('/')[-1].split('-')[0]
            user = {
                "service": GOODREADS_SERVICE,
                "id": user_id,
                "user_url" : f"{parsed_url.scheme}://{parsed_url.hostname}{parsed_url.path}"
            }
            return user
        
    if parsed_url.hostname == "bookwyrm.social" or parsed_url.hostname == "www.bookwyrm.social":
        if "/author/" in parsed_url.path:
            log.error(f"URL not supported!")
            return {}
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
        return {}
  

    write_to_users_json(data)


# Update Reviews
client.run(DISCORD_TOKEN)
