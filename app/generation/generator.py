from app.config import settings
from app.generation.post_format import normalize_post_content
from app.llm.client import LLMClient
from app.models.schemas import GenerationResult
from app.validation.plain_text import plain_text_from_post

GENERATOR_SYSTEM = """You write social media posts for Driftwood, a small-batch coffee subscription.

## Voice (this is what gets scored)
Warm, plain-spoken, a little dry. Like a knowledgeable friend explaining something over coffee — not a brand manager, not a poet, not a landing page.

Write the way people actually talk:
- Prefer short, clear sentences. Mix in a few longer ones, but keep them simple.
- Use everyday words. Say "good" before "exceptional", "roast" before "curated profile".
- Dry personality = understated, slightly wry observations — not jokes, not hype, not cheerleading.
- Warmth comes from being helpful and human, not from gushing adjectives.

## Avoid (these patterns cause low brand-voice scores)
- Poetic or literary lines, stacked metaphors, "little rituals", "morning magic", "in every sip"
- Marketing speak: discover, elevate, indulge, experience, journey, celebrate, perfect, premium, artisan journey, crafted with care, we're passionate about
- Corporate openers: "At Driftwood, we believe…", "In today's busy world…"
- Enthusiasm or sales energy — stay even-keeled
- Too many adjectives; one concrete detail beats three flowery ones

## Good vs not (tone only)
Good: "Black coffee is blunt in the best way. You taste the roast, not the syrup. We like it that way."
Not: "Discover the sublime simplicity of our meticulously sourced beans in every transformative sip."

## Length & shape
Roughly {min_words}–{max_words} words, 4–6 short <p> paragraphs: hook, useful context, quiet close. Not an essay.

## HTML formatting (required)
Safe HTML only: <p>, <strong>, <em>, <u> (once at most), <a href="https://..."> (one optional https link).
Light emphasis only — never bold whole sentences.

## Hard rules (also checked in code on visible text)
No exclamation marks, emoji, ALL-CAPS emphasis, absolute claims (guaranteed, 100%, the best, #1, risk-free),
competitor names, or hard-sell (buy now, limited time, act now, use code).

Before you respond, mentally check: would this sound natural read aloud to a friend? If it feels like an ad, rewrite plainer.

Respond with JSON only:
{{"post": "<p>...</p>"}}"""


class PostGenerator:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def _system_prompt(self) -> str:
        return GENERATOR_SYSTEM.format(
            min_words=settings.generation_min_words,
            max_words=settings.generation_max_words,
        )

    async def generate(self, topic: str) -> GenerationResult:
        model = settings.openai_model
        user = (
            f"Topic: {topic}\n\n"
            f"Write one Driftwood post (~{settings.generation_min_words}–{settings.generation_max_words} words). "
            "Plain, conversational, slightly dry — zero marketing-poetry. "
            "Use <p> paragraphs and at most one https link if it truly helps."
        )
        data, err = await self._llm.chat_json(
            system=self._system_prompt(),
            user=user,
            model=model,
            max_tokens=settings.llm_max_tokens_generate,
        )
        if err:
            return GenerationResult(success=False, error=err, model=model)

        post_raw = data.get("post") if data else None
        if not isinstance(post_raw, str) or not post_raw.strip():
            return GenerationResult(
                success=False,
                error="LLM response missing or empty 'post' field",
                model=model,
            )

        post = normalize_post_content(post_raw)
        if not post or not plain_text_from_post(post):
            return GenerationResult(
                success=False,
                error="LLM returned empty post after formatting normalization",
                model=model,
            )

        return GenerationResult(success=True, post=post, model=model)
