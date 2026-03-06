FROM python:3.11

WORKDIR /app

RUN pip install --no-cache-dir chromadb

EXPOSE 8001

CMD ["chroma", "run", "--host", "0.0.0.0", "--port", "8001", "--path", "/data"]
