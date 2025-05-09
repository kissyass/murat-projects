#!/usr/bin/env python3
"""
Force Rent A Car Updater

A Tkinter GUI to manage multiple WordPress/VikRentCar accounts,
upload Excel-based monthly pricing (with car_id), and push daily fares via REST.
"""

import os
import threading
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pandas as pd
import requests

from datetime import datetime, timedelta

# ── CONFIGURATION ────────────────────────────────────────────────────────
DB_PATH = "app.db"
DATE_FMT = "%Y-%m-%d"


def normalize_domain(d):
    return d.replace("https://", "").replace("http://", "").rstrip("/")


def init_db():
    """
    Initialize the SQLite database with accounts and rates tables.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            domain   TEXT    NOT NULL,
            username TEXT    NOT NULL,
            password TEXT    NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rates (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            car_id     INTEGER NOT NULL,
            car_name   TEXT    NOT NULL,
            min_days   INTEGER NOT NULL,
            max_days   INTEGER NOT NULL,
            jan REAL, feb REAL, mar REAL, apr REAL,
            may REAL, jun REAL, jul REAL, aug REAL,
            sep REAL, oct REAL, nov REAL, decm REAL,
            FOREIGN KEY(account_id) REFERENCES accounts(id)
        )
    """)
    conn.commit()
    conn.close()


def get_car_id_by_name(domain, user, password, name):
    """
    (Still used for testing new accounts)
    Fetch the list of cars from the REST API and return the idcar for 'name'.
    """
    WP_BASE = normalize_domain(domain)
    url = f"https://{WP_BASE}/wp-json/vikrentcar/v1/cars"
    resp = requests.get(url, auth=(user, password), timeout=10)
    resp.raise_for_status()
    cars = resp.json()
    for car in cars:
        if car["name"].lower() == name.lower():
            return int(car["idcar"])
    raise ValueError(f"Car not found: {name!r}")


def update_tariffs(domain, user, password, car_id, prices):
    """
    POST a day→price map to the /tariffs endpoint.
    """
    WP_BASE = normalize_domain(domain)
    url = f"https://{WP_BASE}/wp-json/vikrentcar/v1/tariffs"
    resp = requests.post(
        url,
        auth=(user, password),
        json={"car_id": car_id, "prices": prices},
        timeout=20
    )
    resp.raise_for_status()
    return resp.json()


class App(tk.Tk):
    """
    The main application window, handling frame switching and window centering.
    """

    def __init__(self):
        super().__init__()
        self.title("Force Rent A Car Updater")
        self.resizable(False, False)
        self.win_width, self.win_height = 800, 600
        self._center_window()

        # Shared application state
        self.current_account = None  # (id, domain, username, password)

        # Container for stacked frames
        container = tk.Frame(self, width=self.win_width, height=self.win_height)
        container.place(relx=0.5, rely=0.5, anchor="center")

        # Instantiate all frames
        self.frames = {}
        for F in (
            SelectAccountFrame, NewAccountFrame, ExistingAccountsFrame,
            MainMenuFrame, UploadDataFrame, DataManageFrame, AutoUpdateFrame
        ):
            page = F(container, self)
            self.frames[F] = page
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

        # show only the first page
        self.show_frame(SelectAccountFrame)

    def _center_window(self):
        """
        Center this window on the user's screen.
        """
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - self.win_width) // 2
        y = (sh - self.win_height) // 2
        self.geometry(f"{self.win_width}x{self.win_height}+{x}+{y}")

    def show_frame(self, frame_class):
        """
        Raise the requested frame to the top, calling its on_show() if present.
        """
        frame = self.frames[frame_class]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()


class CenteredFrame(tk.Frame):
    """
    Base frame that centers its children.
    """

    def __init__(self, parent, controller):
        super().__init__(parent,
                         width=controller.win_width,
                         height=controller.win_height)
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)


