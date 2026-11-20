"""
Tests for the LLM plan generation. They use a fake provider, so no model or
network is needed:  cd backend && pytest tests/test_plan_generator.py
"""

import asyncio
import json

import pytest

from app.schemas import TrainingPlanRequest
from app.services.exercise_catalog import CatalogExercise, load_catalog, select_candidates
from app.services.llm import LLMProvider, LLMResponseError, LLMResult, create_llm_provider, extract_json
from app.services.plan_generator import build_user_prompt, generate_training_plan

CATALOG = [
    CatalogExercise("pole_basic_grip", "Basic Pole Grip", "technique", "beginner", "pole", ["forearm"], ["Grip"], True),
    CatalogExercise("Push-Ups", "Push-Ups", "strength", "beginner", "body only", ["chest"]),
    CatalogExercise("Hamstring_Stretch", "Hamstring Stretch", "stretching", "beginner", "body only", ["hamstrings"]),
    CatalogExercise("Barbell_Squat", "Barbell Squat", "strength", "beginner", "barbell", ["quadriceps"]),
    CatalogExercise("Handstand_Pushup", "Handstand Push-Up", "strength", "advanced", "body only", ["shoulders"]),
]


def make_request(**overrides):
    data = dict(
        age=28, experience_level="beginner", fitness_level=5, available_days_per_week=2,
        hours_per_session=1, goals=["strength", "flexibility"], injuries_or_limitations="",
    )
    data.update(overrides)
    return TrainingPlanRequest(**data)


def llm_plan(days=2):
    return {
        "name": "Grundlagen Kraft & Flexibilität",
        "description": "Ein Einstiegsplan.",
        "focus_area": "Kraft",
        "sessions": [
            {
                "day": d,
                "title": f"Einheit {d}",
                "exercises": [
                    {"exercise_id": "pole_basic_grip", "name": "Basic Pole Grip", "duration_minutes": 10, "intensity": "niedrig"},
                    {"exercise_id": "push-ups", "name": "Push-Ups", "duration_minutes": 15, "sets": 3, "repetitions": 8, "intensity": "medium"},
                    {"exercise_id": "???", "name": "Hamstring Stretch", "duration_minutes": 10, "intensity": "low"},
                    {"exercise_id": "made_up", "name": "Fantasieübung", "duration_minutes": 5, "intensity": "high"},
                ],
            }
            for d in range(1, days + 1)
        ],
        "notes": "Langsam steigern.",
    }


class FakeProvider(LLMProvider):
    name = "fake"

    def __init__(self, answers):
        super().__init__("fake-model")
        self.answers = list(answers)
        self.prompts = []

    async def complete_json(self, system_prompt, user_prompt):
        self.prompts.append(user_prompt)
        return LLMResult(text=self.answers.pop(0), provider=self.name, model=self.model, input_tokens=100, output_tokens=50)


def test_request_accepts_form_values():
    req = TrainingPlanRequest(
        age="30", experience_level="beginner", fitness_level="5", available_days_per_week="3",
        hours_per_session="", goals=["endurance"], gender="", injuries_or_limitations="  ",
    )
    assert req.available_days_per_week == 3
    assert req.hours_per_session is None and req.gender is None and req.injuries_or_limitations is None


def test_extract_json_handles_code_fences_and_text():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Hier ist der Plan: {"a": 2} Viel Spaß!') == {"a": 2}
    with pytest.raises(LLMResponseError):
        extract_json("kein json")


def test_candidates_respect_level_and_equipment():
    ids = {c.id for c in select_candidates(CATALOG, "beginner", ["strength"], seed=1)}
    assert "Barbell_Squat" not in ids  # equipment not pole friendly
    assert "Handstand_Pushup" not in ids  # above level
    assert {"pole_basic_grip", "Push-Ups", "Hamstring_Stretch"} <= ids


def test_prompt_contains_parameters_and_catalog():
    prompt = build_user_prompt(make_request(injuries_or_limitations="Schulter links"), CATALOG[:2])
    assert "Training days per week: 2" in prompt
    assert "Session length: 60 minutes" in prompt
    assert "Schulter links" in prompt
    assert "pole_basic_grip | Basic Pole Grip" in prompt


def test_generate_maps_exercises_and_collects_metadata():
    provider = FakeProvider([json.dumps(llm_plan())])
    plan = asyncio.run(generate_training_plan(make_request(), provider, catalog=CATALOG, seed=1))

    assert plan.difficulty_level == "beginner"
    assert len(plan.exercises) == 8
    assert [e.order for e in plan.exercises] == list(range(1, 9))
    first = plan.exercises[0]
    assert first.intensity == "low" and first.instructions == ["Grip"]
    assert plan.exercises[1].exercise_id == "Push-Ups"  # case-insensitive id match
    assert plan.exercises[2].exercise_id == "Hamstring_Stretch"  # matched by name
    assert plan.exercises[3].exercise_id is None
    assert plan.generation.unknown_exercises == ["Fantasieübung", "Fantasieübung"]
    assert plan.generation.attempts == 1 and plan.generation.input_tokens == 100
    assert plan.generation.warnings == []


def test_generate_retries_after_invalid_answer():
    provider = FakeProvider(["das ist kein Plan", json.dumps(llm_plan())])
    plan = asyncio.run(generate_training_plan(make_request(), provider, catalog=CATALOG))
    assert plan.generation.attempts == 2
    assert "previous answer was invalid" in provider.prompts[1]


def test_generate_fails_after_max_attempts():
    provider = FakeProvider(["{}", "{}"])
    with pytest.raises(LLMResponseError):
        asyncio.run(generate_training_plan(make_request(), provider, catalog=CATALOG))


def test_warns_on_wrong_session_count_and_length():
    plan_data = llm_plan(days=1)
    plan_data["sessions"][0]["exercises"][0]["duration_minutes"] = 90
    provider = FakeProvider([json.dumps(plan_data)])
    plan = asyncio.run(generate_training_plan(make_request(), provider, catalog=CATALOG))
    assert len(plan.generation.warnings) == 2


def test_provider_factory(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    assert create_llm_provider("ollama").describe() == {"provider": "ollama", "model": "llama3.1:8b"}
    monkeypatch.setenv("LLM_MODEL", "qwen2.5:7b")
    assert create_llm_provider("openai").model == "qwen2.5:7b"


def test_real_catalog_loads():
    catalog = load_catalog()
    assert len(catalog) > 800
    assert any(c.category == "pole_move" for c in catalog)
