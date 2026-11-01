# MakerWorld File Translator

🇹🇷 MakerWorld'den (ve benzeri kaynaklardan) indirilen dosya/klasörlerdeki **Latin olmayan Asya yazısıyla yazılmış isimleri** (Çince, Japonca, Korece, Tayca, Hintçe...) otomatik olarak **Türkçe, İngilizce, Almanca, İspanyolca veya Fransızca**'ya çevirip yeniden adlandıran, koyu/açık temalı, çok dilli masaüstü uygulaması (PySide6).

🇬🇧 A multilingual desktop app (PySide6) that translates and renames files/folders whose names are written in **non-Latin Asian scripts** (Chinese, Japanese, Korean, Thai, Hindi, ...) — e.g. MakerWorld downloads — into **Turkish, English, German, Spanish or French**, with dark/light themes.

---

## Özellikler / Features

| TR | EN |
|---|---|
| Modern Qt arayüzü (PySide6), **koyu tema varsayılan** | Modern Qt UI (PySide6), **dark theme by default** |
| Kaynak dil: Otomatik veya tek tek seçim (aşağıdaki tablo) | Source language: Auto or pick one (table below) |
| Hedef dil: 🇹🇷 TR / 🇬🇧 EN / 🇩🇪 DE / 🇪🇸 ES / 🇫🇷 FR | Target language: 🇹🇷 TR / 🇬🇧 EN / 🇩🇪 DE / 🇪🇸 ES / 🇫🇷 FR |
| Program dili aynı beş dil; seçimler hatırlanır | Program language offers the same five; choices are remembered |
| Alt klasör tarama (opsiyonel) | Recursive subfolder scan (optional) |
| Klasör isimlerini de çevirme (opsiyonel) | Also translate folder names (optional) |
| **Dry Run** — hiçbir şeyi değiştirmeden önizleme | **Dry Run** — preview without renaming anything |
| Durdur butonu, ilerleme çubuğu, sürükle-bırak klasör seçimi | Stop button, progress bar, drag & drop folder selection |
| **Çakışma koruması:** aynı isim varsa `isim (2)`; hiçbir şeyin üzerine yazılmaz | **Collision protection:** `name (2)` if the name exists; nothing is ever overwritten |
| Windows (.exe) ve macOS Apple Silicon (.app) | Windows (.exe) and macOS Apple Silicon (.app) |

### Desteklenen kaynak yazılar / Supported source scripts

| | |
|---|---|
| 中文 Chinese · 日本語 Japanese · 한국어 Korean | ไทย Thai · ລາວ Lao · မြန်မာ Burmese · ខ្មែរ Khmer |
| हिन्दी Hindi · বাংলা Bengali · ਪੰਜਾਬੀ Punjabi · ગુજરાતી Gujarati | தமிழ் Tamil · తెలుగు Telugu · ಕನ್ನಡ Kannada · മലയാളം Malayalam · සිංහල Sinhala |
| العربية Arabic / Persian · עברית Hebrew | |

🇹🇷 **Otomatik** modda her isim için dil tahmin edilir: kana → Japonca, hangul → Korece, han → Çince, diğerleri → Google'ın otomatik algılaması. Yalnızca Japonca kanji içeren (kana'sız) isimler Çince sanılabilir; bu durumda kaynak dili elle "日本語" seçin.
🇬🇧 In **Auto** mode the language is guessed per name: kana → Japanese, hangul → Korean, han → Chinese, anything else → Google's auto-detection. Japanese names made only of kanji (no kana) may be taken for Chinese; pick "日本語" manually in that case.

🇹🇷 **Not:** Windows'ta bayrak emojileri harf çifti gibi görünür, bu yüzden orada dil düğmelerinde yalnızca dilin kendi adı yazar.
🇬🇧 **Note:** On Windows flag emoji render as letter pairs, so there the language buttons show only the language's own name.

---

## Kurulum (Geliştirme) / Setup (Development)

Python 3.10+ gereklidir. / Requires Python 3.10+.

```bash
git clone https://github.com/BuRsTFiRe47/MakerWorld-Translator.git
cd MakerWorld-Translator
pip install -r requirements.txt
python main.py
```

Testler / Tests (internet ve GUI gerekmez / no network or GUI needed):

```bash
python -m unittest discover -s tests -v
```

