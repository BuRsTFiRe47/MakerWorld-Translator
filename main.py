"""
MakerWorld File Translator
---------------------------
Bulk-renames Chinese file/folder names (e.g. from MakerWorld downloads)
into English or Turkish, with a dark/light GUI, optional recursive
subfolder scan, optional folder-name translation, and a dry-run mode.

Cross-platform: Windows & macOS (Apple Silicon native build via PyInstaller).
"""

import os
import threading
import customtkinter as ctk
from tkinter import filedialog
from deep_translator import GoogleTranslator

# ---------------------------------------------------------------------
# UI text tables (program language: Turkish / English)
# ---------------------------------------------------------------------
TEXTS = {
    "tr": {
        "title": "MakerWorld Dosya Çevirici",
        "select_folder": "Klasör Seç",
        "folder_placeholder": "Bir klasör seçin...",
        "subfolder_check": "Alt Klasörleri Tara",
        "folder_name_check": "Klasör İsimlerini de Çevir",
        "dryrun_check": "Dry Run (Sadece Simülasyon)",
        "translation_direction": "Çeviri Yönü:",
        "dir_en": "Çince → İngilizce",
        "dir_tr": "Çince → Türkçe",
        "ui_lang": "Program Dili:",
        "theme_switch_dark": "Koyu Mod",
        "theme_switch_light": "Açık Mod",
        "start_btn": "İşlemi Başlat",
        "start_btn_busy": "İşlem Yapılıyor...",
        "log_header": "--- İŞLEM BAŞLADI --- (Hedef Dil: {lang})",
        "dryrun_warning": "UYARI: Dry Run aktif. İsimler gerçekte değiştirilmeyecek.\n",
        "no_folder": "Lütfen önce bir klasör seçin!",
        "no_chinese": "Klasörde Çince karakter içeren dosya/klasör bulunamadı.",
        "done": "--- İŞLEM TAMAMLANDI ---",
        "success": "[BAŞARILI]",
        "error": "[HATA]",
        "dry_found": "[DRY RUN] Bulundu",
        "dry_translated": "[DRY RUN] Çevrildi",
        "lang_target_en": "İngilizce",
        "lang_target_tr": "Türkçe",
    },
    "en": {
        "title": "MakerWorld File Translator",
        "select_folder": "Select Folder",
        "folder_placeholder": "Select a folder...",
        "subfolder_check": "Scan Subfolders",
        "folder_name_check": "Also Translate Folder Names",
        "dryrun_check": "Dry Run (Simulation Only)",
        "translation_direction": "Translation Direction:",
        "dir_en": "Chinese → English",
        "dir_tr": "Chinese → Turkish",
        "ui_lang": "Program Language:",
        "theme_switch_dark": "Dark Mode",
        "theme_switch_light": "Light Mode",
        "start_btn": "Start",
        "start_btn_busy": "Processing...",
        "log_header": "--- STARTED --- (Target language: {lang})",
        "dryrun_warning": "WARNING: Dry Run is active. Names will not actually change.\n",
        "no_folder": "Please select a folder first!",
        "no_chinese": "No file/folder with Chinese characters was found.",
        "done": "--- DONE ---",
        "success": "[SUCCESS]",
        "error": "[ERROR]",
        "dry_found": "[DRY RUN] Found",
        "dry_translated": "[DRY RUN] Translated",
        "lang_target_en": "English",
        "lang_target_tr": "Turkish",
    },
}

