#!/usr/bin/env python3
"""
Tkinter Excel Processor

Provides a GUI to upload an Excel file, process its contents into a new
spreadsheet with specified columns (including ChatGPT-enhanced content), and
download the resulting file. Also allows setting and verifying a ChatGPT API key.
"""
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import json
import os
import openai
from openai import OpenAI
import re

# Configuration file to store the API key
CONFIG_FILE = "config.json"


class ExcelProcessorApp(tk.Tk):
    """Main application window for the Excel Processor."""

    def __init__(self):
        super().__init__()
        self.title("Excel Processor")
        self._center_window()
        self.file_path = ""
        self.processed_df = None
        self.api_key = None
        self.client = None
        self._create_widgets()
        self._load_api_key()
        self.categories = pd.read_csv("categories.csv").to_dict(orient="records")

    def _center_window(self):
        """Center the window on the user's screen."""
        self.update_idletasks()
        width = 800
        height = 400
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _create_widgets(self):
        """Create and layout the GUI widgets."""
        padding = {"padx": 10, "pady": 10}
        # Upload button
        upload_btn = ttk.Button(self, text="Upload File", command=self.upload_file)
        upload_btn.grid(row=0, column=0, **padding)
        # File path label
        self.file_label = ttk.Label(self, text="No file selected")
        self.file_label.grid(row=0, column=1, **padding)
        # API key button
        api_btn = ttk.Button(self, text="Add ChatGPT API Key", command=self.open_api_key_window)
        api_btn.grid(row=0, column=2, **padding)
        # Process button
        self.process_btn = ttk.Button(self, text="Process File", command=self.process_file)
        self.process_btn.grid(row=1, column=0, **padding)
        # Download button (disabled until processing)
        self.download_btn = ttk.Button(self, text="Download File", command=self.download_file)
        self.download_btn.grid(row=1, column=1, **padding)
        self.download_btn.state(["disabled"])
        # Progress bar (hidden initially)
        self.progress = ttk.Progressbar(self, mode="indeterminate")

    def open_api_key_window(self):
        """Open a dialog to input and verify the ChatGPT API key."""
        wnd = tk.Toplevel(self)
        wnd.title("Set ChatGPT API Key")
        wnd.update_idletasks()
        w, h = 400, 120
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        wnd.geometry(f"{w}x{h}+{x}+{y}")
        ttk.Label(wnd, text="Paste your ChatGPT API key:").grid(row=0, column=0, padx=10, pady=10)
        entry = ttk.Entry(wnd, width=40, show="*")
        entry.grid(row=0, column=1, padx=10, pady=10)

        def save_key():
            key = entry.get().strip()
            if not key:
                messagebox.showwarning("Warning", "API key is required.")
                return
            openai.api_key = key
            try:
                # Test the key by listing models with the new interface
                openai.models.list()
                # Save to config file
                with open(CONFIG_FILE, "w") as f:
                    json.dump({"api_key": key}, f)
                self.api_key = key
                self.client = OpenAI(api_key=self.api_key)
                messagebox.showinfo("Success", "API key saved and verified.")
                wnd.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"API key invalid:\n{e}")

        ttk.Button(wnd, text="Add Key", command=save_key).grid(row=1, column=0, columnspan=2, pady=10)

    def _load_api_key(self):
        """Load API key from config file if present."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    data = json.load(f)
                    key = data.get("api_key")
                    if key:
                        openai.api_key = key
                        self.api_key = key
                        self.client = OpenAI(api_key=self.api_key)
            except Exception:
                pass

    def upload_file(self):
        """Prompt the user to select an Excel or CSV file."""
        try:
            filetypes = [("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")]
            path = filedialog.askopenfilename(title="Select a file", filetypes=filetypes)
            if path:
                self.file_path = path
                self.file_label.config(text=path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to select file:\n{e}")

    def process_file(self):
        """Start processing the uploaded file in a background thread."""
        if not self.file_path:
            messagebox.showwarning("Warning", "No file selected.")
            return
        self.process_btn.state(["disabled"])
        self.progress.grid(row=2, column=0, columnspan=3, padx=10, pady=10)
        self.progress.start()
        thread = threading.Thread(target=self._process_file)
        thread.start()

    def _process_file(self):
        """Read the uploaded file, enhance content via ChatGPT (if key provided), and transform data."""
        try:
            if self.file_path.lower().endswith(".csv"):
                df = pd.read_csv(self.file_path)
            else:
                df = pd.read_excel(self.file_path)

            records = []
            for _, row in df.iterrows():
                title = row.get("Title") or str(row.iloc[0])
                raw_values = row.iloc[2:].fillna("").astype(str).values
                raw_content = "\n".join(raw_values)
                content = raw_content
                if self.client:
                    try:
                        prompt = f"""Please make this data {raw_content} in a better shape, more professional. If any of the information is missing
                        just skip it, no need to include it. No additional messages. """
                        completion = self.client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "You are a company researcher."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        content = completion.choices[0].message.content.strip().replace('*', '').replace('"', '').replace("'", '')
                    except Exception:
                        self.after(0, lambda err=e: messagebox.showerror("Category Error", f"Category generation failed:\n{err}"))

                info = str(row.get("Additional_Info", ""))
                parts = info.splitlines()
                formatted_address = parts[0] if len(parts) > 0 else ""
                website = parts[1] if len(parts) > 1 else ""
                phone = parts[2] if len(parts) > 2 else ""
                location = formatted_address
                if self.client:
                    try:
                        prompt = f"""Please use this data of the company {title}: {raw_content} and {info} and create me output like this:
                        City: the city of this company.
                        Address: the full address of the company. 
                        Phone: the phone number of the company. 
                        Website: the website of the company. 
                        Latitude: find latitude of the address. 
                        Longitude: find longitude of the address. 
                        You have to arrange the data that you have into this schema. If the provided data is not enough try to find online 
                        and if you cant just leave it blank. No additional messages. """
                        
                        completion = self.client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "You are a company researcher."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        data = completion.choices[0].message.content.strip()
                        
                        cleaned_text = data.replace('*', '').replace('"', '').replace("'", '')
                        # Clean and process the metadata text
                        meta_data = {}
                        for line in cleaned_text.strip().split('\n'):
                            match = re.match(r'(.+?):\s*(.+)', line)
                            if match:
                                key = match.group(1).strip()
                                value = match.group(2).strip()
                                meta_data[key] = value
                    except Exception:
                        self.after(0, lambda err=e: messagebox.showerror("Category Error", f"Category generation failed:\n{err}"))

                record = {
                    "Title": title,
                    "Content": content,
                    "Status": "yay",
                    "Categories": "",
                    "Regions": meta_data.get("City", ""),
                    "Post type": "job_listing",
                    "Job Expires": "6/13/50",
                    "Job Location": meta_data.get("Address", parts[0] if parts else location),
                    "Job Logo": "",
                    "Job Phone": meta_data.get("Phone", parts[2] if len(parts)>2 else phone),
                    "Job Price Range": "notsay",
                    "Job Website": meta_data.get("Website", parts[1] if len(parts)>1 else website),
                    "Geolocated": 1,
                    "Geolocation City": meta_data.get("City", ""),
                    "Geolocation Formatted Address": meta_data.get("Address", parts[0] if parts else formatted_address),
                    "Geolocation Lat": meta_data.get("Latitude", ""),
                    "Geolocation Long": meta_data.get("Longitude", ""),
                }
                records.append(record)

                if self.client and self.categories:
                    cat_list = json.dumps(self.categories, ensure_ascii=False)
                    prompt = (
                        f"Categories: {cat_list}\n\n"
                        f"Title: {title}\n"
                        f"Content: {content}\n\n"
                        "Choose the best matching category. Get the logo from mother or child category. Respond with JSON:\n"
                        "{ \"category_ids\": [mother_id, child_id], \"logo_url\": \"…\" }"
                    )
                    resp = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role":"system","content":"You are a categorization assistant."},
                            {"role":"user","content":prompt}
                        ]
                    )
                    try:
                        cat_data = json.loads(resp.choices[0].message.content)
                        record["Categories"] = ",".join(str(i) for i in cat_data["category_ids"])
                        record["Job Logo"]   = cat_data["logo_url"]
                    except Exception:
                        # fallback if parsing fails
                        record["Categories"] = ""
                        record["Job Logo"]   = ""

            processed_df = pd.DataFrame(records)
            self.after(0, self._on_process_complete, processed_df)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Processing failed:\n{e}"))

    def _on_process_complete(self, df):
        self.progress.stop()
        self.progress.grid_forget()
        self.processed_df = df
        self.download_btn.state(["!disabled"])
        self.process_btn.state(["!disabled"])
        messagebox.showinfo("Info", "File processed successfully.")

    def download_file(self):
        if self.processed_df is None:
            messagebox.showwarning("Warning", "No processed data available.")
            return
        try:
            path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")],
            )
            if not path:
                return
            if path.lower().endswith(".csv"):
                self.processed_df.to_csv(path, index=False)
            else:
                self.processed_df.to_excel(path, index=False)
            messagebox.showinfo("Info", f"File saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}" )


def main():
    app = ExcelProcessorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
