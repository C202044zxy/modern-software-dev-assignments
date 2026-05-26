from __future__ import annotations

import re
from typing import Iterable, List, Protocol
import math

from rag.types import SparseVector


# A token is a contiguous run of word characters, lowercased. Punctuation is
# discarded. This is intentionally simple — production systems use much more
# sophisticated tokenisation, but for TF-IDF on English text this suffices.
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def tokenize(text: str) -> List[str]:
    """Lowercase ``text`` and split it into a list of alphanumeric tokens.

    Args:
        text: The input string.

    Returns:
        The list of tokens in document order, with duplicates preserved.
    """
    return _TOKEN_RE.findall(text.lower())


class Embedder(Protocol):
    """The minimal contract every embedder must satisfy.

    The pipeline only ever talks to embedders through this interface, so you
    can later swap :class:`TfIdfEmbedder` for, say, an Ollama-backed embedder
    without touching any of the retrieval code.
    """

    def fit(self, corpus: Iterable[str]) -> None:
        """Learn any corpus-level statistics needed by :meth:`embed`."""
        ...

    def embed(self, text: str) -> SparseVector:
        """Return the embedding vector for ``text``."""
        ...


class TfIdfEmbedder:

    def __init__(self) -> None:
        self.idf: dict[str, float] = {}
        self.num_documents: int = 0

    def fit(self, corpus: Iterable[str]) -> None:
        """Build the vocabulary and IDF table from ``corpus``.

        Args:
            corpus: An iterable of document strings.
        """
        self.num_documents = 0
        df: dict[str, int] = {}
        for text in corpus:
            self.num_documents += 1
            tokens = tokenize(text)
            for token in set(tokens):
                df[token] = df.get(token, 0) + 1

        self.idf = {t: math.log((1 + self.num_documents) / (1 + df[t])) + 1 for t in df}

    def embed(self, text: str) -> SparseVector:
        """Embed ``text`` as an L2-normalised sparse TF-IDF vector.

        Args:
            text: The input string.

        Returns:
            A sparse vector mapping token -> normalised weight.
        """        
        tokens = tokenize(text)
        tf: dict[str, int] = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        
        embedding: SparseVector = {t: tf[t] * self.idf[t] for t in tf if t in self.idf}
        return self._l2_normalize_sparse(embedding)

    def _l2_normalize_sparse(self, vec: SparseVector) -> SparseVector:
        norm = math.sqrt(sum(v * v for v in vec.values()))
        if norm == 0:
            return vec
        return {k: v / norm for k, v in vec.items()}
