from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import PlainTextResponse
import os
from chatbot import process_incoming_message

router = APIRouter()

@router.post("/whatsapp")
async def receive_whatsapp(request: Request):
    """WhatsApp'tan gelen mesajları işle"""
    body = await request.json()
    
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            
            for msg in messages:
                sender_id = msg.get("from")
                text = msg.get("text", {}).get("body", "")
                
                if sender_id and text:
                    await process_incoming_message("whatsapp", sender_id, text, "whatsapp")
    
    return {"status": "ok"}

@router.get("/whatsapp")
async def verify_whatsapp(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    if hub_mode == "subscribe" and hub_verify_token == os.getenv("VERIFY_TOKEN"):
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Doğrulama başarısız")

@router.get("", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """Meta webhook doğrulaması"""
    print(f"🔐 Webhook doğrulama: mode={hub_mode}, token={hub_verify_token}")

    if hub_mode == "subscribe" and hub_verify_token == os.getenv("VERIFY_TOKEN"):
        print("✅ Webhook doğrulandı!")
        return hub_challenge
    else:
        print("❌ Webhook doğrulama başarısız")
        raise HTTPException(status_code=403, detail="Doğrulama başarısız")


@router.post("")
async def receive_webhook(request: Request):
    """Meta'dan gelen mesajları işle"""
    body = await request.json()

    # Meta 200 beklediği için hemen yanıt ver
    # (Arka planda işleme devam eder)
    object_type = body.get("object")

    if object_type not in ("page", "instagram"):
        return {"status": "ignored"}

    for entry in body.get("entry", []):
        page_id = entry.get("id", "default")

        # Facebook Messenger & Instagram DM (messaging array)
        for event in entry.get("messaging", []):
            msg = event.get("message", {})
            sender_id = event.get("sender", {}).get("id")

            # echo mesajları atla (kendi gönderilen mesajlar)
            if msg.get("is_echo") or not sender_id:
                continue

            text = msg.get("text", "")
            attachments = msg.get("attachments")

            if attachments:
                text = "[Resim/Dosya gönderildi]"

            if text:
                platform = "instagram" if object_type == "instagram" else "facebook"
                await process_incoming_message(platform, sender_id, text, page_id)

        # Instagram eski format (changes array)
        for change in entry.get("changes", []):
            if change.get("field") == "messages":
                val = change.get("value", {})
                sender_id = val.get("sender", {}).get("id")
                text = val.get("message", {}).get("text", "")
                if sender_id and text:
                    await process_incoming_message("instagram", sender_id, text, page_id)

    return {"status": "ok"}
