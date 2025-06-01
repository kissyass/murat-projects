import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import random
import time
import re
from openai import OpenAI
from requests.auth import HTTPBasicAuth
from datetime import datetime 
import requests
from bs4 import BeautifulSoup
from image_resize import resize_and_compress_local_image
import time
import random

from openai_logic import generate_seo_metadata, generate_article, generate_image_prompts_and_images, generate_tags
from openai_logic import generate_html_info, generate_article_summary
from login_logic import log_into_wordpress
from database import init_db, save_account_to_db, get_accounts, find_account, get_record_table_for_account, update_record_table_for_account
from database import create_data_table, insert_data_into_table, get_next_record, mark_record_as_used, update_company_info, get_company_info
from database import get_additional_data_table_for_account, update_additional_data_table_for_account, create_additional_data_table
from database import insert_summary_into_table, get_all_summaries_from_table
from utils import insert_images_evenly, insert_elementor_randomly, encrypt_password, decrypt_password

# -------------------------
# Main Application Class

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Content Generation & Posting App")
        self.root.geometry("900x700")
        init_db()
        
        self.current_account = None  
        self.current_record_table = None 
        self.client = None  
        self.auth = None
        self.wp_base_url = None

        # Variables for Excel file and data table creation.
        self.data_df = None

        # For generation progress tracking.
        self.generating = False

        self.show_login_selection_frame()

    def clear_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # -------------------------
    # Login / Account Selection Frames
    def show_login_selection_frame(self):
        self.clear_frame()
        frame = tk.Frame(self.root)
        frame.pack(expand=True, fill="both")

        tk.Label(frame, text="Select Login Option", font=("Arial", 18)).pack(pady=20)
        tk.Button(frame, text="New Account Login", width=25, command=self.show_new_account_frame).pack(pady=10)
        tk.Button(frame, text="Existing Account Login", width=25, command=self.show_existing_account_frame).pack(pady=10)
    
    def toggle_password_visibility(self):
        # Toggle the password visibility
        self.show_password = not self.show_password
        if self.show_password:
            self.new_password_entry.config(show="")
            self.toggle_password_button.config(text="Hide Password")  # Add a translation for "Hide Password"
        else:
            self.new_password_entry.config(show="*")
            self.toggle_password_button.config(text="Show Password")
    
    def toggle_api_key_visibility(self):
        """Toggle the visibility of the OpenAI API key."""
        self.show_api_key = not self.show_api_key
        if self.show_api_key:
            self.new_api_entry.config(show="")
            self.toggle_api_key_button.config(text='Hide API Key')
        else:
            self.new_api_entry.config(show="*")
            self.toggle_api_key_button.config(text="Show API Key")

    def show_new_account_frame(self):
        self.clear_frame()
        frame = tk.Frame(self.root)
        frame.pack(expand=True, fill="both")

        tk.Label(frame, text="New Account Login", font=("Arial", 18)).pack(pady=10)
        tk.Label(frame, text="Website URL:").pack(pady=5)
        self.new_domain_entry = tk.Entry(frame, width=40)
        self.new_domain_entry.pack(pady=5)

        tk.Label(frame, text="Username:").pack(pady=5)
        self.new_username_entry = tk.Entry(frame, width=40)
        self.new_username_entry.pack(pady=5)

        tk.Label(frame, text="Password:").pack(pady=5)
        self.new_password_entry = tk.Entry(frame, width=40, show="*")
        self.new_password_entry.pack(pady=5)
        
        self.show_password = False
        self.toggle_password_button = tk.Button(
            frame,
            text="Show Password",
            command=self.toggle_password_visibility
        )
        self.toggle_password_button.pack(pady=5)

        tk.Label(frame, text="OpenAI API Key:").pack(pady=5)
        self.new_api_entry = tk.Entry(frame, width=40, show="*")
        self.new_api_entry.pack(pady=5)
        
        # Toggle API key visibility
        self.show_api_key = False
        self.toggle_api_key_button = tk.Button(
            frame,
            text="Show API Key",
            command=self.toggle_api_key_visibility
        )
        self.toggle_api_key_button.pack(pady=5)

        tk.Button(frame, text="Save Account", command=self.save_new_account).pack(pady=15)
        tk.Button(frame, text="Back", command=self.show_login_selection_frame).pack(pady=5)

    def save_new_account(self):
        domain = self.new_domain_entry.get().strip()
        username = self.new_username_entry.get().strip()
        password = self.new_password_entry.get().strip()
        api_key = self.new_api_entry.get().strip()
        if not all([domain, username, password, api_key]):
            messagebox.showerror("Error", "All fields are required!")
            return

        # try to login
        result, message = log_into_wordpress(domain, username, password)
        try:
            client = OpenAI(api_key=api_key)
            client.models.list()
            self.client = client
            if result:
                encrypted_password = encrypt_password(password)
                encrypted_api_key = encrypt_password(api_key)  
                account_id = save_account_to_db(domain, username, encrypted_password, encrypted_api_key)
                self.auth = HTTPBasicAuth(username, password)
                self.current_account = (account_id, domain, username, password, api_key)
                self.wp_base_url = domain

                messagebox.showinfo("Success", "Saved and logged into account successfully")
                self.show_data_management_frame()
            else:
                messagebox.showerror("Error", f"Failed to log into wordpress: {message}. New account is not saved.")
        except Exception as e:
                messagebox.showerror("Error", f'Failed to log into openai: {message}. New account is not saved. {e}')
    
    def log_into_account(self, domain, username):
        """Logs into WordPress using existing credentials and saves them."""
        account = find_account(domain, username)
        if not account:
            messagebox.showerror("Error", "Account is not found")
            return

        account_id, domain, username, encrypted_password, api_key_encrypted = account
        self.account_id = account_id  

        try:
            plaintext_password = decrypt_password(encrypted_password)  
            api_key = decrypt_password(api_key_encrypted)
        except Exception as e:
            messagebox.showerror("Error", "Failed to decrypt password")
            return

        try:
            result, message = log_into_wordpress(domain, username, plaintext_password)
            self.client = OpenAI(api_key=api_key)
            self.client.models.list()
            if result:
                self.wp_base_url = domain
                self.auth = HTTPBasicAuth(username, plaintext_password)
                self.current_account = (account_id, domain, username, plaintext_password, api_key)

                messagebox.showinfo("Success", "Logged in successfully")
                self.show_data_management_frame()
            else:
                messagebox.showerror("Error", f"Failed to log into wordpress: {message}. Account is not saved.")
        except Exception as e:
                messagebox.showerror("Error", f'Failed to log into openai: {message}. Account is not saved. {e}')

    def show_existing_account_frame(self):
        self.clear_frame()
        frame = tk.Frame(self.root)
        frame.pack(expand=True, fill="both")
        tk.Label(frame, text="Existing Accounts", font=("Arial", 18)).pack(pady=10)
        accounts = get_accounts()
        if not accounts:
            tk.Label(frame, text="No accounts found.").pack(pady=10)
        else:
            for acc in accounts:
                acc_id, domain, username, _, _ = acc
                tk.Button(frame, text=f"{domain} - {username}",
                          command=lambda d=domain, u=username: self.log_into_account(d, u)
                         ).pack(pady=5)
        tk.Button(frame, text="Back", command=self.show_login_selection_frame).pack(pady=15)

    # -------------------------
    # Data Management Frame
    def show_data_management_frame(self):
        self.clear_frame()
        frame = tk.Frame(self.root)
        frame.pack(expand=True, fill="both")
        tk.Label(frame, text="Data Management", font=("Arial", 18)).pack(pady=10)
        
        # Check if there is already a data table for this account.
        account_id = self.current_account[0]
        self.current_record_table = get_record_table_for_account(account_id)
        current_company_info = get_company_info(account_id)
        if current_company_info is None:
            _text = "Create Website Information"
        else:
            _text = "Change Website Information"
        if self.current_record_table is None:
            tk.Button(frame, text="Upload Data", width=20, command=self.show_upload_data_frame).pack(pady=10)
        else:
            tk.Label(frame, text=f"Current Record Table: {self.current_record_table}", font=("Arial", 12)).pack(pady=5)
            tk.Button(frame, text="Change Data", width=20, command=self.show_upload_data_frame).pack(pady=10)
            tk.Button(frame, text="Generate Articles", width=20, command=self.show_generate_articles_frame).pack(pady=10)
            tk.Button(frame, text=_text, width=20, command=self.show_website_info_frame).pack(pady=10)
            tk.Button(frame, text="Add Additional Data", width=20, command=self.show_additional_data_frame).pack(pady=10)
    
        tk.Button(frame, text="Back", command=self.show_login_selection_frame).pack(pady=10)

    # -------------------------
    # additional data
    def show_additional_data_frame(self):
        self.clear_frame()
        frame = tk.Frame(self.root)
        frame.pack(expand=True, fill="both")

        tk.Label(frame, text="Add Additional Data", font=("Arial", 16)).pack(pady=10)

        account_id = self.current_account[0]
        existing_table = get_additional_data_table_for_account(account_id)
        
        if existing_table is None:
            tk.Label(frame, text="Table Name:").pack(pady=5)
            self.add_data_table_entry = tk.Entry(frame, width=40)
            self.add_data_table_entry.pack(pady=5)
        else:
            base = existing_table[:-len("_add_data")] if existing_table.endswith("_add_data") else existing_table
            tk.Label(frame, text=f"Using table: {base}", font=("Arial", 12)).pack(pady=5)

        tk.Label(frame, text="Links (one per row):").pack(pady=5)
        self.links_text = tk.Text(frame, height=10, width=80)
        self.links_text.pack(pady=5)

        tk.Button(frame, text="Process", command=self.process_additional_data).pack(pady=10)
        tk.Button(frame, text="Back", command=self.show_data_management_frame).pack(pady=5)

    def process_additional_data(self):
        account_id = self.current_account[0]
        existing = get_additional_data_table_for_account(account_id)

        if existing is None:
            base = self.add_data_table_entry.get().strip()
            if not base:
                messagebox.showerror("Error", "Please enter a table name.")
                return
            # append suffix here
            table_name = f"{base}_add_data"
            create_additional_data_table(table_name)
            update_additional_data_table_for_account(account_id, table_name)
        else:
            table_name = existing

        raw = self.links_text.get("1.0", tk.END).strip()
        links = [line for line in raw.splitlines() if line.strip()]
        if not links:
            messagebox.showerror("Error", "Please enter at least one link.")
            return

        progress = ttk.Progressbar(self.root, length=400, mode='determinate',
                                maximum=len(links))
        progress.pack(pady=10)
        self.root.update_idletasks()

        for idx, link in enumerate(links, 1):
            try:
                summary = generate_article_summary(link, self.client)
                insert_summary_into_table(table_name, link, summary)
            except Exception as e:
                print(f"Error on link {link}: {e}")
            progress['value'] = idx
            self.root.update_idletasks()

        progress.destroy()
        messagebox.showinfo("Done", f"Processed {len(links)} links into table '{table_name}'.")
        self.show_data_management_frame()

    # -------------------------
    # Website Information
    def show_website_info_frame(self):
        self.clear_frame()
        frame = tk.Frame(self.root)
        frame.pack(expand=True, fill="both")
        
        tk.Label(frame, text="Website Information", font=("Arial", 16)).pack(pady=10)
        
        # Field for links (e.g., links from the About Us page)
        tk.Label(frame, text="Paste links on about us page for your website:").pack(pady=5)
        self.website_links_entry = tk.Entry(frame, width=80)
        self.website_links_entry.pack(pady=5)
        
        # Text area for additional company information.
        tk.Label(frame, text="Type additional information about your company:").pack(pady=5)
        self.additional_info_text = tk.Text(frame, height=10, width=80)
        self.additional_info_text.pack(pady=5)
        
        # Save and Back buttons.
        tk.Button(frame, text="Save Website Info", command=self.save_website_info).pack(pady=10)
        tk.Button(frame, text="Back", command=self.show_data_management_frame).pack(pady=5)

    def save_website_info(self):
        links = self.website_links_entry.get().strip()
        additional_info = self.additional_info_text.get("1.0", tk.END).strip()
        
        if not links:
            messagebox.showerror("Error", "Please fill in links.")
            return
        
        try:
            # Generate the final HTML info using OpenAI logic.
            generated_info = generate_html_info(links, additional_info, self.client)
            
            # Update the database with the generated company info.
            account_id = self.current_account[0]
            update_company_info(account_id, generated_info)
            
            messagebox.showinfo("Success", "Website information saved successfully!")
            self.show_data_management_frame()
        except Exception as e:
            messagebox.showerror("Error", f"Error generating website info: {e}")

    # -------------------------
    # Upload Data Frame
    def show_upload_data_frame(self):
        self.clear_frame()
        frame = tk.Frame(self.root)
        frame.pack(expand=True, fill="both")
        tk.Label(frame, text="Upload Data (Excel)", font=("Arial", 16)).pack(pady=10)
        tk.Button(frame, text="Select Excel File", command=self.upload_excel_file).pack(pady=5)
        self.file_path_label = tk.Label(frame, text="No file selected")
        self.file_path_label.pack(pady=5)
        tk.Label(frame, text="Enter Table Name:").pack(pady=5)
        self.table_name_entry = tk.Entry(frame, width=40)
        self.table_name_entry.pack(pady=5)
        tk.Button(frame, text="Save Data", command=self.save_data_table).pack(pady=10)
        tk.Button(frame, text="Back", command=self.show_data_management_frame).pack(pady=5)

    def upload_excel_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls")])
        if file_path:
            self.file_path_label.config(text=file_path)
            try:
                df = pd.read_excel(file_path)
                # Check for required columns
                required_columns = ["record_id", "Title", "Content", "Job Location", "Elementor"]
                for col in required_columns:
                    if col not in df.columns:
                        raise KeyError(f"Missing column: {col}")
                self.data_df = df
                messagebox.showinfo("Info", "File loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Error reading file: {e}")

    def save_data_table(self):
        table_name = self.table_name_entry.get().strip()
        if not table_name:
            messagebox.showerror("Error", "Please provide a table name")
            return
        if self.data_df is None:
            messagebox.showerror("Error", "No data file uploaded!")
            return
        # Create new table and insert data
        try:
            create_data_table(table_name)
            insert_data_into_table(table_name, self.data_df)
            # Link the table to the current account in all_accounts_records
            account_id = self.current_account[0]
            update_record_table_for_account(account_id, table_name)
            self.current_record_table = table_name
            messagebox.showinfo("Success", "Data saved successfully!")
            self.show_data_management_frame()
        except Exception as e:
            messagebox.showerror("Error", f"Error saving data: {e}")

    # -------------------------
    # Article Generation Frame
    def show_generate_articles_frame(self):
        self.clear_frame()
        frame = tk.Frame(self.root)
        frame.pack(expand=True, fill="both")
        tk.Label(frame, text="Article Generation", font=("Arial", 18)).pack(pady=10)
        # Text area to show progress.
        self.progress_text = tk.Text(frame, height=20, wrap="word")
        self.progress_text.pack(expand=True, fill="both", padx=10, pady=10)
        # Start and Stop buttons.
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Start Generation", command=self.start_generation).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Stop Generation", command=self.stop_generation).pack(side="left", padx=5)
        tk.Button(frame, text="Back", command=self.show_data_management_frame).pack(pady=5)

    def start_generation(self):
        if self.current_record_table is None:
            messagebox.showerror("Error", "No data table available!")
            return
        self.generating = True
        self.progress_text.insert(tk.END, "Starting article generation...\n")
        self.root.update()
        current_year = datetime.now().year
        print(self.current_record_table)

        # Process records one by one.
        while self.generating:
            post_url = 'None'
            record = get_next_record(self.current_record_table)
            if record is None:
                self.progress_text.insert(tk.END, "No more records to process.\n")
                break
            print(record)
            record_id, title, content, job_location, elementor = record
            self.progress_text.insert(tk.END, f"\nProcessing Record ID: {record_id}\n")
            print(record_id)
            
            # Check if the page exists before generating any content.
            get_response = requests.get(f"{self.wp_base_url}/wp-json/wp/v2/job-listings/{record_id}", auth=self.auth)
            if get_response.status_code != 200:
                # messagebox.showwarning("Page Not Found", f"Page for record {record_id} doesn't exist. Skipping this record.")
                self.progress_text.insert(tk.END, f"Page for record {record_id} doesn't exist. Skipped.\n")
                mark_record_as_used(self.current_record_table, record_id)
                self.root.update()
                print('no exist')
                time.sleep(2)
                continue
            post_url = get_response.json().get("link", "none")
            url_slug = post_url.strip('/').split('/')[-1]
            
            # Combine the content fields to form topic and context.
            topic = title
            location = job_location
            print(topic, location)
            # Generate SEO metadata.
            try:
                meta_data = {"year": current_year, "url_slug": url_slug, "topic": topic, "content": content, "location": location}
                seo_metadata = generate_seo_metadata(meta_data, self.client)
                self.progress_text.insert(tk.END, "SEO metadata generated.\n")
            except Exception as e:
                self.progress_text.insert(tk.END, f"Error generating SEO metadata: {e}\n")
                continue

            # Generate article content.
            try:
                text_data = {"topic": topic, "content": content, "location": location, "seo_metadata": seo_metadata}
                article_data = generate_article(text_data, self.client)
                
                text_data["article_data"] = article_data
                tags_list = generate_tags(text_data, self.client)
                tag_ids = [self.get_or_create_tag(tag) for tag in tags_list]

                
                self.progress_text.insert(tk.END, "Article text and tags generated.\n")
            except Exception as e:
                self.progress_text.insert(tk.END, f"Error generating article: {e}\n")
                continue

            try:
                if elementor:
                    article_data = insert_elementor_randomly(article_data, elementor.strip())
                    self.progress_text.insert(tk.END, f"Elementors inserted\n")
                else:
                    self.progress_text.insert(tk.END, f"No elementors to insert\n")
            except Exception as e:
                self.progress_text.insert(tk.END, f"Error inserting elementors: {e}\n")
                continue

            # Generate images (2 images, then duplicate each to make 4 images).
            try:
                images = generate_image_prompts_and_images(topic, seo_metadata, article_data, self.client)
                self.generated_images = images
                if images and len(images) >= 2:
                    uploaded_images = self.upload_images_to_wordpress(images)
                    image_tags = []
                    for image in uploaded_images:
                        image_tag = f"<img src='{image['url']}' alt='{image['alt_text']}' title='{image['title']}' />"
                        image_tags.append(image_tag)
                    if not image_tags:
                        messagebox.showerror("Error", "Images were not uploaded")
                        return
                    
                    # Duplicate each image to create a list of 4 images.
                    image_tags = image_tags[:2] + image_tags[:2]
                    self.progress_text.insert(tk.END, "Images generated.\n")
                else:
                    image_tags = []
                    self.progress_text.insert(tk.END, "No images generated.\n")
            except Exception as e:
                self.progress_text.insert(tk.END, f"Error generating images: {e}\n")
                image_tags = []
            
            # Evenly insert images in the article text.
            final_article = insert_images_evenly(article_data, image_tags)
            print(final_article)

            # Simulate posting the article.
            self.progress_text.insert(tk.END, "Posting article...\n")
            print("posting")
            try:
                post_link = self.post_article_to_wordpress(final_article, seo_metadata, topic, tag_ids, uploaded_images, record_id)
                print(post_link)
                self.progress_text.insert(tk.END, f"Article posted for record {record_id}: {post_link}\n")
            except Exception as e:
                self.progress_text.insert(tk.END, f"Error posting article for record {record_id}: {e}\n")
            # Mark record as used.
            mark_record_as_used(self.current_record_table, record_id)
            delay = random.uniform(3*60, 8*60)
            self.progress_text.insert(tk.END, f"Delay for {delay} seconds\n")
            self.root.update()
            time.sleep(delay)  # simulate delay

        self.progress_text.insert(tk.END, "Generation stopped.\n")

    def stop_generation(self):
        self.generating = False
        self.progress_text.insert(tk.END, "Stop signal received. Halting generation...\n")
    
    def upload_images_to_wordpress(self, images):
        """Upload images to WordPress and return their URLs."""
        image_urls = []
        for image_data in images:
            try:
                with open(image_data["local_path"], "rb") as image_file:
                    filename = os.path.basename(image_data["local_path"])
                    filename = filename.encode('utf-8').decode('latin-1')  # Handle non-ASCII characters
                    resize_and_compress_local_image(filename, filename)
                    headers = {"Content-Disposition": f"attachment; filename={filename}"}
                    response = requests.post(f"{self.wp_base_url}/wp-json/wp/v2/media", headers=headers, files={"file": image_file}, auth=self.auth)
                if response.status_code == 201:
                    image_urls.append({"url": response.json()["source_url"], "alt_text": image_data["alt_text"], "title": image_data["title"]})
            except Exception as e:
                print(f"Error uploading images: {e}")
        return image_urls
    
    def get_or_create_tag(self, tag_name):
        # Check if the tag already exists
        response = requests.get(f"{self.wp_base_url}/wp-json/wp/v2/job_listing_tag", params={"search": tag_name}, auth=self.auth)

        if response.status_code == 200 and response.json():
            # Tag exists, return its ID
            # return response.json()[0]["id"]
            # Tag exists — grab its ID...
            term_id = response.json()[0]["id"]

            # ...and re–write its Rank Math meta
            update_payload = {
                "description": tag_name,
                "meta": {
                    "rank_math_focus_keyword": tag_name
                }
            }
            update_resp = requests.put(
                f"{self.wp_base_url}/wp-json/wp/v2/job_listing_tag/{term_id}",
                json=update_payload,
                auth=self.auth
            )
            update_resp.raise_for_status()
            return term_id
        
        # If the tag does not exist, create it with Rank Math meta data included
        create_data = {
            "name": tag_name,
            "description": tag_name,
            "meta": {
                "rank_math_focus_keyword": tag_name,
            }
        }
        
        # Tag doesn't exist, create it
        response = requests.post(
            f"{self.wp_base_url}/wp-json/wp/v2/job_listing_tag",
            json=create_data,
            auth=self.auth
        )
        
        if response.status_code == 201:
            # Tag created, return its ID
            return response.json()["id"]
        
        # If something went wrong
        raise Exception(f"Failed to get or create tag: {tag_name}")
    
    def post_article_to_wordpress(self, article_html, seo_metadata, topic, tag_ids, uploaded_images, record_id):
        post_url = 'none'
        try:
            # Retrieve existing listing data by record_id.
            get_response = requests.get(f"{self.wp_base_url}/wp-json/wp/v2/job-listings/{record_id}", auth=self.auth)
            print(get_response)
            if get_response.status_code != 200:
                messagebox.showerror("Error", f"Failed to retrieve listing with record id {record_id}: {get_response.text}")
                return post_url
            existing_listing = get_response.json()
            # Append new article HTML to the existing listing content.
            existing_content = existing_listing.get("content", {}).get("rendered", "")
            
            # Retrieve company info and append it to the article if available.
            company_info = get_company_info(self.current_account[0])
            if company_info:
                article_html += f"<hr>{company_info}"
            
            new_content = existing_content + "\n\n" + article_html
            final_text = self.append_additional_data(new_content)

            adjusted_keywords, plain_text = self.adjust_keyword_density(final_text, seo_metadata["Focus Keyword"])

            post_data = {
                "title": topic,
                "content": final_text,
                "status": "publish",
                # "slug": seo_metadata["URL Slug"],
                "tags": tag_ids,
                "job_listing_tag": tag_ids,
                "meta": {
                    "rank_math_title": seo_metadata["SEO Title"],
                    "rank_math_description": seo_metadata["Meta Description"],
                    # "rank_math_focus_keyword": seo_metadata["Focus Keyword"]
                    "rank_math_focus_keyword": adjusted_keywords
                }
            }
            # Update the existing listing.
            update_response = requests.put(f"{self.wp_base_url}/wp-json/wp/v2/job-listings/{record_id}", 
                                            json=post_data, auth=self.auth)
            print(update_response)
            if update_response.status_code == 200:
                post_url = update_response.json().get("link", "none")
                # Update featured image for the listing.
                first_image = uploaded_images[0]
                featured_image_id = self.get_image_id(first_image["url"])
                if featured_image_id:
                    update_img_data = {"featured_media": featured_image_id}
                    featured_response = requests.post(
                        f"{self.wp_base_url}/wp-json/wp/v2/job-listings/{record_id}",
                        json=update_img_data,
                        auth=self.auth
                    )
                    if featured_response.status_code == 200:
                        print("Featured image updated successfully")
                    else:
                        print(f"Failed to update featured image: {featured_response.text}")
                else:
                    print("Failed to get featured image ID")
                # Delete local copies of generated images.
                for image in self.generated_images:
                    local_path = image.get("local_path", "")
                    if os.path.exists(local_path):
                        try:
                            os.remove(local_path)
                            print(f"Deleted image locally: {local_path}")
                        except Exception as e:
                            print(f"Failed to delete image {local_path}: {e}")
            else:
                messagebox.showerror("Error", f"Failed to update listing: {update_response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update listing: {e}")

        return post_url
    
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
                print(f"Failed to get media api, code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"Error getting image id: {e}")

        print(f"Failed to get image id: {image_url}")
        return None

    def adjust_keyword_density(self, article_html, focus_keywords):
        """
        Adjusts keyword density for the given article HTML and focus keywords.
        :param article_html: The HTML content of the article.
        :param focus_keywords: The string of focus keywords separated by commas.
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
    
    def append_additional_data(self, article_text):
        """
        Keep appending random, non‑duplicate summaries from the 
        account's additional_data_table until we hit ≥2550 words
        or run out of unique summaries.
        """
        table = get_additional_data_table_for_account(self.current_account[0])
        if not table:
            return article_text

        summaries = get_all_summaries_from_table(table)
        random.shuffle(summaries)

        # simple word‑count via regex
        def word_count(txt):
            return len(re.findall(r'\w+', txt))

        count = word_count(article_text)
        result = article_text
        used = set()

        for summary in summaries:
            if count >= 5000:
                break
            if summary in used:
                continue
            result += "\n\n" + "<hr>" + summary
            used.add(summary)
            count = word_count(result)

        return result

# -------------------------
# Main Routine
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
