FROM python:3.9.13-slim

# Install pkg-config
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y gcc default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/

RUN pip install --upgrade pip \
    && pip install mysqlclient

COPY requirements.txt /app/requirements.txt

WORKDIR app

RUN pip install --no-cache-dir -r requirements.txt

ENV VERSION 0.0.0
COPY . /app
EXPOSE 5051

#CMD ["gunicorn", "application:app", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "--bind", "0.0.0.0:5051"]
#CMD ["sh", "-c", "uvicorn application:app --host 0.0.0.0 --port 5051"]
CMD ["python", "main.py"]