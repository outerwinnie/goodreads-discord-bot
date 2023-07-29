import random
import discord
from discord.ext import commands, tasks
import datetime
import logging
import os
from urllib.parse import urlparse
from rich.logging import RichHandler
from rich.traceback import install
from typing import List
from configuration import LOGLEVEL
from rss_helper import RSSHelper, Review

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

log.info(f":books: Starting Discord Bot on ChannelID {CHANNEL_ID} :books:")

# Importing Users
with open("data/users.txt", "r") as file:
    users = [int(line) for line in file]

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
        await self.timer.start(channel)
        if not self.synced:  # check if slash commands have been synced
            await tree.sync(guild=discord.Object(
                id=GUILD_ID))  # guild specific: leave blank if global (global registration can take 1-24 hours)
            self.synced = True
            
    @tasks.loop(seconds=5)
    async def timer(self, channel):
        log.debug(":stopwatch: Starting timer :stopwatch:")
        # if time().minute == 0 or time().minute == 30:
        if random.randrange(0, 2) == 1:
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
        else:
            self.msg_sent = False


client = UpdatesClient(command_prefix='!', intents=discord.Intents().all())
channel = client.get_channel(CHANNEL_ID)
tree = client.tree

    
# Discord Slash Commands
@tree.command(guild=discord.Object(id=GUILD_ID), name='add', description='Add User')  # guild specific
async def add_user(interaction: discord.Interaction, user_input_url: str):
    await interaction.response.send_message("¡Añadido!", ephemeral=True)
    global users
    global reviews

    user_id = extract_user_id_from_url(user_input_url)
        
    with open("data/users.txt", "a") as file:
        if user_id not in users:
            file.writelines("\n" + str(user_id))

    with open("data/users.txt", "r") as file:
        users = [int(line) for line in file]
        reviews = rsh.get_rss_data(users)


@tree.command(guild=discord.Object(id=GUILD_ID), name='remove', description='Remove User')  # guild specific
async def remove_user(interaction: discord.Interaction, user_id_input: int):
    global reviews
    global users
    users = []
    await interaction.response.send_message("¡Eliminado!", ephemeral=True)

    with open("data/users.txt", "r") as file:
        old_users_list = [int(line) for line in file]

    with open("data/users.txt", "w") as file:
        for user in old_users_list:
            if user != user_id_input:
                users.append(user)
                file.write(str(user))
        print(users)
        reviews = rsh.get_rss_data(users)

def extract_user_id_from_url(url):
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split('/')

    for part in path_parts:
        if '.' in part or '-' in part:
            user_id = part.split('.')[0].split('-')[0]
            return user_id

    return None  


# Update Reviews
client.run(DISCORD_TOKEN)
