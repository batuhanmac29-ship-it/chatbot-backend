import httpx
import os
from typing import Union

META_API_BASE = "https://graph.facebook.com/v19.0"

async def send_message(platform: str, recipient_id: str, message: Union[str, dict]) -> dict:
    token = (
        os.getenv("PAGE_ACCESS_TOKEN")
        if platform == "facebook"
        else os.getenv("INSTAGRAM_ACCESS_TOKEN")
    )

    if not token:
        return {"success": False, "error": f"{platform} token bulunamadı (.env dosyasını kontrol et)"}

    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message} if isinstance(message, str) else message,
        "messaging_type": "RESPONSE"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{META_API_BASE}/me/messages",
                json=payload,
                params={"access_token": token},
                timeout=10
            )
            data = response.json()

            if response.status_code == 200:
                print(f"📤 {platform.upper()} mesaj gönderildi → {recipient_id}")
                return {"success": True, "message_id": data.get("message_id")}
            else:
                error = data.get("error", {}).get("message", "Bilinmeyen hata")
                print(f"❌ {platform.upper()} mesaj hatası: {error}")
                return {"success": False, "error": error}

    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_user_profile(user_id: str, access_token: str) -> dict:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{META_API_BASE}/{user_id}",
                params={"access_token": access_token, "fields": "name,profile_pic"},
                timeout=5
            )
            return {"success": True, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}
async def send_whatsapp_message(recipient_id: str, message: str) -> dict:
    token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID")
    
    if not token or not phone_id:
        return {"success": False, "error": "WhatsApp token veya phone ID eksik"}
    
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "text",
        "text": {"body": message}
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{META_API_BASE}/{phone_id}/messages",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            data = response.json()
            if response.status_code == 200:
                print(f"📤 WhatsApp mesaj gönderildi → {recipient_id}")
                return {"success": True}
            else:
                error = data.get("error", {}).get("message", "Bilinmeyen hata")
                print(f"❌ WhatsApp mesaj hatası: {error}")
                return {"success": False, "error": error}
    except Exception as e:
        return {"success": False, "error": str(e)}