class SelectAccountFrame(CenteredFrame):
    """
    First screen: choose between creating a new account or loading existing ones.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Select Account", font=("Arial", 24)).pack(pady=40)
        ttk.Button(self, text="New Account",
                   command=lambda: controller.show_frame(NewAccountFrame))\
            .pack(pady=10)
        ttk.Button(self, text="Existing Accounts",
                   command=lambda: controller.show_frame(ExistingAccountsFrame))\
            .pack(pady=10)


class NewAccountFrame(CenteredFrame):
    """
    Screen for adding a new WordPress/VikRentCar account.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Create New Account", font=("Arial", 20)).pack(pady=20)

        form = tk.Frame(self)
        form.pack()

        self.dom = tk.StringVar()
        self.usr = tk.StringVar()
        self.pwd = tk.StringVar()

        for label, var, show in [
            ("Domain:", self.dom, None),
            ("Username:", self.usr, None),
            ("Password:", self.pwd, "*")
        ]:
            row = tk.Frame(form); row.pack(fill="x", pady=5)
            tk.Label(row, text=label, width=12, anchor="e").pack(side="left")
            ttk.Entry(row, textvariable=var, show=show or "", width=40).pack(side="right")

        ttk.Button(self, text="Save & Test Login", command=self._save).pack(pady=20)
        ttk.Button(self, text="← Back",
                   command=lambda: controller.show_frame(SelectAccountFrame))\
            .pack()

    def _save(self):
        d, u, p = self.dom.get().strip(), self.usr.get().strip(), self.pwd.get().strip()
        if not (d and u and p):
            messagebox.showwarning("Missing Data", "All fields are required.")
            return
        try:
            # test the REST endpoint
            get_car_id_by_name(d, u, p, "Dacia Duster")
        except Exception as e:
            messagebox.showerror("Login Failed", str(e))
            return

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO accounts(domain,username,password) VALUES (?,?,?)",
            (d, u, p)
        )
        conn.commit()
        conn.close()

        messagebox.showinfo("Saved", "Account saved successfully.")
        self.controller.show_frame(ExistingAccountsFrame)


class ExistingAccountsFrame(CenteredFrame):
    """
    Screen to list and load previously saved accounts.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Existing Accounts", font=("Arial", 20)).pack(pady=20)
        self.listbox = tk.Listbox(self, height=6, width=50)
        self.listbox.pack()
        ttk.Button(self, text="Load Account", command=self._load).pack(pady=5)
        ttk.Button(self, text="← Back",
                   command=lambda: controller.show_frame(SelectAccountFrame))\
            .pack(pady=10)

    def on_show(self):
        self.listbox.delete(0, tk.END)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id,domain,username FROM accounts")
        for rid, dom, usr in cur.fetchall():
            self.listbox.insert(tk.END, f"{rid} | {dom} | {usr}")
        conn.close()

    def _load(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        rid = int(self.listbox.get(sel).split("|")[0].strip())
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT domain,username,password FROM accounts WHERE id=?", (rid,))
        row = cur.fetchone()
        conn.close()
        if row:
            self.controller.current_account = (rid, row[0], row[1], row[2])
            self.controller.show_frame(MainMenuFrame)


class MainMenuFrame(CenteredFrame):
    """
    Post-login dashboard.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Dashboard", font=("Arial", 24)).pack(pady=20)
        ttk.Button(self, text="Upload Data",
                   command=lambda: controller.show_frame(UploadDataFrame))\
            .pack(pady=5)
        ttk.Button(self, text="Manage Data",
                   command=lambda: controller.show_frame(DataManageFrame))\
            .pack(pady=5)
        ttk.Button(self, text="Start Auto Update",
                   command=lambda: controller.show_frame(AutoUpdateFrame))\
            .pack(pady=5)
        ttk.Button(self, text="Logout",
                   command=lambda: controller.show_frame(SelectAccountFrame))\
            .pack(pady=20)


