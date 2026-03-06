"""Deterministic document chunking for embedding-service ingestion."""

from __future__ import annotations

import hashlib
import re
from typing import Any


def _split_by_words(text: str, chunk_size: int) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    current = words[0]

    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        chunks.append(current)
        current = word

    chunks.append(current)

    normalized: list[str] = []
    for chunk in chunks:
        if len(chunk) <= chunk_size:
            normalized.append(chunk)
            continue
        for start in range(0, len(chunk), chunk_size):
            normalized.append(chunk[start : start + chunk_size])
    return normalized


def _split_oversized_paragraph(paragraph: str, chunk_size: int) -> list[str]:
    paragraph = paragraph.strip()
    if not paragraph:
        return []
    if len(paragraph) <= chunk_size:
        return [paragraph]

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", paragraph) if s.strip()]
    if len(sentences) <= 1:
        return _split_by_words(paragraph, chunk_size)

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > chunk_size:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_by_words(sentence, chunk_size))
            continue

        candidate = sentence if not current else f"{current} {sentence}"
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        chunks.append(current)
        current = sentence

    if current:
        chunks.append(current)

    return chunks


def _build_base_chunks(text: str, chunk_size: int) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", cleaned) if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        paragraph_parts = _split_oversized_paragraph(paragraph, chunk_size)
        for part in paragraph_parts:
            candidate = part if not current else f"{current}\n\n{part}"
            if len(candidate) <= chunk_size:
                current = candidate
                continue

            if current:
                chunks.append(current)
            current = part

    if current:
        chunks.append(current)

    return chunks


def _apply_overlap(chunks: list[str], overlap: int) -> list[str]:
    if overlap <= 0:
        return chunks

    overlapped: list[str] = []
    previous_tail = ""
    for chunk in chunks:
        chunk_text = f"{previous_tail} {chunk}".strip() if previous_tail else chunk
        overlapped.append(chunk_text)
        previous_tail = chunk[-overlap:] if len(chunk) > overlap else chunk
    return overlapped


def chunk_document(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
    *,
    tenant_id: str = "",
    source_file: str = "",
) -> list[dict[str, Any]]:
    """Chunk a document into deterministic records with stable metadata."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")
    if overlap < 0:
        raise ValueError("overlap must be non-negative.")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    base_chunks = _build_base_chunks(text, chunk_size)
    final_chunks = _apply_overlap(base_chunks, overlap)

    records: list[dict[str, Any]] = []
    for chunk_index, chunk_text in enumerate(final_chunks):
        digest = hashlib.sha1(
            f"{tenant_id}:{source_file}:{chunk_index}:{chunk_text}".encode("utf-8")
        ).hexdigest()[:16]
        records.append(
            {
                "chunk_id": digest,
                "text": chunk_text,
                "metadata": {
                    "tenant_id": tenant_id,
                    "source_file": source_file,
                    "chunk_index": chunk_index,
                },
            }
        )
    return records
