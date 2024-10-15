
FROM python:3.12-alpine
LABEL APP_LONG="SQS S3 Notifier for Linode Object Storage"
LABEL MAINTAINER="vonEmpalmeOlmos <daniel.m@stormclouds.me>"
LABEL VENDOR="An EdgeTribe Project"

WORKDIR /usr/src/app

RUN apk update && \
    apk add bash


COPY script.py .
RUN chmod +x script.py
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


ENTRYPOINT ["python", "-u", "script.py"]
