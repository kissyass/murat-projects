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
import requests

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
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = response.json()
        if data.get("status") == "success":
            return data.get("country", "Unknown")
        else:
            return "Unknown"
    except Exception:
        return "Unknown"

# Global variables for file paths, links, proxies, and report data.
uploaded_links_file = ""
links = []
uploaded_proxies_file = ""
proxies_list = []
report_data = []
next_link_index = 0  # pointer into links list

def center_window(win):
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

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

def format_proxy(proxy_line):
    # Expecting format: IP:port:username:password
    parts = proxy_line.split(":")
    if len(parts) >= 4:
        ip, port, username, password = parts[:4]
        return f"http://{username}:{password}@{ip}:{port}"
    else:
        return proxy_line

def upload_proxies_file():
    global uploaded_proxies_file, proxies_list
    file_path = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xlsx"), ("Excel files", "*.xls"), ("CSV files", "*.csv")]
    )
    if file_path:
        uploaded_proxies_file = file_path
        proxies_file_label.config(text=f"Proxies File: {uploaded_proxies_file}")
        try:
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path, header=None)
            else:
                df = pd.read_excel(file_path, header=None)
            proxies_list = [format_proxy(line.strip()) for line in df.iloc[:, 0].dropna().tolist()]
            print(proxies_list)
            messagebox.showinfo("File Uploaded", f"Uploaded with {len(proxies_list)} proxies found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load proxies file: {e}")

def open_tab(driver, link, overall_range, proxy):
    """
    Opens a new tab and attempts to load the link.
    Waits for the element with id 'listeo_logo' to appear.
    Returns a dict with timing data if successful, or with "failed": True.
    overall_range: (min_overall, max_overall) in seconds.
    """
    overall_time = random.randint(int(overall_range[0]), int(overall_range[1]))
    phase1 = random.randint(30, 60)
    phase2 = random.randint(30, 60)
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
    
    time.sleep(3)
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
    if not proxies_list:
        messagebox.showwarning("Warning", "Please upload a file with proxies first.")
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

    total_tasks = len(proxies_list) * len(links)
    progress_bar['maximum'] = total_tasks
    progress_count = 0
    report_data.clear()

    # For each proxy, open a new Chrome session and process all links concurrently.
    for proxy in proxies_list:
        print(proxy)
        chrome_options = Options()
        # chrome_options.add_argument("--proxy-bypass-list=*")
        chrome_options.add_argument("--proxy-auto-detect=false")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument(f'--proxy-server={proxy}')
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36")
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            country = get_country(extract_ip(proxy))
            for link in links:
                report_data.append({
                    "Link": link,
                    "Proxy": proxy,
                    "Country": country,
                    "Scrolling Up/Down (min)": "Failed to open the page",
                    "Scrolling Top-to-Bottom (min)": "Failed to open the page",
                    "Staying Still (min)": "Failed to open the page",
                    "Overall (min)": "Failed to open the page"
                })
                progress_count += 1
                progress_bar['value'] = progress_count
                root.update_idletasks()
            continue

        driver.get("about:blank")
        base_handle = driver.current_window_handle  # Save the base tab.
        country = get_country(extract_ip(proxy))
        open_tabs = []  # List of tabs currently processing.
        next_link_index = 0  # For this proxy, process all links.

        # Open first link.
        if next_link_index < len(links):
            tab_data = open_tab(driver, links[next_link_index], overall_range, proxy)
            next_link_index += 1
            if tab_data.get("failed", False):
                report_data.append({
                    "Link": links[next_link_index-1],
                    "Proxy": proxy,
                    "Country": country,
                    "Scrolling Up/Down (min)": "Failed to open the page",
                    "Scrolling Top-to-Bottom (min)": "Failed to open the page",
                    "Staying Still (min)": "Failed to open the page",
                    "Overall (min)": "Failed to open the page"
                })
                progress_count += 1
                progress_bar['value'] = progress_count
                root.update_idletasks()
            else:
                tab_data["proxy"] = proxy
                open_tabs.append(tab_data)

        # Now run a loop to concurrently update all open tabs.
        while open_tabs or next_link_index < len(links):
            now = time.time()
            # Process each open tab.
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
                        new_tab = open_tab(driver, links[next_link_index], overall_range, proxy)
                        next_link_index += 1
                        if new_tab.get("failed", False):
                            report_data.append({
                                "Link": links[next_link_index-1],
                                "Proxy": proxy,
                                "Country": country,
                                "Scrolling Up/Down (min)": "Failed to open the page",
                                "Scrolling Top-to-Bottom (min)": "Failed to open the page",
                                "Staying Still (min)": "Failed to open the page",
                                "Overall (min)": "Failed to open the page"
                            })
                            progress_count += 1
                            progress_bar['value'] = progress_count
                            root.update_idletasks()
                        else:
                            new_tab["proxy"] = proxy
                            open_tabs.append(new_tab)
                            tab["launched_next"] = True
                elif now < tab["overall_end"]:
                    if not tab["middle_set"]:
                        driver.execute_script("window.scrollTo(0, arguments[0]);", tab["page_middle"])
                        tab["middle_set"] = True
                    # Tab remains in Phase 3 concurrently.
                else:
                    # Overall time expired; close tab and record.
                    try:
                        driver.close()
                    except Exception:
                        pass
                    report_data.append({
                        "Link": tab["link"],
                        "Proxy": proxy,
                        "Country": country,
                        "Scrolling Up/Down (min)": round(tab["phase1_duration"] / 60, 2),
                        "Scrolling Top-to-Bottom (min)": round(tab["phase2_duration"] / 60, 2),
                        "Staying Still (min)": round(tab["phase3_duration"] / 60, 2),
                        "Overall (min)": round(tab["overall_duration"] / 60, 2)
                    })
                    open_tabs.remove(tab)
                    # Switch back to base tab.
                    driver.switch_to.window(base_handle)
                    progress_count += 1
                    progress_bar['value'] = progress_count
                    root.update_idletasks()
            time.sleep(0.5)
        driver.quit()
        time.sleep(5)
    progress_bar['value'] = total_tasks
    show_report_window()

