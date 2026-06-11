"""
Database models for Pole Sport Training Plan Generator.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Exercise(Base):
    """Exercise model for storing exercise data."""
    __tablename__ = "exercises"

    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(Text, nullable=True)
    
    # Exercise properties
    category = Column(String(100), index=True)  # strength, flexibility, endurance, etc.
    level = Column(String(50), index=True)  # beginner, intermediate, advanced
    force = Column(String(50), nullable=True)  # push, pull, static
    mechanic = Column(String(50), nullable=True)  # compound, isolation
    
    # Equipment
    equipment = Column(String(255), nullable=True)
    
    # Muscle groups (JSON for flexibility)
    primary_muscles = Column(JSON, default=[])  # ["biceps", "forearms"]
    secondary_muscles = Column(JSON, default=[])
    
    # Instructions and images
    instructions = Column(JSON, default=[])  # Array of instruction steps
    images = Column(JSON, default=[])  # Array of image paths
    
    # Pole sport specific
    is_pole_sport = Column(Boolean, default=False, index=True)
    pole_specific_notes = Column(Text, nullable=True)
    difficulty_progression = Column(String(50), nullable=True)  # Basic, Intermediate, Advanced
    
    # Source information
    source = Column(String(100), default="general")  # "free-exercise-db", "pole-sport", "custom"
    source_url = Column(String(500), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    training_plan_exercises = relationship("TrainingPlanExercise", back_populates="exercise")

    def __repr__(self):
        return f"<Exercise(id={self.id}, name={self.name}, is_pole_sport={self.is_pole_sport})>"


class TrainingPlanExercise(Base):
    """Junction table for Training Plans and Exercises."""
    __tablename__ = "training_plan_exercises"

    id = Column(String(36), primary_key=True)
    training_plan_id = Column(String(36), ForeignKey("training_plans.id"), index=True)
    exercise_id = Column(String(255), ForeignKey("exercises.id"), index=True)
    
    # Exercise specific details for this plan
    duration_minutes = Column(Integer)
    sets = Column(Integer, nullable=True)
    repetitions = Column(Integer, nullable=True)
    rest_seconds = Column(Integer, default=60)
    intensity = Column(String(50))  # low, medium, high
    notes = Column(Text, nullable=True)
    
    # Order in the training plan
    order = Column(Integer)
    
    # Relationships
    training_plan = relationship("TrainingPlan", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="training_plan_exercises")


class TrainingPlan(Base):
    """Training plan model."""
    __tablename__ = "training_plans"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), index=True)
    
    # Plan details
    name = Column(String(255))
    description = Column(Text, nullable=True)
    duration_weeks = Column(Integer)
    focus_area = Column(String(255))  # Upper body strength, Flexibility, etc.
    
    # Difficulty level
    difficulty_level = Column(String(50))  # beginner, intermediate, advanced
    
    # Plan metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    exercises = relationship("TrainingPlanExercise", back_populates="training_plan", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TrainingPlan(id={self.id}, user_id={self.user_id}, focus={self.focus_area})>"


class PoleSportMove(Base):
    """Pole sport specific moves (more granular than exercises)."""
    __tablename__ = "pole_sport_moves"

    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(Text)
    
    # Difficulty progression
    level = Column(String(50), index=True)  # basic, intermediate, advanced, elite
    pole_height = Column(String(100), nullable=True)  # static, spinning, 2.7m, 3.7m
    
    # Prerequisites (can link to other moves)
    prerequisites = Column(JSON, default=[])  # List of move IDs
    
    # Safety information
    safety_tips = Column(JSON, default=[])
    common_mistakes = Column(JSON, default=[])
    
    # Progression steps
    progression_steps = Column(JSON, default=[])
    
    # Muscle groups
    primary_muscles = Column(JSON, default=[])
    secondary_muscles = Column(JSON, default=[])
    
    # Related exercises
    conditioning_exercises = Column(JSON, default=[])  # Exercise IDs for conditioning
    flexibility_exercises = Column(JSON, default=[])
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PoleSportMove(id={self.id}, name={self.name}, level={self.level})>"


class UserProfile(Base):
    """User profile for personalized training plans."""
    __tablename__ = "user_profiles"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), unique=True, index=True)
    
    # Personal info
    age = Column(Integer)
    gender = Column(String(50), nullable=True)
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    
    # Training experience
    pole_sport_level = Column(String(50))  # beginner, intermediate, advanced
    fitness_level = Column(Integer)  # 1-10 scale
    years_pole_experience = Column(Float, nullable=True)
    
    # Availability and preferences
    available_days_per_week = Column(Integer)
    hours_per_session = Column(Float)  # e.g., 1.5 for 1.5 hours
    goals = Column(JSON, default=[])  # ["strength", "flexibility", "new_moves"]
    
    # Health information
    injuries = Column(JSON, default=[])
    limitations = Column(Text, nullable=True)
    
    # Preferences
    preferred_time_of_day = Column(String(50), nullable=True)  # "morning", "evening"
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, level={self.pole_sport_level})>"
