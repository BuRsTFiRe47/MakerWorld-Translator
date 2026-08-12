# MakerWorld File Translator

MakerWorld'den (ve benzeri kaynaklardan) indirilen dosya/klasörlerdeki **Çince isimleri** otomatik olarak **İngilizce** veya **Türkçe**'ye çeviren, karanlık/aydınlık temalı, çift dilli (TR/EN) masaüstü uygulaması.

## Özellikler

- **Modern GUI** — CustomTkinter ile şık arayüz
- **Dark / Light Mode** — sağ üstteki anahtar ile
- **Program Dili** — Türkçe / English arayüz seçimi
- **Alt Klasör Tarama** — opsiyonel, tüm alt klasörlere iner
- **Klasör İsimlerini Çevirme** — opsiyonel, sadece dosyalar değil klasör adları da çevrilebilir
- **Dry Run** — hiçbir şeyi değiştirmeden önce ne olacağını gösterir
- **Çeviri Yönü** — Çince → İngilizce veya Çince → Türkçe
- **Çapraz Platform** — Windows (.exe) ve macOS Apple Silicon (.app, native ARM)

## Kurulum (Geliştirme)

Python 3.10+ gereklidir.

```bash
git clone https://github.com/KULLANICI_ADIN/MakerWorld-Translator.git
cd MakerWorld-Translator
pip install -r requirements.txt
python main.py
```

## Uygulamayı Derleme

Kullanıcıların Python kurmadan çalıştırabilmesi için PyInstaller ile derleyin:

```bash
pip install pyinstaller
```

**Windows (.exe):**
```bash
pyinstaller --noconfirm --onedir --windowed --name "MakerWorldTranslator" main.py
```
Çıktı: `dist/MakerWorldTranslator/MakerWorldTranslator.exe`

**macOS Apple Silicon (.app):**
```bash
pyinstaller --noconfirm --onedir --windowed --name "MakerWorldTranslator" main.py
```
Apple Silicon (M1/M2/M3/M4) üzerinde derlediğiniz için doğrudan ARM mimarisine native olarak çalışır.
Çıktı: `dist/MakerWorldTranslator.app`

### Otomatik Derleme (GitHub Actions)

Repoda `.github/workflows/build.yml` dosyası hazır geliyor. Bir sürüm etiketi (`v1.0.0` gibi) push ettiğinizde ya da Actions sekmesinden manuel tetiklediğinizde, GitHub hem Windows hem de Apple Silicon macOS derlemesini otomatik yapıp "Artifacts" olarak sunar — kendi bilgisayarınızda derlemenize gerek kalmaz.

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Lisans

Bu projeyi dilediğiniz gibi kullanabilir, değiştirebilirsiniz.
