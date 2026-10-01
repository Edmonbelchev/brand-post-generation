from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_generate_requires_topic():
    res = client.post("/api/generate", json={"topic": ""})
    assert res.status_code == 422


def test_validate_rejects_bad_copy_without_llm():
    res = client.post(
        "/api/validate",
        json={
            "topic": "Test topic",
            "post": "We are guaranteed the best. Buy now!",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "reject"
    assert data["post"] is None
    assert not data["checks"]["hard_rules"]["passed"]


def test_generate_without_api_key_holds():
    res = client.post(
        "/api/generate",
        json={"topic": "Why fresh roast matters"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "hold"
    assert data["post"] is None
    assert data["audit_id"]

    audit = client.get(f"/api/audit/{data['audit_id']}")
    assert audit.status_code == 200
    assert audit.json()["topic"] == "Why fresh roast matters"
