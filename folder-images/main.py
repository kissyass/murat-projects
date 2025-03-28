import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import pandas as pd
import os
import requests
import threading

class App:
    def __init__(self, master):
        self.master = master
        master.title("Image Downloader")

        # Center the window (width=600, height=250)
        self.center_window(600, 250)

        # Variable to store the file path
        self.file_path = None

        # Upload Button
        self.upload_button = tk.Button(master, text="Upload File", command=self.upload_file)
        self.upload_button.pack(pady=10)

        # Label to display uploaded file path
        self.file_label = tk.Label(master, text="No file uploaded", wraplength=500)
        self.file_label.pack(pady=5)

        # Process Button (disabled until a file is uploaded)
        self.process_button = tk.Button(master, text="Process", command=self.process_file, state=tk.DISABLED)
        self.process_button.pack(pady=10)

        # Progress Bar
        self.progress_bar = ttk.Progressbar(master, orient="horizontal", length=500, mode="determinate")
        self.progress_bar.pack(pady=10)
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = 100

        # Status Label to show progress
        self.status_label = tk.Label(master, text="")
        self.status_label.pack(pady=5)

    def center_window(self, width, height):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.master.geometry(f"{width}x{height}+{x}+{y}")

    def upload_file(self):
        filetypes = [("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv"), ("All files", "*.*")]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            self.file_path = path
            self.file_label.config(text=f"{self.file_path} is uploaded")
            self.process_button.config(state=tk.NORMAL)

    def process_file(self):
        if not self.file_path:
            messagebox.showwarning("No file", "Please upload a file first.")
            return
        
        # Disable buttons during processing
        self.upload_button.config(state=tk.DISABLED)
        self.process_button.config(state=tk.DISABLED)
        
        # Run processing in a separate thread to avoid freezing the UI
        threading.Thread(target=self._process_file_thread, daemon=True).start()

    def _process_file_thread(self):
        self.update_status("Processing...")
        try:
            # Read file based on its extension
            ext = os.path.splitext(self.file_path)[1].lower()
            if ext in [".xlsx", ".xls"]:
                df = pd.read_excel(self.file_path)
            elif ext == ".csv":
                df = pd.read_csv(self.file_path)
            else:
                self.show_error("Unsupported file", "File type not supported.")
                return

            total_rows = len(df)
            for index, row in df.iterrows():
                id_val = row['no']
                title_val = row['Title']
                images_str = row['Images']
                folder_name = f"{id_val}-{title_val}"
                folder_name = self.sanitize_filename(folder_name)

                # Create the folder if it doesn't exist
                if not os.path.exists(folder_name):
                    os.makedirs(folder_name)

                # Split the images cell by comma and download each image
                image_links = images_str.split(',')
                for i, link in enumerate(image_links):
                    link = link.strip()
                    if link:
                        try:
                            response = requests.get(link, stream=True)
                            if response.status_code == 200:
                                image_path = os.path.join(folder_name, f"image_{i+1}.jpg")
                                with open(image_path, 'wb') as f:
                                    for chunk in response.iter_content(1024):
                                        f.write(chunk)
                        except Exception as e:
                            print(f"Error downloading {link}: {e}")

                # Update progress bar after each row
                progress = ((index + 1) / total_rows) * 100
                self.update_progress(progress)

            self.update_status("Processing Completed!")
        except Exception as e:
            self.show_error("Error", str(e))
            self.update_status("Processing Failed.")
        finally:
            # Re-enable buttons after processing
            self.master.after(0, lambda: self.upload_button.config(state=tk.NORMAL))
            self.master.after(0, lambda: self.process_button.config(state=tk.NORMAL))

    def update_progress(self, value):
        # Schedule progress bar update on the main thread
        self.master.after(0, lambda: self.progress_bar.config(value=value))

    def update_status(self, text):
        # Schedule status label update on the main thread
        self.master.after(0, lambda: self.status_label.config(text=text))

    def show_error(self, title, message):
        # Show error message on the main thread
        self.master.after(0, lambda: messagebox.showerror(title, message))

    def sanitize_filename(self, s):
        # Allow only alphanumeric characters, spaces, hyphens, and underscores.
        return "".join(c for c in s if c.isalnum() or c in (" ", "-", "_")).rstrip()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
