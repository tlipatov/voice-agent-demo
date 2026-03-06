FROM python:3.11-slim

WORKDIR /app

COPY services/agent_gateway/requirements.txt /tmp/requirements.txt
COPY shared/embeddings /tmp/shared-embeddings
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN pip install --no-cache-dir /tmp/shared-embeddings

COPY . /app

CMD ["python", "-c", "print('agent_gateway image ready')"]
