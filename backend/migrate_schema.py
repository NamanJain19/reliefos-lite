import sqlite3

def run_migration():
    conn = sqlite3.connect('reliefos_lite.db')
    cursor = conn.cursor()

    columns_to_add = [
        ('shelters', 'verification_status', "TEXT DEFAULT 'VERIFIED'"),
        ('shelters', 'verification_source', "TEXT DEFAULT 'DDMA Kamrup Metro 2024'"),
        ('shelters', 'verified_date', "TEXT DEFAULT '2024-06-15'"),
        ('shelters', 'location_id', "TEXT DEFAULT 'kamrup_metro'"),
        ('zones', 'location_id', "TEXT DEFAULT 'kamrup_metro'"),
        ('depots', 'location_id', "TEXT DEFAULT 'kamrup_metro'"),
        ('vehicles', 'location_id', "TEXT DEFAULT 'kamrup_metro'"),
        ('road_closures', 'location_id', "TEXT DEFAULT 'kamrup_metro'"),
        ('dispatch_orders', 'location_id', "TEXT DEFAULT 'kamrup_metro'"),
        ('audit_logs', 'location_id', "TEXT DEFAULT 'kamrup_metro'"),
        ('demands', 'lifecycle_status', "TEXT DEFAULT 'REQUESTED'"),
        ('demands', 'location_id', "TEXT DEFAULT 'kamrup_metro'"),
        ('demands', 'verification_status', "TEXT DEFAULT 'UNVERIFIED'"),
        ('demands', 'verified_by', "TEXT"),
        ('demands', 'verified_at', "TIMESTAMP"),
        ('demands', 'request_source', "TEXT DEFAULT 'Field Shelter Coordinator'"),
        ('demands', 'notes', "TEXT DEFAULT ''"),
        ('demands', 'updated_at', "TIMESTAMP"),
        ('inventory_items', 'updated_at', "TIMESTAMP"),
        ('inventory_items', 'last_verified_by', "TEXT DEFAULT 'ASDMA Central Logistics Desk'")
    ]

    for tbl, col, col_def in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_def}")
            print(f"Added column {col} to {tbl}")
        except Exception as e:
            print(f"Column {tbl}.{col} status: {e}")

    conn.commit()
    conn.close()
    print("SQLite migration finished.")

if __name__ == '__main__':
    run_migration()