🇹🇷 Çeviri için internet bağlantısı gerekir (Google Translate, `deep-translator` üzerinden).
🇬🇧 An internet connection is required for translation (Google Translate via `deep-translator`).

---

## Proje Yapısı / Project Layout

```
MakerWorld-Translator/
├── main.py                      # giriş noktası / entry point
├── makerworld_translator/
│   ├── core.py                  # yazı tespiti, yeniden adlandırma, çeviri arka ucu / core logic
│   ├── gui.py                   # PySide6 arayüzü / PySide6 UI
│   └── i18n.py                  # TR/EN/DE/ES/FR metinler / UI strings
├── tests/test_core.py
├── requirements.txt
├── CHANGELOG.md
└── .github/workflows/build.yml  # otomatik derleme + release / auto build + release
```

---

## Uygulamayı Elle Derleme / Manual Build

🇹🇷 Kullanıcıların Python kurmadan çalıştırabilmesi için PyInstaller ile derleyin:
🇬🇧 Build with PyInstaller so end users can run it without installing Python:

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --onedir --windowed --name "MakerWorldTranslator" main.py
```

🇹🇷 Çıktı — Windows: `dist/MakerWorldTranslator/MakerWorldTranslator.exe`, macOS: `dist/MakerWorldTranslator.app`. Apple Silicon üzerinde derlerseniz native ARM çalışır. Qt dahil olduğu için çıktı yüzlerce MB olabilir; bu normaldir.
🇬🇧 Output — Windows: `dist/MakerWorldTranslator/MakerWorldTranslator.exe`, macOS: `dist/MakerWorldTranslator.app`. Building on Apple Silicon gives a native ARM app. Because Qt is bundled, the output can be hundreds of MB; that is expected.

---

## Otomatik Derleme ve Release (GitHub Actions)

🇹🇷 Bir sürüm etiketi (`v2.0.0` gibi) push ettiğinizde GitHub Actions:
1. Birim testlerini çalıştırır,
2. Windows ve Apple Silicon macOS için derler ve zip'ler,
3. Otomatik bir **GitHub Release** oluşturup zip'leri indirilebilir dosya olarak ekler.

🇬🇧 When you push a version tag (e.g. `v2.0.0`), GitHub Actions:
1. Runs the unit tests,
2. Builds and zips for Windows and Apple Silicon macOS,
3. Automatically creates a **GitHub Release** with both zips attached.

```bash
git tag v2.0.0
git push origin v2.0.0
```

🇹🇷 Manuel tetikleme: repo → **Actions** → **Build Executables** → **Run workflow** (derler, release oluşturmaz).
🇬🇧 Manual run: repo → **Actions** → **Build Executables** → **Run workflow** (builds only, no release).

### İlk açılışta uyarı / First-launch warnings

🇹🇷 Uygulama imzasız olduğundan Windows SmartScreen "Daha fazla bilgi → Yine de çalıştır" diyebilir; macOS'ta uygulamaya **sağ tık → Aç** ile ilk kez açın.
🇬🇧 The app is unsigned, so Windows SmartScreen may show "More info → Run anyway"; on macOS open it the first time via **right-click → Open**.

---

## Projeyi Güncelleme / Updating the Project

```bash
git add .
git commit -m "Short description / Kısa açıklama"
git push
```

🇹🇷 Yeni sürüm yayınlamak için değişikliği push ettikten sonra daha büyük bir etiket gönderin (v2.0.0 → v2.0.1 hata düzeltme, v2.1.0 yeni özellik, v3.0.0 uyumsuz değişiklik) ve `CHANGELOG.md` ile `makerworld_translator/__init__.py` içindeki `__version__` değerini güncelleyin.
🇬🇧 To publish a new version, push your change and then push a higher tag (v2.0.0 → v2.0.1 bug fix, v2.1.0 new feature, v3.0.0 breaking change), and update `CHANGELOG.md` and `__version__` in `makerworld_translator/__init__.py`.

---

## Sürüm Geçmişi / Changelog

🇹🇷 Tüm değişiklikler [`CHANGELOG.md`](CHANGELOG.md) dosyasında. Güncel sürüm: **v2.0.0**.
🇬🇧 All changes are in [`CHANGELOG.md`](CHANGELOG.md). Current version: **v2.0.0**.

---

## Lisans / License

🇹🇷 Bu projeyi dilediğiniz gibi kullanabilir, değiştirebilirsiniz.
🇬🇧 Feel free to use and modify this project as you like.
