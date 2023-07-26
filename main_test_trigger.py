import discord
from discord.ext import commands, tasks
import datetime
import logging
from discord import app_commands
from typing import List
from rss_helper import RSSHelper, Review
import random

time = datetime.datetime.now

# Importing keys
with open("data/config.txt", "r") as file:
    keys = [line for line in file]

DISCORD_TOKEN = keys[0]
GUILD_ID = keys[1]
CHANNEL_ID = int(keys[2])

logging.basicConfig(level=logging.INFO)

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

    async def on_ready(self):
        channel = client.get_channel(CHANNEL_ID)  # replace with channel ID that you want to send to
        await self.timer.start(channel)

    @tasks.loop(seconds=5)
    async def timer(self, channel):
        # if time().minute == 00 or time().minute == 30:
        if True:
            if not self.msg_sent:
                await channel.send('Tirando update! (ruben cortes se donde vives)')
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
                    await channel.send(embed=embed, mention_author=True)
                self.msg_sent = True
        else:
            self.msg_sent = False


# Update Reviews
client = UpdatesClient(command_prefix='!', intents=discord.Intents().all())
channel = client.get_channel(CHANNEL_ID)
client.run(DISCORD_TOKEN)
