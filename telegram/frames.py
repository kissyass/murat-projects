import tkinter as tk
import asyncio
from telethon import TelegramClient
from database import get_accounts
from database import insert_account
from tkinter import ttk, messagebox, filedialog
import csv
import pandas as pd
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.errors import ChannelPrivateError, FloodWaitError

# ---------------------------
# Members Extraction Page
# ---------------------------
class MembersFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.members_list = []
        self.container = tk.Frame(self, width=600, height=400)
        self.container.place(relx=0.5, rely=0.5, anchor='center')

        self.title_label = tk.Label(self.container, text=self.controller.get_text("title"), font=("Helvetica", 14))
        self.title_label.pack(pady=10)

        self.group_frame = tk.Frame(self.container)
        self.group_frame.pack(pady=5)
        self.group_label = tk.Label(self.group_frame, text=self.controller.get_text("enter_group_name"))
        self.group_label.pack(side=tk.LEFT, padx=5)
        self.group_entry = tk.Entry(self.group_frame, width=50)
        self.group_entry.pack(side=tk.LEFT, padx=5)
        self.fetch_button = tk.Button(self.container, text=self.controller.get_text("fetch_members"),
                                      command=self.on_fetch_click)
        self.fetch_button.pack(pady=5)

        self.table_frame = tk.Frame(self.container)
        self.table_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        columns = ("first_name", "username", "phone")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", height=10)
        self.tree.heading("first_name", text=self.controller.get_text("api_id"), anchor='center')  # placeholder
        self.tree.heading("first_name", text="First Name", anchor='center')
        self.tree.heading("username", text="Username", anchor='center')
        self.tree.heading("phone", text="Phone", anchor='center')
        self.tree.column("first_name", anchor='center', width=120)
        self.tree.column("username", anchor='center', width=120)
        self.tree.column("phone", anchor='center', width=120)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.vsb = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.btn_frame = tk.Frame(self.container)
        self.btn_frame.pack(pady=5)
        self.csv_all_button = tk.Button(self.btn_frame, text=self.controller.get_text('download_csv_all'),
                                        command=lambda: self.download_csv(True))
        self.csv_all_button.pack(side=tk.LEFT, padx=5)
        self.csv_phone_button = tk.Button(self.btn_frame, text=self.controller.get_text('download_csv_phone'),
                                          command=lambda: self.download_csv(False))
        self.csv_phone_button.pack(side=tk.LEFT, padx=5)
        self.excel_all_button = tk.Button(self.btn_frame, text=self.controller.get_text('download_excel_all'),
                                          command=lambda: self.download_excel(True))
        self.excel_all_button.pack(side=tk.LEFT, padx=5)
        self.excel_phone_button = tk.Button(self.btn_frame, text=self.controller.get_text('download_excel_phone'),
                                            command=lambda: self.download_excel(False))
        self.excel_phone_button.pack(side=tk.LEFT, padx=5)

        self.back_button = tk.Button(self.container, text=self.controller.get_text("back"),
                                     command=lambda: controller.show_frame(DashboardFrame))
        self.back_button.pack(pady=2)
        self.logout_button = tk.Button(self.container, text=self.controller.get_text("logout"),
                                       command=self.logout)
        self.logout_button.pack(pady=2)

    def update_language(self):
        self.title_label.config(text=self.controller.get_text("title"))
        self.group_label.config(text=self.controller.get_text("enter_group_name"))
        self.fetch_button.config(text=self.controller.get_text("fetch_members"))
        self.back_button.config(text=self.controller.get_text("back"))
        self.logout_button.config(text=self.controller.get_text("logout"))
        # Note: For CSV/Excel buttons, you can also update if desired

    def logout(self):
        async def safe_disconnect():
            if self.controller.client:
                await self.controller.client.disconnect()
        asyncio.get_event_loop().create_task(safe_disconnect())
        self.controller.client = None
        self.controller.current_account = None
        self.controller.show_frame(MainMenuFrame)

    def on_fetch_click(self):
        group_name = self.group_entry.get().strip()
        if not group_name:
            messagebox.showwarning(self.controller.get_text("input_error"),
                                   self.controller.get_text("fill_all_fields"))
            return
        asyncio.get_event_loop().create_task(self.fetch_and_update(group_name))

    async def fetch_and_update(self, group_name):
        participants = await self.fetch_members(group_name)
        if isinstance(participants, str):
            messagebox.showerror(self.controller.get_text("input_error"), participants)
        else:
            self.members_list = participants
            self.update_table(participants)

    async def fetch_members(self, group_name):
        try:
            chats = []
            last_date = None
            chunk_size = 200
            result = await self.controller.client(GetDialogsRequest(
                offset_date=last_date,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=chunk_size,
                hash=0
            ))
            chats.extend(result.chats)
            gr_name = group_name.strip('@')
            target_group = None
            for chat in chats:
                if hasattr(chat, 'title') and chat.title == gr_name:
                    target_group = chat
                    break
                if hasattr(chat, 'username') and chat.username == gr_name:
                    target_group = chat
                    break
            if target_group is None:
                return f"Group/channel '{group_name}' not found."
            participants = await self.controller.client.get_participants(target_group)
            return participants
        except ChannelPrivateError:
            return "You do not have permission to access this group/channel."
        except FloodWaitError as e:
            return f"Flood wait error: {e}"
        except Exception as e:
            return f"Error: {e}"

    def update_table(self, participants):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for user in participants:
            first_name = user.first_name if user.first_name else ""
            username = user.username if user.username else ""
            phone_number = user.phone if hasattr(user, 'phone') and user.phone else ""
            self.tree.insert("", tk.END, values=(first_name, username, phone_number))

    def download_csv(self, all_members=True):
        if not self.members_list:
            messagebox.showwarning(self.controller.get_text("input_error"),
                                   self.controller.get_text("no_data"))
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["First Name", "Username", "Phone"])
                for user in self.members_list:
                    first_name = user.first_name if user.first_name else ""
                    username = user.username if user.username else ""
                    phone_number = user.phone if hasattr(user, 'phone') and user.phone else ""
                    if all_members:
                        writer.writerow([first_name, username, phone_number])
                    else:
                        if phone_number:
                            writer.writerow([first_name, username, phone_number])
            messagebox.showinfo(self.controller.get_text("title"),
                                self.controller.get_text("success_csv").format(file_path))
        except Exception as e:
            messagebox.showerror(self.controller.get_text("input_error"),
                                 self.controller.get_text("error_csv").format(e))
    
    def download_excel(self, all_members=True):
        if not self.members_list:
            messagebox.showwarning(self.controller.get_text("input_error"),
                                   self.controller.get_text("no_data"))
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                 filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return
        data = []
        for user in self.members_list:
            first_name = user.first_name if user.first_name else ""
            username = user.username if user.username else ""
            phone_number = user.phone if hasattr(user, 'phone') and user.phone else ""
            if all_members:
                data.append({"First Name": first_name, "Username": username, "Phone": phone_number})
            else:
                if phone_number:
                    data.append({"First Name": first_name, "Username": username, "Phone": phone_number})
        try:
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)
            messagebox.showinfo(self.controller.get_text("title"),
                                self.controller.get_text("success_excel").format(file_path))
        except Exception as e:
            messagebox.showerror(self.controller.get_text("input_error"),
                                 self.controller.get_text("error_excel").format(e))

