"""Augmented-prompt assembly and a thin LLM wrapper.

After retrieval we still need to:

1. Render the retrieved chunks into a prompt the LLM can read, and
2. Send that prompt to an LLM.

These are two separate concerns. The prompt format is pure string formatting
and lives in :func:`format_rag_prompt`. The LLM call is wrapped behind the
:class:`LanguageModel` protocol so the pipeline can be tested with a fake
model and run against Ollama in production.
"""

from __future__ import annotations

from typing import List, Protocol

from rag.rag.types import RetrievalResult


# The system instruction sent to the LLM. Chosen to push the model toward
# extractive answers grounded in the supplied context rather than parametric
# (memorised) recall. You may experiment with this for the demo, but the tests
# assume it is used verbatim.
DEFAULT_SYSTEM_PROMPT = (
    "You are a careful assistant. Answer the user's question using ONLY the "
    "information in the supplied context. If the context does not contain the "
    "answer, reply exactly: \"I don't know based on the provided context.\" "
    "Cite the source id in square brackets after each fact, e.g. [users_api:0]."
)


def format_rag_prompt(question: str, results: List[RetrievalResult]) -> str:
    """Render the user prompt that will be paired with :data:`DEFAULT_SYSTEM_PROMPT`.

    The format you must produce is::

        Context:
        [<chunk_id_1>] <chunk_text_1>
        [<chunk_id_2>] <chunk_text_2>
        ...

        Question: <question>

    Specification:
      * Each retrieved chunk goes on its own line, prefixed by its id in
        square brackets and a single space.
      * Chunks appear in the same order they were passed in (the retriever's
        ranking order).
      * If ``results`` is empty, the context block must read::

            Context:
            (no context retrieved)

      * The question section is exactly ``"Question: " + question``.
      * The context block and the question are separated by exactly one blank
        line.

    YOU IMPLEMENT this function (Part 6a).

    Args:
        question: The user's question.
        results: Retrieved chunks, in ranked order.

    Returns:
        A fully-formatted user prompt.
    """
    # YOUR CODE HERE (Part 6a)
    raise NotImplementedError("Implement format_rag_prompt — see tutorial.md Part 6.")


class LanguageModel(Protocol):
    """Anything callable like a chat LLM.

    Implementations receive a system prompt and a user prompt and return the
    assistant's reply as a single string.
    """

    def __call__(self, system: str, user: str) -> str:
        ...


# ---------------------------------------------------------------------- #
# A real Ollama-backed implementation. Provided for the demo script; you  #
# do not need to modify it.                                               #
# ---------------------------------------------------------------------- #
class OllamaChatModel:
    """Wraps :func:`ollama.chat` behind the :class:`LanguageModel` protocol."""

    def __init__(self, model: str = "llama3.1:8b", temperature: float = 0.0) -> None:
        self.model = model
        self.temperature = temperature

    def __call__(self, system: str, user: str) -> str:
        # Imported lazily so that unit tests do not require ``ollama`` to be
        # installed or the daemon to be running.
        from ollama import chat

        response = chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            options={"temperature": self.temperature},
        )
        return response.message.content
