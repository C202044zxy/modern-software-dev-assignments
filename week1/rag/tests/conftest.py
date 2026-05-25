"""Shared pytest fixtures and helpers.

Adds the assignment root to ``sys.path`` so tests can ``import rag.*``
without needing the project to be installed as a package, and provides a few
fixtures used across multiple test files.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Tuple

import pytest

# Make ``import rag.*`` work when pytest is invoked from the repo root.
_ASSIGNMENT_ROOT = Path(__file__).resolve().parent.parent
if str(_ASSIGNMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_ASSIGNMENT_ROOT))


# Imported AFTER sys.path is set up.
from rag.types import Document  # noqa: E402


@pytest.fixture
def mini_corpus() -> List[Document]:
    """A tiny three-document corpus where each doc is about a distinct topic.

    Chosen so that a query about one topic should clearly retrieve that
    document and not the others.
    """
    return [
        Document(
            id="auth",
            text=(
                "Authenticate every request by sending the X-API-Key header. "
                "Requests without an API key return HTTP 401."
            ),
        ),
        Document(
            id="users",
            text=(
                "GET /users/{id} returns the user with the given id as JSON "
                "with fields id, name, and email."
            ),
        ),
        Document(
            id="refunds",
            text=(
                "Refunds are available within 30 days of the original charge. "
                "Email billing to request a refund."
            ),
        ),
    ]


class FakeLLM:
    """A scripted LLM for unit tests.

    Records every ``(system, user)`` call it receives and returns scripted
    responses in order. If the script runs out, returns the placeholder
    ``"<no more scripted responses>"``.
    """

    def __init__(self, responses: List[str] | None = None) -> None:
        self.responses = list(responses or [])
        self.calls: List[Tuple[str, str]] = []

    def __call__(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        if self.responses:
            return self.responses.pop(0)
        return "<no more scripted responses>"


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()
