import os
import sys
import threading
import time
import re
import requests
import json
from datetime import date, timedelta, datetime
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk

# Selenium-related imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Global language variable (default is English)
current_language = "eng"

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
        # options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# ---------------------------
# Price extraction functions for Etstur, Trivago, Tatilbudur
# ---------------------------
def get_price_etstur(driver, url):
    driver.get(url)
    time.sleep(5)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    price_element = soup.find("p", class_="amount")
    return price_element.get_text(strip=True) if price_element else ""

def get_price_trivago(driver, url):
    driver.get(url)
    time.sleep(10)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
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
                pass
                print(f"Attempt {attempt} for {url} did not find a valid price.\n")
        except Exception as e:
            pass
            print(f"Attempt {attempt} for {url} raised an error: {e}\n")
        finally:
            driver.quit()
            time.sleep(2)
    return None

# ---------------------------
# Updated Otelz extraction with custom parameters (city and number of people)
# ---------------------------
def get_price_otelz_custom(otelz_link, city, desired_people):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    
    driver.get(otelz_link)
    
    # Handle cookie popup if present
    try:
        cookie_popup = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.sc-416269e7-0.gnoTWc.cookiePopup")
        ))
        cookie_button = cookie_popup.find_element(By.TAG_NAME, "button")
        cookie_button.click()
    except Exception as e:
        pass
        # print("Otelz: Cookie popup not found or already closed.")
    
    # Type the provided city into the search input
    search_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.search-input")))
    search_input.clear()
    search_input.send_keys(city)
    time.sleep(5)  # wait for suggestions to load
    
    try:
        suggestion_item = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.name")))
        suggestion_item.click()
    except Exception as e:
        pass
        # print(f"Otelz: Could not click suggestion item for city '{city}'.")
    time.sleep(5)
    
    # Click the rooms container
    rooms_container = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "div.sc-16f24a25-0.itAImy.rooms")
    ))
    rooms_container.click()
    time.sleep(2)
    
    # Adjust the number of adults (default is 2)
    default_adults = 2
    diff = desired_people - default_adults
    if diff > 0:
        plus_btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "div.line.ADULT div.controls div.plus")
        ))
        for _ in range(diff):
            plus_btn.click()
            time.sleep(1)
    elif diff < 0:
        minus_btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "div.line.ADULT div.controls div.minus")
        ))
        for _ in range(abs(diff)):
            minus_btn.click()
            time.sleep(1)
    
    # Click the search button
    search_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.search-btn")))
    search_btn.click()
    time.sleep(5)
    
    # After redirection, click the button with data-testid "lowestPrice"
    lowest_price_btn = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, 'button[data-testid="lowestPrice"]')
    ))
    lowest_price_btn.click()
    time.sleep(5)
    
    final_url = driver.current_url
    price_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.price")))
    price_text = price_element.text.strip()
    
    driver.quit()
    return clean_price(price_text), final_url

def extract_price_otelz_custom_with_retry(otelz_link, city, desired_people, max_attempts=5):
    for attempt in range(1, max_attempts + 1):
        try:
            price, final_url = get_price_otelz_custom(otelz_link, city, desired_people)
            if price is not None:
                print(f"Otelz extraction succeeded on attempt {attempt}\n")
                return price, final_url
            else:
                pass
                print(f"Otelz extraction attempt {attempt} did not find a valid price.\n")
        except Exception as e:
            pass
            print(f"Otelz extraction attempt {attempt} raised an error: {e}\n")
        time.sleep(2)
    return None, None

# ---------------------------
# Functions to update provided extraction links with dynamic dates
# ---------------------------
def update_etstur_link(link, tomorrow_str, day_after_str):
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    parts = urlparse(link)
    qs = parse_qs(parts.query)
    if "check_in" in qs:
        qs["check_in"] = [tomorrow_str]
    if "check_out" in qs:
        qs["check_out"] = [day_after_str]
    new_query = urlencode(qs, doseq=True)
    new_url = urlunparse((parts.scheme, parts.netloc, parts.path, parts.params, new_query, parts.fragment))
    return new_url

