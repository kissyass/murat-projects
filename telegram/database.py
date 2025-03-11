import sqlite3

# ---------------------------
# Database Functions
# ---------------------------
def init_db():
    with sqlite3.connect("accounts.db", timeout=5) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS accounts
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      api_id INTEGER,
                      api_hash TEXT,
                      phone TEXT,
                      session_name TEXT)''')
        conn.commit()

def get_accounts():
    with sqlite3.connect("accounts.db", timeout=5) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM accounts")
        accounts = c.fetchall()
    return accounts

def insert_account(api_id, api_hash, phone, session_name):
    with sqlite3.connect("accounts.db", timeout=5) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM accounts WHERE phone=?", (phone,))
        if c.fetchone() is None:
            c.execute("INSERT INTO accounts (api_id, api_hash, phone, session_name) VALUES (?, ?, ?, ?)",
                      (api_id, api_hash, phone, session_name))
            conn.commit()