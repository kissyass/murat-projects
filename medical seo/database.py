import sqlite3
import pandas as pd
import openpyxl

DB_NAME = "accounts.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Table for accounts (login credentials)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            api_key TEXT NOT NULL
        )
    """)
    # Table linking an account to its record table (if any)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS all_accounts_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            record_table_name TEXT,
            company_info TEXT DEFAULT NULL,
            additional_data_table TEXT DEFAULT NULL,
            FOREIGN KEY(account_id) REFERENCES accounts(id)
        )
    """)
    conn.commit()
    conn.close()

def save_account_to_db(domain, username, password, api_key):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO accounts (domain, username, password, api_key)
        VALUES (?, ?, ?, ?)
    """, (domain, username, password, api_key))
    conn.commit()
    account_id = cursor.lastrowid
    conn.close()
    return account_id

def get_accounts():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, domain, username, password, api_key FROM accounts")
    accounts = cursor.fetchall()
    conn.close()
    return accounts

def find_account(domain, username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, domain, username, password, api_key FROM accounts
        WHERE domain = ? AND username = ?
    """, (domain, username))
    account = cursor.fetchone()
    conn.close()
    return account

def get_record_table_for_account(account_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT record_table_name FROM all_accounts_records
        WHERE account_id = ?
    """, (account_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

def update_record_table_for_account(account_id, table_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if get_record_table_for_account(account_id) is None:
        cursor.execute("""
            INSERT INTO all_accounts_records (account_id, record_table_name)
            VALUES (?, ?)
        """, (account_id, table_name))
    else:
        cursor.execute("""
            UPDATE all_accounts_records
            SET record_table_name = ?
            WHERE account_id = ?
        """, (table_name, account_id))
    conn.commit()
    conn.close()

# def create_data_table(table_name):
#     """Create a new data table with required columns."""
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
#     cursor.execute(f"DROP TABLE IF EXISTS '{table_name}'")
#     conn.commit()
#     cursor.execute(f"""
#         CREATE TABLE '{table_name}' (
#             record_id TEXT PRIMARY KEY,
#             title TEXT,
#             content TEXT,
#             job_location TEXT,
#             elementor TEXT,
#             used INTEGER DEFAULT 0
#         )
#     """)
#     conn.commit()
#     conn.close()

def create_data_table(table_name):
    """Create a new simplified data table with only the required columns."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS '{table_name}'")
    cursor.execute(f"""
        CREATE TABLE '{table_name}' (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            country TEXT,
            city TEXT,
            additional_info TEXT,
            used INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# def insert_data_into_table(table_name, df):
#     """Insert data from DataFrame into the record table."""
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
#     for _, row in df.iterrows():
#         record_id = str(row["record_id"])
#         title = row["Title"]
#         content = row["Content"]
#         job_location = row["Job Location"]
#         elementor = row["Elementor"]
#         cursor.execute(f"""
#             INSERT INTO '{table_name}' (record_id, title, content, job_location, elementor, used)
#             VALUES (?, ?, ?, ?, ?, 0)
#         """, (record_id, title, content, job_location, elementor))
#     conn.commit()
#     conn.close()

def insert_data_into_table(table_name, df):
    """Insert only Title, ülke, şehir, Additional_Info into the table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for _, row in df.iterrows():
        title = row.get("Title", "")
        country = row.get("ülke", "")
        city = row.get("şehir", "")
        additional_info = row.get("Additional_Info", "")
        cursor.execute(f"""
            INSERT INTO '{table_name}' (title, country, city, additional_info, used)
            VALUES (?, ?, ?, ?, 0)
        """, (title, country, city, additional_info))
    conn.commit()
    conn.close()

# def get_next_record(table_name):
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
#     cursor.execute(f"""
#         SELECT record_id, title, content, job_location, elementor FROM '{table_name}'
#         WHERE used = 0 ORDER BY rowid LIMIT 1
#     """)
#     record = cursor.fetchone()
#     conn.close()
#     return record

def get_next_record(table_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT id, title, country, city, additional_info FROM '{table_name}'
        WHERE used = 0 ORDER BY rowid LIMIT 1
    """)
    record = cursor.fetchone()
    conn.close()
    return record

def mark_record_as_used(table_name, record_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # cursor.execute(f"UPDATE '{table_name}' SET used = 1 WHERE record_id = ?", (record_id,))
    cursor.execute(f"UPDATE '{table_name}' SET used = 1 WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

def update_company_info(account_id, company_info):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE all_accounts_records
        SET company_info = ?
        WHERE account_id = ?
    """, (company_info, account_id))
    conn.commit()
    conn.close()

def get_company_info(account_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT company_info FROM all_accounts_records
        WHERE account_id = ?
    """, (account_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_additional_data_table_for_account(account_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT additional_data_table FROM all_accounts_records
        WHERE account_id = ?
    """, (account_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def update_additional_data_table_for_account(account_id, table_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE all_accounts_records
        SET additional_data_table = ?
        WHERE account_id = ?
    """, (table_name, account_id))

    conn.commit()
    conn.close()

def create_additional_data_table(table_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS '{table_name}'")
    cursor.execute(f"""
        CREATE TABLE '{table_name}' (
            link TEXT PRIMARY KEY,
            summary TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_summary_into_table(table_name, link, summary):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT OR REPLACE INTO '{table_name}' (link, summary)
        VALUES (?, ?)
    """, (link, summary))
    conn.commit()
    conn.close()

def get_all_summaries_from_table(table_name):
    """Fetch all summaries from the given additional‑data table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"SELECT summary FROM '{table_name}'")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def domain_to_table_name(domain):
    sanitized = domain.replace("https://", "").replace("http://", "").replace(".", "_").replace("/", "_")
    return f"{sanitized}_post_logs"

def create_account_post_log_table(domain):
    table_name = domain_to_table_name(domain)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS '{table_name}' (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            post_url TEXT,
            phone TEXT,
            email TEXT,
            categories TEXT,
            category_image TEXT,
            amenities TEXT,
            country TEXT,
            city TEXT,
            location TEXT,
            latitude TEXT,
            longitude TEXT,
            working_hours TEXT,
            video TEXT,
            website TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()
    return table_name

def insert_account_post_log(domain, post_data):
    table_name = domain_to_table_name(domain)
    create_account_post_log_table(domain)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO '{table_name}' (
            post_id, post_url, phone, email, categories, category_image, amenities, country, city,
            location, latitude, longitude, working_hours, website, video, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        post_data["post_id"],
        post_data["post_url"],
        post_data["phone number"],
        post_data["email"],
        post_data['category'],
        post_data['category_image'],
        ",".join(x.strip() for x in post_data["amenities"].split(",")),
        post_data["country"],
        post_data["city"],
        post_data["address"],
        post_data["latitude"],
        post_data["longitude"],
        post_data["working hours"],
        post_data["website"],
        post_data["video"]
    ))
    conn.commit()
    conn.close()

def export_post_logs_to_csv(domain, file_path):
    table_name = domain_to_table_name(domain)
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)
    conn.close()
    df.to_csv(file_path, index=False)

def export_post_logs_to_excel(domain, file_path):
    table_name = domain_to_table_name(domain)
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)
    conn.close()
    df.to_excel(file_path, index=False)

