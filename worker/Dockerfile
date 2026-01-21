FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for FFmpeg and MoviePy
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick policy for MoviePy text handling if needed
RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml || true

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["celery", "-A", "tasks", "worker", "--loglevel=info", "--concurrency=4"]
