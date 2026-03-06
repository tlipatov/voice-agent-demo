"""Unit tests for deterministic chunk preparation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SERVICE_DIR = PROJECT_ROOT / "services" / "embedding_service"
sys.path.insert(0, str(SERVICE_DIR))

from chunking import chunk_document


class ChunkingTests(unittest.TestCase):
    def test_chunk_document_prefers_paragraph_boundaries(self):
        text = (
            "Alpha paragraph is short.\n\n"
            "Beta paragraph is also short.\n\n"
            "Gamma paragraph is short too."
        )

        records = chunk_document(
            text,
            chunk_size=60,
            overlap=0,
            tenant_id="silver_pine",
            source_file="/tmp/faq.md",
        )

        self.assertEqual([r["metadata"]["chunk_index"] for r in records], [0, 1])
        self.assertEqual(
            [r["text"] for r in records],
            [
                "Alpha paragraph is short.\n\nBeta paragraph is also short.",
                "Gamma paragraph is short too.",
            ],
        )

    def test_chunk_document_sample_output_for_oversized_text(self):
        text = (
            "This paragraph is intentionally oversized so it must be split into smaller chunks. "
            "The split should be deterministic every run."
        )

        records = chunk_document(
            text,
            chunk_size=45,
            overlap=5,
            tenant_id="smith_law",
            source_file="/tmp/brief.txt",
        )

        self.assertEqual(
            [record["text"] for record in records],
            [
                "This paragraph is intentionally oversized so",
                "ed so it must be split into smaller chunks.",
                "unks. The split should be deterministic every run.",
            ],
        )
        self.assertEqual(
            [record["metadata"] for record in records],
            [
                {
                    "tenant_id": "smith_law",
                    "source_file": "/tmp/brief.txt",
                    "chunk_index": 0,
                },
                {
                    "tenant_id": "smith_law",
                    "source_file": "/tmp/brief.txt",
                    "chunk_index": 1,
                },
                {
                    "tenant_id": "smith_law",
                    "source_file": "/tmp/brief.txt",
                    "chunk_index": 2,
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
