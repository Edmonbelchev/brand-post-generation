"""
Invariant: no content containing a non-negotiable violation can ever reach PUBLISH.
"""

import pytest

from app.decision.engine import decide
from app.models.schemas import BrandVoiceResult, Decision, GenerationResult, HardRulesResult
from app.pipeline import BrandVoiceGatePipeline
from app.generation.generator import PostGenerator
from app.validation.brand_voice.evaluator import BrandVoiceEvaluator
from app.validation.hard_rules.validator import validate_hard_rules
from tests.mocks import MockLLMClient

VIOLATING_POSTS = [
    "We are the best roasters in town.",
    "Guaranteed freshness every time.",
    "100% satisfaction or your money back.",
    "Better than Starbucks, honestly.",
    "Buy now and taste the difference.",
    "Limited time only on this blend.",
    "Act now!",
    "Use code FRESH.",
    "Wow!",
    "Great coffee ☕",
    "This is AMAZING coffee.",
]


@pytest.mark.parametrize("post", VIOLATING_POSTS)
def test_hard_rules_fail_for_violations(post: str):
    result = validate_hard_rules(post)
    assert not result.passed


@pytest.mark.parametrize("post", VIOLATING_POSTS)
def test_decision_never_publish_with_violations(post: str):
    hard = validate_hard_rules(post)
    decision, _ = decide(
        generation=GenerationResult(success=True, post=post),
        hard_rules=hard,
        brand_voice=BrandVoiceResult(score=100, passed=True),
    )
    assert decision != Decision.PUBLISH
    if not hard.passed:
        assert decision == Decision.REJECT


@pytest.mark.asyncio
@pytest.mark.parametrize("post", VIOLATING_POSTS)
async def test_pipeline_never_publish_with_violations(post: str):
    llm = MockLLMClient(
        generate_response=({"post": post}, None),
        evaluate_response=({"score": 100, "feedback": []}, None),
    )
    pipeline = BrandVoiceGatePipeline(PostGenerator(llm), BrandVoiceEvaluator(llm))
    result = await pipeline.run("invariant test")
    assert result.decision != Decision.PUBLISH
