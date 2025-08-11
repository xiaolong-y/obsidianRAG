"""
Scheduling and monitoring helpers for automated ingestion.

This module contains utilities for running background tasks that keep your
vector store in sync with one or more Obsidian vaults.  Two flavours of
schedulers are provided:

* `cron_schedule` – generate a cron expression and instructions for adding
  an entry to the user’s crontab on macOS.  The cron job could run a
  script that scans the vault and updates embeddings nightly or hourly.
* `watch_vault` – monitor a vault directory in real time using the
  `watchdog` library.  When a Markdown file changes, a callback is
  triggered to update the vector store.  This is useful for immediate
  reflection of changes without waiting for a cron job.

Because macOS versions after Catalina restrict access to cron, you may need
to use `launchd` instead of cron.  The `launchd_plist` function returns a
template for a LaunchAgent plist that runs a script at specified intervals.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:  # pragma: no cover
    Observer = None  # type: ignore
    FileSystemEventHandler = object  # type: ignore


def cron_schedule(script_path: Path, interval_minutes: int = 60) -> str:
    """Return a cron entry for executing a script every `interval_minutes`.

    Parameters
    ----------
    script_path:
        Path to the Python script to execute.
    interval_minutes:
        Interval in minutes between runs.

    Returns
    -------
    str
        A line that can be added to the user's crontab.

    Example
    -------
    >>> cron_schedule(Path('/usr/local/bin/update_embeddings.py'), 30)
    '*/30 * * * * /usr/local/bin/python3 /usr/local/bin/update_embeddings.py > /tmp/obskg.log 2>&1'
    """
    return f"*/{interval_minutes} * * * * {os.environ.get('PYTHON', 'python3')} {script_path} > /tmp/obskg.log 2>&1"


def launchd_plist(label: str, script_path: Path, interval_minutes: int = 60) -> str:
    """Generate a LaunchAgent plist for macOS to run a script periodically."""
    return f"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{os.environ.get('PYTHON', 'python3')}</string>
        <string>{script_path}</string>
    </array>
    <key>StartInterval</key>
    <integer>{interval_minutes * 60}</integer>
    <key>StandardOutPath</key>
    <string>/tmp/{label}.out</string>
    <key>StandardErrorPath</key>
    <string>/tmp/{label}.err</string>
</dict>
</plist>
"""


class VaultEventHandler(FileSystemEventHandler):  # pragma: no cover
    """Watchdog event handler that triggers a callback when a .md file changes."""

    def __init__(self, callback: Callable[[Path], None]) -> None:
        super().__init__()
        self.callback = callback

    def on_modified(self, event) -> None:
        if not event.is_directory and event.src_path.endswith('.md'):
            self.callback(Path(event.src_path))

    def on_created(self, event) -> None:
        if not event.is_directory and event.src_path.endswith('.md'):
            self.callback(Path(event.src_path))


def watch_vault(vault_path: Path, callback: Callable[[Path], None]) -> Optional[Observer]:  # pragma: no cover
    """Watch a vault directory and trigger callback on Markdown changes."""
    if Observer is None:
        raise RuntimeError("watchdog is not installed")
    event_handler = VaultEventHandler(callback)
    observer = Observer()
    observer.schedule(event_handler, str(vault_path), recursive=True)
    observer.start()
    return observer