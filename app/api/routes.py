from fastapi import APIRouter, HTTPException

from app.audit.store import AuditStore
from app.llm.client import OpenAILLMClient
from app.models.schemas import AuditRecord, GenerateRequest, GenerateResponse, ValidateRequest
from app.pipeline import BrandVoiceGatePipeline
from app.generation.generator import PostGenerator
from app.validation.brand_voice.evaluator import BrandVoiceEvaluator

router = APIRouter()
_audit = AuditStore()


def _pipeline() -> BrandVoiceGatePipeline:
    llm = OpenAILLMClient()
    return BrandVoiceGatePipeline(
        generator=PostGenerator(llm),
        evaluator=BrandVoiceEvaluator(llm),
        audit=_audit,
    )


@router.post("/generate", response_model=GenerateResponse)
async def generate_post(body: GenerateRequest) -> GenerateResponse:
    return await _pipeline().run(body.topic)


@router.post("/validate", response_model=GenerateResponse)
async def validate_post(body: ValidateRequest) -> GenerateResponse:
    return await _pipeline().validate_post(topic=body.topic, post=body.post)


@router.get("/audit/{audit_id}", response_model=AuditRecord)
async def get_audit(audit_id: str) -> AuditRecord:
    record = _audit.get(audit_id)
    if not record:
        raise HTTPException(status_code=404, detail="Audit record not found")
    return record


@router.get("/audit", response_model=list[AuditRecord])
async def list_audit(limit: int = 20) -> list[AuditRecord]:
    return _audit.list_recent(limit=min(limit, 100))
