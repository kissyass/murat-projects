import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import requests
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager


def test_wordpress_login(domain, username, password):
    '''Test WordPress REST API login with provided credentials.'''
    try:
        url = f"{domain.rstrip('/')}/wp-json/wp/v2/users/me"
        response = requests.get(url, auth=(username, password), timeout=10)
        return response.status_code == 200, response.status_code
    except requests.RequestException as exc:
        return False, str(exc)


def test_links(links):
    '''Test accessibility of provided links using headless Chrome via WebDriverManager.'''
    chrome_options = ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
        for name, link in links.items():
            driver.get(link)
            time.sleep(2)
        return True, None
    except Exception as exc:
        return False, str(exc)
    finally:
        driver.quit()


class AccountDBManager:
    '''Handles SQLite database operations for WordPress accounts, with migrations.'''
    def __init__(self, db_name='accounts.db'):
        self.db_name = db_name
        self._create_table()

    def _create_table(self):
        '''Create or migrate the accounts table.'''
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # Initial creation with full schema
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                page_to_post TEXT NOT NULL,
                etstur_link TEXT NOT NULL,
                trivago_link TEXT NOT NULL,
                tatilbudur_link TEXT NOT NULL,
                otelz_link TEXT NOT NULL,
                otelz_city TEXT NOT NULL,
                otelz_num_adults INTEGER NOT NULL,
                etstur_logo TEXT,
                trivago_logo TEXT,
                tatilbudur_logo TEXT,
                otelz_logo TEXT
            )
            '''
        )
        conn.commit()
        # Migration: add missing columns if upgrading from older schema
        cursor.execute("PRAGMA table_info(accounts)")
        existing_cols = [row[1] for row in cursor.fetchall()]
        if 'page_to_post' not in existing_cols:
            cursor.execute(
                "ALTER TABLE accounts ADD COLUMN page_to_post TEXT NOT NULL DEFAULT ''"
            )
        conn.commit()
        conn.close()

    def add_account(self, account_data):
        '''Insert a new account into the database.'''
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO accounts (domain, username, password, page_to_post, etstur_link, trivago_link, tatilbudur_link, otelz_link, otelz_city, otelz_num_adults, etstur_logo, trivago_logo, tatilbudur_logo, otelz_logo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            [
                account_data['domain'],
                account_data['username'],
                account_data['password'],
                account_data.get('page_to_post', ''),
                account_data['etstur_link'],
                account_data['trivago_link'],
                account_data['tatilbudur_link'],
                account_data['otelz_link'],
                account_data['otelz_city'],
                int(account_data['otelz_num_adults']),
                account_data.get('etstur_logo', ''),
                account_data.get('trivago_logo', ''),
                account_data.get('tatilbudur_logo', ''),
                account_data.get('otelz_logo', ''),
            ]
        )
        conn.commit()
        conn.close()

    def get_accounts(self):
        '''Retrieve all saved accounts from the database.'''
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id, domain, username FROM accounts')
        rows = cursor.fetchall()
        conn.close()
        return rows


class SelectionFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text='Welcome to WP Account Manager', font=('Arial', 16, 'bold')).pack(pady=(20,10))
        tk.Label(self, text='Select an option:', font=('Arial', 14)).pack(pady=5)
        ttk.Button(self, text='Log into Existing Account', command=lambda: controller.show_frame('ExistingAccountFrame')).pack(pady=5)
        ttk.Button(self, text='Log into New Account', command=lambda: controller.show_frame('NewAccountFrame')).pack(pady=5)


class ExistingAccountFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text='Existing Accounts', font=('Arial', 16, 'bold')).pack(pady=(20,10))
        self.content_frame = tk.Frame(self)
        self.content_frame.pack(pady=5)
        ttk.Button(self, text='Back', command=lambda: controller.show_frame('SelectionFrame')).pack(side='bottom', pady=(20,10))

    def populate_accounts(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        accounts = self.controller.db_manager.get_accounts()
        if not accounts:
            tk.Label(self.content_frame, text='No existing data', font=('Arial', 12)).pack(pady=10)
        else:
            for acct_id, domain, username in accounts:
                ttk.Button(self.content_frame, text=f"{domain} - {username}", width=40,
                           command=lambda aid=acct_id: self.login_selected(aid)).pack(pady=3)

    def login_selected(self, acct_id):
        conn = sqlite3.connect(self.controller.db_manager.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT domain, username, password FROM accounts WHERE id=?', (acct_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            success, info = test_wordpress_login(*row)
            if success:
                messagebox.showinfo('Success', 'Logged in successfully to WordPress.')
            else:
                messagebox.showerror('Error', f'Login failed: {info}')
        else:
            messagebox.showerror('Error', 'Invalid account selection.')


class NewAccountFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text='New Account Setup', font=('Arial', 16, 'bold')).grid(row=0, column=0, pady=(20,10))
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        form = tk.Frame(self)
        form.grid(row=1, column=0)
        self.fields, self.logos = {}, {}
        fields = [
            ('domain', 'Website Domain:'), ('username', 'Username:'), ('password', 'Password:'),
            ('page_to_post', 'Page to Post:'), ('etstur_link', 'Etstur Link:'), ('trivago_link', 'Trivago Link:'),
            ('tatilbudur_link', 'Tatilbudur Link:'), ('otelz_link', 'Otelz Link:'), ('otelz_city', 'Otelz City:'),
            ('otelz_num_adults', 'Otelz Num of Adults:')
        ]
        for i, (k, lbl) in enumerate(fields):
            tk.Label(form, text=lbl).grid(row=i, column=0, sticky='e', padx=5, pady=4)
            ent = tk.Entry(form, show='*' if k=='password' else '', width=40)
            ent.grid(row=i, column=1, padx=5, pady=4)
            self.fields[k] = ent
        logos = [('etstur_logo','Etstur Logo:'),('trivago_logo','Trivago Logo:'),
                 ('tatilbudur_logo','Tatilbudur Logo:'),('otelz_logo','Otelz Logo:')]
        offset = len(fields)
        for j, (k, lbl) in enumerate(logos):
            r = offset + j
            tk.Label(form, text=lbl).grid(row=r, column=0, sticky='e', padx=5, pady=4)
            btn = ttk.Button(form, text='Upload', command=lambda key=k: self.upload_logo(key))
            btn.grid(row=r, column=1, sticky='w', padx=5, pady=4)
            pl = tk.Label(form, text='No file selected')
            pl.grid(row=r, column=2, padx=5, pady=4)
            self.logos[k] = pl
        bf = tk.Frame(form)
        bf.grid(row=offset+len(logos)+1, column=0, columnspan=3, pady=(30,10))
        ttk.Button(bf, text='Save and Continue', command=self.save_account).pack(side='left', padx=20)
        ttk.Button(bf, text='Back', command=lambda: controller.show_frame('SelectionFrame')).pack(side='left', padx=20)

    def upload_logo(self, key):
        path = filedialog.askopenfilename(title='Select Logo', filetypes=[('Image files','*.png *.jpg *.jpeg *.gif'),('All files','*.*')])
        if path:
            self.logos[key].config(text=path)

    def save_account(self):
        data = {k: v.get().strip() for k,v in self.fields.items()}
        if any(not x for x in data.values()):
            messagebox.showerror('Error','Please fill all fields')
            return
        for k,lbl in self.logos.items():
            val = lbl.cget('text')
            data[k] = val if val!='No file selected' else ''
        ok,info = test_wordpress_login(data['domain'], data['username'], data['password'])
        if not ok:
            messagebox.showerror('Error',f'WordPress login failed: {info}')
            return
        links = {'Etstur':data['etstur_link'],'Trivago':data['trivago_link'],
                 'Tatilbudur':data['tatilbudur_link'],'Otelz':data['otelz_link']}
        ok,info = test_links(links)
        if not ok:
            messagebox.showerror('Error',f'Link check failed: {info}')
            return
        self.controller.db_manager.add_account(data)
        messagebox.showinfo('Saved','Account saved successfully.')
        self.controller.show_frame('ExistingAccountFrame')


class WordPressAccountManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('WordPress Account Manager')
        w,h=1000,700;sw,sh=self.winfo_screenwidth(),self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.resizable(False,False)
        self.db_manager = AccountDBManager()
        container = tk.Frame(self)
        container.pack(fill='both', expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (SelectionFrame, ExistingAccountFrame, NewAccountFrame):
            f = F(container, self)
            self.frames[F.__name__] = f
            f.grid(row=0, column=0, sticky='nsew')
        self.show_frame('SelectionFrame')

    def show_frame(self, name):
        f = self.frames[name]
        if hasattr(f, 'populate_accounts'):
            f.populate_accounts()
        f.tkraise()


if __name__ == '__main__':
    app = WordPressAccountManagerApp()
    app.mainloop()
