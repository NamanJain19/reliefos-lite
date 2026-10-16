#!/usr/bin/env python3
"""
RELIEFOS Lite — Operational Database Backup Utility
Creates an atomic, consistent point-in-time snapshot of the active operational ledger
with cryptographic SHA-256 verification and compression.
"""

import os
import sys
import time
import gzip
import shutil
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# Determine project paths
BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DB_PATH = BASE_DIR / "reliefos_lite.db"

def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def backup_sqlite(source_path: Path) -> Path:
    if not source_path.exists():
        print(f"[ERROR] Source database not found at: {source_path}", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    raw_backup_path = BACKUP_DIR / f"reliefos_snapshot_{timestamp}.db"
    compressed_backup_path = BACKUP_DIR / f"reliefos_snapshot_{timestamp}.db.gz"

    print(f"[*] Starting atomic SQLite backup from: {source_path}")
    start_time = time.time()

    # Use SQLite Online Backup API for 100% transactional consistency during active writes
    src_conn = sqlite3.connect(str(source_path))
    dst_conn = sqlite3.connect(str(raw_backup_path))
    with dst_conn:
        src_conn.backup(dst_conn, pages=100)
    dst_conn.close()
    src_conn.close()

    # Verify integrity of snapshot
    verify_conn = sqlite3.connect(str(raw_backup_path))
    cursor = verify_conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    integrity = cursor.fetchone()[0]
    verify_conn.close()

    if integrity != "ok":
        raw_backup_path.unlink(missing_ok=True)
        print(f"[FATAL] Backup integrity check failed: {integrity}", file=sys.stderr)
        sys.exit(1)

    # Gzip compress the verified snapshot
    with open(raw_backup_path, "rb") as f_in:
        with gzip.open(compressed_backup_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Remove raw uncompressed snapshot
    raw_backup_path.unlink(missing_ok=True)

    # Compute cryptographic checksum
    sha256_hash = compute_sha256(compressed_backup_path)
    checksum_file = BACKUP_DIR / f"reliefos_snapshot_{timestamp}.sha256"
    checksum_file.write_text(f"{sha256_hash}  {compressed_backup_path.name}\n")

    elapsed = time.time() - start_time
    size_mb = compressed_backup_path.stat().st_size / (1024 * 1024)

    print(f"[SUCCESS] Operational snapshot created in {elapsed:.2f}s")
    print(f"          Path:     {compressed_backup_path}")
    print(f"          Size:     {size_mb:.3f} MB")
    print(f"          SHA-256:  {sha256_hash}")
    return compressed_backup_path

def main():
    db_path = Path(os.environ.get("DATABASE_PATH", str(DEFAULT_DB_PATH)))
    backup_sqlite(db_path)

if __name__ == "__main__":
    main()
