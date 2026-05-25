from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from database import init_db
from routes import webhook, messages, appointments

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("\n🚀 Messenger Bot Backend çalışıyor!")
    print("📡 http://localhost:3000")
    print("🔗 Webhook: http://localhost:3000/webhook")
    print("\n⚠️  Ngrok ile test için: npx ngrok http 3000")
    print("   Meta Console'a webhook URL'ini gir: https://XXXX.ngrok.io/webhook\n")
    yield
from dotenv import load_dotenv
load_dotenv()
app = FastAPI(
    title="Messenger Chatbot Backend",
    description="Facebook & Instagram chatbot API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router, prefix="/webhook", tags=["Webhook"])
app.include_router(messages.router, prefix="/api", tags=["Mesajlar"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Randevular"])

@app.get("/", tags=["Genel"])
async def root():
    return {
        "name": "Messenger Chatbot Backend",
        "version": "1.0.0",
        "endpoints": {
            "GET /webhook": "Meta doğrulama",
            "POST /webhook": "Gelen mesajlar",
            "GET /api/conversations": "Konuşmalar",
            "GET /api/conversations/{id}/messages": "Mesajlar",
            "POST /api/conversations/{id}/send": "Mesaj gönder",
            "GET /api/stats": "İstatistikler",
            "GET /api/appointments": "Randevular",
            "POST /api/appointments": "Randevu oluştur",
            "PATCH /api/appointments/{id}": "Randevu güncelle",
        }
    }
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    with open("admin.html") as f:
        return f.read()
@app.get("/health", tags=["Genel"])
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
