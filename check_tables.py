import sqlite3
conn = sqlite3.connect('local.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print('tables=' + str(len(tables)))
for t in tables:
    print('  ' + t[0])
conn.close()
