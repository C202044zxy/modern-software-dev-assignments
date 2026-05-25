"""A minimal Retrieval-Augmented Generation library implemented from scratch.

The package is organised so you build the pipeline bottom-up:

    types        -> shared data classes (provided)
    chunking     -> split documents into retrievable units (Part 2)
    embeddings   -> turn text into vectors (Part 3)
    vector_store -> store vectors and find nearest neighbours (Part 4)
    retriever    -> wire embedder + store together (Part 5)
    generation   -> assemble the augmented prompt (Part 6)
    pipeline     -> the end-to-end ``index -> retrieve -> generate`` loop (Part 6)

Most modules ship as skeletons; follow ``tutorial.md`` to fill them in.
"""

from rag.types import Chunk, Document, EmbeddedChunk, RetrievalResult

__all__ = ["Chunk", "Document", "EmbeddedChunk", "RetrievalResult"]