def update_trivago_link(link, tomorrow_trivago, day_after_trivago):
    new_link = re.sub(r"dr-\d{8}-\d{8}-s", f"dr-{tomorrow_trivago}-{day_after_trivago}-s", link)
    return new_link

def update_tatilbudur_link(link, tomorrow_str, day_after_str):
    link = re.sub(r"checkInDate=\d{2}\.\d{2}\.\d{4}", f"checkInDate={tomorrow_str}", link)
    link = re.sub(r"checkOutDate=\d{2}\.\d{2}\.\d{4}", f"checkOutDate={day_after_str}", link)
    return link

# ---------------------------
# Build container HTML using dynamic data (with language support)
# ---------------------------
def build_container_html(logo_urls, site_data, best_price, last_update, lang="eng"):
    # Set the container texts based on the language.
    if lang == "tr":
        lowest_price_text = "en düşük fiyat"
        our_best_price_text = "En iyi fiyat:"
        last_updated_text = "Son güncelleme:"
    else:
        lowest_price_text = "lowest price"
        our_best_price_text = "Our best price:"
        last_updated_text = "Last updated:"
        
    container_html = f"""
<div class="hotel-price" style="font-size:16px; line-height:1.5; margin-top:20px; border:1px solid #ccc; padding:10px;">
  <div class="price-container" style="margin-bottom:10px;">
    <a href="{site_data['etstur']['link']}" target="_blank" style="text-decoration:none; color:#000;">
      <img src="{logo_urls.get('etstur', '')}" alt="Etstur Logo" style="width:50px; vertical-align:middle; margin-right:10px;" />
      <span>{lowest_price_text} {site_data['etstur']['price']} TL</span>
    </a>
  </div>
  <div class="price-container" style="margin-bottom:10px;">
    <a href="{site_data['trivago']['link']}" target="_blank" style="text-decoration:none; color:#000;">
      <img src="{logo_urls.get('trivago', '')}" alt="Trivago Logo" style="width:50px; vertical-align:middle; margin-right:10px;" />
      <span>{lowest_price_text} {site_data['trivago']['price']} TL</span>
    </a>
  </div>
  <div class="price-container" style="margin-bottom:10px;">
    <a href="{site_data['otelz']['link']}" target="_blank" style="text-decoration:none; color:#000;">
      <img src="{logo_urls.get('otelz', '')}" alt="Otelz Logo" style="width:50px; vertical-align:middle; margin-right:10px;" />
      <span>{lowest_price_text} {site_data['otelz']['price']} TL</span>
    </a>
  </div>
  <div class="price-container" style="margin-bottom:10px;">
    <a href="{site_data['tatilbudur']['link']}" target="_blank" style="text-decoration:none; color:#000;">
      <img src="{logo_urls.get('tatilbudur', '')}" alt="Tatilbudur Logo" style="width:50px; vertical-align:middle; margin-right:10px;" />
      <span>{lowest_price_text} {site_data['tatilbudur']['price']} TL</span>
    </a>
  </div>
  <div class="best-price" style="margin-top:15px;">
    <strong>{our_best_price_text} {best_price} TL</strong>
  </div>
  <div class="last-updated" style="margin-top:10px; font-size:14px; color:#666;">
    {last_updated_text} {last_update}
  </div>
</div>
"""
    return container_html

# ---------------------------
# WordPress media and page functions
# ---------------------------
def get_existing_media(file_name, username, password, base_url):
    media_endpoint = base_url + "wp-json/wp/v2/media"
    params = {"search": file_name}
    response = requests.get(media_endpoint, params=params, auth=(username, password))
    if response.status_code != 200:
        # print("Error checking existing media. Status code:", response.status_code)
        return None
    media_items = response.json()
    for item in media_items:
        source_url = item.get("source_url", "")
        if file_name.lower() in source_url.lower():
            # print(f"Found existing {file_name}. URL: {source_url}\n")
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
        # print(response.text)
        return None
    media_json = response.json()
    media_url = media_json.get("source_url")
    # print(f"Uploaded {file_name} successfully. URL: {media_url}\n")
    return media_url

