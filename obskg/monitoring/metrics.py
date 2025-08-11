"""Metrics collection utilities for the Obsidian‑LLM integration.

This module defines a ``MetricsCollector`` class which tracks key
performance indicators such as Time to Insight (TTI), Knowledge Reuse
Rate (KRR), Synthesis Velocity (SV), Cognitive Load Index (CLI) and
AI Augmentation Rate (AAR).  These metrics inform optimisation and
user experience improvements.

In this simplified version, metrics are stored in memory.  In a
production implementation you might persist metrics to a time‑series
database (e.g. InfluxDB) or expose them via a monitoring API.
"""

from __future__ import annotations

import time
from typing import Dict, List


class MetricsCollector:
    """Collect and report key performance indicators."""

    def __init__(self) -> None:
        self.metrics: Dict[str, List[float]] = {
            "TTI": [],
            "KRR": [],
            "SV": [],
            "CLI": [],
            "AAR": [],
        }

    def track_query(self, start_time: float, end_time: float, notes_accessed: int) -> None:
        """Record metrics for a single query.

        Parameters
        ----------
        start_time : float
            Epoch timestamp when the query began.
        end_time : float
            Epoch timestamp when the query finished.
        notes_accessed : int
            Number of notes retrieved from the vector store during the query.
        """
        duration = end_time - start_time
        # Time to Insight: raw duration in seconds
        self.metrics["TTI"].append(duration)
        # Knowledge Reuse Rate: ratio of cached responses used (placeholder)
        self.metrics["KRR"].append(0.0)
        # Synthesis Velocity: notes per second processed (placeholder)
        if duration > 0:
            self.metrics["SV"].append(notes_accessed / duration)
        else:
            self.metrics["SV"].append(0.0)
        # Cognitive Load Index: inverse of notes processed (simplified)
        self.metrics["CLI"].append(1.0 / max(1, notes_accessed))
        # AI Augmentation Rate: proportion of AI involvement (placeholder)
        self.metrics["AAR"].append(0.5)

    def generate_report(self) -> Dict[str, float]:
        """Summarise metrics for reporting.

        Returns
        -------
        dict
            A dictionary of average values for each tracked metric.
        """
        report = {}
        for key, values in self.metrics.items():
            if values:
                report[key] = sum(values) / len(values)
            else:
                report[key] = 0.0
        return report