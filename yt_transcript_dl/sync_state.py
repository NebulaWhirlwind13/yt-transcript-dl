"""Sync state management for incremental downloads."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Set


class SyncState:
    """Manages sync state for incremental transcript downloads."""

    def __init__(self, state_file: Path):
        """
        Initialize sync state manager.

        Args:
            state_file: Path to sync state JSON file
        """
        self.state_file = state_file
        self.downloaded_ids: Set[str] = set()
        self.last_sync: Optional[str] = None
        self._load()

    def _load(self) -> None:
        """Load sync state from file."""
        if not self.state_file.exists():
            return

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.downloaded_ids = set(data.get('downloaded_ids', []))
                self.last_sync = data.get('last_sync')
        except (json.JSONDecodeError, OSError):
            # If file is corrupted, start fresh
            pass

    def save(self) -> None:
        """Save sync state to file."""
        data = {
            'downloaded_ids': list(self.downloaded_ids),
            'last_sync': datetime.now().isoformat(),
        }

        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError:
            # Silently fail if we can't save state
            pass

    def is_downloaded(self, video_id: str) -> bool:
        """
        Check if video was already downloaded.

        Args:
            video_id: YouTube video ID

        Returns:
            True if video was downloaded before
        """
        return video_id in self.downloaded_ids

    def mark_downloaded(self, video_id: str) -> None:
        """
        Mark video as downloaded.

        Args:
            video_id: YouTube video ID
        """
        self.downloaded_ids.add(video_id)

    def should_download_by_date(self, upload_date: str) -> bool:
        """
        Check if video should be downloaded based on upload date.

        Args:
            upload_date: Video upload date in YYYYMMDD format

        Returns:
            True if video is newer than last sync
        """
        if not self.last_sync or not upload_date:
            return True

        try:
            # Parse last_sync ISO format
            last_sync_dt = datetime.fromisoformat(self.last_sync)

            # Parse upload_date YYYYMMDD format
            if len(upload_date) == 8:
                upload_dt = datetime(
                    int(upload_date[:4]),
                    int(upload_date[4:6]),
                    int(upload_date[6:])
                )

                return upload_dt >= last_sync_dt
        except (ValueError, IndexError):
            # If date parsing fails, download to be safe
            return True

        return True

    def clear(self) -> None:
        """Clear all sync state."""
        self.downloaded_ids.clear()
        self.last_sync = None

        if self.state_file.exists():
            try:
                self.state_file.unlink()
            except OSError:
                pass
