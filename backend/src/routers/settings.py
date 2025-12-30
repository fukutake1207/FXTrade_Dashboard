from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.narrative_provider import get_provider, set_provider

router = APIRouter(
    prefix="/settings",
    tags=["settings"]
)


class NarrativeProviderResponse(BaseModel):
    provider: str


class NarrativeProviderRequest(BaseModel):
    provider: str


@router.get("/narrative-provider", response_model=NarrativeProviderResponse)
async def get_narrative_provider():
    return {"provider": get_provider()}


@router.put("/narrative-provider", response_model=NarrativeProviderResponse)
async def update_narrative_provider(payload: NarrativeProviderRequest):
    try:
        provider = set_provider(payload.provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"provider": provider}
