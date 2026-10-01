from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(title="Driftwood Brand Voice Gate", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

_frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
_public_dir = Path(__file__).resolve().parent.parent / "public"
_static_dir = _frontend_dist if _frontend_dist.is_dir() else _public_dir
if _static_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="frontend")
