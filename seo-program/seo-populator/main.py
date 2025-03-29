import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from openai import OpenAI
from deep_translator import GoogleTranslator
from cryptography.fernet import Fernet

def translate_text(text, target_language):
    """Translate text to the specified target language."""
    try:
        return GoogleTranslator(source="auto", target=target_language).translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Fallback to original text if translation fails

# Database Configuration
DB_FILE = "projects.db"

# Initialize SQLite database
if not os.path.exists(DB_FILE):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                folder_path TEXT NOT NULL,
                html_path TEXT,
                db_path TEXT,
                company_name TEXT,
                api_key TEXT
            )
        """)
        conn.commit()

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Project Data Manager")
        self.geometry("800x600")
        self.resizable(False, False)
        self.project_name = ""
        self.project_id = None
        self.language = "en"  # Default language
        self.company_name = ""
        self.center_window()
        self.show_language_selection()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"800x600+{x}+{y}")

    def show_language_selection(self):
        """Display language selection screen."""
        self.clear_frame()
        lang_frame = tk.Frame(self)
        lang_frame.pack(expand=True)

        tk.Label(lang_frame, text="Select Language / Dil Seçimi", font=("Arial", 16)).pack(pady=20)
        tk.Label(lang_frame, text="The summaries and info will be generated in the selected language", font=("Arial", 12)).pack(pady=20)
        tk.Button(lang_frame, text="English", command=lambda: self.set_language("en"), width=20, height=2).pack(pady=10)
        tk.Button(lang_frame, text="Türkçe", command=lambda: self.set_language("tr"), width=20, height=2).pack(pady=10)

    def set_language(self, lang_code):
        """Set the application language and use Google Translate for UI text."""
        self.language = lang_code
        self.translations = self.load_translations(lang_code)
        self.show_main_page()

    def load_translations(self, lang_code):
        """Translate default English text into the selected language."""
        base_texts = {
            "welcome": "Welcome to DB and HTML Creator",
            "create_new_project": "Create New Project",
            "populate_existing_project": "Populate Existing Project",
            "no_existing_projects": "No existing projects.",
            "enter_project_name": "Enter Project Name:",
            "save_project_name": "Save Project Name",
            "back": "Back",
            "generate_html": "Generate HTML",
            "generate_summaries": "Generate Article Summaries",
            "select_project": "Select a Project:",
            "success": "Success",
            "error": "Error",
            "project_saved": "Project saved successfully.",
            "project_exists": "Project name already exists.",
            "project_name_empty": "Project name cannot be empty!",
            "company_name": "Enter Company Name:",
            "useful_links": "Enter Useful Links (comma-separated):",
            "html_exists": "HTML already exists. Regenerate?",
            "html_generated": "HTML generated successfully.",
            "provide_links": "Please provide valid article links.",
            "provide_product_links": "Please provide valid product links.",
            "generated_articles": "Generated {count} articles, {duplicates} duplicates found.",
            "generated_products": "Generated {count} product descriptions, {duplicates} duplicates found.",
            "project": "Project",
            "both_fields_required": "Both fields are required.",
            "file_exists": "File Exists",
            "failed_generate_HTML": "Failed to generate HTML:",
            "enter_article_links": "Enter Article Links (one per line):",
            "failed_summarize": "Failed to summarize",
            "generate_product_summaries": "Generate Product summaries",
            "enter_product_links": "Enter Product Links (one per line):",
            "processing": "Processing",
            "wait_a_minute": "This might take a minute. Please wait.",
            "wait_a_few_minutes": "This might take a few minutes. Please wait. 1 minute per 5 links",
            "help": "Help",
            "manual": "SEO Addition Tool - Instructions Manual",
            "enter_openai_key": "Enter OpenAI API Key:",
            "openai_key_empty": "OpenAI API Key cannot be empty!",
            "incorrect_openai_key": "Incorrect OpenAI API Key!",
            "openai_error": "API Key validation error:",
            "generating_html": "Generating HTML...",
            "generating_articles": "Generating Articles...",
            "generating_pd": "Generating Product Descriptions...",
        }

        turk_text = {
            "welcome": "DB ve HTML Oluşturucuya Hoş Geldiniz",
            "create_new_project": "Yeni Proje Oluştur",
            "populate_existing_project": "Mevcut Projeyi Doldur",
            "no_existing_projects": "Mevcut proje yok.",
            "enter_project_name": "Proje Adını Girin:",
            "save_project_name": "Proje Adını Kaydet",
            "back": "Geri",
            "generate_html": "HTML Oluştur",
            "generate_summaries": "Makale Özetleri Oluştur",
            "select_project": "Bir Proje Seçin:",
            "success": "Başarılı",
            "error": "Hata",
            "project_saved": "Proje başarıyla kaydedildi.",
            "project_exists": "Proje adı zaten mevcut.",
            "project_name_empty": "Proje adı boş olamaz!",
            "company_name": "Şirket Adını Girin:",
            "useful_links": "Kullanışlı Bağlantıları Girin (virgülle ayrılmış):",
            "html_exists": "HTML zaten mevcut. Yeniden oluştursun mu?",
            "html_generated": "HTML başarıyla oluşturuldu.",
            "provide_links": "Lütfen geçerli makale bağlantıları sağlayın.",
            "provide_product_links": "Lütfen geçerli ürün bağlantıları sağlayın.",
            "generated_articles": "Oluşturulan {count} makale, {duplicates} kopya bulundu.",
            "generated_products": "Oluşturulan {count} ürün açıklamaları, {duplicates} kopya bulundu.",
            "project": "Proje",
            "both_fields_required": "Her iki alan da gereklidir.",
            "file_exists": "Dosya Mevcut",
            "failed_generate_HTML": "HTML oluşturulamadı:",
            "enter_article_links": "Makale Bağlantılarını Girin (her satıra bir tane):",
            "failed_summarize": "Özet oluşturulamadı",
            "generate_product_summaries": "Ürün özetleri oluştur",
            "enter_product_links": "Ürün Bağlantılarını Girin (her satıra bir tane):",
            "processing": "İşleniyor",
            "wait_a_minute": "Bu bir dakika sürebilir. Lütfen bekleyin.",
            "wait_a_few_minutes": "Bu birkaç dakika sürebilir. Lütfen bekleyin. Her 5 bağlantı için 1 dakika.",
            "help": "Yardım",
            "manual": "SEO Ekleme Aracı - Talimatlar Kılavuzu",
            "enter_openai_key": "OpenAI API Anahtarını Girin:",
            "openai_key_empty": "OpenAI API Anahtarı boş olamaz!",
            "incorrect_openai_key": "Yanlış OpenAI API Anahtarı!",
            "openai_error": "API Anahtarı doğrulama hatası:",
            "generating_html": "HTML Üretiliyor...",
            "generating_articles": "Makaleler Üretiliyor...",
            "generating_pd": "Ürün Açıklamaları Üretiliyor...",
        }

        if lang_code == "en":
            return base_texts
        else:
            return turk_text

    def show_main_page(self):
        self.clear_frame()
        main_frame = tk.Frame(self)
        main_frame.pack(expand=True)

        tk.Label(main_frame, text=self.translations["welcome"], font=("Arial", 16)).pack(pady=20)
        tk.Button(main_frame, text=self.translations["help"], command=self.show_help_page, width=30, height=2).pack(pady=10)
        tk.Button(main_frame, text=self.translations["create_new_project"], command=self.show_create_project_page, width=30, height=2).pack(pady=10)
        tk.Button(main_frame, text=self.translations["populate_existing_project"], command=self.show_existing_projects_page, width=30, height=2).pack(pady=10)
        tk.Button(main_frame, text=self.translations["back"], command=self.show_language_selection, width=30, height=2).pack(pady=10)
    
    def show_help_page(self):
        self.clear_frame()
        help_frame = tk.Frame(self)
        help_frame.pack(expand=True, fill="both", padx=20, pady=20)

        title_label = tk.Label(help_frame, text=self.translations["manual"], font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 10))

        instructions = (
            "Welcome!\n"
            "==================================\n"
            "This program is designed as an addition to your SEO program that creates summaries of previous articles "
            "and product descriptions from your website, as well as additional company information. The extra data generated "
            "here is later integrated into your SEO program to extend text length, add essential links, and ultimately boost "
            "your Rank Math SEO score.\n\n"
            "Project Selection:\n"
            "------------------\n"
            "1. Create New Project:\n"
            "   1.1. Enter the project name (preferably the same as your company/website name, e.g., 'facebook').\n"
            "   1.2. 'Enter Open AI Key' - you will need to enter the generated key from your open ai account.\n"
            "   1.3. Click 'Save Project Name'.\n"
            "   1.4. After saving, you will be redirected to the database creation page for the project.\n\n"
            "2. Populate Existing Project:\n"
            "   2.1. Simply select the project you wish to update.\n"
            "   2.2. You will then be redirected to the page to update the project database.\n\n"
            "Database Creation - Selection Page:\n"
            "-------------------------------------\n"
            "1. Generate HTML:\n"
            "   1.1. Enter the company name. This name will appear in the text when referring to your company website, so please be "
            "mindful when specifying it.\n"
            "   1.2. Enter useful links (e.g., main page, about us page) from your website. If adding more than one link, separate them with a comma.\n"
            "   1.3. Click the 'Generate HTML' button.\n"
            "   1.4. The generation of the company information text may take up to a minute. Please wait. Once generated, a message box "
            "will appear and you will be redirected back to the selection page.\n\n"
            "2. Generate Article Summaries:\n"
            "   2.1. This option creates summaries of existing articles on your website. First, provide the links to the articles.\n"
            "   2.2. Enter one article link per line in the provided text box.\n"
            "   2.3. These links can be found in your sitemap, extracted using tools like Screaming Frog, and copied manually.\n"
            "   2.4. It is recommended to add at least 10 links—the more, the better.\n"
            "   2.5. Duplicate links will not be processed.\n"
            "   2.6. Each link may take between 10-40 seconds to process. For example, 10 links might take between 2-7 minutes. Please be patient.\n"
            "   2.7. Once processing is complete, you will see how many summaries were created and how many duplicates were found.\n"
            "   2.8. A message box will confirm generation and redirect you back to the selection page.\n\n"
            "3. Generate Product Summaries:\n"
            "   3.1. This option creates summaries of existing products on your website. First, provide the links to the products.\n"
            "   3.2. Enter one product link per line in the provided text box.\n"
            "   3.3. These links can be found in your sitemap, extracted using tools like Screaming Frog, and copied manually.\n"
            "   3.4. It is recommended to add at least 10 links—the more, the better.\n"
            "   3.5. Duplicate links will not be processed.\n"
            "   3.6. Each link may take between 10-40 seconds to process. For example, 10 links might take between 2-7 minutes. Please be patient.\n"
            "   3.7. Once processing is complete, you will see how many summaries were created and how many duplicates were found.\n"
            "   3.8. A message box will confirm generation and redirect you back to the selection page.\n\n"
            "Additional Notes:\n"
            "-----------------\n"
            "• Please make sure to generate the HTML as this is essential for your SEO information.\n"
            "• If you only need to create summaries for articles or product descriptions, you can skip the option you don't require.\n"
            "• Once you have created everything you need, simply exit the program. You will find a folder named after your project name "
            "in the same directory as this program.\n"
        )

        # Translate the instructions if the selected language is not English.
        if self.language != "en":
            instructions = translate_text(instructions, self.language)

        # Create a read-only Text widget to display the instructions with a scrollbar
        text_frame = tk.Frame(help_frame)
        text_frame.pack(expand=True, fill="both")
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        text_widget = tk.Text(text_frame, wrap="word", font=("Arial", 12), yscrollcommand=scrollbar.set, bg="#f9f9f9")
        text_widget.insert("1.0", instructions)
        text_widget.config(state="disabled")  # make read-only
        text_widget.pack(expand=True, fill="both")
        
        scrollbar.config(command=text_widget.yview)

        tk.Button(help_frame, text=self.translations["back"], command=self.show_main_page, font=("Arial", 12, "bold")).pack(pady=10)

    def show_create_project_page(self):
        self.clear_frame()
        create_frame = tk.Frame(self)
        create_frame.pack(expand=True)

        tk.Label(create_frame, text=self.translations["enter_project_name"]).pack(pady=5)
        project_name_entry = tk.Entry(create_frame, width=50)
        project_name_entry.pack(pady=5)

        tk.Label(create_frame, text=self.translations["enter_openai_key"]).pack(pady=5)
        api_key_entry = tk.Entry(create_frame, width=50)
        api_key_entry.pack(pady=5)

        def save_project():
            self.project_name = project_name_entry.get().strip()
            api_key = api_key_entry.get().strip()

            if not self.project_name:
                messagebox.showerror(self.translations["error"], self.translations["project_name_empty"])
                return

            if not api_key:
                messagebox.showerror(self.translations["error"], self.translations["openai_key_empty"])
                return

            # Validate the API key
            if not self.validate_api_key(api_key):
                messagebox.showerror(self.translations["error"], self.translations["incorrect_openai_key"])
                return

            # Encrypt the API key
            encrypted_api_key = self.encrypt_api_key(api_key)

            folder_path = os.path.abspath(self.project_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO projects (name, folder_path, api_key) VALUES (?, ?, ?)", (self.project_name, folder_path, encrypted_api_key))
                    conn.commit()
                    messagebox.showinfo(self.translations["success"], self.translations["project_saved"])
                    self.project_id = cursor.lastrowid
                    self.show_project_options_page()
                except sqlite3.IntegrityError:
                    messagebox.showerror(self.translations["error"], self.translations["project_exists"])

        tk.Button(create_frame, text=self.translations["save_project_name"], command=save_project, width=30, height=2).pack(pady=10)
        tk.Button(create_frame, text=self.translations["back"], command=self.show_main_page, width=30, height=2).pack(pady=10)

    def validate_api_key(self, api_key):
        try:
            self.client = OpenAI(api_key=api_key)
            self.client.models.list()
            return True
        except Exception as e:
            print(f"{self.translations['openai_error']} {e}")
            return False

    def encrypt_api_key(self, api_key):
        key = b'JQu0uhAlauqJA1XDGtniaPlqCLECIGBVAPm6VhYltPc='
        cipher_suite = Fernet(key)
        encrypted_api_key = cipher_suite.encrypt(api_key.encode())
        return encrypted_api_key

    def decrypt_api_key(self, encrypted_api_key):
        key = b'JQu0uhAlauqJA1XDGtniaPlqCLECIGBVAPm6VhYltPc='
        cipher_suite = Fernet(key)
        decrypted_api_key = cipher_suite.decrypt(encrypted_api_key).decode()
        return decrypted_api_key

    def show_project_options_page(self):
        self.clear_frame()
        options_frame = tk.Frame(self)
        options_frame.pack(expand=True)

        tk.Label(options_frame, text=f"{self.translations['project']}: {self.project_name}", font=("Arial", 14)).pack(pady=10)
        tk.Button(options_frame, text=self.translations["generate_html"], command=self.generate_html, width=30, height=2).pack(pady=10)
        tk.Button(options_frame, text=self.translations["generate_summaries"], command=lambda: self.show_summary_page("article"), width=30, height=2).pack(pady=10)
        tk.Button(options_frame, text=self.translations["generate_product_summaries"], command=lambda: self.show_summary_page("product"), width=30, height=2).pack(pady=10)
        tk.Button(options_frame, text=self.translations["back"], command=self.show_main_page, width=30, height=2).pack(pady=10)

    def show_existing_projects_page(self):
        self.clear_frame()
        existing_frame = tk.Frame(self)
        existing_frame.pack(expand=True)

        tk.Label(existing_frame, text=self.translations["select_project"], font=("Arial", 14)).pack(pady=10)
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM projects")
            projects = cursor.fetchall()

        if not projects:
            tk.Label(existing_frame, text=self.translations["no_existing_projects"], font=("Arial", 12), fg="red").pack(pady=10)
        else:
            for project_id, project_name in projects:
                tk.Button(existing_frame, text=project_name, command=lambda id=project_id: self.load_project(id), width=30, height=2).pack(pady=5)

        tk.Button(existing_frame, text=self.translations["back"], command=self.show_main_page, width=30, height=2).pack(pady=10)

    def load_project(self, project_id):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, folder_path, company_name, api_key FROM projects WHERE id = ?", (project_id,))
            project = cursor.fetchone()

        if project:
            self.project_id = project_id
            self.project_name = project[0]
            self.company_name = project[2]
            self.api_key = self.decrypt_api_key(project[3])
            self.client = OpenAI(api_key=self.api_key)
            self.show_project_options_page()

    def generate_html(self):
        self.clear_frame()
        html_frame = tk.Frame(self)
        html_frame.pack(expand=True)

        tk.Label(html_frame, text=self.translations["company_name"]).pack(pady=5)
        company_entry = tk.Entry(html_frame, width=50)
        company_entry.pack(pady=5)

        tk.Label(html_frame, text=self.translations["useful_links"]).pack(pady=5)
        links_entry = tk.Entry(html_frame, width=50)
        links_entry.pack(pady=5)

        def generate():            
            company_name = company_entry.get().strip()
            links = links_entry.get().strip()

            if not company_name or not links:
                messagebox.showerror(self.translations["error"], self.translations["both_fields_required"])
                return

            html_path = os.path.join(self.project_name, "company.html")
            txt_path = os.path.join(self.project_name, "company.txt")
            if os.path.exists(html_path):
                if not messagebox.askyesno(self.translations["file_exists"], self.translations["html_exists"]):
                    return

            prompt = f"""Could you please write me a 1000 character long text about this company: {company_name}. Useful links {links}.
            Could you please describe why this company is the best and why customers should choose us, write the advantages of the company.
            Also in the text please include at least 2 links on the company website (can be used from the provided) and 2 links on outside 
            websites (can be websites like wikipedia or any other informational website). Use <a> tags for the links. The expected output is html formatted text, without 
            doctype or any unnecessary tags like divs, just directly start with headings (h2, h3 and h4) and ps. when you will be reffering to
            the company in text please use {company_name} as the company name and include it t least 50 times in the text. It should appear in
            every sentence. One paragraph should be 40-100 words long, use <p> tags for the paragraphs. Please generate text in {self.language} language. 
            Thank you! And please don’t add any text, just give me output right away.
            """
            generation_label = ttk.Label(html_frame, text=self.translations["generating_html"], font=("Arial", 10))
            generation_label.pack(pady=5)

            progress = ttk.Progressbar(html_frame, orient="horizontal", length=400, mode="indeterminate")
            progress.pack(pady=10)
            progress.start()
            try:
                messagebox.showinfo(self.translations["processing"], self.translations["wait_a_minute"])
                
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a content creator."},
                        {"role": "user", "content": prompt}
                    ]
                )
                html_content = response.choices[0].message.content
                cleaned_html_content = html_content.replace("```html", "").replace("```", "").strip()
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(cleaned_html_content)

                with open(txt_path, "w", encoding="utf-8") as txt_file:
                    txt_file.write(company_name)

                with sqlite3.connect(DB_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE projects SET html_path = ?, company_name = ? WHERE id = ?", (html_path, company_name, self.project_id))
                    conn.commit()

                self.company_name = company_name
                progress.stop()
                progress.destroy()
                generation_label.destroy()
                messagebox.showinfo(self.translations["success"], self.translations["html_generated"])
                self.show_project_options_page()
            except Exception as e:
                progress.stop()
                progress.destroy()
                generation_label.destroy()
                messagebox.showerror(self.translations["error"], f"{self.translations['failed_generate_HTML']} {str(e)}")

        tk.Button(html_frame, text=self.translations["generate_html"], command=generate, width=30, height=2).pack(pady=10)
        tk.Button(html_frame, text=self.translations["back"], command=self.show_project_options_page, width=30, height=2).pack(pady=10)

    def show_summary_page(self, summary_type):
        """Show the summary generation page for articles or products."""
        self.clear_frame()
        summary_frame = tk.Frame(self)
        summary_frame.pack(expand=True)

        label_text = self.translations["enter_article_links"] if summary_type == "article" else self.translations["enter_product_links"]
        tk.Label(summary_frame, text=label_text).pack(pady=5)
        links_text = tk.Text(summary_frame, width=80, height=20)
        links_text.pack(pady=5)

        def generate():
            links = links_text.get("1.0", "end").strip().split("\n")
            links = [link.rstrip("/") for link in links if link.strip()]

            if not links:
                messagebox.showerror(self.translations["error"], self.translations["provide_links"])
                return

            db_path = os.path.join(self.project_name, f"{summary_type}_summaries.db")
            table_name = f"{summary_type}_summaries"

            # Initialize the database file if it doesn't exist
            if not os.path.exists(db_path):
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"""
                        CREATE TABLE IF NOT EXISTS {table_name} (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            link TEXT UNIQUE NOT NULL,
                            summary TEXT NOT NULL
                        )
                    """)
                    conn.commit()
            if summary_type == "article":
                generation_label = ttk.Label(summary_frame, text=self.translations["generating_articles"], font=("Arial", 10))
                generation_label.pack(pady=5)
            else:
                generation_label = ttk.Label(summary_frame, text=self.translations["generating_pd"], font=("Arial", 10))
                generation_label.pack(pady=5)

            progress = ttk.Progressbar(summary_frame, orient="horizontal", length=400, mode="determinate")
            progress.pack(pady=10)
            progress["maximum"] = len(links)

            summaries = []
            duplicate_count = 0

            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                messagebox.showinfo(self.translations["processing"], self.translations["wait_a_few_minutes"])
                for i, link in enumerate(links):
                    # Check for duplicates in the database
                    cursor.execute(f"SELECT 1 FROM {table_name} WHERE link = ?", (link,))
                    if cursor.fetchone():
                        duplicate_count += 1
                        continue

                    prompt = f"""Could you please write me a summary of this {'article' if summary_type == 'article' else 'product'} {link}. The word count should be 200-300 words.
                    At the end add the link on the {'article' if summary_type == 'article' else 'product'} with text "Read More on {self.company_name} {'Blog' if summary_type == 'article' else 'Products Page'}..". This phrase should be translated
                    if the {'articles' if summary_type == 'article' else 'products'} are in different languages. The expected output is html formatted text, without doctype or any unnecessary tags 
                    like divs, just directly start with heading h3 with the {'article' if summary_type == 'article' else 'product'} name and ps. One paragraph should be 40-100 words long, use <p> tags for the paragraphs. The summary has to be in {self.language} language.
                    Thank you! And please don’t add any text, just give me output right away.
                    """

                    try:
                        response = self.client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": f"You are a SEO Specialist and a copywriter and an expert in summarizing {'articles' if summary_type == 'article' else 'product descriptions'}."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        summary_content = response.choices[0].message.content
                        cleaned_summary_content = summary_content.replace("```html", "").replace("```", "").strip()
                        summaries.append((link, cleaned_summary_content))
                        cursor.execute(f"INSERT INTO {table_name} (link, summary) VALUES (?, ?)", (link, summary_content))
                    except Exception as e:
                        messagebox.showerror(self.translations["error"], f"{self.translations['failed_summarize']} {link}: {str(e)}")

                    progress["value"] = i + 1
                    self.update_idletasks()

                conn.commit()

            generated_message = self.translations["generated_articles"].format(count=len(summaries), duplicates=duplicate_count) if summary_type == "article" else self.translations["generated_products"].format(count=len(summaries), duplicates=duplicate_count)
            messagebox.showinfo(self.translations["success"], generated_message)
            generation_label.destroy()
            self.show_project_options_page()

        tk.Button(summary_frame, text=self.translations["generate_summaries"] if summary_type == "article" else self.translations["generate_product_summaries"], command=generate, width=30, height=2).pack(pady=10)
        tk.Button(summary_frame, text=self.translations["back"], command=self.show_project_options_page, width=30, height=2).pack(pady=10)

    def clear_frame(self):
        for widget in self.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = Application()
    app.mainloop()