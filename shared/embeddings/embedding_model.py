"""Shared embedding utilities for single and batch text inputs."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def load_embedding_model() -> "SentenceTransformer":
    """Load and cache the sentence-transformers embedding model."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> List[float]:
    """Return a single embedding vector for one text input."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text.strip():
        raise ValueError("text must be non-empty")

    model = load_embedding_model()
    embedding = model.encode(text)
    return embedding.tolist()


def embed_documents(list_of_text: List[str]) -> List[List[float]]:
    """Return embedding vectors for a list of text inputs."""
    if not isinstance(list_of_text, list):
        raise TypeError("list_of_text must be a list of strings")
    if not list_of_text:
        return []
    if any((not isinstance(text, str) or not text.strip()) for text in list_of_text):
        raise ValueError("list_of_text must contain only non-empty strings")

    model = load_embedding_model()
    embeddings = model.encode(list_of_text)
    return embeddings.tolist()
