# backend/app/main.py
import os
from pathlib import Path
from contextlib import asynccontextmanager
import firebase_admin
from firebase_admin import credentials
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(env_path)

from .db.database import engine, Base
from .db import models
from .routers import auth as auth_router
from .routers import contacts as contacts_router
from .routers import websocket as websocket_router
from .routers import history as history_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- SERVER STARTING: Checking database ---")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("--- DATABASE READY: personly.db is active ---")
    yield

def get_application() -> FastAPI:
    app = FastAPI(
        title=os.getenv("PROJECT_NAME", "Personly API"),
        description="Backend API for the Personly real-time communication platform.",
        version=os.getenv("VERSION", "1.0.0"),
        lifespan=lifespan
    )

    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "./serviceAccountKey.json")
    if os.path.exists(cred_path):
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully.")
    else:
        print(f"CRITICAL WARNING: Firebase credentials not found at {cred_path}")

    # Security Hardening: Middleware to add strict HTTP headers
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router.router)
    app.include_router(contacts_router.router)
    app.include_router(history_router.router)
    app.include_router(websocket_router.router)

    return app

app = get_application()

@app.get("/health")
async def health_check():
    firebase_status = "connected" if firebase_admin._apps else "disconnected"
    return {
        "status": "online",
        "service": os.getenv("PROJECT_NAME", "Personly API"),
        "firebase_admin": firebase_status
    }