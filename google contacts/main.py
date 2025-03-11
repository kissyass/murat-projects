import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import sqlite3
import re

##############################################################################
# Shared helper: phone number processing
##############################################################################
def process_phone_number(phone):
    """
    Process a single phone number string, clean it by removing non-digits,
    apply various country-specific patterns, and return the cleaned phone
    and detected country.
    """
    original = phone.strip()
    sanitized = re.sub(r'\D', '', phone)
    cleaned = ""
    country = ""
    if sanitized:
        # Turkey Patterns
        if len(sanitized) == 10 and sanitized.startswith("5"):
            cleaned = f"+90{sanitized}"
            country = "Turkey"
        elif len(sanitized) == 11 and sanitized.startswith("05"):
            cleaned = f"+9{sanitized[1:]}"
            country = "Turkey"
        elif len(sanitized) == 12 and sanitized.startswith("90"):
            cleaned = f"+{sanitized}"
            country = "Turkey"
        elif len(sanitized) == 10 and sanitized.startswith("85"):
            cleaned = f"+90{sanitized}"
            country = "Turkey"
        elif len(sanitized) == 12 and sanitized.startswith("9085"):
            cleaned = f"+{sanitized}"
            country = "Turkey"
        # Russia Patterns
        elif len(sanitized) == 11 and sanitized.startswith("79"):
            cleaned = f"+{sanitized}"
            country = "Russia"
        elif len(sanitized) == 11 and sanitized.startswith("89"):
            cleaned = f"+79{sanitized[2:]}"
            country = "Russia"
        elif len(sanitized) == 11 and sanitized.startswith("84"):
            cleaned = f"+74{sanitized[2:]}"
            country = "Russia"
        elif len(sanitized) == 11 and sanitized.startswith("88"):
            cleaned = f"+78{sanitized[2:]}"
            country = "Russia"
        # Kazakhstan Patterns
        elif len(sanitized) == 11 and sanitized.startswith("87"):
            cleaned = f"+77{sanitized[2:]}"
            country = "Kazakhstan"
        elif len(sanitized) == 11 and sanitized.startswith("77"):
            cleaned = f"+77{sanitized[2:]}"
            country = "Kazakhstan"
        # Luxembourg Patterns
        elif len(sanitized) == 11 and (sanitized.startswith("99") or sanitized.startswith("49")):
            cleaned = f"+352{sanitized}"
            country = "Luxembourg"
        elif len(sanitized) == 14 and sanitized.startswith("352"):
            cleaned = f"+{sanitized}"
            country = "Luxembourg"
        # Indonesia Patterns
        elif len(sanitized) == 11 and (sanitized.startswith("98") or sanitized.startswith("243") or sanitized.startswith("240")):
            cleaned = f"+62{sanitized}"
            country = "Indonesia"
        elif len(sanitized) == 13 and sanitized.startswith("62"):
            cleaned = f"+{sanitized}"
            country = "Indonesia"
        # Germany Patterns
        elif len(sanitized) == 11 and sanitized.startswith("97"):
            cleaned = f"+49{sanitized}"
            country = "Germany"
        elif len(sanitized) == 13 and sanitized.startswith("4997"):
            cleaned = f"+{sanitized}"
            country = "Germany"
        elif len(sanitized) == 11 and sanitized.startswith("6"):
            cleaned = f"+49{sanitized}"
            country = "Germany"
        # US Patterns
        elif len(sanitized) == 10 and sanitized.startswith("775"):
            cleaned = f"+1{sanitized}"
            country = "US"
        elif len(sanitized) == 10 and sanitized.startswith("212"):
            cleaned = f"+1{sanitized}"
            country = "US"
        elif len(sanitized) == 11 and sanitized.startswith("131"):
            cleaned = f"+{sanitized}"
            country = "US"
        # Sweden Patterns
        elif len(sanitized) == 8 and sanitized.startswith("185"):
            cleaned = f"+46{sanitized}"
            country = "Sweden"
        # Taiwan Patterns
        elif len(sanitized) == 11 and sanitized.startswith("100"):
            cleaned = f"+886{sanitized}"
            country = "Taiwan"
        # Uzbekistan Patterns
        elif len(sanitized) == 12 and sanitized.startswith("998"):
            cleaned = f"+{sanitized}"
            country = "Uzbekistan"
        # Kyrgyzstan Patterns
        elif len(sanitized) == 12 and sanitized.startswith("996"):
            cleaned = f"+{sanitized}"
            country = "Kyrgyzstan"
        # Tajikistan Patterns
        elif len(sanitized) == 12 and sanitized.startswith("992"):
            cleaned = f"+{sanitized}"
            country = "Tajikistan"
        # Belarus Patterns
        elif len(sanitized) == 12 and sanitized.startswith("375"):
            cleaned = f"+{sanitized}"
            country = "Belarus"
        # Israel Patterns
        elif len(sanitized) == 12 and sanitized.startswith("972"):
            cleaned = f"+{sanitized}"
            country = "Israel"
        # Ukraine Patterns
        elif len(sanitized) == 12 and sanitized.startswith("380"):
            cleaned = f"+{sanitized}"
            country = "Ukraine"
        # Azerbaijan Patterns
        elif len(sanitized) == 12 and sanitized.startswith("994"):
            cleaned = f"+{sanitized}"
            country = "Azerbaijan"
        # Estonia Patterns
        elif len(sanitized) == 11 and sanitized.startswith("372"):
            cleaned = f"+{sanitized}"
            country = "Estonia"
        # Moldova Patterns
        elif len(sanitized) == 11 and sanitized.startswith("373"):
            cleaned = f"+{sanitized}"
            country = "Moldova"
        # South Africa Patterns
        elif len(sanitized) == 11 and sanitized.startswith("27"):
            cleaned = f"+{sanitized}"
            country = "South Africa"
        # Germany Patterns (alternative)
        elif len(sanitized) == 13 and sanitized.startswith("49"):
            cleaned = f"+{sanitized}"
            country = "Germany"
        # USA Patterns (alternative)
        elif len(sanitized) == 11 and sanitized.startswith("1"):
            cleaned = f"+{sanitized}"
            country = "USA"
        # Colombia Patterns
        elif len(sanitized) == 12 and sanitized.startswith("57"):
            cleaned = f"+{sanitized}"
            country = "Colombia"
        # France Patterns
        elif len(sanitized) == 11 and sanitized.startswith("33"):
            cleaned = f"+{sanitized}"
            country = "France"
        # Italy Patterns
        elif len(sanitized) == 12 and sanitized.startswith("39"):
            cleaned = f"+{sanitized}"
            country = "Italy"
        # Hungary Patterns
        elif len(sanitized) == 11 and sanitized.startswith("36"):
            cleaned = f"+{sanitized}"
            country = "Hungary"
        # Spain Patterns
        elif len(sanitized) == 11 and sanitized.startswith("34"):
            cleaned = f"+{sanitized}"
            country = "Spain"
        # Netherlands Patterns
        elif len(sanitized) == 11 and sanitized.startswith("31"):
            cleaned = f"+{sanitized}"
            country = "Netherlands"
        # Korea, South Patterns
        elif len(sanitized) == 12 and sanitized.startswith("82"):
            cleaned = f"+{sanitized}"
            country = "Korea, South"
        # If the phone already starts with a plus
        elif phone.startswith("+"):
            cleaned = sanitized
            country = "Unknown"
        else:
            cleaned = original
            country = "N/A"
    else:
        cleaned = ""
        country = ""
    return {"original": original, "cleaned": cleaned, "country": country}

