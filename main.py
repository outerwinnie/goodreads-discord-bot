import random
import json
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
from configuration import LOGLEVEL
from rss_helper import RSSHelper, Review, DATE_FORMAT_INPUT, DATE_FORMAT_OUTPUT
from rss_helper import get_data_from_users_json, write_to_users_json

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
    
time = datetime.datetime.now

# Importing keys
with open("data/config.txt", "r") as file:
    keys = [line for line in file]

try:
    DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
    GUILD_ID = os.environ['GUILD_ID']
    CHANNEL_ID = int(os.environ['CHANNEL_ID'])
except:
    DISCORD_TOKEN = keys[0]
    GUILD_ID = keys[1]
    CHANNEL_ID = int(keys[2])

USERS_JSON_FILE_PATH = "data/users.json"

logging.debug(f"Este es el ID del canal {CHANNEL_ID}")

# Importing Users
f = open(USERS_JSON_FILE_PATH)
data = json.load(f)
users = [int(user['id']) for user in data["users"]]
log.info(f":books: Starting Discord Bot on ChannelID {CHANNEL_ID} :books:")

# Variables
rsh = RSSHelper()
reviews: List[Review] = rsh.get_rss_data(users)
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
                   
    @tasks.loop(seconds=5)
    async def timer(self, channel):
        global reviews
        log.debug(":stopwatch: Starting timer :stopwatch:")
        log.debug(f"Is sync? {self.synced}")
        if time().minute == 0 or time().minute == 30:
        # if random.randrange(0, 2) == 1: # Uncomment to test
            if not self.msg_sent:
                i: int
                for i in reviews:
                    score_star = ''
                    for x in range(reviews[i]['score']):
                        score_star += '★'

                    embed = discord.Embed(title=reviews[i]['title'] + ' ' + score_star,
                                          description=reviews[i]['author'],
                                          url=reviews[i]['url'])
                    embed.set_author(name=reviews[i]['username'],
                                     url=reviews[i]["user_url"], icon_url=reviews[i]["user_image_url"])
                    embed.set_thumbnail(url=reviews[i]['image_url'])
                    log.debug(f"Review sent for user: {reviews[i]['username']}")
                    await channel.send(embed=embed, mention_author=True)
                self.msg_sent = True
                reviews = {}
                reviews = rsh.get_rss_data(users)
        else:
            self.msg_sent = False


client = UpdatesClient(command_prefix='/', intents=discord.Intents().all())
channel = client.get_channel(CHANNEL_ID)
tree = client.tree
 
# Discord Slash Commands
@tree.command(guild=discord.Object(id=GUILD_ID), name='add', description='Add User')  # guild specific
async def add_user(interaction: discord.Interaction, user_input_url: str):
    await interaction.response.send_message("¡Añadido!", ephemeral=True)
    global users
    global reviews
    user_id = extract_user_id_from_url(user_input_url)
    
    data = get_data_from_users_json()
    users_id = [user["id"] for user in data["users"]]
    if user_id not in users_id:
        data["users"].append({
            "id" : user_id,
            "last_review_ts" : datetime.datetime.now().strftime(DATE_FORMAT_OUTPUT)
        })
        users.append(user_id)
    users = []
    for user in data["users"]:
        users.append(user["id"])
    log.info (f"User {user_input_url} added!")
    log.info (f"New user list: {users}")
            
    write_to_users_json(data)
    

    if user_id == -1:
        await interaction.response.send_message("URL not supported!", ephemeral=True)
        return

@tree.command(guild=discord.Object(id=GUILD_ID), name='remove', description='Remove User')  # guild specific
async def remove_user(interaction: discord.Interaction, user_input_url: str):
    await interaction.response.send_message("¡Eliminado!", ephemeral=True)
    global reviews
    global users
    users = []

    await interaction.response.send_message("¡Eliminado!", ephemeral=True)
    user_id = int(extract_user_id_from_url(user_input_url))
    
    data = get_data_from_users_json()

    for i, user in enumerate(data["users"]):
        if user["id"] == user_id:
            del data["users"][i]
    write_to_users_json(data)
    
    if user_id == -1:
        await interaction.response.send_message("URL not supported!", ephemeral=True)
        return
    
    
    log.info (f"User {user_input_url} removed!")

@tree.command(guild=discord.Object(id=GUILD_ID), name='sync', description='Sync bot (dev)')  # guild specific
async def sync_bot(interaction: discord.Interaction):
    await tree.sync(guild=discord.Object(
                id=GUILD_ID))
    await interaction.response.send_message("Bot synced!", ephemeral=True)
    log.info (f"Bot synced!") 

def extract_user_id_from_url(url) -> int:
    parsed_url = urlparse(url)
    if parsed_url.hostname == "goodreads.com" or "www.goodreads.com":
        if "/author/" in parsed_url.path:
            log.error(f"URL not supported!")
            return -1
        else:
            user_id = parsed_url.path.split('/')[-1].split('-')[0]
            return int(user_id)
    else:
        log.error(f"URL not supported!")
        return -1
  

    write_to_users_json(data)

# Update Reviews
client.run(DISCORD_TOKEN)
