FROM python:3.9-slim
MAINTAINER IgnacioGovantes "ignaciogovo@gmail.com"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir flask imageio[ffmpeg] yt_dlp python-telegram-bot==20.8 python-dotenv nest-asyncio

RUN chmod +x start.sh

EXPOSE 5000

CMD ["./start.sh"]