##############################################################################
# Utility function to center a window or container
##############################################################################
def center_window(win):
    win.update_idletasks()
    w = win.winfo_reqwidth()
    h = win.winfo_reqheight()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")

##############################################################################
# MainMenuFrame: The start page with two buttons to switch between interfaces
##############################################################################
class MainMenuFrame(tk.Frame):
    def __init__(self, master, controller):
        tk.Frame.__init__(self, master)
        self.controller = controller
        upload_button = tk.Button(self, text="Upload Data to Database",
                                  command=lambda: controller.show_frame("ContactsFrame"))
        upload_button.pack(pady=10)
        filter_button = tk.Button(self, text="Extract Data from DB",
                                  command=lambda: controller.show_frame("FilterFrame"))
        filter_button.pack(pady=10)

##############################################################################
# ContactsFrame: Handles uploading CSV/Excel data to the database
##############################################################################
class ContactsFrame(tk.Frame):
    def __init__(self, master, controller):
        tk.Frame.__init__(self, master)
        self.controller = controller
        self.data = None
        self.columns = []
        self.load_button = tk.Button(self, text="Upload Excel/CSV", command=self.load_file)
        self.load_button.pack(pady=10)
        self.mapping_frame = tk.Frame(self)
        self.mapping_frame.pack(pady=10)
        self.mappings = {}
        self.save_button = tk.Button(self, text="Save to Database", command=self.save_to_db, state=tk.DISABLED)
        self.save_button.pack(pady=10)
        self.clear_button = tk.Button(self, text="Clear Data", command=self.clear_data, state=tk.DISABLED)
        self.clear_button.pack(pady=10)
        back_button = tk.Button(self, text="Back to Main Menu",
                                command=lambda: controller.show_frame("MainMenuFrame"))
        back_button.pack(pady=10)

    def load_file(self):
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
            messagebox.showinfo("Success", f"File loaded successfully with columns: {', '.join(self.columns)}")
            self.create_mapping_widgets()
            self.clear_button.config(state=tk.NORMAL)
            center_window(self.controller.root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def create_mapping_widgets(self):
        for widget in self.mapping_frame.winfo_children():
            widget.destroy()
        tk.Label(self.mapping_frame, text="Full Name (combine up to 3 columns):").grid(row=0, column=0, columnspan=2, sticky="w")
        self.mappings['full_name'] = []
        for i in range(3):
            var = tk.StringVar()
            var.set("None")
            dropdown = tk.OptionMenu(self.mapping_frame, var, "None", *self.columns)
            dropdown.grid(row=1, column=i, padx=5, pady=5)
            self.mappings['full_name'].append(var)
        tk.Label(self.mapping_frame, text="Phone Number:").grid(row=2, column=0, sticky="w")
        self.mappings['phone'] = tk.StringVar()
        self.mappings['phone'].set("None")
        phone_menu = tk.OptionMenu(self.mapping_frame, self.mappings['phone'], "None", *self.columns)
        phone_menu.grid(row=2, column=1, padx=5, pady=5)
        tk.Label(self.mapping_frame, text="Email:").grid(row=3, column=0, sticky="w")
        self.mappings['email'] = tk.StringVar()
        self.mappings['email'].set("None")
        email_menu = tk.OptionMenu(self.mapping_frame, self.mappings['email'], "None", *self.columns)
        email_menu.grid(row=3, column=1, padx=5, pady=5)
        tk.Label(self.mapping_frame, text="Data Source (map column or default value):").grid(row=4, column=0, sticky="w")
        self.mappings['data_source'] = tk.StringVar()
        self.mappings['data_source'].set("None")
        data_source_menu = tk.OptionMenu(self.mapping_frame, self.mappings['data_source'], "None", *self.columns)
        data_source_menu.grid(row=4, column=1, padx=5, pady=5)
        tk.Label(self.mapping_frame, text="or enter fixed value:").grid(row=4, column=2, sticky="w")
        self.fixed_data_source = tk.Entry(self.mapping_frame)
        self.fixed_data_source.grid(row=4, column=3, padx=5, pady=5)
        tk.Label(self.mapping_frame, text="Tags (map column or default value):").grid(row=5, column=0, sticky="w")
        self.mappings['tags'] = tk.StringVar()
        self.mappings['tags'].set("None")
        tags_menu = tk.OptionMenu(self.mapping_frame, self.mappings['tags'], "None", *self.columns)
        tags_menu.grid(row=5, column=1, padx=5, pady=5)
        tk.Label(self.mapping_frame, text="or enter fixed value:").grid(row=5, column=2, sticky="w")
        self.fixed_tags = tk.Entry(self.mapping_frame)
        self.fixed_tags.grid(row=5, column=3, padx=5, pady=5)
        self.save_button.config(state=tk.NORMAL)

    def save_to_db(self):
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
        messagebox.showinfo("Success", "Data saved to database successfully.")

    def clear_data(self):
        self.data = None
        self.columns = []
        for widget in self.mapping_frame.winfo_children():
            widget.destroy()
        self.save_button.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.DISABLED)
        messagebox.showinfo("Cleared", "Data cleared. Please upload a new file.")

