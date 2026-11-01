"""GUI-independent core logic / GUI'den bağımsız çekirdek mantık.

TR: Yazı (script) tespiti, isim temizleme, çakışmasız yeniden adlandırma ve
    Google Translate arka ucu burada. Hiçbir Qt bağımlılığı yoktur, bu yüzden
    ağsız ve GUI'siz test edilebilir.
EN: Script detection, name sanitising, collision-safe renaming and the Google
    Translate backend live here. No Qt dependency, so it is testable without
    network or GUI.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from typing import Callable, Optional

# ---------------------------------------------------------------------------
# TR: Yazı aralıkları (Unicode)  /  EN: Unicode script ranges
# ---------------------------------------------------------------------------
HAN = ((0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF), (0x20000, 0x2A6DF))
KANA = ((0x3040, 0x30FF), (0x31F0, 0x31FF), (0xFF66, 0xFF9F))
HANGUL = ((0x1100, 0x11FF), (0x3130, 0x318F), (0xA960, 0xA97F), (0xAC00, 0xD7AF), (0xD7B0, 0xD7FF))


@dataclass(frozen=True)
class SourceLanguage:
    code: str       # Google Translate source code / kaynak dil kodu
    native: str     # name in its own script / kendi yazısıyla adı
    english: str
    ranges: tuple


# TR: Latin olmayan Asya yazıları. Kiril/Gürcü/Ermeni kapsam dışı.
# EN: Non-Latin Asian scripts. Cyrillic/Georgian/Armenian are out of scope.
SOURCE_LANGUAGES: tuple[SourceLanguage, ...] = (
    SourceLanguage("zh-CN", "中文", "Chinese", HAN),
    SourceLanguage("ja", "日本語", "Japanese", HAN + KANA),
    SourceLanguage("ko", "한국어", "Korean", HANGUL),
    SourceLanguage("th", "ไทย", "Thai", ((0x0E00, 0x0E7F),)),
    SourceLanguage("hi", "हिन्दी", "Hindi", ((0x0900, 0x097F),)),
    SourceLanguage("bn", "বাংলা", "Bengali", ((0x0980, 0x09FF),)),
    SourceLanguage("pa", "ਪੰਜਾਬੀ", "Punjabi", ((0x0A00, 0x0A7F),)),
    SourceLanguage("gu", "ગુજરાતી", "Gujarati", ((0x0A80, 0x0AFF),)),
    SourceLanguage("ta", "தமிழ்", "Tamil", ((0x0B80, 0x0BFF),)),
    SourceLanguage("te", "తెలుగు", "Telugu", ((0x0C00, 0x0C7F),)),
    SourceLanguage("kn", "ಕನ್ನಡ", "Kannada", ((0x0C80, 0x0CFF),)),
    SourceLanguage("ml", "മലയാളം", "Malayalam", ((0x0D00, 0x0D7F),)),
    SourceLanguage("si", "සිංහල", "Sinhala", ((0x0D80, 0x0DFF),)),
    SourceLanguage("lo", "ລາວ", "Lao", ((0x0E80, 0x0EFF),)),
    SourceLanguage("my", "မြန်မာ", "Burmese", ((0x1000, 0x109F),)),
    SourceLanguage("km", "ខ្មែរ", "Khmer", ((0x1780, 0x17FF),)),
    SourceLanguage(
        "ar", "العربية", "Arabic / Persian",
        ((0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)),
    ),
    SourceLanguage("iw", "עברית", "Hebrew", ((0x0590, 0x05FF), (0xFB1D, 0xFB4F))),
)

ALL_RANGES = tuple(r for lang in SOURCE_LANGUAGES for r in lang.ranges)
TARGET_CODES = ("tr", "en", "de", "es", "fr")


def contains_script(text: str, ranges: tuple) -> bool:
    for ch in text:
        cp = ord(ch)
        for lo, hi in ranges:
            if lo <= cp <= hi:
                return True
    return False


def detect_source(text: str) -> str:
    """TR: Otomatik modda isim bazında kaynak dil tahmini. Belirsizse 'auto'.
    EN: Per-name source guess in auto mode. Falls back to 'auto'."""
    if contains_script(text, KANA):
        return "ja"
    if contains_script(text, HANGUL):
        return "ko"
    if contains_script(text, HAN):
        return "zh-CN"
    return "auto"


# ---------------------------------------------------------------------------
# TR: İsim temizleme  /  EN: Name sanitising
# ---------------------------------------------------------------------------
INVALID_CHARS = '<>:"/\\|?*'
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
MAX_NAME_LEN = 120


def clean_name(name: str) -> str:
    for ch in INVALID_CHARS:
        name = name.replace(ch, "")
    name = _CONTROL.sub("", name)
    name = re.sub(r"\s+", " ", name).strip().rstrip(". ")
    if len(name) > MAX_NAME_LEN:
        name = name[:MAX_NAME_LEN].rstrip()
    if name.upper() in _RESERVED:
        name += "_"
    return name


# ---------------------------------------------------------------------------
# TR: Arka uç  /  EN: Backend
# ---------------------------------------------------------------------------
class GoogleBackend:
    """deep-translator üstünde önbellekli, yeniden denemeli çeviri.
    Cached, retrying translation on top of deep-translator."""

    def __init__(self, retries: int = 2, delay: float = 0.8):
        self.retries = retries
        self.delay = delay
        self._cache: dict[tuple[str, str, str], str] = {}

    def translate(self, text: str, source: str, target: str) -> str:
        key = (text, source, target)
        if key in self._cache:
            return self._cache[key]
        from deep_translator import GoogleTranslator

        last: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                result = GoogleTranslator(source=source, target=target).translate(text) or ""
                self._cache[key] = result
                return result
            except Exception as exc:  # network, rate limit, ...
                last = exc
                if attempt < self.retries:
                    time.sleep(self.delay * (attempt + 1))
        assert last is not None
        raise last


# ---------------------------------------------------------------------------
# TR: Olaylar ve özet  /  EN: Events and summary
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Event:
    kind: str          # renamed | dry | unchanged | error | none | stopped
    old: str = ""
    new: str = ""
    detail: str = ""


@dataclass
class Summary:
    total: int = 0
    renamed: int = 0   # dry-run'da "yeniden adlandırılacak" sayısı / would-rename count in dry run
    unchanged: int = 0
    errors: int = 0
    stopped: bool = False


def collect(base: str, recursive: bool, include_folders: bool) -> tuple[list[str], list[str]]:
    """TR: Dosya ve klasör yollarını toplar; klasörler en derinden başlayacak şekilde sıralanır.
    EN: Collects file and folder paths; folders sorted deepest-first."""
    files: list[str] = []
    folders: list[str] = []
    if recursive:
        for root, dirs, fs in os.walk(base):
            files += [os.path.join(root, f) for f in fs]
            if include_folders:
                folders += [os.path.join(root, d) for d in dirs]
    else:
        with os.scandir(base) as it:
            for entry in it:
                if entry.is_file():
                    files.append(entry.path)
                elif entry.is_dir() and include_folders:
                    folders.append(entry.path)
    folders.sort(key=lambda p: p.count(os.sep), reverse=True)
    return files, folders


def _key(path: str) -> str:
    return os.path.normcase(path).casefold()


def unique_name(directory: str, stem: str, ext: str, taken: set[str], old_path: str) -> str:
    """TR: Hedefte aynı isim varsa ' (2)', ' (3)'... ekler. Üzerine yazmayı önler.
    EN: Appends ' (2)', ' (3)'... when the target exists. Prevents overwriting."""
    candidate = stem + ext
    n = 2
    while True:
        full = os.path.join(directory, candidate)
        k = _key(full)
        exists = os.path.exists(full) and k != _key(old_path)
        if k not in taken and not exists:
            taken.add(k)
            return candidate
        candidate = f"{stem} ({n}){ext}"
        n += 1


TranslateFn = Callable[[str, str, str], str]


def run(
    base_folder: str,
    *,
    source: Optional[SourceLanguage],
    target_code: str,
    recursive: bool,
    include_folders: bool,
    dry_run: bool,
    translate: TranslateFn,
    emit: Callable[[Event], None],
    should_stop: Callable[[], bool] = lambda: False,
    progress: Callable[[int, int], None] = lambda done, total: None,
) -> Summary:
    """TR: Ana iş. source=None → otomatik (Latin olmayan tüm Asya yazıları).
    EN: Main job. source=None → auto (all non-Latin Asian scripts)."""
    ranges = source.ranges if source else ALL_RANGES
    files, folders = collect(base_folder, recursive, include_folders)

    items: list[tuple[str, bool]] = [(p, False) for p in files if contains_script(os.path.basename(p), ranges)]
    items += [(p, True) for p in folders if contains_script(os.path.basename(p), ranges)]

    summary = Summary(total=len(items))
    if not items:
        emit(Event("none"))
        return summary

    taken: set[str] = set()
    progress(0, len(items))
    for i, (path, is_dir) in enumerate(items, 1):
        if should_stop():
            summary.stopped = True
            emit(Event("stopped"))
            break
        directory, base = os.path.split(path)
        stem, ext = (base, "") if is_dir else os.path.splitext(base)
        src = source.code if source else detect_source(stem)
        try:
            translated = clean_name(translate(stem, src, target_code))
            if not translated:
                raise ValueError("empty translation")
            new_name = unique_name(directory, translated, ext, taken, path)
            if new_name == base:
                summary.unchanged += 1
                emit(Event("unchanged", base))
            elif dry_run:
                summary.renamed += 1
                emit(Event("dry", base, new_name))
            else:
                os.rename(path, os.path.join(directory, new_name))
                summary.renamed += 1
                emit(Event("renamed", base, new_name))
        except Exception as exc:
            summary.errors += 1
            emit(Event("error", base, detail=str(exc)))
        progress(i, len(items))
    return summary
