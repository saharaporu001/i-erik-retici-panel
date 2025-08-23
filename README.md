# SahaRaporcusu Web v2

- 🔒 Basit giriş sistemi (kullanıcı: `saha`, şifre: `raporcusu` — ENV ile değiştirilebilir)
- 📹 Telif Koruma: video yükle → `video.mp4` olarak işlenir → indir
- ⚽ Gol Çarpışma: Web’de logoları seç → 90sn video üret (rastgele 2–5 gol)

## Çalıştırma
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Sonra: http://localhost:8000  (önce /login)

## Ortam Değişkenleri
- `APP_SECRET`  (session için)
- `APP_USER`    (varsayılan `saha`)
- `APP_PASS`    (varsayılan `raporcusu`)

## İndirme
Artık indirme linki absolute path ile çalışıyor: `/download?path=/full/path/to/file.mp4`

## Notlar
- Gol videosu üretimi Pygame menüsüne gerek olmadan web’den seçimle çalışır.
- Telif aracı, yüklenen dosyayı `video.mp4` ismine dönüştürüp kendi klasöründe çalıştırır.
