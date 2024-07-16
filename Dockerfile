FROM python:3.10-slim
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y git
RUN apt-get update && \
    echo "deb http://httpredir.debian.org/debian sid buster main contrib non-free" >>/etc/apt/sources.list && \
    apt-get update && \
    apt-get -t sid install -y --no-install-recommends ffmpeg=7:6.1.1-5
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY . /app
COPY .env_prod .env
RUN chmod +x db-init-scripts/create-multiple-dbs.sh
