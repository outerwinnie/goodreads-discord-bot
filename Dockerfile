FROM python:3.11

ADD old_main.py .
ADD rss_helper.py .
ADD scrapper.py .
COPY data /data/

RUN pip install -U discord.py
RUN pip install beautifulsoup4
RUN pip install feedparser
RUN pip install requests

CMD ["python", "./main.py"]