# ---------------------------
# Dashboard (new page)
# ---------------------------
class DashboardFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.container = tk.Frame(self, width=400, height=300)
        self.container.place(relx=0.5, rely=0.5, anchor='center')

        self.title_label = tk.Label(self.container, text=self.controller.get_text("dashboard"), font=("Helvetica", 16))
        self.title_label.pack(pady=20)

        self.fetch_button = tk.Button(self.container, text=self.controller.get_text("fetch_members"),
                                      command=lambda: controller.show_frame(MembersFrame))
        self.fetch_button.pack(pady=5)

        self.logout_button = tk.Button(self.container, text=self.controller.get_text("logout"),
                                       command=self.logout)
        self.logout_button.pack(pady=5)

    def update_language(self):
        self.title_label.config(text=self.controller.get_text("dashboard"))
        self.fetch_button.config(text=self.controller.get_text("fetch_members"))
        self.logout_button.config(text=self.controller.get_text("logout"))

    def logout(self):
        async def safe_disconnect():
            if self.controller.client:
                await self.controller.client.disconnect()
        asyncio.get_event_loop().create_task(safe_disconnect())
        self.controller.client = None
        self.controller.current_account = None
        self.controller.show_frame(MainMenuFrame)

# ---------------------------
# Main Menu Page
# ---------------------------
class MainMenuFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.container = tk.Frame(self, width=400, height=300)
        self.container.place(relx=0.5, rely=0.5, anchor='center')

        self.title_label = tk.Label(self.container, text=self.controller.get_text("saved_accounts"), font=("Helvetica", 14))
        self.title_label.pack(pady=10)

        self.accounts_listbox = tk.Listbox(self.container, width=50, justify='center')
        self.accounts_listbox.pack(pady=5)

        self.login_button = tk.Button(self.container, text=self.controller.get_text("login_with_selected_account"),
                                      command=self.login_selected)
        self.login_button.pack(pady=5)
        self.signup_button = tk.Button(self.container, text=self.controller.get_text("sign_up_new_account"),
                                       command=lambda: controller.show_frame(SignupFrame))
        self.signup_button.pack(pady=5)

    def update_language(self):
        self.title_label.config(text=self.controller.get_text("saved_accounts"))
        self.login_button.config(text=self.controller.get_text("login_with_selected_account"))
        self.signup_button.config(text=self.controller.get_text("sign_up_new_account"))

    def refresh_accounts(self):
        self.accounts_listbox.delete(0, tk.END)
        accounts = get_accounts()
        for acc in accounts:
            phone_only = acc[3]
            self.accounts_listbox.insert(tk.END, phone_only)

    def login_selected(self):
        selection = self.accounts_listbox.curselection()
        if not selection:
            messagebox.showwarning(self.controller.get_text("input_error"),
                                   self.controller.get_text("select_account"))
            return
        index = selection[0]
        accounts = get_accounts()
        account = accounts[index]
        self.controller.current_account = account
        session_name = account[4]
        api_id = account[1]
        api_hash = account[2]
        phone = account[3]
        self.controller.client = TelegramClient(session_name, int(api_id), api_hash)
        asyncio.get_event_loop().create_task(self.start_client_and_proceed(phone))

    async def start_client_and_proceed(self, phone):
        try:
            await self.controller.client.start(phone=phone)
            messagebox.showinfo(self.controller.get_text("title"), self.controller.get_text("login_success"))
            self.controller.show_frame(DashboardFrame)
        except Exception as e:
            messagebox.showerror(self.controller.get_text("login_error"), str(e))

