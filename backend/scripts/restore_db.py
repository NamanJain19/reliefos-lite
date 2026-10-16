#!/usr/bin/env python3
"""
RELIEFOS Lite — Operational Database Restore Utility
Safely restores an atomic database snapshot, verifying SHA-256 integrity and PRAGMA status
before atomically swapping into active production service.
"""

import os
import sys
import time
import gzip
import shutil
import sqlite3
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_TARGET_DB = BASE_DIR / "reliefos_lite.db"

def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def restore_sqlite(backup_file: Path, target_path: Path):
    if not backup_file.exists():
        print(f"[ERROR] Backup archive not found: {backup_file}", file=sys.stderr)
        sys.exit(1)

    # 1. Verify SHA-256 checksum if companion file exists
    checksum_file = backup_file.with_suffix(".sha256")
    if checksum_file.exists():
        expected_hash = checksum_file.read_text().split()[0]
        actual_hash = compute_sha256(backup_file)
        if actual_hash.lower() != expected_hash.lower():
            print(f"[FATAL] SHA-256 mismatch! Expected {expected_hash}, calculated {actual_hash}", file=sys.stderr)
            sys.exit(1)
        print("[*] SHA-256 cryptographic verification passed.")

    # 2. Decompress into temporary validation database
    temp_restored_db = target_path.parent / f"reliefos_restore_tmp_{os.getpid()}.db"
    print(f"[*] Decompressing {backup_file.name} to staging database...")

    if backup_file.name.endswith(".gz"):
        with gzip.open(backup_file, "rb") as f_in:
            with open(temp_restored_db, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
    else:
        shutil.copy2(backup_file, temp_restored_db)

    # 3. Perform integrity check on staging database
    conn = sqlite3.connect(str(temp_restored_db))
    cur = conn.cursor()
    cur.execute("PRAGMA integrity_check;")
    res = cur.fetchone()[0]

    # Query key operational tables to verify sanity
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cur.fetchall()]
    conn.close()

    if res != "ok":
        temp_restored_db.unlink(missing_ok=True)
        print(f"[FATAL] Restored database corrupted: {res}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Staging database verified healthy ('{res}'). Verified tables: {len(tables)} tables found.")

    # 4. Atomic cutover to production database path
    target_backup_prev = target_path.with_suffix(f".pre_restore_{int(time.time())}.bak")
    if target_path.exists():
        print(f"[*] Creating rollback safety copy of current DB -> {target_backup_prev.name}")
        shutil.copy2(target_path, target_backup_prev)

    shutil.move(str(temp_restored_db), str(target_path))
    print(f"[SUCCESS] Database successfully restored to: {target_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python restore_db.py <path_to_backup.db.gz> [target_db_path]")
        sys.exit(1)

    backup_path = Path(sys.argv[1])
    target_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_TARGET_DB
    restore_sqlite(backup_path, target_path)

if __name__ == "__main__":
    main()
