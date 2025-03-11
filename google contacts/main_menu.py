import tkinter as tk
from translations import translations

##############################################################################
# MainMenuFrame: The start page with language selection and navigation buttons
##############################################################################
class MainMenuFrame(tk.Frame):
    def __init__(self, master, controller):
        tk.Frame.__init__(self, master)
        self.controller = controller

        # Language selection dropdown
        lang_label = tk.Label(self)
        lang_label.pack(pady=5)
        self.lang_label = lang_label

        self.lang_var = tk.StringVar(value=self.controller.lang)
        lang_options = [("English", "en"), ("Türkçe", "tr")]
        option_menu = tk.OptionMenu(self, self.lang_var, *[opt[0] for opt in lang_options],
                                    command=self.change_language)
        option_menu.pack(pady=5)
        self.option_menu = option_menu

        # Navigation buttons
        self.upload_button = tk.Button(self, command=lambda: controller.show_frame("ContactsFrame"))
        self.upload_button.pack(pady=10)
        self.filter_button = tk.Button(self, command=lambda: controller.show_frame("FilterFrame"))
        self.filter_button.pack(pady=10)

    def change_language(self, selection):
        # Map the displayed language to its code.
        mapping = {"English": "en", "Türkçe": "tr"}
        lang_code = mapping.get(selection, "en")
        self.controller.set_language(lang_code)

    def update_texts(self):
        t = translations[self.controller.lang]
        self.lang_label.config(text=t["language"] + ":")
        # The option menu text is managed by the variable; ensure it shows proper label
        # (You may need additional handling if you want the menu items to update)
        self.upload_button.config(text=t["upload_data"])
        self.filter_button.config(text=t["extract_data"])
