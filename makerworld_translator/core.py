"""GUI-independent core logic / GUI'den bağımsız çekirdek mantık.

TR: Yazı (script) tespiti, isim temizleme, çakışmasız yeniden adlandırma ve
    Google Translate arka ucu burada. Hiçbir Qt bağımlılığı yoktur, bu yüzden
    ağsız ve GUI'siz test edilebilir.
EN: Script detection, name sanitising, collision-safe renaming and the Google
    Translate backend live here. No Qt dependency, so it is testable without
    network or GUI.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
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
# TR: Çeviri motorları  /  EN: Translation engines
#
# TR: Üç motor, hepsi API anahtarsız: Google (toplu), Microsoft (Edge çeviri uç
#     noktası, toplu), MyMemory (tek tek). "Otomatik" modda sırayla denenir;
#     biri istek sınırına takılırsa sonrakine geçilir.
# EN: Three engines, none needs an API key: Google (batched), Microsoft (Edge
#     translate endpoint, batched), MyMemory (one by one). "Auto" tries them in
#     that order and fails over to the next when one hits its rate limit.
# ---------------------------------------------------------------------------
class FatalTranslateError(Exception):
    """TR: Hiçbir motor kullanılamıyor (limit veya bağlantı). EN: No engine is usable (limit or connection)."""


class RateLimited(Exception):
    """TR: Motor "çok fazla istek / engellendi" dedi. retry=False: beklemek işe yaramaz (günlük kota).
    EN: Engine said "too many requests / blocked". retry=False: waiting will not help (daily quota)."""

    def __init__(self, message: str = "", retry: bool = True):
        super().__init__(message)
        self.retry = retry


class BatchMismatch(Exception):
    """TR: Toplu yanıt isteğe uymadı; tek tek denenecek. EN: Batch reply did not line up; retry one by one."""


_SSL_CONTEXT = None


def _ssl_context():
    """TR: Derlenmiş (PyInstaller) uygulamalarda, özellikle macOS'ta, sistem sertifika yolu boş olabilir;
        bu yüzden certifi'nin paketini kullanırız.
    EN: In frozen (PyInstaller) apps, especially on macOS, the default CA path can be empty,
        so we use certifi's bundle."""
    global _SSL_CONTEXT
    if _SSL_CONTEXT is None:
        import ssl
        try:
            import certifi
            _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            _SSL_CONTEXT = ssl.create_default_context()
    return _SSL_CONTEXT


def http_request(url, data=None, headers=None, method=None, timeout=15):
    """TR: Standart kütüphane ile HTTP. (durum_kodu, gövde) döner. EN: Stdlib HTTP. Returns (status, body)."""
    hdrs = {"User-Agent": "Mozilla/5.0 (MakerWorldTranslator)"}
    hdrs.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


class Engine:
    name = "?"
    max_batch = 1        # tek istekte en fazla kaç isim / names per request
    max_chars = 600      # tek istekte en fazla karakter / characters per request
    min_interval = 0.4   # istekler arası saniye / seconds between requests

    def __init__(self, http=http_request):
        self.http = http

    def translate_many(self, texts: list, source: str, target: str) -> list:
        raise NotImplementedError


class GoogleEngine(Engine):
    """translate.googleapis.com (gtx). İsimler satır sonuyla birleştirilip tek istekte gider.
    Names are joined with newlines and sent in a single request."""

    name = "Google"
    max_batch = 25
    min_interval = 0.5
    URL = "https://translate.googleapis.com/translate_a/single"

    def translate_many(self, texts, source, target):
        query = urllib.parse.urlencode(
            {"client": "gtx", "sl": source, "tl": target, "dt": "t", "q": "\n".join(texts)}
        )
        status, body = self.http(f"{self.URL}?{query}")
        if status in (403, 429, 503) or "unusual traffic" in body.lower():
            raise RateLimited(f"Google: HTTP {status}")
        if status != 200:
            raise RuntimeError(f"Google: HTTP {status}")
        try:
            data = json.loads(body)
            joined = "".join(seg[0] for seg in data[0] if seg and seg[0])
        except (ValueError, TypeError, IndexError, KeyError):
            raise RuntimeError("Google: unexpected response")
        if len(texts) == 1:
            return [joined.strip()]
        parts = [p.strip() for p in joined.strip("\n").split("\n")]
        if len(parts) != len(texts):
            raise BatchMismatch()
        return parts


