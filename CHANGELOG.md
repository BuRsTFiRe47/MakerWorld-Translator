# Changelog

TR: Bu proje [Semantic Versioning](https://semver.org/lang/tr/) kullanır.
EN: This project uses [Semantic Versioning](https://semver.org/).

## [2.1.0] - 2026-11-02

### TR — Değişenler
- **Çeviri motoru değişti.** v2.0.1'deki yavaşlatma Google'ın istek sınırını yine de aşıyordu, çünkü `deep-translator` Google'ın web arayüzünü kazıyor ve her dosya adı için ayrı istek atıyordu. Artık:
  - İsimler **toplu** çevrilir (tek istekte ~25 isim). 10 dosya = 1 istek.
  - **Üç motor** var: Google, Microsoft (Edge çeviri uç noktası), MyMemory. Hiçbiri API anahtarı istemez.
  - Varsayılan **Otomatik** modda biri istek sınırına takılırsa kısa bekleyip yeniden dener, olmazsa **otomatik olarak sonraki motora geçer** (logda görünür). Motoru elle de seçebilirsiniz.
  - Arayüze **motor seçici** ve isteğe bağlı **MyMemory e-posta** alanı eklendi (günlük limiti ~10 kat artırır). Seçimler hatırlanır.
- `deep-translator` bağımlılığı kaldırıldı; motorlar yalnızca standart kütüphane kullanır (paket boyutu küçüldü).
- Ağ düzeyinde hata (motora ulaşılamıyor) da sonraki motora geçişi tetikler.
- Log mesajları 5 dilde güncellendi. Birim test sayısı 33'e çıktı (sahte HTTP yanıtlarıyla, ağ gerektirmez).

### EN — Changed
- **New translation backend.** The v2.0.1 throttling still tripped Google's limit because `deep-translator` scrapes Google's web UI and sends one request per file name. Now:
  - Names are translated **in batches** (~25 names per request). 10 files = 1 request.
  - **Three engines**: Google, Microsoft (Edge translate endpoint), MyMemory. None needs an API key.
  - In the default **Auto** mode, if one hits its rate limit the app waits briefly, retries, then **fails over to the next engine automatically** (shown in the log). You can also pick an engine manually.
  - New **engine selector** and an optional **MyMemory email** field (raises the daily limit ~10x). Choices are remembered.
- Dropped the `deep-translator` dependency; the engines use only the standard library (smaller bundle).
- A network-level failure (engine unreachable) also triggers failover.
- Log messages updated in 5 languages. Unit tests grew to 33 (fake HTTP responses, no network needed).

---

## [2.0.1] - 2026-11-01

### TR — Düzeltmeler
- **Google "Too many requests" (istek sınırı) hatası giderildi.** Google yaklaşık saniyede 5 isteğe izin veriyor; uygulama isimleri arka arkaya hızlıca gönderdiği için çok dosyalı klasörlerde sınıra takılıyordu.
  - İstekler artık saniyede ~3 ile sınırlandırılıyor.
  - Yine de sınır gelirse 3-6-12-24-30 sn bekleyip otomatik yeniden deniyor; bekleme sırasında logda bilgi veriliyor.
  - Sınır tamamen aşılırsa kalan dosyalar için dakikalarca beklemek yerine işlem temiz şekilde durur. Hiçbir dosya bozulmaz; birkaç dakika sonra tekrar çalıştırınca çevrilmemiş dosyalardan devam eder.
  - **Durdur** butonu bekleme sırasında da anında çalışır.
- Yeni log mesajları 5 dilde (TR/EN/DE/ES/FR).
- Bu davranış için ağ gerektirmeyen birim testleri eklendi (toplam 19).
- **CI:** GitHub `macos-14` runner'ını emekliye ayırdığı için (2 Kasım 2026) macOS derlemesi `macos-15` (Apple Silicon) runner'ına taşındı.

### EN — Fixed
- **Fixed the Google "Too many requests" (rate limit) error.** Google allows about 5 requests per second; the app sent names back-to-back, so folders with many files hit the limit.
  - Requests are now throttled to ~3 per second.
  - If the limit is still hit, it waits 3-6-12-24-30 s and retries automatically, and the log says so while waiting.
  - If the limit is fully exhausted, the job stops cleanly instead of waiting minutes for every remaining file. No file is damaged; run it again a few minutes later and it continues with the files not yet translated.
  - The **Stop** button now works instantly even during a wait.
- New log messages in 5 languages (TR/EN/DE/ES/FR).
- Added network-free unit tests for this behaviour (19 in total).
- **CI:** the macOS build moved to the `macos-15` (Apple Silicon) runner because GitHub retired `macos-14` on 2 November 2026.

---

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
