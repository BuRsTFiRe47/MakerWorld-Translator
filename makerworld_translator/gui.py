"""PySide6 GUI / PySide6 arayüzü."""

from __future__ import annotations

import os
import sys

from PySide6.QtCore import QLocale, QSettings, Qt, QThread, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QPlainTextEdit, QProgressBar, QPushButton, QVBoxLayout, QWidget,
)

from . import GITHUB_URL, __version__, core
from .i18n import FLAGS, LANGS, NATIVE, STRINGS

# TR: Windows'ta bayrak emojileri harf çiftine dönüşür; orada sadece yerel isim gösterilir.
# EN: Windows renders flag emoji as letter pairs; there we show the native name only.
USE_FLAGS = sys.platform != "win32"

THEMES = {
    "dark": dict(window="#1e1f22", base="#2b2d30", text="#e6e6e6", btn="#33363b", border="#43474d",
                 accent="#3b82f6", muted="#9aa0a6", logbg="#17181a", link="#7db2ff"),
    "light": dict(window="#f3f4f6", base="#ffffff", text="#111827", btn="#ffffff", border="#cbd5e1",
                  accent="#2563eb", muted="#6b7280", logbg="#ffffff", link="#2563eb"),
}

QSS = """
QPushButton[seg="first"], QPushButton[seg="mid"], QPushButton[seg="last"] {
    background: @btn@; color: @text@; border: 1px solid @border@; padding: 6px 14px; margin-right: -1px;
}
QPushButton[seg="first"]:checked, QPushButton[seg="mid"]:checked, QPushButton[seg="last"]:checked {
    background: @accent@; color: white; border-color: @accent@;
}
QPushButton[seg="first"] { border-top-left-radius: 6px; border-bottom-left-radius: 6px; }
QPushButton[seg="last"] { border-top-right-radius: 6px; border-bottom-right-radius: 6px; margin-right: 0; }
QPushButton#primary { background: #2e8b57; color: white; border: none; border-radius: 6px; padding: 9px 18px; font-weight: 600; }
QPushButton#primary:hover { background: #256d46; }
QPushButton#primary:disabled { background: @border@; color: @muted@; }
QPushButton#danger { background: #b4443f; color: white; border: none; border-radius: 6px; padding: 9px 18px; font-weight: 600; }
QPushButton#danger:hover { background: #963833; }
QPushButton#danger:disabled { background: @border@; color: @muted@; }
QPushButton#browse { background: @btn@; color: @text@; border: 1px solid @border@; border-radius: 6px; padding: 6px 14px; }
QLineEdit, QPlainTextEdit { background: @logbg@; color: @text@; border: 1px solid @border@; border-radius: 6px; padding: 5px; }
QLabel#muted { color: @muted@; }
QProgressBar { border: 1px solid @border@; border-radius: 6px; text-align: center; background: @logbg@; color: @text@; }
QProgressBar::chunk { background: @accent@; border-radius: 5px; }
"""


def apply_theme(app: QApplication, mode: str) -> None:
    c = THEMES[mode]
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(c["window"]))
    pal.setColor(QPalette.WindowText, QColor(c["text"]))
    pal.setColor(QPalette.Base, QColor(c["base"]))
    pal.setColor(QPalette.AlternateBase, QColor(c["window"]))
    pal.setColor(QPalette.Text, QColor(c["text"]))
    pal.setColor(QPalette.Button, QColor(c["btn"]))
    pal.setColor(QPalette.ButtonText, QColor(c["text"]))
    pal.setColor(QPalette.ToolTipBase, QColor(c["base"]))
    pal.setColor(QPalette.ToolTipText, QColor(c["text"]))
    pal.setColor(QPalette.Highlight, QColor(c["accent"]))
    pal.setColor(QPalette.HighlightedText, QColor("white"))
    pal.setColor(QPalette.PlaceholderText, QColor(c["muted"]))
    pal.setColor(QPalette.Link, QColor(c["link"]))
    app.setPalette(pal)
    qss = QSS
    for key, val in c.items():
        qss = qss.replace(f"@{key}@", val)
    app.setStyleSheet(qss)


class Segmented(QWidget):
    """Tek seçimli buton grubu / exclusive button group (replaces dropdowns)."""

    changed = Signal(str)

    def __init__(self, items):
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QPushButton] = {}
        for i, (key, text, tip) in enumerate(items):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setToolTip(tip)
            btn.setCursor(Qt.PointingHandCursor)
            pos = "first" if i == 0 else "last" if i == len(items) - 1 else "mid"
            btn.setProperty("seg", pos)
            btn.clicked.connect(lambda _=False, k=key: self.changed.emit(k))
            self._group.addButton(btn)
            lay.addWidget(btn)
            self._buttons[key] = btn

    def set_current(self, key: str) -> None:
        self._buttons[key].setChecked(True)

    def set_text(self, key: str, text: str) -> None:
        self._buttons[key].setText(text)


def lang_button_text(code: str) -> str:
    return f"{FLAGS[code]} {NATIVE[code]}" if USE_FLAGS else NATIVE[code]


