import sqlite3

conn = sqlite3.connect('local.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('SELECT COUNT(*) as cnt FROM sms_message')
total = cur.fetchone()['cnt']
print('total=' + str(total))

cur.execute("SELECT id, body FROM sms_message WHERE body LIKE '%Jaja%'")
jaja = cur.fetchall()
print('jaja=' + str(len(jaja)))

cur.execute('SELECT body FROM sms_message ORDER BY id DESC LIMIT 1')
last = cur.fetchone()
if last:
    body = last[0][:80] if last[0] else "None"
    print('last=' + body)
