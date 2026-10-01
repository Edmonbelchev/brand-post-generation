import pytest

from app.audit.store import AuditStore
from app.config import settings
from app.generation.generator import PostGenerator
from app.models.schemas import Decision
from app.pipeline import BrandVoiceGatePipeline
from app.validation.brand_voice.evaluator import BrandVoiceEvaluator
from tests.mocks import MockLLMClient


@pytest.mark.asyncio
async def test_valid_post_publish():
    llm = MockLLMClient(
        generate_response=(
            {"post": "Small-batch coffee, roasted mid-week. Tastes like someone cared."},
            None,
        ),
        evaluate_response=({"score": 91, "feedback": []}, None),
    )
    pipeline = BrandVoiceGatePipeline(
        PostGenerator(llm),
        BrandVoiceEvaluator(llm, threshold=80),
        AuditStore(),
    )
    result = await pipeline.run("Why fresh roast matters")
    assert result.decision == Decision.PUBLISH
    assert result.post is not None
    assert result.checks.hard_rules.passed
    assert result.checks.brand_voice.passed


@pytest.mark.asyncio
async def test_bad_model_content_rejected_deterministically():
    bad = (
        "Our coffee is the BEST and is guaranteed to improve your morning. Buy now!"
    )
    llm = MockLLMClient(
        generate_response=({"post": bad}, None),
        evaluate_response=({"score": 100, "feedback": []}, None),
    )
    pipeline = BrandVoiceGatePipeline(
        PostGenerator(llm),
        BrandVoiceEvaluator(llm),
        AuditStore(),
    )
    result = await pipeline.run("Hype topic")
    assert result.decision == Decision.REJECT
    assert result.post is None
    assert not result.checks.hard_rules.passed
    assert llm.evaluate_calls == 0


@pytest.mark.asyncio
async def test_generation_timeout_hold():
    llm = MockLLMClient(generate_response=(None, "LLM request timed out"))
    pipeline = BrandVoiceGatePipeline(PostGenerator(llm), BrandVoiceEvaluator(llm))
    result = await pipeline.run("Topic")
    assert result.decision == Decision.HOLD
    assert result.post is None


@pytest.mark.asyncio
async def test_malformed_generation_hold():
    llm = MockLLMClient(generate_response=({"not_post": "x"}, None))
    pipeline = BrandVoiceGatePipeline(PostGenerator(llm), BrandVoiceEvaluator(llm))
    result = await pipeline.run("Topic")
    assert result.decision == Decision.HOLD


@pytest.mark.asyncio
async def test_brand_voice_below_threshold_hold():
    post = "Quiet morning, decent mug, no speeches."
    llm = MockLLMClient(
        generate_response=({"post": post}, None),
        evaluate_response=({"score": 62, "feedback": ["Too promotional."]}, None),
    )
    pipeline = BrandVoiceGatePipeline(PostGenerator(llm), BrandVoiceEvaluator(llm, threshold=80))
    result = await pipeline.run("Topic")
    assert result.decision == Decision.HOLD
    assert result.checks.hard_rules.passed


@pytest.mark.asyncio
async def test_evaluator_failure_hold():
    post = "Quiet morning, decent mug, no speeches."
    llm = MockLLMClient(
        generate_response=({"post": post}, None),
        evaluate_response=(None, "LLM returned malformed JSON"),
    )
    pipeline = BrandVoiceGatePipeline(PostGenerator(llm), BrandVoiceEvaluator(llm))
    result = await pipeline.run("Topic")
    assert result.decision == Decision.HOLD


@pytest.mark.asyncio
async def test_audit_record_created():
    llm = MockLLMClient()
    audit = AuditStore()
    pipeline = BrandVoiceGatePipeline(PostGenerator(llm), BrandVoiceEvaluator(llm), audit)
    result = await pipeline.run("Audit topic")
    record = audit.get(result.audit_id)
    assert record is not None
    assert record.topic == "Audit topic"
    assert record.decision == result.decision
