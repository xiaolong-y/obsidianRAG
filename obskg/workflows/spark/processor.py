"""Processor phase of the SPARK research workflow.

The processor transforms raw content into smaller, more digestible
components known as atomic notes.  Each atomic note represents a single
idea or concept extracted from the source material.  The processor
performs summarisation and auto‑tagging, then suggests potential
connections between notes.

This skeleton implementation demonstrates the API but does not
include sophisticated NLP models.  You can integrate LLMs or other
machine learning libraries to perform summarisation and tagging.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Dict


@dataclass
class AtomicNote:
    """Simple representation of an atomic note.

    Attributes
    ----------
    content : str
        The text of the note.
    tags : list[str]
        Automatically generated tags or keywords.
    connections : list[str]
        Suggested IDs of related notes.
    """

    content: str
    tags: List[str]
    connections: List[str]


class SPARKProcessor:
    """Transform raw content into atomic notes.

    This class implements the Process phase of the SPARK workflow.  It
    extracts short summaries from raw documents, assigns tags using
    simple heuristics and proposes connections based on overlapping
    keywords.  For demonstration, the summarisation here simply
    truncates the input and the tagging splits on whitespace.
    """

    def process(self, raw_content: str) -> List[AtomicNote]:
        """Process a single raw content string.

        Parameters
        ----------
        raw_content : str
            The unprocessed source text.

        Returns
        -------
        list of AtomicNote
            A list of atomic notes extracted from the content.
        """
        if not raw_content:
            return []
        # Naïve split into paragraphs as atomic notes
        paragraphs = [p.strip() for p in raw_content.split("\n\n") if p.strip()]
        notes: List[AtomicNote] = []
        for para in paragraphs:
            # Truncate to first 150 words as a summary
            words = para.split()
            summary = " ".join(words[:150])
            # Simple auto‑tagging: take top 3 unique words >4 characters
            tokens = [w.strip(".,;:!?()").lower() for w in words]
            # Filter tokens by length and alphabetic
            candidates = [t for t in tokens if len(t) > 4 and t.isalpha()]
            unique_candidates = []
            for tok in candidates:
                if tok not in unique_candidates:
                    unique_candidates.append(tok)
                if len(unique_candidates) >= 3:
                    break
            tags = unique_candidates
            # For connections, we leave empty; to be filled by analyzer
            notes.append(AtomicNote(content=summary, tags=tags, connections=[]))
        return notes

    def auto_tag(self, note: AtomicNote) -> List[str]:
        """Assign tags to an existing note using simple heuristics.

        Parameters
        ----------
        note : AtomicNote
            The note to tag.

        Returns
        -------
        list of str
            A list of tag strings with no duplicates.
        """
        words = note.content.split()
        tokens = [w.strip(".,;:!?()").lower() for w in words]
        candidates = [t for t in tokens if len(t) > 4 and t.isalpha()]
        tags: List[str] = []
        for tok in candidates:
            if tok not in tags:
                tags.append(tok)
            if len(tags) >= 5:
                break
        return tags