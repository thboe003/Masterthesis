"""
Root project configuration and utilities.
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
ML_DIR = PROJECT_ROOT / "ml"
DOCS_DIR = PROJECT_ROOT / "docs"
DOCKER_DIR = PROJECT_ROOT / "docker"

# Create necessary directories
for directory in [BACKEND_DIR, FRONTEND_DIR, ML_DIR, DOCS_DIR, DOCKER_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

print(f"Project root: {PROJECT_ROOT}")
print(f"Backend: {BACKEND_DIR}")
print(f"Frontend: {FRONTEND_DIR}")
print(f"ML Pipeline: {ML_DIR}")