class Worker(QThread):
    event = Signal(object)
    progress = Signal(int, int)
    done = Signal(object)

    def __init__(self, params: dict):
        super().__init__()
        self.params = params
        self._stop = False

    def request_stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        p = self.params
        try:
            summary = core.run(
                p["folder"], source=p["source"], target_code=p["target"], recursive=p["recursive"],
                include_folders=p["folders"], dry_run=p["dry"],
                translate=core.GoogleBackend().translate, emit=self.event.emit,
                should_stop=lambda: self._stop, progress=self.progress.emit,
            )
        except Exception as exc:  # e.g. permission error while scanning
            self.event.emit(core.Event("error", detail=str(exc)))
            summary = core.Summary(errors=1)
        self.done.emit(summary)


class MainWindow(QWidget):
    def __init__(self, settings: QSettings):
        super().__init__()
        self.settings = settings
        sys_lang = QLocale.system().name()[:2]
        self.ui_lang = str(settings.value("ui_lang", sys_lang if sys_lang in LANGS else "en"))
        if self.ui_lang not in LANGS:
            self.ui_lang = "en"
        self.theme = str(settings.value("theme", "dark"))  # dark by default
        if self.theme not in THEMES:
            self.theme = "dark"
        self.target = str(settings.value("target", "en"))
        if self.target not in core.TARGET_CODES:
            self.target = "en"
        self.worker: Worker | None = None
        self._dry = False

        self.resize(820, 680)
        self.setAcceptDrops(True)
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 14)
        root.setSpacing(12)

        # Row 1: UI language + theme
        row = QHBoxLayout()
        self.lbl_ui = QLabel()
        self.ui_seg = Segmented([(c, lang_button_text(c), NATIVE[c]) for c in LANGS])
        self.ui_seg.set_current(self.ui_lang)
        self.ui_seg.changed.connect(self.on_ui_lang)
        self.theme_seg = Segmented([("dark", "🌙", ""), ("light", "☀", "")])
        self.theme_seg.set_current(self.theme)
        self.theme_seg.changed.connect(self.on_theme)
        row.addWidget(self.lbl_ui)
        row.addWidget(self.ui_seg)
        row.addStretch(1)
        row.addWidget(self.theme_seg)
        root.addLayout(row)

        # Row 2: folder
        row = QHBoxLayout()
        self.folder_edit = QLineEdit()
        self.folder_edit.setReadOnly(True)
        self.browse_btn = QPushButton()
        self.browse_btn.setObjectName("browse")
        self.browse_btn.clicked.connect(self.browse)
        row.addWidget(self.folder_edit, 1)
        row.addWidget(self.browse_btn)
        root.addLayout(row)

        # Row 3: source language
        row = QHBoxLayout()
        self.lbl_src = QLabel()
        self.src_combo = QComboBox()
        self.src_combo.addItem("")
        for lang in core.SOURCE_LANGUAGES:
            self.src_combo.addItem(f"{lang.native} — {lang.english}", lang.code)
        saved_src = str(settings.value("source", ""))
        idx = self.src_combo.findData(saved_src) if saved_src else 0
        self.src_combo.setCurrentIndex(max(idx, 0))
        row.addWidget(self.lbl_src)
        row.addWidget(self.src_combo, 1)
        root.addLayout(row)

        # Row 4: target language
        row = QHBoxLayout()
        self.lbl_dst = QLabel()
        self.dst_seg = Segmented([(c, lang_button_text(c), NATIVE[c]) for c in core.TARGET_CODES])
        self.dst_seg.set_current(self.target)
        self.dst_seg.changed.connect(self.on_target)
        row.addWidget(self.lbl_dst)
        row.addWidget(self.dst_seg)
        row.addStretch(1)
        root.addLayout(row)

        # Row 5: options
        row = QHBoxLayout()
        self.chk_sub = QCheckBox()
        self.chk_folders = QCheckBox()
        self.chk_dry = QCheckBox()
        for chk in (self.chk_sub, self.chk_folders, self.chk_dry):
            row.addWidget(chk)
        row.addStretch(1)
        root.addLayout(row)

        # Row 6: start / stop + progress
        row = QHBoxLayout()
        self.start_btn = QPushButton()
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self.start)
        self.stop_btn = QPushButton()
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop)
        row.addWidget(self.start_btn, 1)
        row.addWidget(self.stop_btn)
        root.addLayout(row)
        self.bar = QProgressBar()
        self.bar.setValue(0)
        root.addWidget(self.bar)

        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        mono = self.log_box.font()
        mono.setFamily("Menlo" if sys.platform == "darwin" else "Consolas")
        mono.setStyleHint(mono.StyleHint.Monospace)
        self.log_box.setFont(mono)
        root.addWidget(self.log_box, 1)

        footer = QLabel(f'v{__version__} · <a href="{GITHUB_URL}">github.com/BuRsTFiRe47/MakerWorld-Translator</a>')
        footer.setObjectName("muted")
        footer.setOpenExternalLinks(True)
        footer.setAlignment(Qt.AlignRight)
        root.addWidget(footer)

        # TR: Etiketleri tüm dillerdeki en uzun metne göre hizala (kesilmesin).
        # EN: Align labels to the longest text across all languages (no clipping).
        fm = self.lbl_ui.fontMetrics()
        label_w = max(
            fm.horizontalAdvance(STRINGS[c][k]) for c in LANGS for k in ("ui_language", "source_label", "target_label")
        ) + 12
        for lbl in (self.lbl_ui, self.lbl_src, self.lbl_dst):
            lbl.setMinimumWidth(label_w)

        apply_theme(QApplication.instance(), self.theme)
        self.retranslate()

    # --- helpers ---------------------------------------------------------
    @property
    def T(self) -> dict:
        return STRINGS[self.ui_lang]

    def retranslate(self) -> None:
        T = self.T
        self.setWindowTitle(f"{T['window_title']} v{__version__}")
        self.lbl_ui.setText(T["ui_language"])
        self.theme_seg._buttons["dark"].setToolTip(T["theme_dark"])
        self.theme_seg._buttons["light"].setToolTip(T["theme_light"])
        self.folder_edit.setPlaceholderText(T["folder_placeholder"])
        self.browse_btn.setText(T["browse"])
        self.lbl_src.setText(T["source_label"])
        self.src_combo.setItemText(0, T["source_auto"])
        self.lbl_dst.setText(T["target_label"])
        self.chk_sub.setText(T["opt_subfolders"])
        self.chk_folders.setText(T["opt_folders"])
        self.chk_dry.setText(T["opt_dry"])
        self.start_btn.setText(T["start"])
        self.stop_btn.setText(T["stop"])

    def log(self, text: str) -> None:
        self.log_box.appendPlainText(text)

    # --- slots -----------------------------------------------------------
    def on_ui_lang(self, code: str) -> None:
        self.ui_lang = code
        self.settings.setValue("ui_lang", code)
        self.retranslate()

    def on_theme(self, mode: str) -> None:
        self.theme = mode
        self.settings.setValue("theme", mode)
        apply_theme(QApplication.instance(), mode)

    def on_target(self, code: str) -> None:
        self.target = code
        self.settings.setValue("target", code)

    def browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, self.T["browse"])
        if folder:
            self.folder_edit.setText(folder)

    def dragEnterEvent(self, e) -> None:
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e) -> None:
        for url in e.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                self.folder_edit.setText(path)
                break

    def set_running(self, running: bool) -> None:
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.stop_btn.setText(self.T["stop"])

    def start(self) -> None:
        T = self.T
        folder = self.folder_edit.text()
        if not folder:
            self.log(f"{T['tag_err']} {T['err_no_folder']}")
            return
        if not os.path.isdir(folder):
            self.log(f"{T['tag_err']} {T['err_bad_folder'].format(path=folder)}")
            return
        code = self.src_combo.currentData()
        source = next((s for s in core.SOURCE_LANGUAGES if s.code == code), None)
        self.settings.setValue("source", code or "")
        self._dry = self.chk_dry.isChecked()
        src_name = T["source_auto"] if source is None else source.native
        self.log(T["log_start"].format(src=src_name, dst=NATIVE[self.target]))
        if self._dry:
            self.log(T["log_dry_notice"])
        self.bar.setValue(0)
        self.set_running(True)
        self.worker = Worker(dict(
            folder=folder, source=source, target=self.target, recursive=self.chk_sub.isChecked(),
            folders=self.chk_folders.isChecked(), dry=self._dry,
        ))
        self.worker.event.connect(self.on_event)
        self.worker.progress.connect(self.on_progress)
        self.worker.done.connect(self.on_done)
        self.worker.start()

    def stop(self) -> None:
        if self.worker:
            self.worker.request_stop()
            self.stop_btn.setEnabled(False)
            self.stop_btn.setText(self.T["stopping"])

    def on_progress(self, done: int, total: int) -> None:
        self.bar.setMaximum(max(total, 1))
        self.bar.setValue(done)

    def on_event(self, ev: core.Event) -> None:
        T = self.T
        k = ev.kind
        if k == "renamed":
            self.log(f"{T['tag_ok']} {ev.old}  →  {ev.new}")
        elif k == "dry":
            self.log(f"{T['tag_dry']} {ev.old}  →  {ev.new}")
        elif k == "unchanged":
            self.log(f"{T['tag_same']} {ev.old}")
        elif k == "error":
            self.log(f"{T['tag_err']} {ev.old + ': ' if ev.old else ''}{ev.detail}")
        elif k == "none":
            self.log(T["log_none"])
        elif k == "stopped":
            self.log(T["log_stopped"])

    def on_done(self, s: core.Summary) -> None:
        T = self.T
        key = "log_done_dry" if self._dry else "log_done"
        self.log(T[key].format(ok=s.renamed, same=s.unchanged, err=s.errors))
        self.set_running(False)

    def closeEvent(self, e) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.request_stop()
            self.worker.wait(3000)
        super().closeEvent(e)


def run() -> None:
    app = QApplication(sys.argv)
    app.setOrganizationName("BuRsTFiRe47")
    app.setApplicationName("MakerWorldTranslator")
    win = MainWindow(QSettings())
    win.show()
    sys.exit(app.exec())
