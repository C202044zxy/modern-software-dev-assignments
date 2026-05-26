# Assignment: Build a RAG System from Scratch

> "An LLM with retrieval is to an LLM without it as an open-book exam is to a
> closed-book one." — folk wisdom

## Overview

In this assignment you will implement a **Retrieval-Augmented Generation
(RAG)** system end-to-end. By the end you will have:

* a document **chunker** that turns long files into retrievable units;
* a **TF-IDF embedder** that maps text to sparse vectors;
* an in-memory **vector store** that supports nearest-neighbour search;
* a **retriever** that, given a question, returns the most relevant chunks;
* a **prompt formatter + LLM wrapper** that turns retrieved chunks into an
  answer; and
* an end-to-end **pipeline** that you can point at any corpus.

Most of the code is yours to write. The skeleton supplies the data classes,
interfaces, and a runnable Ollama demo, but every function with substantive
logic is left as `NotImplementedError("...")` waiting for your code.

A complete pytest suite ships alongside the skeleton. **At the start of the
assignment every test is failing.** As you implement each part the
corresponding tests turn green, and at the end the whole suite passes.

### Logistics

| Part | Module | What you build | Tests |
| ---- | ------ | -------------- | ----- |
| 1 | — | Background reading & setup | — |
| 2 | `rag/chunking.py` | Token-window chunker | `tests/test_chunking.py` |
| 3 | `rag/embeddings.py` | Tokeniser + TF-IDF | `tests/test_embeddings.py` |
| 4 | `rag/vector_store.py` | Cosine similarity + in-memory store | `tests/test_vector_store.py` |
| 5 | `rag/retriever.py` | Embed-then-search retriever | `tests/test_retriever.py` |
| 6 | `rag/generation.py`, `rag/pipeline.py` | Prompt format + end-to-end pipeline | `tests/test_pipeline.py` |
| 7 | `run_demo.py` | Drive the full pipeline against Ollama | — |

### How to run the tests

From `week1/rag/`:

```bash
# Run everything
pytest

# Run a single part
pytest tests/test_chunking.py -v

# Stop on first failure (useful while iterating)
pytest -x
```

If `pytest` is not on your path, run it through Poetry: `poetry run pytest`.

---

## Part 1 — Background

### Why RAG?

A vanilla LLM call has two sources of knowledge:

1. **Parametric memory** — what the model learned during pre-training. This is
   frozen at training time, so the model has no idea about your codebase, your
   customer's invoice, or this morning's incident.
2. **The prompt** — anything you put in the user/system message. This can be
   anything *current*, but the context window is finite, so you cannot just
   stuff your entire knowledge base in there.

RAG bridges the two. Before answering, we **retrieve** a small number of
relevant snippets from a corpus and **augment** the prompt with them. The LLM
then generates an answer grounded in the supplied context rather than relying
on possibly-stale parametric memory.

```
                                  ┌─────────────────────────────┐
                                  │            Corpus           │
                                  │ (your docs, code, tickets…) │
                                  └─────────────┬───────────────┘
                                                │  (offline)
                                                ▼
            ┌───────────┐   ┌────────────┐   ┌─────────────┐
            │   user    │──▶│  retriever │──▶│ top-k chunks│
            │ question  │   │ (embedding │   └──────┬──────┘
            └───────────┘   │  + search) │          │
                            └────────────┘          │
                                                    ▼
                                       ┌──────────────────────┐
                                       │  prompt template     │
                                       │  (question + chunks) │
                                       └──────────┬───────────┘
                                                  ▼
                                            ┌──────────┐
                                            │   LLM    │──▶ answer
                                            └──────────┘
```

### Pipeline phases

A RAG system has two phases:

**Indexing (offline).** You take a corpus of documents, split each into
**chunks** (small enough to be retrieval-granular and to fit in the context
window), turn each chunk into a vector with an **embedder**, and store those
vectors in a **vector store**.

**Querying (online).** You embed the user's question with the *same* embedder,
ask the vector store for the top-`k` most similar chunks, drop those chunks
into a prompt template, and send the prompt to an LLM. The LLM's reply is
your answer.

### Why TF-IDF?

Modern RAG systems use dense neural embeddings — `text-embedding-3-small`,
`nomic-embed-text`, etc. We are going to implement classical **TF-IDF**
instead because:

