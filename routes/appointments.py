from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import aiosqlite
import uuid

router = APIRouter()
DB_PATH = "data/chatbot.db"


class AppointmentCreate(BaseModel):
    conversation_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    appointment_date: str   # GG/AA veya YYYY-MM-DD
    appointment_time: str   # SS:DD
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None  # pending|confirmed|cancelled|completed
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None


@router.get("")
async def list_appointments(status: str = None, date: str = None, limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = """
            SELECT a.*, c.platform, c.sender_name
            FROM appointments a
            LEFT JOIN conversations c ON c.id = a.conversation_id
        """
        conditions, params = [], []
        if status:
            conditions.append("a.status=?"); params.append(status)
        if date:
            conditions.append("a.appointment_date=?"); params.append(date)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY a.appointment_date ASC, a.appointment_time ASC LIMIT ?"
        params.append(limit)

        async with db.execute(query, params) as cur:
            rows = await cur.fetchall()
        return {"success": True, "data": [dict(r) for r in rows]}


@router.post("", status_code=201)
async def create_appointment(body: AppointmentCreate):
    appt_id = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO appointments
               (id, conversation_id, title, description, customer_name, customer_phone,
                appointment_date, appointment_time, notes)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (appt_id, body.conversation_id, body.title, body.description,
             body.customer_name, body.customer_phone,
             body.appointment_date, body.appointment_time, body.notes)
        )
        await db.commit()
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM appointments WHERE id=?", (appt_id,)) as cur:
            row = await cur.fetchone()
    return {"success": True, "data": dict(row)}


@router.patch("/{appt_id}")
async def update_appointment(appt_id: str, body: AppointmentUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Güncellenecek alan yok")

    set_clause = ", ".join(f"{k}=?" for k in updates)
    values = list(updates.values()) + [appt_id]

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            f"UPDATE appointments SET {set_clause}, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            values
        )
        await db.commit()
        async with db.execute("SELECT * FROM appointments WHERE id=?", (appt_id,)) as cur:
            row = await cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Randevu bulunamadı")
    return {"success": True, "data": dict(row)}


@router.delete("/{appt_id}")
async def cancel_appointment(appt_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE appointments SET status='cancelled' WHERE id=?", (appt_id,)
        )
        await db.commit()
    return {"success": True, "message": "Randevu iptal edildi"}
