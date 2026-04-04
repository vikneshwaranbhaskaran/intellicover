import sqlite3

conn = sqlite3.connect(".app.db")
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT type, status, amount, reason, datetime FROM claims ORDER BY datetime ASC").fetchall()
for r in rows:
    d = dict(r)
    print(f"{d['type']} | {d['status']} | {d['amount']} | {d['reason']}")
conn.close()
