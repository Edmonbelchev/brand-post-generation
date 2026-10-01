import re
from typing import Iterable

from app.models.schemas import HardRulesResult, RuleViolation
from app.validation.hard_rules.config import DEFAULT_HARD_RULES_CONFIG, HardRulesConfig

# Broad emoji detection (common ranges)
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U00002600-\U000026FF"
    "\U00002700-\U000027BF"
    "]+",
    flags=re.UNICODE,
)

# Standalone ALL-CAPS words (2+ letters)
_CAPS_WORD_PATTERN = re.compile(r"\b[A-Z]{2,}\b")


def _find_phrase_violations(
    text: str,
    phrases: Iterable[str],
    rule: str,
    message_prefix: str,
) -> list[RuleViolation]:
    lower = text.lower()
    violations: list[RuleViolation] = []
    for phrase in phrases:
        if phrase in lower:
            violations.append(
                RuleViolation(
                    rule=rule,
                    message=f"{message_prefix}: '{phrase}'",
                )
            )
    return violations


def _check_exclamation(text: str) -> list[RuleViolation]:
    if "!" in text:
        return [
            RuleViolation(
                rule="exclamation_mark",
                message="Contains exclamation mark (not allowed for Driftwood)",
            )
        ]
    return []


def _check_emoji(text: str) -> list[RuleViolation]:
    if _EMOJI_PATTERN.search(text):
        return [
            RuleViolation(
                rule="emoji",
                message="Contains emoji (not allowed for Driftwood)",
            )
        ]
    return []


def _check_all_caps_hype(text: str, config: HardRulesConfig) -> list[RuleViolation]:
    violations: list[RuleViolation] = []
    for match in _CAPS_WORD_PATTERN.finditer(text):
        word = match.group(0)
        if word in config.caps_hype_allowlist:
            continue
        if len(word) >= config.min_caps_hype_word_length:
            violations.append(
                RuleViolation(
                    rule="all_caps_hype",
                    message=f"Contains ALL-CAPS hype: '{word}'",
                )
            )
    return violations


def validate_hard_rules(
    post: str,
    config: HardRulesConfig | None = None,
) -> HardRulesResult:
    """Deterministic validation of non-negotiable Driftwood rules."""
    if config is None:
        config = DEFAULT_HARD_RULES_CONFIG

    if not post or not post.strip():
        return HardRulesResult(
            passed=False,
            violations=[
                RuleViolation(rule="empty_post", message="Generated post is empty"),
            ],
        )

    violations: list[RuleViolation] = []
    violations.extend(
        _find_phrase_violations(
            post,
            config.absolute_claim_phrases,
            "absolute_claim",
            "Contains prohibited absolute claim",
        )
    )
    violations.extend(
        _find_phrase_violations(
            post,
            config.competitor_names,
            "competitor_mention",
            "Names a competitor",
        )
    )
    violations.extend(
        _find_phrase_violations(
            post,
            config.hard_sell_phrases,
            "hard_sell",
            "Contains hard-sell language",
        )
    )
    violations.extend(_check_exclamation(post))
    violations.extend(_check_emoji(post))
    violations.extend(_check_all_caps_hype(post, config))

    return HardRulesResult(passed=len(violations) == 0, violations=violations)