class UploadDataFrame(CenteredFrame):
    """
    Select an Excel file (must have car_id & car name) and insert into rates.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Upload & Process Excel", font=("Arial", 20)).pack(pady=10)
        self.path_lbl = ttk.Label(self, text="No file selected", foreground="gray")
        self.path_lbl.pack(pady=5)
        ttk.Button(self, text="Select File", command=self._select_file).pack(pady=5)
        ttk.Button(self, text="Process File", command=self._process_file).pack(pady=5)
        ttk.Button(self, text="← Back",
                   command=lambda: controller.show_frame(MainMenuFrame))\
            .pack(pady=20)
        self.filepath = None

    def _select_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if filename:
            self.filepath = filename
            self.path_lbl.config(text=os.path.basename(filename), foreground="black")

    def _process_file(self):
        if not self.filepath:
            messagebox.showwarning("No File", "Please select an Excel file first.")
            return

        try:
            df = pd.read_excel(self.filepath)
        except Exception as e:
            messagebox.showerror("Read Error", str(e))
            return

        required = [
            "car_id", "car",
            "min days", "max days",
            "January","February","March","April",
            "May","June","July","August",
            "September","October","November","December"
        ]
        if not all(col in df.columns for col in required):
            messagebox.showerror(
                "Format Error",
                "Excel must have columns:\n" + ", ".join(required)
            )
            return

        acc_id = self.controller.current_account[0]
        conn = sqlite3.connect(DB_PATH)
        cur  = conn.cursor()
        cur.execute("DELETE FROM rates WHERE account_id=?", (acc_id,))

        for _, row in df.iterrows():
            cid = int(row["car_id"])
            cur.execute(
                """
                INSERT INTO rates
                (account_id,car_id,car_name,min_days,max_days,
                 jan,feb,mar,apr,may,jun,jul,aug,sep,oct,nov,decm)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    acc_id,
                    cid,
                    row["car"],
                    int(row["min days"]),
                    int(row["max days"]),
                    float(row["January"]),
                    float(row["February"]),
                    float(row["March"]),
                    float(row["April"]),
                    float(row["May"]),
                    float(row["June"]),
                    float(row["July"]),
                    float(row["August"]),
                    float(row["September"]),
                    float(row["October"]),
                    float(row["November"]),
                    float(row["December"]),
                )
            )

        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Excel data processed.")
        self.controller.show_frame(MainMenuFrame)


class DataManageFrame(CenteredFrame):
    """
    View, export, change, or add rate data.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Manage Data", font=("Arial", 20)).pack(pady=10)

        columns = (
            "ID", "CarID", "Car", "Min", "Max",
            "Jan","Feb","Mar","Apr","May","Jun",
            "Jul","Aug","Sep","Oct","Nov","Dec"
        )
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=60)
        self.tree.pack()

        btn_frame = tk.Frame(self); btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Export",     command=self._export).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Change Data", command=self._change).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Add Data",    command=self._add).grid(row=0, column=2, padx=5)
        ttk.Button(self, text="← Back",
                   command=lambda: controller.show_frame(MainMenuFrame))\
            .pack(pady=10)

    def on_show(self):
        if not self.controller.current_account:
            messagebox.showwarning("No Account", "Please select an account first.")
            self.controller.show_frame(SelectAccountFrame)
            return
        self._populate()

    def _populate(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        acc_id = self.controller.current_account[0]
        conn = sqlite3.connect(DB_PATH)
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, car_id, car_name, min_days, max_days,
                   jan,feb,mar,apr,may,jun,jul,aug,sep,oct,nov,decm
              FROM rates
             WHERE account_id=?
        """, (acc_id,))
        for row in cur.fetchall():
            self.tree.insert("", tk.END, values=row)
        conn.close()

    def _export(self):
        acc_id = self.controller.current_account[0]
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("""
            SELECT car_id AS "car_id",
                   car_name AS car,
                   min_days AS "min days",
                   max_days AS "max days",
                   jan AS January,
                   feb AS February,
                   mar AS March,
                   apr AS April,
                   may AS May,
                   jun AS June,
                   jul AS July,
                   aug AS August,
                   sep AS September,
                   oct AS October,
                   nov AS November,
                   decm AS December
              FROM rates
             WHERE account_id=?
        """, conn, params=(acc_id,))
        conn.close()

        path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                            filetypes=[("Excel files","*.xlsx")])
        if not path:
            return
        df.to_excel(path, index=False)
        messagebox.showinfo("Exported", f"Data exported to\n{path}")

    def _change(self):
        if not messagebox.askyesno("Confirm","Delete current data and re-upload?"):
            return
        acc_id = self.controller.current_account[0]
        conn = sqlite3.connect(DB_PATH)
        cur  = conn.cursor()
        cur.execute("DELETE FROM rates WHERE account_id=?", (acc_id,))
        conn.commit()
        conn.close()
        self.controller.show_frame(UploadDataFrame)

    def _add(self):
        self.controller.show_frame(UploadDataFrame)


