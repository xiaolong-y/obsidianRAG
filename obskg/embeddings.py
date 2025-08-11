"""
Embedding generation helpers.

This module abstracts away the details of generating dense vector
representations for note content.  It provides a unified interface for
embedding notes via different providers.  Current implementations include
OpenAI's embedding models and a local fallback using HuggingFace models
loaded via `sentence_transformers`.  Support for Anthropic and xAI can be
added by implementing appropriate API calls.

The functions here return NumPy arrays for interoperability with vector
stores like FAISS.  If NumPy is unavailable, a list of floats is returned.

Cost considerations
-------------------

Embedding generation often constitutes a large portion of the cost when
building a retrieval‑augmented generation (RAG) system.  Using cheaper
models such as OpenAI's `text-embedding-3-small` (priced at $0.02 per 1M
tokens【25145589279390†L90-L106】) can drastically reduce expenses compared
with older models like `ada-002`.  When privacy is paramount or API costs
are prohibitive, local models can be used at the expense of longer compute
times and higher memory usage.  To further reduce costs, embedding vectors
should be cached and reused across sessions (see `obskg.cache`).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional, Sequence

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover
    SentenceTransformer = None  # type: ignore


logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    provider: str = "openai"
    model: str = "text-embedding-3-small"
    api_key: Optional[str] = None
    device: Optional[str] = None  # used for local models


def _to_array(vec: Sequence[float]):
    if np is not None:
        return np.array(vec, dtype=np.float32)
    return list(vec)


@lru_cache(maxsize=None)
def _load_local_model(model_name: str, device: Optional[str] = None):
    """Load a local sentence transformer model (cached)."""
    if SentenceTransformer is None:
        raise RuntimeError("sentence_transformers is not installed")
    return SentenceTransformer(model_name, device=device)


def embed_texts(texts: List[str], config: EmbeddingConfig) -> List[Sequence[float]]:
    """Embed a list of strings using the specified provider/model.

    Parameters
    ----------
    texts:
        A list of documents or sentences to embed.
    config:
        Configuration specifying the provider and model.  For OpenAI, an API
        key must be provided.  For local models, `device` can be set to
        "cpu" or a CUDA device string.

    Returns
    -------
    List of embedding vectors (NumPy arrays if NumPy is installed, otherwise
    lists of floats).

    Notes
    -----
    This function does not implement batching or rate limiting.  When
    embedding a large corpus, callers should chunk the input and sleep
    between batches to respect provider quotas and avoid timeouts.
    """
    if not texts:
        return []
    if config.provider.lower() == "openai":
        if OpenAI is None:
            raise RuntimeError("OpenAI SDK is not installed")
        if not config.api_key:
            raise ValueError("OpenAI API key must be supplied when using OpenAI embeddings")
        client = OpenAI(api_key=config.api_key)
        # The OpenAI embeddings API accepts up to 8191 input tokens per call.
        # We rely on the SDK to batch internally when given a list.
        response = client.embeddings.create(input=texts, model=config.model)
        vectors = [record.embedding for record in response.data]
        return [_to_array(v) for v in vectors]
    elif config.provider.lower() == "local":
        # Use a local sentence transformer (e.g., all-MiniLM-L6-v2)
        model = _load_local_model(config.model, device=config.device)
        vectors = model.encode(texts, convert_to_numpy=np is not None)
        if np is None:
            return [list(v) for v in vectors]
        return [v.astype(np.float32) for v in vectors]
    else:
        raise ValueError(f"Unsupported embedding provider: {config.provider}")