"""
CLI utilities for managing exercise data.
"""

import click
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Exercise database management CLI."""
    pass


@cli.command()
@click.option('--output', default='ml/data/exercises.json', help='Output file path')
@click.option('--use-cache/--no-cache', default=True, help='Use cached file if available')
def fetch_exercises(output, use_cache):
    """Fetch exercises from free-exercise-db."""
    from app.core.data_loader import FreeExerciseDBLoader
    
    # Check cache
    if use_cache and Path(output).exists():
        logger.info(f"Using cached exercises from {output}")
        exercises = FreeExerciseDBLoader.load_local(output)
    else:
        exercises = FreeExerciseDBLoader.fetch_exercises()
        if exercises:
            FreeExerciseDBLoader.save_locally(exercises, output)
    
    click.echo(f"✓ Loaded {len(exercises)} exercises")


@cli.command()
@click.option('--input', default='ml/data/exercises.json', help='Input file path')
@click.option('--db-url', default=None, help='Database URL (uses .env if not provided)')
def import_exercises(input, db_url):
    """Import exercises into database."""
    from app.core.data_loader import FreeExerciseDBLoader, PoleExerciseImporter, PoleSpecificExerciseGenerator
    from app.core.database import SessionLocal
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Load exercises
    exercises = FreeExerciseDBLoader.load_local(input)
    if not exercises:
        click.echo("✗ No exercises found")
        return
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Import free exercises
        count = PoleExerciseImporter.import_exercises(db, exercises)
        click.echo(f"✓ Imported {count} general exercises")
        
        # Import pole sport exercises
        count_pole = PoleSpecificExerciseGenerator.import_pole_exercises(db)
        click.echo(f"✓ Imported {count_pole} pole sport exercises")
        
    finally:
        db.close()


@cli.command()
@click.option('--db-url', default=None, help='Database URL')
def init_db(db_url):
    """Initialize database tables."""
    from app.core.database import init_db
    
    try:
        init_db()
        click.echo("✓ Database initialized successfully")
    except Exception as e:
        click.echo(f"✗ Error initializing database: {e}")


@cli.command()
@click.option('--db-url', default=None, help='Database URL')
def migrate_data(db_url):
    """Fetch and import all exercise data."""
    from app.core.data_loader import FreeExerciseDBLoader, PoleExerciseImporter, PoleSpecificExerciseGenerator
    from app.core.database import SessionLocal, init_db
    from pathlib import Path
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return
    
    # Fetch exercises
    exercises_file = 'ml/data/exercises.json'
    logger.info("Fetching exercises from free-exercise-db...")
    exercises = FreeExerciseDBLoader.fetch_exercises()
    
    if not exercises:
        # Try to load from cache
        logger.info("Trying to load from cache...")
        exercises = FreeExerciseDBLoader.load_local(exercises_file)
    else:
        FreeExerciseDBLoader.save_locally(exercises, exercises_file)
    
    if not exercises:
        click.echo("✗ Failed to load exercises")
        return
    
    # Import to database
    db = SessionLocal()
    
    try:
        count_general = PoleExerciseImporter.import_exercises(db, exercises)
        click.echo(f"✓ Imported {count_general} general exercises")
        
        count_pole = PoleSpecificExerciseGenerator.import_pole_exercises(db)
        click.echo(f"✓ Imported {count_pole} pole sport exercises")
        
        click.echo("✓ Data migration completed successfully")
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        click.echo(f"✗ Migration failed: {e}")
    finally:
        db.close()


if __name__ == '__main__':
    cli()
