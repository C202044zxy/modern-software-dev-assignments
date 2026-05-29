"""End-to-end RAG pipeline.

Now we tie everything together. The pipeline owns:

* a :class:`~rag.retriever.Retriever` (which owns an embedder + a vector store);
* a :class:`~rag.generation.LanguageModel`;
* the system prompt sent to the LLM.

It exposes two operations:

* :meth:`RagPipeline.index_documents` — chunk → embed → store.
* :meth:`RagPipeline.answer` — retrieve → format prompt → call LLM → return text.

YOU IMPLEMENT: :meth:`RagPipeline.index_documents` and :meth:`RagPipeline.answer`.
"""

from __future__ import annotations

from typing import List

from rag.rag.generation import DEFAULT_SYSTEM_PROMPT, LanguageModel
from rag.rag.retriever import Retriever
from rag.rag.types import Document


class RagPipeline:
    """Drives the index/retrieve/generate loop.

    Args:
        retriever: A :class:`Retriever`. Its embedder does not need to be
            fitted in advance — :meth:`index_documents` will fit it.
        llm: A :class:`~rag.generation.LanguageModel` callable.
        chunk_size: Tokens per chunk passed to :func:`chunk_document`.
        chunk_overlap: Token overlap between adjacent chunks.
        system_prompt: System message sent to the LLM. Defaults to
            :data:`~rag.generation.DEFAULT_SYSTEM_PROMPT`.
    """

    def __init__(
        self,
        retriever: Retriever,
        llm: LanguageModel,
        chunk_size: int = 80,
        chunk_overlap: int = 20,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self.retriever = retriever
        self.llm = llm
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.system_prompt = system_prompt

    def index_documents(self, docs: List[Document]) -> None:
        """Chunk every document and build the retrieval index.

        Steps:
          1. Call :func:`~rag.chunking.chunk_document` on every document using
             ``self.chunk_size`` and ``self.chunk_overlap``. Concatenate the
             resulting chunk lists.
          2. Hand the combined chunk list to
             :meth:`~rag.retriever.Retriever.index_corpus`, which fits the
             embedder and inserts the chunks into the vector store.

        Args:
            docs: The documents to index.
        """
        # YOUR CODE HERE (Part 6b)
        raise NotImplementedError("Implement RagPipeline.index_documents — see tutorial.md Part 6.")

    def answer(self, question: str, k: int = 4) -> str:
        """Answer ``question`` using retrieval-augmented generation.

        Steps:
          1. ``results = self.retriever.retrieve(question, k=k)``
          2. ``user_prompt = format_rag_prompt(question, results)``
          3. ``return self.llm(self.system_prompt, user_prompt)``

        Args:
            question: The user's natural-language question.
            k: How many chunks to retrieve.

        Returns:
            The model's answer as a single string.
        """
        # YOUR CODE HERE (Part 6c)
        raise NotImplementedError("Implement RagPipeline.answer — see tutorial.md Part 6.")
