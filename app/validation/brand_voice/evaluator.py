from app.config import settings
from app.llm.client import LLMClient
from app.models.schemas import BrandVoiceResult

EVALUATOR_SYSTEM = """You evaluate whether copy matches the Driftwood coffee brand voice.

Driftwood is warm, plain-spoken, slightly dry, conversational — like a person, not a billboard.

Score from 0-100 how well the post matches that voice on:
- warmth
- plain language
- conversational tone
- subtle dry personality
- not sounding like generic marketing

Do NOT decide publish/reject on legal or policy rules; only brand voice fit.

Respond with JSON only:
{
  "score": <integer 0-100>,
  "feedback": ["<optional short notes>"]
}"""


class BrandVoiceEvaluator:
    def __init__(self, llm: LLMClient, threshold: int | None = None) -> None:
        self._llm = llm
        self._threshold = threshold if threshold is not None else settings.brand_voice_threshold

    async def evaluate(self, post: str) -> BrandVoiceResult:
        data, err = await self._llm.chat_json(
            system=EVALUATOR_SYSTEM,
            user=f"Post to evaluate:\n\n{post}",
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
