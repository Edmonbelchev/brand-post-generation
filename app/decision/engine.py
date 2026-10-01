from app.models.schemas import (
    BrandVoiceResult,
    Decision,
    GenerationResult,
    HardRulesResult,
    RuleViolation,
)


def decide(
    *,
    generation: GenerationResult,
    hard_rules: HardRulesResult | None,
    brand_voice: BrandVoiceResult | None,
) -> tuple[Decision, list[RuleViolation | dict[str, str]]]:
    """
    Final decision is always made in application code.
    REJECT on deterministic violations; HOLD on uncertainty; PUBLISH only when all checks pass.
    """
    reasons: list[RuleViolation | dict[str, str]] = []

    if not generation.success or not generation.post:
        msg = generation.error or "Content generation failed"
        reasons.append({"rule": "generation_failed", "message": msg})
        return Decision.HOLD, reasons

    assert hard_rules is not None
    if not hard_rules.passed:
        reasons.extend(hard_rules.violations)
        return Decision.REJECT, reasons

    if brand_voice is None:
        reasons.append(
            {"rule": "brand_voice_skipped", "message": "Brand voice evaluation did not run"}
        )
        return Decision.HOLD, reasons

    if brand_voice.error:
        reasons.append({"rule": "brand_voice_error", "message": brand_voice.error})
        for fb in brand_voice.feedback:
            reasons.append({"rule": "brand_voice_feedback", "message": fb})
        return Decision.HOLD, reasons

    if not brand_voice.passed:
        reasons.append(
            {
                "rule": "brand_voice_threshold",
                "message": f"Brand voice score {brand_voice.score} below required threshold",
            }
        )
        for fb in brand_voice.feedback:
            reasons.append({"rule": "brand_voice_feedback", "message": fb})
        return Decision.HOLD, reasons

    return Decision.PUBLISH, []
