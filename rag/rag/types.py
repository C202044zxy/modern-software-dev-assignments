"""Shared data classes used across the RAG pipeline.

These are intentionally simple containers — no behaviour, just data. Every
other module in the package consumes or produces one of these types, so they
form the "vocabulary" of the pipeline.

You do not need to modify this file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Document:
    """A whole document loaded from disk before any processing.

    Attributes:
        id: A stable identifier for the document (e.g. its filename).
        text: The full raw text of the document.
        metadata: Arbitrary key/value metadata (source path, tags, ...).
    """

    id: str
    text: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Chunk:
    """A retrievable slice of a document.

    A ``Document`` is split into many ``Chunk`` objects during indexing. Each
    chunk carries enough information to (a) be embedded and (b) be traced back
    to its source document for citation.

    Attributes:
        id: A unique identifier of the form ``"{doc_id}:{chunk_index}"``.
        doc_id: The id of the source document.
        chunk_index: Position of this chunk within its source document, 0-based.
        text: The raw text of the chunk.
    """

    id: str
    doc_id: str
    chunk_index: int
    text: str


# A sparse vector. Token -> weight. Missing keys are implicitly zero.
# We use a dict instead of a numpy array because TF-IDF vectors are large and
# very sparse — most documents only use a tiny fraction of the vocabulary.
SparseVector = Dict[str, float]


@dataclass
class EmbeddedChunk:
    """A chunk paired with its embedding vector."""

    chunk: Chunk
    vector: SparseVector


@dataclass
class RetrievalResult:
    """A chunk returned by the retriever, with its similarity score."""

    chunk: Chunk
    score: float
