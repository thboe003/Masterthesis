"""
Data loading and migration utilities for exercise databases.
"""

import json
import os
from pathlib import Path
from typing import List, Dict
import logging
import requests
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class FreeExerciseDBLoader:
    """Load exercises from free-exercise-db GitHub repository."""
    
    BASE_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
    
    @staticmethod
    def fetch_exercises() -> List[Dict]:
        """
        Fetch exercises from free-exercise-db.
        
        Returns:
            List of exercise dictionaries
        """
        try:
            logger.info(f"Fetching exercises from {FreeExerciseDBLoader.BASE_URL}...")
            response = requests.get(FreeExerciseDBLoader.BASE_URL, timeout=30)
            response.raise_for_status()
            exercises = response.json()
            logger.info(f"Successfully fetched {len(exercises)} exercises")
            return exercises
        except requests.RequestException as e:
            logger.error(f"Error fetching exercises: {e}")
            return []
    
    @staticmethod
    def save_locally(exercises: List[Dict], filepath: str) -> None:
        """
        Save exercises to local JSON file.
        
        Args:
            exercises: List of exercise dictionaries
            filepath: Path to save JSON file
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(exercises, f, indent=2)
        logger.info(f"Saved {len(exercises)} exercises to {filepath}")
    
    @staticmethod
    def load_local(filepath: str) -> List[Dict]:
        """
        Load exercises from local JSON file.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            List of exercise dictionaries
        """
        try:
            with open(filepath, 'r') as f:
                exercises = json.load(f)
            logger.info(f"Loaded {len(exercises)} exercises from {filepath}")
            return exercises
        except FileNotFoundError:
            logger.warning(f"File not found: {filepath}")
            return []


class PoleExerciseImporter:
    """Import free-exercise-db exercises into database."""
    
    @staticmethod
    def import_exercises(db: Session, exercises: List[Dict]) -> int:
        """
        Import exercises into database.
        
        Args:
            db: Database session
            exercises: List of exercise dictionaries
            
        Returns:
            Number of exercises imported
        """
        from app.models import Exercise
        
        imported_count = 0
        
        for exercise_data in exercises:
            try:
                # Check if exercise already exists
                existing = db.query(Exercise).filter(
                    Exercise.id == exercise_data.get('id')
                ).first()
                
                if existing:
                    logger.debug(f"Exercise {exercise_data.get('id')} already exists, skipping")
                    continue
                
                # Create new exercise
                exercise = Exercise(
                    id=exercise_data.get('id'),
                    name=exercise_data.get('name'),
                    description=exercise_data.get('description', ''),
                    category=exercise_data.get('category', 'general'),
                    level=exercise_data.get('level', 'beginner'),
                    force=exercise_data.get('force'),
                    mechanic=exercise_data.get('mechanic'),
                    equipment=exercise_data.get('equipment'),
                    primary_muscles=exercise_data.get('primaryMuscles', []),
                    secondary_muscles=exercise_data.get('secondaryMuscles', []),
                    instructions=exercise_data.get('instructions', []),
                    images=exercise_data.get('images', []),
                    source='free-exercise-db',
                    source_url='https://github.com/yuhonas/free-exercise-db',
                    is_pole_sport=False
                )
                
                db.add(exercise)
                imported_count += 1
                
                if imported_count % 100 == 0:
                    logger.info(f"Imported {imported_count} exercises so far...")
                    
            except Exception as e:
                logger.error(f"Error importing exercise {exercise_data.get('id')}: {e}")
                continue
        
        db.commit()
        logger.info(f"Successfully imported {imported_count} exercises")
        return imported_count


class PoleSpecificExerciseGenerator:
    """Generate pole sport specific exercises and moves."""
    
    POLE_EXERCISES = [
        {
            "id": "pole_basic_grip",
            "name": "Basic Pole Grip",
            "description": "Fundamental grip technique for pole dancing",
            "level": "beginner",
            "category": "technique",
            "primary_muscles": ["hand", "forearm"],
            "secondary_muscles": ["wrist", "grip"],
            "instructions": [
                "Stand facing the pole",
                "Wrap your hand around the pole",
                "Keep fingers spread for better grip",
                "Maintain firm contact with palm"
            ],
            "is_pole_sport": True,
            "difficulty_progression": "Basic"
        },
        {
            "id": "pole_spin_conditioning",
            "name": "Pole Spin Conditioning",
            "description": "Build grip strength for spinning poles",
            "level": "intermediate",
            "category": "strength",
            "primary_muscles": ["grip", "forearm"],
            "secondary_muscles": ["arm", "shoulder"],
            "instructions": [
                "Start with basic pole grip",
                "Engage core and maintain body contact",
                "Allow pole to spin",
                "Control rotation with grip pressure"
            ],
            "is_pole_sport": True,
            "difficulty_progression": "Intermediate"
        },
        {
            "id": "pole_flexibility_routine",
            "name": "Pole Flexibility Routine",
            "description": "Essential flexibility training for advanced moves",
            "level": "intermediate",
            "category": "flexibility",
            "primary_muscles": ["hip", "shoulder", "back"],
            "secondary_muscles": ["hamstring", "quad"],
            "instructions": [
                "Perform hip opener stretches",
                "Include shoulder mobility work",
                "Work on back flexibility",
                "Hold each stretch 30-60 seconds"
            ],
            "is_pole_sport": True,
            "difficulty_progression": "Intermediate"
        },
        {
            "id": "pole_invert_strength",
            "name": "Invert Preparation Strength",
            "description": "Build strength for safe inversions",
            "level": "advanced",
            "category": "strength",
            "primary_muscles": ["core", "shoulder", "arm"],
            "secondary_muscles": ["back", "chest"],
            "instructions": [
                "Perform controlled handstands",
                "Practice shoulder shrugs on pole",
                "Build scapular strength",
                "Work on core engagement"
            ],
            "is_pole_sport": True,
            "difficulty_progression": "Advanced"
        },
        {
            "id": "pole_pole_sit_progression",
            "name": "Pole Sit Progression",
            "description": "Progressive training for pole sit holds",
            "level": "intermediate",
            "category": "strength",
            "primary_muscles": ["leg", "grip"],
            "secondary_muscles": ["core", "arm"],
            "instructions": [
                "Start in basic pole sit position",
                "Increase hold duration gradually",
                "Practice on both sides",
                "Build grip endurance"
            ],
            "is_pole_sport": True,
            "difficulty_progression": "Intermediate"
        }
    ]
    
    @staticmethod
    def import_pole_exercises(db: Session) -> int:
        """
        Import pole sport specific exercises into database.
        
        Args:
            db: Database session
            
        Returns:
            Number of exercises imported
        """
        from app.models import Exercise
        
        imported_count = 0
        
        for exercise_data in PoleSpecificExerciseGenerator.POLE_EXERCISES:
            try:
                # Check if exercise already exists
                existing = db.query(Exercise).filter(
                    Exercise.id == exercise_data.get('id')
                ).first()
                
                if existing:
                    logger.debug(f"Pole exercise {exercise_data.get('id')} already exists")
                    continue
                
                # Create new exercise
                exercise = Exercise(
                    id=exercise_data.get('id'),
                    name=exercise_data.get('name'),
                    description=exercise_data.get('description'),
                    category=exercise_data.get('category', 'pole-sport'),
                    level=exercise_data.get('level', 'intermediate'),
                    primary_muscles=exercise_data.get('primary_muscles', []),
                    secondary_muscles=exercise_data.get('secondary_muscles', []),
                    instructions=exercise_data.get('instructions', []),
                    source='pole-sport',
                    is_pole_sport=True,
                    pole_specific_notes=f"Difficulty: {exercise_data.get('difficulty_progression')}",
                    difficulty_progression=exercise_data.get('difficulty_progression')
                )
                
                db.add(exercise)
                imported_count += 1
                
            except Exception as e:
                logger.error(f"Error importing pole exercise {exercise_data.get('id')}: {e}")
                continue
        
        db.commit()
        logger.info(f"Successfully imported {imported_count} pole sport exercises")
        return imported_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    print("Exercise data loading utilities initialized")
