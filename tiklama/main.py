import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import pandas as pd
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests

# Global variables for files, data, and reports
uploaded_links_file = ""
links = []
uploaded_proxies_file = ""
proxies = []
logs = []
report_data = []

def center_window(win):
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

def upload_links_file():
    global uploaded_links_file, links
    file_path = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xlsx"), ("Excel files", "*.xls"), ("CSV files", "*.csv")]
    )
    if file_path:
        uploaded_links_file = file_path
        links_label.config(text=f"Links File: {uploaded_links_file}")
        try:
            # Use header=None so that the first row is not skipped even if there is no header.
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path, header=None)
            else:
                df = pd.read_excel(file_path, header=None)
            # Extract links from the first column
            links = df.iloc[:, 0].dropna().tolist()
            messagebox.showinfo("File Uploaded", f"Links file uploaded with {len(links)} links found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process links file: {e}")

def upload_proxies_file():
    global uploaded_proxies_file, proxies
    file_path = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xlsx"), ("Excel files", "*.xls"), ("CSV files", "*.csv")]
    )
    if file_path:
        uploaded_proxies_file = file_path
        proxies_label.config(text=f"Proxies File: {uploaded_proxies_file}")
        try:
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path, header=None)
            else:
                df = pd.read_excel(file_path, header=None)
            proxies = df.iloc[:, 0].dropna().tolist()
            messagebox.showinfo("File Uploaded", f"Proxies file uploaded with {len(proxies)} proxies found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process proxies file: {e}")

def extract_ip(proxy):
    try:
        if proxy.startswith("http://"):
            ip_port = proxy[7:]
        elif proxy.startswith("https://"):
            ip_port = proxy[8:]
        else:
            ip_port = proxy
        ip = ip_port.split(":")[0]
        return ip
    except Exception:
        return "Unknown"

def get_country(ip):
    try:
        # Free API to fetch country info for an IP
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = response.json()
        if data.get("status") == "success":
            return data.get("country", "Unknown")
        else:
            return "Unknown"
    except Exception:
        return "Unknown"

def process_link(link, proxy, min_time, max_time, headless):
    chrome_options = Options()
    chrome_options.add_argument(f'--proxy-server={proxy}')
    if headless:
        chrome_options.add_argument('--headless')
    # Create the webdriver instance (ensure chromedriver is in PATH)
    driver = webdriver.Chrome(options=chrome_options)
    start_time = time.time()
    try:
        driver.get(link)
        time.sleep(3)  # Wait for page load
        
        # Determine a random duration (in seconds) to simulate user scrolling
        random_duration = random.randint(min_time, max_time)
        end_time = time.time() + random_duration
        # Simulate user scrolling in small increments until the random duration elapses
        while time.time() < end_time:
            driver.execute_script("window.scrollBy(0, 200);")
            time.sleep(1)
            
        total_time = time.time() - start_time
        ip = extract_ip(proxy)
        country = get_country(ip)
        log_message = f"Link '{link}' processed by IP {proxy} ({country}) in {total_time:.2f} sec."
        return total_time, country, log_message
    except Exception as e:
        ip = extract_ip(proxy)
        country = get_country(ip)
        error_message = f"Error processing '{link}' using proxy {proxy} ({country}): this IP doesn't work. ({e})"
        print(error_message)
        return None, country, error_message
    finally:
        driver.quit()

