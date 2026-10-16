import sys
import sqlite3
import subprocess
import importlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_SCRIPT = BASE_DIR / "scripts" / "backup_db.py"
RESTORE_SCRIPT = BASE_DIR / "scripts" / "restore_db.py"
BACKUP_DIR = BASE_DIR / "backups"
ISOLATED_TEST_DB = BASE_DIR / "test_isolated_restore.db"

print("==================================================================")
print("RELIEFOS Lite -- Database Backup & Isolated Restore Verification")
print("==================================================================")

# 1. Run fresh point-in-time backup
print("\n[STEP 1] Generating fresh atomic backup...")
res = subprocess.run([sys.executable, str(BACKUP_SCRIPT)], capture_output=True, text=True)
print(res.stdout)
assert res.returncode == 0, f"Backup failed: {res.stderr}"

# Find the newest backup archive
gz_files = sorted(BACKUP_DIR.glob("reliefos_snapshot_*.db.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
assert len(gz_files) > 0, "No backup file found!"
latest_backup = gz_files[0]
print(f"  * Latest verified backup archive: {latest_backup.name} ({latest_backup.stat().st_size / 1024:.1f} KB)")

# 2. Restore into isolated test database (NOT touching reliefos_lite.db)
if ISOLATED_TEST_DB.exists():
    ISOLATED_TEST_DB.unlink()

print(f"\n[STEP 2] Restoring {latest_backup.name} into isolated target: {ISOLATED_TEST_DB.name}...")
res_restore = subprocess.run([sys.executable, str(RESTORE_SCRIPT), str(latest_backup), str(ISOLATED_TEST_DB)], capture_output=True, text=True)
print(res_restore.stdout)
assert res_restore.returncode == 0, f"Restore failed: {res_restore.stderr}"
assert ISOLATED_TEST_DB.exists(), "Isolated test database was not created!"

# 3. Verify SQLite PRAGMA integrity
print("\n[STEP 3] Running SQLite PRAGMA integrity check on isolated restored DB...")
conn = sqlite3.connect(str(ISOLATED_TEST_DB))
cur = conn.cursor()
cur.execute("PRAGMA integrity_check;")
integrity_result = cur.fetchone()[0]
assert integrity_result == "ok", f"Integrity check failed: {integrity_result}"
print(f"  [PASS] SQLite PRAGMA integrity check result: '{integrity_result}'")

# Query tables in isolated database
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = [r[0] for r in cur.fetchall() if not r[0].startswith("sqlite_")]
print(f"  * Restored Tables Found ({len(tables)}): {', '.join(tables)}")
assert len(tables) >= 8, f"Expected at least 8 operational tables, found {len(tables)}"

# 4. Verify record counts and query operational data
print("\n[STEP 4] Verifying table records and query access...")
table_counts = {}
for tbl in tables:
    cur.execute(f"SELECT COUNT(*) FROM {tbl};")
    count_row = cur.fetchone()
    count = count_row[0] if count_row else 0
    table_counts[tbl] = count
    print(f"  * Table '{tbl}': {count} records")

assert table_counts.get("zones", 0) >= 5, "Zones table must have at least 5 records"
assert table_counts.get("inventory_items", 0) >= 3, "Inventory table must have items"
assert table_counts.get("shelters", 0) >= 2, "Shelters table must have records"
assert table_counts.get("audit_logs", 0) >= 1, "Audit logs must be present"

# Query specific records to verify data integrity
cur.execute("SELECT code, name, risk_level, affected_population FROM zones LIMIT 1;")
sample_zone = cur.fetchone()
assert sample_zone is not None, "Failed to retrieve sample zone record"
print(f"\n  * Verified Sample Zone Record: Code={sample_zone[0]}, Name={sample_zone[1]}, Risk={sample_zone[2]}, Pop={sample_zone[3]}")

cur.execute("SELECT sku, name, available_quantity, unit FROM inventory_items LIMIT 1;")
sample_inv = cur.fetchone()
assert sample_inv is not None, "Failed to retrieve sample inventory record"
print(f"  * Verified Sample Inventory Record: SKU={sample_inv[0]}, Name={sample_inv[1]}, Available={sample_inv[2]} {sample_inv[3]}")

# Optional SQLAlchemy ORM connection verification
try:
    venv_site = BASE_DIR / ".venv" / "Lib" / "site-packages"
    if venv_site.exists() and str(venv_site) not in sys.path:
        sys.path.insert(0, str(venv_site))
    sa = importlib.import_module("sqlalchemy")
    sa_create_engine = getattr(sa, "create_engine")
    sa_text = getattr(sa, "text")
    sa_engine = sa_create_engine(f"sqlite:///{ISOLATED_TEST_DB.as_posix()}", echo=False)
    with sa_engine.connect() as sa_conn:
        z_count = sa_conn.execute(sa_text("SELECT COUNT(*) FROM zones")).scalar()
        print(f"  * SQLAlchemy ORM layer verified: Successfully queried {z_count} zones via engine")
    sa_engine.dispose()
except Exception as e:
    print(f"  * Optional SQLAlchemy ORM check note: {e}")

conn.close()

# Clean up isolated test database
ISOLATED_TEST_DB.unlink(missing_ok=True)
# Clean up any pre_restore backup safety copy if created
for p in BASE_DIR.glob("test_isolated_restore.db.pre_restore_*.bak"):
    p.unlink(missing_ok=True)

print("\n==================================================================")
print("ISOLATED BACKUP & RESTORE VERIFICATION PASSED (100% SUCCESS)")
print("==================================================================")
