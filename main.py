from pprint import pprint
from typing import List
import discord, logging
from rss_helper import RSSHelper, Book
logging.basicConfig(level=logging.INFO)

rss_feed = 'https://www.goodreads.com/user/updates_rss/35497141'

rsh = RSSHelper()
books: List[Book] = rsh.get_rss_data(rss_feed)


class MyClient(discord.Client):
    async def on_ready(self):
        logging.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logging.info('------')

    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return

        if message.content.startswith('!read'):
            i: int
            for i in books:
                score_star = ''
                for x in range(books[i]['score']):
                    score_star += '★'

                embed = discord.Embed(title=books[i]['title'] + ' ' + score_star,
                                      description=books[i]['author'],
                                      url=books[i]['url'])
                embed.set_author(name=books[i]['username'],
                                 url=books[i]["user_url"])
                embed.set_thumbnail(url=books[i]['image_url'])
                await message.reply(embed=embed, mention_author=True)


intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run('MTEzMzA0MTYxNzg4MDc2MDQ1MQ.G9-ImJ.q06XFz55-mgZrA95nyQ_ATlyiXFLQZY6Ap8aQM')
channel = client.get_channel(815716163102179350)
