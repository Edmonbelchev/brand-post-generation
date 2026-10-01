"""Vercel serverless entrypoint (ASGI). Static UI is served from /public."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from app.main import app  # noqa: E402, F401
