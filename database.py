import aiosqlite
import os

DB_PATH = "data/chatbot.db"

async def init_db():
    os.makedirs("data", exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            PRAGMA journal_mode=WAL;

            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                sender_id TEXT NOT NULL,
                sender_name TEXT,
                page_id TEXT DEFAULT 'default',
                status TEXT DEFAULT 'active',
                last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(platform, sender_id, page_id)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                direction TEXT NOT NULL,
                content TEXT,
                message_type TEXT DEFAULT 'text',
                platform_message_id TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read INTEGER DEFAULT 0,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );

            CREATE TABLE IF NOT EXISTS appointments (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                customer_name TEXT,
                customer_phone TEXT,
                appointment_date TEXT,
                appointment_time TEXT,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );

            CREATE TABLE IF NOT EXISTS bot_flows (
                id TEXT PRIMARY KEY,
                trigger_keyword TEXT NOT NULL,
                response_text TEXT NOT NULL,
                platform TEXT DEFAULT 'all',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            INSERT OR IGNORE INTO bot_flows (id, trigger_keyword, response_text) VALUES
                ('flow_1', 'merhaba', 'Merhaba! 👋 Size nasıl yardımcı olabilirim?

1️⃣ Randevu al
2️⃣ Bilgi al
3️⃣ İnsan ile konuş'),
                ('flow_2', 'randevu', 'Randevu almak için lütfen şu bilgileri gönderin:

Format:
RANDEVU: Adınız | Tarih GG/AA | Saat SS:DD | Konu

Örnek:
RANDEVU: Ahmet Yılmaz | 15/06 | 14:30 | Danışmanlık'),
                ('flow_3', 'teşekkür', 'Rica ederim! 😊 Başka bir konuda yardımcı olabilir miyim?'),
                ('flow_4', 'saatler', '🕐 Çalışma saatlerimiz:
Hafta içi: 09:00 - 18:00
Cumartesi: 10:00 - 14:00
Pazar: Kapalı'),
                ('flow_5', 'iletişim', '📞 Bize ulaşın:
Tel: +90 XXX XXX XX XX
E-posta: info@example.com');
        """)
        await db.commit()
    print("✅ Veritabanı hazır:", DB_PATH)

async def get_db():
    return aiosqlite.connect(DB_PATH)
