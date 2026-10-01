# Driftwood Brand Voice Gate

Production-minded gate for Driftwood social copy: an LLM drafts a post from a topic, deterministic code enforces non-negotiable rules, an LLM scores subjective brand voice, and **application code** makes the final `PUBLISH` / `HOLD` / `REJECT` decision. The model never owns the publish decision.

## Architecture

```
Topic → LLM Generator → Hard Rule Validator → Brand Voice Evaluator → Decision Engine → Audit Log
```

| Layer | Responsibility |
|--------|----------------|
| **LLM generator** | Draft on-brand copy as sanitized HTML (`<p>`, `<strong>`, `<em>`, `<u>`, `<a>`) |
| **Hard rule validator** | Absolute claims, competitors, hard-sell, `!`, emoji, ALL-CAPS hype |
| **Brand voice evaluator** | LLM scores warmth / tone (threshold configurable) |
| **Decision engine** | `REJECT` on rule breaks; `HOLD` on uncertainty; `PUBLISH` only when all checks pass |
| **Audit store** | SQLite record for every attempt |

## Setup

**Requirements:** Python 3.11+, optional OpenAI API key for live generation.

```bash
cd /path/to/Driftwood
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
bash scripts/build_frontend.sh
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (empty) | OpenAI key; without it, generation returns HOLD |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model for generate + evaluate |
| `BRAND_VOICE_THRESHOLD` | `80` | Minimum brand voice score to publish |
| `LLM_TIMEOUT_SECONDS` | `30` | Request timeout |
| `LLM_MAX_TOKENS_GENERATE` | `1200` | Token budget for drafting longer posts |
| `GENERATION_MIN_WORDS` | `180` | Target minimum length (prompt guidance) |
| `GENERATION_MAX_WORDS` | `320` | Target maximum length (prompt guidance) |
| `AUDIT_DB_PATH` | `./data/audit.db` | SQLite audit log path |

## Run backend (+ UI)

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000). API docs: [http://localhost:8000/docs](http://localhost:8000/docs).

## Run frontend only (dev)

The UI is static files under `frontend/dist/`, copied by `scripts/build_frontend.sh`. Edit `frontend/*` and re-run the script after changes.

## Tests

```bash
pytest -q
```

Tests mock the LLM and cover deterministic rejects, failure modes (timeout, malformed JSON, low brand score), and the invariant that **no violating copy reaches PUBLISH**.

## API

### `POST /api/generate`

```json
{ "topic": "Why freshly roasted coffee tastes different" }
```

Example **PUBLISH** response:

```json
{
  "decision": "publish",
  "post": "…",
  "generated_post": "…",
  "checks": {
    "hard_rules": { "passed": true, "violations": [] },
    "brand_voice": { "score": 91, "passed": true, "feedback": [] }
  },
  "reasons": [],
  "audit_id": "…"
}
```

**REJECT** (deterministic): `decision: "reject"`, `post: null`, `reasons` / `checks.hard_rules.violations` explain why.

**HOLD** (uncertainty): generation failure, evaluator error, or score below threshold — never silently publishes.

### `POST /api/validate`

Re-run hard rules and brand voice on **edited** copy (no LLM draft step). Use after manual edits in the UI.

```json
{
  "topic": "Why freshly roasted coffee tastes different",
  "post": "Your edited post text…"
}
```

Response shape matches `POST /api/generate`.

### `GET /api/audit/{audit_id}`

Full audit record for a decision.

### `GET /api/audit?limit=20`

Recent decisions (newest first).

## Example curl

```bash
curl -s -X POST http://localhost:8000/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"topic":"Why freshly roasted coffee tastes different"}' | jq
```

## Key decisions

See [DECISIONS.md](./DECISIONS.md) for trust boundaries, failure handling, and intentional omissions.
