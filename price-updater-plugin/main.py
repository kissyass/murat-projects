import os
import sys
import threading
import time
import re
import requests
import json
from datetime import date, timedelta
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk
from datetime import datetime

# Selenium-related imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# ---------------------------
# Language dictionaries
# ---------------------------
LANG_TEXT = {
    "eng": {
        "title": "Price Updater Plugin",
        "domain": "Domain (e.g., https://example.com/)",
        "page_url": "Page URL (e.g., https://example.com/test-page/)",
        "username": "Username",
        "password": "Password",
        "interval": "Interval (minutes)",
        "run_update": "Run Update",
        "start_auto": "Start Auto Update",
        "stop_auto": "Stop Auto Update"
    },
    "tr": {
        "title": "Fiyat Güncelleme Eklentisi",
        "domain": "Alan Adı (örn. https://example.com/)",
        "page_url": "Sayfa URL'si (örn. https://example.com/test-page/)",
        "username": "Kullanıcı Adı",
        "password": "Parola",
        "interval": "Aralık (dakika)",
        "run_update": "Güncellemeyi Başlat",
        "start_auto": "Otomatik Güncellemeyi Başlat",
        "stop_auto": "Otomatik Güncellemeyi Durdur"
    }
}

# ---------------------------
# Utility: Center the window
# ---------------------------
def center_window(win, width, height):
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = int((screen_width - width) / 2)
    y = int((screen_height - height) / 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

# ---------------------------
# Redirect stdout to our log widget
# ---------------------------
class TextRedirector(object):
    def __init__(self, widget):
        self.widget = widget
    def write(self, s):
        self.widget.insert(tk.END, s)
        self.widget.see(tk.END)
    def flush(self):
        pass

# ---------------------------
# Selenium driver initialization using webdriver_manager
# ---------------------------
def get_chrome_driver(headless=True):
    options = Options()
    if headless:
        options.headless = True
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# ---------------------------
# Extraction functions for Etstur, Trivago, Tatilbudur, Otelz
# ---------------------------
def get_price_etstur(driver, url):
    driver.get(url)
    time.sleep(5)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    # For example, we search for <p class="amount">
    price_element = soup.find("p", class_="amount")
    return price_element.get_text(strip=True) if price_element else ""

def get_price_trivago(driver, url):
    driver.get(url)
    time.sleep(10)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    # Look for element with data-testid="recommended-price"
    price_element = soup.find(attrs={"data-testid": "recommended-price"})
    return price_element.get_text(strip=True) if price_element else ""

def get_price_tatil(driver, url):
    driver.get(url)
    time.sleep(10)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    price_element = soup.find("div", class_="c-card__current-price")
    return price_element.get_text(strip=True) if price_element else ""

def clean_price(price_str):
    digits = re.sub(r'\D', '', price_str)
    return int(digits) if digits else None

def extract_price_with_retry(extraction_function, url, max_attempts=5):
    for attempt in range(1, max_attempts + 1):
        driver = get_chrome_driver(headless=True)
        try:
            raw_price = extraction_function(driver, url)
            price = clean_price(raw_price)
            if price is not None:
                print(f"Success on attempt {attempt} for {url}\n")
                return price
            else:
                print(f"Attempt {attempt} for {url} did not find a valid price.\n")
        except Exception as e:
            print(f"Attempt {attempt} for {url} raised an error: {e}\n")
        finally:
            driver.quit()
            time.sleep(2)
    return None

def get_price_otelz():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    
    # Navigate to Otelz homepage
    driver.get("https://www.otelz.com/")
    
    # Handle cookie popup
    try:
        cookie_popup = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.sc-416269e7-0.gnoTWc.cookiePopup")
        ))
        cookie_button = cookie_popup.find_element(By.TAG_NAME, "button")
        cookie_button.click()
    except Exception as e:
        print("Otelz: Cookie popup not found or already closed:")
    
    # Type "alanya" in the search input
    search_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.search-input")))
    search_input.clear()
    search_input.send_keys("alanya")
    
    # Wait a few seconds for the suggestions to load, then try to click li with id "loc-0"
    time.sleep(5)
    try:
        suggestion_item = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "div.name")
        ))
        suggestion_item.click()
    except Exception as e:
        print("Otelz: Could not click div class name:")
    
    time.sleep(5)  # wait a moment after clicking suggestion
    
    # Click the rooms container
    rooms_container = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "div.sc-16f24a25-0.itAImy.rooms")
    ))
    rooms_container.click()
    
    # In the ADULT section, click the plus button twice.
    plus_btn = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "div.line.ADULT div.controls div.plus")
    ))
    plus_btn.click()
    time.sleep(1)
    plus_btn.click()
    
    # Click the search button
    search_btn = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "button.search-btn")
    ))
    search_btn.click()
    
    # After redirection, click the button with data-testid "lowestPrice"
    lowest_price_btn = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, 'button[data-testid="lowestPrice"]')
    ))
    lowest_price_btn.click()
    time.sleep(5)  # wait for final redirection
    
    # Retrieve final URL
    final_url = driver.current_url
    
    # Extract the price from the first element with class "price"
    price_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.price")))
    price_text = price_element.text.strip()
    
    driver.quit()
    return clean_price(price_text), final_url

