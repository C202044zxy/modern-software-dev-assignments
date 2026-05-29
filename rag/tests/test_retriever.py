"""Unit tests for rag.retriever (Part 5)."""

from __future__ import annotations

from rag.rag.chunking import chunk_document
from rag.rag.embeddings import TfIdfEmbedder
from rag.rag.retriever import Retriever
from rag.rag.vector_store import InMemoryVectorStore


class TestRetrieverIndex:
    def test_index_populates_store(self, mini_corpus):
        embedder = TfIdfEmbedder()
        embedder.fit([d.text for d in mini_corpus])
        store = InMemoryVectorStore()
        retriever = Retriever(embedder=embedder, store=store)

        chunks = []
        for doc in mini_corpus:
            chunks.extend(chunk_document(doc, chunk_size=20, overlap=5))
        retriever.index(chunks)

        assert len(store) == len(chunks)

    def test_index_empty_chunks_leaves_store_empty(self):
        embedder = TfIdfEmbedder()
        embedder.fit(["something to fit on"])
        store = InMemoryVectorStore()
        retriever = Retriever(embedder=embedder, store=store)
        retriever.index([])
        assert len(store) == 0


class TestRetrieverRetrieve:
    def _build(self, mini_corpus):
        retriever = Retriever(embedder=TfIdfEmbedder())
        chunks = []
        for doc in mini_corpus:
            chunks.extend(chunk_document(doc, chunk_size=40, overlap=0))
        retriever.index_corpus(chunks)
        return retriever, chunks

    def test_query_returns_relevant_doc_first(self, mini_corpus):
        retriever, _ = self._build(mini_corpus)
        top = retriever.retrieve("How do I get a refund?", k=1)
        assert len(top) == 1
        assert top[0].chunk.doc_id == "refunds"

    def test_query_about_users_ranks_users_first(self, mini_corpus):
        retriever, _ = self._build(mini_corpus)
        top = retriever.retrieve("How do I look up a user by id?", k=1)
        assert top[0].chunk.doc_id == "users"

    def test_query_about_auth_ranks_auth_first(self, mini_corpus):
        retriever, _ = self._build(mini_corpus)
        top = retriever.retrieve("Where do I put my API key?", k=1)
        assert top[0].chunk.doc_id == "auth"

    def test_k_controls_result_count(self, mini_corpus):
        retriever, chunks = self._build(mini_corpus)
        assert len(retriever.retrieve("user", k=2)) == 2
        assert len(retriever.retrieve("user", k=len(chunks) + 5)) == len(chunks)

    def test_completely_irrelevant_query_returns_low_scores(self, mini_corpus):
        retriever, _ = self._build(mini_corpus)
        results = retriever.retrieve("quokka wallaby zebra emu", k=3)
        for r in results:
            assert r.score == 0.0
