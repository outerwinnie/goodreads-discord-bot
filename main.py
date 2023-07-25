import discord, logging
from typing import List

import rss_helper
from rss_helper import RSSHelper, Review

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

class MyClient(discord.Client):
    async def on_ready(self):
        logging.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logging.info('------')

    # Avoid reply to himself
    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        # React to !read with the new book changes
        if message.content.startswith('!read'):
            i: int
            for i in reviews:
                score_star = ''
                for x in range(reviews[i]['score']):
                    score_star += '★'

                embed = discord.Embed(title=reviews[i]['title'] + ' ' + score_star,
                                      description=reviews[i]['author'],
                                      url=reviews[i]['url'])
                embed.set_author(name=reviews[i]['username'],
                                 url=reviews[i]["user_url"])
                embed.set_thumbnail(url=reviews[i]['image_url'])
                await message.reply(embed=embed, mention_author=True)


# Dependant Variables
client = MyClient(intents=intents)
client.run('MTEzMzA0MTYxNzg4MDc2MDQ1MQ.G9-ImJ.q06XFz55-mgZrA95nyQ_ATlyiXFLQZY6Ap8aQM')
channel = client.get_channel(815716163102179350)
