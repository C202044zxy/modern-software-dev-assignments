"""Sparse vector storage and nearest-neighbour search.

Once we have embeddings, we need somewhere to put them and a way to find the
``k`` most similar ones to a query vector. Production systems use specialised
vector databases (FAISS, pgvector, Weaviate, ...). We use the simplest thing
that works: a Python list scanned linearly. This is O(N) per query, which is
perfectly fine for the small corpora in this assignment.

YOU IMPLEMENT: :func:`cosine_similarity` and :class:`InMemoryVectorStore`.
"""

from __future__ import annotations

from typing import Iterable, List

from rag.types import EmbeddedChunk, RetrievalResult, SparseVector


def cosine_similarity(a: SparseVector, b: SparseVector) -> float:
    """Compute the cosine similarity between two sparse vectors.

    Cosine similarity is defined as::

        cos(a, b) = (a · b) / (||a|| * ||b||)

    where ``·`` denotes the dot product and ``||·||`` the Euclidean norm.

    **Optimisation hint.** Iterate over the *smaller* of the two dicts and look
    up each key in the other — keys missing from a sparse vector implicitly
    contribute zero to the dot product, so there is no need to walk the union
    of keys.

    Specification:
      * If either input is empty, return 0.0 (the convention for a zero vector).
      * If either vector has zero norm, return 0.0 (no division by zero).
      * The result is a finite float in the range ``[-1.0, 1.0]``. In this
        assignment all weights are non-negative, so the practical range is
        ``[0.0, 1.0]``.

    Args:
        a: A sparse vector.
        b: A sparse vector.

    Returns:
        The cosine similarity of ``a`` and ``b``.
    """
    # YOUR CODE HERE (Part 4a)
    raise NotImplementedError("Implement cosine_similarity — see tutorial.md Part 4.")


class InMemoryVectorStore:
    """An ``EmbeddedChunk`` collection with top-k similarity search.

    The store keeps every embedded chunk in a Python list and answers queries
    by computing the cosine similarity against every stored vector.
    """

    def __init__(self) -> None:
        self._entries: List[EmbeddedChunk] = []

    def __len__(self) -> int:
        return len(self._entries)

    def add(self, embedded: Iterable[EmbeddedChunk]) -> None:
        """Append every :class:`EmbeddedChunk` in ``embedded`` to the store.

        Args:
            embedded: Any iterable of embedded chunks.
        """
        # YOUR CODE HERE (Part 4b) — one or two lines.
        raise NotImplementedError("Implement InMemoryVectorStore.add — see tutorial.md Part 4.")

    def search(self, query: SparseVector, k: int) -> List[RetrievalResult]:
        """Return the top-``k`` stored chunks ranked by similarity to ``query``.

        Specification:
          * Compute :func:`cosine_similarity` between ``query`` and every
            stored vector.
          * Return at most ``k`` :class:`RetrievalResult` objects, sorted by
            score in descending order. Ties may be broken arbitrarily.
          * If ``k`` is greater than the number of stored chunks, return all
            of them (still sorted).
          * If ``k <= 0`` or the store is empty, return ``[]``.
          * Do **not** mutate the store.

        Args:
            query: The query vector.
            k: The maximum number of results to return.

        Returns:
            A list of retrieval results, ordered by descending score.
        """
        # YOUR CODE HERE (Part 4c)
        raise NotImplementedError("Implement InMemoryVectorStore.search — see tutorial.md Part 4.")
