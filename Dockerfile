FROM python:3.12-alpine3.19

ENV BOT_TOKEN=''
ENV DB_URL='sqlite:///travels.db?check_same_thread=False'
ENV HOTELS_API_KEY=''

WORKDIR /travel_bot

COPY . .
RUN pip install -r ./requirements.txt

COPY travel_bot ./travel_bot
