FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (ffmpeg is required for music bot)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

# Gunicorn runs the 'server' object from 'main.py'
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "main:server"]
