import discord
import logging
from discord import app_commands
from typing import List
from rss_helper import RSSHelper, Review

DISCORD_TOKEN = 'MTEzMzA0MTYxNzg4MDc2MDQ1MQ.GzeSxH.bWdrgje2rF7EOXhfOLs-hi23nhKAOsz7r9KkQs'
GUILD_ID = 757271564227182602
CHANNEL_ID = 815716163102179350

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
class UpdatesClient(discord.Client):

    def __init__(self):
        super().__init__(intents=intents)
        self.synced = False

    async def on_ready(self):
        logging.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logging.info('------')

        await self.wait_until_ready()
        if not self.synced:  # check if slash commands have been synced
            await tree.sync(guild=discord.Object(
                id=GUILD_ID))  # guild specific: leave blank if global (global registration can take 1-24 hours)
            self.synced = True

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
                                 url=reviews[i]["user_url"], icon_url=reviews[i]["user_image_url"])
                embed.set_thumbnail(url=reviews[i]['image_url'])
                await message.reply(embed=embed, mention_author=True)


# Update Reviews
client = UpdatesClient()
channel = client.get_channel(CHANNEL_ID)

# Add Command
tree = app_commands.CommandTree(client)


@tree.command(guild=discord.Object(id=757271564227182602), name='add', description='Add User')  # guild specific
# slash command
async def add_user(interaction: discord.Interaction, user_id_input: int):
    await interaction.response.send_message(f"¡Añadido!", ephemeral=True)

    with open("data/users.txt", "a") as file:
        if user_id_input not in users:
            file.writelines("\n" + str(user_id_input))
    print(user_id_input)


@tree.command(guild=discord.Object(id=GUILD_ID), name='remove', description='Remove User')  # guild specific
async def remove_user(interaction: discord.Interaction, user_id_input: int):
    await interaction.response.send_message(f"¡Eliminado!", ephemeral=True)

    with open("data/users.txt", "r") as file:
        new_users_list = [line for line in file]

    with open("data/users.txt", "w") as file:
        for user in new_users_list:
            if int(user) != user_id_input:
                file.write(user)


client.run(DISCORD_TOKEN)