def extract_price_otelz_with_retry(max_attempts=5):
    for attempt in range(1, max_attempts + 1):
        try:
            price, final_url = get_price_otelz()
            if price is not None:
                print(f"Otelz extraction succeeded on attempt {attempt}\n")
                return price, final_url
            else:
                print(f"Otelz extraction attempt {attempt} did not find a valid price.\n")
        except Exception as e:
            print(f"Otelz extraction attempt {attempt} raised an error: {e}\n")
        time.sleep(2)
    return None, None

# ---------------------------
# WordPress media and page functions
# ---------------------------
def get_existing_media(file_name, username, password, base_url):
    media_endpoint = base_url + "wp-json/wp/v2/media"
    params = {"search": file_name}
    response = requests.get(media_endpoint, params=params, auth=(username, password))
    if response.status_code != 200:
        print("Error checking existing media. Status code:", response.status_code)
        return None
    media_items = response.json()
    for item in media_items:
        source_url = item.get("source_url", "")
        if file_name.lower() in source_url.lower():
            print(f"Found existing {file_name}. URL: {source_url}\n")
            return source_url
    return None

def upload_media(file_path, username, password, base_url):
    file_name = os.path.basename(file_path)
    existing_url = get_existing_media(file_name, username, password, base_url)
    if existing_url:
        return existing_url
    media_endpoint = base_url + "wp-json/wp/v2/media"
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.\n")
        return None
    headers = {
        "Content-Disposition": f"attachment; filename={file_name}",
        "Content-Type": "image/png"
    }
    with open(file_path, "rb") as f:
        file_data = f.read()
    response = requests.post(media_endpoint, headers=headers, data=file_data, auth=(username, password))
    if response.status_code not in [200, 201]:
        print(f"Failed to upload {file_name}. Status code: {response.status_code}\n")
        print(response.text)
        return None
    media_json = response.json()
    media_url = media_json.get("source_url")
    print(f"Uploaded {file_name} successfully. URL: {media_url}\n")
    return media_url

def fetch_page(base_url, slug, username, password):
    pages_endpoint = base_url + "wp-json/wp/v2/pages"
    params = {"slug": slug}
    response = requests.get(pages_endpoint, params=params, auth=(username, password))
    if response.status_code != 200:
        print("Failed to fetch page. Status code:", response.status_code)
        print(response.text)
        return None
    pages = response.json()
    if not pages:
        print(f"No page found with slug '{slug}'.\n")
        return None
    return pages[0]

def update_page_content(base_url, page_id, new_content, username, password):
    update_endpoint = base_url + f"wp-json/wp/v2/pages/{page_id}"
    payload = {"content": new_content}
    response = requests.post(update_endpoint, json=payload, auth=(username, password))
    if response.status_code not in [200, 201]:
        print("Failed to update page. Status code:", response.status_code)
        print(response.text)
        return False
    print("Page updated successfully!\n")
    return True

