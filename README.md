# Goodreads-Bot

##  MAYBE
- Ajustar las fotos de perfil
- Añadir la review completa
- Integracion de la creacion de imagenes de Docker con Github CI


docker-compose.yml:

```
version: "2.1"
services:
  goodreads-discord-bot:
    image: 	goodreads-discord-bot:latest	
    container_name: goodreads-discord-bot
    environment:
      - TZ=Europe/Madrid
      - DISCORD_TOKEN=MTEzMzA0MTYxNzg4MDc2MDQ1MQ.G46Y9I.iD37GxaS_K7MXIp20qvVP5FRJggSBnrZmCs-Tk
      - GUILD_ID=757271564227182602
      - CHANNEL_ID=815716163102179350
    mem_limit: 50m
    cpus: 0.1
    restart: unless-stoppe
```
