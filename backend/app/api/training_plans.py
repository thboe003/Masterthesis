"""Training plan generation endpoints."""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from app.schemas import TrainingPlan, TrainingPlanRequest
from app.services.llm import LLMProvider, LLMResponseError, LLMUnavailableError, get_llm_provider
from app.services.plan_generator import debug_prompt, generate_training_plan as run_generation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/training-plans", tags=["training-plans"])


def llm_provider_dependency() -> LLMProvider:
    try:
        return get_llm_provider()
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/generate", response_model=TrainingPlan)
async def generate_training_plan(
    request: TrainingPlanRequest,
    provider: LLMProvider = Depends(llm_provider_dependency),
) -> TrainingPlan:
    """
    Generate a training plan with the configured LLM (see ``LLM_PROVIDER``).

    The parameters are the ones selected in the profile form. The response
    contains the plan plus ``generation`` metadata (provider, model, latency,
    tokens, warnings).
    """
    try:
        return await run_generation(request, provider)
    except LLMUnavailableError as exc:
        logger.error("LLM unavailable: %s", exc)
        raise HTTPException(status_code=503, detail=f"Sprachmodell nicht erreichbar: {exc}") from exc
    except LLMResponseError as exc:
        logger.error("LLM returned unusable output: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/llm-info")
async def llm_info(provider: LLMProvider = Depends(llm_provider_dependency)) -> Dict[str, str]:
    """Which provider and model are currently configured."""
    return provider.describe()


@router.post("/prompt-preview")
async def prompt_preview(request: TrainingPlanRequest) -> Dict[str, str]:
    """Show the prompts that would be sent to the LLM, without calling it."""
    return debug_prompt(request)


@router.get("/{plan_id}", response_model=TrainingPlan)
async def get_training_plan(plan_id: str) -> TrainingPlan:
    """Retrieve a specific training plan."""
    # TODO: Implement database retrieval
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.put("/{plan_id}", response_model=TrainingPlan)
async def update_training_plan(
    plan_id: str, 
    plan_update: TrainingPlan
) -> TrainingPlan:
    """Update an existing training plan."""
    # TODO: Implement plan update
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/{plan_id}")
async def delete_training_plan(plan_id: str) -> dict:
    """Delete a training plan."""
    # TODO: Implement plan deletion
    raise HTTPException(status_code=501, detail="Not implemented yet")
