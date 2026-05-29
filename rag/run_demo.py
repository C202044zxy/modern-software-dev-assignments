"""End-to-end RAG demo against an Ollama-served model.

# OBSERVATION FROM PART 7:
# (fill in once you've experimented — e.g. "with k=1 the refund question
#  fails because the relevant facts span chunks refunds:0 and refunds:1")

Run from this directory:

    python run_demo.py

Prerequisites: Ollama is installed and `llama3.1:8b` has been pulled
(see week1/README.md). If you do not have Ollama available, pass
``--dry-run`` to skip the LLM call and only print retrieval results.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

# Make ``import rag.*`` resolve when running this file directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rag.rag.embeddings import TfIdfEmbedder
from rag.rag.generation import OllamaChatModel
from rag.rag.pipeline import RagPipeline
from rag.rag.retriever import Retriever
from rag.rag.types import Document

CORPUS_DIR = Path(__file__).resolve().parent / "data" / "corpus"


# A handful of questions exercising different retrieval cases.
DEMO_QUESTIONS = [
    "How do I authenticate requests to the Acme API?",
    "What endpoint do I call to update a user's email?",
    "Can I get a refund for a charge from last year?",
    "What headers does the API return to tell me about rate limits?",
    "What is the SLA on customer support response time?",  # unanswerable
]


def load_corpus(corpus_dir: Path) -> List[Document]:
    docs: List[Document] = []
    for path in sorted(corpus_dir.glob("*.md")):
        docs.append(
            Document(
                id=path.stem,
                text=path.read_text(encoding="utf-8"),
                metadata={"source": str(path)},
            )
        )
    return docs


def build_pipeline(llm) -> RagPipeline:
    retriever = Retriever(embedder=TfIdfEmbedder())
    return RagPipeline(
        retriever=retriever,
        llm=llm,
        chunk_size=80,
        chunk_overlap=20,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip the LLM call and only print retrieval results.",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=3,
        help="Number of chunks to retrieve per question (default: 3).",
    )
    parser.add_argument(
        "--model",
        default="llama3.1:8b",
        help="Ollama model name (default: llama3.1:8b).",
    )
    args = parser.parse_args()

    docs = load_corpus(CORPUS_DIR)
    if not docs:
        print(f"No documents found under {CORPUS_DIR}.", file=sys.stderr)
        return 1

    if args.dry_run:
        # A no-op LLM. Lets you exercise the indexing + retrieval path even
        # without Ollama installed.
        def llm(system: str, user: str) -> str:
            return "<dry-run: LLM not called>"

    else:
        llm = OllamaChatModel(model=args.model)

    pipeline = build_pipeline(llm)
    pipeline.index_documents(docs)

    for question in DEMO_QUESTIONS:
        print("=" * 72)
        print(f"Q: {question}")
        print("-" * 72)
        # Show what the retriever found, then what the LLM said.
        retrieved = pipeline.retriever.retrieve(question, k=args.k)
        for r in retrieved:
            preview = r.chunk.text.replace("\n", " ")
            if len(preview) > 100:
                preview = preview[:97] + "..."
            print(f"  [{r.chunk.id}] score={r.score:.3f}  {preview}")
        print("-" * 72)
        answer = pipeline.answer(question, k=args.k)
        print(f"A: {answer}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
