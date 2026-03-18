"""gRPC server exposing query functionality for embedding_service."""

from __future__ import annotations

import os
from concurrent import futures
from typing import Any

import grpc

from app import _do_query
from proto import embedding_pb2, embedding_pb2_grpc


def _stringify_metadata(metadata: dict[str, Any] | None) -> dict[str, str]:
    if not metadata:
        return {}
    return {str(key): str(value) for key, value in metadata.items()}


class EmbeddingServiceServicer(embedding_pb2_grpc.EmbeddingServiceServicer):
    def Query(
        self, request: embedding_pb2.QueryRequest, context: grpc.ServicerContext
    ) -> embedding_pb2.QueryResponse:
        tenant_id = request.tenant_id.strip()
        query = request.query.strip()

        if not tenant_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "tenant_id must not be empty")
        if not query:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "query must not be empty")

        if request.n_results == 0:
            n_results = 5
        else:
            n_results = max(1, min(request.n_results, 50))

        result = _do_query(tenant_id, query, n_results)
        matches: list[embedding_pb2.Match] = []
        for item in result.get("matches", []):
            distance = item.get("distance")
            matches.append(
                embedding_pb2.Match(
                    document=item.get("document", ""),
                    metadata=_stringify_metadata(item.get("metadata")),
                    distance=float(distance) if distance is not None else 0.0,
                )
            )

        return embedding_pb2.QueryResponse(
            tenant_id=result.get("tenant_id", tenant_id),
            query=result.get("query", query),
            matches=matches,
        )


def serve(port: int) -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    embedding_pb2_grpc.add_EmbeddingServiceServicer_to_server(EmbeddingServiceServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve(int(os.getenv("GRPC_PORT", "50051")))
