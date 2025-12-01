"""Progress tracking for long-running operations."""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class ProgressTracker:
    """Track progress of categorization operations."""

    def __init__(self, progress_file: str = "data/categorization_progress.json"):
        self.progress_file = Path(progress_file)
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)

    def start(self, operation: str, total: int):
        """Start tracking a new operation."""
        progress = {
            "operation": operation,
            "status": "running",
            "total": total,
            "processed": 0,
            "transaction_type_matched": 0,
            "rule_matched": 0,
            "ai_categorized": 0,
            "uncategorized": 0,
            "errors": 0,
            "current_batch": 0,
            "total_batches": 0,
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "message": f"Starting {operation}...",
        }
        self._write(progress)

    def update(
        self,
        processed: int,
        message: str = "",
        transaction_type_matched: int = 0,
        rule_matched: int = 0,
        ai_categorized: int = 0,
        uncategorized: int = 0,
        errors: int = 0,
        current_batch: int = 0,
        total_batches: int = 0,
    ):
        """Update progress."""
        progress = self._read()
        if progress:
            progress["processed"] = processed
            progress["transaction_type_matched"] = transaction_type_matched
            progress["rule_matched"] = rule_matched
            progress["ai_categorized"] = ai_categorized
            progress["uncategorized"] = uncategorized
            progress["errors"] = errors
            progress["current_batch"] = current_batch
            progress["total_batches"] = total_batches
            progress["last_update"] = datetime.now().isoformat()
            if message:
                progress["message"] = message
            self._write(progress)

    def complete(self, message: str = "Complete"):
        """Mark operation as complete."""
        progress = self._read()
        if progress:
            progress["status"] = "complete"
            progress["message"] = message
            progress["last_update"] = datetime.now().isoformat()
            self._write(progress)

    def error(self, message: str):
        """Mark operation as failed."""
        progress = self._read()
        if progress:
            progress["status"] = "error"
            progress["message"] = message
            progress["last_update"] = datetime.now().isoformat()
            self._write(progress)

    def get_progress(self) -> Optional[dict]:
        """Get current progress."""
        return self._read()

    def clear(self):
        """Clear progress file."""
        if self.progress_file.exists():
            self.progress_file.unlink()

    def _read(self) -> Optional[dict]:
        """Read progress from file."""
        if not self.progress_file.exists():
            return None
        try:
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None

    def _write(self, progress: dict):
        """Write progress to file."""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
        except Exception as e:
            print(f"Failed to write progress: {e}")
