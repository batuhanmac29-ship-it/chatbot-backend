# 🤖 Messenger & Instagram Chatbot Backend

Facebook Messenger ve Instagram DM için tam özellikli chatbot backend.  
**Python + FastAPI + SQLite** — kurulumu 5 dakika.

---

## 📁 Dosya Yapısı

```
chatbot-backend/
├── main.py               # Ana uygulama
├── database.py           # SQLite şema & bağlantı
├── chatbot.py            # Bot mantığı, otomatik cevaplar
├── meta_api.py           # Meta Graph API (mesaj gönderme)
├── routes/
│   ├── webhook.py        # Gelen mesajları al (Meta → siz)
│   ├── messages.py       # Konuşma & mesaj API'si
│   └── appointments.py   # Randevu API'si
├── data/
│   └── chatbot.db        # SQLite veritabanı (otomatik oluşur)
├── .env                  # Tokenlar (git'e ekleme!)
└── requirements.txt
```

---

## 🚀 Kurulum (5 adım)

### 1. Python bağımlılıklarını yükle
```bash
pip install -r requirements.txt
```

### 2. .env dosyasını oluştur
```bash
cp .env.example .env
```
Sonra `.env` dosyasını aç ve tokenlarını gir:
```
PAGE_ACCESS_TOKEN=EAAxxxxxxx        # Facebook token
INSTAGRAM_ACCESS_TOKEN=EAAxxxxxxx  # Instagram token
VERIFY_TOKEN=istedigin_bir_sifre   # Kendi belirlediğin şifre
```

### 3. Sunucuyu başlat
```bash
# Geliştirme (otomatik yeniden başlar)
uvicorn main:app --reload --port 3000

# Veya direkt
python main.py
```

### 4. Ngrok ile dışarıya aç (Meta buna ihtiyaç duyar)
```bash
# Yeni terminal:
npx ngrok http 3000
# Çıktıdan URL'yi kopyala: https://XXXX.ngrok.io
```

### 5. Meta Developer Console'da webhook ayarla
1. https://developers.facebook.com → Uygulamanı seç
2. **Messenger → Settings → Webhooks → Add Callback URL**
3. Callback URL: `https://XXXX.ngrok.io/webhook`
4. Verify Token: `.env`'deki `VERIFY_TOKEN` değeri
5. Subscriptions: `messages` ve `messaging_postbacks` seç
6. **Verify and Save** tıkla ✅

---

## 📡 API Referansı

### Konuşmalar
| Method | URL | Açıklama |
|--------|-----|----------|
| GET | `/api/conversations` | Tüm konuşmaları listele |
| GET | `/api/conversations/{id}/messages` | Mesajları getir |
| POST | `/api/conversations/{id}/send` | Manuel mesaj gönder |
| PATCH | `/api/conversations/{id}/status` | Durum güncelle |
| GET | `/api/stats` | İstatistikler |

### Randevular
| Method | URL | Açıklama |
|--------|-----|----------|
| GET | `/api/appointments` | Randevuları listele |
| POST | `/api/appointments` | Randevu oluştur |
| PATCH | `/api/appointments/{id}` | Randevu güncelle |
| DELETE | `/api/appointments/{id}` | Randevu iptal et |

### Swagger UI (otomatik dokümantasyon)
Sunucu açıkken: http://localhost:3000/docs

---

## 🤖 Bot Komutları

Kullanıcılar şunları yazabilir:

| Mesaj | Bot cevabı |
|-------|-----------|
| `merhaba` | Ana menü |
| `randevu` | Randevu alma bilgisi |
| `1` | Randevu al |
| `saatler` | Çalışma saatleri |
| `iletişim` | İletişim bilgileri |
| `teşekkür` | Teşekkür cevabı |

### Randevu oluşturma formatı:
```
RANDEVU: Ahmet Yılmaz | 15/06 | 14:30 | Danışmanlık
```

---

## ⚙️ Yeni Bot Cevabı Eklemek

`database.py` içindeki `bot_flows` tablosuna yeni satır ekle:
```python
INSERT INTO bot_flows (id, trigger_keyword, response_text)
VALUES ('flow_10', 'fiyat', '💰 Fiyatlarımız için web sitemizi ziyaret edin.')
```

---

## 🚢 Sunucuya Taşıma

### Railway.app (en kolay, ücretsiz)
```bash
npm install -g @railway/cli
railway login && railway init && railway up
```

### VPS (Ubuntu) ile PM2
```bash
pip install -r requirements.txt
npm install -g pm2
pm2 start "uvicorn main:app --host 0.0.0.0 --port 3000" --name chatbot
pm2 save && pm2 startup
```

---

## 🔧 Sorun Giderme

**Webhook doğrulanamıyor:**
- VERIFY_TOKEN .env ve Meta Console'da aynı mı?
- Ngrok aktif mi? (`ngrok http 3000`)

**Mesaj gönderilemiyor:**
- PAGE_ACCESS_TOKEN geçerli mi?
- Token'ın `pages_messaging` iznine sahip olduğunu kontrol et

**Swagger UI'ya erişim:**
- http://localhost:3000/docs — tüm endpoint'leri buradan test edebilirsin
