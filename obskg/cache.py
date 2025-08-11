"""
Simple caching utilities for embeddings and LLM responses.

Caching repeated calls can drastically reduce the number of API requests to
LLMs and embedding services, saving money and improving latency.  For
example, research on semantic caching shows that storing embeddings of user
queries and retrieving semantically similar responses can reduce API calls by
over 60%【553445371674628†L69-L86】.  This module implements a minimal cache
using `sqlite3` and JSON for persistence.  It is not meant for
production‑grade traffic but serves as a demonstration of how to structure
cache lookups in a RAG pipeline.

Two caches are provided:

* `EmbeddingCache` – maps text hashes to vector embeddings.  Uses SHA256 to
  derive keys and stores vectors as BLOBs via Python’s `pickle` module.
* `ResponseCache` – maps a prompt string (or another fingerprint) to a
  generated response.  Stores responses as plain text.

These caches support an optional time‑to‑live (TTL) value to expire entries.
"""

from __future__ import annotations

import hashlib
import json
import pickle
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Tuple

import numpy as np


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class EmbeddingCache:
    path: Path
    ttl: Optional[int] = None  # Time to live in seconds

    def __post_init__(self) -> None:
        self.conn = sqlite3.connect(str(self.path))
        cur = self.conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS embeddings (key TEXT PRIMARY KEY, value BLOB, timestamp REAL)"
        )
        self.conn.commit()

    def get(self, text: str) -> Optional[Sequence[float]]:
        key = _hash_text(text)
        cur = self.conn.cursor()
        cur.execute("SELECT value, timestamp FROM embeddings WHERE key=?", (key,))
        row = cur.fetchone()
        if not row:
            return None
        value_blob, ts = row
        if self.ttl is not None and (time.time() - ts) > self.ttl:
            # expired
            cur.execute("DELETE FROM embeddings WHERE key=?", (key,))
            self.conn.commit()
            return None
        try:
            return pickle.loads(value_blob)
        except Exception:
            return None

    def set(self, text: str, vector: Sequence[float]) -> None:
        key = _hash_text(text)
        data = pickle.dumps(vector)
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO embeddings (key, value, timestamp) VALUES (?, ?, ?)",
            (key, data, time.time()),
        )
        self.conn.commit()


@dataclass
class ResponseCache:
    path: Path
    ttl: Optional[int] = None

    def __post_init__(self) -> None:
        self.conn = sqlite3.connect(str(self.path))
        cur = self.conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS responses (key TEXT PRIMARY KEY, value TEXT, timestamp REAL)"
        )
        self.conn.commit()

    def get(self, prompt: str) -> Optional[str]:
        cur = self.conn.cursor()
        cur.execute("SELECT value, timestamp FROM responses WHERE key=?", (_hash_text(prompt),))
        row = cur.fetchone()
        if not row:
            return None
        value, ts = row
        if self.ttl is not None and (time.time() - ts) > self.ttl:
            # Expired
            cur.execute("DELETE FROM responses WHERE key=?", (_hash_text(prompt),))
            self.conn.commit()
            return None
        return value

    def set(self, prompt: str, value: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO responses (key, value, timestamp) VALUES (?, ?, ?)",
            (_hash_text(prompt), value, time.time()),
        )
        self.conn.commit()


