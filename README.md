# Goodreads-Bot

##  MAYBE
- Ajustar las fotos de perfil
- Añadir la review completa
- Integracion de la creacion de imagenes de Docker con Github CI


## BUGS
-  Forzar el checkeo de reviews sin usuarios añadidos peta el bot

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
    mem_limit: 50m
    cpus: 0.1
    restart: unless-stoppe
```
