FROM python:3.11

ADD main.py .
ADD rss_helper.py .
COPY data /data/

RUN pip install -U discord.py
RUN pip install beautifulsoup4
RUN pip install feedparser
RUN pip install requests

CMD ["python", "./main.py"]
