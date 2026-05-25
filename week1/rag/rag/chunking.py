"""Document chunking.

Why chunk at all? Two reasons:

1. **Retrieval granularity.** A typical document is too long to be useful as a
   single retrieval unit — the relevant sentence drowns in unrelated text and
   the embedding becomes an average of many topics.
2. **Context budget.** The LLM has a fixed context window. Retrieving small,
   focused chunks lets us pack more *relevant* tokens into the prompt.

We use the simplest reasonable strategy: a sliding window over whitespace
tokens, with optional overlap between adjacent chunks so we do not split a
sentence right down the middle.

YOU IMPLEMENT: :func:`chunk_text` and :func:`chunk_document`.
"""

from __future__ import annotations

from typing import List

from rag.types import Chunk, Document


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Split a string into overlapping chunks of (approximately) ``chunk_size`` tokens.

    A "token" here is just a whitespace-separated word — no fancy tokeniser.
    The function should return chunks reconstructed with single spaces between
    tokens (so original whitespace is *not* preserved exactly).

    Specification:
      * ``chunk_size`` must be a positive integer; raise ``ValueError`` otherwise.
      * ``overlap`` must satisfy ``0 <= overlap < chunk_size``; raise ``ValueError``
        otherwise. An ``overlap`` equal to ``chunk_size`` would mean the window
        never advances, so it is disallowed.
      * If ``text`` is empty or whitespace-only, return ``[]``.
      * If the text has fewer than or equal to ``chunk_size`` tokens, return a
        single chunk containing the whole text.
      * Otherwise, slide a window of size ``chunk_size`` over the tokens,
        advancing by ``chunk_size - overlap`` tokens between consecutive
        windows. The final chunk should always include the last token, even if
        it ends up shorter than ``chunk_size``.

    Example:
        >>> chunk_text("a b c d e f g", chunk_size=3, overlap=1)
        ['a b c', 'c d e', 'e f g']

    Args:
        text: The input text.
        chunk_size: Maximum number of tokens per chunk.
        overlap: Number of tokens shared between consecutive chunks.

    Returns:
        A list of chunk strings in document order.
    """
    # YOUR CODE HERE (Part 2)
    raise NotImplementedError("Implement chunk_text — see tutorial.md Part 2.")


def chunk_document(doc: Document, chunk_size: int, overlap: int) -> List[Chunk]:
    """Split a :class:`Document` into a list of :class:`Chunk` objects.

    This is a thin wrapper over :func:`chunk_text` that attaches bookkeeping
    metadata to each chunk.

    Each returned chunk must have:
      * ``doc_id`` equal to ``doc.id``;
      * ``chunk_index`` reflecting its 0-based position in the document;
      * ``id`` equal to ``f"{doc.id}:{chunk_index}"``;
      * ``text`` equal to the corresponding output of :func:`chunk_text`.

    Args:
        doc: The source document.
        chunk_size: Forwarded to :func:`chunk_text`.
        overlap: Forwarded to :func:`chunk_text`.

    Returns:
        A list of chunks. May be empty if the document is empty.
    """
    # YOUR CODE HERE (Part 2)
    raise NotImplementedError("Implement chunk_document — see tutorial.md Part 2.")