* it is **fully deterministic**, so unit tests are reproducible;
* it requires **no model weights or GPU**;
* it is a **strong baseline** for keyword-heavy retrieval over a small
  corpus (which is exactly our setting);
* implementing it from scratch makes the abstract concept of "an embedding"
  concrete.

The architecture is set up so that you can swap the embedder for a dense one
later without touching any of the retrieval, prompting, or pipeline code —
that is the whole point of the `Embedder` protocol you will see in Part 3.

### Setup

This assignment lives at `week1/rag/`. Layout:

```
week1/rag/
├── tutorial.md               <- this file
├── README.md                 <- short reference
├── rag/                      <- the package you implement
│   ├── __init__.py
│   ├── types.py              <- shared dataclasses (provided)
│   ├── chunking.py           <- Part 2
│   ├── embeddings.py         <- Part 3
│   ├── vector_store.py       <- Part 4
│   ├── retriever.py          <- Part 5
│   ├── generation.py         <- Part 6
│   └── pipeline.py           <- Part 6
├── tests/                    <- pytest suite (provided)
│   ├── conftest.py
│   ├── test_chunking.py
│   ├── test_embeddings.py
│   ├── test_vector_store.py
│   ├── test_retriever.py
│   └── test_pipeline.py
├── data/corpus/              <- sample documents (provided)
└── run_demo.py               <- end-to-end demo against Ollama (provided)
```

Confirm everything is wired up before you start writing code:

```bash
cd week1/rag
pytest -q
```

You should see a long list of failures, each one a `NotImplementedError`.
That is the starting state — every failing test is one you will turn green.

---

## Part 2 — Chunking (`rag/chunking.py`)

### The problem

A single Wikipedia article might be 30 KB of text. If we embed the whole
article as one vector, two things go wrong:

1. **The vector loses information.** The embedding averages over every topic
   the article touches. A query about one sentence will match weakly because
   the vector mostly represents the rest of the article.
2. **The retrieved chunk does not fit in the prompt.** Even with a large
   context window, we want to retrieve *several* chunks per query and leave
   room for the answer.

So we split each document into smaller **chunks**.

### The strategy

We will use the simplest reasonable strategy: a sliding window over
whitespace-separated tokens. Two knobs control it:

* **`chunk_size`** — maximum tokens per chunk.
* **`overlap`** — tokens shared between consecutive chunks, to avoid cutting
  important phrases in half.

If `chunk_size = 5` and `overlap = 2`, the window advances by `5 − 2 = 3`
tokens between chunks:

```
tokens:    a  b  c  d  e  f  g  h  i  j
chunk 0:  [a  b  c  d  e]
chunk 1:           [d  e  f  g  h]
chunk 2:                    [g  h  i  j]
```

Notice the last chunk is shorter than `chunk_size` (4 tokens instead of 5).
That is fine and expected — we never want to drop the tail of the document.

### Your task

Open `rag/chunking.py` and implement:

* `chunk_text(text, chunk_size, overlap) -> List[str]`
* `chunk_document(doc, chunk_size, overlap) -> List[Chunk]`

The docstrings spell out the contract; the tests pin it down precisely. A few
things to watch for:

* Validate inputs: `chunk_size > 0` and `0 ≤ overlap < chunk_size`.
* Empty / whitespace-only input returns `[]` — *not* `[""]`.
* The last chunk must always include the last token.
* Avoid producing duplicate chunks when `len(tokens)` is an exact multiple of
  the stride (an easy off-by-one bug). The test
  `test_does_not_duplicate_final_chunk_when_aligned` catches this.

### Run the tests

```bash
pytest tests/test_chunking.py -v
```

All 14 tests should pass before you continue.

### Quick design discussion

Is whitespace tokenisation the "right" choice? In practice no — production
systems chunk by sentences or by recursive character splitters that respect
paragraph boundaries. But word-window chunking is simple, predictable, and
captures the essential trade-off (granularity vs. context coherence) that
every chunker has to navigate. You can replace it later without changing any
downstream code, because every other module only sees `Chunk` objects.

---

## Part 3 — Embeddings (`rag/embeddings.py`)

### The problem

We need a function that maps a string to a vector such that **strings about
the same topic produce nearby vectors**. Then we can answer "what is the
most similar chunk to this query?" with a vector lookup.

### TF-IDF in one screen

For a corpus of `N` documents:

* **Term frequency** `tf(t, d)`: how many times token `t` appears in document
  `d`. We use the raw count.