def fetch_page(base_url, slug, username, password):
    pages_endpoint = base_url + "wp-json/wp/v2/pages"
    params = {"slug": slug}
    response = requests.get(pages_endpoint, params=params, auth=(username, password))
    if response.status_code != 200:
        print("Failed to fetch page. Status code:", response.status_code)
        # print(response.text)
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
        # print(response.text)
        return False
    # print("Page updated successfully!\n")
    return True

# ---------------------------
# Main update function (integrated with new env settings and language support)
# ---------------------------
def update_wordpress():
    # Log the start time of the update.
    print("Update started at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\n")
    
    # Read settings from env.txt (row-by-row)
    # Expected env.txt lines:
    # 0: Base URL
    # 1: Page URL
    # 2: Username
    # 3: Password
    # 4: Etstur extraction link
    # 5: Trivago extraction link
    # 6: Tatilbudur extraction link
    # 7: Otelz base link
    # 8: Otelz city (e.g., alanya)
    # 9: Number of people staying (e.g., 4)
    try:
        with open("env.txt", "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        if len(lines) < 10:
            print("env.txt does not contain enough values.")
            return
        base_url = lines[0]
        page_url = lines[1]
        wp_username = lines[2]
        wp_password = lines[3]
        etstur_link_orig = lines[4]
        trivago_link_orig = lines[5]
        tatilbudur_link_orig = lines[6]
        otelz_link = lines[7]
        otelz_city = lines[8]
        otelz_people = int(lines[9])
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

    # Update the provided extraction links with current dates.
    updated_etstur_link = update_etstur_link(etstur_link_orig, tomorrow_str, day_after_str)
    updated_trivago_link = update_trivago_link(trivago_link_orig, tomorrow_trivago, day_after_trivago)
    updated_tatilbudur_link = update_tatilbudur_link(tatilbudur_link_orig, tomorrow_str, day_after_str)

    # Extract prices from the updated links.
    price_etstur = extract_price_with_retry(get_price_etstur, updated_etstur_link)
    price_trivago = extract_price_with_retry(get_price_trivago, updated_trivago_link)
    price_tatil = extract_price_with_retry(get_price_tatil, updated_tatilbudur_link)
    price_otelz, otelz_final_url = extract_price_otelz_custom_with_retry(otelz_link, otelz_city, otelz_people)

    # print("\nExtracted Prices and Links:")
    # print("Etstur Price:", price_etstur)
    # print("Trivago Price:", price_trivago)
    # print("Tatilbudur Price:", price_tatil)
    # print("Otelz Price:", price_otelz)
    # print("Otelz Final URL:", otelz_final_url)

    all_prices = [p for p in (price_etstur, price_trivago, price_tatil, price_otelz) if p is not None]
    if all_prices:
        smallest = min(all_prices)
        best_price = smallest - 1
    else:
        print("Could not determine final price due to missing data.")
        return

    site_data = {
        "etstur": {"price": price_etstur if price_etstur is not None else 0, "link": updated_etstur_link},
        "trivago": {"price": price_trivago if price_trivago is not None else 0, "link": updated_trivago_link},
        "otelz": {"price": price_otelz if price_otelz is not None else 0, "link": otelz_final_url if otelz_final_url else otelz_link},
        "tatilbudur": {"price": price_tatil if price_tatil is not None else 0, "link": updated_tatilbudur_link}
    }

    # Get the last update time to show in the HTML container.
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # --- WordPress update part ---
    # print("Fetching page with slug '{}'...".format(slug))
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
        # print("Existing container found. Using existing logo URLs.")
        imgs = container_div.find_all("img")
        if len(imgs) >= 4:
            logo_urls["etstur"] = imgs[0].get("src", "")
            logo_urls["trivago"] = imgs[1].get("src", "")
            logo_urls["otelz"] = imgs[2].get("src", "")
            logo_urls["tatilbudur"] = imgs[3].get("src", "")
        else:
            # print("Not enough images found; uploading logos instead.")
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

    # Use the global current_language to choose container texts.
    new_container_html = build_container_html(logo_urls, site_data, best_price, last_update, lang=current_language)

    if container_div:
        # print("Updating existing container.")
        container_div.clear()
        new_fragment = BeautifulSoup(new_container_html, "html.parser")
        container_div.append(new_fragment)
    else:
        # print("Appending new container to page content.")
        new_fragment = BeautifulSoup(new_container_html, "html.parser")
        if soup_new.body:
            soup_new.body.append(new_fragment)
        else:
            soup_new.append(new_fragment)

    updated_content = str(soup_new)

    # print("Updating page content...")
    success = update_page_content(base_url, page_id, updated_content, wp_username, wp_password)
    if success:
        print("Page updated successfully.")
    else:
        print("Page update failed.")

    print("Update finished at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\n")

# ---------------------------
# Tkinter GUI with Auto Update Timer
# ---------------------------
def main_gui():
    global current_language
    root = tk.Tk()
    root.title("Price Updater Plugin")
    
    # Center window
    window_width = 800
    window_height = 700
    center_window(root, window_width, window_height)
    
    # Language selection
    lang_var = tk.StringVar(value="eng")
    
    def update_language():
        global current_language
        lang = lang_var.get()
        current_language = lang  # update global language used for container texts
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
    
    # Pre-fill entries from env.txt (only first four lines are used here)
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
    
    # Global auto-update job holder
    global auto_update_job
    auto_update_job = None

    def on_run():
        env_file = "env.txt"
        new_values = [
            domain_entry.get().strip() + "\n",
            page_url_entry.get().strip() + "\n",
            username_entry.get().strip() + "\n",
            password_entry.get().strip() + "\n"
        ]
        # Read the entire file if it exists.
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                lines = f.readlines()
        else:
            lines = []
        while len(lines) < 4:
            lines.append("\n")
        lines[:4] = new_values
        with open(env_file, "w") as f:
            f.writelines(lines)
        threading.Thread(target=update_wordpress, daemon=True).start()
    
    run_button = tk.Button(root, text=LANG_TEXT["eng"]["run_update"], command=on_run)
    run_button.grid(row=6, column=0, columnspan=2, pady=5)
    
    def start_auto(interval_minutes, log_widget, root):
        global auto_update_job
        def update_and_schedule():
            global auto_update_job
            update_wordpress()
            auto_update_job = root.after(interval_minutes * 60 * 1000, update_and_schedule)
        update_and_schedule()
    
    def stop_auto():
        global auto_update_job
        print("Stopping auto-update.\n")
        if auto_update_job:
            root.after_cancel(auto_update_job)
            auto_update_job = None
            print("Auto-update stopped.\n")
    
    def start_auto_thread():
        try:
            interval = int(interval_entry.get().strip())
        except ValueError:
            print("Invalid interval. Please enter a number (minutes).")
            return
        threading.Thread(target=start_auto, args=(interval, log_text, root), daemon=True).start()
    
    start_auto_button = tk.Button(root, text=LANG_TEXT["eng"]["start_auto"], command=start_auto_thread)
    start_auto_button.grid(row=8, column=0, pady=5)
    
    stop_auto_button = tk.Button(root, text=LANG_TEXT["eng"]["stop_auto"], command=stop_auto)
    stop_auto_button.grid(row=8, column=1, pady=5)
    
    update_language()  # Initialize texts for selected language
    root.mainloop()

if __name__ == "__main__":
    main_gui()
