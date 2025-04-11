import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import time
import random
import time
import threading

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

def simulate_user_interactions(driver,
                               total_time_range=(200, 250),
                               random_scroll_range=(60, 90),
                               slow_scroll_range=(60, 90)):
    """
    Simulate user interactions on the current page sequentially.
    - Total simulation time is between 4-5 minutes.
    - Random scrolling up and down for 1-2 minutes.
    - Slow scroll from top to bottom for 1-2 minutes.
    - Idle the remaining time.
    """
    total_time = random.uniform(*total_time_range)
    random_scroll_time = random.uniform(*random_scroll_range)
    slow_scroll_time = random.uniform(*slow_scroll_range)
    remaining_time = total_time - (random_scroll_time + slow_scroll_time)
    print(f"Simulating interactions: total {total_time:.0f}s, random scroll {random_scroll_time:.0f}s, "
          f"slow scroll {slow_scroll_time:.0f}s, idle {remaining_time:.0f}s.")

    # 1. Random scrolling for random_scroll_time seconds:
    end_random = time.time() + random_scroll_time
    while time.time() < end_random:
        page_height = driver.execute_script("return document.body.scrollHeight")
        random_position = random.randint(0, int(page_height))
        driver.execute_script("window.scrollTo(0, arguments[0]);", random_position)
        time.sleep(random.uniform(2, 5))

    # 2. Slow scroll from top to bottom for slow_scroll_time seconds:
    page_height = driver.execute_script("return document.body.scrollHeight")
    steps = 50
    step_time = slow_scroll_time / steps
    for i in range(steps):
        position = int(i * page_height / steps)
        driver.execute_script("window.scrollTo(0, arguments[0]);", position)
        time.sleep(step_time)

    # 3. Idle for remaining time (if any)
    if remaining_time > 0:
        time.sleep(remaining_time)
    print("User interaction simulation complete.")

class App:
    def __init__(self, master):
        self.master = master
        master.title("Excel Search Automation")
        # Set a fixed window size (adjust as needed)
        window_width, window_height = 600, 200
        self.center_window(window_width, window_height)

        # Initialize file path storage
        self.file_path = ""

        # Button to upload an Excel file
        self.upload_button = tk.Button(master, text="Upload Excel File", command=self.upload_file)
        self.upload_button.pack(pady=10)

        # Button to process the Excel file
        self.process_button = tk.Button(master, text="Process File", command=self.process_file)
        self.process_button.pack(pady=10)

        # Label to show the file path
        self.label = tk.Label(master, text="No file selected")
        self.label.pack(pady=10)

    def center_window(self, width, height):
        # Calculate x and y coordinates for the Tkinter window to be centered
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        self.master.geometry(f"{width}x{height}+{x}+{y}")

    def upload_file(self):
        self.file_path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx"), ("Excel files", "*.xls"), ("CSV files", "*.csv")])
        if self.file_path:
            self.label.config(text=self.file_path)
        else:
            self.label.config(text="No file selected")

    def process_file(self):
        if not self.file_path:
            messagebox.showerror("Error", "Please upload an Excel file first.")
            return

        try:
            df = pd.read_excel(self.file_path, header=None)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read the Excel file: {e}")
            return

        if df.shape[1] < 2:
            messagebox.showerror("Error", "Excel file must have at least two columns.")
            return

        try:
            chrome_options = Options()
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get("about:blank")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start ChromeDriver: {e}")
            return

        wait = WebDriverWait(driver, 15)

        # Process each row in the Excel file
        for index, row in df.iterrows():
            search_text = str(row[0]).strip()
            website_to_click = str(row[1]).strip()
            found = False
            page_attempt = 1

            try:
                driver.get("https://www.google.com")
                time.sleep(2)

                # Check for CAPTCHA before entering the query
                try:
                    captcha_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'unusual traffic')]")
                    if captcha_elements:
                        input("CAPTCHA challenge detected on Google. Please solve it manually in the browser and press Enter to continue...")
                        print('captch 1a')
                        time.sleep(10)
                except Exception as captcha_err:
                    print("Captcha check error:", captcha_err)

                # Wait for the search box, then simulate typing the query
                search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")))
                search_box.clear()
                for char in search_text:
                    search_box.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.3))
                search_box.submit()

                # Loop through search result pages until target is found or no next page exists
                while True:
                    time.sleep(3)
                    # Wait for search results elements to load
                    try:
                        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'byrV5b')]")))
                    except TimeoutException:
                        print('failed')

                    # Check for CAPTCHA after loading results
                    try:
                        captcha_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'unusual traffic')]")
                        if captcha_elements:
                            input("CAPTCHA challenge detected after search. Please solve it manually and press Enter to continue...")
                            time.sleep(10)
                    except Exception as e:
                        print("Captcha check error:", e)

                    # Look through current page results
                    elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'byrV5b')]")
                    for elem in elements:
                        # Try to get the href attribute directly from the element
                        href = elem.get_attribute("href")
                        
                        # If href is None, try finding an anchor tag inside the element
                        if not href:
                            try:
                                a_elem = elem.find_element(By.TAG_NAME, "a")
                                href = a_elem.get_attribute("href")
                            except Exception:
                                href = None  # if no anchor exists, remain None

                        # Now only proceed if href is not None
                        if href and website_to_click in href:
                            print(f"Found matching link: {href}")
                            # If the anchor tag is found inside the element, click that element
                            # Alternatively, if elem is clickable itself, use elem.click()
                            try:
                                elem.click()
                            except Exception:
                                # If direct click on div fails, try clicking the inner anchor tag
                                try:
                                    a_elem.click()
                                except Exception as click_err:
                                    print("Error clicking the element:", click_err)
                            found = True
                            break

                    if found:
                        print(f"Found target website on page {page_attempt} for search text: '{search_text}'")

                        # Simulate user interactions on the found page sequentially.
                        simulate_user_interactions(driver)
                        
                        # After simulation is complete, navigate to a blank page to prepare for the next row.
                        
                        driver.get("about:blank")
                        break

                    # Try to click the "Next" button with id "pnnext"
                    try:
                        # Scroll to the bottom to reveal the Next button
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        next_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="pnnext"]/span[2]')))
                        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                        time.sleep(3)
                        
                        # Record current URL for waiting after navigation
                        current_url = driver.current_url
                        next_button.click()
                        page_attempt += 1
                        
                        # Wait until the URL changes to ensure the new page is loaded
                        wait.until(EC.url_changes(current_url))
                        time.sleep(random.uniform(3, 5))
                    except Exception:
                        print(f"[Row {index}] Last page reached. Website '{website_to_click}' not found for search text: '{search_text}'")
                        break

                time.sleep(random.uniform(4, 6))
            except Exception as row_err:
                print(f"Error processing row {index}: {row_err}")

        driver.quit()
        messagebox.showinfo("Info", "Processing finished!")

def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
