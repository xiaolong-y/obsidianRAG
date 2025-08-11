"""
Document summarization helpers.

This module offers a thin wrapper around large language models for
summarizing documents or answering questions.  It supports multiple
providers and includes a simple caching mechanism to avoid redundant
requests (see `obskg.cache`).  When summarizing long documents, the
content is automatically chunked to respect model context limits and then
combined with a map‑reduce pattern.

Research underpinning summary writing suggests that actively distilling
information into your own words helps with comprehension and recall.  Notes
apps should therefore encourage summarization rather than verbatim copying
【126204223791625†L269-L339】.  By generating AI‑assisted summaries, we
provide scaffolding while still prompting users to engage with the material.

Example
-------

```python
from obskg.summarize import summarize_document
from obskg.embeddings import EmbeddingConfig

summary = summarize_document(
    text=open("long_note.md").read(),
    config=EmbeddingConfig(provider="openai", model="gpt-4o", api_key=OPENAI_API_KEY),
    max_tokens=1024,
    prompt="Summarize the key insights from this note in three bullet points."
)
print(summary)
```
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Callable, List, Optional

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore


logger = logging.getLogger(__name__)


@dataclass
class SummarizationConfig:
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 1024
    system_prompt: Optional[str] = None


def _chunk_text(text: str, max_chars: int = 4000) -> List[str]:
    """Chunk a long string into approximately equal parts without splitting words."""
    words = text.split()
    chunks: List[str] = []
    current: List[str] = []
    count = 0
    for w in words:
        count += len(w) + 1
        if count > max_chars:
            chunks.append(" ".join(current))
            current = [w]
            count = len(w) + 1
        else:
            current.append(w)
    if current:
        chunks.append(" ".join(current))
    return chunks


def _call_openai(prompt: str, config: SummarizationConfig) -> str:
    if OpenAI is None:
        raise RuntimeError("OpenAI SDK is not installed")
    if not config.api_key:
        raise ValueError("OpenAI API key is required for summarization")
    client = OpenAI(api_key=config.api_key)
    messages = []
    if config.system_prompt:
        messages.append({"role": "system", "content": config.system_prompt})
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model=config.model,
        messages=messages,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )
    return response.choices[0].message.content  # type: ignore


def summarize_document(
    text: str,
    config: SummarizationConfig,
    max_tokens: int = 1024,
    prompt: str = "Summarize the following text."
) -> str:
    """Summarize a long document using a map‑reduce approach.

    The input text is split into smaller chunks to satisfy the context window
    limits of the underlying model (OpenAI GPT models have limits between
    16 k and 400 k tokens depending on the tier).  Each chunk is summarized
    separately and then the summaries are concatenated and summarized again
    to produce a final result.

    Parameters
    ----------
    text:
        The document to summarize.
    config:
        SummarizationConfig specifying the model and provider.
    max_tokens:
        Maximum tokens for each individual summarization call.
    prompt:
        The user prompt describing how the text should be summarized.

    Returns
    -------
    A string containing the final summary.
    """
    # Heuristic to approximate character limit for given max_tokens (1 token ~ 4 chars)
    approx_chars_per_chunk = (max_tokens - 100) * 4
    chunks = _chunk_text(text, max_chars=approx_chars_per_chunk)
    logger.debug("Splitting document into %d chunks", len(chunks))
    partial_summaries: List[str] = []
    for i, chunk in enumerate(chunks):
        chunk_prompt = f"{prompt}\n\n{chunk}"
        summary = _call_openai(chunk_prompt, config)
        partial_summaries.append(summary.strip())
    if len(partial_summaries) == 1:
        return partial_summaries[0]
    # Reduce: summarize the summaries
    combined = "\n\n".join(partial_summaries)
    final_prompt = f"Combine the following summaries into a coherent summary:\n\n{combined}"
    return _call_openai(final_prompt, config).strip()