@dataclass
class SemanticResponseCache:
    """Semantic cache for mapping input embeddings to LLM responses.

    Traditional response caches rely on exact string matching: the prompt is
    hashed and used as a key into a table.  This works well when the same
    prompt is repeated verbatim, but fails to capture semantically similar
    queries.  Semantic caching instead stores the embedding of each prompt
    alongside the response and performs a nearest‑neighbour search at
    retrieval time.  If a previously stored embedding is sufficiently
    similar (cosine similarity above a threshold), its response can be
    reused.  This can reduce repeated LLM calls even when users rephrase
    their requests.

    Attributes
    ----------
    path : Path
        SQLite database path.
    threshold : float, optional
        Cosine similarity threshold for a cache hit.  Default 0.95.
    ttl : int | None
        Optional time‑to‑live in seconds.  Entries older than ``ttl`` are
        evicted on lookup.
    """

    path: Path
    threshold: float = 0.95
    ttl: Optional[int] = None

    def __post_init__(self) -> None:
        self.conn = sqlite3.connect(str(self.path))
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS semantic_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vector BLOB NOT NULL,
                response TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
            """
        )
        self.conn.commit()

    def _load_vectors(self) -> Tuple[np.ndarray, list[str], list[float]]:
        """Load all cached embeddings, responses and timestamps.

        Returns
        -------
        tuple
            A tuple of (matrix, responses, timestamps) where ``matrix`` is a
            2D ``numpy.ndarray`` of shape (n, d), ``responses`` is a list of
            response strings and ``timestamps`` is a list of float epoch
            seconds.  If no entries exist the matrix will have shape
            ``(0, 0)``.
        """
        cur = self.conn.cursor()
        cur.execute("SELECT vector, response, timestamp FROM semantic_cache")
        rows = cur.fetchall()
        if not rows:
            return np.empty((0, 0)), [], []
        vectors = []
        responses = []
        timestamps = []
        for vec_blob, resp, ts in rows:
            try:
                vec = pickle.loads(vec_blob)
            except Exception:
                continue
            vectors.append(vec)
            responses.append(resp)
            timestamps.append(ts)
        # Convert to array of floats
        matrix = np.array(vectors, dtype=float)
        return matrix, responses, timestamps

    def get(self, embedding: Sequence[float]) -> Optional[str]:
        """Retrieve the cached response whose embedding is most similar.

        Parameters
        ----------
        embedding : Sequence[float]
            Embedding vector of the query.

        Returns
        -------
        str | None
            Cached response if a similar embedding above the threshold is
            found and the entry is not expired; otherwise ``None``.
        """
        emb = np.array(embedding, dtype=float)
        # Load existing vectors and responses
        matrix, responses, timestamps = self._load_vectors()
        if matrix.size == 0:
            return None
        # Compute cosine similarities: (v · e) / (||v|| * ||e||)
        # Add small epsilon to avoid division by zero
        try:
            e_norm = np.linalg.norm(emb) + 1e-9
            v_norms = np.linalg.norm(matrix, axis=1) + 1e-9
            sims = (matrix @ emb) / (v_norms * e_norm)
        except Exception:
            return None
        # Find index of highest similarity
        idx = int(np.argmax(sims))
        sim = float(sims[idx])
        # Check threshold and TTL
        if sim >= self.threshold:
            ts = timestamps[idx]
            if self.ttl is not None and (time.time() - ts) > self.ttl:
                # expired entry; remove
                cur = self.conn.cursor()
                cur.execute("DELETE FROM semantic_cache WHERE rowid=?", (idx + 1,))
                self.conn.commit()
                return None
            return responses[idx]
        return None

    def set(self, embedding: Sequence[float], response: str) -> None:
        """Store an embedding and its response in the semantic cache.

        Parameters
        ----------
        embedding : Sequence[float]
            The embedding vector for the prompt.
        response : str
            The LLM response text.
        """
        vec_blob = pickle.dumps(list(embedding))
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO semantic_cache (vector, response, timestamp) VALUES (?, ?, ?)",
            (vec_blob, response, time.time()),
        )
        self.conn.commit()

    def warm_up(self, entries: Sequence[Tuple[Sequence[float], str]]) -> None:
        """Bulk load entries into the semantic cache.

        This method can be used to prepopulate the cache from existing
        historical data (e.g. commonly asked queries and their answers),
        improving hit rates and reducing initial API usage.

        Parameters
        ----------
        entries : Sequence[tuple]
            A sequence of (embedding, response) tuples.
        """
        cur = self.conn.cursor()
        for emb, resp in entries:
            try:
                vec_blob = pickle.dumps(list(emb))
                cur.execute(
                    "INSERT INTO semantic_cache (vector, response, timestamp) VALUES (?, ?, ?)",
                    (vec_blob, resp, time.time()),
                )
            except Exception:
                continue
        self.conn.commit()