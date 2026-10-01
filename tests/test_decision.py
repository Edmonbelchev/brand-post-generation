from app.decision.engine import decide
from app.models.schemas import BrandVoiceResult, Decision, GenerationResult, HardRulesResult, RuleViolation


def test_publish_when_all_pass():
    decision, reasons = decide(
        generation=GenerationResult(success=True, post="Hello"),
        hard_rules=HardRulesResult(passed=True),
        brand_voice=BrandVoiceResult(score=85, passed=True),
    )
    assert decision == Decision.PUBLISH
    assert reasons == []


def test_reject_on_hard_rules():
    decision, reasons = decide(
        generation=GenerationResult(success=True, post="Buy now"),
        hard_rules=HardRulesResult(
            passed=False,
            violations=[RuleViolation(rule="hard_sell", message="Contains hard-sell language: 'buy now'")],
        ),
        brand_voice=BrandVoiceResult(score=99, passed=True),
    )
    assert decision == Decision.REJECT
    assert len(reasons) == 1


def test_hold_on_generation_failure():
    decision, reasons = decide(
        generation=GenerationResult(success=False, error="timeout"),
        hard_rules=HardRulesResult(passed=True),
        brand_voice=BrandVoiceResult(passed=True, score=90),
    )
    assert decision == Decision.HOLD
    assert reasons[0]["rule"] == "generation_failed"


def test_hold_on_low_brand_voice():
    decision, reasons = decide(
        generation=GenerationResult(success=True, post="Nice coffee."),
        hard_rules=HardRulesResult(passed=True),
        brand_voice=BrandVoiceResult(score=50, passed=False, feedback=["Too salesy"]),
    )
    assert decision == Decision.HOLD
    assert any(r.get("rule") == "brand_voice_threshold" for r in reasons if isinstance(r, dict))


def test_hold_on_brand_voice_error():
    decision, _ = decide(
        generation=GenerationResult(success=True, post="Nice coffee."),
        hard_rules=HardRulesResult(passed=True),
        brand_voice=BrandVoiceResult(passed=False, error="malformed JSON"),
    )
    assert decision == Decision.HOLD
