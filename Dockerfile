FROM ubuntu:24.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY web.py .
COPY start_server.sh .
RUN chmod +x start_server.sh

ENV DOWNLOAD_FOLDER=/data

EXPOSE 8080

CMD ["python3", "web.py"]
