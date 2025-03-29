from tkinter import Frame, Label, Button, Entry, messagebox, Text, Checkbutton, BooleanVar, filedialog, StringVar, Scrollbar
from database import init_db, save_account, get_accounts, find_account, decrypt_password
from openai_logic import generate_seo_metadata, generate_article, generate_image_prompts_and_images
from login_logic import log_into_wordpress
import requests
from requests.auth import HTTPBasicAuth
import os
import sqlite3
from bs4 import BeautifulSoup
import re
from translations import load_translations, translate_text
from openai import OpenAI
import random
import pandas as pd
from docx import Document
import time
from tkinter import ttk
import threading
import queue
from datetime import datetime, timedelta

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Account Manager")
        self.root.geometry("800x750")  
        self.root.minsize(800, 750)
        self.language = "en"
        self.translations = {} 

        self.center_window()

        init_db()

        self.wp_base_url = None
        self.wp_username = None
        self.wp_password = None
        self.auth = None

        self.generated_seo_metadata = None
        self.generated_article = None
        self.generated_images = None

        # Start with language selection
        self.show_language_selection()

    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"+{x}+{y}")
    
    def clear_frame(self):
        """Destroy all widgets in the root window."""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_language_selection(self):
        """Display language selection screen."""
        self.clear_frame()
        lang_frame = Frame(self.root)
        lang_frame.pack(expand=True)

        Label(lang_frame, text="Select Language / Dil Seçimi", font=("Arial", 16)).pack(pady=20)
        Button(lang_frame, text="English", command=lambda: self.set_language("en"), width=20, height=2).pack(pady=10)
        Button(lang_frame, text="Türkçe", command=lambda: self.set_language("tr"), width=20, height=2).pack(pady=10)

    def set_language(self, lang_code):
        """Set the application language and load translations."""
        self.language = lang_code
        self.translations = load_translations(lang_code)
        self.setup_main_frame()
    
    def show_help_page(self):
        self.clear_frame()
        help_frame = Frame(self.root)
        help_frame.pack(expand=True)

        title_label = Label(help_frame, text=self.translations["manual"], font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 10))

        instructions = (
            "Welcome to the Automated WordPress Content Creator!\n"
            "====================================================\n"
            "This program automatically creates articles and product descriptions (PD) for your WordPress site and posts them directly. "
            "Below is a quick guide on how to get started and use each feature.\n\n"
            
            "1. Language Selection\n"
            "---------------------\n"
            "• Upon launching, you’ll be prompted to select a language: English or Turkish.\n"
            "• After choosing a language, you can either log into an existing account or create a new one.\n\n"
            
            "2. Logging into a New Account\n"
            "-----------------------------\n"
            "   2.1. Paste your website URL in the format https://domain.com/ (e.g., https://www.facebook.com/). This is for WordPress.\n"
            "   2.2. Enter your WordPress account username and password. IMPORTANT: Use your API password, not your regular login password. "
            "Refer to this guide on how to get it:\n"
            "       https://make.wordpress.org/core/2020/11/05/application-passwords-integration-guide/\n"
            "   2.3. Enter your OpenAI API key. You can find instructions on how to obtain it here:\n"
            "       https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key\n"
            "   2.4. Click 'Save Account'. If everything is correct, you’ll be taken back to the main page, where you can go to 'Log into Existing Account' and log in.\n"
            "   2.5. If there’s an error, the program will let you know what’s wrong.\n\n"
            
            "3. Logging into an Existing Account\n"
            "-----------------------------------\n"
            "   3.1. You’ll see a list of all your saved accounts. Click on the one (website + user) you want to log in as.\n"
            "   3.2. If everything is correct, you’ll be redirected to the content creation page. Otherwise, try updating your data by "
            "going to the 'Log into New Account' section and re-entering all the info.\n\n"
            
            "4. Content Creation Main Page\n"
            "-----------------------------\n"
            "   4.1. Here, you can select the language in which your articles or product descriptions will be generated (English or Turkish). "
            "You can also select the language for any additional data.\n"
            "   4.2. Choose whether you want to generate a single article, a product description, or bulk articles.\n"
            "   4.3. Don’t forget to upload the 'add data' folder created with the SEO Populator program if you need that extra data.\n\n"
            
            "5. Generate Article\n"
            "-------------------\n"
            "   5.1. Enter the article topic.\n"
            "   5.2. Enter any elementors (if needed).\n"
            "   5.3. Click 'Generate Content'. A message box and progress bar will appear. Please wait a few minutes while the article is created.\n"
            "   5.4. Once generated, you’ll be redirected to a preview page where you can see metadata and the article preview.\n"
            "   5.5. Click 'Post Article on WordPress'. Another message box and progress bar will appear.\n"
            "   5.6. After a successful post, you’ll be taken back to the content creation main page.\n\n"
            
            "6. Generate Product Description (PD)\n"
            "-----------------------------------\n"
            "   6.1. Enter the product topic, quantity, and price.\n"
            "   6.2. Enter any elementors (if needed).\n"
            "   6.3. Click 'Generate Content'. Wait a few minutes while the PD is generated.\n"
            "   6.4. Once done, you’ll be redirected to a preview page showing metadata and the PD preview.\n"
            "   6.5. Click 'Post PD on WordPress'. You’ll see a message box and progress bar.\n"
            "   6.6. After a successful post, you’ll be redirected to the content creation main page.\n\n"
            
            "7. Generate Bulk Articles\n"
            "-------------------------\n"
            "   7.1. Paste or upload a list of article topics.\n"
            "   7.2. If uploading, use CSV, DOCX, or Excel files. Topics will be auto-pasted (one topic per line). You can edit them before starting.\n"
            "   7.3. Select the time range for articles to be posted (default is 5–10 minutes).\n"
            "   7.4. Click 'Start Bulk Generation'. A message box and progress bar will appear.\n"
            "   7.5. Do NOT close the program until generation is complete. The program may become unresponsive, but this is normal.\n"
            "   7.6. Once finished, you’ll see a confirmation message and be taken back to the content creation main page.\n\n"
            
            "Conclusion\n"
            "----------\n"
            "This program is designed to streamline your content creation process by automatically generating and posting articles "
            "and product descriptions to your WordPress site. With language selection, account management, and bulk generation options, "
            "it aims to save you time and effort, so you can focus on what truly matters—growing your website.\n"
        )

        # Translate the instructions if the selected language is not English.
        if self.language != "en":
            instructions = translate_text(instructions, self.language)

        # Create a read-only Text widget to display the instructions with a scrollbar
        text_frame = Frame(help_frame)
        text_frame.pack(expand=True, fill="both")
        
        scrollbar = Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        text_widget = Text(text_frame, wrap="word", font=("Arial", 12), yscrollcommand=scrollbar.set, bg="#f9f9f9")
        text_widget.insert("1.0", instructions)
        text_widget.config(state="disabled")  # make read-only
        text_widget.pack(expand=True, fill="both")
        
        scrollbar.config(command=text_widget.yview)

        Button(help_frame, text=self.translations["back"], command=self.setup_main_frame, font=("Arial", 12, "bold")).pack(pady=10)

    def setup_main_frame(self):
        self.clear_frame()
        main_frame = Frame(self.root)
        main_frame.pack(fill="both", expand=True)

        Label(main_frame, text=self.translations["welcome"], font=("Arial", 16)).pack(pady=20)
        Button(main_frame, text=self.translations["help"], command=self.show_help_page).pack(pady=10)
        Button(main_frame, text=self.translations["log_existing_account"], command=self.setup_existing_account_frame).pack(pady=10)
        Button(main_frame, text=self.translations["log_new_account"], command=self.setup_new_account_frame).pack(pady=10)
        Button(main_frame, text=self.translations["back_to_languages"], command=self.show_language_selection).pack(pady=10)

    def setup_new_account_frame(self):
        self.clear_frame()
        new_account_frame = Frame(self.root)
        new_account_frame.pack(fill="both", expand=True)

        Label(new_account_frame, text=self.translations["new_acc"], font=("Arial", 16)).pack(pady=10)
        Label(new_account_frame, text=self.translations["website_url"]).pack(pady=10)
        self.url_entry = Entry(new_account_frame, width=40)
        self.url_entry.pack(pady=5)

        Label(new_account_frame, text=self.translations["username"]).pack(pady=10)
        self.username_entry = Entry(new_account_frame, width=40)
        self.username_entry.pack(pady=5)

        Label(new_account_frame, text=self.translations["password"]).pack(pady=10)
        self.password_entry = Entry(new_account_frame, width=40, show="*")
        self.password_entry.pack(pady=5)

        # Add a button to toggle password visibility
        self.show_password = False  # Track the current state of password visibility
        self.toggle_password_button = Button(
            new_account_frame,
            text=self.translations["show_password"],  # Add a translation for "Show Password"
            command=self.toggle_password_visibility
        )
        self.toggle_password_button.pack(pady=5)

        # OpenAI API Key
        Label(new_account_frame, text=self.translations["openai_api_key"]).pack(pady=10)
        self.api_key_entry = Entry(new_account_frame, width=40, show="*")  # Hide the API key by default
        self.api_key_entry.pack(pady=5)

        # Toggle API key visibility
        self.show_api_key = False
        self.toggle_api_key_button = Button(
            new_account_frame,
            text=self.translations["show_api_key"],
            command=self.toggle_api_key_visibility
        )
        self.toggle_api_key_button.pack(pady=5)

        Button(new_account_frame, text=self.translations["save_acc"], command=self.save_account).pack(pady=20)
        Button(new_account_frame, text=self.translations["back"], command=self.setup_main_frame).pack(pady=10)

    def toggle_password_visibility(self):
        # Toggle the password visibility
        self.show_password = not self.show_password
        if self.show_password:
            self.password_entry.config(show="")
            self.toggle_password_button.config(text=self.translations["hide_password"])  # Add a translation for "Hide Password"
        else:
            self.password_entry.config(show="*")
            self.toggle_password_button.config(text=self.translations["show_password"])
    
    def toggle_api_key_visibility(self):
        """Toggle the visibility of the OpenAI API key."""
        self.show_api_key = not self.show_api_key
        if self.show_api_key:
            self.api_key_entry.config(show="")
            self.toggle_api_key_button.config(text=self.translations["hide_api_key"])
        else:
            self.api_key_entry.config(show="*")
            self.toggle_api_key_button.config(text=self.translations["show_api_key"])

    def save_account(self):
        domain = self.url_entry.get().strip()
        username = self.username_entry.get().strip()
        plaintext_password = self.password_entry.get().strip()
        api_key = self.api_key_entry.get().strip()  # Get the OpenAI API key

        if not domain or not username or not plaintext_password or not api_key:
            messagebox.showerror(self.translations["error"], self.translations["all_fields_required"])
            return

        # Check if login is successful before saving
        result, message = log_into_wordpress(domain, username, plaintext_password, self.language)
        try:
            client = OpenAI(api_key=api_key)
            client.models.list()
            if result:
                self.wp_base_url = domain
                self.wp_username = username
                self.wp_password = plaintext_password
                self.auth = HTTPBasicAuth(username, plaintext_password)

                save_account(domain, username, plaintext_password, api_key)
                # messagebox.showinfo(self.translations["success"], f"{self.translations['login_success']} {self.translations['acc_saved']}")
                self.log_into_account(domain, username)
            else:
                messagebox.showerror(self.translations["error"], f'{self.translations["login_failed"]}: {message}. {self.translations["acc_not_saved"]}')
        except Exception as e:
                messagebox.showerror(self.translations["error"], f'{self.translations["openai_key_error"]}: {message}. {self.translations["acc_not_saved"]}')

    def setup_existing_account_frame(self):
        self.clear_frame()
        existing_account_frame = Frame(self.root)
        existing_account_frame.pack(fill="both", expand=True)

        Label(existing_account_frame, text=self.translations["existing_accs"], font=("Arial", 16)).pack(pady=10)

        accounts = get_accounts()
        if not accounts:
            Label(existing_account_frame, text=self.translations["no_data_yet"]).pack(pady=10)
        else:
            for account in accounts:
                account_id, domain, username, *_ = account
                Button(
                    existing_account_frame,
                    text=f"{domain} - {username}",
                    command=lambda d=domain, u=username: self.log_into_account(d, u)
                ).pack(pady=5)

        Button(existing_account_frame, text=self.translations["back"], command=self.setup_main_frame).pack(pady=10)

    def log_into_account(self, domain, username):
        """Logs into WordPress using existing credentials and saves them."""
        account = find_account(domain, username)
        if not account:
            messagebox.showerror(self.translations["error"], self.translations["acc_not_found"])
            return

        account_id, encrypted_password, api_key_encrypted, add_data_available, add_data_folder = account
        self.account_id = account_id  
        self.add_data_available = bool(add_data_available)  
        self.add_data_folder = add_data_folder

        try:
            plaintext_password = decrypt_password(encrypted_password)  
            api_key = decrypt_password(api_key_encrypted)  
        except Exception as e:
            messagebox.showerror(self.translations["error"], f"{self.translations['failed_decrypt_password']}: {e}")
            return

        result, message = log_into_wordpress(domain, username, plaintext_password, self.language)
        try:
            self.client = OpenAI(api_key=api_key)
            self.client.models.list()  # Test the API key by listing models
            if result:
                self.wp_base_url = domain
                self.wp_username = username
                self.wp_password = plaintext_password
                self.auth = HTTPBasicAuth(username, plaintext_password)

                messagebox.showinfo(self.translations["success"], self.translations["login_success"])
                self.show_content_selection_frame()  # Navigate to the selection frame
            else:
                messagebox.showerror(self.translations["error"], f"{self.translations['login_failed']}: {message}")
        except Exception as e:
                messagebox.showerror(self.translations["error"], f'{self.translations["openai_key_error"]}: {message}. {self.translations["acc_not_saved"]}')

    def show_content_selection_frame(self):
        """Show the frame to select between generating an article or a product description."""
        self.clear_frame()
        content_selection_frame = Frame(self.root)
        content_selection_frame.pack(fill="both", expand=True)

        Label(content_selection_frame, text=self.translations["select_content_type"], font=("Arial", 16)).pack(pady=20)

        # Language selection for content generation
        Label(content_selection_frame, text=self.translations["select_content_language"], font=("Arial", 12)).pack(pady=5)
        self.content_language_var = StringVar(value="tr")  # Default to English
        content_language_dropdown = ttk.Combobox(
            content_selection_frame,
            textvariable=self.content_language_var,
            values=["en", "tr"],  # Add more languages if needed
            state="readonly",
            width=10
        )
        content_language_dropdown.pack(pady=5)

        Button(
            content_selection_frame,
            text=self.translations["generate_article"],
            command=self.setup_article_frame
        ).pack(pady=10)

        Button(
            content_selection_frame,
            text=self.translations["generate_product_description"],
            command=self.setup_product_description_frame
        ).pack(pady=10)

        # Add button for bulk generation
        Button(
            content_selection_frame,
            text=self.translations["bulk_generation"],
            command=self.setup_bulk_generation_frame
        ).pack(pady=10)

        # Check if additional data is available for the logged-in account
        account = find_account(self.wp_base_url, self.wp_username)
        if account:
            account_id, _, _, add_data_available, add_data_folder = account

            if add_data_available:
                # Checkbox to use additional data
                self.use_additional_data = BooleanVar(value=True)
                Checkbutton(
                    content_selection_frame,
                    text=self.translations["use_add_data"],
                    variable=self.use_additional_data
                ).pack(pady=5)

                # Button to change the additional data folder
                Button(
                    content_selection_frame,
                    text=self.translations["change_add_data_folder"],
                    command=lambda: self.change_additional_data_folder(account_id)
                ).pack(pady=10)
            else:
                # Button to upload the additional data folder
                Button(
                    content_selection_frame,
                    text=self.translations["upload_add_data_folder"],
                    command=lambda: self.upload_additional_data_folder(account_id)
                ).pack(pady=10)

        Button(
            content_selection_frame,
            text=self.translations["back_to_login"],
            command=self.setup_main_frame
        ).pack(pady=10)

    def setup_product_description_frame(self):
        """Set up the frame for generating product descriptions."""
        self.clear_frame()
        product_description_frame = Frame(self.root)
        product_description_frame.pack(fill="both", expand=True)

        Label(product_description_frame, text=self.translations["generate_product_description"], font=("Arial", 16)).pack(pady=20)

        Label(product_description_frame, text=f"{self.translations['enter_topic']}:").pack(pady=10)
        self.topic_entry = Entry(product_description_frame, width=50)
        self.topic_entry.pack(pady=10)

        Label(product_description_frame, text=self.translations["enter_price"]).pack(pady=10)
        self.price_entry = Entry(product_description_frame, width=50)
        self.price_entry.insert(0, "0")  # Default price
        self.price_entry.pack(pady=10)

        Label(product_description_frame, text=self.translations["enter_stock_quantity"]).pack(pady=10)
        self.stock_entry = Entry(product_description_frame, width=50)
        self.stock_entry.insert(0, "1")  # Default stock quantity
        self.stock_entry.pack(pady=10)

        # Add Elementor elements input
        Label(product_description_frame, text=self.translations["enter_elementor_elements"]).pack(pady=10)
        self.elementor_elements_entry = Text(product_description_frame, height=3, width=50)
        self.elementor_elements_entry.pack(pady=10)

        Button(
            product_description_frame,
            text=self.translations["generate_content"],
            command=self.generate_product_description
        ).pack(pady=20)

        Button(
            product_description_frame,
            text=self.translations["back"],
            command=self.show_content_selection_frame
        ).pack(pady=10)

    def insert_elementor_elements(self, content, elements):
        """Insert Elementor elements randomly into the content."""
        if not elements:
            return content

        paragraphs = content.split("\n\n")  # Split content into paragraphs
        for element in elements:
            # Insert the element at a random position
            insert_position = random.randint(0, len(paragraphs))
            paragraphs.insert(insert_position, element)

        return "\n\n".join(paragraphs)

    def generate_product_description(self):
        """Generates a product description."""
        generation_label = ttk.Label(self.root, text=self.translations["generating_pd"], font=("Arial", 10))
        generation_label.pack(pady=5)
        
        progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="indeterminate")
        progress.pack(pady=10)
        progress.start()

        self.topic_pd = self.topic_entry.get().strip()
        self.price = self.price_entry.get().strip()
        self.stock = self.stock_entry.get().strip()

        elements_text = self.elementor_elements_entry.get("1.0", "end-1c").strip()
        if not elements_text:
            self.elementor = []
        else:
            self.elementor = elements_text.splitlines()

        if not self.topic_pd:
            messagebox.showerror(self.translations["error"], self.translations["enter_topic"])
            return
        
        content_language = self.content_language_var.get()

        try:
            messagebox.showinfo(self.translations["processing"], self.translations["wait_minute_pd"])
            self.generated_seo_metadata = generate_seo_metadata(self.topic_pd, 'product description', self.client, language=content_language)
            self.generated_article = generate_article(
                self.topic_pd,
                self.generated_seo_metadata,
                self.client,
                account_id=self.account_id,
                content_type="product_description",
                language=content_language
            )
            self.generated_images = generate_image_prompts_and_images(self.topic_pd, self.generated_seo_metadata, "product_description", self.client, language=content_language)
            
            progress.stop()
            progress.destroy()
            generation_label.destroy()

            self.post_product()

        except Exception as e:
            progress.stop()
            progress.destroy()
            generation_label.destroy()
            messagebox.showerror(self.translations["error"], f"{self.translations['failed_generate_content']}: {e}")

    def setup_article_frame(self):
        """Sets up the article generation frame."""
        self.clear_frame()
        article_frame = Frame(self.root)
        article_frame.pack(fill="both", expand=True)

        Label(article_frame, text=self.translations["generate_article"], font=("Arial", 16)).pack(pady=20)

        Label(article_frame, text=f"{self.translations['enter_topic']}:").pack(pady=10)
        self.topic_entry = Entry(article_frame, width=50)
        self.topic_entry.pack(pady=10)

        Label(article_frame, text=self.translations["enter_elementor_elements"]).pack(pady=10)
        self.elementor_elements_entry = Text(article_frame, height=3, width=50)
        self.elementor_elements_entry.pack(pady=10)

        account = find_account(self.wp_base_url, self.wp_username)
        if account:
            account_id, _, _, add_data_available, add_data_folder = account

        Button(article_frame, text=self.translations["generate_content"], command=lambda: self.generate_content(account_id)).pack(pady=20)
        Button(article_frame, text=self.translations["back"], command=self.show_content_selection_frame).pack(pady=10)

    def change_additional_data_folder(self, account_id):
        """Change the folder containing additional data."""
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return

        # Validate the folder contains the required files
        required_files = ["company.html", "company.txt"]
        for file in required_files:
            if not os.path.exists(os.path.join(folder_path, file)):
                generated_message = self.translations["missing_required_file"].format(file=file)
                messagebox.showerror(self.translations["error"], f"{generated_message}")
                return

        # Update the database with the new folder path
        conn = sqlite3.connect("accounts.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE accounts
            SET add_data_available = 1, add_data_folder = ?
            WHERE id = ?
        """, (folder_path, account_id))
        conn.commit()
        conn.close()

        messagebox.showinfo(self.translations["success"], self.translations["add_data_folder_success"])
        self.setup_article_frame() 

    def generate_content(self, account_id):
        """Generates SEO metadata, article, and images."""
        # Create and display the progress bar
        generation_label = ttk.Label(self.root, text=self.translations["generating_article"], font=("Arial", 10))
        generation_label.pack(pady=5)

        progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="indeterminate")
        progress.pack(pady=10)
        progress.start()

        topic = self.topic_entry.get().strip()

        elements_text = self.elementor_elements_entry.get("1.0", "end-1c").strip()
        if not elements_text:
            self.elementor = []
        else:
            self.elementor = elements_text.splitlines()

        if not topic:
            messagebox.showerror(self.translations["error"], self.translations["enter_topic"])
            return
        
        # Get selected languages
        content_language = self.content_language_var.get()
        
        try:
            messagebox.showinfo(self.translations["processing"], self.translations["wait_minute_article"])
            self.generated_seo_metadata = generate_seo_metadata(topic, "article", self.client, language=content_language)
            use_additional_data = getattr(self, "use_additional_data", BooleanVar(value=False)).get()
            self.generated_article = generate_article(topic, self.generated_seo_metadata, self.client, account_id if use_additional_data else None, "article", language=content_language)
            self.generated_images = generate_image_prompts_and_images(topic, self.generated_seo_metadata, "article", self.client, language=content_language)
            
            progress.stop()
            progress.destroy()
            generation_label.destroy()
            self.post_article()

        except Exception as e:
            progress.stop()
            progress.destroy()
            generation_label.destroy()
            messagebox.showerror(self.translations["error"], f"{self.translations['failed_generate_content']}: {e}")

    def upload_additional_data_folder(self, account_id):
        """Upload a folder containing additional data."""
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return

        required_files = ["company.html", "company.txt"]
        for file in required_files:
            if not os.path.exists(os.path.join(folder_path, file)):
                generated_message = self.translations["missing_required_file"].format(file=file)
                messagebox.showerror(self.translations["error"], f"{generated_message}")
                return

        conn = sqlite3.connect("accounts.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE accounts
            SET add_data_available = 1, add_data_folder = ?
            WHERE id = ?
        """, (folder_path, account_id))
        conn.commit()
        conn.close()

        messagebox.showinfo(self.translations["success"], self.translations["add_data_folder_upload_success"])
        self.setup_article_frame() 
    
    def get_or_create_tag(self, tag_name):
        # Check if the tag already exists
        response = requests.get(f"{self.wp_base_url}/wp-json/wp/v2/tags", params={"search": tag_name}, auth=self.auth)

        if response.status_code == 200 and response.json():
            # Tag exists, return its ID
            return response.json()[0]["id"]
        
        # Tag doesn't exist, create it
        response = requests.post(
            f"{self.wp_base_url}/wp-json/wp/v2/tags",
            json={"name": tag_name},
            auth=self.auth
        )
        
        if response.status_code == 201:
            # Tag created, return its ID
            return response.json()["id"]
        
        # If something went wrong
        raise Exception(f"Failed to get or create tag: {tag_name}")

    def post_article(self, content_type="single"):
        """Posts the article to WordPress."""
        generation_label = ttk.Label(self.root, text=self.translations["posting_article"], font=("Arial", 10))
        generation_label.pack(pady=5)

        progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="indeterminate")
        progress.pack(pady=10)
        progress.start()

        if not self.wp_base_url or not self.auth:
            messagebox.showerror(self.translations["error"], self.translations["must_login"])
            return

        if not self.generated_seo_metadata or not self.generated_article or not self.generated_images:
            messagebox.showerror(self.translations["error"], self.translations["missing_generated_content"])
            return

        try:
            if content_type == "single":
                messagebox.showinfo(self.translations["processing"], self.translations["article_being_posted"])
            self.generated_article["article"] = self.insert_elementor_elements(self.generated_article["article"], self.elementor)
            
            uploaded_images = self.upload_images_to_wordpress()

            if not uploaded_images:
                messagebox.showerror(self.translations["error"], self.translations["no_images_uploaded"])
                return

            images_html = ""
            for image in uploaded_images:
                image_tag = f"<img src='{image['url']}' alt='{image['alt_text']}' title='{image['title']}' />"
                images_html += f"{image_tag}\n"

            content = self.generated_article

            article_text = content["article"]
            additional_content = content["additional_content"]
            additional_fk = content["additional_fk"]
            tags = content["tags"]
            tag_ids = [self.get_or_create_tag(tag) for tag in tags]

            article_html = article_text + images_html + additional_content + images_html

            focus_keywords = f'{self.generated_seo_metadata["Focus Keyword"]}, {additional_fk}'
            adjusted_keywords, plain_text = self.adjust_keyword_density(article_html, focus_keywords, content_type="article")

            post_data = {
                "title": self.generated_seo_metadata["SEO Title"],
                "content": article_html,
                "status": "publish",
                "slug": self.generated_seo_metadata["URL Slug"],
                "tags": tag_ids,  # Add tags as a list of tag names
                "meta": {
                    "rank_math_title": self.generated_seo_metadata["SEO Title"],
                    "rank_math_description": self.generated_seo_metadata["Meta Description"],
                    "rank_math_focus_keyword": adjusted_keywords
                }
            }
            
            response = requests.post(f"{self.wp_base_url}/wp-json/wp/v2/posts", json=post_data, auth=self.auth)
            if response.status_code == 201:
                post_id = response.json()["id"]  
                if content_type == "single":
                    messagebox.showinfo(self.translations["success"], self.translations["articles_posted_successfully"])

                first_image = uploaded_images[0]
                featured_image_id = self.get_image_id(first_image["url"]) 

                if featured_image_id:
                    update_post_data = {"featured_media": featured_image_id}
                    update_response = requests.post(
                        f"{self.wp_base_url}/wp-json/wp/v2/posts/{post_id}",
                        json=update_post_data,
                        auth=self.auth
                    )
                    if update_response.status_code == 200:
                        print(self.translations["feature_image_success"])
                    else:
                        print(f"{self.translations['feature_image_fail']}: {update_response.text}")
                else:
                    print(self.translations["feature_image_id_fail"])

                for image in self.generated_images:
                    local_path = image["local_path"]
                    if os.path.exists(local_path):
                        try:
                            os.remove(local_path)
                            print(f"{self.translations['deleted_local_image']}: {local_path}")
                        except Exception as e:
                            print(f"{self.translations['delete_local_image_fail']} {local_path}: {e}")
                progress.stop()
                progress.destroy()
                generation_label.destroy()
                if content_type == "single":
                    self.show_content_selection_frame()
            else:
                progress.stop()
                progress.destroy()
                generation_label.destroy()
                messagebox.showerror(self.translations["error"], f"{self.translations['fail_post_article']}: {response.text}")
        except Exception as e:
            progress.stop()
            progress.destroy()
            messagebox.showerror(self.translations["error"], f"{self.translations['fail_post_article']}: {e}")

    def get_or_create_tag_pd(self, tag_name):
        # Check if the tag already exists
        response = requests.get(
            f"{self.wp_base_url}/wp-json/wc/v3/products/tags",
            params={"search": tag_name},
            auth=self.auth
        )

        if response.status_code == 200 and response.json():
            # Tag exists, return its ID as a dictionary
            return {"id": response.json()[0]["id"]}
        
        # Tag doesn't exist, create it
        response = requests.post(
            f"{self.wp_base_url}/wp-json/wc/v3/products/tags",
            json={"name": tag_name},
            auth=self.auth
        )
        
        if response.status_code == 201:
            # Tag created, return its ID as a dictionary
            return {"id": response.json()["id"]}
        
        # If something went wrong
        raise Exception(f"Failed to get or create tag: {tag_name}")

    def post_product(self):
        """Posts the article to WordPress."""
        generation_label = ttk.Label(self.root, text=self.translations["posting_pd"], font=("Arial", 10))
        generation_label.pack(pady=5)

        progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="indeterminate")
        progress.pack(pady=10)
        progress.start()

        if not self.wp_base_url or not self.auth:
            messagebox.showerror(self.translations["error"], self.translations["must_login"])
            return

        if not self.generated_seo_metadata or not self.generated_article or not self.generated_images:
            messagebox.showerror(self.translations["error"], self.translations["missing_generated_content"])
            return

        try:
            messagebox.showinfo(self.translations["processing"], self.translations["pd_being_posted"])
            # self.generated_article["article"] = self.insert_elementor_elements(self.generated_article["article"], self.elementor)
            
            uploaded_images = self.upload_images_to_wordpress()

            if not uploaded_images:
                messagebox.showerror(self.translations["error"], self.translations["no_images_uploaded"])
                return

            images_html = ""
            for image in uploaded_images:
                image_tag = f"<img src='{image['url']}' alt='{image['alt_text']}' title='{image['title']}' />"
                images_html += f"{image_tag}\n"

            content = self.generated_article

            article_text = content["article"]
            additional_content = content["additional_content"]
            additional_fk = content["additional_fk"]
            tags = content["tags"]
            tag_ids = [self.get_or_create_tag_pd(tag) for tag in tags]
            print(tag_ids)

            article_html = article_text + images_html + additional_content + images_html
            article_html_kw_density = article_text + article_html

            focus_keywords = f'{self.generated_seo_metadata["Focus Keyword"]}, {additional_fk}'
            adjusted_keywords, plain_text = self.adjust_keyword_density(article_html_kw_density, focus_keywords, content_type="product_description")
            
            article_html = self.insert_elementor_elements(article_html, self.elementor)

            topic = self.topic_pd
            price = self.price
            stock = self.stock

            # Prepare product data
            post_data = {
                "name": topic,
                "type": "simple",
                "regular_price": str(price),
                "description": article_html,
                "short_description": article_text,
                "images": [{"src": image['url']} for image in uploaded_images],
                "stock_status": "instock" if int(stock) > 0 else "outofstock",
                "title": self.generated_seo_metadata["SEO Title"],
                "status": "publish",
                "slug": self.generated_seo_metadata["URL Slug"],
                "tags": tag_ids,
                "meta_data": [
                    {"key": "rank_math_title", "value": self.generated_seo_metadata["SEO Title"]},
                    {"key": "rank_math_description", "value": self.generated_seo_metadata["Meta Description"]},
                    {"key": "rank_math_focus_keyword", "value": adjusted_keywords}
                ]
            }
            
            response = requests.post(f"{self.wp_base_url}/wp-json/wc/v3/products", json=post_data, auth=self.auth)
            if response.status_code == 201:
                post_id = response.json()["id"]  
                messagebox.showinfo(self.translations["success"], self.translations["product_posted_successfully"])

                first_image = uploaded_images[0]
                featured_image_id = self.get_image_id(first_image["url"]) 

                if featured_image_id:
                    update_post_data = {"featured_media": featured_image_id}
                    update_response = requests.post(
                        f"{self.wp_base_url}/wp-json/wc/v3/products/{post_id}",
                        json=update_post_data,
                        auth=self.auth
                    )
                    if update_response.status_code == 200:
                        print(self.translations["feature_image_success"])
                    else:
                        print(f"{self.translations['feature_image_fail']}: {update_response.text}")
                else:
                    print(self.translations["feature_image_id_fail"])

                for image in self.generated_images:
                    local_path = image["local_path"]
                    if os.path.exists(local_path):
                        try:
                            os.remove(local_path)
                            print(f"{self.translations['deleted_local_image']}: {local_path}")
                        except Exception as e:
                            print(f"{self.translations['delete_local_image_fail']} {local_path}: {e}")
                progress.stop()
                progress.destroy() 
                generation_label.destroy()
                self.show_content_selection_frame()

            else:
                progress.stop()
                progress.destroy()
                generation_label.destroy()
                messagebox.showerror(self.translations["error"], f"{self.translations['fail_post_article']}: {response.text}")
        except Exception as e:
            progress.stop()
            progress.destroy()
            generation_label.destroy()
            messagebox.showerror(self.translations["error"], f"{self.translations['fail_post_article']}: {e}")

    def get_image_id(self, image_url):
        """
        Retrieve the ID of an uploaded image by its URL.
        """
        try:
            filename = os.path.basename(image_url)

            response = requests.get(
                f"{self.wp_base_url}/wp-json/wp/v2/media",
                params={"search": filename},
                auth=self.auth
            )

            if response.status_code == 200:
                media_items = response.json()
                for item in media_items:
                    if item.get("source_url") == image_url:
                        return item["id"]
            else:
                print(f"{self.translations['media_api_fail']} {self.translations['status_code']}: {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"{self.translations['get_image_id_error']}: {e}")

        print(f"{self.translations['fail_media_id_image']}: {image_url}")
        return None

    def upload_images_to_wordpress(self):
        """Upload images to WordPress and return their URLs."""
        image_urls = []
        for image_data in self.generated_images:
            try:
                with open(image_data["local_path"], "rb") as image_file:
                    filename = os.path.basename(image_data["local_path"])
                    filename = filename.encode('utf-8').decode('latin-1')  # Handle non-ASCII characters
                    headers = {"Content-Disposition": f"attachment; filename={filename}"}
                    response = requests.post(f"{self.wp_base_url}/wp-json/wp/v2/media", headers=headers, files={"file": image_file}, auth=self.auth)
                if response.status_code == 201:
                    image_urls.append({"url": response.json()["source_url"], "alt_text": image_data["alt_text"], "title": image_data["title"]})
            except Exception as e:
                print(f"{self.translations['image_upload_error']}: {e}")
        return image_urls

    def adjust_keyword_density(self, article_html, focus_keywords, content_type="article"):
        """
        Adjusts keyword density for the given article HTML and focus keywords.
        :param article_html: The HTML content of the article.
        :param focus_keywords: The string of focus keywords separated by commas.
        :param content_type: Type of content ("article" or "product_description").
        :return: Updated focus keywords string and cleaned HTML text.
        """
        # Extract plain text from HTML
        text_content = BeautifulSoup(article_html, "html.parser").get_text()

        # Split focus keywords into a list
        focus_keyword_list = [kw.strip() for kw in focus_keywords.split(",")]
        preserved_keyword = focus_keyword_list[0]  # Always keep the first keyword
        remaining_keywords = focus_keyword_list[1:]  # Keywords that can be removed

        # Calculate initial keyword density
        keyword_counts = {}
        for kw in focus_keyword_list:
            pattern = rf'\b{re.escape(kw)}\w*'
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            keyword_counts[kw] = len(matches)

        total_occurrences = sum(keyword_counts.values())
        total_word_count = len(re.findall(r'\b\w+\b', text_content))  # Total words in the text
        keyword_density = total_occurrences / total_word_count

        # Remove the last keyword while density is too high
        while keyword_density > 0.024 and remaining_keywords:
            removed_keyword = remaining_keywords.pop()  # Remove the last keyword
            del keyword_counts[removed_keyword]  # Remove its count
            total_occurrences = sum(keyword_counts.values())  # Recalculate total occurrences
            keyword_density = total_occurrences / total_word_count  # Recalculate density
        
        # Join the preserved keyword and remaining keywords
        updated_focus_keywords = ", ".join([preserved_keyword] + remaining_keywords)

        return updated_focus_keywords, text_content

    def setup_bulk_generation_frame(self):
        """Set up the frame for bulk article generation."""
        self.clear_frame()
        bulk_frame = Frame(self.root)
        bulk_frame.pack(fill="both", expand=True)

        Label(bulk_frame, text=self.translations["bulk_generation"], font=("Arial", 16)).pack(pady=20)

        # Option to upload a file or paste topics
        Label(bulk_frame, text=self.translations["upload_or_paste_topics"]).pack(pady=10)
        self.bulk_topics_entry = Text(bulk_frame, height=10, width=50)
        self.bulk_topics_entry.pack(pady=10)

        Button(
            bulk_frame,
            text=self.translations["upload_file"],
            command=self.upload_bulk_topics_file
        ).pack(pady=10)

        # Elementor elements input
        Label(bulk_frame, text=self.translations["enter_elementor_elements"]).pack(pady=10)
        self.bulk_elementor_elements_entry = Text(bulk_frame, height=3, width=50)
        self.bulk_elementor_elements_entry.pack(pady=10)

        # Time range for posting
        Label(bulk_frame, text=self.translations["enter_time_range"]).pack(pady=10)
        time_range_frame = Frame(bulk_frame)
        time_range_frame.pack(pady=10)

        Label(time_range_frame, text=self.translations["min_minutes"]).pack(side="left")
        self.min_time_entry = Entry(time_range_frame, width=5)
        self.min_time_entry.pack(side="left", padx=5)
        self.min_time_entry.insert(0, "5")  # Default minimum time

        Label(time_range_frame, text=self.translations["max_minutes"]).pack(side="left")
        self.max_time_entry = Entry(time_range_frame, width=5)
        self.max_time_entry.pack(side="left", padx=5)
        self.max_time_entry.insert(0, "10")  # Default maximum time

        # Check if additional data is available for the logged-in account
        account = find_account(self.wp_base_url, self.wp_username)
        if account:
            account_id, _, _, add_data_available, add_data_folder = account

        Button(bulk_frame, text=self.translations["start_bulk_generation"], command=lambda: self.start_bulk_generation(account_id)).pack(pady=20)

        Button(
            bulk_frame,
            text=self.translations["back"],
            command=self.show_content_selection_frame
        ).pack(pady=10)

    def upload_bulk_topics_file(self):
        """Upload a file containing topics for bulk generation."""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("CSV Files", "*.csv"),
                ("Word Files", "*.docx"),
                ("Excel Files", "*.xlsx")
            ]
        )
        if not file_path:
            return

        try:
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path)
                topics = df.iloc[:, 0].tolist()  # Assume topics are in the first column
            elif file_path.endswith(".docx"):
                doc = Document(file_path)
                topics = [para.text for para in doc.paragraphs if para.text.strip()]
            elif file_path.endswith(".xlsx"):
                df = pd.read_excel(file_path)
                topics = df.iloc[:, 0].tolist()  # Assume topics are in the first column
            else:
                messagebox.showerror(self.translations["error"], self.translations["unsupported_file_format"])
                return

            # Insert topics into the text widget
            self.bulk_topics_entry.delete("1.0", "end")
            self.bulk_topics_entry.insert("1.0", "\n".join(topics))

        except Exception as e:
            messagebox.showerror(self.translations["error"], f"{self.translations['file_upload_error']}: {e}")

    def start_bulk_generation(self, account_id):
        """Start the bulk article generation process with threading and incremental scheduling."""
        # Create and display a label to indicate generation is in progress
        generation_label = ttk.Label(self.root, text=self.translations["generating_articles"], font=("Arial", 10))
        generation_label.pack(pady=5)
        
        # Create a determinate progress bar
        progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        progress.pack(pady=10)

        # Retrieve topics
        topics_text = self.bulk_topics_entry.get("1.0", "end-1c").strip()
        if not topics_text:
            messagebox.showerror(self.translations["error"], self.translations["no_topics_provided"])
            progress.destroy()
            generation_label.destroy()
            return
        
        topics = topics_text.splitlines()
        # Set the maximum value of the progress bar to the number of topics
        progress["maximum"] = len(topics)

        # Get selected languages
        content_language = self.content_language_var.get()

        # Retrieve Elementor elements
        elements_text = self.bulk_elementor_elements_entry.get("1.0", "end-1c").strip()
        if not elements_text:
            self.elementor = []
        else:
            self.elementor = elements_text.splitlines()

        # Retrieve time range
        try:
            min_time = int(self.min_time_entry.get().strip())
            max_time = int(self.max_time_entry.get().strip())
            if min_time < 1 or max_time < 1 or min_time > max_time:
                raise ValueError("Invalid time range")
        except Exception as e:
            progress.destroy()
            generation_label.destroy()
            messagebox.showerror(self.translations["error"], self.translations["invalid_time_range"])
            return

        # Function to generate and schedule articles
        def generate_and_schedule_article(topic, delay):
            try:
                self.generated_seo_metadata = generate_seo_metadata(topic, "article", self.client, language=content_language)
                use_additional_data = self.use_additional_data.get()
                self.generated_article = generate_article(topic, self.generated_seo_metadata, self.client, account_id if use_additional_data else None, "article", language=content_language)
                self.generated_images = generate_image_prompts_and_images(topic, self.generated_seo_metadata, "article", self.client, language=content_language)
                self.schedule_post()
                time.sleep(delay)
            except Exception as e:
                print(f"Failed to generate or schedule article for topic {topic}: {e}")
            finally:
                progress["value"] += 1
                self.root.update_idletasks()  # Update the GUI

        messagebox.showinfo(self.translations["processing"], self.translations["wait_bulk_articles"])

        for topic in topics:
            delay = random.randint(min_time * 60, max_time * 60)  # Convert minutes to seconds
            generate_and_schedule_article(topic, delay)

        progress.destroy()
        generation_label.destroy()
        messagebox.showinfo(self.translations["success"], self.translations["all_articles_scheduled"])
        self.show_content_selection_frame()

    def schedule_post(self):
        """Schedule the article to be posted immediately."""
        if not self.wp_base_url or not self.auth:
            messagebox.showerror(self.translations["error"], self.translations["must_login"])
            return

        if not self.generated_seo_metadata or not self.generated_article or not self.generated_images:
            messagebox.showerror(self.translations["error"], self.translations["missing_generated_content"])
            return

        try:
            self.generated_article["article"] = self.insert_elementor_elements(self.generated_article["article"], self.elementor)
            
            uploaded_images = self.upload_images_to_wordpress()

            if not uploaded_images:
                messagebox.showerror(self.translations["error"], self.translations["no_images_uploaded"])
                return

            images_html = ""
            for image in uploaded_images:
                image_tag = f"<img src='{image['url']}' alt='{image['alt_text']}' title='{image['title']}' />"
                images_html += f"{image_tag}\n"

            content = self.generated_article

            article_text = content["article"]
            additional_content = content["additional_content"]
            additional_fk = content["additional_fk"]
            tags = content["tags"]
            tag_ids = [self.get_or_create_tag(tag) for tag in tags]

            article_html = article_text + images_html + additional_content + images_html

            focus_keywords = f'{self.generated_seo_metadata["Focus Keyword"]}, {additional_fk}'
            adjusted_keywords, plain_text = self.adjust_keyword_density(article_html, focus_keywords, content_type="article")

            post_data = {
                "title": self.generated_seo_metadata["SEO Title"],
                "content": article_html,
                "status": "publish",
                "slug": self.generated_seo_metadata["URL Slug"],
                "tags": tag_ids,
                "meta": {
                    "rank_math_title": self.generated_seo_metadata["SEO Title"],
                    "rank_math_description": self.generated_seo_metadata["Meta Description"],
                    "rank_math_focus_keyword": adjusted_keywords
                }
            }
            
            response = requests.post(f"{self.wp_base_url}/wp-json/wp/v2/posts", json=post_data, auth=self.auth)
            if response.status_code == 201:
                post_id = response.json()["id"]  

                first_image = uploaded_images[0]
                featured_image_id = self.get_image_id(first_image["url"]) 

                if featured_image_id:
                    update_post_data = {"featured_media": featured_image_id}
                    update_response = requests.post(
                        f"{self.wp_base_url}/wp-json/wp/v2/posts/{post_id}",
                        json=update_post_data,
                        auth=self.auth
                    )
                    if update_response.status_code == 200:
                        print(self.translations["feature_image_success"])
                    else:
                        print(f"{self.translations['feature_image_fail']}: {update_response.text}")
                else:
                    print(self.translations["feature_image_id_fail"])

                for image in self.generated_images:
                    local_path = image["local_path"]
                    if os.path.exists(local_path):
                        try:
                            os.remove(local_path)
                            print(f"{self.translations['deleted_local_image']}: {local_path}")
                        except Exception as e:
                            print(f"{self.translations['delete_local_image_fail']} {local_path}: {e}")
            else:
                messagebox.showerror(self.translations["error"], f"{self.translations['fail_post_article']}: {response.text}")
        except Exception as e:
            messagebox.showerror(self.translations["error"], f"{self.translations['fail_post_article']}: {e}")

