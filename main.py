import random
import discord
from discord.ext import commands, tasks
import datetime
import logging
from typing import List
from rss_helper import RSSHelper, Review

time = datetime.datetime.now
logging.basicConfig(level=logging.INFO)

# Importing keys
with open("data/config.txt", "r") as file:
    keys = [line for line in file]

logging.debug("Arranca")
DISCORD_TOKEN = keys[0]
GUILD_ID = keys[1]
CHANNEL_ID = int(keys[2])

logging.debug(f"Este es el ID del canal {CHANNEL_ID}")



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

    with open("data/users.txt", "a") as file:
        if user_id_input not in users:
            file.writelines("\n" + str(user_id_input))

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


# Update Reviews
client.run(DISCORD_TOKEN)
