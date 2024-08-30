# 📚 Goodreads & BookWyrm Discord Bot

A Discord bot that tracks and shares new reviews from both Goodreads and BookWyrm users directly in your server. Keep your community updated with the latest book reviews!

## ✨ Features

- 🔄 **Automated Review Updates**: Periodically checks for new reviews from tracked Goodreads and BookWyrm users and shares them in your Discord channel.
- ➕ **Add/Remove Users**: Use slash commands to track or untrack users from Goodreads or BookWyrm.
- 📊 **Interactive Embeds**: Displays reviews in rich embed format with links, ratings, and user info.

## 🐳 Docker Setup

1. **Docker Compose**:
   
   Create a `docker-compose.yml` file with the following content:

   ```yaml
   version: "2.1"
   services:
     goodreads-discord-bot:
       image: ghcr.io/outerwinnie/goodreads-discord-bot:latest
       container_name: goodreads-discord-bot
       environment:
         - TZ=Europe/Madrid
         - CHANNEL_ID=
         - GUILD_ID=
         - DISCORD_TOKEN=
         - LOGLEVEL={20-10}
         - PGID=1000
         - PUID=1000
       restart: unless-stopped
   ```

2. **Run the bot**:

   ```bash
   docker-compose up -d
   ```

## 🛠️ Usage

### Commands

- `/add`: Track a new Goodreads or BookWyrm user.
- `/remove`: Untrack a user.
- `/review_check`: Manually trigger a review check.
- `/sync`: Sync the bot commands (for developers).


