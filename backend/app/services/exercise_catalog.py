"""
Exercise catalog used to ground the LLM.

The LLM should build plans from exercises that actually exist in our data, not
invent them. This module loads the catalog (database first, JSON files as a
fallback) and picks a compact, relevant subset for a given user profile, which
is then embedded in the prompt.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import random
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent
EXERCISES_JSON = BACKEND_DIR / "ml" / "data" / "exercises.json"
POLE_MOVES_PY = PROJECT_ROOT / "ml" / "data" / "pole_sport_moves.py"

# Equipment that is realistic in a pole studio or at home.
POLE_FRIENDLY_EQUIPMENT = {None, "body only", "bands", "dumbbell", "kettlebells", "foam roll",
                           "exercise ball", "medicine ball", "other", "pole"}

GOAL_CATEGORIES = {
    "strength": {"strength"},
    "flexibility": {"stretching", "flexibility"},
    "endurance": {"cardio", "plyometrics"},
    "new_moves": {"technique", "pole_move"},
}

LEVEL_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}
LEVEL_ALIASES = {"basic": "beginner", "expert": "advanced", "elite": "advanced"}


@dataclass
class CatalogExercise:
    id: str
    name: str
    category: str
    level: str
    equipment: Optional[str] = None
    primary_muscles: List[str] = field(default_factory=list)
    instructions: List[str] = field(default_factory=list)
    is_pole_sport: bool = False

    def prompt_line(self) -> str:
        muscles = ", ".join(self.primary_muscles[:3]) or "-"
        return f"{self.id} | {self.name} | {self.category} | {self.level} | {muscles}"


def _norm_level(level: Optional[str]) -> str:
    level = (level or "beginner").lower()
    return LEVEL_ALIASES.get(level, level if level in LEVEL_ORDER else "beginner")


def _from_dict(d: Dict, is_pole: bool = False, category: Optional[str] = None) -> CatalogExercise:
    return CatalogExercise(
        id=str(d["id"]),
        name=d.get("name", d["id"]),
        category=(category or d.get("category") or "general").lower(),
        level=_norm_level(d.get("level")),
        equipment=d.get("equipment"),
        primary_muscles=list(d.get("primary_muscles") or d.get("primaryMuscles") or []),
        instructions=list(d.get("instructions") or d.get("progression_steps") or []),
        is_pole_sport=bool(d.get("is_pole_sport", is_pole)),
    )


def _load_from_db() -> List[CatalogExercise]:
    try:
        from app.core.database import SessionLocal
        from app.models import Exercise
    except Exception as exc:  # sqlalchemy missing or models not importable
        logger.debug("Exercise DB not available: %s", exc)
        return []
    try:
        db = SessionLocal()
        try:
            rows = db.query(Exercise).all()
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Could not read exercises from database, using JSON fallback: %s", exc)
        return []
    return [
        CatalogExercise(
            id=r.id, name=r.name, category=(r.category or "general").lower(), level=_norm_level(r.level),
            equipment=r.equipment, primary_muscles=list(r.primary_muscles or []),
            instructions=list(r.instructions or []), is_pole_sport=bool(r.is_pole_sport),
        )
        for r in rows
    ]


def _load_pole_moves() -> List[CatalogExercise]:
    """Pole moves from ml/data/pole_sport_moves.py (loaded by path, it is not a package)."""
    if not POLE_MOVES_PY.exists():
        return []
    try:
        spec = importlib.util.spec_from_file_location("pole_sport_moves", POLE_MOVES_PY)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        moves = getattr(module, "POLE_SPORT_MOVES", {})
    except Exception as exc:
        logger.warning("Could not load pole moves: %s", exc)
        return []
    result = []
    for move in moves.values():
        item = _from_dict({**move, "id": f"move_{move['id']}", "equipment": "pole"}, is_pole=True, category="pole_move")
        result.append(item)
    return result


def _load_pole_exercises() -> List[CatalogExercise]:
    try:
        from app.core.data_loader import PoleSpecificExerciseGenerator
    except Exception as exc:
        logger.debug("Pole exercise definitions not importable: %s", exc)
        return []
    return [_from_dict({**e, "equipment": "pole"}, is_pole=True) for e in PoleSpecificExerciseGenerator.POLE_EXERCISES]


def _load_from_files() -> List[CatalogExercise]:
    items: List[CatalogExercise] = []
    if EXERCISES_JSON.exists():
        with open(EXERCISES_JSON, encoding="utf-8") as f:
            items.extend(_from_dict(d) for d in json.load(f))
    items.extend(_load_pole_exercises())
    return items


def _dedupe(items: Iterable[CatalogExercise]) -> List[CatalogExercise]:
    seen: Dict[str, CatalogExercise] = {}
    for item in items:
        seen.setdefault(item.id, item)
    return list(seen.values())


@lru_cache(maxsize=1)
def load_catalog() -> List[CatalogExercise]:
    """Full catalog: database (or JSON fallback) plus pole moves."""
    items = _load_from_db() or _load_from_files()
    items = _dedupe([*items, *_load_pole_moves()])
    logger.info("Exercise catalog loaded with %d entries", len(items))
    return items


def select_candidates(
    catalog: List[CatalogExercise],
    experience_level: str,
    goals: List[str],
    per_goal: int = 15,
    seed: Optional[int] = None,
) -> List[CatalogExercise]:
    """
    Pick a relevant subset of the catalog for the prompt.

    - only exercises up to the user's level
    - only equipment that is realistic for pole training
    - up to ``per_goal`` exercises per selected goal, pole-specific ones first
    - always a few warm-up / mobility exercises
    """
    rng = random.Random(seed)
    max_level = LEVEL_ORDER.get(experience_level, 0)
    usable = [
        e for e in catalog
        if LEVEL_ORDER.get(e.level, 0) <= max_level and (e.is_pole_sport or e.equipment in POLE_FRIENDLY_EQUIPMENT)
    ]

    chosen: Dict[str, CatalogExercise] = {}

    def take(pool: List[CatalogExercise], n: int) -> None:
        pole = [e for e in pool if e.is_pole_sport]
        other = [e for e in pool if not e.is_pole_sport]
        rng.shuffle(other)
        for e in (pole + other)[:n]:
            chosen.setdefault(e.id, e)

    for goal in goals:
        categories = GOAL_CATEGORIES.get(goal, set())
        take([e for e in usable if e.category in categories], per_goal)

    # Warm-up and cool-down material is always needed.
    take([e for e in usable if e.category == "stretching"], 6)
    # Pole conditioning is useful for every goal.
    take([e for e in usable if e.is_pole_sport and e.category != "pole_move"], 10)

    return list(chosen.values())
