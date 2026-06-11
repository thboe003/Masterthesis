#!/usr/bin/env python
"""
Backend management script for Pole Sport AI Training Generator.
Similar to Django's manage.py.

Usage:
    python manage.py init-db           # Initialize database
    python manage.py fetch-exercises   # Fetch exercises from free-exercise-db
    python manage.py import-exercises  # Import exercises into database
    python manage.py migrate-data      # Full data migration
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.cli import cli

if __name__ == "__main__":
    cli()
