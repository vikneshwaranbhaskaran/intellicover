import sqlite3, os

for db in [".app.db", "app.db"]:
    if os.path.exists(db):
        print(f"\n=== {db} ===")
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        print(f"Tables: {tables}")
        
        for t in tables:
            cursor.execute(f"PRAGMA table_info({t})")
            cols = [(r[1], r[2]) for r in cursor.fetchall()]
            print(f"\n  {t} columns: {cols}")
            
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            print(f"  {t} row count: {cursor.fetchone()[0]}")
        
        # Check users data
        if "users" in tables:
            conn.row_factory = sqlite3.Row
            c2 = conn.cursor()
            c2.execute("SELECT * FROM users LIMIT 2")
            for row in c2.fetchall():
                print(f"\n  User: {dict(row)}")
        
        conn.close()
    else:
        print(f"{db} NOT FOUND")
