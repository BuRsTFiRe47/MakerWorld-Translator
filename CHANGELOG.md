# Changelog

TR: Bu proje [Semantic Versioning](https://semver.org/lang/tr/) kullanır.
EN: This project uses [Semantic Versioning](https://semver.org/).

## [2.0.0] - 2026-11-01

### TR — Değişenler
- Arayüz **CustomTkinter'dan PySide6'ya (Qt)** taşındı. Arka plan işlemi artık Qt sinyalleriyle arayüze güvenli şekilde bağlanıyor.
- Kaynak dil artık sadece Çince değil: **Latin olmayan Asya yazıları** desteklenir — Çince, Japonca, Korece, Tayca, Hintçe, Bengalce, Pencapça, Gucaratça, Tamilce, Telugu, Kannada, Malayalam, Sinhala, Lao, Birmanca, Kmerce, Arapça/Farsça, İbranice. Varsayılan "Otomatik" modda isim bazında dil tahmini yapılır (kana → Japonca, hangul → Korece, han → Çince).
- Hedef dillere **Fransızca** eklendi (TR / EN / DE / ES / FR). Program arayüz dili de aynı beş dil.
- Koyu tema varsayılan; seçilen dil, tema, kaynak ve hedef dil bir sonraki açılış için hatırlanır.
- Windows'ta bayrak emojileri harf çifti gibi göründüğü için orada sadece dilin kendi adı (Türkçe, English, Deutsch...) gösterilir; macOS'ta bayrak da görünür.

### TR — Eklenenler
- **Durdur** butonu ve **ilerleme çubuğu**.
- Klasörü pencereye **sürükle-bırak** ile seçme.
- **Çakışma koruması:** hedef isim zaten varsa `isim (2)` eklenir; mevcut dosyanın üzerine asla yazılmaz (önceki sürümde macOS/Linux'ta üzerine yazılabiliyordu).
- Geçersiz karakter, Windows ayrılmış isimleri (CON, NUL...), sondaki nokta/boşluk ve çok uzun isimler için temizleme.
- Ağ hatalarında otomatik yeniden deneme ve aynı ismi tekrar çevirmemek için önbellek.
- GUI'den bağımsız çekirdek mantık için **birim testleri** ve CI'da otomatik test adımı.

### EN — Changed
- UI moved from **CustomTkinter to PySide6 (Qt)**. The background job now talks to the UI through Qt signals (thread-safe).
- Source language is no longer Chinese-only: **non-Latin Asian scripts** are supported — Chinese, Japanese, Korean, Thai, Hindi, Bengali, Punjabi, Gujarati, Tamil, Telugu, Kannada, Malayalam, Sinhala, Lao, Burmese, Khmer, Arabic/Persian, Hebrew. The default "Auto" mode guesses the language per name (kana → Japanese, hangul → Korean, han → Chinese).
- **French** added to the target languages (TR / EN / DE / ES / FR). The program UI language offers the same five.
- Dark theme is the default; chosen language, theme, source and target are remembered for the next launch.
- Flag emoji render as letter pairs on Windows, so there only the language's own name is shown (Türkçe, English, Deutsch...); on macOS the flag is shown too.

### EN — Added
- **Stop** button and **progress bar**.
- Pick a folder by **drag & drop** onto the window.
- **Collision protection:** if the target name exists, ` (2)` is appended; an existing file is never overwritten (the previous version could overwrite on macOS/Linux).
- Sanitising for invalid characters, Windows reserved names (CON, NUL...), trailing dots/spaces and overly long names.
- Automatic retry on network errors and a cache so identical names aren't translated twice.
- **Unit tests** for the GUI-independent core logic, plus an automatic test step in CI.

---

## [1.5.0] - 2026-08-13

### TR — Eklenenler
- Program arayüz diline **Almanca** ve **İspanyolca** eklendi (TR / EN / DE / ES).
- Dosya/klasör çeviri hedef diline de **Almanca** ve **İspanyolca** eklendi.
- Dil seçimi dropdown yerine **bayrak + kod** gösteren buton grubuna çevrildi.
- Pencere başlığında sürüm numarası gösteriliyor.

### EN — Added
- **German** and **Spanish** added to the program UI language (TR / EN / DE / ES).
- **German** and **Spanish** added to the file/folder translation target language.
- Language pickers switched from a dropdown to a **flag + code** button group.
- Window title now shows the version number.

---

## [1.0.0] - 2026-08-13

### TR — İlk Sürüm
- MakerWorld dosya/klasör isimlerindeki Çince karakterleri İngilizce veya Türkçe'ye toplu çeviren masaüstü uygulaması.
- Dark/Light mod, alt klasör tarama (opsiyonel), klasör ismi çevirisi (opsiyonel), Dry Run modu.
- Program arayüzü Türkçe/İngilizce.
- Windows (.exe) ve macOS Apple Silicon (.app) için PyInstaller derleme desteği.
- GitHub Actions ile otomatik derleme ve Release oluşturma.

### EN — Initial Release
- Desktop app that bulk-translates Chinese characters in MakerWorld file/folder names into English or Turkish.
- Dark/Light mode, optional subfolder scan, optional folder-name translation, Dry Run mode.
- Turkish/English UI.
- PyInstaller build support for Windows (.exe) and macOS Apple Silicon (.app).
- Automatic build + Release creation via GitHub Actions.