##############################################################################
# FilterFrame: Handles filtering/extracting data from the database and export
##############################################################################
class FilterFrame(tk.Frame):
    def __init__(self, master, controller):
        tk.Frame.__init__(self, master)
        self.controller = controller
        self.columns = ["id", "full_name", "phone", "email", "data_source", "tags", "country"]
        # Filtering area
        self.filter_frame = tk.Frame(self)
        self.filter_frame.pack(pady=10, fill="x")
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=10, fill="x")
        # Results area (Treeview)
        self.results_frame = tk.Frame(self)
        self.results_frame.pack(pady=10, fill="both", expand=True)
        self.filter_rows = []
        self.add_filter_row(first=True)
        self.add_filter_button = tk.Button(self.button_frame, text="Add Filter", command=self.add_filter_row)
        self.add_filter_button.pack(side="left", padx=5)
        self.search_button = tk.Button(self.button_frame, text="Search", command=self.search)
        self.search_button.pack(side="left", padx=5)
        # New: Clear Filters & Refresh button
        self.clear_filters_button = tk.Button(self.button_frame, text="Clear Filters & Refresh", command=self.clear_filters)
        self.clear_filters_button.pack(side="left", padx=5)
        self.tree = ttk.Treeview(self.results_frame, columns=self.columns, show="headings")
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.pack(fill="both", expand=True)
        # Export options: checkboxes for columns and export buttons
        self.export_frame = tk.Frame(self)
        self.export_frame.pack(pady=10, fill="x")
        tk.Label(self.export_frame, text="Select columns to export:").pack(anchor="w")
        self.export_vars = {}
        for col in self.columns:
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(self.export_frame, text=col, variable=var)
            cb.pack(side="left", padx=2)
            self.export_vars[col] = var
        self.export_buttons_frame = tk.Frame(self)
        self.export_buttons_frame.pack(pady=5)
        self.export_csv_button = tk.Button(self.export_buttons_frame, text="Export as CSV", command=self.export_csv)
        self.export_csv_button.pack(side="left", padx=5)
        self.export_excel_button = tk.Button(self.export_buttons_frame, text="Export as Excel", command=self.export_excel)
        self.export_excel_button.pack(side="left", padx=5)
        back_button = tk.Button(self, text="Back to Main Menu",
                                command=lambda: controller.show_frame("MainMenuFrame"))
        back_button.pack(pady=10)
        self.load_all_contacts()

    def add_filter_row(self, first=False):
        row_index = len(self.filter_rows)
        row_widgets = {}
        if row_index > 0:
            op_var = tk.StringVar(value="AND")
            op_menu = tk.OptionMenu(self.filter_frame, op_var, "AND", "OR")
            op_menu.grid(row=row_index, column=0, padx=5, pady=5)
            row_widgets["operator"] = op_var
            col_offset = 1
        else:
            col_offset = 0
        col_var = tk.StringVar(value=self.columns[1])
        col_menu = tk.OptionMenu(self.filter_frame, col_var, *self.columns,
                                 command=lambda event, row=row_index: self.update_value_options(row))
        col_menu.grid(row=row_index, column=col_offset, padx=5, pady=5)
        row_widgets["column"] = col_var
        # New: Condition type dropdown (Equals or Not Empty)
        cond_var = tk.StringVar(value="Equals")
        cond_menu = tk.OptionMenu(self.filter_frame, cond_var, "Equals", "Not Empty",
                                  command=lambda val, row=row_index: self.update_value_state(row))
        cond_menu.grid(row=row_index, column=col_offset+1, padx=5, pady=5)
        row_widgets["condition"] = cond_var
        val_var = tk.StringVar(value="")
        val_menu = tk.OptionMenu(self.filter_frame, val_var, "")
        val_menu.grid(row=row_index, column=col_offset+2, padx=5, pady=5)
        row_widgets["value"] = val_var
        row_widgets["value_menu"] = val_menu
        self.filter_rows.append(row_widgets)
        self.update_value_options(row_index)
        self.update_value_state(row_index)

    def update_value_options(self, row_index):
        row_widgets = self.filter_rows[row_index]
        selected_col = row_widgets["column"].get()
        conn = sqlite3.connect("contacts.db")
        cursor = conn.cursor()
        try:
            query = f"SELECT DISTINCT {selected_col} FROM contacts"
            cursor.execute(query)
            results = cursor.fetchall()
            options = sorted({str(r[0]) for r in results if r[0] not in (None, "")})
            if not options:
                options = [""]
        except Exception as e:
            messagebox.showerror("Error", f"Error fetching values: {e}")
            options = [""]
        finally:
            conn.close()
        menu = row_widgets["value_menu"]["menu"]
        menu.delete(0, "end")
        for option in options:
            menu.add_command(
                label=option,
                command=lambda value=option, var=row_widgets["value"]: var.set(value)
            )
        row_widgets["value"].set(options[0] if options else "")

    def update_value_state(self, row_index):
        row_widgets = self.filter_rows[row_index]
        if row_widgets["condition"].get() == "Not Empty":
            row_widgets["value_menu"].config(state="disabled")
        else:
            row_widgets["value_menu"].config(state="normal")

    def build_query(self):
        base_query = "SELECT id, full_name, phone, email, data_source, tags, country FROM contacts"
        conditions = []
        params = []
        for row in self.filter_rows:
            col = row["column"].get()
            cond = row["condition"].get()
            if cond == "Equals":
                val = row["value"].get()
                if val != "":
                    conditions.append(f"{col} = ?")
                    params.append(val)
            elif cond == "Not Empty":
                conditions.append(f"({col} IS NOT NULL AND {col} != '' AND lower({col}) != 'n/a' AND lower({col}) != 'nan')")
        if not conditions:
            return base_query, []
        query = base_query + " WHERE " + conditions[0]
        for i in range(1, len(conditions)):
            op_var = self.filter_rows[i].get("operator")
            op = op_var.get() if op_var else "AND"
            query += f" {op} {conditions[i]}"
        return query, params

    def search(self):
        query, params = self.build_query()
        conn = sqlite3.connect("contacts.db")
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            results = cursor.fetchall()
        except Exception as e:
            messagebox.showerror("Error", f"Query failed: {e}")
            results = []
        finally:
            conn.close()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in results:
            self.tree.insert("", "end", values=row)

    def load_all_contacts(self):
        query = "SELECT id, full_name, phone, email, data_source, tags, country FROM contacts"
        conn = sqlite3.connect("contacts.db")
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            results = cursor.fetchall()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load contacts: {e}")
            results = []
        finally:
            conn.close()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in results:
            self.tree.insert("", "end", values=row)

    def export_csv(self):
        self.export_data("csv")

    def export_excel(self):
        self.export_data("excel")

    def export_data(self, filetype):
        selected_columns = [col for col, var in self.export_vars.items() if var.get()]
        if not selected_columns:
            messagebox.showerror("Error", "No columns selected for export.")
            return
        rows = []
        for item in self.tree.get_children():
            row = self.tree.item(item, "values")
            rows.append(row)
        df = pd.DataFrame(rows, columns=self.columns)
        df = df[selected_columns]
        if filetype == "csv":
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
            if file_path:
                df.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Data exported as CSV to {file_path}")
        elif filetype == "excel":
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
            if file_path:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Success", f"Data exported as Excel to {file_path}")

    def clear_filters(self):
        for widget in self.filter_frame.winfo_children():
            widget.destroy()
        self.filter_rows = []
        self.add_filter_row(first=True)
        self.load_all_contacts()

##############################################################################
# MainApp: Handles switching frames within the same window
##############################################################################
class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Contacts Application")
        self.root.geometry("700x350")
        self.frames = {}
        for F in (MainMenuFrame, ContactsFrame, FilterFrame):
            page_name = F.__name__
            frame = F(self.root, self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("MainMenuFrame")
        center_window(self.root)

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

##############################################################################
# Script entry point
##############################################################################
if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
