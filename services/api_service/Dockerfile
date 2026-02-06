FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN grep -v "^mysqlclient" /app/requirements.txt > /app/requirements.docker.txt \
    && pip install --no-cache-dir -r /app/requirements.docker.txt

COPY . /app

ENV PYTHONPATH=/app

CMD ["uvicorn", "services.api_service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
