"""Unit tests for rag.embeddings (Part 3)."""

from __future__ import annotations

import math

import pytest

from rag.rag.embeddings import TfIdfEmbedder, tokenize


# ---------- tokenize ----------

class TestTokenize:
    def test_basic(self):
        assert tokenize("Hello, World!") == ["hello", "world"]

    def test_alphanumeric_kept(self):
        assert tokenize("HTTP/2 OAuth2 v1.0") == ["http", "2", "oauth2", "v1", "0"]

    def test_empty_string(self):
        assert tokenize("") == []

    def test_punctuation_only(self):
        assert tokenize("!?.,;:") == []

    def test_preserves_duplicates_and_order(self):
        assert tokenize("foo bar foo baz bar foo") == [
            "foo",
            "bar",
            "foo",
            "baz",
            "bar",
            "foo",
        ]


# ---------- TfIdfEmbedder.fit ----------

class TestTfIdfEmbedderFit:
    def test_records_num_documents(self):
        e = TfIdfEmbedder()
        e.fit(["a b c", "b c d", "c d e"])
        assert e.num_documents == 3

    def test_vocabulary_is_union_of_tokens(self):
        e = TfIdfEmbedder()
        e.fit(["a b c", "b c d"])
        assert set(e.idf.keys()) == {"a", "b", "c", "d"}

    def test_idf_uses_smoothed_formula(self):
        # N = 3 documents.
        # df("a") = 1 -> idf = log(4/2) + 1 = log(2) + 1
        # df("c") = 3 -> idf = log(4/4) + 1 = 1.0
        e = TfIdfEmbedder()
        e.fit(["a b c", "b c", "c"])
        assert e.idf["a"] == pytest.approx(math.log(4 / 2) + 1)
        assert e.idf["b"] == pytest.approx(math.log(4 / 3) + 1)
        assert e.idf["c"] == pytest.approx(1.0)

    def test_idf_treats_documents_not_terms(self):
        # "a" appears many times in the same document, but df is still 1.
        e = TfIdfEmbedder()
        e.fit(["a a a a a", "b"])
        # df("a") = 1, N = 2 => idf = log(3/2) + 1
        assert e.idf["a"] == pytest.approx(math.log(3 / 2) + 1)

    def test_fit_is_idempotent_on_repeated_call(self):
        e = TfIdfEmbedder()
        e.fit(["a b", "b c"])
        idf_first = dict(e.idf)
        e.fit(["a b", "b c"])
        assert e.idf == idf_first
        assert e.num_documents == 2


# ---------- TfIdfEmbedder.embed ----------

class TestTfIdfEmbedderEmbed:
    def _fitted(self):
        e = TfIdfEmbedder()
        e.fit([
            "the cat sat on the mat",
            "the dog sat on the log",
            "the bird flew",
        ])
        return e

    def test_embedding_is_l2_normalised(self):
        e = self._fitted()
        v = e.embed("the cat sat on the mat")
        norm_sq = sum(w * w for w in v.values())
        assert norm_sq == pytest.approx(1.0)

    def test_oov_tokens_are_ignored(self):
        e = self._fitted()
        # "quokka" and "zebra" are out of vocabulary.
        v = e.embed("quokka cat zebra")
        assert "quokka" not in v
        assert "zebra" not in v
        assert "cat" in v

    def test_all_oov_returns_empty_dict(self):
        e = self._fitted()
        v = e.embed("quokka zebra wallaby")
        assert v == {}

    def test_repeated_tokens_increase_weight(self):
        e = self._fitted()
        v1 = e.embed("cat")
        v2 = e.embed("cat cat cat cat cat")
        # After L2 normalisation, repeating the *same* token still produces
        # a unit vector pointing in the same direction.
        assert set(v1.keys()) == set(v2.keys()) == {"cat"}
        assert v1["cat"] == pytest.approx(1.0)
        assert v2["cat"] == pytest.approx(1.0)

    def test_same_text_produces_same_vector(self):
        e = self._fitted()
        assert e.embed("the cat sat") == e.embed("the cat sat")

    def test_rare_terms_outweigh_common_terms(self):
        # "the" appears in all three docs (df=3), "bird" in one (df=1).
        # After multiplying by tf=1 each and L2-normalising, "bird" should
        # have a larger weight than "the".
        e = self._fitted()
        v = e.embed("the bird")
        assert v["bird"] > v["the"]
