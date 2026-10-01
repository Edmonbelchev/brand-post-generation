"""Root ASGI entry for Vercel (do not name this file app.py — conflicts with app/ package)."""

from app.main import app

__all__ = ["app"]