INVALID_CHARS = '<>:"/\\|?*'


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.ui_lang = "tr"          # program dili / UI language
        self.T = TEXTS[self.ui_lang]

        self.geometry("700x600")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # ---------------- Top bar: program language + theme ----------------
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.top_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.ui_lang_label = ctk.CTkLabel(self.top_frame, text="")
        self.ui_lang_label.grid(row=0, column=0, padx=(15, 5), pady=10, sticky="w")

        self.ui_lang_menu = ctk.CTkOptionMenu(
            self.top_frame, values=["Türkçe", "English"], command=self.change_ui_lang, width=110
        )
        self.ui_lang_menu.set("Türkçe")
        self.ui_lang_menu.grid(row=0, column=1, padx=5, pady=10, sticky="w")

        self.theme_switch = ctk.CTkSwitch(self.top_frame, text="", command=self.toggle_theme)
        self.theme_switch.grid(row=0, column=3, padx=(5, 15), pady=10, sticky="e")

        # ---------------- Folder selection ----------------
        self.folder_frame = ctk.CTkFrame(self)
        self.folder_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.folder_frame.grid_columnconfigure(0, weight=1)

        self.folder_path = ctk.StringVar()
        self.folder_entry = ctk.CTkEntry(self.folder_frame, textvariable=self.folder_path, state="disabled")
        self.folder_entry.grid(row=0, column=0, padx=(10, 10), pady=10, sticky="ew")

        self.browse_btn = ctk.CTkButton(self.folder_frame, text="", command=self.browse_folder, width=130)
        self.browse_btn.grid(row=0, column=1, padx=(0, 10), pady=10)

        # ---------------- Options ----------------
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.options_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.subfolder_var = ctk.BooleanVar(value=False)
        self.subfolder_checkbox = ctk.CTkCheckBox(self.options_frame, text="", variable=self.subfolder_var)
        self.subfolder_checkbox.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.folder_name_var = ctk.BooleanVar(value=False)
        self.folder_name_checkbox = ctk.CTkCheckBox(self.options_frame, text="", variable=self.folder_name_var)
        self.folder_name_checkbox.grid(row=0, column=1, padx=15, pady=10, sticky="w")

        self.dryrun_var = ctk.BooleanVar(value=False)
        self.dryrun_checkbox = ctk.CTkCheckBox(self.options_frame, text="", variable=self.dryrun_var)
        self.dryrun_checkbox.grid(row=0, column=2, padx=15, pady=10, sticky="w")

        # ---------------- Translation direction ----------------
        self.lang_frame = ctk.CTkFrame(self)
        self.lang_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.lang_dir_label = ctk.CTkLabel(self.lang_frame, text="")
        self.lang_dir_label.grid(row=0, column=0, padx=(15, 10), pady=10, sticky="w")

        self.lang_var = ctk.StringVar(value="en")
        self.lang_menu = ctk.CTkOptionMenu(self.lang_frame, values=[], command=self.change_target_lang)
        self.lang_menu.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # ---------------- Start button ----------------
        self.start_btn = ctk.CTkButton(
            self, text="", command=self.start_process, fg_color="#2e8b57", hover_color="#256d46", height=40
        )
        self.start_btn.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        # ---------------- Log console ----------------
        self.log_textbox = ctk.CTkTextbox(self, state="disabled", font=("Consolas", 12))
        self.log_textbox.grid(row=5, column=0, padx=20, pady=(10, 20), sticky="nsew")

        self.refresh_texts()

    # -------------------------------------------------------------
    # UI language / theme handling
    # -------------------------------------------------------------
    def change_ui_lang(self, choice):
        self.ui_lang = "tr" if choice == "Türkçe" else "en"
        self.T = TEXTS[self.ui_lang]
        self.refresh_texts()

    def refresh_texts(self):
        T = self.T
        self.title(T["title"])
        self.ui_lang_label.configure(text=T["ui_lang"])
        self.folder_entry.configure(placeholder_text=T["folder_placeholder"])
        self.browse_btn.configure(text=T["select_folder"])
        self.subfolder_checkbox.configure(text=T["subfolder_check"])
        self.folder_name_checkbox.configure(text=T["folder_name_check"])
        self.dryrun_checkbox.configure(text=T["dryrun_check"])
        self.lang_dir_label.configure(text=T["translation_direction"])

        current_target = self.lang_var.get()
        self.lang_menu.configure(values=[T["dir_en"], T["dir_tr"]])
        self.lang_menu.set(T["dir_en"] if current_target == "en" else T["dir_tr"])

        is_light = self.theme_switch.get()
        self.theme_switch.configure(text=T["theme_switch_light"] if not is_light else T["theme_switch_dark"])

        self.start_btn.configure(text=T["start_btn"])

    def toggle_theme(self):
        if self.theme_switch.get():
            ctk.set_appearance_mode("Light")
        else:
            ctk.set_appearance_mode("Dark")
        self.refresh_texts()

    def change_target_lang(self, choice):
        self.lang_var.set("en" if choice == self.T["dir_en"] else "tr")

    # -------------------------------------------------------------
    # Folder selection / logging helpers
    # -------------------------------------------------------------
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    @staticmethod
    def is_chinese(text):
        return any('\u4e00' <= ch <= '\u9fff' for ch in text)

    @staticmethod
    def clean_name(name):
        for ch in INVALID_CHARS:
            name = name.replace(ch, '')
        return name.strip()

    # -------------------------------------------------------------
    # Main process
    # -------------------------------------------------------------
    def start_process(self):
        folder = self.folder_path.get()
        T = self.T
        if not folder:
            self.log(T["no_folder"])
            return
        self.start_btn.configure(state="disabled", text=T["start_btn_busy"])
        threading.Thread(target=self.process_files, args=(folder,), daemon=True).start()

    def process_files(self, base_folder):
        T = self.T
        include_subfolders = self.subfolder_var.get()
        translate_folders = self.folder_name_var.get()
        dry_run = self.dryrun_var.get()
        target_lang = self.lang_var.get()

        translator = GoogleTranslator(source='auto', target=target_lang)
        lang_name = T["lang_target_en"] if target_lang == "en" else T["lang_target_tr"]
        self.log(T["log_header"].format(lang=lang_name))
        if dry_run:
            self.log(T["dryrun_warning"])

        file_list = []
        folder_list = []

        if include_subfolders:
            for root, dirs, files in os.walk(base_folder):
                for f in files:
                    file_list.append(os.path.join(root, f))
                if translate_folders:
                    for d in dirs:
                        folder_list.append(os.path.join(root, d))
        else:
            for entry in os.listdir(base_folder):
                full_path = os.path.join(base_folder, entry)
                if os.path.isfile(full_path):
                    file_list.append(full_path)
                elif os.path.isdir(full_path) and translate_folders:
                    folder_list.append(full_path)

        found_any = False

        # --- Files first ---
        for path in file_list:
            dir_name, file_name = os.path.split(path)
            if self.is_chinese(file_name):
                found_any = True
                name, ext = os.path.splitext(file_name)
                try:
                    translated = self.clean_name(translator.translate(name))
                    new_name = translated + ext
                    new_path = os.path.join(dir_name, new_name)
                    if dry_run:
                        self.log(f"{T['dry_found']}: {file_name}\n{T['dry_translated']}: {new_name}\n")
                    else:
                        os.rename(path, new_path)
                        self.log(f"{T['success']} {file_name} -> {new_name}")
                except Exception as e:
                    self.log(f"{T['error']} {file_name}: {e}")

        # --- Folders bottom-up, so renaming a parent never breaks a
        #     still-pending child path ---
        folder_list.sort(key=lambda p: p.count(os.sep), reverse=True)
        for path in folder_list:
            dir_name, folder_name = os.path.split(path)
            if self.is_chinese(folder_name):
                found_any = True
                try:
                    new_name = self.clean_name(translator.translate(folder_name))
                    new_path = os.path.join(dir_name, new_name)
                    if dry_run:
                        self.log(f"{T['dry_found']}: {folder_name}\n{T['dry_translated']}: {new_name}\n")
                    else:
                        os.rename(path, new_path)
                        self.log(f"{T['success']} {folder_name} -> {new_name}")
                except Exception as e:
                    self.log(f"{T['error']} {folder_name}: {e}")

        if not found_any:
            self.log(T["no_chinese"])

        self.log(T["done"])
        self.start_btn.configure(state="normal", text=T["start_btn"])


if __name__ == "__main__":
    app = App()
    app.mainloop()