# ---------------------------
# Build container HTML using dynamic data
# ---------------------------
def build_container_html(logo_urls, site_data, best_price):
    container_html = f"""
<div class="hotel-price" style="font-size:16px; line-height:1.5; margin-top:20px; border:1px solid #ccc; padding:10px;">
  <div class="price-container" style="margin-bottom:10px;">
    <a href="{site_data['etstur']['link']}" target="_blank" style="text-decoration:none; color:#000;">
      <img src="{logo_urls.get('etstur', '')}" alt="Etstur Logo" style="width:50px; vertical-align:middle; margin-right:10px;" />
      <span>lowest price {site_data['etstur']['price']} TL</span>
    </a>
  </div>
  <div class="price-container" style="margin-bottom:10px;">
    <a href="{site_data['trivago']['link']}" target="_blank" style="text-decoration:none; color:#000;">
      <img src="{logo_urls.get('trivago', '')}" alt="Trivago Logo" style="width:50px; vertical-align:middle; margin-right:10px;" />
      <span>lowest price {site_data['trivago']['price']} TL</span>
    </a>
  </div>
  <div class="price-container" style="margin-bottom:10px;">
    <a href="{site_data['otelz']['link']}" target="_blank" style="text-decoration:none; color:#000;">
      <img src="{logo_urls.get('otelz', '')}" alt="Otelz Logo" style="width:50px; vertical-align:middle; margin-right:10px;" />
      <span>lowest price {site_data['otelz']['price']} TL</span>
    </a>
  </div>
  <div class="price-container" style="margin-bottom:10px;">
    <a href="{site_data['tatilbudur']['link']}" target="_blank" style="text-decoration:none; color:#000;">
      <img src="{logo_urls.get('tatilbudur', '')}" alt="Tatilbudur Logo" style="width:50px; vertical-align:middle; margin-right:10px;" />
      <span>lowest price {site_data['tatilbudur']['price']} TL</span>
    </a>
  </div>
  <div class="best-price" style="margin-top:15px;">
    <strong>Our best price: {best_price} TL</strong>
  </div>
</div>
"""
    return container_html

