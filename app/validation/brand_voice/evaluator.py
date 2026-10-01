from app.config import settings
from app.llm.client import LLMClient
from app.models.schemas import BrandVoiceResult

EVALUATOR_SYSTEM = """You score how well copy matches Driftwood Coffee's brand voice.

Driftwood voice: warm, plain-spoken, slightly dry, conversational — a person talking, not a billboard or brochure.

## Score rubric (use the full range)
- **90–100**: Sounds like a calm, witty friend who knows coffee. Simple words, natural rhythm, subtle dry edge. Not salesy.
- **80–89**: Clearly on-brand; minor polish issues only (slightly formal word here or there).
- **70–79**: Warm but too poetic, formal, elaborate, or "marketing blog" — enthusiasm or adjectives outweigh plain speech.
- **50–69**: Mostly generic brand/marketing copy.
- **Below 50**: Wrong tone entirely.

## What to reward
- Concrete, useful details stated simply
- Understatement and even tone
- Sentences you might say out loud without cringing

## What to penalize (each major issue often caps the score around 70–75)
- Poetic/literary phrasing, metaphor stacks, flowery descriptions
- Marketing buzzwords (discover, elevate, journey, indulge, experience, perfect, premium, passionate)
- Corporate or billboard cadence ("At Driftwood, we…" as hype)
- Cheerleading enthusiasm instead of dry warmth

Policy/legal rules (claims, competitors, etc.) are handled elsewhere — score voice only.

Respond with JSON only:
{
  "score": <integer 0-100>,
  "feedback": ["<1-3 short, specific notes; say what to simplify if below 80>"]
}"""


class BrandVoiceEvaluator:
    def __init__(self, llm: LLMClient, threshold: int | None = None) -> None:
        self._llm = llm
        self._threshold = threshold if threshold is not None else settings.brand_voice_threshold

    async def evaluate(self, post: str) -> BrandVoiceResult:
        data, err = await self._llm.chat_json(
            system=EVALUATOR_SYSTEM,
            user=(
                "Evaluate visible text only (formatting tags already removed).\n\n"
                f"Post:\n\n{post}"
            ),
        )
        if err:
            return BrandVoiceResult(passed=False, error=err, feedback=[err])

        if data is None:
            return BrandVoiceResult(
                passed=False,
                error="No evaluation data",
                feedback=["Brand voice evaluation failed"],
            )

        score_raw = data.get("score")
        feedback_raw = data.get("feedback", [])

        if not isinstance(score_raw, (int, float)):
            return BrandVoiceResult(
                passed=False,
                error="Missing or invalid 'score' in evaluator response",
                feedback=["Brand voice evaluator returned malformed output"],
            )

        score = int(max(0, min(100, score_raw)))
        feedback: list[str] = []
        if isinstance(feedback_raw, list):
            feedback = [str(f) for f in feedback_raw if f]

        passed = score >= self._threshold
        if not passed and not feedback:
            feedback.append(f"Brand voice score {score} is below threshold {self._threshold}")

        return BrandVoiceResult(score=score, passed=passed, feedback=feedback)
