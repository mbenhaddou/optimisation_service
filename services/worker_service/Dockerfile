FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN grep -v "^mysqlclient" /app/requirements.txt > /app/requirements.docker.txt \
    && pip install --no-cache-dir -r /app/requirements.docker.txt

COPY . /app

ENV PYTHONPATH=/app

CMD ["celery", "-A", "services.worker_service.app.celery_app.celery_app", "worker", "--loglevel=info"]
