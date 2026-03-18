FROM pytorch/pytorch:2.2.2-cuda12.1-cudnn8-runtime

WORKDIR /app

COPY services/embedding_service/requirements.txt /tmp/requirements.txt
COPY shared/embeddings/pyproject.toml /tmp/shared-embeddings/pyproject.toml
COPY shared/embeddings/README.md /tmp/shared-embeddings/README.md
COPY shared/embeddings/embedding_model.py /tmp/shared-embeddings/embedding_model.py
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN pip install --no-cache-dir /tmp/shared-embeddings

COPY services/embedding_service/proto /app/services/embedding_service/proto
RUN python -m grpc_tools.protoc \
    -I /app/services/embedding_service/proto \
    --python_out=/app/services/embedding_service/proto \
    --grpc_python_out=/app/services/embedding_service/proto \
    /app/services/embedding_service/proto/embedding.proto

COPY . /app

WORKDIR /app/services/embedding_service
COPY services/embedding_service/entrypoint.sh /app/services/embedding_service/entrypoint.sh
RUN chmod +x /app/services/embedding_service/entrypoint.sh
EXPOSE 8010
EXPOSE 50051

CMD ["/app/services/embedding_service/entrypoint.sh"]
