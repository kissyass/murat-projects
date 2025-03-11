import tkinter as tk
from utility import center_window
from contacts import ContactsFrame
from filters import FilterFrame
from main_menu import MainMenuFrame

##############################################################################
# MainApp and Frames with Language Support
##############################################################################
class MainApp:
    def __init__(self, root):
        self.root = root
        self.lang = "en"  # default language
        self.root.title("Contacts Application")
        self.root.geometry("700x400")
        self.frames = {}
        for F in (MainMenuFrame, ContactsFrame, FilterFrame):
            page_name = F.__name__
            frame = F(self.root, self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("MainMenuFrame")
        center_window(self.root)

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        frame.update_texts()

    def set_language(self, lang):
        self.lang = lang
        # Update texts on all frames
        for frame in self.frames.values():
            frame.update_texts()

##############################################################################
# Script entry point
##############################################################################
if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