# ---------------------------
# Sign Up / Login Page
# ---------------------------
class SignupFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.code_sent = False
        self.container = tk.Frame(self, width=400, height=400)
        self.container.place(relx=0.5, rely=0.5, anchor='center')

        self.title_label = tk.Label(self.container, text=self.controller.get_text("sign_up_login"), font=("Helvetica", 14))
        self.title_label.pack(pady=10)
        
        self.api_id_label = tk.Label(self.container, text=self.controller.get_text("api_id"))
        self.api_id_label.pack(pady=2)
        self.api_id_entry = tk.Entry(self.container)
        self.api_id_entry.pack(pady=2)

        self.api_hash_label = tk.Label(self.container, text=self.controller.get_text("api_hash"))
        self.api_hash_label.pack(pady=2)
        self.api_hash_entry = tk.Entry(self.container)
        self.api_hash_entry.pack(pady=2)

        self.phone_label = tk.Label(self.container, text=self.controller.get_text("phone_number"))
        self.phone_label.pack(pady=2)
        self.phone_entry = tk.Entry(self.container)
        self.phone_entry.pack(pady=2)

        self.send_code_button = tk.Button(self.container, text=self.controller.get_text("receive_code"),
                                          command=self.receive_code)
        self.send_code_button.pack(pady=5)

        self.enter_code_label = tk.Label(self.container, text=self.controller.get_text("enter_code"))
        self.enter_code_label.pack(pady=2)
        self.code_entry = tk.Entry(self.container)
        self.code_entry.pack(pady=2)

        self.login_button = tk.Button(self.container, text=self.controller.get_text("login_with_selected_account"),
                                      command=self.login_with_code)
        self.login_button.pack(pady=5)

        self.back_button = tk.Button(self.container, text=self.controller.get_text("back"),
                                     command=lambda: controller.show_frame(MainMenuFrame))
        self.back_button.pack(pady=5)

    def update_language(self):
        self.title_label.config(text=self.controller.get_text("sign_up_login"))
        self.api_id_label.config(text=self.controller.get_text("api_id"))
        self.api_hash_label.config(text=self.controller.get_text("api_hash"))
        self.phone_label.config(text=self.controller.get_text("phone_number"))
        self.send_code_button.config(text=self.controller.get_text("receive_code"))
        self.enter_code_label.config(text=self.controller.get_text("enter_code"))
        self.login_button.config(text=self.controller.get_text("login_with_selected_account"))
        self.back_button.config(text=self.controller.get_text("back"))

    def receive_code(self):
        api_id = self.api_id_entry.get().strip()
        api_hash = self.api_hash_entry.get().strip()
        phone = self.phone_entry.get().strip()
        if not api_id or not api_hash or not phone:
            messagebox.showwarning(self.controller.get_text("input_error"),
                                   self.controller.get_text("fill_all_fields"))
            return
        session_name = "session_" + phone
        self.controller.client = TelegramClient(session_name, int(api_id), api_hash)
        asyncio.get_event_loop().create_task(self.send_code(phone))

    async def send_code(self, phone):
        try:
            await self.controller.client.connect()
            if not await self.controller.client.is_user_authorized():
                await self.controller.client.send_code_request(phone)
                self.code_sent = True
                messagebox.showinfo(self.controller.get_text("title"), self.controller.get_text("code_sent"))
            else:
                messagebox.showinfo(self.controller.get_text("title"), self.controller.get_text("already_logged_in"))
        except Exception as e:
            messagebox.showerror(self.controller.get_text("login_error"), str(e))

    def login_with_code(self):
        if not self.code_sent:
            messagebox.showwarning(self.controller.get_text("input_error"),
                                   self.controller.get_text("fill_all_fields"))
            return
        code = self.code_entry.get().strip()
        if not code:
            messagebox.showwarning(self.controller.get_text("input_error"),
                                   self.controller.get_text("fill_all_fields"))
            return
        asyncio.get_event_loop().create_task(self.perform_login(code))

    async def perform_login(self, code):
        try:
            phone = self.phone_entry.get().strip()
            await self.controller.client.sign_in(phone=phone, code=code)
            messagebox.showinfo(self.controller.get_text("title"), self.controller.get_text("login_success"))
            api_id = self.api_id_entry.get().strip()
            api_hash = self.api_hash_entry.get().strip()
            session_name = "session_" + phone
            insert_account(int(api_id), api_hash, phone, session_name)
            self.controller.current_account = (None, int(api_id), api_hash, phone, session_name)
            self.controller.show_frame(DashboardFrame)
        except Exception as e:
            messagebox.showerror(self.controller.get_text("login_error"), str(e))
