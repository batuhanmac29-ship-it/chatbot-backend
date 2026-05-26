from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import uvicorn

from database import init_db
from routes import webhook, messages, appointments

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("\n🚀 Messenger Bot Backend çalışıyor!")
    print("📡 http://localhost:3000")
    print("🔗 Webhook: http://localhost:3000/webhook\n")
    yield

app = FastAPI(title="Messenger Chatbot Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(webhook.router, prefix="/webhook", tags=["Webhook"])
app.include_router(messages.router, prefix="/api", tags=["Mesajlar"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Randevular"])

@app.get("/", tags=["Genel"])
async def root():
    return {"name": "Messenger Chatbot Backend", "version": "1.0.0"}

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    with open("admin.html") as f:
        return f.read()

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy():
    with open("privacy.html") as f:
        return f.read()

@app.get("/health", tags=["Genel"])
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
