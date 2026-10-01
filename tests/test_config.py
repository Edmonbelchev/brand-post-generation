import os

from app.config import Settings


def test_vercel_forces_tmp_audit_db(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    s = Settings(audit_db_path="./data/audit.db")
    assert s.audit_db_path == "/tmp/audit.db"


def test_local_keeps_audit_path(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    s = Settings(audit_db_path="./data/audit.db")
    assert s.audit_db_path == "./data/audit.db"
