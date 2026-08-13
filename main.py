"""
MakerWorld File Translator
---------------------------
TR: MakerWorld gibi kaynaklardan indirilen dosya/klasörlerdeki Çince
    isimleri toplu halde İngilizce, Türkçe, Almanca veya İspanyolca'ya
    çevirir. Koyu/açık temalı arayüz, opsiyonel alt klasör taraması,
    opsiyonel klasör ismi çevirisi ve dry-run (simülasyon) modu içerir.
EN: Bulk-renames Chinese file/folder names (e.g. from MakerWorld
    downloads) into English, Turkish, German, or Spanish, with a
    dark/light GUI, optional recursive subfolder scan, optional
    folder-name translation, and a dry-run mode.

TR: Çapraz platform: Windows ve macOS (Apple Silicon için PyInstaller
    ile native derleme).
EN: Cross-platform: Windows & macOS (Apple Silicon native build via
    PyInstaller).

Author / GitHub: BuRsTFiRe47
"""

import os
import threading
import customtkinter as ctk
from tkinter import filedialog
from deep_translator import GoogleTranslator

__version__ = "1.5.0"

# ---------------------------------------------------------------------
# TR: Desteklenen diller — hem arayüz dili hem de çeviri hedef dili için
#     kullanılır. Etiketler bayrak + iki harfli kod içerir: bir dil
#     bilmeyen kişi bile bayraktan (veya en kötü ihtimalle koddan)
#     kendi dilini bulabilir. NOT: Windows'ta bazı yazı tipleri bayrak
#     emojisini harf çifti olarak gösterebilir — bu yüzden kod da yanına
#     eklendi, tek başına bayrağa güvenilmiyor.
# EN: Supported languages — used for both the UI language and the file
#     translation target language. Labels combine a flag + two-letter
#     code: even someone who can't read the language can find their own
#     by the flag (or, worst case, the code). NOTE: On Windows some
#     fonts render flag emoji as plain letter pairs — pairing the code
#     alongside it avoids relying on the flag alone.
# ---------------------------------------------------------------------
LANG_OPTIONS = [
    ("tr", "🇹🇷 TR"),
    ("en", "🇬🇧 EN"),
    ("de", "🇩🇪 DE"),
    ("es", "🇪🇸 ES"),
]
LABEL_TO_CODE = {label: code for code, label in LANG_OPTIONS}
CODE_TO_LABEL = {code: label for code, label in LANG_OPTIONS}

# ---------------------------------------------------------------------
# TR: Arayüz metin tabloları (program dili: TR / EN / DE / ES)
# EN: UI text tables (program language: TR / EN / DE / ES)
# ---------------------------------------------------------------------
TEXTS = {
    "tr": {
        "title": "MakerWorld Dosya Çevirici",
        "select_folder": "Klasör Seç",
        "folder_placeholder": "Bir klasör seçin...",
        "subfolder_check": "Alt Klasörleri Tara",
        "folder_name_check": "Klasör İsimlerini de Çevir",
        "dryrun_check": "Dry Run (Sadece Simülasyon)",
        "translation_direction": "Çeviri Yönü (Çince →):",
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
        "lang_names": {"tr": "Türkçe", "en": "İngilizce", "de": "Almanca", "es": "İspanyolca"},
    },
    "en": {
        "title": "MakerWorld File Translator",
        "select_folder": "Select Folder",
        "folder_placeholder": "Select a folder...",
        "subfolder_check": "Scan Subfolders",
        "folder_name_check": "Also Translate Folder Names",
        "dryrun_check": "Dry Run (Simulation Only)",
        "translation_direction": "Translation Direction (Chinese →):",
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
        "lang_names": {"tr": "Turkish", "en": "English", "de": "German", "es": "Spanish"},
    },
    "de": {
        "title": "MakerWorld Datei-Übersetzer",
        "select_folder": "Ordner Auswählen",
        "folder_placeholder": "Wählen Sie einen Ordner...",
        "subfolder_check": "Unterordner Durchsuchen",
        "folder_name_check": "Auch Ordnernamen Übersetzen",
        "dryrun_check": "Testlauf (Nur Simulation)",
        "translation_direction": "Übersetzungsrichtung (Chinesisch →):",
        "ui_lang": "Programmsprache:",
        "theme_switch_dark": "Dunkler Modus",
        "theme_switch_light": "Heller Modus",
        "start_btn": "Starten",
        "start_btn_busy": "Wird verarbeitet...",
        "log_header": "--- GESTARTET --- (Zielsprache: {lang})",
        "dryrun_warning": "WARNUNG: Testlauf ist aktiv. Namen werden nicht tatsächlich geändert.\n",
        "no_folder": "Bitte wählen Sie zuerst einen Ordner aus!",
        "no_chinese": "Keine Datei/kein Ordner mit chinesischen Zeichen gefunden.",
        "done": "--- FERTIG ---",
        "success": "[ERFOLG]",
        "error": "[FEHLER]",
        "dry_found": "[TESTLAUF] Gefunden",
        "dry_translated": "[TESTLAUF] Übersetzt",
        "lang_names": {"tr": "Türkisch", "en": "Englisch", "de": "Deutsch", "es": "Spanisch"},
    },
    "es": {
        "title": "Traductor de Archivos MakerWorld",
        "select_folder": "Seleccionar Carpeta",
        "folder_placeholder": "Selecciona una carpeta...",
        "subfolder_check": "Escanear Subcarpetas",
        "folder_name_check": "Traducir También los Nombres de Carpetas",
        "dryrun_check": "Simulación (Solo Prueba)",
        "translation_direction": "Dirección de Traducción (Chino →):",
        "ui_lang": "Idioma del Programa:",
        "theme_switch_dark": "Modo Oscuro",
        "theme_switch_light": "Modo Claro",
        "start_btn": "Iniciar",
        "start_btn_busy": "Procesando...",
        "log_header": "--- INICIADO --- (Idioma de destino: {lang})",
        "dryrun_warning": "AVISO: La simulación está activa. Los nombres no cambiarán realmente.\n",
        "no_folder": "¡Por favor selecciona una carpeta primero!",
        "no_chinese": "No se encontró ningún archivo/carpeta con caracteres chinos.",
        "done": "--- COMPLETADO ---",
        "success": "[ÉXITO]",
        "error": "[ERROR]",
        "dry_found": "[SIMULACIÓN] Encontrado",
        "dry_translated": "[SIMULACIÓN] Traducido",
        "lang_names": {"tr": "Turco", "en": "Inglés", "de": "Alemán", "es": "Español"},
    },
}

