import tkinter as tk
from tkinter import ttk
import asyncio
from translations import translations
from database import init_db
from frames import SignupFrame, MainMenuFrame, DashboardFrame, MembersFrame

# ---------------------------
# Tkinter Application Setup
# ---------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.lang = "en"  # default language
        self.title(translations[self.lang]["title"])
        self.geometry("900x500")
        self.center_window(900, 500)
        self.client = None           # Telethon client (set after login)
        self.current_account = None  # Current account tuple from DB

        # Top bar for language selection
        top_bar = tk.Frame(self)
        top_bar.pack(side=tk.TOP, fill=tk.X)
        lang_label = tk.Label(top_bar, text=self.get_text("language"))
        lang_label.pack(side=tk.RIGHT, padx=5)
        self.lang_var = tk.StringVar(value="English")
        lang_menu = ttk.Combobox(top_bar, textvariable=self.lang_var, values=["English", "Türkçe"], state="readonly", width=10)
        lang_menu.pack(side=tk.RIGHT, padx=5)
        lang_menu.bind("<<ComboboxSelected>>", self.change_language)

        # Container for switching pages
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)

        # Register all frames
        self.frames = {}
        for F in (MainMenuFrame, SignupFrame, DashboardFrame, MembersFrame):
            frame = F(parent=self.container, controller=self)
            self.frames[F] = frame
            frame.place(x=0, y=0, relwidth=1, relheight=1)

        self.show_frame(MainMenuFrame)
        self.process_asyncio_events()

    def get_text(self, key):
        return translations[self.lang].get(key, key)

    def change_language(self, event=None):
        selection = self.lang_var.get()
        self.lang = "en" if selection == "English" else "tr"
        self.title(self.get_text("title"))
        for frame in self.frames.values():
            if hasattr(frame, "update_language"):
                frame.update_language()

    def center_window(self, width=700, height=500):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        if frame_class == MainMenuFrame:
            frame.refresh_accounts()
        if hasattr(frame, "update_language"):
            frame.update_language()
        frame.tkraise()

    def process_asyncio_events(self):
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0))
        self.after(50, self.process_asyncio_events)

# ---------------------------
# Main Execution
# ---------------------------
if __name__ == "__main__":
    init_db()
    app = App()
    app.mainloop()
