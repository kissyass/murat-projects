#!/usr/bin/env python3
"""
price_updater.py

A Tkinter GUI tool that lets you create or select
an “account” record, then run your hotel‑price scraping
and WordPress update as before—now backed by SQLite.
"""

import os
import re
import sqlite3
import threading
import time
import requests
from datetime import date, timedelta, datetime
from tkinter import (
    Tk, Frame, Label, Entry, Button, OptionMenu, StringVar,
    Listbox, filedialog, messagebox, END
)
from tkinter.scrolledtext import ScrolledText
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from main import *
from selenium.common.exceptions import WebDriverException
# ----------------------------------------------------------------
# ---------- 1. DATABASE LAYER  ---------------------------------
# ----------------------------------------------------------------

DB_FILE = "accounts.db"

def init_db():
    """Ensure the accounts table exists."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY,
        domain TEXT, username TEXT, password TEXT,
        page_url TEXT,
        etstur_link TEXT, trivago_link TEXT,
        tatilbudur_link TEXT, otelz_link TEXT,
        otelz_city TEXT, otelz_people INTEGER,
        logo_etstur TEXT, logo_trivago TEXT,
        logo_tatilbudur TEXT, logo_otelz TEXT
    )
    """)
    conn.commit()
    conn.close()

def save_account(data: dict):
    """
    Insert a new account record and return its ID.
    Expects a dict with all 14 keys matching the table columns (except id).
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    placeholders = ",".join("?" for _ in data)
    cols = ",".join(data.keys())
    cur.execute(f"INSERT INTO accounts ({cols}) VALUES ({placeholders})",
                tuple(data.values()))
    conn.commit()
    aid = cur.lastrowid
    conn.close()
    return aid

def list_accounts():
    """Return list of (id, domain, username) for existing accounts."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, domain, username FROM accounts")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_account(aid: int):
    """Load one account record as a dict by ID."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM accounts WHERE id=?", (aid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))

# ----------------------------------------------------------------
# ---------- 2. COMMON UTILITIES & SCRAPERS  ---------------------
# ----------------------------------------------------------------

def get_chrome_driver(headless=True):
    opts = Options()
    if headless:
        opts.add_argument("--headless")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--disable-gpu")
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)

def clean_price(price_str):
    digits = re.sub(r"\D", "", price_str)
    return int(digits) if digits else None

def extract_price_with_retry(fn, url, max_attempts=3):
    for i in range(max_attempts):
        driver = get_chrome_driver()
        try:
            raw = fn(driver, url)
            p = clean_price(raw)
            if p is not None:
                print(f"[✓] {url} → {p}")
                return p
            print(f"[!] no price at attempt {i+1}")
        except Exception as e:
            print(f"[!] error on attempt {i+1}: {e}")
        finally:
            driver.quit()
            time.sleep(1)
    return None

def get_price_etstur(driver, url):
    driver.get(url); time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    el = soup.find("p", class_="amount")
    return el.get_text(strip=True) if el else ""

def get_price_trivago(driver, url):
    driver.get(url); time.sleep(8)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    el = soup.find(attrs={"data-testid": "recommended-price"})
    return el.get_text(strip=True) if el else ""

def get_price_tatil(driver, url):
    driver.get(url); time.sleep(8)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    el = soup.find("div", class_="c-card__current-price")
    return el.get_text(strip=True) if el else ""

# Otelz custom extractor omitted here for brevity—
# copy your existing get_price_otelz_custom + retry wrapper.

# URL‑updaters: update_etstur_link, update_trivago_link, update_tatilbudur_link
# copy your existing functions here unchanged.

# build_container_html, fetch_page, update_page_content, upload_media, etc.
# copy your existing WordPress helpers here unchanged.

# ----------------------------------------------------------------
# ---------- 3. GUI CLASSES & FLOW  ------------------------------
# ----------------------------------------------------------------

class PriceUpdaterApp(Tk):
    def __init__(self):
        super().__init__()

        self.title("Price Updater")
        init_db()
            
        # ────────── NEW: set size & center ──────────
        width, height = 800, 600
        self.geometry(f"{width}x{height}")
        self.update_idletasks()  # ensure winfo_* is accurate
        x = (self.winfo_screenwidth()  - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        # ─────────────────────────────────────────────

        self.selected_account = None  # will hold the dict of the logged‑in record

        # Shared language var
        self.lang_var = StringVar(value="eng")

        # Frames
        self.login_frame = LoginFrame(self)
        self.config_frame = ConfigFrame(self)
        self.main_frame   = MainFrame(self)

        self.login_frame.pack(fill="both", expand=True)

    def show_config(self):
        self.login_frame.pack_forget()
        self.config_frame.pack(fill="both", expand=True)

    def show_existing_list(self):
        self.login_frame.pack_forget()
        self.login_frame.populate_list()
        self.login_frame.listbox.pack(side="left", fill="y")
        self.login_frame.login_button.pack(pady=5)

    def login_existing(self, aid):
        self.selected_account = get_account(aid)
        self.config_frame.pack_forget()
        self.login_frame.pack_forget()
        self.main_frame.load_account(self.selected_account)
        self.main_frame.pack(fill="both", expand=True)

    def login_new(self):
        self.show_config()

    def finish_config(self, data):
        # data validated already
        aid = save_account(data)
        self.selected_account = get_account(aid)
        self.config_frame.pack_forget()
        self.main_frame.load_account(self.selected_account)
        self.main_frame.pack(fill="both", expand=True)

class LoginFrame(Frame):
    def __init__(self, master):
        super().__init__(master, padx=20, pady=20)
        Label(self, text="Select Account Mode").pack(pady=10)
        Button(self, text="➕ New Account", command=master.login_new).pack(fill="x")
        Button(self, text="👥 Existing Account", command=self.show_list).pack(fill="x", pady=5)

        # Hidden until “Existing” clicked:
        self.listbox = Listbox(self)
        self.login_button = Button(self, text="Login", command=self.on_login)

    def show_list(self):
        self.listbox.delete(0, END)
        for aid, domain, user in list_accounts():
            self.listbox.insert(END, f"{aid}: {domain} — {user}")
        self.listbox.pack(side="left", fill="y")
        self.login_button.pack(pady=5)

    def on_login(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Choose one", "Please select an account first.")
            return
        aid = int(self.listbox.get(sel[0]).split(":")[0])
        self.master.login_existing(aid)

class ConfigFrame(Frame):
    FIELDS = [
        ("domain", "Website Domain"),
        ("username", "WP Username"),
        ("password", "WP Password"),
        ("page_url", "Page to Post"),
        ("etstur_link", "Etstur Link"),
        ("trivago_link", "Trivago Link"),
        ("tatilbudur_link", "Tatilbudur Link"),
        ("otelz_link", "Otelz Base Link"),
        ("otelz_city", "Otelz City"),
        ("otelz_people", "Otelz # Adults"),
    ]
    LOGO_KEYS = [
        ("logo_etstur", "Etstur Logo"),
        ("logo_trivago", "Trivago Logo"),
        ("logo_tatilbudur", "Tatilbudur Logo"),
        ("logo_otelz", "Otelz Logo")
    ]

    def __init__(self, master):
        super().__init__(master, padx=20, pady=20)
        self.entries = {}
        for i, (k, lbl) in enumerate(self.FIELDS):
            Label(self, text=lbl).grid(row=i, column=0, sticky="w")
            e = Entry(self, width=40)
            e.grid(row=i, column=1, pady=2)
            self.entries[k] = e

        self.logo_paths = {}
        self.logo_labels = {}   # map logo_key → Label showing path
        # now build the logo rows
        for j, (key, label_text) in enumerate(self.LOGO_KEYS, start=len(self.FIELDS)):
            Label(self, text=label_text).grid(row=j, column=0, sticky="w")
            btn = Button(self, text="Select…",
                         command=lambda k=key: self.select_logo(k))
            btn.grid(row=j, column=1, sticky="w", pady=2)

            # ← add a Label in column 2 to show the path
            path_lbl = Label(self, text="(no file)")
            path_lbl.grid(row=j, column=2, sticky="w", padx=10)
            self.logo_labels[key] = path_lbl

        Button(self, text="Save & Continue", command=self.on_save).grid(
            row=len(self.FIELDS)+len(self.LOGO_KEYS), column=0, columnspan=2, pady=10
        )

    def select_logo(self, key):
        path = filedialog.askopenfilename(
            title="Select logo PNG/WebP",
            filetypes=[
                ("Image files", "*.png *.webp *.jpg *.jpeg"),
                ("PNG only", "*.png"),
                ("WEBP only", "*.webp"),
                ("JPEG only", ("*.jpg","*.jpeg")),
            ]
        )
        if not path:
            return

        # store it
        self.logo_paths[key] = path

        # update the label next to the button
        display_name = os.path.basename(path)
        self.logo_labels[key].config(text=display_name)
    
    def validate_with_selenium(self, link):
        driver = get_chrome_driver(headless=True)
        try:
            driver.get(link)
            time.sleep(3)
            code = driver.execute_script("return document.readyState")
            # you could also check driver.title or page_source for “403” patterns
            return True
        except WebDriverException as e:
            return False
        finally:
            driver.quit()

    def on_save(self):
        # Collect
        data = {k: self.entries[k].get().strip() for k,_ in self.FIELDS}
        data["otelz_people"] = int(data["otelz_people"] or 1)
        # Add logos
        for k in self.logo_paths:
            data[k] = self.logo_paths[k]
        # --- VALIDATION ---
        # 1) WP login test
        if not test_wp_login(data["domain"], data["username"], data["password"], data["page_url"]):
            return
        # 2) HEAD on each link
        # in on_save:
        for link in (data["etstur_link"], data["trivago_link"],
                    data["tatilbudur_link"], data["otelz_link"]):
            ok = self.validate_with_selenium(link)
            if not ok:
                messagebox.showerror("Link Error", f"Failed to load:\n{link}")
                return

        # PASS
        self.master.finish_config(data)

class MainFrame(Frame):
    def __init__(self, master):
        super().__init__(master, padx=20, pady=20)
        # Language selector
        Label(self, text="Language:").grid(row=0, column=0, sticky="w")
        OptionMenu(self, master.lang_var, "eng","tr").grid(row=0, column=1, sticky="w")

        Label(self, text="Interval (min):").grid(row=1, column=0, sticky="w")
        self.interval_entry = Entry(self, width=5); self.interval_entry.grid(row=1, column=1, sticky="w")
        self.interval_entry.insert(0, "30")

        Button(self, text="Run Update", command=self.on_run).grid(row=2, column=0, pady=5)
        Button(self, text="Start Auto", command=self.on_start).grid(row=2, column=1)
        Button(self, text="Stop Auto", command=self.on_stop).grid(row=2, column=2)

        self.log = ScrolledText(self, width=80, height=20)
        self.log.grid(row=3, column=0, columnspan=3, pady=10)

        self.auto_job = None

    def load_account(self, acct):
        """Called once after login—store account for update calls."""
        self.account = acct
        self.log.insert(END, f"Loaded account: {acct['domain']} / {acct['username']}\n")

    def on_run(self):
        threading.Thread(target=self.run_update, daemon=True).start()

    def run_update(self):
        # Redirect prints into the log
        import sys
        class TOut:
            def write(self,s): self_log.insert(END, s)
            def flush(self): pass
        self_log = self.log
        old = sys.stdout; sys.stdout = TOut()

        try:
            # Here, call your existing update_wordpress()
            # but pass self.account and master.lang_var.get() instead of env.txt
            update_wordpress_with_account(self.account, self.master.lang_var.get())
        except Exception as e:
            print(f"[Error] {e}")
        finally:
            sys.stdout = old

    def on_start(self):
        interval = int(self.interval_entry.get())
        def loop():
            self.run_update()
            self.auto_job = self.after(interval*60*1000, loop)
        loop()

    def on_stop(self):
        if self.auto_job:
            self.after_cancel(self.auto_job)
            self.auto_job = None
            self.log.insert(END, "Auto‐update stopped.\n")

# ----------------------------------------------------------------
# ---------- 4. STUBBED HELPERS FOR DEMO PURPOSES  ---------------
# ----------------------------------------------------------------

def test_wp_login(domain, user, pwd, page_url):
    """Quick check that we can fetch the WP page slug."""
    try:
        from urllib.parse import urlparse
        slug = urlparse(page_url).path.strip("/")
        # call your fetch_page(domain, slug, user, pwd)
        p = fetch_page(domain, slug, user, pwd)
        if p is None:
            messagebox.showerror("Login Failed", "Could not fetch page with those credentials.")
            return False
        return True
    except Exception as e:
        messagebox.showerror("WP Error", str(e))
        return False

def update_wordpress_with_account(account, lang):
    """
    Adapt your original `update_wordpress()` logic
    to accept `account` dict + `lang`.
    - Read the links from account: account["etstur_link"], etc.
    - Use account["domain"], account["username"], account["password"], account["page_url"]
    - Pass `lang` into build_container_html or wherever you need it.
    You can literally copy/paste your existing function body here,
    replacing the `env.txt` read with the `account[...]` lookups.
    """
    # … your existing code goes here …
    print("Running update for:", account["domain"], "lang=", lang)
    # For demo:
    time.sleep(2)
    print("Update complete!\n")

# ----------------------------------------------------------------
# ---------- 5. ENTRY POINT  -------------------------------------
# ----------------------------------------------------------------

def main():
    app = PriceUpdaterApp()
    app.mainloop()

if __name__ == "__main__":
    main()
