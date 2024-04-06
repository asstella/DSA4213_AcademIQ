FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev

RUN pip install -r requirements.txt

CMD ["wave", "run", "--no-reload", "app.py"]
