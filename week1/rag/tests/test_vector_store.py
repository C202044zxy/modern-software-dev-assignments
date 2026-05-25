"""Unit tests for rag.vector_store (Part 4)."""

from __future__ import annotations

import math

import pytest

from rag.types import Chunk, EmbeddedChunk
from rag.vector_store import InMemoryVectorStore, cosine_similarity


def _chunk(cid: str, text: str = "") -> Chunk:
    return Chunk(id=cid, doc_id=cid.split(":")[0], chunk_index=0, text=text)


def _embedded(cid: str, vec: dict) -> EmbeddedChunk:
    return EmbeddedChunk(chunk=_chunk(cid), vector=vec)


# ---------- cosine_similarity ----------

class TestCosineSimilarity:
    def test_identical_unit_vectors_score_one(self):
        # Already unit-norm: a single coordinate with magnitude 1.
        a = {"x": 1.0}
        assert cosine_similarity(a, a) == pytest.approx(1.0)

    def test_orthogonal_vectors_score_zero(self):
        assert cosine_similarity({"a": 1.0}, {"b": 1.0}) == pytest.approx(0.0)

    def test_partial_overlap(self):
        # Both vectors L2-normalised by construction so dot product == cosine.
        a = {"x": 1 / math.sqrt(2), "y": 1 / math.sqrt(2)}
        b = {"x": 1.0}
        assert cosine_similarity(a, b) == pytest.approx(1 / math.sqrt(2))

    def test_empty_vector_returns_zero(self):
        assert cosine_similarity({}, {"a": 1.0}) == 0.0
        assert cosine_similarity({"a": 1.0}, {}) == 0.0
        assert cosine_similarity({}, {}) == 0.0

    def test_zero_norm_vector_returns_zero(self):
        # Theoretically a degenerate case; should not divide by zero.
        assert cosine_similarity({"a": 0.0}, {"a": 1.0}) == 0.0

    def test_unnormalised_vectors_still_yield_cosine(self):
        # cos(a, b) is invariant to magnitude.
        a = {"x": 3.0, "y": 4.0}  # ||a|| = 5
        b = {"x": 6.0, "y": 8.0}  # ||b|| = 10, same direction as a
        assert cosine_similarity(a, b) == pytest.approx(1.0)


# ---------- InMemoryVectorStore ----------

class TestInMemoryVectorStore:
    def test_empty_store_has_length_zero(self):
        store = InMemoryVectorStore()
        assert len(store) == 0

    def test_add_increases_length(self):
        store = InMemoryVectorStore()
        store.add([_embedded("a:0", {"x": 1.0})])
        store.add([_embedded("b:0", {"y": 1.0}), _embedded("c:0", {"z": 1.0})])
        assert len(store) == 3

    def test_search_on_empty_store_returns_empty_list(self):
        store = InMemoryVectorStore()
        assert store.search({"x": 1.0}, k=5) == []

    def test_search_returns_top_k_in_descending_order(self):
        store = InMemoryVectorStore()
        store.add([
            _embedded("a:0", {"x": 1.0}),  # cos with query = 1.0
            _embedded("b:0", {"x": 1 / math.sqrt(2), "y": 1 / math.sqrt(2)}),  # ~0.707
            _embedded("c:0", {"y": 1.0}),  # 0
        ])
        results = store.search({"x": 1.0}, k=2)
        assert [r.chunk.id for r in results] == ["a:0", "b:0"]
        assert results[0].score >= results[1].score
        assert results[0].score == pytest.approx(1.0)

    def test_search_k_larger_than_store_returns_all(self):
        store = InMemoryVectorStore()
        store.add([
            _embedded("a:0", {"x": 1.0}),
            _embedded("b:0", {"y": 1.0}),
        ])
        results = store.search({"x": 1.0}, k=10)
        assert len(results) == 2

    def test_search_k_zero_or_negative_returns_empty(self):
        store = InMemoryVectorStore()
        store.add([_embedded("a:0", {"x": 1.0})])
        assert store.search({"x": 1.0}, k=0) == []
        assert store.search({"x": 1.0}, k=-3) == []

    def test_search_does_not_mutate_store(self):
        store = InMemoryVectorStore()
        store.add([_embedded("a:0", {"x": 1.0}), _embedded("b:0", {"y": 1.0})])
        before = len(store)
        store.search({"x": 1.0}, k=1)
        assert len(store) == before
