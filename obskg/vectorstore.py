"""
Vector store utilities.

This module provides a simple wrapper around FAISS (Facebook AI Similarity
Search) for storing and querying document embeddings.  FAISS is an open
source library developed by Meta that enables efficient similarity search
across billions of vectors and is optimized for both speed and memory usage【473621506626253†L47-L54】【473621506626253†L119-L124】.

When FAISS is unavailable or if you prefer another vector database (e.g.,
Milvus, Pinecone, Qdrant), you can implement the same `BaseVectorStore`
interface and plug in your own backend.  The default implementation here
stores embeddings in RAM using FAISS and persists metadata in a
lightweight SQLite database via `sqlite3`.  This allows you to persist note
metadata (title, path, vault name) alongside the vector index.

Example
-------

```python
from obskg.vectorstore import FaissVectorStore
from obskg.embeddings import EmbeddingConfig, embed_texts
from obskg.vault import iter_notes

store = FaissVectorStore(index_path="index.faiss", meta_path="meta.sqlite3")
texts = []
metas = []
for note in iter_notes([Path("~/Obsidian/MyVault").expanduser()]):
    texts.append(note.content)
    metas.append({"title": note.title, "path": str(note.path), "vault": note.vault})
vectors = embed_texts(texts, EmbeddingConfig(api_key=OPENAI_API_KEY))
store.add_vectors(vectors, metas)

# Query the store with a new question
q_vec = embed_texts(["How do I set up a reverse proxy?"], EmbeddingConfig(api_key=OPENAI_API_KEY))[0]
for score, meta in store.search(q_vec, top_k=5):
    print(score, meta["title"])
```
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence, Tuple

try:
    import faiss
except ImportError:  # pragma: no cover
    faiss = None  # type: ignore

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore


@dataclass
class BaseVectorStore:
    """Abstract base class for a vector store."""

    def add_vectors(self, vectors: Iterable[Sequence[float]], metadatas: Iterable[dict]) -> None:
        raise NotImplementedError

    def search(self, vector: Sequence[float], top_k: int = 5) -> List[Tuple[float, dict]]:
        raise NotImplementedError

    def persist(self) -> None:
        raise NotImplementedError


class FaissVectorStore(BaseVectorStore):
    """FAISS‐backed vector store with metadata persistence in SQLite."""

    def __init__(self, index_path: str, meta_path: str, dim: Optional[int] = None):
        if faiss is None:
            raise RuntimeError("faiss library is required for FaissVectorStore")
        if np is None:
            raise RuntimeError("numpy is required for FaissVectorStore")
        self.index_path = Path(index_path)
        self.meta_path = Path(meta_path)
        self.dim = dim
        self.index: Optional[faiss.IndexFlatIP] = None
        self.conn: Optional[sqlite3.Connection] = None
        self._load()

    def _load(self) -> None:
        # Load or initialize the FAISS index
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            self.dim = self.index.d
        elif self.dim is not None:
            self.index = faiss.IndexFlatIP(self.dim)
        else:
            # Will be set when the first vector is added
            self.index = None
        # Setup SQLite for metadata
        self.conn = sqlite3.connect(str(self.meta_path))
        cur = self.conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS metadata (id INTEGER PRIMARY KEY, title TEXT, path TEXT, vault TEXT, extra TEXT)"
        )
        self.conn.commit()

    def _ensure_index(self, dim: int) -> None:
        if self.index is None:
            self.index = faiss.IndexFlatIP(dim)
            self.dim = dim

    def add_vectors(self, vectors: Iterable[Sequence[float]], metadatas: Iterable[dict]) -> None:
        vec_list = list(vectors)
        meta_list = list(metadatas)
        if not vec_list:
            return
        # Determine dimensionality
        first_vec = vec_list[0]
        dim = len(first_vec)
        self._ensure_index(dim)
        # Convert to 2D NumPy array of shape (n, dim)
        arr = np.vstack([np.asarray(v, dtype=np.float32) for v in vec_list])
        # Normalize vectors for inner product search (convert to unit length)
        faiss.normalize_L2(arr)
        # Add to index; track the starting offset for metadata
        start_id = self.index.ntotal
        self.index.add(arr)
        # Insert metadata
        cur = self.conn.cursor()
        for i, meta in enumerate(meta_list):
            cur.execute(
                "INSERT INTO metadata (id, title, path, vault, extra) VALUES (?, ?, ?, ?, ?)",
                (start_id + i, meta.get("title"), meta.get("path"), meta.get("vault"), json_dumps(meta.get("extra"))),
            )
        self.conn.commit()

    def search(self, vector: Sequence[float], top_k: int = 5) -> List[Tuple[float, dict]]:
        if self.index is None:
            return []
        arr = np.asarray(vector, dtype=np.float32)[np.newaxis, :]
        faiss.normalize_L2(arr)
        distances, indices = self.index.search(arr, top_k)
        results: List[Tuple[float, dict]] = []
        cur = self.conn.cursor()
        for score, idx in zip(distances[0], indices[0]):
            cur.execute("SELECT title, path, vault, extra FROM metadata WHERE id=?", (int(idx),))
            row = cur.fetchone()
            if row:
                title, path, vault, extra = row
                results.append((float(score), {"title": title, "path": path, "vault": vault, "extra": json_loads(extra)}))
        return results

    def persist(self) -> None:
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_path))
        if self.conn is not None:
            self.conn.commit()
            self.conn.close()


def json_dumps(obj: Any) -> Optional[str]:  # pragma: no cover
    import json
    if obj is None:
        return None
    return json.dumps(obj)


def json_loads(s: Optional[str]) -> Any:  # pragma: no cover
    import json
    if s is None:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None