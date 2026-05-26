# RAG — Build a Retrieval-Augmented Generation system from scratch

This assignment walks you through implementing a complete RAG pipeline:
chunking → TF-IDF embeddings → vector store → retriever → LLM generation.

**Start with [`tutorial.md`](./tutorial.md).** It explains the theory,
specifies what you need to implement, and tells you when to run which tests.

## Quick reference

```bash
# Run the tests (from week1/rag/)
pytest

# Run a single part
pytest tests/test_chunking.py -v
pytest tests/test_embeddings.py -v
pytest tests/test_vector_store.py -v
pytest tests/test_retriever.py -v
pytest tests/test_pipeline.py -v

# Once everything is green, run the end-to-end demo against Ollama
python run_demo.py

# Or, without Ollama, exercise just the retrieval path
python run_demo.py --dry-run
```

## What you implement

| File | Functions / classes |
| ---- | ------------------- |
| `rag/chunking.py`     | `chunk_text`, `chunk_document` |
| `rag/embeddings.py`   | `tokenize`, `TfIdfEmbedder.fit`, `TfIdfEmbedder.embed` |
| `rag/vector_store.py` | `cosine_similarity`, `InMemoryVectorStore.add`, `InMemoryVectorStore.search` |
| `rag/retriever.py`    | `Retriever.index`, `Retriever.retrieve` |
| `rag/generation.py`   | `format_rag_prompt` |
| `rag/pipeline.py`     | `RagPipeline.index_documents`, `RagPipeline.answer` |

Everything else (data classes, the Ollama LLM wrapper, the `index_corpus`
convenience method, the sample corpus, the test suite, the demo runner) is
provided.
