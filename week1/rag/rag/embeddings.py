"""Text embeddings.

An *embedding* is a function that maps a string to a vector such that strings
with similar meaning have vectors with high similarity. RAG depends on
embeddings because we use vector similarity to decide which chunks of the
corpus are most relevant to a user's question.

There are many ways to produce embeddings, ranging from very simple
(bag-of-words, TF-IDF) to very expensive (transformer encoders such as
``text-embedding-3-small``). In this assignment we implement classical
TF-IDF from scratch. It is fast, fully deterministic, requires no model
weights, and — perhaps surprisingly — is a strong baseline for keyword-heavy
retrieval over a small corpus.

YOU IMPLEMENT: :func:`tokenize`, :class:`TfIdfEmbedder` (``fit`` and ``embed``).
"""

from __future__ import annotations

import re
from typing import Iterable, List, Protocol

from rag.types import SparseVector


# A token is a contiguous run of word characters, lowercased. Punctuation is
# discarded. This is intentionally simple — production systems use much more
# sophisticated tokenisation, but for TF-IDF on English text this suffices.
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def tokenize(text: str) -> List[str]:
    """Lowercase ``text`` and split it into a list of alphanumeric tokens.

    Specification:
      * Tokens are matched by the regular expression ``[A-Za-z0-9]+``.
      * The output is lowercase.
      * The empty string and pure-punctuation input both return ``[]``.

    Examples:
        >>> tokenize("Hello, World!  HTTP/2")
        ['hello', 'world', 'http', '2']
        >>> tokenize("")
        []

    Args:
        text: The input string.

    Returns:
        The list of tokens in document order, with duplicates preserved.
    """
    # YOUR CODE HERE (Part 3a) — one line, use _TOKEN_RE.
    raise NotImplementedError("Implement tokenize — see tutorial.md Part 3.")


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
    """Term-frequency × inverse-document-frequency embedder.

    The score for token ``t`` in document ``d`` (relative to a corpus of
    ``N`` documents) is::

        tf(t, d)  = number of occurrences of t in d
        idf(t)    = log( (1 + N) / (1 + df(t)) ) + 1
        weight    = tf(t, d) * idf(t)

    where ``df(t)`` is the number of documents in the corpus containing ``t``.
    The final embedding is the resulting sparse vector **L2-normalised**, so
    that the dot product of two embeddings equals their cosine similarity.

    Why ``log((1+N)/(1+df)) + 1`` rather than ``log(N/df)``?

    * The ``+1`` in the numerator and denominator avoids division by zero and
      ``log(0)`` for tokens that appear in zero or all documents.
    * The trailing ``+1`` keeps every IDF strictly positive, so very common
      tokens still receive a small (but non-zero) weight rather than being
      discarded entirely.

    This matches scikit-learn's ``TfidfVectorizer(smooth_idf=True)``.
    """

    def __init__(self) -> None:
        # Mapping from token -> idf weight. Populated by ``fit``. Tokens not
        # present in ``self.idf`` are out-of-vocabulary and should be ignored
        # at embed time.
        self.idf: dict[str, float] = {}
        # Number of documents the embedder was fit on (useful for debugging).
        self.num_documents: int = 0

    def fit(self, corpus: Iterable[str]) -> None:
        """Build the vocabulary and IDF table from ``corpus``.

        Steps you must implement:
          1. Tokenise each document with :func:`tokenize`.
          2. Compute the document frequency ``df(t)`` — the number of
             documents in which ``t`` appears at least once.
          3. Compute ``idf(t) = log((1 + N) / (1 + df(t))) + 1`` for every
             token. Use :func:`math.log` (natural log).
          4. Store the result in ``self.idf`` and update ``self.num_documents``.

        After ``fit`` returns, ``self.idf`` must contain exactly one entry per
        unique token observed in the corpus.

        Args:
            corpus: An iterable of document strings.
        """
        # YOUR CODE HERE (Part 3b)
        raise NotImplementedError("Implement TfIdfEmbedder.fit — see tutorial.md Part 3.")

    def embed(self, text: str) -> SparseVector:
        """Embed ``text`` as an L2-normalised sparse TF-IDF vector.

        Steps you must implement:
          1. Tokenise ``text``.
          2. Count term frequencies.
          3. For each token present in ``self.idf``, compute
             ``weight = tf * idf``. Out-of-vocabulary tokens are skipped.
          4. L2-normalise the vector so that ``sum(w*w for w in vec.values())``
             equals 1. If every weight is zero (e.g. the input has no
             in-vocabulary tokens), return an empty dict — *do not* divide
             by zero.

        Args:
            text: The input string.

        Returns:
            A sparse vector mapping token -> normalised weight.
        """
        # YOUR CODE HERE (Part 3c)
        raise NotImplementedError("Implement TfIdfEmbedder.embed — see tutorial.md Part 3.")
