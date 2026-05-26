from __future__ import annotations

from typing import List

from rag.rag.types import Chunk, Document


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Split a string into overlapping chunks of (approximately) ``chunk_size`` tokens.

    A "token" here is just a whitespace-separated word — no fancy tokeniser.
    The function should return chunks reconstructed with single spaces between
    tokens (so original whitespace is *not* preserved exactly).

    Args:
        text: The input text.
        chunk_size: Maximum number of tokens per chunk.
        overlap: Number of tokens shared between consecutive chunks.

    Returns:
        A list of chunk strings in document order.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size should be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("0 <= overlap < chunk_size should be satisfied")
    
    tokens = text.split()
    step = chunk_size - overlap
    chunks: List[str] = []
    for i in range(0, len(tokens), step):
        chunks.append(" ".join(tokens[i: i + chunk_size]))
        if i + chunk_size >= len(tokens):
            break
    return chunks


def chunk_document(doc: Document, chunk_size: int, overlap: int) -> List[Chunk]:
    """Split a :class:`Document` into a list of :class:`Chunk` objects.

    This is a thin wrapper over :func:`chunk_text` that attaches bookkeeping
    metadata to each chunk.

    Args:
        doc: The source document.
        chunk_size: Forwarded to :func:`chunk_text`.
        overlap: Forwarded to :func:`chunk_text`.

    Returns:
        A list of chunks. May be empty if the document is empty.
    """
    chunks_str = chunk_text(doc.text, chunk_size, overlap)
    chunks: List[Chunk] = []
    for i, chunk_str in enumerate(chunks_str):
        id = "{doc_id}:{chunk_index}".format(doc_id=doc.id, chunk_index=i)
        chunks.append(Chunk(id, doc.id, i, chunk_str))
    return chunks
