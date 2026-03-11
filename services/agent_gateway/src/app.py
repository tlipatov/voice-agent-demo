from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.agent_gateway.src.context_builder import load_startup_context


def main() -> int:
    config_dir = os.getenv("TENANT_CONFIG_DIR", "/app/configs/tenants")
    snapshot = load_startup_context(config_dir)
    print(f"Loaded {len(snapshot)} tenant context(s) from {config_dir}")
    for tenant_id, context in snapshot.items():
        print(
            f"- tenant={tenant_id} "
            f"business='{context.business_name}' "
            f"collection='{context.rag_collection}'"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
