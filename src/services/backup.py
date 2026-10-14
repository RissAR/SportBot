"""Automated SQLite hot backup and retention rotation service."""

import asyncio
from datetime import datetime
import glob
import logging
import os
from typing import Optional

from sqlalchemy import text

from src.db.session import async_session_factory

logger = logging.getLogger("sportbot.services.backup")


async def create_db_backup(backup_dir: str = "backups", max_backups: int = 7) -> Optional[str]:
    """Execute an atomic SQLite VACUUM INTO hot backup and prune old copies."""
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"sportbot_backup_{timestamp}.db"
    backup_path = os.path.abspath(os.path.join(backup_dir, backup_filename))
    if os.path.exists(backup_path):
        os.remove(backup_path)

    logger.info("Initiating hot SQLite database backup to %s...", backup_path)
    try:
        async with async_session_factory() as session:
            # Atomic copy to target location
            await session.execute(text(f"VACUUM INTO '{backup_path}'"))
            # Flush dirty WAL pages to main DB
            await session.execute(text("PRAGMA wal_checkpoint(PASSIVE)"))

        size_kb = os.path.getsize(backup_path) / 1024
        logger.info("Backup successfully generated: %s (%.1f KB)", backup_filename, size_kb)
    except Exception as ex:
        logger.error("Failed to execute database backup: %s", ex, exc_info=True)
        if os.path.exists(backup_path):
            try:
                os.remove(backup_path)
            except OSError:
                pass
        return None

    # Backup rotation: retain only the latest `max_backups`
    try:
        pattern = os.path.join(backup_dir, "sportbot_backup_*.db")
        existing_backups = sorted(glob.glob(pattern), key=os.path.getmtime)

        if len(existing_backups) > max_backups:
            to_remove = existing_backups[:-max_backups]
            for old_file in to_remove:
                try:
                    os.remove(old_file)
                    logger.info("Pruned old backup file: %s", os.path.basename(old_file))
                except OSError as err:
                    logger.warning("Could not delete old backup %s: %s", old_file, err)

        remaining_count = len(glob.glob(pattern))
        logger.info("Current backup retention count: %d (max: %d)", remaining_count, max_backups)
    except Exception as rot_err:
        logger.warning("Error during backup rotation check: %s", rot_err)

    return backup_path


async def run_backup_worker(
    interval_seconds: int = 86400,
    backup_dir: str = "backups",
    max_backups: int = 7,
) -> None:
    """Infinite background task triggering daily SQLite backups."""
    logger.info("Starting BackupWorker (interval: %ds, retention: %d)...", interval_seconds, max_backups)

    try:
        while True:
            await create_db_backup(backup_dir=backup_dir, max_backups=max_backups)
            await asyncio.sleep(interval_seconds)
    except asyncio.CancelledError:
        logger.info("BackupWorker received cancellation.")
