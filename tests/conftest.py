import os
import tempfile

import pytest

from app.config import settings


@pytest.fixture(autouse=True)
def isolated_audit_db(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test_audit.db")
        monkeypatch.setattr(settings, "audit_db_path", db_path)
        yield
