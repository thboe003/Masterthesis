"""
LLM-based training plan generation.

Pipeline:
    1. pick relevant exercises from the catalog (grounding)
    2. build system + user prompt from the UI parameters
    3. call the configured LLM and parse its JSON answer
    4. validate against ``LLMPlan``; on failure retry once with the error message
    5. post-process: map exercises to catalog IDs, check plausibility, build the
       API response
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from pydantic import ValidationError

from app.schemas import GenerationInfo, LLMPlan, TrainingPlan, TrainingPlanExercise, TrainingPlanRequest
from app.services.exercise_catalog import CatalogExercise, load_catalog, select_candidates
from app.services.llm import LLMProvider, LLMResponseError, extract_json

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = int(os.getenv("LLM_MAX_ATTEMPTS", "2"))

GOAL_LABELS = {
    "strength": "Kraft aufbauen",
    "flexibility": "Flexibilität verbessern",
    "new_moves": "Neue Pole-Moves lernen",
    "endurance": "Ausdauer verbessern",
}
LEVEL_LABELS = {
    "beginner": "Anfänger (0-6 Monate Pole-Erfahrung)",
    "intermediate": "Fortgeschritten (6-24 Monate Pole-Erfahrung)",
    "advanced": "Erfahren (mehr als 2 Jahre Pole-Erfahrung)",
}

SYSTEM_PROMPT = """You are an experienced pole sport coach and certified strength & conditioning trainer.
You create safe, progressive, personalised weekly training plans for pole sport athletes.

Rules:
- Use ONLY exercises from the provided catalog and copy their exercise_id exactly.
- Create exactly one session per available training day (day = 1..N).
- Every session starts with a warm-up and ends with a cool-down / stretching block.
- The sum of duration_minutes per session must fit the available session length.
- Match difficulty to the experience and fitness level. Never prescribe moves above the user's level.
- Respect injuries and limitations strictly: leave out exercises that could aggravate them and mention adaptations in "notes".
- Use sets/repetitions for strength exercises and duration_minutes for holds, stretching and pole practice.
- Write all human-readable text (name, description, focus_area, title, notes) in German.
- Answer with a single JSON object only, no Markdown, no explanation.

