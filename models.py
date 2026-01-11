import sqlite3

conn = sqlite3.connect("grievance.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS user_state (
  phone TEXT PRIMARY KEY,
  step TEXT,
  temp_data TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS grievances (
  grievance_id TEXT PRIMARY KEY,
  phone TEXT,
  category TEXT,
  description TEXT,
  anonymous INTEGER,
  name TEXT,
  status TEXT,
  created_at TEXT
)
""")

conn.commit()
conn.close()

print("Tables created successfully")
