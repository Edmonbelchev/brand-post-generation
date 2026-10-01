from app.audit.store import AuditStore
from app.decision.engine import decide
from app.generation.generator import PostGenerator
from app.generation.post_format import normalize_post_content
from app.models.schemas import (
    BrandVoiceResult,
    ChecksResponse,
    Decision,
    GenerateResponse,
    GenerationResult,
    HardRulesResult,
)
from app.validation.brand_voice.evaluator import BrandVoiceEvaluator
from app.validation.hard_rules.validator import validate_hard_rules
from app.validation.plain_text import plain_text_from_post


class BrandVoiceGatePipeline:
    def __init__(
        self,
        generator: PostGenerator,
        evaluator: BrandVoiceEvaluator,
        audit: AuditStore | None = None,
    ) -> None:
        self._generator = generator
        self._evaluator = evaluator
        self._audit = audit or AuditStore()

    async def _finalize(
        self,
        *,
        topic: str,
        generation: GenerationResult,
    ) -> GenerateResponse:
        hard_rules: HardRulesResult
        brand_voice: BrandVoiceResult

        if generation.success and generation.post:
            text_for_checks = plain_text_from_post(generation.post)
            hard_rules = validate_hard_rules(text_for_checks)
            if hard_rules.passed:
                brand_voice = await self._evaluator.evaluate(text_for_checks)
            else:
                brand_voice = BrandVoiceResult(
                    passed=False,
                    score=None,
                    feedback=["Skipped: hard rules failed"],
                )
        else:
            hard_rules = HardRulesResult(passed=False, violations=[])
            brand_voice = BrandVoiceResult(
                passed=False,
                error=generation.error,
                feedback=["Skipped: generation failed"],
            )

        decision, reasons = decide(
            generation=generation,
            hard_rules=hard_rules,
            brand_voice=brand_voice,
        )

        audit_id = self._audit.save(
            topic=topic,
            post=generation.post,
            hard_rules=hard_rules,
            brand_voice=brand_voice,
            decision=decision,
            reasons=reasons,
            generation=generation,
            model=generation.model,
        )

        post_out = generation.post if decision == Decision.PUBLISH else None

        return GenerateResponse(
            decision=decision,
            post=post_out,
            generated_post=generation.post,
            checks=ChecksResponse(hard_rules=hard_rules, brand_voice=brand_voice),
            reasons=reasons,
            audit_id=audit_id,
        )

    async def run(self, topic: str) -> GenerateResponse:
        generation: GenerationResult = await self._generator.generate(topic)
        return await self._finalize(topic=topic, generation=generation)

    async def validate_post(self, *, topic: str, post: str) -> GenerateResponse:
        text = normalize_post_content(post)
        if not text:
            return await self._finalize(
                topic=topic,
                generation=GenerationResult(
                    success=False,
                    error="Post is empty",
                    post=None,
                ),
            )
        generation = GenerationResult(success=True, post=text, model=None)
        return await self._finalize(topic=topic, generation=generation)
