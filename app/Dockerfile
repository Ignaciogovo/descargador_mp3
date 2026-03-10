FROM python:3.9-slim
MAINTAINER IgnacioGovantes "ignaciogovo@gmail.com"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir flask imageio[ffmpeg] yt_dlp

EXPOSE 5000

CMD ["python", "app.py"]

