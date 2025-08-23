import cv2
import numpy as np
import os

# ===== AYARLAR =====
video_dosya = "video.mp4"            # Düzenlenecek video
logo_dosya = "saharaporcusu.png"     # Eklenecek logo
cikis_dosya = "video_telif_korumali.mp4"
blur_logolar = True                   # True = logolar blur, False = siyah kutu ile sil

# Video yükle
cap = cv2.VideoCapture(video_dosya)
fps = int(cap.get(cv2.CAP_PROP_FPS))
genislik = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
yukseklik = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(cikis_dosya, fourcc, fps, (genislik, yukseklik))

# Kendi logonu yükle ve boyutlandır
logo = cv2.imread(logo_dosya, cv2.IMREAD_UNCHANGED)
logo_yeni_yukseklik = 80
oran = logo_yeni_yukseklik / logo.shape[0]
logo_yeni = cv2.resize(logo, (int(logo.shape[1] * oran), logo_yeni_yukseklik))

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # --- LOGO TESPİTİ ---
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Otomatik parlak alan tespiti
    # Burada parlak ve renkli logoları tespit ediyoruz
    # Daha doğru sonuç için farklı HSV aralıklarını deneyebilirsin
    lower = np.array([0, 0, 180])
    upper = np.array([180, 60, 255])
    mask = cv2.inRange(hsv, lower, upper)

    # Maskeyi aç/kapa işlemleri ile temizle
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # Logoları sil veya blur uygula
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 30 and h > 30:  # küçük lekeleri atla
            if blur_logolar:
                frame[y:y+h, x:x+w] = cv2.GaussianBlur(frame[y:y+h, x:x+w], (25,25), 30)
            else:
                frame[y:y+h, x:x+w] = 0  # siyah kutu ile sil

    # --- KENDİ LOGONU EKLE ---
    lx, ly = frame.shape[1] - logo_yeni.shape[1] - 15, 15
    for c in range(0, 3):
        frame[ly:ly+logo_yeni.shape[0], lx:lx+logo_yeni.shape[1], c] = \
            logo_yeni[:, :, c] * (logo_yeni[:, :, 3]/255.0) + \
            frame[ly:ly+logo_yeni.shape[0], lx:lx+logo_yeni.shape[1], c] * (1.0 - logo_yeni[:, :, 3]/255.0)

    out.write(frame)

cap.release()
out.release()
print("✅ İşlem tamam! Çıkış dosyası:", cikis_dosya)