class AutoUpdateFrame(CenteredFrame):
    """
    Run an automatic daily-update pass at midnight, logging each update.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Auto Update", font=("Arial", 20)).pack(pady=10)

        self.log = tk.Text(self, width=80, height=20, state="disabled")
        self.log.pack()

        btn_frame = tk.Frame(self); btn_frame.pack(pady=5)
        self.btn_start = ttk.Button(btn_frame, text="Start", command=self._start)
        self.btn_stop  = ttk.Button(btn_frame, text="Stop",  command=self._stop, state="disabled")
        self.btn_start.grid(row=0, column=0, padx=5)
        self.btn_stop .grid(row=0, column=1, padx=5)

        ttk.Button(self, text="← Back", command=self._back).pack(pady=10)

        self.stop_event = threading.Event()
        self.running    = False
        self.thread     = None

    def log_msg(self, msg):
        self.log.configure(state="normal")
        self.log.insert(tk.END, f"{datetime.now().strftime(DATE_FMT)} {msg}\n")
        self.log.see(tk.END)
        self.log.configure(state="disabled")

    def _worker(self):
        while not self.stop_event.is_set():
            self.log_msg("=== Starting update pass ===")
            idx, domain, user, pwd = self.controller.current_account
            month_idx = datetime.now().month - 1

            conn = sqlite3.connect(DB_PATH)
            cur  = conn.cursor()
            cur.execute("""
                SELECT car_id, car_name, min_days, max_days,
                       jan,feb,mar,apr,may,jun,jul,aug,sep,oct,nov,decm
                  FROM rates
                 WHERE account_id=?
            """, (idx,))
            rows = cur.fetchall()
            conn.close()

            for car_id, car_name, min_d, max_d, *months in rows:
                if self.stop_event.is_set():
                    break
                price   = months[month_idx]
                day_map = {d: price * d for d in range(min_d, max_d+1)}
                try:
                    res = update_tariffs(domain, user, pwd, car_id, day_map)
                    self.log_msg(f"Car {car_id} - {car_name}: updated {res['rows_updated']} rows. Days: {min_d} - {max_d}; price: {price}")
                except Exception as e:
                    self.log_msg(f"Car {car_id} - {car_name}: ERROR {e}")

            self.log_msg("=== Update pass complete ===")

            # sleep until next midnight
            now = datetime.now()
            tomorrow = now + timedelta(days=1)
            next_midnight = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
            wait = (next_midnight - now).total_seconds()

            if self.stop_event.wait(timeout=wait):
                break

        # cleanup
        self.running = False
        self.btn_start.config(state="normal")
        self.btn_stop .config(state="disabled")
        self.log_msg("=== Auto-update stopped ===")

    def _start(self):
        if self.running:
            return
        self.running    = True
        self.stop_event.clear()
        self.btn_start.config(state="disabled")
        self.btn_stop .config(state="normal")
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _stop(self):
        self.stop_event.set()
        self.btn_stop.config(state="disabled")

    def _back(self):
        if self.running and not messagebox.askyesno("Stop Updates?",
                                                    "Please stop auto-update first."):
            return
        self.stop_event.set()
        self.controller.show_frame(MainMenuFrame)


def main():
    try:
        init_db()
        app = App()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Fatal Error", str(e))


if __name__ == "__main__":
    main()
