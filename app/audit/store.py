import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.config import _running_on_vercel, settings
from app.models.schemas import AuditRecord, BrandVoiceResult, Decision, GenerationResult, HardRulesResult


def _audit_db_path() -> str:
    path = settings.audit_db_path
    if _running_on_vercel() and not path.startswith("/tmp"):
        return "/tmp/audit.db"
    return path


def _ensure_db() -> None:
    path = _audit_db_path()
    p = Path(path)
    if p.parent != Path(".") and str(p.parent) != "/tmp":
        p.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


@contextmanager
def _connect():
    path = _audit_db_path()
    _ensure_db()
    conn = sqlite3.connect(path)
    try:
        yield conn
    finally:
        conn.close()


class AuditStore:
    def save(
        self,
        *,
        topic: str,
        post: str | None,
        hard_rules: HardRulesResult,
        brand_voice: BrandVoiceResult,
        decision: Decision,
        reasons: list,
        generation: GenerationResult | None,
        model: str | None,
    ) -> str:
        audit_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)
        record = AuditRecord(
            id=audit_id,
            topic=topic,
            post=post,
            hard_rules=hard_rules,
            brand_voice=brand_voice,
            decision=decision,
            reasons=reasons,
            generation=generation,
            created_at=created_at,
            model=model,
        )
        payload = record.model_dump(mode="json")
        with _connect() as conn:
            conn.execute(
                "INSERT INTO audit_log (id, payload, created_at) VALUES (?, ?, ?)",
                (audit_id, json.dumps(payload), created_at.isoformat()),
            )
            conn.commit()
        return audit_id

    def get(self, audit_id: str) -> AuditRecord | None:
        with _connect() as conn:
            row = conn.execute(
                "SELECT payload FROM audit_log WHERE id = ?", (audit_id,)
            ).fetchone()
        if not row:
            return None
        data = json.loads(row[0])
        return AuditRecord.model_validate(data)

    def list_recent(self, limit: int = 20) -> list[AuditRecord]:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM audit_log ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        records: list[AuditRecord] = []
        for row in rows:
            records.append(AuditRecord.model_validate(json.loads(row[0])))
        return records