class MicrosoftEngine(Engine):
    """Edge tarayıcısının çeviri uç noktası; JWT'yi kendisi alır, toplu JSON destekler.
    The Edge browser's translate endpoint; fetches its own JWT, supports JSON batches."""

    name = "Microsoft"
    max_batch = 40
    min_interval = 0.4
    AUTH_URL = "https://edge.microsoft.com/translate/auth"
    API_URL = "https://api-edge.cognitive.microsofttranslator.com/translate"
    LANG = {"zh-CN": "zh-Hans", "iw": "he"}

    def __init__(self, http=http_request, clock=time.monotonic):
        super().__init__(http)
        self._clock = clock
        self._token = ""
        self._token_at = 0.0

    def _get_token(self, force=False):
        if force or not self._token or self._clock() - self._token_at > 480:
            status, body = self.http(self.AUTH_URL)
            if status in (403, 429):
                raise RateLimited(f"Microsoft: auth HTTP {status}")
            if status != 200 or not body.strip():
                raise RuntimeError(f"Microsoft: auth HTTP {status}")
            self._token, self._token_at = body.strip(), self._clock()
        return self._token

    def translate_many(self, texts, source, target):
        params = {"api-version": "3.0", "to": self.LANG.get(target, target)}
        if source != "auto":
            params["from"] = self.LANG.get(source, source)
        url = f"{self.API_URL}?{urllib.parse.urlencode(params)}"
        payload = json.dumps([{"Text": t} for t in texts]).encode("utf-8")
        status, body = 0, ""
        for attempt in (0, 1):   # TR: 401 → jetonu yenile, bir kez daha dene / EN: 401 → refresh token once
            status, body = self.http(
                url, data=payload, method="POST",
                headers={"Authorization": f"Bearer {self._get_token(force=attempt == 1)}",
                         "Content-Type": "application/json"},
            )
            if status != 401:
                break
        if status in (403, 429):
            raise RateLimited(f"Microsoft: HTTP {status}")
        if status != 200:
            raise RuntimeError(f"Microsoft: HTTP {status}")
        try:
            out = [item["translations"][0]["text"] for item in json.loads(body)]
        except (ValueError, TypeError, IndexError, KeyError):
            raise RuntimeError("Microsoft: unexpected response")
        if len(out) != len(texts):
            raise BatchMismatch()
        return out


class MyMemoryEngine(Engine):
    """api.mymemory.translated.net — anonim ~5000 karakter/gün; e-posta verilirse ~50000.
    Anonymous ~5000 chars/day; ~50000 when an email is supplied."""

    name = "MyMemory"
    max_batch = 1
    min_interval = 0.6
    URL = "https://api.mymemory.translated.net/get"

    def __init__(self, http=http_request, email: str = ""):
        super().__init__(http)
        self.email = email

    def translate_many(self, texts, source, target):
        (text,) = texts
        if len(text.encode("utf-8")) > 480:
            raise ValueError("name too long for MyMemory")
        src = "Autodetect" if source == "auto" else {"iw": "he"}.get(source, source)
        params = {"q": text, "langpair": f"{src}|{target}"}
        if self.email:
            params["de"] = self.email
        status, body = self.http(f"{self.URL}?{urllib.parse.urlencode(params)}")
        if status == 429:
            raise RateLimited("MyMemory: HTTP 429", retry=False)
        if status != 200:
            raise RuntimeError(f"MyMemory: HTTP {status}")
        try:
            data = json.loads(body)
            translated = data["responseData"]["translatedText"]
        except (ValueError, TypeError, KeyError):
            raise RuntimeError("MyMemory: unexpected response")
        if "MYMEMORY WARNING" in str(translated).upper() or str(data.get("responseStatus")) == "429":
            raise RateLimited(f"MyMemory: {translated}", retry=False)
        return [translated]


