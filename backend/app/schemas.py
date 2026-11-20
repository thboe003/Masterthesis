"""
Pydantic schemas shared by the API and the plan generator.

Field names match the Angular models in ``frontend/src/app/models/index.ts``.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

ExperienceLevel = Literal["beginner", "intermediate", "advanced"]
Intensity = Literal["low", "medium", "high"]
Goal = Literal["strength", "flexibility", "new_moves", "endurance"]


# --------------------------------------------------------------------------- #
# Request
# --------------------------------------------------------------------------- #
class TrainingPlanRequest(BaseModel):
    """Parameters the user selects in the profile form."""

    age: int = Field(..., ge=18, le=100)
    gender: Optional[str] = None
    experience_level: ExperienceLevel
    fitness_level: int = Field(..., ge=1, le=10)
    available_days_per_week: int = Field(..., ge=1, le=7)
    hours_per_session: Optional[float] = Field(None, gt=0, le=4)
    goals: List[Goal] = Field(..., min_length=1)
    injuries_or_limitations: Optional[str] = Field(None, max_length=1000)
    duration_weeks: int = Field(4, ge=1, le=12)

    @field_validator("gender", "injuries_or_limitations", mode="before")
    @classmethod
    def empty_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("hours_per_session", mode="before")
    @classmethod
    def empty_hours_to_none(cls, value):
        return None if value in ("", None) else value


# --------------------------------------------------------------------------- #
# What the LLM has to return (validated before it reaches the client)
# --------------------------------------------------------------------------- #
def _normalize_intensity(value):
    mapping = {
        "niedrig": "low", "leicht": "low", "easy": "low", "light": "low",
        "mittel": "medium", "moderate": "medium", "moderat": "medium",
        "hoch": "high", "hard": "high", "intense": "high",
    }
    if isinstance(value, str):
        value = value.strip().lower()
        return mapping.get(value, value)
    return value


class LLMExercise(BaseModel):
    exercise_id: Optional[str] = None
    name: str
    duration_minutes: int = Field(..., ge=1, le=120)
    sets: Optional[int] = Field(None, ge=1, le=20)
    repetitions: Optional[int] = Field(None, ge=1, le=200)
    rest_seconds: int = Field(60, ge=0, le=600)
    intensity: Intensity = "medium"
    notes: Optional[str] = None

    @field_validator("intensity", mode="before")
    @classmethod
    def normalize_intensity(cls, value):
        return _normalize_intensity(value)

    @field_validator("sets", "repetitions", mode="before")
    @classmethod
    def zero_to_none(cls, value):
        return None if value in (0, "", "0") else value


class LLMSession(BaseModel):
    day: int = Field(..., ge=1, le=7)
    title: str
    exercises: List[LLMExercise] = Field(..., min_length=1)


class LLMPlan(BaseModel):
    name: str
    description: str = ""
    focus_area: str
    sessions: List[LLMSession] = Field(..., min_length=1)
    notes: str = ""


# --------------------------------------------------------------------------- #
# Response
# --------------------------------------------------------------------------- #
class TrainingPlanExercise(BaseModel):
    exercise_id: Optional[str] = None
    name: str
    duration_minutes: int
    sets: Optional[int] = None
    repetitions: Optional[int] = None
    rest_seconds: int
    intensity: Intensity
    instructions: Optional[List[str]] = None
    notes: Optional[str] = None
    order: int
    day: int
    session_title: str


class GenerationInfo(BaseModel):
    """Metadata about the generation, useful for the evaluation in the thesis."""

    provider: str
    model: str
    duration_ms: int
    attempts: int
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    catalog_size: int
    unknown_exercises: List[str] = []
    warnings: List[str] = []


class TrainingPlan(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    duration_weeks: int
    focus_area: str
    difficulty_level: ExperienceLevel
    exercises: List[TrainingPlanExercise]
    notes: str = ""
    created_at: str
    is_active: bool = True
    generation: Optional[GenerationInfo] = None
