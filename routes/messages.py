from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import aiosqlite
from meta_api import send_message
from chatbot import save_message

router = APIRouter()
DB_PATH = "data/chatbot.db"

class SendMessageBody(BaseModel):
    message: str

class UpdateStatusBody(BaseModel):
    status: str  # active | resolved | pending


@router.get("/conversations")
async def list_conversations(platform: str = None, status: str = None, limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = """
            SELECT c.*,
                COUNT(m.id) as message_count,
                SUM(CASE WHEN m.direction='incoming' AND m.is_read=0 THEN 1 ELSE 0 END) as unread_count,
                (SELECT content FROM messages WHERE conversation_id=c.id ORDER BY sent_at DESC LIMIT 1) as last_message
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.id
        """
        conditions, params = [], []
        if platform:
            conditions.append("c.platform=?"); params.append(platform)
        if status:
            conditions.append("c.status=?"); params.append(status)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " GROUP BY c.id ORDER BY c.last_message_at DESC LIMIT ?"
        params.append(limit)

        async with db.execute(query, params) as cur:
            rows = await cur.fetchall()
        return {"success": True, "data": [dict(r) for r in rows]}


@router.get("/conversations/{conv_id}/messages")
async def get_messages(conv_id: str, limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM conversations WHERE id=?", (conv_id,)) as cur:
            conv = await cur.fetchone()
        if not conv:
            raise HTTPException(status_code=404, detail="Konuşma bulunamadı")

        async with db.execute(
            "SELECT * FROM messages WHERE conversation_id=? ORDER BY sent_at DESC LIMIT ?",
            (conv_id, limit)
        ) as cur:
            msgs = await cur.fetchall()

        # Okundu işaretle
        await db.execute(
            "UPDATE messages SET is_read=1 WHERE conversation_id=? AND direction='incoming' AND is_read=0",
            (conv_id,)
        )
        await db.commit()

        return {
            "success": True,
            "conversation": dict(conv),
            "messages": [dict(m) for m in reversed(msgs)]
        }


@router.post("/conversations/{conv_id}/send")
async def send_manual_message(conv_id: str, body: SendMessageBody):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM conversations WHERE id=?", (conv_id,)) as cur:
            conv = await cur.fetchone()
        if not conv:
            raise HTTPException(status_code=404, detail="Konuşma bulunamadı")

        result = await send_message(conv["platform"], conv["sender_id"], body.message)
        if result["success"]:
            await save_message(db, conv_id, "outgoing", body.message)
            return {"success": True, "message": "Gönderildi"}
        else:
            raise HTTPException(status_code=500, detail=result["error"])


@router.patch("/conversations/{conv_id}/status")
async def update_status(conv_id: str, body: UpdateStatusBody):
    if body.status not in ("active", "resolved", "pending"):
        raise HTTPException(status_code=400, detail="Geçersiz durum")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE conversations SET status=? WHERE id=?", (body.status, conv_id))
        await db.commit()
    return {"success": True}


@router.get("/stats")
async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async def count(q, p=()):
            async with db.execute(q, p) as c:
                r = await c.fetchone()
                return r[0]

        conversations = await count("SELECT COUNT(*) FROM conversations")
        messages = await count("SELECT COUNT(*) FROM messages")
        unread = await count("SELECT COUNT(*) FROM messages WHERE direction='incoming' AND is_read=0")
        appointments = await count("SELECT COUNT(*) FROM appointments")
        today = await count("SELECT COUNT(*) FROM messages WHERE date(sent_at)=date('now')")

        async with db.execute("SELECT platform, COUNT(*) as cnt FROM conversations GROUP BY platform") as cur:
            by_platform = [dict(r) for r in await cur.fetchall()]

    return {
        "success": True,
        "data": {
            "conversations": conversations,
            "messages": messages,
            "unread": unread,
            "appointments": appointments,
            "today_messages": today,
            "by_platform": by_platform
        }
    }
@router.get("/botflows")
async def list_botflows():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM bot_flows ORDER BY created_at ASC") as cur:
            rows = await cur.fetchall()
        return {"success": True, "data": [dict(r) for r in rows]}

@router.post("/botflows")
async def create_botflow(body: dict):
    import uuid
    flow_id = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO bot_flows (id, trigger_keyword, response_text, platform) VALUES (?,?,?,?)",
            (flow_id, body["trigger_keyword"], body["response_text"], body.get("platform","all"))
        )
        await db.commit()
    return {"success": True, "id": flow_id}

@router.patch("/botflows/{flow_id}")
async def update_botflow(flow_id: str, body: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE bot_flows SET trigger_keyword=?, response_text=?, is_active=? WHERE id=?",
            (body["trigger_keyword"], body["response_text"], body.get("is_active", 1), flow_id)
        )
        await db.commit()
    return {"success": True}

@router.delete("/botflows/{flow_id}")
async def delete_botflow(flow_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM bot_flows WHERE id=?", (flow_id,))
        await db.commit()
    return {"success": True}
@router.get("/botflows")
async def list_botflows():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM bot_flows ORDER BY created_at ASC") as cur:
            rows = await cur.fetchall()
        return {"success": True, "data": [dict(r) for r in rows]}

@router.post("/botflows")
async def create_botflow(body: dict):
    import uuid
    flow_id = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO bot_flows (id, trigger_keyword, response_text, platform) VALUES (?,?,?,?)",
            (flow_id, body["trigger_keyword"], body["response_text"], body.get("platform","all"))
        )
        await db.commit()
    return {"success": True, "id": flow_id}

@router.patch("/botflows/{flow_id}")
async def update_botflow(flow_id: str, body: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE bot_flows SET trigger_keyword=?, response_text=?, is_active=? WHERE id=?",
            (body["trigger_keyword"], body["response_text"], body.get("is_active", 1), flow_id)
        )
        await db.commit()
    return {"success": True}

@router.delete("/botflows/{flow_id}")
async def delete_botflow(flow_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM bot_flows WHERE id=?", (flow_id,))
        await db.commit()
    return {"success": True}
