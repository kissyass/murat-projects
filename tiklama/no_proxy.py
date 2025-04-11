import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import pandas as pd
import random
import time
import math
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def center_window(win):
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

# Global variables for file paths, links, and report data.
uploaded_links_file = ""
links = []
report_data = []
next_link_index = 0  # pointer into links list

def upload_links_file():
    global uploaded_links_file, links, next_link_index
    file_path = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xlsx"), ("Excel files", "*.xls"), ("CSV files", "*.csv")]
    )
    if file_path:
        uploaded_links_file = file_path
        links_file_label.config(text=f"Links File: {uploaded_links_file}")
        try:
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path, header=None)
            else:
                df = pd.read_excel(file_path, header=None)
            links = df.iloc[:, 0].dropna().tolist()
            next_link_index = 0
            messagebox.showinfo("File Uploaded", f"Uploaded with {len(links)} links found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load links file: {e}")

def open_tab(driver, link, overall_range):
    """
    Opens a new tab and attempts to load the link.
    Waits for the element with id 'listeo_logo' to appear.
    Returns a dict with timing data if successful, or with "failed": True.
    overall_range: (min_overall, max_overall) in seconds.
    """
    overall_time = random.randint(int(overall_range[0]), int(overall_range[1]))
    phase1 = random.randint(60, 120)
    phase2 = random.randint(60, 120)
    if overall_time < (phase1 + phase2 + 60):
        overall_time = phase1 + phase2 + 60
    phase3 = overall_time - (phase1 + phase2)
    start = time.time()

    driver.execute_script("window.open();")
    handle = driver.window_handles[-1]
    driver.switch_to.window(handle)
    driver.set_page_load_timeout(30)
    try:
        driver.get(link)
    except (TimeoutException, WebDriverException) as e:
        return {"failed": True, "link": link, "error": str(e)}
    
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "listeo_logo")))
    except TimeoutException:
        return {"failed": True, "link": link, "error": "Logo element not loaded (timeout)."}
    
    time.sleep(3)  # Additional wait for stability
    current_url = driver.current_url.lower()
    if "gstatic.com/generate_204" in current_url or "connect" in current_url:
        return {"failed": True, "link": link, "error": "Captive portal or connectivity check encountered."}
    try:
        page_height = driver.execute_script("return document.body.scrollHeight;")
    except Exception:
        page_height = 1000
    page_middle = page_height / 2

    return {
        "failed": False,
        "link": link,
        "handle": handle,
        "start": start,
        "phase1_duration": phase1,
        "phase2_duration": phase2,
        "phase3_duration": phase3,
        "phase1_end": start + phase1,
        "phase2_end": start + phase1 + phase2,
        "overall_end": start + overall_time,
        "page_middle": page_middle,
        "launched_next": False,
        "middle_set": False,
        "overall_duration": overall_time
    }

def perform_phase1(tab, driver):
    driver.execute_script("window.scrollBy(0, arguments[0]);", random.choice([200, -200]))

def perform_phase2(tab, driver):
    elapsed = time.time() - tab["phase1_end"]
    fraction = elapsed / tab["phase2_duration"]
    fraction = min(fraction, 1)
    try:
        page_height = driver.execute_script("return document.body.scrollHeight;")
    except Exception:
        page_height = tab["page_middle"] * 2
    new_position = fraction * page_height
    driver.execute_script("window.scrollTo(0, arguments[0]);", new_position)