def show_report_window():
    report_win = tk.Toplevel(root)
    report_win.title("Processing Report")
    report_win.geometry("900x400")
    st = scrolledtext.ScrolledText(report_win, wrap=tk.NONE, font=("Courier", 10))
    st.pack(expand=True, fill='both')
    header = (f"{'Link':60} | {'Proxy/IP':20} | {'Country':15} | "
              f"{'Scrolling Up/Down (min)':>25} | {'Scrolling Top-to-Bottom (min)':>30} | "
              f"{'Staying Still (min)':>20} | {'Overall (min)':>15}\n")
    separator = "-" * 160 + "\n"
    st.insert(tk.END, header)
    st.insert(tk.END, separator)
    for row in report_data:
        sc_ud = row["Scrolling Up/Down (min)"]
        sc_td = row["Scrolling Top-to-Bottom (min)"]
        still = row["Staying Still (min)"]
        overall = row["Overall (min)"]
        if isinstance(sc_ud, (float, int)):
            sc_ud = f"{sc_ud:.2f}"
        if isinstance(sc_td, (float, int)):
            sc_td = f"{sc_td:.2f}"
        if isinstance(still, (float, int)):
            still = f"{still:.2f}"
        if isinstance(overall, (float, int)):
            overall = f"{overall:.2f}"
        line = (f"{row['Link'][:60]:60} | {row['Proxy'][:20]:20} | {row['Country'][:15]:15} | "
                f"{sc_ud:25} | {sc_td:30} | {still:20} | {overall:15}\n")
        st.insert(tk.END, line)

def clear_data():
    global uploaded_links_file, links, uploaded_proxies_file, proxies_list, report_data, next_link_index
    uploaded_links_file = ""
    links = []
    uploaded_proxies_file = ""
    proxies_list = []
    report_data = []
    next_link_index = 0
    links_file_label.config(text="No links file uploaded.")
    proxies_file_label.config(text="No proxies file uploaded.")
    progress_bar['value'] = 0

# -------------------------
# Set up the main Tkinter window.
root = tk.Tk()
root.title("Link Engagement Simulator with Proxies")
root.geometry("500x650")
def center_and_set(win): 
    center_window(win)
center_and_set(root)

upload_links_button = tk.Button(root, text="Upload Links File", command=upload_links_file)
upload_links_button.pack(pady=10)
links_file_label = tk.Label(root, text="No links file uploaded.")
links_file_label.pack()

upload_proxies_button = tk.Button(root, text="Upload Proxies File", command=upload_proxies_file)
upload_proxies_button.pack(pady=10)
proxies_file_label = tk.Label(root, text="No proxies file uploaded.")
proxies_file_label.pack()

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
