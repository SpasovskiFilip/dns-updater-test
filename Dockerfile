FROM python:3.11-slim

WORKDIR /app

COPY main.py /app

RUN pip install --no-cache-dir requests schedule

CMD ["python", "main.py"]
