"""
Vault scanning and document ingestion.

This module provides utility functions for traversing one or more Obsidian
vaults on disk and collecting Markdown files along with basic metadata.  An
Obsidian vault is simply a directory tree where each note is stored as a
`.md` file.  The functions here extract the note’s title, path, front matter
(YAML metadata), and body content.

Example
-------

```python
from pathlib import Path
from obskg.vault import iter_notes

vault_path = Path("~/Documents/Obsidian/MyVault").expanduser()
for note in iter_notes(vault_path):
    print(note["title"], len(note["content"].split()))
```

Design considerations
---------------------

* Multi‑vault support: the functions accept a list of root directories.  Each
  note record includes its vault name so you can index multiple vaults
  without collisions.
* Front matter parsing: notes often include YAML front matter enclosed by
  triple dashes (`---`).  This module parses the front matter into a
  dictionary using PyYAML (optional dependency).
* Unicode normalization: note contents are normalized to NFC to ensure
  consistent embedding generation.
* Pluggable metadata extraction: you can customize or extend the extraction
  behaviour via callbacks.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


@dataclass
class Note:
    """A representation of a single Markdown note in an Obsidian vault."""

    vault: str
    path: Path
    title: str
    content: str
    front_matter: Dict[str, object]


def _parse_front_matter(text: str) -> Tuple[Dict[str, object], str]:
    """Extract YAML front matter from a Markdown document.

    Parameters
    ----------
    text:
        The raw Markdown content.

    Returns
    -------
    A tuple of the parsed front matter dictionary and the body text with
    front matter removed.  If no front matter is present or PyYAML is not
    installed, an empty dict is returned and the original text is returned
    unchanged.
    """
    if not text.startswith("---\n"):
        return {}, text
    if yaml is None:
        return {}, text
    # Split on the second '---' line
    parts = text.split("\n---", 1)
    if len(parts) < 2:
        return {}, text
    front_matter_text = parts[0].strip("-\n")
    body = parts[1].lstrip('\n')
    try:
        data = yaml.safe_load(front_matter_text) or {}
    except Exception:
        data = {}
    return data, body


def iter_notes(vaults: Iterable[Path]) -> Iterator[Note]:
    """Yield Note objects for all Markdown files in the provided vaults.

    Parameters
    ----------
    vaults:
        A collection of `Path` objects representing root directories of
        Obsidian vaults.

    Yields
    ------
    Note
        An object containing the vault name, file path, title and content of
        each Markdown file.  Vault name defaults to the directory name of
        the root path.
    """
    md_pattern = re.compile(r"\.md$", re.IGNORECASE)
    for root in vaults:
        vault_name = root.name
        for path in root.rglob("*.md"):
            if not md_pattern.search(path.name):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, FileNotFoundError):
                continue
            front, body = _parse_front_matter(text)
            # Normalize to NFC for consistent embeddings
            body_nfc = unicodedata.normalize("NFC", body)
            title = front.get("title") if isinstance(front.get("title"), str) else path.stem
            yield Note(
                vault=vault_name,
                path=path,
                title=title,
                content=body_nfc,
                front_matter=front,
            )