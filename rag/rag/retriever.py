"""Retriever — embed-then-search.

The :class:`Retriever` is the glue between the embedder (Part 3) and the
vector store (Part 4). It exposes two operations:

* :meth:`Retriever.index` — embed a list of chunks and insert them into the
  underlying store.
* :meth:`Retriever.retrieve` — embed a query string and search the store for
  the top-``k`` most similar chunks.

This module is small. By the time you reach Part 5 you have already done all
the hard work; the retriever just composes pieces.

YOU IMPLEMENT: :class:`Retriever`.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import List

from rag.rag.embeddings import Embedder
from rag.rag.types import Chunk, RetrievalResult
from rag.rag.vector_store import InMemoryVectorStore


class Retriever:
    """Embeds chunks/queries and answers nearest-neighbour queries.

    Args:
        embedder: An :class:`~rag.embeddings.Embedder`. Must already be fitted
            before :meth:`retrieve` is called — see :meth:`index_corpus`, which
            handles fitting for you, or call ``embedder.fit(...)`` yourself.
        store: A vector store. Defaults to a fresh :class:`InMemoryVectorStore`.
    """

    def __init__(
        self,
        embedder: Embedder,
        store: InMemoryVectorStore | None = None,
    ) -> None:
        self.embedder = embedder
        self.store = store if store is not None else InMemoryVectorStore()

    def index(self, chunks: Iterable[Chunk]) -> None:
        """Embed every chunk and add it to the underlying store.

        Note: the embedder must already be fitted on a corpus. If you have a
        chunk list and want a one-call "fit + index", use :meth:`index_corpus`.

        Steps:
          1. For each ``chunk`` in ``chunks``, call ``self.embedder.embed`` on
             its text to produce a vector.
          2. Wrap the chunk + vector in an :class:`EmbeddedChunk`.
          3. Add all of them to ``self.store``.

        Args:
            chunks: Any iterable of :class:`Chunk` objects.
        """
        # YOUR CODE HERE (Part 5a)
        raise NotImplementedError("Implement Retriever.index — see tutorial.md Part 5.")

    def retrieve(self, query: str, k: int = 4) -> List[RetrievalResult]:
        """Return the top-``k`` chunks most similar to ``query``.

        Steps:
          1. Embed ``query`` using ``self.embedder``.
          2. Delegate to ``self.store.search`` and return the result.

        Args:
            query: The user's question (or any natural-language string).
            k: The number of chunks to retrieve.

        Returns:
            A list of :class:`RetrievalResult` ranked by descending score.
        """
        # YOUR CODE HERE (Part 5b)
        raise NotImplementedError("Implement Retriever.retrieve — see tutorial.md Part 5.")

    # ------------------------------------------------------------------ #
    # Convenience method — provided. You do NOT need to modify this.     #
    # ------------------------------------------------------------------ #
    def index_corpus(self, chunks: List[Chunk]) -> None:
        """Fit the embedder on ``chunks`` and index them.

        Most callers want a one-shot "build the index" entry point and don't
        care about the fit/index split. This wraps both for convenience.
        """
        self.embedder.fit([c.text for c in chunks])
        self.index(chunks)
