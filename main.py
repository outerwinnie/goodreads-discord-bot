import random
import json
import discord
from discord.ext import commands, tasks
import datetime
import logging
import os
from typing import List
from rss_helper import RSSHelper, Review
from rss_helper import get_data_from_users_json, write_to_users_json

time = datetime.datetime.now
logging.basicConfig(level=logging.INFO)

# Importing keys
with open("data/config.txt", "r") as file:
    keys = [line for line in file]

logging.debug("Arranca")

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
            logging.debug("Conectado")
        logging.debug("No Conectado")

    @tasks.loop(seconds=5)
    async def timer(self, channel):
        logging.debug("Starting timer")
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
                    logging.debug(f"Review enviada de {reviews[i]['username']}")
                    await channel.send(embed=embed, mention_author=True)
                self.msg_sent = True
        else:
            self.msg_sent = False


client = UpdatesClient(command_prefix='!', intents=discord.Intents().all())
channel = client.get_channel(CHANNEL_ID)
tree = client.tree


# Discord Slash Commands
@tree.command(guild=discord.Object(id=GUILD_ID), name='add', description='Add User')  # guild specific
async def add_user(interaction: discord.Interaction, user_id_input: int):
    await interaction.response.send_message("¡Añadido!", ephemeral=True)
    global users
    global reviews

    data = get_data_from_users_json()
    users_id = [user["id"] for user in data["users"]]
    for user_id in users_id:
        if user_id not in users:
            data["users"].append({
                "id" : user_id,
                "last_review_ts" : datetime.datetime.now()
            })

    write_to_users_json(data)


@tree.command(guild=discord.Object(id=GUILD_ID), name='remove', description='Remove User')  # guild specific
async def remove_user(interaction: discord.Interaction, user_id_input: int):
    global reviews
    global users
    users = []
    await interaction.response.send_message("¡Eliminado!", ephemeral=True)

    data = get_data_from_users_json()

    for i, user in enumerate(data["users"]):
        if user["id"] == user_id_input:
            del data["users"][i]

    write_to_users_json(data)

# Update Reviews
client.run(DISCORD_TOKEN)
