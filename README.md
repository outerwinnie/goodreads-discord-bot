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
    image: goodreads-discord-bot:latest	
    container_name: goodreads-discord-bot
    environment:
      - TZ=Europe/Madrid
      - DISCORD_TOKEN_ENV=
    mem_limit: 128m
    cpus: 0.1
    restart: unless-stoppe
```
