FROM python:3.10-slim
RUN apt update -y --allow-unauthenticated
RUN apt install -y git
RUN apt-get install ffmpeg
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY . /app
COPY .env_prod .env