# TR: Windows/macOS dosya isimlerinde yasak olan karakterler
# EN: Characters not allowed in Windows/macOS file names
INVALID_CHARS = '<>:"/\\|?*'


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.ui_lang = "tr"          # program dili / UI language
        self.T = TEXTS[self.ui_lang]

        self.geometry("760x620")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # TR: Üst bar — program dili seçimi (bayrak + kod düğmeleri) ve tema anahtarı
        # EN: Top bar — program language selector (flag + code buttons) and theme switch
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.top_frame.grid_columnconfigure(1, weight=1)

        self.ui_lang_label = ctk.CTkLabel(self.top_frame, text="")
        self.ui_lang_label.grid(row=0, column=0, padx=(15, 10), pady=10, sticky="w")

        self.ui_lang_selector = ctk.CTkSegmentedButton(
            self.top_frame,
            values=[label for _, label in LANG_OPTIONS],
            command=self.change_ui_lang,
        )
        self.ui_lang_selector.set(CODE_TO_LABEL[self.ui_lang])
        self.ui_lang_selector.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.theme_switch = ctk.CTkSwitch(self.top_frame, text="", command=self.toggle_theme)
        self.theme_switch.grid(row=0, column=2, padx=(10, 15), pady=10, sticky="e")

        # TR: Klasör seçimi
        # EN: Folder selection
        self.folder_frame = ctk.CTkFrame(self)
        self.folder_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.folder_frame.grid_columnconfigure(0, weight=1)

        self.folder_path = ctk.StringVar()
        self.folder_entry = ctk.CTkEntry(self.folder_frame, textvariable=self.folder_path, state="disabled")
        self.folder_entry.grid(row=0, column=0, padx=(10, 10), pady=10, sticky="ew")

        self.browse_btn = ctk.CTkButton(self.folder_frame, text="", command=self.browse_folder, width=130)
        self.browse_btn.grid(row=0, column=1, padx=(0, 10), pady=10)

        # TR: Seçenekler — alt klasör tarama, klasör ismi çevirisi, dry run
        # EN: Options — subfolder scan, folder-name translation, dry run
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

        # TR: Çeviri yönü — hedef dil bayrak + kod düğmeleriyle seçilir
        # EN: Translation direction — target language chosen via flag + code buttons
        self.lang_frame = ctk.CTkFrame(self)
        self.lang_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.lang_dir_label = ctk.CTkLabel(self.lang_frame, text="")
        self.lang_dir_label.grid(row=0, column=0, padx=(15, 10), pady=10, sticky="w")

        self.lang_var = ctk.StringVar(value="en")
        self.lang_selector = ctk.CTkSegmentedButton(
            self.lang_frame,
            values=[label for _, label in LANG_OPTIONS],
            command=self.change_target_lang,
        )
        self.lang_selector.set(CODE_TO_LABEL[self.lang_var.get()])
        self.lang_selector.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # TR: Başlat butonu
        # EN: Start button
        self.start_btn = ctk.CTkButton(
            self, text="", command=self.start_process, fg_color="#2e8b57", hover_color="#256d46", height=40
        )
        self.start_btn.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        # TR: Log / konsol ekranı
        # EN: Log console
        self.log_textbox = ctk.CTkTextbox(self, state="disabled", font=("Consolas", 12))
        self.log_textbox.grid(row=5, column=0, padx=20, pady=(10, 20), sticky="nsew")

        self.refresh_texts()

    # -------------------------------------------------------------
    # TR: Arayüz dili / tema yönetimi
    # EN: UI language / theme handling
    # -------------------------------------------------------------
    def change_ui_lang(self, label):
        """TR: Program dilini değiştirir. EN: Switches the program (UI) language."""
        self.ui_lang = LABEL_TO_CODE[label]
        self.T = TEXTS[self.ui_lang]
        self.refresh_texts()

    def refresh_texts(self):
        """TR: Tüm arayüz metinlerini seçili dile göre günceller.
        EN: Refreshes every UI label according to the selected language."""
        T = self.T
        self.title(f"{T['title']} v{__version__}")
        self.ui_lang_label.configure(text=T["ui_lang"])
        self.folder_entry.configure(placeholder_text=T["folder_placeholder"])
        self.browse_btn.configure(text=T["select_folder"])
        self.subfolder_checkbox.configure(text=T["subfolder_check"])
        self.folder_name_checkbox.configure(text=T["folder_name_check"])
        self.dryrun_checkbox.configure(text=T["dryrun_check"])
        self.lang_dir_label.configure(text=T["translation_direction"])

        is_light = self.theme_switch.get()
        self.theme_switch.configure(text=T["theme_switch_light"] if not is_light else T["theme_switch_dark"])

        self.start_btn.configure(text=T["start_btn"])

    def toggle_theme(self):
        """TR: Koyu/açık temayı değiştirir. EN: Toggles dark/light theme."""
        if self.theme_switch.get():
            ctk.set_appearance_mode("Light")
        else:
            ctk.set_appearance_mode("Dark")
        self.refresh_texts()

    def change_target_lang(self, label):
        """TR: Çeviri hedef dilini günceller. EN: Updates the translation target language."""
        self.lang_var.set(LABEL_TO_CODE[label])

    # -------------------------------------------------------------
    # TR: Klasör seçimi / log yardımcı fonksiyonları
    # EN: Folder selection / logging helpers
    # -------------------------------------------------------------
    def browse_folder(self):
        """TR: Kullanıcıya klasör seçtirir. EN: Opens a folder-picker dialog."""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def log(self, message):
        """TR: Log kutusuna bir satır ekler. EN: Appends a line to the log box."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    @staticmethod
    def is_chinese(text):
        """TR: Metinde Çince karakter olup olmadığını kontrol eder.
        EN: Checks whether the text contains any Chinese characters."""
        return any('\u4e00' <= ch <= '\u9fff' for ch in text)

    @staticmethod
    def clean_name(name):
        """TR: Dosya/klasör isimlerinde yasak karakterleri temizler.
        EN: Strips characters that are invalid in file/folder names."""
        for ch in INVALID_CHARS:
            name = name.replace(ch, '')
        return name.strip()

    # -------------------------------------------------------------
    # TR: Ana işlem
    # EN: Main process
    # -------------------------------------------------------------
    def start_process(self):
        """TR: 'Başlat' butonuna basıldığında işlemi arka planda thread'de başlatır.
        EN: Kicks off the renaming job on a background thread when Start is pressed."""
        folder = self.folder_path.get()
        T = self.T
        if not folder:
            self.log(T["no_folder"])
            return
        self.start_btn.configure(state="disabled", text=T["start_btn_busy"])
        threading.Thread(target=self.process_files, args=(folder,), daemon=True).start()

    def process_files(self, base_folder):
        """TR: Seçilen klasördeki (ve isteğe göre alt klasörlerdeki) Çince
        isimli dosya/klasörleri tarar, çevirir ve yeniden adlandırır.
        EN: Scans the selected folder (and optionally its subfolders) for
        Chinese-named files/folders, translates them, and renames them."""
        T = self.T
        include_subfolders = self.subfolder_var.get()
        translate_folders = self.folder_name_var.get()
        dry_run = self.dryrun_var.get()
        target_lang = self.lang_var.get()

        translator = GoogleTranslator(source='auto', target=target_lang)
        lang_name = T["lang_names"][target_lang]
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

        # TR: Önce dosyalar
        # EN: Files first
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

        # TR: Klasörler en derinden başlanarak (bottom-up) işlenir; böylece
        #     bir üst klasör yeniden adlandırıldığında henüz işlenmemiş bir
        #     alt klasörün yolu bozulmaz.
        # EN: Folders are processed bottom-up, so renaming a parent never
        #     breaks a still-pending child path.
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
