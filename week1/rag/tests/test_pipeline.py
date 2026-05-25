"""Unit tests for rag.generation and rag.pipeline (Part 6)."""

from __future__ import annotations

from rag.embeddings import TfIdfEmbedder
from rag.generation import DEFAULT_SYSTEM_PROMPT, format_rag_prompt
from rag.pipeline import RagPipeline
from rag.retriever import Retriever
from rag.types import Chunk, RetrievalResult

from .conftest import FakeLLM


def _result(cid: str, text: str, score: float = 1.0) -> RetrievalResult:
    return RetrievalResult(
        chunk=Chunk(id=cid, doc_id=cid.split(":")[0], chunk_index=0, text=text),
        score=score,
    )


# ---------- format_rag_prompt ----------

class TestFormatRagPrompt:
    def test_basic_layout(self):
        prompt = format_rag_prompt(
            "What is X?",
            [_result("a:0", "alpha doc"), _result("b:0", "beta doc")],
        )
        expected = (
            "Context:\n"
            "[a:0] alpha doc\n"
            "[b:0] beta doc\n"
            "\n"
            "Question: What is X?"
        )
        assert prompt == expected

    def test_preserves_retrieval_order(self):
        prompt = format_rag_prompt(
            "Q",
            [_result("b:0", "second"), _result("a:0", "first")],
        )
        # b:0 must come before a:0 because that is the order we passed in.
        assert prompt.index("[b:0]") < prompt.index("[a:0]")

    def test_empty_results_uses_placeholder(self):
        prompt = format_rag_prompt("Q?", [])
        assert "Context:\n(no context retrieved)" in prompt
        assert prompt.endswith("Question: Q?")

    def test_chunk_id_is_present_for_citation(self):
        prompt = format_rag_prompt("Q", [_result("refunds:2", "txt")])
        assert "[refunds:2]" in prompt


# ---------- RagPipeline ----------

class TestRagPipeline:
    def _pipeline(self, mini_corpus, llm: FakeLLM) -> RagPipeline:
        retriever = Retriever(embedder=TfIdfEmbedder())
        pipe = RagPipeline(
            retriever=retriever,
            llm=llm,
            chunk_size=40,
            chunk_overlap=10,
        )
        pipe.index_documents(mini_corpus)
        return pipe

    def test_index_documents_populates_store(self, mini_corpus, fake_llm):
        pipe = self._pipeline(mini_corpus, fake_llm)
        assert len(pipe.retriever.store) > 0

    def test_answer_calls_llm_once(self, mini_corpus):
        llm = FakeLLM(responses=["The answer."])
        pipe = self._pipeline(mini_corpus, llm)
        result = pipe.answer("How do I authenticate?", k=2)
        assert result == "The answer."
        assert len(llm.calls) == 1

    def test_answer_uses_default_system_prompt(self, mini_corpus):
        llm = FakeLLM(responses=["ok"])
        pipe = self._pipeline(mini_corpus, llm)
        pipe.answer("test", k=1)
        system, _ = llm.calls[0]
        assert system == DEFAULT_SYSTEM_PROMPT

    def test_answer_passes_retrieved_context_to_llm(self, mini_corpus):
        llm = FakeLLM(responses=["ok"])
        pipe = self._pipeline(mini_corpus, llm)
        pipe.answer("How do I get a refund?", k=1)
        _, user_prompt = llm.calls[0]
        # The retrieved chunk should be from the refunds doc, so the user
        # prompt must contain its doc id as a citation marker.
        assert "[refunds:" in user_prompt
        # And of course the question itself.
        assert "How do I get a refund?" in user_prompt

    def test_answer_respects_custom_system_prompt(self, mini_corpus):
        llm = FakeLLM(responses=["ok"])
        retriever = Retriever(embedder=TfIdfEmbedder())
        pipe = RagPipeline(
            retriever=retriever,
            llm=llm,
            chunk_size=40,
            chunk_overlap=10,
            system_prompt="custom-system",
        )
        pipe.index_documents(mini_corpus)
        pipe.answer("test", k=1)
        assert llm.calls[0][0] == "custom-system"
