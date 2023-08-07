FROM python:3.11

ADD main.py .
ADD rss_helper.py .
ADD configuration.py .
ADD classes.py .
ADD bookwyrm.py .
ADD exceptions.py .

RUN pip install -U discord.py
RUN pip install beautifulsoup4
RUN pip install feedparser
RUN pip install requests
RUN pip install rich
RUN pip install pytz
RUN pip install load_dotenv

CMD ["python", "./main.py"]
