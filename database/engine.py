"""
Database Engine - Core database functions
"""

import sqlite3
import pandas as pd
import logging
from pathlib import Path
from config.settings import REAL_DB_PATH, DEMO_DB_PATH, BACKUP_DIR

logger = logging.getLogger(__name__)


def get_db_path(mode='real'):
    """Get database path based on mode"""
    if mode == 'demo':
        return str(DEMO_DB_PATH)
    return str(REAL_DB_PATH)


def get_connection(mode='real'):
    """Get database connection"""
    db_path = get_db_path(mode)
    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def backup_database(mode='real'):
    """Create a backup of the database"""
    import shutil
    from datetime import datetime
    
    try:
        db_path = get_db_path(mode)
        if db_path and Path(db_path).exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = BACKUP_DIR / f"backup_{mode}_{timestamp}.db"
            shutil.copy(db_path, backup_path)
            
            # Keep only last 10 backups
            backups = sorted(BACKUP_DIR.glob(f"backup_{mode}_*.db"))
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    old_backup.unlink()
            
            logger.info(f"Database backed up to {backup_path}")
            return str(backup_path)
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return None


def vacuum_database(mode='real'):
    """Optimize database"""
    conn = get_connection(mode)
    conn.execute("VACUUM")
    conn.close()
    logger.info(f"Database vacuumed in {mode} mode")


def get_database_size(mode='real'):
    """Get database file size in MB"""
    import os
    db_path = get_db_path(mode)
    if db_path and Path(db_path).exists():
        size_bytes = Path(db_path).stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    return 0