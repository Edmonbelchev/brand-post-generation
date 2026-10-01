import pytest

from app.audit.store import AuditStore
from app.generation.generator import PostGenerator
from app.models.schemas import Decision
from app.pipeline import BrandVoiceGatePipeline
from app.validation.brand_voice.evaluator import BrandVoiceEvaluator
from tests.mocks import MockLLMClient


@pytest.mark.asyncio
async def test_validate_post_rejects_hard_rules_without_generation():
    post = "Our coffee is the best. Buy now!"
    llm = MockLLMClient(evaluate_response=({"score": 100, "feedback": []}, None))
    pipeline = BrandVoiceGatePipeline(PostGenerator(llm), BrandVoiceEvaluator(llm))
    result = await pipeline.validate_post(topic="Edited copy", post=post)
    assert result.decision == Decision.REJECT
    assert not result.checks.hard_rules.passed
    assert llm.generate_calls == 0
    assert llm.evaluate_calls == 0


@pytest.mark.asyncio
async def test_validate_post_runs_brand_voice_when_rules_pass():
    post = "Small-batch roast, shipped mid-week. No speeches."
    llm = MockLLMClient(evaluate_response=({"score": 88, "feedback": []}, None))
    pipeline = BrandVoiceGatePipeline(PostGenerator(llm), BrandVoiceEvaluator(llm), AuditStore())
    result = await pipeline.validate_post(topic="Manual edit", post=post)
    assert result.decision == Decision.PUBLISH
    assert llm.evaluate_calls == 1
    assert result.generated_post == "<p>Small-batch roast, shipped mid-week. No speeches.</p>"
