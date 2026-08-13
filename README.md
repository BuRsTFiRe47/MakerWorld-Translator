# MakerWorld File Translator

🇹🇷 MakerWorld'den (ve benzeri kaynaklardan) indirilen dosya/klasörlerdeki **Çince isimleri** otomatik olarak **İngilizce** veya **Türkçe**'ye çeviren, karanlık/aydınlık temalı, çift dilli (TR/EN) masaüstü uygulaması.

🇬🇧 A desktop app that automatically translates **Chinese file/folder names** (e.g. from MakerWorld downloads) into **English** or **Turkish**, with a dark/light theme and a bilingual (TR/EN) interface.

---

## Özellikler / Features

| TR | EN |
|---|---|
| Modern GUI (CustomTkinter) | Modern GUI (CustomTkinter) |
| Dark / Light Mode (sağ üstteki anahtar) | Dark / Light Mode (switch, top right) |
| Program Dili: 🇹🇷 TR / 🇬🇧 EN / 🇩🇪 DE / 🇪🇸 ES — bayrak+kod butonlarıyla seçim | Program language: 🇹🇷 TR / 🇬🇧 EN / 🇩🇪 DE / 🇪🇸 ES — picked via flag+code buttons |
| Alt Klasör Tarama (opsiyonel) | Recursive subfolder scan (optional) |
| Klasör İsimlerini de Çevirme (opsiyonel) | Also translate folder names (optional) |
| Dry Run — hiçbir şeyi değiştirmeden önizleme | Dry Run — preview changes without renaming anything |
| Çeviri Yönü: Çince → TR / EN / DE / ES — bayrak+kod butonlarıyla seçim | Translation direction: Chinese → TR / EN / DE / ES — picked via flag+code buttons |
| Çapraz Platform: Windows (.exe) ve macOS Apple Silicon (.app, native ARM) | Cross-platform: Windows (.exe) and macOS Apple Silicon (.app, native ARM) |

🇹🇷 **Not:** Dil seçim butonlarındaki bayrak+kod kombinasyonu, o dili bilmeyen birinin bile arayüzü/kendi dilini bulabilmesi için tasarlandı. (Windows'ta bazı sistem yazı tiplerinde bayrak emojisi düz harf çifti olarak görünebilir — bu yüzden kod da yanına eklendi.)
🇬🇧 **Note:** The flag+code combo on the language buttons is designed so even someone who doesn't read the language can find their own. (On Windows, some system fonts render flag emoji as plain letter pairs — the code is included alongside it for that reason.)

---

## Kurulum (Geliştirme) / Setup (Development)

Python 3.10+ gereklidir. / Requires Python 3.10+.

```bash
git clone https://github.com/BuRsTFiRe47/MakerWorld-Translator.git
cd MakerWorld-Translator
pip install -r requirements.txt
python main.py
```

---

## Uygulamayı Elle Derleme / Manual Build

🇹🇷 Kullanıcıların Python kurmadan çalıştırabilmesi için PyInstaller ile derleyin:
🇬🇧 Build with PyInstaller so end users can run it without installing Python:

```bash
pip install pyinstaller
```

**Windows (.exe):**
```bash
pyinstaller --noconfirm --onedir --windowed --name "MakerWorldTranslator" main.py
```
🇹🇷 Çıktı: `dist/MakerWorldTranslator/MakerWorldTranslator.exe`
🇬🇧 Output: `dist/MakerWorldTranslator/MakerWorldTranslator.exe`

**macOS Apple Silicon (.app):**
```bash
pyinstaller --noconfirm --onedir --windowed --name "MakerWorldTranslator" main.py
```
🇹🇷 Apple Silicon (M1/M2/M3/M4) üzerinde derlediğiniz için doğrudan ARM mimarisine native olarak çalışır. Çıktı: `dist/MakerWorldTranslator.app`
🇬🇧 Building on Apple Silicon (M1/M2/M3/M4) produces a native ARM build. Output: `dist/MakerWorldTranslator.app`

---

## Otomatik Derleme ve Release (GitHub Actions)

🇹🇷 Repoda `.github/workflows/build.yml` hazır geliyor. Bir sürüm etiketi (`v1.0.0` gibi) push ettiğinizde, GitHub Actions:
1. Windows ve Apple Silicon macOS için otomatik derleme yapar,
2. İkisini de zip'ler,
3. Otomatik olarak bir **GitHub Release** oluşturup bu zip'leri o release'e asset olarak ekler.

Yani release sayfasına gidip "Releases" altında derlenmiş `.exe` ve `.app` dosyalarını doğrudan indirilebilir halde bulursunuz — elle hiçbir şey yapmanıza gerek kalmaz.

🇬🇧 The repo ships with `.github/workflows/build.yml`. When you push a version tag (e.g. `v1.0.0`), GitHub Actions:
1. Automatically builds for Windows and Apple Silicon macOS,
2. Zips both builds,
3. Automatically creates a **GitHub Release** and attaches both zips as downloadable assets.

So under the "Releases" tab you'll find ready-to-download `.exe` and `.app` builds — no manual steps needed.

```bash
git tag v1.0.0
git push origin v1.0.0
```

Manuel olarak da tetikleyebilirsiniz: repo → **Actions** sekmesi → **Build Executables** → **Run workflow**.
You can also trigger it manually: repo → **Actions** tab → **Build Executables** → **Run workflow**.

---

## Projeyi Güncelleme / Updating the Project

🇹🇷 Koda bir değişiklik yaptıktan sonra GitHub'a göndermek için:

```bash
git add .
git commit -m "Değişikliğin kısa açıklaması"
git push
```

Yeni bir sürüm (ve otomatik derlenmiş .exe/.app) yayınlamak isterseniz, önce değişikliği push edin, sonra yeni bir etiket oluşturup gönderin:

```bash
git tag v1.1.0
git push origin v1.1.0
```

(Sürüm numarasını her seferinde bir öncekinden büyük olacak şekilde artırın: v1.0.0 → v1.1.0 → v1.2.0 gibi.)

🇬🇧 After making a code change, to push it to GitHub:

```bash
git add .
git commit -m "Short description of the change"
git push
```

To publish a new version (with an automatically built .exe/.app), push the change first, then create and push a new tag:

```bash
git tag v1.1.0
git push origin v1.1.0
```

(Always bump the version number higher than the previous one: v1.0.0 → v1.1.0 → v1.2.0, etc.)

---

## Sürüm Geçmişi / Changelog

🇹🇷 Tüm değişiklikler [`CHANGELOG.md`](CHANGELOG.md) dosyasında listelenir. Güncel sürüm: **v1.5.0**.
🇬🇧 All changes are listed in [`CHANGELOG.md`](CHANGELOG.md). Current version: **v1.5.0**.

---

## Lisans / License

🇹🇷 Bu projeyi dilediğiniz gibi kullanabilir, değiştirebilirsiniz.
🇬🇧 Feel free to use and modify this project as you like.
