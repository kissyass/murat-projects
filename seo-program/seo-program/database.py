import sqlite3
from cryptography.fernet import Fernet

# Encryption Key - This should be stored securely in an environment variable or secure storage
ENCRYPTION_KEY = b'JQu0uhAlauqJA1XDGtniaPlqCLECIGBVAPm6VhYltPc='  # Replace this with a secure key
fernet = Fernet(ENCRYPTION_KEY)

DB_NAME = "accounts.db"

# Encrypt a password
def encrypt_password(plaintext_password):
    return fernet.encrypt(plaintext_password.encode()).decode()

# Decrypt a password
def decrypt_password(encrypted_password):
    return fernet.decrypt(encrypted_password.encode()).decode()

# Initialize the database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            api_key TEXT NOT NULL,
            add_data_available BOOLEAN DEFAULT FALSE,
            add_data_folder TEXT
        )
    """)
    conn.commit()
    conn.close()

# Update additional data fields for an account
def update_add_data(account_id, folder_path):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE accounts
        SET add_data_available = ?, add_data_folder = ?
        WHERE id = ?
    """, (True, folder_path, account_id))
    conn.commit()
    conn.close()

# Save a new account (encrypt the password)
def save_account(domain, username, plaintext_password, api_key):
    encrypted_password = encrypt_password(plaintext_password)
    encrypted_api_key = encrypt_password(api_key)  

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO accounts (domain, username, password, api_key)
        VALUES (?, ?, ?, ?)
    """, (domain, username, encrypted_password, encrypted_api_key))
    conn.commit()
    conn.close()

# Retrieve all accounts
def get_accounts():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, domain, username, password, api_key, add_data_available, add_data_folder FROM accounts")
    accounts = cursor.fetchall()
    conn.close()
    return accounts

def find_account(domain, username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, password, api_key, add_data_available, add_data_folder 
        FROM accounts
        WHERE domain = ? AND username = ?
    """, (domain, username))
    account = cursor.fetchone()
    conn.close()
    return account

# Check if additional data is available for an account
def is_add_data_available(account_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT add_data_available, add_data_folder FROM accounts
        WHERE id = ?
    """, (account_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0], result[1]  # Return (add_data_available, add_data_folder)
    return False, None