# ---------------------------
# Main update function
# ---------------------------
def update_wordpress():
    # Log the start time of the update.
    print("Update started at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\n")
    
    # Read settings from env.txt (row-by-row)
    try:
        with open("env.txt", "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        if len(lines) < 4:
            print("env.txt does not contain enough values (domain, page URL, username, password).")
            return
        base_url = lines[0]
        page_url = lines[1]
        wp_username = lines[2]
        wp_password = lines[3]
    except Exception as e:
        print("Error reading env.txt:", e)
        return

    if not base_url.endswith("/"):
        base_url += "/"
    slug = page_url[len(base_url):].strip("/")

    # Set up dates and build dynamic extraction URLs
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    tomorrow_str = tomorrow.strftime("%d.%m.%Y")
    day_after_str = day_after.strftime("%d.%m.%Y")
    tomorrow_trivago = tomorrow.strftime("%Y%m%d")
    day_after_trivago = day_after.strftime("%Y%m%d")

    etstur_link = f"https://www.etstur.com/Alanya-Otelleri?check_in={tomorrow_str}&check_out={day_after_str}&adult_1=4&filters=&sortType=price&sortDirection=asc"
    trivago_link = f"https://www.trivago.com.tr/tr/lm/ucuz-alanya-t%C3%BCrkiye-otelleri?search=200-15242;dr-{tomorrow_trivago}-{day_after_trivago}-s;rc-1-4;so-1"
    tatilbudur_link = f"https://www.tatilbudur.com/yurtici-oteller/antalya/alanya-otelleri?checkInDate={tomorrow_str}&checkOutDate={day_after_str}&latStart=0&latEnd=0&lonStart=0&lonEnd=0&min=&max=&sort=price&sort-type=asc&searchType=hotel&hotelCategory=yurtici-oteller%2Fantalya%2Falanya-otelleri&key=Alanya&checkInDate={tomorrow_str}&checkOutDate={day_after_str}&adult=4&child=0&personCount=4+Yeti%C5%9Fkin+&type=region&id=&regionType=&item_list_id=search&item_list_name=Alanya+Otelleri&cd_item_list_location=search&price-range=false&searchType=hotel"

    price_etstur = extract_price_with_retry(get_price_etstur, etstur_link)
    price_trivago = extract_price_with_retry(get_price_trivago, trivago_link)
    price_tatil = extract_price_with_retry(get_price_tatil, tatilbudur_link)
    price_otelz, otelz_final_url = extract_price_otelz_with_retry(max_attempts=5)

    print("\nExtracted Prices:")
    print("Etstur Price:", price_etstur)
    print("Trivago Price:", price_trivago)
    print("Tatilbudur Price:", price_tatil)
    print("Otelz Price:", price_otelz)

    all_prices = [p for p in (price_etstur, price_trivago, price_tatil, price_otelz) if p is not None]
    if all_prices:
        smallest = min(all_prices)
        best_price = smallest - 1
    else:
        print("Could not determine final price due to missing data.")
        return

    site_data = {
        "etstur": {"price": price_etstur if price_etstur is not None else 0, "link": etstur_link},
        "trivago": {"price": price_trivago if price_trivago is not None else 0, "link": trivago_link},
        "otelz": {"price": price_otelz if price_otelz is not None else 0, "link": otelz_final_url if otelz_final_url else "https://www.otelz.com/"},
        "tatilbudur": {"price": price_tatil if price_tatil is not None else 0, "link": tatilbudur_link}
    }

    # --- WordPress update part ---
    print("Fetching page with slug '{}'...".format(slug))
    page = fetch_page(base_url, slug, wp_username, wp_password)
    if not page:
        return
    page_id = page.get("id")
    current_content = page["content"]["rendered"]

    soup_new = BeautifulSoup(current_content, "html.parser")
    container_div = soup_new.find("div", class_="hotel-price")

    logos = {
        "etstur": "etstur-logo.webp",
        "tatilbudur": "tatilbudur-logo.webp",
        "otelz": "otelz-logo.png",
        "trivago": "trivago-logo.png"
    }

    logo_urls = {}
    if container_div:
        print("Existing container found. Using existing logo URLs.")
        imgs = container_div.find_all("img")
        if len(imgs) >= 4:
            logo_urls["etstur"] = imgs[0].get("src", "")
            logo_urls["trivago"] = imgs[1].get("src", "")
            logo_urls["otelz"] = imgs[2].get("src", "")
            logo_urls["tatilbudur"] = imgs[3].get("src", "")
        else:
            print("Not enough images found; uploading logos instead.")
            for key, file_path in logos.items():
                url = upload_media(file_path, wp_username, wp_password, base_url)
                if url:
                    logo_urls[key] = url
                else:
                    print(f"Error uploading {key} logo. Exiting.")
                    return
    else:
        print("Container not found. Uploading logos.")
        for key, file_path in logos.items():
            url = upload_media(file_path, wp_username, wp_password, base_url)
            if url:
                logo_urls[key] = url
            else:
                print(f"Error uploading {key} logo. Exiting.")
                return

    new_container_html = build_container_html(logo_urls, site_data, best_price)

    if container_div:
        print("Updating existing container.")
        container_div.clear()
        new_fragment = BeautifulSoup(new_container_html, "html.parser")
        container_div.append(new_fragment)
    else:
        print("Appending new container to page content.")
        new_fragment = BeautifulSoup(new_container_html, "html.parser")
        if soup_new.body:
            soup_new.body.append(new_fragment)
        else:
            soup_new.append(new_fragment)

    updated_content = str(soup_new)

    print("Updating page content...")
    success = update_page_content(base_url, page_id, updated_content, wp_username, wp_password)
    if success:
        print("Page updated successfully.")
    else:
        print("Page update failed.")

    # Log the finish time of the update.
    print("Update finished at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\n")

# ---------------------------
# Tkinter GUI with Auto Update Timer
# ---------------------------
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import threading

# Text redirector for logs
class TextRedirector(object):
    def __init__(self, widget):
        self.widget = widget
    def write(self, s):
        self.widget.insert(tk.END, s)
        self.widget.see(tk.END)
    def flush(self):
        pass

auto_update_job = None  # Global job ID for auto-update

def start_auto_update(interval_minutes, log_widget, root):
    global auto_update_job
    def update_and_schedule():
        update_wordpress()
        # Schedule next update after interval_minutes * 60 * 1000 milliseconds
        global auto_update_job
        auto_update_job = root.after(interval_minutes * 60 * 1000, update_and_schedule)
    update_and_schedule()

def stop_auto_update(root):
    global auto_update_job
    if auto_update_job:
        root.after_cancel(auto_update_job)
        auto_update_job = None
        print("Auto-update stopped.\n")

def main_gui():
    root = tk.Tk()
    root.title("Price Updater Plugin")
    
    # Center window
    window_width = 800
    window_height = 700
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width - window_width) / 2)
    y = int((screen_height - window_height) / 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Language selection
    lang_var = tk.StringVar(value="eng")
    
    def update_language():
        lang = lang_var.get()
        texts = LANG_TEXT[lang]
        domain_label.config(text=texts["domain"])
        page_url_label.config(text=texts["page_url"])
        username_label.config(text=texts["username"])
        password_label.config(text=texts["password"])
        interval_label.config(text=texts["interval"])
        run_button.config(text=texts["run_update"])
        start_auto_button.config(text=texts["start_auto"])
        stop_auto_button.config(text=texts["stop_auto"])
        root.title(texts["title"])
    
    tk.Label(root, text="Language:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    lang_menu = tk.OptionMenu(root, lang_var, "eng", "tr", command=lambda x: update_language())
    lang_menu.grid(row=0, column=1, sticky="w", padx=5, pady=5)
    
    # Entry fields
    domain_label = tk.Label(root, text=LANG_TEXT["eng"]["domain"])
    domain_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
    domain_entry = tk.Entry(root, width=50)
    domain_entry.grid(row=1, column=1, padx=5, pady=5)
    
    page_url_label = tk.Label(root, text=LANG_TEXT["eng"]["page_url"])
    page_url_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)
    page_url_entry = tk.Entry(root, width=50)
    page_url_entry.grid(row=2, column=1, padx=5, pady=5)
    
    username_label = tk.Label(root, text=LANG_TEXT["eng"]["username"])
    username_label.grid(row=3, column=0, sticky="w", padx=5, pady=5)
    username_entry = tk.Entry(root, width=30)
    username_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)
    
    password_label = tk.Label(root, text=LANG_TEXT["eng"]["password"])
    password_label.grid(row=4, column=0, sticky="w", padx=5, pady=5)
    password_entry = tk.Entry(root, width=30, show="*")
    password_entry.grid(row=4, column=1, sticky="w", padx=5, pady=5)
    
    interval_label = tk.Label(root, text=LANG_TEXT["eng"]["interval"])
    interval_label.grid(row=5, column=0, sticky="w", padx=5, pady=5)
    interval_entry = tk.Entry(root, width=10)
    interval_entry.grid(row=5, column=1, sticky="w", padx=5, pady=5)
    interval_entry.insert(0, "30")  # default 30 minutes
    
    # Pre-fill entries from env.txt if exists
    if os.path.exists("env.txt"):
        with open("env.txt", "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        if len(lines) >= 4:
            domain_entry.insert(0, lines[0])
            page_url_entry.insert(0, lines[1])
            username_entry.insert(0, lines[2])
            password_entry.insert(0, lines[3])
    
    # ScrolledText for log output
    log_text = ScrolledText(root, width=100, height=25)
    log_text.grid(row=7, column=0, columnspan=2, padx=5, pady=5)
    sys.stdout = TextRedirector(log_text)
    
    # Buttons for manual and auto update
    def on_run():
        with open("env.txt", "w") as f:
            f.write(domain_entry.get().strip() + "\n")
            f.write(page_url_entry.get().strip() + "\n")
            f.write(username_entry.get().strip() + "\n")
            f.write(password_entry.get().strip() + "\n")
        threading.Thread(target=update_wordpress, daemon=True).start()
    
    run_button = tk.Button(root, text=LANG_TEXT["eng"]["run_update"], command=on_run)
    run_button.grid(row=6, column=0, columnspan=2, pady=5)
    
    def start_auto():
        try:
            interval = int(interval_entry.get().strip())
        except ValueError:
            print("Invalid interval. Please enter a number (minutes).")
            return
        threading.Thread(target=start_auto_update, args=(interval, log_text, root), daemon=True).start()
    
    def stop_auto():
        stop_auto_update(root)
    
    start_auto_button = tk.Button(root, text=LANG_TEXT["eng"]["start_auto"], command=start_auto)
    start_auto_button.grid(row=8, column=0, pady=5)
    
    stop_auto_button = tk.Button(root, text=LANG_TEXT["eng"]["stop_auto"], command=lambda: stop_auto_update(root))
    stop_auto_button.grid(row=8, column=1, pady=5)
    
    update_language()  # Initialize texts for selected language
    root.mainloop()

if __name__ == "__main__":
    main_gui()