class TranslatorChain:
    """TR: Motorları sırayla dener, hız sınırlar, önbellekler, toplu isteği (prefetch) yönetir.
        Motor limite takılırsa kısa bekleyip yeniden dener, olmazsa sonraki motora geçer.
    EN: Tries engines in order, throttles, caches and runs batched prefetch. On a rate limit it
        waits briefly and retries, then fails over to the next engine."""

    def __init__(self, engines, *, rate_waits=(3, 8), final_waits=(3, 6, 12, 24, 30),
                 retries: int = 2, delay: float = 0.8):
        if not engines:
            raise ValueError("at least one engine is required")
        self.engines = list(engines)
        self.rate_waits = rate_waits      # başka motor varken / while another engine is left
        self.final_waits = final_waits    # son motorda / on the last engine
        self.retries = retries
        self.delay = delay
        self.on_wait: Optional[Callable[[str, int], None]] = None
        self.on_switch: Optional[Callable[[str, str], None]] = None
        self.cancelled = False
        self.active = 0
        self._last: dict = {}
        self._cache: dict = {}
        self._last_error = ""

    # --- timing ----------------------------------------------------------
    def _sleep(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while not self.cancelled:
            left = end - time.monotonic()
            if left <= 0:
                return
            time.sleep(min(0.1, left))

    def _throttle(self, engine) -> None:
        wait = self._last.get(engine.name, 0.0) + engine.min_interval - time.monotonic()
        if wait > 0:
            self._sleep(wait)
        self._last[engine.name] = time.monotonic()

    # --- core ------------------------------------------------------------
    def _attempt(self, texts, source, target):
        while True:
            engine = self.engines[self.active]
            if len(texts) > engine.max_batch:
                out: list = []
                for i in range(0, len(texts), engine.max_batch):
                    out += self._attempt(texts[i:i + engine.max_batch], source, target)
                return out
            waits = self.final_waits if self.active == len(self.engines) - 1 else self.rate_waits
            rate_tries = other_tries = 0
            while True:
                if self.cancelled:
                    raise RuntimeError("cancelled")
                self._throttle(engine)
                try:
                    return engine.translate_many(texts, source, target)
                except BatchMismatch:
                    if len(texts) == 1:
                        raise RuntimeError(f"{engine.name}: unexpected response")
                    return [self._attempt([t], source, target)[0] for t in texts]
                except RateLimited as exc:
                    self._last_error = str(exc)
                    if not exc.retry or rate_tries >= len(waits):
                        break
                    wait = waits[rate_tries]
                    rate_tries += 1
                    if self.on_wait:
                        self.on_wait(engine.name, wait)
                    self._sleep(wait)
                except OSError as exc:   # TR: ağ düzeyi hata: motora ulaşılamıyor / EN: network-level: engine unreachable
                    self._last_error = f"{engine.name}: {exc}"
                    if other_tries >= self.retries:
                        break
                    other_tries += 1
                    self._sleep(self.delay * other_tries)
                except Exception:
                    if other_tries >= self.retries:
                        raise
                    other_tries += 1
                    self._sleep(self.delay * other_tries)
            # TR: Bu motor pes etti → sonrakine geç, yoksa işi bırak
            # EN: This engine gave up → fail over, or give up entirely
            if self.active + 1 >= len(self.engines):
                raise FatalTranslateError(self._last_error or "no translation engine available")
            old = engine.name
            self.active += 1
            if self.on_switch:
                self.on_switch(old, self.engines[self.active].name)

    def translate(self, text: str, source: str, target: str) -> str:
        key = (text, source, target)
        if key in self._cache:
            return self._cache[key]
        out = self._attempt([text], source, target)[0]
        self._cache[key] = out
        return out

    def _chunks(self, texts):
        engine = self.engines[self.active]
        chunk: list = []
        size = 0
        for t in texts:
            if chunk and (len(chunk) >= engine.max_batch or size + len(t) > engine.max_chars):
                yield chunk
                chunk, size = [], 0
            chunk.append(t)
            size += len(t)
        if chunk:
            yield chunk

    def prefetch(self, items, target: str) -> None:
        """TR: Tüm isimleri en az sayıda istekle önceden çevirip önbelleğe koyar.
        EN: Translates all names up front in as few requests as possible and caches them."""
        groups: dict = {}
        for text, src in items:
            if (text, src, target) in self._cache:
                continue
            bucket = groups.setdefault(src, [])
            if text not in bucket:
                bucket.append(text)
        for src, texts in groups.items():
            for chunk in self._chunks(texts):
                try:
                    out = self._attempt(chunk, src, target)
                except FatalTranslateError:
                    raise
                except Exception:
                    if self.cancelled:
                        raise
                    continue   # TR: tek tek yol bu isimler için hatayı raporlar / EN: the per-name path will report it
                for t, o in zip(chunk, out):
                    if o:
                        self._cache[(t, src, target)] = o


ENGINE_CHOICES = ("auto", "google", "microsoft", "mymemory")


def build_chain(choice: str = "auto", email: str = "", http=http_request) -> TranslatorChain:
    makers = {
        "google": lambda: GoogleEngine(http),
        "microsoft": lambda: MicrosoftEngine(http),
        "mymemory": lambda: MyMemoryEngine(http, email=email.strip()),
    }
    order = ["google", "microsoft", "mymemory"] if choice == "auto" else [choice]
    return TranslatorChain([makers[k]() for k in order])


# ---------------------------------------------------------------------------
# TR: Olaylar ve özet  /  EN: Events and summary
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Event:
    kind: str          # renamed | dry | unchanged | error | none | stopped | wait | switch | aborted
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
    aborted: bool = False   # istek sınırı yüzünden erken bitti / ended early due to rate limit


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
    prefetch: Optional[Callable[[list], None]] = None,
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

    # TR: Önce tüm isimler toplu çevrilir (az istek = limite takılmaz); döngü önbellekten okur.
    # EN: Translate all names in batches first (few requests = no rate limit); the loop reads the cache.
    if prefetch is not None:
        pairs = []
        for path, is_dir in items:
            b = os.path.basename(path)
            stem = b if is_dir else os.path.splitext(b)[0]
            pairs.append((stem, source.code if source else detect_source(stem)))
        try:
            prefetch(pairs)
        except FatalTranslateError as exc:
            summary.errors += 1
            summary.aborted = True
            emit(Event("error", detail=str(exc)))
            emit(Event("aborted"))
            return summary
        except Exception:
            if should_stop():
                summary.stopped = True
                emit(Event("stopped"))
                return summary
            raise

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
        except FatalTranslateError as exc:
            # TR: Sınır aşıldıysa kalan her dosya için dakikalarca beklemek yerine işi bitir.
            # EN: Rate limit exhausted: end the job instead of waiting minutes per remaining file.
            summary.errors += 1
            summary.aborted = True
            emit(Event("error", base, detail=str(exc)))
            emit(Event("aborted"))
            break
        except Exception as exc:
            if should_stop():   # iptal sırasında fırlayan hata / error raised while cancelling
                summary.stopped = True
                emit(Event("stopped"))
                break
            summary.errors += 1
            emit(Event("error", base, detail=str(exc)))
        progress(i, len(items))
    return summary
