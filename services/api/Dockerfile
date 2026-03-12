FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN adduser --disabled-password --no-create-home appuser \
    && mkdir -p /data/uploads \
    && chown -R appuser:appuser /data/uploads
USER appuser

CMD ["celery", "-A", "app.celery_app:celery_app", "worker", "--loglevel=info"]