def process_file():
    global logs, report_data
    if not links:
        messagebox.showwarning("Warning", "Please upload a links file first.")
        return
    if not proxies:
        messagebox.showwarning("Warning", "Please upload a proxies file first.")
        return
    
    try:
        min_time = int(min_time_entry.get())
        max_time = int(max_time_entry.get())
        if min_time > max_time:
            messagebox.showerror("Error", "Minimum time cannot be greater than maximum time.")
            return
    except Exception:
        messagebox.showerror("Error", "Please enter valid integer times (in seconds).")
        return

    headless = headless_var.get()
    logs.clear()
    report_data.clear()

    total_tasks = len(links) * len(proxies)
    current_task = 0
    progress_bar['maximum'] = total_tasks
    progress_bar['value'] = 0

    for link in links:
        logs.append(f"Processing link: {link}")
        for proxy in proxies:
            logs.append(f"Trying proxy: {proxy} for link: {link}")
            total_time, country, message = process_link(link, proxy, min_time, max_time, headless)
            logs.append(message)
            report_data.append({
                "Link": link,
                "IP": proxy,
                "Country": country,
                "Time Spent (s)": total_time if total_time is not None else "Failed"
            })
            current_task += 1
            progress_bar['value'] = current_task
            progress_label.config(text=f"Progress: {current_task}/{total_tasks}")
            root.update_idletasks()  # Update GUI

    show_report_window()

def show_report_window():
    report_win = tk.Toplevel(root)
    report_win.title("Processing Report")
    report_win.geometry("800x400")
    
    # Create a scrolled text widget to display the report as a table
    st = scrolledtext.ScrolledText(report_win, wrap=tk.NONE, font=("Courier", 10))
    st.pack(expand=True, fill='both')
    
    # Prepare header and separator row
    header = f"{'Link':60} | {'IP':20} | {'Country':20} | {'Time Spent (s)':15}\n"
    separator = "-" * 130 + "\n"
    st.insert(tk.END, header)
    st.insert(tk.END, separator)
    # Insert report data rows
    for row in report_data:
        link = row["Link"][:57] + "..." if len(row["Link"]) > 60 else row["Link"]
        ip = row["IP"]
        country = row["Country"]
        time_spent = row["Time Spent (s)"]
        line = f"{link:60} | {ip:20} | {country:20} | {str(time_spent):15}\n"
        st.insert(tk.END, line)
    
    # Button to download the report as an Excel file
    download_btn = tk.Button(report_win, text="Download Report", command=save_report)
    download_btn.pack(pady=10)

def save_report():
    if not report_data:
        messagebox.showwarning("Warning", "No report data to save.")
        return
    df = pd.DataFrame(report_data)
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                             filetypes=[("Excel files", "*.xlsx")])
    if file_path:
        try:
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Report Saved", f"Report successfully saved at {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save report: {e}")

# --------------------------
# Set up the main Tkinter window
root = tk.Tk()
root.title("Link Processor")
root.geometry("600x550")
center_window(root)

# Upload buttons for links and proxies
upload_links_button = tk.Button(root, text="Upload Links File", command=upload_links_file)
upload_links_button.pack(pady=5)
links_label = tk.Label(root, text="No links file uploaded.")
links_label.pack(pady=5)

upload_proxies_button = tk.Button(root, text="Upload Proxies File", command=upload_proxies_file)
upload_proxies_button.pack(pady=5)
proxies_label = tk.Label(root, text="No proxies file uploaded.")
proxies_label.pack(pady=5)

# Time range inputs
time_frame = tk.Frame(root)
time_frame.pack(pady=10)
min_time_label = tk.Label(time_frame, text="Min Time (sec):")
min_time_label.grid(row=0, column=0, padx=5)
min_time_entry = tk.Entry(time_frame, width=5)
min_time_entry.grid(row=0, column=1, padx=5)
min_time_entry.insert(0, "5")
max_time_label = tk.Label(time_frame, text="Max Time (sec):")
max_time_label.grid(row=0, column=2, padx=5)
max_time_entry = tk.Entry(time_frame, width=5)
max_time_entry.grid(row=0, column=3, padx=5)
max_time_entry.insert(0, "10")

# Checkbox for headless mode
headless_var = tk.BooleanVar()
headless_checkbox = tk.Checkbutton(root, text="Headless Mode", variable=headless_var)
headless_checkbox.pack(pady=5)

# Progress bar and label
progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=10)
progress_label = tk.Label(root, text="Progress: 0/0")
progress_label.pack(pady=5)

# Process file button
process_button = tk.Button(root, text="Process File", command=process_file)
process_button.pack(pady=10)

root.mainloop()
