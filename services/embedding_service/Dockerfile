FROM pytorch/pytorch:2.2.2-cuda12.1-cudnn8-runtime

WORKDIR /app

COPY services/embedding_service/requirements.txt /tmp/requirements.txt
COPY shared/embeddings/pyproject.toml /tmp/shared-embeddings/pyproject.toml
COPY shared/embeddings/README.md /tmp/shared-embeddings/README.md
COPY shared/embeddings/embedding_model.py /tmp/shared-embeddings/embedding_model.py
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN pip install --no-cache-dir /tmp/shared-embeddings

COPY . /app

WORKDIR /app/services/embedding_service
EXPOSE 8010

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8010"]
