"""
Progress tracking for background AI categorization.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class ProgressTracker:
    """Tracks progress of AI categorization for UI display."""

    def __init__(self, progress_file: Path = None):
        if progress_file is None:
            progress_file = Path("data/ai_progress.json")
        self.progress_file = progress_file

    def start(self, total_transactions: int):
        """Mark categorization as started."""
        self._write({
            "status": "running",
            "total": total_transactions,
            "processed": 0,
            "rule_matched": 0,
            "ai_categorized": 0,
            "uncategorized": 0,
            "percent": 0.0,
            "eta_minutes": 0.0,
            "started_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        })

    def update(self, processed: int, rule_matched: int, ai_categorized: int,
               uncategorized: int, eta_minutes: float = 0.0):
        """Update progress."""
        data = self._read()
        if data:
            total = data.get("total", processed)
            percent = (processed / total * 100) if total > 0 else 0

            data.update({
                "processed": processed,
                "rule_matched": rule_matched,
                "ai_categorized": ai_categorized,
                "uncategorized": uncategorized,
                "percent": round(percent, 1),
                "eta_minutes": round(eta_minutes, 1),
                "updated_at": datetime.now().isoformat(),
            })
            self._write(data)

    def complete(self, rule_matched: int, ai_categorized: int,
                 uncategorized: int, cost_usd: float, elapsed_minutes: float):
        """Mark as complete."""
        data = self._read()
        if data:
            data.update({
                "status": "complete",
                "processed": data.get("total", 0),
                "rule_matched": rule_matched,
                "ai_categorized": ai_categorized,
                "uncategorized": uncategorized,
                "percent": 100.0,
                "cost_usd": round(cost_usd, 4),
                "elapsed_minutes": round(elapsed_minutes, 1),
                "completed_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            })
            self._write(data)

    def error(self, error_message: str):
        """Mark as failed."""
        data = self._read()
        if data:
            data.update({
                "status": "error",
                "error": error_message,
                "updated_at": datetime.now().isoformat(),
            })
            self._write(data)

    def get_progress(self) -> Optional[dict]:
        """Get current progress."""
        return self._read()

    def clear(self):
        """Clear progress file."""
        if self.progress_file.exists():
            self.progress_file.unlink()

    def _read(self) -> Optional[dict]:
        """Read progress file."""
        if not self.progress_file.exists():
            return None
        try:
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        except:
            return None

    def _write(self, data: dict):
        """Write progress file."""
        self.progress_file.parent.mkdir(exist_ok=True, parents=True)
        with open(self.progress_file, 'w') as f:
            json.dump(data, f, indent=2)
