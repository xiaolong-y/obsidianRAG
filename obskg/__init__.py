"""
obskg
======

This Python package contains modules for integrating Obsidian‑based knowledge
bases with large language models (LLMs).  The goal is to provide a modular
architecture that supports ingesting, indexing and querying Markdown notes
stored in Obsidian vaults.  The package is designed to be agnostic to the
choice of language model and vector database, allowing you to swap providers
depending on cost, performance and privacy requirements.

Modules
-------

* `vault` – scan one or more Obsidian vaults and yield note metadata.
* `embeddings` – generate dense vector embeddings using cloud or local models
  (OpenAI, Anthropic, xAI or open‑source models via HuggingFace).
* `vectorstore` – build and query a similarity index (defaults to the FAISS
  library) to enable retrieval‑augmented generation (RAG) workflows.
* `summarize` – produce summaries or other distilled representations of
  documents using LLM completions.
* `cache` – simple caching utilities to reuse embeddings and LLM responses
  across runs, reducing cost and latency.
* `scheduler` – helpers for scheduling background ingestion on macOS (via
  `cron` or `launchd`) and for monitoring vaults in real time using
  `watchdog`.

The package can serve as the foundation for building advanced knowledge
processing pipelines.  It is intended to be paired with higher‑level workflow
orchestration and knowledge structure design layers (for example, the
productivity methods that Claude Opus 4.1 will provide).  By separating the
concerns of data ingestion and LLM integration from note‑taking semantics, the
architecture remains flexible and cost‑efficient.
"""

__all__ = [
    "vault",
    "embeddings",
    "vectorstore",
    "summarize",
    "cache",
    "scheduler",
]