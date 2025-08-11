"""Basic tests for the Obsidian‑LLM integration system.

These tests exercise the SPARK and LEAP workflows to ensure that the
pipelines run without errors and produce reasonable output.  They use
pytest fixtures for isolation.
"""

import asyncio
import os
from pathlib import Path

import pytest

from obskg.workflows.spark import SPARKPipeline
from obskg.workflows.leap import LEAPPipeline


@pytest.fixture
def sample_vault(tmp_path: Path) -> Path:
    """Create a temporary vault with a few notes for testing."""
    vault = tmp_path / "vault"
    vault.mkdir()
    # Create a couple of Markdown files
    (vault / "note1.md").write_text("""# Note 1\n\nThis is the first note.\nIt has some content about testing.\n\nMore text here.""")
    (vault / "note2.md").write_text("""# Note 2\n\nAnother note for the vault.\nIt discusses unit tests and pipelines.""")
    return vault


def test_spark_workflow(sample_vault: Path) -> None:
    """Ensure that the SPARK pipeline runs end‑to‑end."""
    pipeline = SPARKPipeline(vault_path=str(sample_vault))
    results = asyncio.run(pipeline.run())
    assert "tti" in results
    assert results["num_produced"] >= 0


def test_leap_workflow() -> None:
    """Ensure that the LEAP pipeline runs and returns counts."""
    pipeline = LEAPPipeline()
    results = pipeline.run()
    assert isinstance(results["num_gaps"], int)
    assert isinstance(results["num_experiments"], int)