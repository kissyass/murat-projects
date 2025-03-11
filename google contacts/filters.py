import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd # type: ignore
import sqlite3
from translations import translations

##############################################################################
# FilterFrame: Handles filtering/extracting data from the database, export, and new filter type
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
        self.add_filter_button = tk.Button(self.button_frame, command=self.add_filter_row)
        self.add_filter_button.pack(side="left", padx=5)
        self.search_button = tk.Button(self.button_frame, command=self.search)
        self.search_button.pack(side="left", padx=5)
        self.clear_filters_button = tk.Button(self.button_frame, command=self.clear_filters)
        self.clear_filters_button.pack(side="left", padx=5)
        self.tree = ttk.Treeview(self.results_frame, columns=self.columns, show="headings")
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.pack(fill="both", expand=True)
        # Export options
        self.export_frame = tk.Frame(self)
        self.export_frame.pack(pady=10, fill="x")
        self.export_label = tk.Label(self.export_frame)
        self.export_label.pack(anchor="w")
        self.export_vars = {}
        for col in self.columns:
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(self.export_frame, variable=var, text=col)
            cb.pack(side="left", padx=2)
            self.export_vars[col] = var
        self.export_buttons_frame = tk.Frame(self)
        self.export_buttons_frame.pack(pady=5)
        self.export_csv_button = tk.Button(self.export_buttons_frame, command=self.export_csv)
        self.export_csv_button.pack(side="left", padx=5)
        self.export_excel_button = tk.Button(self.export_buttons_frame, command=self.export_excel)
        self.export_excel_button.pack(side="left", padx=5)
        self.back_button = tk.Button(self, command=lambda: self.controller.show_frame("MainMenuFrame"))
        self.back_button.pack(pady=10)
        self.load_all_contacts()

    def update_texts(self):
        t = translations[self.controller.lang]
        self.add_filter_button.config(text=t["add_filter"])
        self.search_button.config(text=t["search"])
        self.clear_filters_button.config(text=t["clear_filters"])
        self.export_label.config(text=t["select_export"])
        self.export_csv_button.config(text=t["export_csv"])
        self.export_excel_button.config(text=t["export_excel"])
        self.back_button.config(text=t["back_main"])
        # Update condition dropdown labels if needed by iterating filter rows.
        for row in self.filter_rows:
            # If the condition dropdown exists, update its menu
            cond = row.get("condition")
            if cond:
                # Reset condition value to current (will be updated by re-creating the menu)
                current = cond.get()
                cond_menu = row.get("condition_menu")
                if cond_menu:
                    # Clear and add new options from translation dictionary.
                    menu = cond_menu["menu"]
                    menu.delete(0, "end")
                    for option in [t["equals"], t["not_empty"]]:
                        menu.add_command(label=option, command=lambda opt=option, var=cond: var.set(opt))
                    cond.set(t["equals"])  # default back to Equals

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
        # New: Condition dropdown (Equals or Not Empty)
        cond_var = tk.StringVar(value=translations[self.controller.lang]["equals"])
        cond_menu = tk.OptionMenu(self.filter_frame, cond_var, translations[self.controller.lang]["equals"],
                                  translations[self.controller.lang]["not_empty"],
                                  command=lambda val, row=row_index: self.update_value_state(row))
        cond_menu.grid(row=row_index, column=col_offset+1, padx=5, pady=5)
        row_widgets["condition"] = cond_var
        row_widgets["condition_menu"] = cond_menu
        val_var = tk.StringVar(value="")
        val_menu = tk.OptionMenu(self.filter_frame, val_var, "")
        val_menu.grid(row=row_index, column=col_offset+2, padx=5, pady=5)
        row_widgets["value"] = val_var
        row_widgets["value_menu"] = val_menu
        self.filter_rows.append(row_widgets)
        self.update_value_options(row_index)
        self.update_value_state(row_index)

    def update_value_options(self, row_index):
        t = translations[self.controller.lang]
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
            messagebox.showerror(t["error"], f"{t['error_fetch_values']}: {e}")
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
        if row_widgets["condition"].get() == translations[self.controller.lang]["not_empty"]:
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
            if cond == translations[self.controller.lang]["equals"]:
                val = row["value"].get()
                if val != "":
                    conditions.append(f"{col} = ?")
                    params.append(val)
            elif cond == translations[self.controller.lang]["not_empty"]:
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
        t = translations[self.controller.lang]
        query, params = self.build_query()
        conn = sqlite3.connect("contacts.db")
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            results = cursor.fetchall()
        except Exception as e:
            messagebox.showerror(t["error"], f"{t['query_fail']}: {e}")
            results = []
        finally:
            conn.close()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in results:
            self.tree.insert("", "end", values=row)

    def load_all_contacts(self):
        t = translations[self.controller.lang]
        query = "SELECT id, full_name, phone, email, data_source, tags, country FROM contacts"
        conn = sqlite3.connect("contacts.db")
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            results = cursor.fetchall()
        except Exception as e:
            messagebox.showerror(t["error"], f"{t['contacts_load_fail']}: {e}")
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
        t = translations[self.controller.lang]
        selected_columns = [col for col, var in self.export_vars.items() if var.get()]
        if not selected_columns:
            messagebox.showerror(t["error"], t["no_columns_selected"])
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
                messagebox.showinfo(t["success"], f"{t['data_exported_csv']} {file_path}")
        elif filetype == "excel":
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
            if file_path:
                df.to_excel(file_path, index=False)
                messagebox.showinfo(t["success"], f"{t['data_exported_excel']} {file_path}")

    def clear_filters(self):
        for widget in self.filter_frame.winfo_children():
            widget.destroy()
        self.filter_rows = []
        self.add_filter_row(first=True)
        self.load_all_contacts()

    def update_texts(self):
        t = translations[self.controller.lang]
        self.add_filter_button.config(text=t["add_filter"])
        self.search_button.config(text=t["search"])
        self.clear_filters_button.config(text=t["clear_filters"])
        self.export_label.config(text=t["select_export"])
        self.export_csv_button.config(text=t["export_csv"])
        self.export_excel_button.config(text=t["export_excel"])
        self.back_button.config(text=t["back_main"])
        # Also update each filter row's condition options:
        for row in self.filter_rows:
            cond_var = row.get("condition")
            cond_menu = row.get("condition_menu")
            if cond_menu:
                menu = cond_menu["menu"]
                menu.delete(0, "end")
                for option in [t["equals"], t["not_empty"]]:
                    menu.add_command(label=option, command=lambda opt=option, var=cond_var: var.set(opt))
                cond_var.set(t["equals"])
            else:
                # If condition menu not saved, recreate it.
                pass
