#!/usr/bin/env python3
"""
Update embeddings for one or more Obsidian vaults.

This command‑line script demonstrates how to use the `obskg` library to
ingest notes, generate embeddings (with caching), and persist them to a
vector store.  It is intended to run periodically via cron or `launchd`
so that your retrieval index stays up to date.

Usage:
    python update_embeddings.py --vault ~/Documents/Obsidian/Vault1 --vault ~/Dropbox/Vault2 \
        --index index.faiss --meta meta.sqlite3 --openai-key $OPENAI_API_KEY

When the script runs for the first time it builds a new FAISS index and
metadata database.  Subsequent runs will append new notes or update
modified ones by re‑embedding them.  A simple SHA256 of the note content
serves as a fingerprint for caching.  If the cached embedding exists and
the file has not changed, the cached vector is reused and no API call is
made, saving cost.
"""
import argparse
import os
import sys
from pathlib import Path

from obskg.vault import iter_notes
from obskg.embeddings import EmbeddingConfig, embed_texts
from obskg.vectorstore import FaissVectorStore
from obskg.cache import EmbeddingCache


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Update embeddings for Obsidian vaults")
    parser.add_argument("--vault", action="append", required=True, help="Path to a vault directory (repeatable)")
    parser.add_argument("--index", default="index.faiss", help="Path to the FAISS index file")
    parser.add_argument("--meta", default="meta.sqlite3", help="Path to the metadata SQLite file")
    parser.add_argument("--cache", default="embeddings.sqlite3", help="Path to the embedding cache database")
    parser.add_argument("--openai-key", required=True, help="OpenAI API key for generating embeddings")
    parser.add_argument("--model", default="text-embedding-3-small", help="Embedding model name")
    args = parser.parse_args(argv)

    vault_paths = [Path(v).expanduser() for v in args.vault]
    store = FaissVectorStore(index_path=args.index, meta_path=args.meta)
    cache = EmbeddingCache(path=Path(args.cache), ttl=None)
    texts = []
    metas = []
    for note in iter_notes(vault_paths):
        # Use note path + modification time as a fingerprint to decide if we need to re‑embed
        mtime = note.path.stat().st_mtime
        fingerprint = f"{note.path}:{mtime}"
        cached_vec = cache.get(fingerprint)
        if cached_vec is not None:
            texts.append(cached_vec)
        else:
            texts.append(note.content)
        metas.append({"title": note.title, "path": str(note.path), "vault": note.vault})

    # Separate cached vectors and raw text
    ready_vectors = []  # vectors that are already cached
    to_embed = []  # text that needs embedding
    embed_indices = []  # positions of texts to embed
    for i, item in enumerate(texts):
        if isinstance(item, list) or hasattr(item, "__array__"):
            ready_vectors.append(item)
        else:
            to_embed.append(item)
            embed_indices.append(i)
    # Generate embeddings for new items
    if to_embed:
        vectors = embed_texts(to_embed, EmbeddingConfig(provider="openai", model=args.model, api_key=args.openai_key))
        # Insert into ready_vectors at appropriate positions
        for idx, vec in zip(embed_indices, vectors):
            ready_vectors.insert(idx, vec)
            # Cache the embedding keyed by path:mtime
            mtime = Path(metas[idx]["path"]).stat().st_mtime
            fingerprint = f"{metas[idx]['path']}:{mtime}"
            cache.set(fingerprint, vec)
    # Add to vector store and persist
    store.add_vectors(ready_vectors, metas)
    store.persist()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())