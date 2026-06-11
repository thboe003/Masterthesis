"""
Exercise management API routes.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models import Exercise

router = APIRouter(prefix="/api/v1/exercises", tags=["exercises"])


class ExerciseResponse(BaseModel):
    """Exercise response model."""
    id: str
    name: str
    description: Optional[str] = None
    category: str
    level: str
    equipment: Optional[str] = None
    primary_muscles: List[str] = []
    secondary_muscles: List[str] = []
    is_pole_sport: bool
    difficulty_progression: Optional[str] = None


@router.get("", response_model=List[ExerciseResponse])
async def list_exercises(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    level: Optional[str] = None,
    is_pole_sport: Optional[bool] = None,
    search: Optional[str] = None
) -> List[ExerciseResponse]:
    """
    List exercises with filtering and pagination.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum records to return (default: 10, max: 100)
    - **category**: Filter by category (e.g., "strength", "flexibility")
    - **level**: Filter by level (e.g., "beginner", "intermediate", "advanced")
    - **is_pole_sport**: Filter for pole sport specific exercises
    - **search**: Search in name and description
    """
    query = db.query(Exercise)
    
    if category:
        query = query.filter(Exercise.category == category)
    
    if level:
        query = query.filter(Exercise.level == level)
    
    if is_pole_sport is not None:
        query = query.filter(Exercise.is_pole_sport == is_pole_sport)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Exercise.name.ilike(search_term)) |
            (Exercise.description.ilike(search_term))
        )
    
    exercises = query.offset(skip).limit(limit).all()
    return exercises


@router.get("/pole-sport", response_model=List[ExerciseResponse])
async def list_pole_exercises(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    level: Optional[str] = None
) -> List[ExerciseResponse]:
    """
    List pole sport specific exercises.
    
    - **level**: Filter by difficulty level
    """
    query = db.query(Exercise).filter(Exercise.is_pole_sport == True)
    
    if level:
        query = query.filter(Exercise.level == level)
    
    exercises = query.offset(skip).limit(limit).all()
    return exercises


@router.get("/categories", response_model=List[str])
async def get_categories(db: Session = Depends(get_db)) -> List[str]:
    """Get all available exercise categories."""
    categories = db.query(Exercise.category).distinct().all()
    return [cat[0] for cat in categories if cat[0]]


@router.get("/by-muscle/{muscle}", response_model=List[ExerciseResponse])
async def get_exercises_by_muscle(
    muscle: str,
    db: Session = Depends(get_db),
    limit: int = Query(20, le=100)
) -> List[ExerciseResponse]:
    """
    Get exercises that target a specific muscle group.
    
    - **muscle**: Muscle name (e.g., "biceps", "quadriceps")
    """
    exercises = db.query(Exercise).filter(
        (Exercise.primary_muscles.contains([muscle])) |
        (Exercise.secondary_muscles.contains([muscle]))
    ).limit(limit).all()
    
    return exercises


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: str,
    db: Session = Depends(get_db)
) -> ExerciseResponse:
    """Get a specific exercise by ID."""
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    return exercise


@router.get("", response_model=dict)
async def get_statistics(db: Session = Depends(get_db)) -> dict:
    """Get exercise database statistics."""
    total_exercises = db.query(Exercise).count()
    pole_sport_exercises = db.query(Exercise).filter(Exercise.is_pole_sport == True).count()
    general_exercises = total_exercises - pole_sport_exercises
    
    return {
        "total_exercises": total_exercises,
        "pole_sport_exercises": pole_sport_exercises,
        "general_exercises": general_exercises,
        "sources": ["free-exercise-db", "pole-sport"]
    }
