# Goodreads-Bot

##  TODO
- Ajustar las fotos de perfil

docker-compose.yml:

```
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
      - PGID=1000
      - PUID=1000
    restart: unless-stopped
```
