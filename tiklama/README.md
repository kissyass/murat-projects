# Selenium Interaction Programs Suite

This repository contains three Python programs that automate simulated user interactions using Selenium and ChromeDriverManager. Each program processes Excel file inputs to control web interactions in different ways.

## Programs Overview

### 1. main.py (Proxies Simulation)
- **Description:**  
  Uses proxies to simulate user interactions while opening links.
- **Features:**  
  - Uploads two Excel files:
    - One containing proxy settings.
    - One with links to be opened.
  - Uses the specified proxies to open links and simulate user interactions.
- **Status:**  
  Currently in development and may not work as expected.

### 2. no_proxy.py (Direct Interaction)
- **Description:**  
  Processes an Excel file with links, opening each URL directly without using proxies.
- **Features:**  
  - Upload an Excel file with URLs.
  - Opens the links and simulates user interactions sequentially.

### 3. google_tiklama.py (Google Search Interaction)
- **Description:**  
  Automates interactions with Google search based on Excel file inputs.
- **Features:**  
  - Upload an Excel file containing two columns:
    - **First Column:** The text to search.
    - **Second Column:** The target website URL.
  - For each row, the program:
    - Types the provided text into Google.
    - Searches for the specified website.
    - Opens the target website from the search results.
    - Simulates further user interaction on that website.

All three programs use Selenium for browser automation and ChromeDriverManager to manage the Chrome WebDriver.
