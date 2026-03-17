import sqlite3
conn = sqlite3.connect('local.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('SELECT COUNT(*) as cnt FROM sms_messages')
total = cur.fetchone()['cnt']
print('total=' + str(total))

cur.execute("SELECT id, body FROM sms_messages WHERE body LIKE '%Jaja%'")
jaja = cur.fetchall()
print('jaja_count=' + str(len(jaja)))

cur.execute('SELECT body, direction, created_at FROM sms_messages ORDER BY id DESC LIMIT 1')
last = cur.fetchone()
if last:
    body = last['body'][:50] if last['body'] else 'None'
    print('last_msg=' + body + '...')
    print('last_dir=' + last['direction'])
conn.close()
