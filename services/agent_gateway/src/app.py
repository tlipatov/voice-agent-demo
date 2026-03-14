from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.agent_gateway.src.context_builder import load_startup_context


def _verify_embedding_service(base_url: str, timeout_seconds: float = 5.0) -> None:
    health_url = f"{base_url.rstrip('/')}/healthz"
    try:
        with urlopen(health_url, timeout=timeout_seconds) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"Embedding service health check failed at {health_url}: HTTP {response.status}"
                )
    except URLError as exc:
        raise RuntimeError(
            f"Embedding service is unreachable at {health_url}: {exc}"
        ) from exc


def main() -> int:
    config_dir = os.getenv("TENANT_CONFIG_DIR", "/app/configs/tenants")
    embedding_service_url = os.getenv("EMBEDDING_SERVICE_URL")
    if embedding_service_url:
        _verify_embedding_service(embedding_service_url)
    snapshot = load_startup_context(config_dir)
    print(f"Loaded {len(snapshot)} tenant context(s) from {config_dir}")
    for tenant_id, context in snapshot.items():
        print(
            f"- tenant={tenant_id} "
            f"business='{context.business_name}' "
            f"collection='{context.rag_collection}'"
        )
    if embedding_service_url:
        print(f"Embedding service reachable at {embedding_service_url.rstrip('/')}/healthz")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
