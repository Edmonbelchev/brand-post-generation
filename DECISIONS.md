# Engineering decisions — Brand Voice Gate

## What we trust the LLM to do

- **Draft** social copy from a topic, guided by brand voice instructions.
- **Score subjective brand fit** (warmth, plain language, dry personality) on a 0–100 scale with short feedback.

Both use structured JSON responses and timeouts.

## What we do not trust the LLM to do

- Detect or enforce **non-negotiable** policy (absolute claims, competitors, hard-sell, formatting).
- Make the **publish** decision.
- Override a failed deterministic check — brand voice is **skipped** when hard rules fail.

## Why deterministic validation exists

LLMs are stochastic. Policy violations must not depend on the model “ behaving ” on a given run. Hard rules live in configurable Python (phrases, competitors, regex for emoji / ALL-CAPS / exclamation marks) and return structured violations for `REJECT` and audit.

## Why brand voice uses an LLM

“Sounds like Driftwood” is subjective. A fixed keyword list would miss nuance and false-positive on good copy. A separate evaluator prompt keeps **policy** and **voice** concerns split. Threshold (default 80) is configurable.

## Why the final decision is application code

`decide()` applies a fixed order: generation must succeed → hard rules must pass → brand voice must pass without error. Only then `PUBLISH`. This is testable without calling OpenAI.

## Why uncertainty → HOLD

Timeout, API errors, malformed JSON, missing fields, empty posts, evaluator failures, and low brand scores all map to **HOLD**, not publish. When we cannot confidently say the post is safe and on-brand, we do not ship it.

## Failure modes handled

| Condition | Outcome |
|-----------|---------|
| LLM timeout / API error | HOLD |
| Malformed or empty generation | HOLD |
| Hard rule violation | REJECT (evaluator not run) |
| Evaluator error / bad JSON | HOLD |
| Score &lt; threshold | HOLD |

## Tradeoffs

- **Phrase lists** are maintainable but not semantically complete; they match the brief’s examples and are easy to extend in `HardRulesConfig`.
- **SQLite audit** adds persistence with no extra infrastructure; not built for high-volume analytics.
- **Single OpenAI client** for generate + evaluate keeps setup simple; interfaces allow mocks in tests.

## Intentionally not built

Authentication, real social posting, microservices, vector/RAG, agent orchestration, and human review workflows. This is a thin, reviewable slice focused on **safe automation boundaries**.
