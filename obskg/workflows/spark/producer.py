"""Producer phase of the SPARK research workflow.

This module contains the ``SPARKProducer`` class responsible for
generating final outputs (e.g. Markdown files, Obsidian pages, JSON
export) from the refined analysis.  The produced notes are saved to the
specified vault path or returned to the caller.

In this simplified implementation, the producer writes each refined
report as a JSON file to the vault directory.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


class SPARKProducer:
    """Produce final artefacts from refined analysis."""

    def produce(self, refined_reports: Iterable[Dict[str, Any]], vault_path: str) -> List[Path]:
        """Write refined reports into the vault as JSON files.

        Parameters
        ----------
        refined_reports : Iterable[dict]
            The results of the refinement phase.
        vault_path : str
            Filesystem path to the target Obsidian vault.  If the
            directory does not exist it will be created.

        Returns
        -------
        list of pathlib.Path
            Paths to the files that were written.
        """
        vault = Path(vault_path)
        vault.mkdir(parents=True, exist_ok=True)
        written: List[Path] = []
        for report in refined_reports:
            analysis_id = report.get("analysis_id", "unknown")
            out_file = vault / f"spark_report_{analysis_id}.json"
            try:
                with out_file.open("w", encoding="utf-8") as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                written.append(out_file)
            except Exception:
                continue
        return written