"""SPARK workflow pipeline.

This package contains the implementation of the SPARK method (Scan,
Process, Analyze, Refine, Produce) for research workflows.  Each phase
is encapsulated in its own module to facilitate testing and reuse.  The
``SPARKPipeline`` class orchestrates the phases in sequence and may be
invoked synchronously or asynchronously.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .scanner import SPARKScanner  # noqa: F401
from .processor import SPARKProcessor  # noqa: F401
from .analyzer import SPARKAnalyzer  # noqa: F401
from .refiner import SPARKRefiner  # noqa: F401
from .producer import SPARKProducer  # noqa: F401


class SPARKPipeline:
    """End‑to‑end coordinator for the SPARK workflow.

    Parameters
    ----------
    vault_path : str
        Path to the Obsidian vault that will receive notes produced by the
        SPARK pipeline.
    config : dict, optional
        Optional configuration settings for the scanner and other phases.
    """

    def __init__(self, vault_path: str, config: Optional[Dict[str, Any]] = None) -> None:
        self.vault_path = vault_path
        self.config = config or {}
        # Initialise each phase with its own config segment
        self.scanner = SPARKScanner(self.config.get("scanner", {}))
        self.processor = SPARKProcessor()
        self.analyzer = SPARKAnalyzer()
        self.refiner = SPARKRefiner()
        self.producer = SPARKProducer()

    async def run(self, trigger: str = "manual") -> Dict[str, Any]:
        """Execute the full pipeline asynchronously.

        Parameters
        ----------
        trigger : str
            A label indicating what triggered the pipeline (e.g. ``"manual"``,
            ``"scheduled"``).  Used for monitoring and logging.

        Returns
        -------
        dict
            A summary dictionary containing high‑level metrics (e.g. total
            processing time, cost, accuracy).  The structure is left
            intentionally loose to allow future expansion.
        """
        import time

        start = time.time()
        # 1. Scan for new content
        raw_contents = await self.scanner.scan_async()
        # 2. Process into atomic notes
        atomic_notes = []
        for content in raw_contents:
            atomic_notes.extend(self.processor.process(content))
        # 3. Analyze patterns and contradictions
        analysis_report = self.analyzer.analyze(atomic_notes)
        # 4. Refine results (human/AI collaboration)
        refined_notes = self.refiner.refine(analysis_report)
        # 5. Produce final notes or summaries
        produced = self.producer.produce(refined_notes, self.vault_path)
        end = time.time()
        return {
            "trigger": trigger,
            "num_sources": len(raw_contents),
            "num_atomic_notes": len(atomic_notes),
            "analysis_id": analysis_report.get("analysis_id"),
            "num_produced": len(produced),
            "tti": end - start,
        }