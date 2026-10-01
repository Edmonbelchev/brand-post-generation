import pytest

from app.validation.hard_rules.validator import validate_hard_rules


@pytest.mark.parametrize(
    "snippet,rule_substring",
    [
        ("We think this might be the best cup you have this week.", "absolute_claim"),
        ("Save 100% of your disappointment.", "absolute_claim"),
        ("It is guaranteed to arrive.", "absolute_claim"),
        ("Starbucks wishes they roasted like this.", "competitor_mention"),
        ("Buy now before we run out.", "hard_sell"),
        ("Limited time offer on subscriptions.", "hard_sell"),
        ("Act now and subscribe.", "hard_sell"),
        ("Use code DRIFT at checkout.", "hard_sell"),
        ("Coffee is good!", "exclamation_mark"),
    ],
)
def test_reject_patterns(snippet: str, rule_substring: str):
    result = validate_hard_rules(snippet)
    assert not result.passed
    assert any(v.rule == rule_substring for v in result.violations)


def test_emoji_rejected():
    result = validate_hard_rules("Morning coffee ☕ hits different.")
    assert not result.passed
    assert any(v.rule == "emoji" for v in result.violations)


def test_all_caps_hype_rejected():
    result = validate_hard_rules("This roast is AMAZING and BOLD.")
    assert not result.passed
    assert any(v.rule == "all_caps_hype" for v in result.violations)


def test_valid_post_passes():
    post = (
        "Freshly roasted beans taste different because the oils are still lively. "
        "We ship small batches each week. No billboards required."
    )
    result = validate_hard_rules(post)
    assert result.passed
    assert result.violations == []


def test_empty_post_fails():
    result = validate_hard_rules("   ")
    assert not result.passed
    assert any(v.rule == "empty_post" for v in result.violations)
