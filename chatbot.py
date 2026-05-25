import uuid
import aiosqlite
from meta_api import send_message, send_whatsapp_message

DB_PATH = "data/chatbot.db"

async def process_incoming_message(platform: str, sender_id: str, text: str, page_id: str = "default"):
    print(f"📨 {platform.upper()} [{sender_id}]: {text}")

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        conversation = await get_or_create_conversation(db, platform, sender_id, page_id)
        conv_id = conversation["id"]

        await save_message(db, conv_id, "incoming", text)

        bot_response = await generate_response(db, text, conversation)

        if bot_response:
            if platform == "whatsapp":
                result = await send_whatsapp_message(sender_id, bot_response)
            else:
                result = await send_message(platform, sender_id, bot_response)

            if result["success"]:
                await save_message(db, conv_id, "outgoing", bot_response)
            return {"conversation_id": conv_id, "response": bot_response, "sent": result["success"]}

    return {"conversation_id": conv_id, "response": None, "sent": False}


async def get_or_create_conversation(db, platform, sender_id, page_id):
    async with db.execute(
        "SELECT * FROM conversations WHERE platform=? AND sender_id=? AND page_id=?",
        (platform, sender_id, page_id)
    ) as cur:
        row = await cur.fetchone()

    if row:
        await db.execute(
            "UPDATE conversations SET last_message_at=CURRENT_TIMESTAMP WHERE id=?",
            (row["id"],)
        )
        await db.commit()
        return dict(row)

    conv_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO conversations (id, platform, sender_id, page_id) VALUES (?, ?, ?, ?)",
        (conv_id, platform, sender_id, page_id)
    )
    await db.commit()
    print(f"🆕 Yeni konuşma: {conv_id}")
    return {"id": conv_id, "platform": platform, "sender_id": sender_id, "page_id": page_id}


async def save_message(db, conversation_id, direction, content, platform_msg_id=None):
    msg_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO messages (id, conversation_id, direction, content, platform_message_id) VALUES (?,?,?,?,?)",
        (msg_id, conversation_id, direction, content, platform_msg_id)
    )
    await db.commit()
    return msg_id


async def generate_response(db, text: str, conversation: dict) -> str | None:
    if not text:
        return None

    lower = text.lower().strip()

    appt_response = await check_appointment_flow(db, lower, conversation)
    if appt_response:
        return appt_response

    async with db.execute(
        "SELECT * FROM bot_flows WHERE is_active=1 AND (platform='all' OR platform=?)",
        (conversation["platform"],)
    ) as cur:
        flows = await cur.fetchall()

    for flow in flows:
        if flow["trigger_keyword"].lower() in lower:
            return flow["response_text"]

    return "🤖 Mesajınızı aldım! Yardımcı olmak için buradayım.\n\nAna menü için 'merhaba' yazabilirsiniz."


async def check_appointment_flow(db, text: str, conversation: dict) -> str | None:
    triggers = ["randevu al", "randevu almak", "appointment", "1️⃣", "1)"]
    if any(t in text for t in triggers):
        return (
            "📅 Randevu almak için lütfen şu formatı kullanın:\n\n"
            "RANDEVU: Adınız | Tarih GG/AA | Saat SS:DD | Konu\n\n"
            "Örnek:\nRANDEVU: Ahmet Yılmaz | 15/06 | 14:30 | Danışmanlık"
        )

    if text.startswith("randevu:"):
        return await parse_and_create_appointment(db, text, conversation)

    return None


async def parse_and_create_appointment(db, text: str, conversation: dict) -> str:
    try:
        raw = text.replace("randevu:", "").strip()
        parts = [p.strip() for p in raw.split("|")]

        if len(parts) < 3:
            return "❌ Format hatalı. Örnek:\nRANDEVU: Adınız | 15/06 | 14:30 | Konu"

        customer_name = parts[0]
        date_str = parts[1]
        time_str = parts[2]
        topic = parts[3] if len(parts) > 3 else "Genel randevu"

        appt_id = str(uuid.uuid4())
        await db.execute(
            """INSERT INTO appointments
               (id, conversation_id, title, customer_name, appointment_date, appointment_time, status)
               VALUES (?, ?, ?, ?, ?, ?, 'pending')""",
            (appt_id, conversation["id"], topic, customer_name, date_str, time_str)
        )
        await db.commit()
        print(f"📅 Randevu oluşturuldu: {appt_id}")

        return (
            f"✅ Randevunuz alındı!\n\n"
            f"👤 Ad: {customer_name}\n"
            f"📅 Tarih: {date_str}\n"
            f"🕐 Saat: {time_str}\n"
            f"📝 Konu: {topic}\n\n"
            f"En kısa sürede onaylayacağız. Teşekkürler! 🙏"
        )
    except Exception as e:
        print(f"Randevu parse hatası: {e}")
        return "❌ Randevu oluşturulamadı. Lütfen tekrar deneyin."
