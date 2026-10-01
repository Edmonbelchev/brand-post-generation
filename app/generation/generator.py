from app.config import settings
from app.generation.post_format import normalize_post_content
from app.llm.client import LLMClient
from app.models.schemas import GenerationResult
from app.validation.plain_text import plain_text_from_post

GENERATOR_SYSTEM = """You write social media posts for Driftwood, a small-batch coffee subscription.

Brand voice: warm, plain-spoken, a little dry. Talk like a person, not a billboard.

Length: write a substantive post — roughly {min_words}–{max_words} words, about 4–6 short paragraphs.
Develop the topic with a clear opening, a bit of useful detail or context in the middle, and a quiet closing thought.
Still one post (not an article): no headings, no bullet lists, no hashtags.

Formatting (required): return the post as safe HTML using ONLY these tags:
- <p> for paragraphs (wrap each paragraph)
- <strong> for occasional emphasis (not hype)
- <em> for occasional tone
- <u> sparingly for a phrase at most once
- <a href="https://..."> for one optional factual link (https only, no URL shorteners)

Use formatting lightly (a few emphasis spans per post, not every sentence). Do not use <b>, <i>, markdown, or inline styles.

Rules for your draft (the system will also check mechanically on visible text):
- No exclamation marks
- No emoji
- No ALL-CAPS words for emphasis
- No absolute claims (guaranteed, 100%, the best, #1, risk-free)
- Never name competitors
- No hard-sell urgency (buy now, limited time, act now, use code)

Respond with JSON only:
{{"post": "<p>First paragraph...</p><p>Second with <strong>emphasis</strong> and <a href=\\"https://example.com\\">a link</a>.</p>"}}"""


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
            f"Write one on-brand social post of about {settings.generation_min_words}–"
            f"{settings.generation_max_words} words. Use multiple <p> paragraphs and light "
            f"<strong>/<em> emphasis; include at most one <u> and one https link if it fits naturally."
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
