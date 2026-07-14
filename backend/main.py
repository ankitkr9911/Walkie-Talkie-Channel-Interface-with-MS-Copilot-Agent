"""
main.py — FastAPI Application Entry Point
===========================================
Walkie Talkie Channel Interface with MS Copilot Agent

This backend is purely an infrastructure layer:
  - Speech processing (STT/TTS)
  - Database access (SQLite/PostgreSQL)
  - REST APIs for Copilot Studio tools
  - Relay between frontend and Copilot Studio

ALL intelligence, intent detection, and tool selection lives in Copilot Studio.
The backend never decides what to do — it only executes what it's told.

Run: uvicorn main:app --reload --port 8000
"""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load .env BEFORE importing app modules — they read os.getenv() at import time
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from copilot_client import copilot
from routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize DB + seed data. Shutdown: cleanup connections."""
    print("[*] Starting Walkie Talkie Backend...")
    await init_db()
    print("[OK] Database initialized")
    yield
    await copilot.close()
    print("[*] Backend shut down")


# ---------- FastAPI App ----------
app = FastAPI(
    title="Walkie Talkie Inventory Agent API",
    description=(
        "Backend infrastructure for the Walkie Talkie Channel Interface. "
        "Provides voice/chat pipelines and inventory tool APIs for Microsoft Copilot Studio. "
        "All AI intelligence lives in Copilot Studio — this backend only handles "
        "speech processing, database queries, and API hosting."
    ),
    version="1.0.0",
    openapi_version="3.0.3",   # Copilot Studio requires 3.0.x — NOT 3.1.0
    lifespan=lifespan,
)

# CORS — allow frontend dev server (React on port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routes
app.include_router(router)


# Health check endpoint
@app.get("/health", summary="Health check")
async def health():
    return {"status": "healthy", "service": "walkie-talkie-backend"}
