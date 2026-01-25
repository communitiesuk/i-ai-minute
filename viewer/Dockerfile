FROM python:3.11-slim

WORKDIR /app

COPY viewer/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY viewer /app/viewer

ENV PORT=8080
ENV RUNS_ROOT=/data/runs

RUN mkdir -p /data/runs

VOLUME ["/data/runs"]

EXPOSE 8080

CMD ["python", "/app/viewer/app.py"]
