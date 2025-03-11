from phone_numbers import process_phone_number
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import sqlite3
from translations import translations
from utility import center_window

##############################################################################
# ContactsFrame: Handles uploading CSV/Excel data to the database
##############################################################################
class ContactsFrame(tk.Frame):
    def __init__(self, master, controller):
        tk.Frame.__init__(self, master)
        self.controller = controller
        self.data = None
        self.columns = []
        self.load_button = tk.Button(self, command=self.load_file)
        self.load_button.pack(pady=10)
        self.mapping_frame = tk.Frame(self)
        self.mapping_frame.pack(pady=10)
        self.mappings = {}
        self.save_button = tk.Button(self, command=self.save_to_db, state=tk.DISABLED)
        self.save_button.pack(pady=10)
        self.clear_button = tk.Button(self, command=self.clear_data, state=tk.DISABLED)
        self.clear_button.pack(pady=10)
        self.back_button = tk.Button(self, command=lambda: self.controller.show_frame("MainMenuFrame"))
        self.back_button.pack(pady=10)

    def update_texts(self):
        t = translations[self.controller.lang]
        self.load_button.config(text=t["upload_file"])
        self.save_button.config(text=t["save_db"])
        self.clear_button.config(text=t["clear_data"])
        self.back_button.config(text=t["back_main"])
        # Update mapping labels inside mapping_frame:
        for widget in self.mapping_frame.winfo_children():
            widget.destroy()
        tk.Label(self.mapping_frame, text=t["full_name"]).grid(row=0, column=0, columnspan=2, sticky="w")
        self.mappings['full_name'] = []
        for i in range(3):
            var = tk.StringVar()
            var.set("None")
            dropdown = tk.OptionMenu(self.mapping_frame, var, "None", *self.columns)
            dropdown.grid(row=1, column=i, padx=5, pady=5)
            self.mappings['full_name'].append(var)
        tk.Label(self.mapping_frame, text=t["phone"]).grid(row=2, column=0, sticky="w")
        self.mappings['phone'] = tk.StringVar()
        self.mappings['phone'].set("None")
        phone_menu = tk.OptionMenu(self.mapping_frame, self.mappings['phone'], "None", *self.columns)
        phone_menu.grid(row=2, column=1, padx=5, pady=5)
        tk.Label(self.mapping_frame, text=t["email"]).grid(row=3, column=0, sticky="w")
        self.mappings['email'] = tk.StringVar()
        self.mappings['email'].set("None")
        email_menu = tk.OptionMenu(self.mapping_frame, self.mappings['email'], "None", *self.columns)
        email_menu.grid(row=3, column=1, padx=5, pady=5)
        tk.Label(self.mapping_frame, text=t["data_source"]).grid(row=4, column=0, sticky="w")
        self.mappings['data_source'] = tk.StringVar()
        self.mappings['data_source'].set("None")
        data_source_menu = tk.OptionMenu(self.mapping_frame, self.mappings['data_source'], "None", *self.columns)
        data_source_menu.grid(row=4, column=1, padx=5, pady=5)
        tk.Label(self.mapping_frame, text=t["or_fixed"]).grid(row=4, column=2, sticky="w")
        self.fixed_data_source = tk.Entry(self.mapping_frame)
        self.fixed_data_source.grid(row=4, column=3, padx=5, pady=5)
        tk.Label(self.mapping_frame, text=t["tags"]).grid(row=5, column=0, sticky="w")
        self.mappings['tags'] = tk.StringVar()
        self.mappings['tags'].set("None")
        tags_menu = tk.OptionMenu(self.mapping_frame, self.mappings['tags'], "None", *self.columns)
        tags_menu.grid(row=5, column=1, padx=5, pady=5)
        tk.Label(self.mapping_frame, text=t["or_fixed"]).grid(row=5, column=2, sticky="w")
        self.fixed_tags = tk.Entry(self.mapping_frame)
        self.fixed_tags.grid(row=5, column=3, padx=5, pady=5)
        self.save_button.config(state=tk.NORMAL)

    def load_file(self):
        t = translations[self.controller.lang]
        file_path = filedialog.askopenfilename(
            title="Select Excel or CSV file",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")]
        )
        if not file_path:
            return
        try:
            if file_path.endswith('.csv'):
                self.data = pd.read_csv(file_path)
            else:
                self.data = pd.read_excel(file_path)
            self.columns = list(self.data.columns)
            messagebox.showinfo(t["success"], f"{t['file_load_success']}: {', '.join(self.columns)}")
            self.create_mapping_widgets()
            self.clear_button.config(state=tk.NORMAL)
            center_window(self.controller.root)
        except Exception as e:
            messagebox.showerror(t["error"], f"{t['file_load_fail']}: {e}")

    def create_mapping_widgets(self):
        self.update_texts()

    def save_to_db(self):
        t = translations[self.controller.lang]
        conn = sqlite3.connect("contacts.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT,
                phone TEXT,
                email TEXT,
                data_source TEXT,
                tags TEXT,
                country TEXT
            )
        """)
        for index, row in self.data.iterrows():
            full_name_parts = []
            for var in self.mappings['full_name']:
                col = var.get()
                if col != "None":
                    full_name_parts.append(str(row[col]))
            full_name = " ".join(full_name_parts) if full_name_parts else ""
            phone_col = self.mappings['phone'].get()
            if phone_col != "None":
                phone_raw = str(row[phone_col]).strip()
                if phone_raw:
                    phone_info = process_phone_number(phone_raw)
                    phone_cleaned = phone_info["cleaned"]
                    country = phone_info["country"]
                else:
                    phone_cleaned = ""
                    country = ""
            else:
                phone_cleaned = ""
                country = ""
            email_col = self.mappings['email'].get()
            email = str(row[email_col]) if email_col != "None" else ""
            data_source_col = self.mappings['data_source'].get()
            if data_source_col != "None":
                data_source = str(row[data_source_col])
            else:
                data_source = self.fixed_data_source.get().strip()
            tags_col = self.mappings['tags'].get()
            if tags_col != "None":
                tags = str(row[tags_col])
            else:
                tags = self.fixed_tags.get().strip()
            cursor.execute("""
                INSERT INTO contacts (full_name, phone, email, data_source, tags, country)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (full_name, phone_cleaned, email, data_source, tags, country))
        conn.commit()
        conn.close()
        messagebox.showinfo(t["success"], t["data_saved_db"])

    def clear_data(self):
        t = translations[self.controller.lang]
        self.data = None
        self.columns = []
        for widget in self.mapping_frame.winfo_children():
            widget.destroy()
        self.save_button.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.DISABLED)
        messagebox.showinfo(t["cleared"], t["data_cleared"])
