"""
Automatic backup system for rules and categories.
Protects against data loss by creating timestamped backups.
"""
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional

# Backup directory
BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)

# Keep last N backups
MAX_BACKUPS = 10


def create_rules_backup(db, description: str = "auto") -> str:
    """
    Create a timestamped backup of all rules.

    Args:
        db: FinanceDatabase instance
        description: Description of backup (e.g., 'auto', 'manual', 'before_import')

    Returns:
        Path to backup file
    """
    from src.data.database import FinanceDatabase

    # Get all rules and categories
    rules = db.get_rules()
    categories = {c.id: c.name for c in db.get_categories()}

    # Build export data
    data = []
    for r in rules:
        data.append({
            'Pattern': r.pattern,
            'Category': categories.get(r.category_id, 'Unknown'),
            'Priority': r.priority,
            'Created': r.created_at
        })

    df = pd.DataFrame(data)

    # Create timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = BACKUP_DIR / f"rules_{description}_{timestamp}.xlsx"

    # Save backup
    df.to_excel(filename, index=False)

    print(f"[BACKUP] Created backup: {filename} ({len(df)} rules)")

    # Clean up old backups
    cleanup_old_backups()

    return str(filename)


def cleanup_old_backups():
    """Remove old backup files, keeping only the most recent MAX_BACKUPS."""
    backup_files = sorted(BACKUP_DIR.glob("rules_*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)

    if len(backup_files) > MAX_BACKUPS:
        for old_file in backup_files[MAX_BACKUPS:]:
            print(f"[BACKUP] Removing old backup: {old_file.name}")
            old_file.unlink()


def export_rules_to_downloads(db) -> str:
    """
    Export rules to user's Downloads folder for manual safekeeping.

    Returns:
        Path to exported file
    """
    # Get all rules and categories
    rules = db.get_rules()
    categories = {c.id: c.name for c in db.get_categories()}

    # Build export data
    data = []
    for r in rules:
        data.append({
            'Pattern': r.pattern,
            'Category': categories.get(r.category_id, 'Unknown'),
            'Priority': r.priority,
            'Created': r.created_at
        })

    df = pd.DataFrame(data)

    # Export to Downloads
    downloads_path = Path.home() / "Downloads"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = downloads_path / f"rules_export_{timestamp}.xlsx"

    df.to_excel(filename, index=False)

    print(f"[EXPORT] Rules exported to: {filename} ({len(df)} rules)")

    return str(filename)


def create_master_rules_file(db):
    """
    Create a master rules CSV file in project root (git-tracked).
    This serves as a version-controlled backup.
    """
    # Get all rules and categories
    rules = db.get_rules()
    categories = {c.id: c.name for c in db.get_categories()}

    # Build export data (CSV for better git diffs)
    data = []
    for r in sorted(rules, key=lambda x: (x.priority, x.pattern), reverse=True):
        data.append({
            'pattern': r.pattern,
            'category': categories.get(r.category_id, 'Unknown'),
            'priority': r.priority
        })

    df = pd.DataFrame(data)

    # Save as CSV in project root
    filename = "rules_master.csv"
    df.to_csv(filename, index=False)

    print(f"[MASTER] Updated master rules file: {filename} ({len(df)} rules)")

    return filename
