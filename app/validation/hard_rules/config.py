from dataclasses import dataclass, field


@dataclass(frozen=True)
class HardRulesConfig:
    """Central configuration for deterministic brand rules."""

    absolute_claim_phrases: tuple[str, ...] = (
        "guaranteed",
        "100%",
        "risk-free",
        "the best",
        "#1",
        "number one",
        "best coffee",
        "never fails",
        "always perfect",
    )

    hard_sell_phrases: tuple[str, ...] = (
        "buy now",
        "limited time",
        "act now",
        "use code",
        "order today",
        "don't miss",
        "last chance",
        "while supplies last",
    )

    competitor_names: tuple[str, ...] = (
        "starbucks",
        "blue bottle",
        "nespresso",
        "peet's",
        "peets",
        "dunkin",
        "lavazza",
        "illy",
        "counter culture",
    )

    # Whole-word ALL-CAPS tokens (2+ letters) treated as hype, except common acronyms
    caps_hype_allowlist: frozenset[str] = frozenset(
        {"US", "UK", "EU", "AM", "PM", "OK", "ID", "TV", "AI", "FAQ"}
    )

    min_caps_hype_word_length: int = 2


DEFAULT_HARD_RULES_CONFIG = HardRulesConfig()
