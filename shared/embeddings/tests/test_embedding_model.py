"""Tests for shared embedding utilities."""

from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import patch

import embedding_model


class FakeEmbedding:
    """Simple stand-in for numpy arrays returned by encode()."""

    def __init__(self, value):
        self._value = value

    def tolist(self):
        return self._value


class FakeModel:
    """Model stub that returns deterministic embeddings."""

    def encode(self, text_or_texts):
        if isinstance(text_or_texts, str):
            return FakeEmbedding([0.1, 0.2, 0.3])
        return FakeEmbedding([[0.1, 0.2, 0.3] for _ in text_or_texts])


class FakeSentenceTransformer(FakeModel):
    init_calls = 0

    def __init__(self, model_name):
        self.model_name = model_name
        FakeSentenceTransformer.init_calls += 1


class EmbeddingModelTests(unittest.TestCase):
    def setUp(self):
        embedding_model.load_embedding_model.cache_clear()
        FakeSentenceTransformer.init_calls = 0

    def test_load_embedding_model_is_cached(self):
        fake_module = types.SimpleNamespace(SentenceTransformer=FakeSentenceTransformer)
        with patch.dict(sys.modules, {"sentence_transformers": fake_module}):
            first = embedding_model.load_embedding_model()
            second = embedding_model.load_embedding_model()

        self.assertIs(first, second)
        self.assertEqual(FakeSentenceTransformer.init_calls, 1)
        self.assertEqual(first.model_name, embedding_model.MODEL_NAME)

    @patch("embedding_model.load_embedding_model", return_value=FakeModel())
    def test_embed_text_returns_non_empty_vector(self, _):
        embedding = embedding_model.embed_text("Hello world")

        self.assertIsInstance(embedding, list)
        self.assertGreater(len(embedding), 0)

    @patch("embedding_model.load_embedding_model", return_value=FakeModel())
    def test_embed_documents_returns_vectors_for_each_input(self, _):
        embeddings = embedding_model.embed_documents(["doc one", "doc two"])

        self.assertEqual(len(embeddings), 2)
        self.assertTrue(all(isinstance(vector, list) and len(vector) > 0 for vector in embeddings))


if __name__ == "__main__":
    unittest.main()
