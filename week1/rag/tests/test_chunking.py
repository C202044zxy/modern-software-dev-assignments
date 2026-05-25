"""Unit tests for rag.chunking (Part 2)."""

from __future__ import annotations

import pytest

from rag.chunking import chunk_document, chunk_text
from rag.types import Document


# ---------- chunk_text ----------

class TestChunkText:
    def test_empty_string_returns_empty_list(self):
        assert chunk_text("", chunk_size=10, overlap=0) == []

    def test_whitespace_only_returns_empty_list(self):
        assert chunk_text("   \n  \t ", chunk_size=10, overlap=0) == []

    def test_text_shorter_than_chunk_returns_single_chunk(self):
        assert chunk_text("a b c", chunk_size=10, overlap=0) == ["a b c"]

    def test_text_equal_to_chunk_size_returns_single_chunk(self):
        assert chunk_text("a b c", chunk_size=3, overlap=0) == ["a b c"]

    def test_simple_split_no_overlap(self):
        assert chunk_text("a b c d e f", chunk_size=2, overlap=0) == [
            "a b",
            "c d",
            "e f",
        ]

    def test_split_with_overlap(self):
        # Window size 3, step = 3 - 1 = 2 => starts at 0, 2, 4
        assert chunk_text("a b c d e f g", chunk_size=3, overlap=1) == [
            "a b c",
            "c d e",
            "e f g",
        ]

    def test_final_chunk_includes_last_token_even_if_short(self):
        # 7 tokens, window=3, step=3 => starts at 0, 3, 6 => last chunk has 1 token
        result = chunk_text("a b c d e f g", chunk_size=3, overlap=0)
        assert result[-1].split()[-1] == "g"

    def test_does_not_duplicate_final_chunk_when_aligned(self):
        # 6 tokens, window=3, step=3 => starts at 0, 3 => exactly two chunks,
        # no spurious extra chunk.
        assert chunk_text("a b c d e f", chunk_size=3, overlap=0) == [
            "a b c",
            "d e f",
        ]

    def test_invalid_chunk_size_raises(self):
        with pytest.raises(ValueError):
            chunk_text("a b c", chunk_size=0, overlap=0)
        with pytest.raises(ValueError):
            chunk_text("a b c", chunk_size=-3, overlap=0)

    def test_overlap_equal_to_chunk_size_raises(self):
        with pytest.raises(ValueError):
            chunk_text("a b c", chunk_size=3, overlap=3)

    def test_negative_overlap_raises(self):
        with pytest.raises(ValueError):
            chunk_text("a b c", chunk_size=3, overlap=-1)

    def test_chunks_collectively_cover_all_tokens(self):
        text = " ".join(str(i) for i in range(50))
        chunks = chunk_text(text, chunk_size=7, overlap=2)
        all_tokens = set()
        for c in chunks:
            all_tokens.update(c.split())
        assert all_tokens == {str(i) for i in range(50)}


# ---------- chunk_document ----------

class TestChunkDocument:
    def test_returns_chunks_with_correct_doc_id_and_index(self):
        doc = Document(id="users_api", text="a b c d e f g h", metadata={})
        chunks = chunk_document(doc, chunk_size=3, overlap=0)
        assert [c.doc_id for c in chunks] == ["users_api"] * len(chunks)
        assert [c.chunk_index for c in chunks] == list(range(len(chunks)))

    def test_chunk_id_format(self):
        doc = Document(id="auth", text="x y z w", metadata={})
        chunks = chunk_document(doc, chunk_size=2, overlap=0)
        assert chunks[0].id == "auth:0"
        assert chunks[1].id == "auth:1"

    def test_empty_document_returns_empty_list(self):
        doc = Document(id="empty", text="", metadata={})
        assert chunk_document(doc, chunk_size=10, overlap=0) == []