def process_links():
    global report_data, next_link_index
    if not links:
        messagebox.showwarning("Warning", "Please upload a file with links first.")
        return
    try:
        min_overall = float(min_overall_entry.get()) * 60
        max_overall = float(max_overall_entry.get()) * 60
        if min_overall > max_overall:
            messagebox.showerror("Error", "Minimum overall time cannot be greater than maximum overall time.")
            return
    except Exception:
        messagebox.showerror("Error", "Please enter valid overall time values (in minutes).")
        return

    overall_range = (min_overall, max_overall)
    headless = headless_var.get()

    total_tasks = len(links)
    progress_bar['maximum'] = total_tasks
    progress_count = 0
    report_data.clear()
    next_link_index = 0

    # Open a single Chrome session.
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("about:blank")
    base_handle = driver.current_window_handle

    # List to manage open tabs concurrently.
    open_tabs = []
    # Open the first link.
    if next_link_index < len(links):
        tab_data = open_tab(driver, links[next_link_index], overall_range)
        next_link_index += 1
        if tab_data.get("failed", False):
            report_data.append({
                "Link": links[next_link_index-1],
                "Status": "Failed to open the page"
            })
            progress_count += 1
            progress_bar['value'] = progress_count
        else:
            open_tabs.append(tab_data)

    # Main loop: Process open tabs concurrently.
    while open_tabs or next_link_index < len(links):
        now = time.time()
        for tab in open_tabs[:]:
            try:
                driver.switch_to.window(tab["handle"])
            except Exception:
                open_tabs.remove(tab)
                continue

            if now < tab["phase1_end"]:
                perform_phase1(tab, driver)
            elif now < tab["phase2_end"]:
                perform_phase2(tab, driver)
                # As soon as a tab finishes Phase 2, if there is another link, open it.
                if (not tab.get("launched_next", False)) and (next_link_index < len(links)):
                    new_tab = open_tab(driver, links[next_link_index], overall_range)
                    next_link_index += 1
                    if new_tab.get("failed", False):
                        report_data.append({
                            "Link": links[next_link_index-1],
                            "Status": "Failed to open the page"
                        })
                        progress_count += 1
                        progress_bar['value'] = progress_count
                    else:
                        open_tabs.append(new_tab)
                        tab["launched_next"] = True
            elif now < tab["overall_end"]:
                if not tab["middle_set"]:
                    driver.execute_script("window.scrollTo(0, arguments[0]);", tab["page_middle"])
                    tab["middle_set"] = True
            else:
                try:
                    driver.close()
                except Exception:
                    pass
                report_data.append({
                    "Link": tab["link"],
                    "Status": "Opened successfully"
                })
                open_tabs.remove(tab)
                driver.switch_to.window(base_handle)
                progress_count += 1
                progress_bar['value'] = progress_count
        time.sleep(0.5)
        if not open_tabs and next_link_index < len(links):
            new_tab = open_tab(driver, links[next_link_index], overall_range)
            next_link_index += 1
            if new_tab.get("failed", False):
                report_data.append({
                    "Link": links[next_link_index-1],
                    "Status": "Failed to open the page"
                })
                progress_count += 1
                progress_bar['value'] = progress_count
            else:
                open_tabs.append(new_tab)
    driver.quit()
    progress_bar['value'] = total_tasks
    show_report_window()

def download_report():
    # Convert report_data to DataFrame and save as Excel.
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files","*.xlsx"), ("All Files","*.*")])
    if file_path:
        try:
            df = pd.DataFrame(report_data)
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Success", f"Report saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save report: {e}")

def show_report_window():
    report_win = tk.Toplevel(root)
    report_win.title("Processing Report")
    report_win.geometry("900x600")
    
    st = scrolledtext.ScrolledText(report_win, wrap=tk.NONE, font=("Courier", 10))
    st.pack(expand=True, fill='both')
    
    header = (f"{'Link':60} | {'Status':30}\n")
    separator = "-" * 100 + "\n"
    st.insert(tk.END, header)
    st.insert(tk.END, separator)
    for row in report_data:
        line = f"{row['Link'][:60]:60} | {row['Status'][:30]:30}\n"
        st.insert(tk.END, line)
    
    # Add a Download Report button to export the report to Excel.
    download_btn = tk.Button(report_win, text="Download Report as Excel", command=download_report)
    download_btn.pack(pady=10)

def clear_data():
    global uploaded_links_file, links, report_data, next_link_index
    uploaded_links_file = ""
    links = []
    report_data = []
    next_link_index = 0
    links_file_label.config(text="No links file uploaded.")
    progress_bar['value'] = 0

# -------------------------
# Set up the main Tkinter window.
root = tk.Tk()
root.title("Link Engagement Simulator (No Proxies)")
root.geometry("500x650")
def center_and_set(win):
    center_window(win)
center_and_set(root)

upload_links_button = tk.Button(root, text="Upload Links File", command=upload_links_file)
upload_links_button.pack(pady=10)
links_file_label = tk.Label(root, text="No links file uploaded.")
links_file_label.pack()

headless_var = tk.BooleanVar()
headless_checkbox = tk.Checkbutton(root, text="Headless Mode", variable=headless_var)
headless_checkbox.pack(pady=10)

min_overall_label = tk.Label(root, text="Min Overall Time (min):")
min_overall_label.pack()
min_overall_entry = tk.Entry(root, width=5)
min_overall_entry.insert(0, "5")
min_overall_entry.pack()

max_overall_label = tk.Label(root, text="Max Overall Time (min):")
max_overall_label.pack()
max_overall_entry = tk.Entry(root, width=5)
max_overall_entry.insert(0, "10")
max_overall_entry.pack()

process_button = tk.Button(root, text="Process Links", command=process_links)
process_button.pack(pady=10)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progress_bar.pack(pady=10)

clear_button = tk.Button(root, text="Clear Data", command=clear_data)
clear_button.pack(pady=10)

root.mainloop()