* **Document frequency** `df(t)`: how many distinct documents contain `t` at
  least once. Note: **distinct documents**, not total occurrences.
* **Inverse document frequency** `idf(t)`:

  ![idf](https://render.githubusercontent.com/render/math?math=%5Coperatorname%7Bidf%7D(t)%20%3D%20%5Clog%5Cfrac%7B1%2BN%7D%7B1%2B%5Coperatorname%7Bdf%7D(t)%7D%20%2B%201)

  In Python: `math.log((1 + N) / (1 + df_t)) + 1`. The `+1`s smooth two
  pathological cases — `df = 0` (would divide by zero) and `df = N` (would
  give zero weight). The trailing `+ 1` keeps the weight strictly positive
  even for tokens that appear in every document.

* **TF-IDF weight**: `tf(t, d) × idf(t)`.

The embedding of `d` is the sparse vector `{t: tf(t, d) × idf(t) for t in d}`,
then **L2-normalised** to unit length. Why normalise?

> If `||a|| = ||b|| = 1`, then `cos(a, b) = a · b`.

This identity is the reason we can swap "search by similarity" for "search by
dot product" in Part 4 and get the same answer, more efficiently.

### Sparse vectors

A document of 100 unique tokens produces a vector with only 100 non-zero
entries — but the vocabulary might have 10,000 entries. We use a Python
`Dict[str, float]` rather than a list of 10,000 floats so the
representation only stores what is non-zero. The dot product becomes:

```python
sum(a[t] * b[t] for t in a.keys() & b.keys())  # or: for t in a if t in b
```

### The `Embedder` protocol

`rag/embeddings.py` defines:

```python
class Embedder(Protocol):
    def fit(self, corpus): ...
    def embed(self, text) -> SparseVector: ...
```

Every embedder in this assignment satisfies this protocol. If you wanted to
switch to a dense neural embedder later (say, an Ollama-backed
`nomic-embed-text` wrapper), you would create a new class implementing these
two methods — and nothing else in the codebase would need to change.

### Your task

In `rag/embeddings.py`, implement:

1. `tokenize(text)` — lowercase + alphanumeric tokens. One line.
2. `TfIdfEmbedder.fit(corpus)` — build the IDF table.
3. `TfIdfEmbedder.embed(text)` — return the L2-normalised sparse vector.

#### Common bugs to avoid

* **Counting occurrences instead of documents.** `df("the") = 5` because
  `"the"` appears in 5 *documents*, not because it appears 5 *times*.
* **Forgetting to normalise.** If your test sees `score > 1` or wildly
  different scores for paraphrases, you probably forgot the L2 normalisation.
* **Dividing by a zero norm.** If a query has no in-vocabulary tokens, every
  weight is zero and `||v|| = 0`. Return `{}` rather than crashing.

### Run the tests

```bash
pytest tests/test_embeddings.py -v
```

All 16 tests should pass.

### Sanity check (optional)

Open a Python REPL and try:

```python
from rag.embeddings import TfIdfEmbedder
e = TfIdfEmbedder()
e.fit(["the cat sat on the mat", "the dog ate the bone"])
v_cat = e.embed("cat on a mat")
v_dog = e.embed("dog with a bone")
print(v_cat)   # weight on 'cat' and 'mat' should dominate 'on'
print(v_dog)   # similarly for 'dog' and 'bone'
```

Notice how the high-IDF tokens (`cat`, `mat`, `dog`, `bone`) have larger
weights than the low-IDF token (`the`, `on`) — that is TF-IDF doing its job.

---

## Part 4 — Vector Store (`rag/vector_store.py`)

### The problem

Given a query vector `q` and a collection of stored vectors
`{v_1, v_2, ..., v_n}`, find the `k` vectors with the highest cosine
similarity to `q`.

### Cosine similarity

For two vectors `a, b`:

```
              a · b
cos(a, b) = ─────────────
            ||a|| · ||b||
```

Properties we rely on:

* **Range.** `cos ∈ [-1, 1]`. Since our TF-IDF weights are all non-negative,
  in practice `cos ∈ [0, 1]`.
* **1 means identical direction.** Doubling every weight of a vector does
  not change its direction, so it does not change the cosine.
* **0 means orthogonal.** No tokens in common ⇒ dot product is zero ⇒ cosine
  is zero.

Cosine on already-normalised vectors collapses to a dot product, which is
why Part 3 normalises. But your `cosine_similarity` function should still
divide by the norms — it must work even on un-normalised input, as the test
`test_unnormalised_vectors_still_yield_cosine` checks.

### The store

`InMemoryVectorStore` is a list of `EmbeddedChunk` objects plus a linear
`search`:

```python
def search(self, query, k):
    scored = [(cosine_similarity(query, e.vector), e.chunk) for e in self._entries]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [RetrievalResult(chunk=c, score=s) for s, c in scored[:k]]
```

That is essentially the reference implementation. Yours might look slightly
different (e.g. using `heapq.nlargest`, which is faster for small `k`) — both
are fine.

### Your task

In `rag/vector_store.py`, implement:

1. `cosine_similarity(a, b)` — handle zero-norm and empty-vector cases by
   returning `0.0` rather than dividing by zero.
2. `InMemoryVectorStore.add(embedded)` — append everything.
3. `InMemoryVectorStore.search(query, k)` — return at most `k` results,
   sorted by descending score. Handle `k <= 0` and an empty store.

### Run the tests

```bash
pytest tests/test_vector_store.py -v
```

All 13 tests should pass.

### Why "in-memory"? When would I need more?

Linear scan is `O(N · D)` per query, where `N` is the number of stored
vectors and `D` is the average vector density. For `N ≈ 10,000` and our
sparse TF-IDF vectors that is still milliseconds. For `N ≈ 10,000,000`
you would need approximate-nearest-neighbour indexes (FAISS, HNSW, IVF,
ScaNN). These are out of scope here, but the *interface* you implemented —
"give me top-k for this query vector" — is the same one those libraries
expose, so you could swap the store without rewriting the rest.

---

## Part 5 — Retriever (`rag/retriever.py`)

### The problem

Composing Part 3 and Part 4 into a single object that answers:

* "Given these chunks, build an index." (`index`)
* "Given this query string, what are the top-`k` chunks?" (`retrieve`)

### The composition

This part is mostly mechanical:

```python
def index(self, chunks):
    embedded = [EmbeddedChunk(chunk=c, vector=self.embedder.embed(c.text))
                for c in chunks]
    self.store.add(embedded)

def retrieve(self, query, k=4):
    q_vec = self.embedder.embed(query)
    return self.store.search(q_vec, k=k)
```

The skeleton also provides `index_corpus(chunks)` as a convenience — it fits
the embedder *and* indexes, in one call. You do not need to modify it.

### Why have a `Retriever` at all?

Two reasons:

1. **It owns the embedder.** The fundamental rule of RAG is "embed queries
   with the same model you embedded chunks with." Bundling them in one
   object makes that hard to get wrong.
2. **It is the seam.** The downstream `RagPipeline` only ever calls
   `retriever.retrieve(...)`. If you later swap TF-IDF for a dense embedder
   plus FAISS, you only change the retriever; the pipeline does not know.

### Your task

Implement `Retriever.index` and `Retriever.retrieve` in `rag/retriever.py`.

### Run the tests

```bash
pytest tests/test_retriever.py -v
```

The interesting tests here are the ones that check ranking actually works:

* "How do I get a refund?" → top result is from `refunds`.
* "How do I look up a user by id?" → top result is from `users`.
* "Where do I put my API key?" → top result is from `auth`.

If any of these fail, your TF-IDF implementation in Part 3 is suspect, even
if its own tests pass.

---

## Part 6 — Prompt assembly & end-to-end pipeline

### The problem

We have a retriever. Now we need to:

1. Render the retrieved chunks into a prompt the LLM can read.
2. Call the LLM.
3. Wire it all into a one-call `answer(question)` API.

### The prompt template

We use a deliberately rigid format:

```
Context:
[users_api:0] GET /users/{id} returns the user with the given id ...
[users_api:1] PATCH /users/{id} updates the name and/or email ...

Question: How do I update a user's email?
```

Two design choices worth calling out:

* **Citations.** Each chunk is prefixed with its id in square brackets. The
  system prompt instructs the model to cite which chunk each fact came from
  (`[users_api:0]`). This is how you get checkable, attributable answers
  instead of confident hallucination.
* **The "no context" branch.** If retrieval returns nothing, we still emit
  a `Context: (no context retrieved)` block. This makes the LLM aware that
  the absence is intentional, not an accident, and the system prompt's
  fallback rule ("reply 'I don't know based on the provided context.'")
  kicks in cleanly.

### The system prompt

```
You are a careful assistant. Answer the user's question using ONLY the
information in the supplied context. If the context does not contain the
answer, reply exactly: "I don't know based on the provided context."
Cite the source id in square brackets after each fact, e.g. [users_api:0].
```

The tests assume this prompt is used verbatim, so do not edit
`DEFAULT_SYSTEM_PROMPT` while you are getting them green. Once everything
passes, feel free to experiment with the prompt in the demo and observe how
the answers change.

### The `LanguageModel` protocol

```python
class LanguageModel(Protocol):
    def __call__(self, system: str, user: str) -> str: ...
```

Anything callable with this signature is a language model. The skeleton
provides `OllamaChatModel`, which wraps `ollama.chat`, for the demo. The
test suite uses a `FakeLLM` (see `tests/conftest.py`) that records calls
and returns scripted strings. That is how we can test the pipeline without
actually invoking an LLM.

### Your task

Implement three things:

1. `format_rag_prompt(question, results)` in `rag/generation.py`.
2. `RagPipeline.index_documents(docs)` in `rag/pipeline.py`.
3. `RagPipeline.answer(question, k)` in `rag/pipeline.py`.

### Run the tests

```bash
pytest tests/test_pipeline.py -v
```

This is the integration suite — if it passes, your whole RAG stack works.

### Run the whole suite

```bash
pytest
```

You should now see something like:

```
tests/test_chunking.py    .............. [ 21%]
tests/test_embeddings.py  ................ [ 45%]
tests/test_vector_store.py .............  [ 65%]
tests/test_retriever.py   ........        [ 78%]
tests/test_pipeline.py    ........        [100%]
======== N passed in 0.42s ========
```

---

## Part 7 — Run the demo against Ollama

Once the suite is green, run the end-to-end demo on the sample corpus
(`data/corpus/`):

```bash
# from week1/rag/
python run_demo.py
```

The script:

1. Loads every `*.md` file in `data/corpus/` as a `Document`.
2. Builds a `RagPipeline` with `TfIdfEmbedder` + `OllamaChatModel`.
3. Indexes the documents.
4. Asks a handful of questions and prints the retrieved chunks and the
   model's answer side-by-side.

You will need [Ollama](https://ollama.com/) installed and the
`llama3.1:8b` model pulled (see `week1/README.md` for setup).

### Things to try

* **Ask a question the corpus answers.** "How do I authenticate to the API?"
  → the model should produce an extractive answer with a `[authentication:N]`
  citation.
* **Ask a question the corpus does not answer.** "What is the SLA on
  customer support response time?" → the model should reply exactly
  `"I don't know based on the provided context."` Compare with what
  happens if you remove the retrieval step entirely (the LLM will gladly
  make something up).
* **Tweak `k`.** Set `k=1` and ask a question whose answer spans two
  chunks — watch the answer degrade. Set `k=8` and watch the prompt get
  noisier; sometimes more context hurts.
* **Tweak `chunk_size` / `chunk_overlap`.** Very small chunks (≤ 20 tokens)
  fragment the API docs to the point that no single chunk contains a full
  endpoint. Very large chunks (≥ 200) blur topic boundaries.

### Stretch goals (optional)

These are not graded but make for good follow-up exploration:

* **Dense embeddings.** Write an `OllamaEmbedder` that implements the
  `Embedder` protocol using `ollama.embeddings(model="nomic-embed-text",
  prompt=text)`. Swap it into the demo. Nothing else should need to change.
* **Hybrid retrieval.** Combine TF-IDF scores with dense-embedding scores
  (`score = α · cos_tfidf + (1 − α) · cos_dense`) and observe which queries
  benefit.
* **Re-ranking.** After retrieving the top-20 with TF-IDF, ask a small LLM
  to re-rank them by relevance to the question, then take the top-3 for the
  final answer prompt.
* **Persistence.** Pickle the vector store to disk so the demo does not
  re-index on every run.

---

## Submission

* Make sure every test passes: `pytest` from `week1/rag/`.
* Commit your filled-in versions of `chunking.py`, `embeddings.py`,
  `vector_store.py`, `retriever.py`, `generation.py`, and `pipeline.py`.
* Include a 1-paragraph note in a top-level comment of `run_demo.py`
  summarising one observation from Part 7 (e.g. "with `k=1` the
  refund-policy question fails because the answer spans two chunks").

That is it — you have built a working RAG system from first principles.
