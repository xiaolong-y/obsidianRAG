"""Hybrid task routing for combining human and AI contributions.

This module defines a ``HybridTaskRouter`` class that routes tasks between
human operators and AI models based on the task type and estimated
complexity.  Research suggests that an optimal division of labour can
reduce processing time by up to 45 %, provided that tasks are assigned
appropriately according to their nature and difficulty.

Tasks that involve rote processing (e.g. transcription, tag generation or
duplicate detection) can often be handled by AI with high accuracy.  In
contrast, tasks requiring critical thinking, ethical judgement or creative
insight may be better suited to humans.  Some tasks benefit from a
collaborative approach where the AI proposes drafts and the human
refines them.

The router exposes a simple ``route`` method that takes a ``task_type``
string and a numeric ``complexity_score`` (0.0–1.0).  It returns a
dictionary indicating which agent should handle the task (``"ai"``,
``"human"`` or ``"collaborative"``) and a confidence score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class HybridTaskRouter:
    """Route tasks to human or AI based on complexity and type.

    Attributes
    ----------
    ai_first_tasks : List[str]
        Task identifiers that are generally suited to AI.  These are
        typically repetitive or pattern‑based tasks where the AI performs
        with high accuracy.
    human_first_tasks : List[str]
        Task identifiers that are better suited to human judgement.  These
        tasks often require nuance, creativity or ethical considerations.
    """

    ai_first_tasks: List[str] = field(default_factory=lambda: [
        "transcription",
        "tag_generation",
        "duplicate_detection",
        "basic_summarization",
        "pattern_detection",
    ])
    human_first_tasks: List[str] = field(default_factory=lambda: [
        "critical_thinking",
        "creative_connections",
        "ethical_decisions",
        "quality_validation",
        "personal_reflection",
    ])

    def route(self, task_type: str, complexity_score: float) -> Dict[str, float]:
        """Determine the handler for a given task.

        Parameters
        ----------
        task_type : str
            A symbolic identifier describing the nature of the task.  This
            could be provided by higher‑level workflow logic (e.g.
            ``"transcription"`` or ``"critical_thinking"``).
        complexity_score : float
            A value between 0.0 and 1.0 indicating the estimated difficulty
            of the task.  Lower values denote simple tasks, while higher
            values indicate complex, nuanced tasks.

        Returns
        -------
        Dict[str, float]
            A dictionary with keys ``"handler"`` and ``"confidence"``.
            ``"handler"`` is either ``"ai"``, ``"human"`` or
            ``"collaborative"``.  ``"confidence"`` is a value between 0.0
            and 1.0 reflecting the router’s confidence in its decision.
        """
        handler: str
        confidence: float
        # Determine initial assignment based on task type
        if task_type in self.ai_first_tasks:
            handler = "ai"
            base_confidence = 0.8
        elif task_type in self.human_first_tasks:
            handler = "human"
            base_confidence = 0.8
        else:
            # Unknown task: prefer collaborative approach
            handler = "collaborative"
            base_confidence = 0.5
        # Adjust confidence based on complexity
        # Highly complex tasks lean towards human or collaborative routing
        if complexity_score < 0.3:
            # Simple task: AI confident
            if handler == "ai":
                confidence = min(1.0, base_confidence + 0.15)
            elif handler == "human":
                confidence = max(0.0, base_confidence - 0.3)
            else:
                confidence = base_confidence
        elif complexity_score > 0.7:
            # Complex task: human confident
            if handler == "human":
                confidence = min(1.0, base_confidence + 0.15)
            elif handler == "ai":
                # Suggest collaborative for complex AI‑first tasks
                handler = "collaborative"
                confidence = 0.6
            else:
                confidence = base_confidence
        else:
            # Moderate complexity: collaborative recommended
            if handler != "collaborative":
                handler = "collaborative"
                confidence = 0.7
            else:
                confidence = base_confidence
        return {"handler": handler, "confidence": round(confidence, 2)}