JSON format:
{
  "name": "string, short plan title",
  "description": "string, 1-2 sentences",
  "focus_area": "string, main focus",
  "sessions": [
    {
      "day": 1,
      "title": "string",
      "exercises": [
        {
          "exercise_id": "id from catalog",
          "name": "exercise name",
          "duration_minutes": 10,
          "sets": 3,
          "repetitions": 10,
          "rest_seconds": 60,
          "intensity": "low | medium | high",
          "notes": "short coaching cue"
        }
      ]
    }
  ],
  "notes": "string, general advice incl. progression over the weeks and safety"
}"""


def build_user_prompt(request: TrainingPlanRequest, candidates: List[CatalogExercise]) -> str:
    minutes = int(round((request.hours_per_session or 1.0) * 60))
    goals = ", ".join(GOAL_LABELS.get(g, g) for g in request.goals)
    lines = [
        "Create a training plan for this athlete:",
        f"- Age: {request.age}",
        f"- Gender: {request.gender or 'not specified'}",
        f"- Pole experience: {LEVEL_LABELS[request.experience_level]}",
        f"- Fitness level: {request.fitness_level}/10",
        f"- Training days per week: {request.available_days_per_week}",
        f"- Session length: {minutes} minutes",
        f"- Goals: {goals}",
        f"- Injuries / limitations: {request.injuries_or_limitations or 'none'}",
        f"- Plan duration: {request.duration_weeks} weeks (the weekly structure repeats; describe the progression in notes)",
        "",
        "Exercise catalog (exercise_id | name | category | level | primary muscles):",
        *(c.prompt_line() for c in candidates),
    ]
    return "\n".join(lines)


def _match_exercise(
    exercise_id: Optional[str], name: str, by_id: Dict[str, CatalogExercise], by_name: Dict[str, CatalogExercise]
) -> Optional[CatalogExercise]:
    if exercise_id and exercise_id in by_id:
        return by_id[exercise_id]
    if exercise_id and exercise_id.lower() in by_id:
        return by_id[exercise_id.lower()]
    return by_name.get(name.strip().lower())


def _post_process(
    plan: LLMPlan, request: TrainingPlanRequest, catalog: List[CatalogExercise]
) -> Tuple[List[TrainingPlanExercise], List[str], List[str]]:
    by_id = {c.id: c for c in catalog}
    by_id.update({c.id.lower(): c for c in catalog})
    by_name = {c.name.strip().lower(): c for c in catalog}

    exercises: List[TrainingPlanExercise] = []
    unknown: List[str] = []
    warnings: List[str] = []
    session_limit = (request.hours_per_session or 1.0) * 60

    sessions = sorted(plan.sessions, key=lambda s: s.day)
    if len(sessions) != request.available_days_per_week:
        warnings.append(
            f"Modell hat {len(sessions)} Einheiten statt {request.available_days_per_week} erzeugt."
        )

    order = 0
    for session in sessions:
        total = sum(e.duration_minutes for e in session.exercises)
        if total > session_limit * 1.2:
            warnings.append(f"Tag {session.day}: {total} min geplant, verfügbar sind {session_limit:.0f} min.")
        for item in session.exercises:
            order += 1
            match = _match_exercise(item.exercise_id, item.name, by_id, by_name)
            if match is None:
                unknown.append(item.name)
            exercises.append(
                TrainingPlanExercise(
                    exercise_id=match.id if match else None,
                    name=match.name if match else item.name,
                    duration_minutes=item.duration_minutes,
                    sets=item.sets,
                    repetitions=item.repetitions,
                    rest_seconds=item.rest_seconds,
                    intensity=item.intensity,
                    instructions=(match.instructions or None) if match else None,
                    notes=item.notes,
                    order=order,
                    day=session.day,
                    session_title=session.title,
                )
            )
    return exercises, unknown, warnings


async def generate_training_plan(
    request: TrainingPlanRequest,
    provider: LLMProvider,
    catalog: Optional[List[CatalogExercise]] = None,
    seed: Optional[int] = None,
    user_id: str = "anonymous",
) -> TrainingPlan:
    """Generate a validated training plan with the given LLM provider."""
    catalog = catalog if catalog is not None else load_catalog()
    candidates = select_candidates(catalog, request.experience_level, list(request.goals), seed=seed)
    user_prompt = build_user_prompt(request, candidates)

    started = time.perf_counter()
    input_tokens = output_tokens = 0
    last_error: Optional[str] = None
    plan: Optional[LLMPlan] = None
    attempts = 0
    model_name = provider.model

    for attempts in range(1, MAX_ATTEMPTS + 1):
        prompt = user_prompt
        if last_error:
            prompt += (
                "\n\nYour previous answer was invalid:\n"
                f"{last_error}\n"
                "Return the complete plan again as valid JSON in the required format."
            )
        result = await provider.complete_json(SYSTEM_PROMPT, prompt)
        model_name = result.model
        input_tokens += result.input_tokens or 0
        output_tokens += result.output_tokens or 0
        try:
            plan = LLMPlan.model_validate(extract_json(result.text))
            break
        except (LLMResponseError, ValidationError) as exc:
            last_error = str(exc)[:1500]
            logger.warning("LLM attempt %d returned an invalid plan: %s", attempts, last_error)

    if plan is None:
        raise LLMResponseError(
            f"Das Modell hat nach {attempts} Versuchen keinen gültigen Plan geliefert. Letzter Fehler: {last_error}"
        )

    exercises, unknown, warnings = _post_process(plan, request, catalog)
    duration_ms = int((time.perf_counter() - started) * 1000)

    return TrainingPlan(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=plan.name,
        description=plan.description or None,
        duration_weeks=request.duration_weeks,
        focus_area=plan.focus_area,
        difficulty_level=request.experience_level,
        exercises=exercises,
        notes=plan.notes,
        created_at=datetime.now(timezone.utc).isoformat(),
        is_active=True,
        generation=GenerationInfo(
            provider=provider.name,
            model=model_name,
            duration_ms=duration_ms,
            attempts=attempts,
            input_tokens=input_tokens or None,
            output_tokens=output_tokens or None,
            catalog_size=len(candidates),
            unknown_exercises=unknown,
            warnings=warnings,
        ),
    )


def debug_prompt(request: TrainingPlanRequest, seed: Optional[int] = None) -> Dict[str, str]:
    """Return the prompts that would be sent (for inspection / the thesis appendix)."""
    candidates = select_candidates(load_catalog(), request.experience_level, list(request.goals), seed=seed)
    return {"system_prompt": SYSTEM_PROMPT, "user_prompt": build_user_prompt(request, candidates)}


__all__ = ["generate_training_plan", "build_user_prompt", "debug_prompt", "SYSTEM_PROMPT"]
